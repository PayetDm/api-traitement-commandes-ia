from contextlib import asynccontextmanager
import logging
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import Base, Commande, SessionLocal, engine, get_db, obtenir_commande, sauvegarder_commande
from app.schemas import CommandeSchema, EmailIn, CommandeStatutUpdate
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
            # 1. Verification du gardien Python / LLM
            est_commande = donnees_extraites.get("est_une_commande", True)
            articles = donnees_extraites.get("articles", [])
            montant = float(donnees_extraites.get("montant_total", 0.0))

            # Si c'est hors-sujet ou sans articles/montant -> Direction SAV
            if not est_commande or (len(articles) == 0 and montant == 0.0):
                statut_final = "transfere_sav"
                logger.info("Email classe comme Hors-Sujet/SAV.")
            else:
                statut_final = "en_attente"

            # 2. Preparation des donnees propres avec les bonnes clés
            donnees_adaptees = {
                "client": donnees_extraites.get("client", "Inconnu"),
                "montant_total": montant,
                "urgente": donnees_extraites.get("urgente", False),
                "articles": articles,
                "statut": statut_final,
            }

            commande = sauvegarder_commande(db, donnees_adaptees)
            logger.info("Enregistrement #%s sauvegarde (Statut: %s).", commande.id, statut_final)
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


@app.get("/commandes", response_model=list[CommandeSchema])
def lister_commandes(db: Session = Depends(get_db)):
    """Recupere la liste de toutes les commandes."""
    return db.query(Commande).all()


@app.patch("/commandes/{commande_id}/statut", response_model=CommandeSchema)
def mettre_a_jour_statut(
    commande_id: int, 
    payload: CommandeStatutUpdate, 
    db: Session = Depends(get_db)
):
    """Met a jour le statut d'une commande (ex: en_attente, traitee, expediee)."""
    commande = obtenir_commande(db, commande_id)
    if not commande:
        raise HTTPException(status_code=404, detail="Commande non trouvee.")
    
    commande.statut = payload.statut
    db.commit()
    db.refresh(commande)
    return commande