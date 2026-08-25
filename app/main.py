from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db, obtenir_commande, sauvegarder_commande
from app.schemas import CommandeSchema, EmailIn
from app.services import analyser_mail_avec_llm  # <--- Nom exact du service


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="API Traitement Commandes IA - V2", lifespan=lifespan)


@app.post(
    "/commandes/analyser",
    response_model=CommandeSchema,
    status_code=status.HTTP_201_CREATED,
)
async def analyser_commande(payload: EmailIn, db: Session = Depends(get_db)):
    # 1. Analyse IA avec le bon nom de fonction
    donnees_extraites = analyser_mail_avec_llm(payload.contenu_email)

    if not donnees_extraites:
        raise HTTPException(
            status_code=400, detail="Impossible d'extraire les données de l'e-mail."
        )

    # 2. Harmonisation simple si les clés du JSON diffèrent légèrement
    donnees_adaptees = {
        "client": donnees_extraites.get("client", "Inconnu"),
        "montant_total": float(donnees_extraites.get("montant_total_eur", 0.0)),
        "urgente": donnees_extraites.get("statut_livraison") == "urgent",
        "articles": donnees_extraites.get("articles", []),
    }

    # 3. Sauvegarde ORM
    commande = sauvegarder_commande(db, donnees_adaptees)
    return commande


@app.get("/commandes/{commande_id}", response_model=CommandeSchema)
def lire_commande(commande_id: int, db: Session = Depends(get_db)):
    commande = obtenir_commande(db, commande_id)
    if not commande:
        raise HTTPException(status_code=404, detail="Commande non trouvée.")
    return commande