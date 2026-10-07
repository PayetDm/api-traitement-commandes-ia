from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

StatutCommande = Literal[
    "en_attente",
    "traitee",
    "expediee",
    "transfere_sav",
    "transfere_service_client",
    "erreur_technique",
]

# --- Schémas pour la lecture des Articles et Commandes ---

class ArticleSchema(BaseModel):
    nom: str = Field(min_length=1, max_length=200)
    quantite: int = Field(ge=1, le=100000)
    prix_unitaire: float = Field(ge=0, le=10000000, allow_inf_nan=False)


class CommandeSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client: str = Field(min_length=1, max_length=200)
    message_id: Optional[str] = None
    contenu_email: Optional[str] = None
    email_client: Optional[str] = Field(default=None, max_length=320)
    montant_total: float = Field(ge=0, le=100000000, allow_inf_nan=False)
    urgente: bool
    statut: StatutCommande
    articles: List[ArticleSchema] = Field(default_factory=list)

# --- Schémas pour les requêtes entrantes (Input) ---

class EmailIn(BaseModel):
    contenu_email: str = Field(min_length=1, max_length=10000)


class CommandeStatutUpdate(BaseModel):
    statut: StatutCommande


class CommandeIAOutput(BaseModel):
    """Schéma de validation stricte pour la réponse d'Ollama."""
    est_une_commande: bool = Field(default=True, description="True si le mail contient une intention de commande, sinon False")
    client: str = Field(default="Client Inconnu", max_length=200)
    montant_total: float = Field(default=0.0, ge=0, le=100000000, allow_inf_nan=False)
    urgente: bool = Field(default=False)
    articles: List[ArticleSchema] = Field(default_factory=list)


class RedirectionInput(BaseModel):
    """Payload pour rediriger un dossier vers une autre catégorie."""
    nouvelle_categorie: Literal["commande", "sav", "service_client"]
    ancienne_categorie: Optional[str] = None