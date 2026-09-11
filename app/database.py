import os
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# 1. URL de la BDD
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite:///./commandes.db"
)

# SQLite a besoin de connect_args, mais pas PostgreSQL
connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base unique pour tout le projet
Base = declarative_base()


def get_db():
    """Dépendance FastAPI pour fournir une session BDD par requête."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Fonctions Helper BDD ---
# On importe le modèle unique défini dans models.py
from app.models import Commande  # noqa: E402


def sauvegarder_commande(db: Session, data: dict) -> Commande:
    """Enregistre un mail analysé (commande ou transfert SAV)."""
    statut_final = data.get("statut", "en_attente")

    nouvelle_commande = Commande(
        client=data.get("client", "Client Inconnu"),
        montant_total=data.get("montant_total", 0.0),
        urgente=1 if data.get("urgente", False) else 0,
        statut=statut_final,
    )
    db.add(nouvelle_commande)
    db.commit()
    db.refresh(nouvelle_commande)
    return nouvelle_commande


def obtenir_commande(db: Session, commande_id: int) -> Commande:
    """Récupère une commande par son ID."""
    return db.query(Commande).filter(Commande.id == commande_id).first()