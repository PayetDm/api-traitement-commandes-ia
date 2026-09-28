from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
import logging
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.services import analyser_mail_avec_llm
from app.models import Article, Commande
from app.schemas import CommandeStatutUpdate, CommandeSchema
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
        commande = Commande(
            client=data.get("client", "Client Inconnu"),
            message_id=message_id,
            contenu_email=contenu_email,
            montant_total=data.get("montant_total", 0.0),
            urgente=1 if data.get("urgente", False) else 0,
            statut=("en_attente" if data.get("est_une_commande", False) else "transfere_sav"),
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
    return {
        "total_commandes": db.query(Commande).count(),
        "total_demandes": db.query(Commande).count(),
        "chiffre_affaires_cumule": db.query(
            func.coalesce(func.sum(Commande.montant_total), 0.0)
        ).scalar(),
        "commandes_urgentes": db.query(Commande)
        .filter(Commande.urgente == 1)
        .count(),
        "dossiers_a_verifier": db.query(Commande)
        .filter(Commande.statut == "a_verifier_manuellement")
        .count(),
    }