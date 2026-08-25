from typing import List
from pydantic import BaseModel, ConfigDict, Field


class EmailIn(BaseModel):
    contenu_email: str = Field(..., min_length=10)


class ArticleSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    nom: str
    quantite: int
    prix_unitaire: float


class CommandeSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client: str
    montant_total: float
    urgente: bool
    articles: List[ArticleSchema] = []