from typing import List, Optional
from pydantic import BaseModel, Field

# --- Schémas pour la lecture des Articles et Commandes ---

class ArticleSchema(BaseModel):
    nom: str
    quantite: int
    prix_unitaire: float


class CommandeSchema(BaseModel):
    id: int
    client: str
    montant_total: float
    urgente: bool
    statut: str  # <-- Notre nouveau champ statut
    articles: List[ArticleSchema]

    class Config:
        from_attributes = True


# --- Schémas pour les requêtes entrantes (Input) ---

class EmailIn(BaseModel):
    contenu_email: str


class CommandeStatutUpdate(BaseModel):
    statut: str


class CommandeIAOutput(BaseModel):
    """Schéma de validation stricte pour la réponse d'Ollama."""
    est_une_commande: bool = Field(default=True, description="True si le mail contient une intention de commande, sinon False")
    client: str = Field(default="Client Inconnu")
    montant_total: float = Field(default=0.0)
    urgente: bool = Field(default=False)
    articles: List[ArticleSchema] = Field(default_factory=list)