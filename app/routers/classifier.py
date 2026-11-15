from fastapi import APIRouter, Depends
from pydantic import BaseModel
# ... (ajoute ici tes autres imports si besoin, ex: classifier.py)

# --- NOUVEAUX IMPORTS DE SÉCURITÉ (RBAC) ---
from app.security.auth import require_role, User
from app.security.roles import Role

router = APIRouter(tags=["IA"])

class ClassificationInput(BaseModel):
    text: str

# --- PROTÉGÉ (Operator) : Appel direct au LLM ---
@router.post("/ai/classify")
def classifier_texte(
    payload: ClassificationInput,
    user: User = Depends(require_role(Role.OPERATOR)) # <-- RBAC
):
    """
    Route de test/classification. Exige Operator car elle consomme 
    des ressources LLM coûteuses et peut être sujette au DoS.
    """
    # ... (ton code de classification actuel) ...
    # Exemple de retour :
    return {"categorie": "commande", "methode": "regles_deterministes"}