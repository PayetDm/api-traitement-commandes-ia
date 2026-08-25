from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# URL de la base de données (SQLite en local)
SQLALCHEMY_DATABASE_URL = "sqlite:///./commandes.db"

# Création du moteur SQLite
# check_same_thread=False est nécessaire uniquement pour SQLite avec FastAPI
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Session pour interagir avec la BDD
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base de classe pour nos modèles ORM
Base = declarative_base()


def get_db():
    """Dépendance FastAPI pour obtenir une session de BDD par requête."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from sqlalchemy.orm import Session
from app.models import Article, Commande


def sauvegarder_commande(db: Session, donnes: dict) -> Commande:
    """Enregistre une commande et ses articles en BDD via SQLAlchemy."""
    # 1. Création de la commande
    nouvelle_commande = Commande(
        client=donnes["client"],
        montant_total=donnes["montant_total"],
        urgente=1 if donnes.get("urgente") else 0,
    )
    db.add(nouvelle_commande)
    db.commit()
    db.refresh(nouvelle_commande)

    # 2. Création des articles associés
    for item in donnes.get("articles", []):
        article = Article(
            commande_id=nouvelle_commande.id,
            nom=item["nom"],
            quantite=item["quantite"],
            prix_unitaire=item["prix_unitaire"],
        )
        db.add(article)

    db.commit()
    db.refresh(nouvelle_commande)
    return nouvelle_commande


def obtenir_commande(db: Session, commande_id: int):
    """Récupère une commande par son ID avec ses articles."""
    return db.query(Commande).filter(Commande.id == commande_id).first()