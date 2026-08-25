import os
from sqlalchemy import Column, Float, Integer, String, Boolean, JSON, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

SQLALCHEMY_DATABASE_URL = "sqlite:///./commandes.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Commande(Base):
    __tablename__ = "commandes"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    client = Column(String, index=True)
    montant_total = Column(Float)
    urgente = Column(Boolean, default=False)
    statut = Column(String, default="en_attente")
    articles = Column(JSON)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Fonctions Helper BDD ---

def sauvegarder_commande(db: Session, data: dict) -> Commande:
    """Enregistre un mail analysé (commande ou transfert SAV)."""
    
    # On récupère le statut préparé en amont par main.py
    statut_final = data.get("statut", "en_attente")

    nouvelle_commande = Commande(
        client=data.get("client", "Client Inconnu"),
        montant_total=data.get("montant_total", 0.0),
        urgente=data.get("urgente", False),
        statut=statut_final,
        articles=data.get("articles", [])
    )
    db.add(nouvelle_commande)
    db.commit()
    db.refresh(nouvelle_commande)
    return nouvelle_commande


def obtenir_commande(db: Session, commande_id: int) -> Commande:
    """Récupère une commande par son ID."""
    return db.query(Commande).filter(Commande.id == commande_id).first()