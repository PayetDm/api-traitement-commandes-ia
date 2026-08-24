from typing import List
from pydantic import BaseModel, Field


class Article(BaseModel):
    nom: str = Field(..., example="Panneau de chêne massif")
    quantite: int = Field(..., gt=0, example=2)
    prix_unitaire: float = Field(..., gt=0.0, example=45.0)


class EmailIn(BaseModel):
    texte_email: str = Field(
        ...,
        min_length=10,
        description="Le contenu brut du mail contenant la commande",
        example="Bonjour, commande CMD-102 pour Damien : 2 tables à 50€. Urgent.",
    )


class CommandeOut(BaseModel):
    id: int
    numero_commande: str
    client: str
    montant_total: float
    urgence: str
    articles: List[Article]