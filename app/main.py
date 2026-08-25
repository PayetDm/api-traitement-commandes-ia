from contextlib import asynccontextmanager
import logging
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine, get_db, obtenir_commande, sauvegarder_commande
from app.schemas import CommandeSchema, EmailIn
from app.security import verifier_cle_api
from app.services import analyser_mail_avec_llm

# Configuration globale du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Demarrage de l'application et creation des tables...")
    Base.metadata.create_all(bind=engine)
    yield
    logger.info("Arret de l'application.")


app = FastAPI(title="API Traitement Commandes IA - V2", lifespan=lifespan)


def traiter_email_en_tache_de_fond(texte_email: str):
    logger.info("Debut du traitement en arriere-plan pour l'e-mail.")
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
            commande = sauvegarder_commande(db, donnees_adaptees)
            logger.info("Commande #%s sauvegardee avec succes.", commande.id)
        else:
            logger.warning("Aucune donnee valide n'a pu etre extraite de l'e-mail.")
    except Exception as e:
        logger.error("Erreur inattendue lors du traitement en arriere-plan : %s", e)
    finally:
        db.close()


@app.get("/health", status_code=status.HTTP_200_OK)
def health_check(db: Session = Depends(get_db)):
    """Endpoint permettant de verifier l'etat de sante de l'API et de la BDD."""
    try:
        db.execute(text("SELECT 1"))
        return {"statut": "ok", "base_de_donnees": "connectee"}
    except Exception as e:
        logger.error("Echec du test de sante de la BDD : %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="La base de donnees ne repond pas.",
        )


@app.post(
    "/commandes/analyser",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(verifier_cle_api)],
)
async def analyser_commande(
    payload: EmailIn, background_tasks: BackgroundTasks
):
    logger.info("Reception d'une demande d'analyse de commande.")
    background_tasks.add_task(traiter_email_en_tache_de_fond, payload.contenu_email)

    return {
        "message": "E-mail recu et en cours d'analyse par l'IA.",
        "statut": "en_cours",
    }


@app.get("/commandes/{commande_id}", response_model=CommandeSchema)
def lire_commande(commande_id: int, db: Session = Depends(get_db)):
    commande = obtenir_commande(db, commande_id)
    if not commande:
        raise HTTPException(status_code=404, detail="Commande non trouvee.")
    return commande