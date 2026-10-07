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
    """Enregistre un mail analysé (commande, SAV ou service client) avec ses articles."""
    from app.models import Article # Import local pour éviter les problèmes de dépendances circulaires

    statut_final = data.get("statut", "en_attente")

    nouvelle_commande = Commande(
        client=data.get("client", "Client Inconnu"),
        message_id=data.get("message_id"),
        contenu_email=data.get("contenu_email"),
        montant_total=data.get("montant_total", 0.0),
        urgente=1 if data.get("urgente", False) else 0,
        statut=statut_final,
    )

    # Ajout des articles extrait par le LLM
    for article_data in data.get("articles", []):
        if not isinstance(article_data, dict):
            continue  # Ignore les articles mal formés
        # Saute les articles avec des champs manquants ou invalides
        if "nom" not in article_data or "quantite" not in article_data:
            continue
        nouvelle_commande.articles.append(
            Article(
                nom=article_data.get("nom", "Article non identifié"),
                quantite=article_data.get("quantite", 1),
                prix_unitaire=article_data.get("prix_unitaire", 0.0),
            )
        )

    db.add(nouvelle_commande)
    db.commit()
    db.refresh(nouvelle_commande)
    return nouvelle_commande


def obtenir_commande(db: Session, commande_id: int) -> Commande:
    """Récupère une commande par son ID."""
    return db.query(Commande).filter(Commande.id == commande_id).first()