from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status
import logging
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session
from langfuse import get_client

from app.database import SessionLocal, get_db
from app.services import analyser_mail_avec_llm
from app.models import Article, Commande
from app.schemas import CommandeStatutUpdate, CommandeSchema, RedirectionInput

# --- NOUVEAUX IMPORTS DE SÉCURITÉ (RBAC) ---
from app.security.auth import require_role, User
from app.security.roles import Role

router = APIRouter(tags=["Commandes"])
logger = logging.getLogger(__name__)


# ==========================================
# SCHÉMAS ET FONCTIONS UTILITAIRES
# ==========================================
class EmailInput(BaseModel):
    contenu_email: str = Field(min_length=1, max_length=10000)
    message_id: str | None = None


def _nettoyer_client(client_value) -> str:
    """Nettoie la valeur du client (protection contre les données invalides)."""
    if not client_value:
        return "Client Inconnu"
    if not isinstance(client_value, str):
        return "Client Inconnu"
    client_clean = client_value.strip()
    if not client_clean:
        return "Client Inconnu"
    return client_clean[:200]


def _analyser_en_arriere_plan(contenu_email: str, message_id: str | None = None) -> None:
    """Traite l'e-mail en arrière-plan et enregistre la commande en base."""
    db = SessionLocal()
    try:
        data = analyser_mail_avec_llm(contenu_email)
        articles = [Article(**article) for article in data.get("articles", [])]

        categorie = data.get("categorie", "autre")
        if categorie == "commande":
            statut_initial = "en_attente"
        elif categorie == "sav":
            statut_initial = "transfere_sav"
        elif categorie == "service_client":
            statut_initial = "transfere_service_client"
        else:
            statut_initial = "transfere_service_client"

        client_final = _nettoyer_client(data.get("client"))

        montant = data.get("montant_total", 0.0)
        if not isinstance(montant, (int, float)) or montant < 0:
            montant = 0.0

        commande = Commande(
            client=client_final,
            message_id=message_id,
            contenu_email=contenu_email,
            montant_total=montant,
            urgente=1 if data.get("urgente", False) else 0,
            statut=statut_initial,
            langfuse_trace_id=data.get("langfuse_trace_id"),
            classification_method=data.get("classification_method"),
            articles=articles,
        )
        db.add(commande)
        db.commit()
        logger.info(f"Commande enregistrée : client={client_final}, statut={statut_initial}, montant={montant}€")
    except Exception:
        db.rollback()
        logger.exception("Erreur lors de l'enregistrement de l'e-mail analyse.")
    finally:
        db.close()


# ==========================================
# ROUTES DE L'API (avec RBAC)
# ==========================================

# --- PROTÉGÉ (Operator) : Ingestion d'e-mail ---
@router.post("/commandes/analyser", status_code=status.HTTP_202_ACCEPTED)
def analyser_commande(
    request: Request,
    email: EmailInput,
    user: User = Depends(require_role(Role.OPERATOR)), # <-- RBAC
):
    from app.rate_limit import check_rate_limit
    check_rate_limit(request, max_requests=5, window_seconds=60)

    _analyser_en_arriere_plan(email.contenu_email, email.message_id)
    return {"statut": "en_cours"}


# --- PROTÉGÉ (Reader) : Lecture de la liste ---
@router.get("/commandes", response_model=List[CommandeSchema])
def lister_commandes(
    user: User = Depends(require_role(Role.READER)), # <-- RBAC
    db: Session = Depends(get_db),
):
    commandes = db.query(Commande).all()
    for c in commandes:
        if not c.client or not c.client.strip():
            logger.warning(f"⚠️ Commande #{c.id} a un client vide : '{c.client}'")
    return commandes


# --- PROTÉGÉ (Reader) : Lecture d'une commande spécifique ---
@router.get("/commandes/{commande_id}", response_model=CommandeSchema)
def lire_commande(
    commande_id: int,
    user: User = Depends(require_role(Role.READER)), # <-- RBAC
    db: Session = Depends(get_db),
):
    commande = db.query(Commande).filter(Commande.id == commande_id).first()
    if commande is None:
        raise HTTPException(status_code=404, detail="Commande introuvable")
    return commande


# --- PROTÉGÉ (Operator) : Modification de statut ---
@router.patch("/commandes/{commande_id}/statut", response_model=CommandeSchema)
def mettre_a_jour_statut(
    commande_id: int,
    statut_update: CommandeStatutUpdate,
    user: User = Depends(require_role(Role.OPERATOR)), # <-- RBAC
    db: Session = Depends(get_db),
):
    commande = db.query(Commande).filter(Commande.id == commande_id).first()
    if commande is None:
        raise HTTPException(status_code=404, detail="Commande introuvable")

    commande.statut = statut_update.statut
    db.commit()
    db.refresh(commande)
    return commande


# --- PROTÉGÉ (Reader) : KPIs Dashboard ---
@router.get("/stats")
def statistiques(
    user: User = Depends(require_role(Role.READER)), # <-- RBAC
    db: Session = Depends(get_db),
):
    total = db.query(Commande).count()
    nb_fallbacks = db.query(Commande).filter(Commande.classification_method == "llm_unavailable_fallback").count()

    taux_fiabilite = 0.0
    if total > 0:
        taux_fiabilite = round(((total - nb_fallbacks) / total) * 100, 1)

    return {
        "total_commandes": total,
        "total_demandes": total,
        "chiffre_affaires_cumule": db.query(func.coalesce(func.sum(Commande.montant_total), 0.0)).scalar(),
        "commandes_urgentes": db.query(Commande).filter(Commande.urgente == 1).filter(Commande.statut.notin_(["expediee", "traitee"])).count(),
        "en_service_client": db.query(Commande).filter(Commande.statut == "transfere_service_client").count(),
        "nb_fallbacks_llm": nb_fallbacks,
        "taux_fiabilite_llm": taux_fiabilite,
    }


# --- PROTÉGÉ (Admin) : Redirection HITL (Critique) ---
@router.post("/commandes/{commande_id}/rediriger", response_model=CommandeSchema)
def rediriger_commande(
    commande_id: int,
    payload: RedirectionInput,
    user: User = Depends(require_role(Role.ADMIN)), # <-- RBAC (Action sensible)
    db: Session = Depends(get_db),
):
    """
    Redirige un dossier vers une autre catégorie (Human-in-the-Loop).
    Change le statut et envoie un score de qualité à Langfuse.
    """
    commande = db.query(Commande).filter(Commande.id == commande_id).first()
    if commande is None:
        raise HTTPException(status_code=404, detail="Commande introuvable")

    ancien_statut = commande.statut

    mapping_statut = {
        "commande": "en_attente",
        "sav": "transfere_sav",
        "service_client": "transfere_service_client",
    }
    nouveau_statut = mapping_statut.get(payload.nouvelle_categorie)
    if not nouveau_statut:
        raise HTTPException(status_code=400, detail=f"Catégorie invalide : {payload.nouvelle_categorie}")

    commande.statut = nouveau_statut
    db.commit()
    db.refresh(commande)

    logger.info(f"Dossier #{commande_id} redirigé : {ancien_statut} → {nouveau_statut} (par {user.role.name})")

    # Feedback loop MLOps
    if commande.langfuse_trace_id:
        try:
            langfuse = get_client()
            langfuse.create_score(
                trace_id=commande.langfuse_trace_id,
                name="classification_accuracy",
                value=0.0,
                comment=f"Redirigé manuellement : {ancien_statut} → {nouveau_statut}",
            )
            langfuse.flush()
            logger.info(f"Score Langfuse envoyé (0.0) sur la trace {commande.langfuse_trace_id}")
        except Exception as e:
            logger.warning(f"Impossible d'envoyer le score Langfuse : {e}")
            
    return commande