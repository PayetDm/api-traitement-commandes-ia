from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base


class Commande(Base):
    """Table 'commandes' en BDD."""

    __tablename__ = "commandes"

    id = Column(Integer, primary_key=True, index=True)
    client = Column(String, nullable=False)
    montant_total = Column(Float, nullable=False)
    urgente = Column(Integer, default=0)  # 1 si urgente, 0 sinon

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