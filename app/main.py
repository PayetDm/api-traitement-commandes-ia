from contextlib import asynccontextmanager
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine, get_db, obtenir_commande, sauvegarder_commande
from app.schemas import CommandeSchema, EmailIn
from app.security import verifier_cle_api
from app.services import analyser_mail_avec_llm


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="API Traitement Commandes IA - V2", lifespan=lifespan)


def traiter_email_en_tache_de_fond(texte_email: str):
    """Fonction exécutée en arrière-plan pour appeler l'IA et sauvegarder."""
    db = SessionLocal()
    try:
        donnees_extraites = analyser_mail_avec_llm(texte_email)
        if donnees_extraites:
            donnees_adaptees = {
                "client": donnees_extraites.get("client", "Inconnu"),
                "montant_total": float(donnees_extraites.get("montant_total_eur", 0.0)),
                "urgente": donnees_extraites.get("statut_livraison") == "urgent",
                "articles": donnees_extraites.get("articles", []),
            }
            sauvegarder_commande(db, donnees_adaptees)
    finally:
        db.close()


@app.post(
    "/commandes/analyser",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(verifier_cle_api)], # <--- Sécurité
)
async def analyser_commande(
    payload: EmailIn, background_tasks: BackgroundTasks
):
    # Traitement dans la file d'attente d'arrière-plan
    background_tasks.add_task(traiter_email_en_tache_de_fond, payload.contenu_email)

    return {
        "message": "E-mail reçu et en cours d'analyse par l'IA.",
        "statut": "en_cours",
    }


@app.get("/commandes/{commande_id}", response_model=CommandeSchema)
def lire_commande(commande_id: int, db: Session = Depends(get_db)):
    commande = obtenir_commande(db, commande_id)
    if not commande:
        raise HTTPException(status_code=404, detail="Commande non trouvée.")
    return commande