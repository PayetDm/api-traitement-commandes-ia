from sqlalchemy import Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Commande(Base):
    """Table 'commandes' en BDD."""

    __tablename__ = "commandes"

    id = Column(Integer, primary_key=True, index=True)
    client = Column(String, nullable=False)
    message_id = Column(String, unique=True, index=True, nullable=True)
    contenu_email = Column(Text, nullable=True)
    montant_total = Column(Float, nullable=False)
    urgente = Column(Integer, default=0)  # 1 si urgente, 0 sinon
    statut = Column(String, default="en_attente")

    # ─── Observabilité MLOps ───
    langfuse_trace_id = Column(String, nullable=True, index=True)
    classification_method = Column(String, nullable=True)

    # Relation 1-à-plusieurs avec les articles
    articles = relationship(
        "Article", back_populates="commande", cascade="all, delete-orphan"
    )


class Article(Base):
    """Table 'articles' en BDD."""

    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    commande_id = Column(Integer, ForeignKey("commandes.id"), nullable=False)
    nom = Column(String, nullable=False)
    quantite = Column(Integer, nullable=False)
    prix_unitaire = Column(Float, nullable=False)

    # Relation inverse vers la commande
    commande = relationship("Commande", back_populates="articles")