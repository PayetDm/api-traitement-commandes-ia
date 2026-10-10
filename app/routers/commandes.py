from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
import logging
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session
from langfuse import get_client

from app.database import SessionLocal, get_db
from app.services import analyser_mail_avec_llm
from app.models import Article, Commande
from app.schemas import CommandeStatutUpdate, CommandeSchema, RedirectionInput
from app.security import verifier_cle_api

router = APIRouter(tags=["Commandes"])
logger = logging.getLogger(__name__)

class EmailInput(BaseModel):
    contenu_email: str = Field(min_length=1, max_length=10000)
    message_id: str | None = None

def _analyser_en_arriere_plan(contenu_email: str, message_id: str | None = None) -> None:
    db = SessionLocal()
    try:
        data = analyser_mail_avec_llm(contenu_email)
        articles = [Article(**article) for article in data.get("articles", [])]

        # Détermine le statut en fonction de la classification
        categorie = data.get("categorie", "autre")
        if categorie == "commande":
            statut_initial = "en_attente"
        elif categorie == "sav":
            statut_initial = "transfere_sav"
        elif categorie == "service_client":
            statut_initial = "transfere_service_client"
        else:
            # Fallback : on met en service_client (traitement humain)
            statut_initial = "transfere_service_client"

        commande = Commande(
            client=data.get("client", "Client Inconnu"),
            message_id=message_id,
            contenu_email=contenu_email,
            montant_total=data.get("montant_total", 0.0),
            urgente=1 if data.get("urgente", False) else 0,
            statut=statut_initial,
            langfuse_trace_id=data.get("langfuse_trace_id"),
            classification_method=data.get("classification_method"),
            articles=articles,
        )
        db.add(commande)
        db.commit()
        logger.info("Commande ou dossier enregistre en arriere-plan avec succes.")
    except Exception:
        db.rollback()
        logger.exception("Erreur lors de l'enregistrement de l'e-mail analyse.")
    finally:
        db.close()

@router.post("/commandes/analyser", status_code=status.HTTP_202_ACCEPTED)
def analyser_commande(
    email: EmailInput,
    _: str = Depends(verifier_cle_api),
):
    _analyser_en_arriere_plan(email.contenu_email, email.message_id)
    return {"statut": "en_cours"}

@router.get("/commandes", response_model=List[CommandeSchema])
def lister_commandes(
    _: str = Depends(verifier_cle_api),
    db: Session = Depends(get_db),
):
    return db.query(Commande).all()

@router.get("/commandes/{commande_id}", response_model=CommandeSchema)
def lire_commande(
    commande_id: int,
    _: str = Depends(verifier_cle_api),
    db: Session = Depends(get_db),
):
    commande = db.query(Commande).filter(Commande.id == commande_id).first()
    if commande is None:
        raise HTTPException(status_code=404, detail="Commande introuvable")
    return commande


@router.patch("/commandes/{commande_id}/statut", response_model=CommandeSchema)
def mettre_a_jour_statut(
    commande_id: int,
    statut_update: CommandeStatutUpdate,
    _: str = Depends(verifier_cle_api),
    db: Session = Depends(get_db),
):
    commande = db.query(Commande).filter(Commande.id == commande_id).first()
    if commande is None:
        raise HTTPException(status_code=404, detail="Commande introuvable")

    commande.statut = statut_update.statut
    db.commit()
    db.refresh(commande)
    return commande


@router.get("/stats")
def statistiques(
    _: str = Depends(verifier_cle_api),
    db: Session = Depends(get_db),
):
    total = db.query(Commande).count()
    nb_fallbacks = db.query(Commande).filter(
        Commande.classification_method == "llm_unavailable_fallback"
    ).count()
    
    taux_fiabilite = 0.0
    if total > 0:
        taux_fiabilite = round(((total - nb_fallbacks) / total) * 100, 1)
    
    return {
        "total_commandes": total,
        "total_demandes": total,
        "chiffre_affaires_cumule": db.query(
            func.coalesce(func.sum(Commande.montant_total), 0.0)
        ).scalar(),
        "commandes_urgentes": db.query(Commande)
        .filter(Commande.urgente == 1)
        .filter(Commande.statut.notin_(["expediee", "traitee"]))
        .count(),
        "en_service_client": db.query(Commande)
        .filter(Commande.statut == "transfere_service_client")
        .count(),
        "nb_fallbacks_llm": nb_fallbacks,
        "taux_fiabilite_llm": taux_fiabilite,      
    }


@router.post("/commandes/{commande_id}/rediriger", response_model=CommandeSchema)
def rediriger_commande(
    commande_id: int,
    payload: RedirectionInput,
    _: str = Depends(verifier_cle_api),
    db: Session = Depends(get_db),
):
    """
    Redirige un dossier vers une autre catégorie (Human-in-the-Loop).
    Change le statut en fonction de la nouvelle catégorie.
    """
    commande = db.query(Commande).filter(Commande.id == commande_id).first()
    if commande is None:
        raise HTTPException(status_code=404, detail="Commande introuvable")

    ancien_statut = commande.statut

    # Mapping catégorie → statut
    mapping_statut = {
        "commande": "en_attente",
        "sav": "transfere_sav",
        "service_client": "transfere_service_client",
    }
    nouveau_statut = mapping_statut.get(payload.nouvelle_categorie)
    if not nouveau_statut:
        raise HTTPException(
            status_code=400,
            detail=f"Catégorie invalide : {payload.nouvelle_categorie}",
        )

    commande.statut = nouveau_statut
    db.commit()
    db.refresh(commande)

    logger.info(
        f"Dossier #{commande_id} redirigé : {ancien_statut} → {nouveau_statut} "
        f"(correction humaine)"
    )

    # ─── Feedback loop MLOps : envoyer un score à Langfuse ───
    if commande.langfuse_trace_id:
        try:
            langfuse = get_client()
            langfuse.create_score(
                trace_id=commande.langfuse_trace_id,
                name="classification_accuracy",
                value=0.0,  # 0.0 = correction humaine = classification IA incorrecte
                comment=(
                    f"Redirigé manuellement : {ancien_statut} → {nouveau_statut}"
                ),
            )
            langfuse.flush()
            logger.info(
                f"Score Langfuse envoyé (0.0) sur la trace "
                f"{commande.langfuse_trace_id}"
            )
        except Exception as e:
            logger.warning(f"Impossible d'envoyer le score Langfuse : {e}")
    else:
        logger.debug(
            f"Pas de trace Langfuse pour la commande #{commande_id}, "
            f"score non envoyé"
        )

    return commande