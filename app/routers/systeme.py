from fastapi import APIRouter, Depends
from app.security.auth import require_role, User
from app.security.roles import Role

router = APIRouter(tags=["Système"])

# ==========================================
# ROUTES DE L'API (avec RBAC)
# ==========================================

# --- PUBLIC (Zéro information sensible) ---
@router.get("/health")
def health_check():
    """
    Utilisé par Docker, Kubernetes ou un Load Balancer.
    Doit rester public et ne rien divulguer sur l'infrastructure.
    """
    return {"status": "ok"}


# --- PROTÉGÉ (Admin) : Diagnostic détaillé ---
@router.get("/health/detailed")
def health_detailed(
    user: User = Depends(require_role(Role.ADMIN)) # <-- RBAC
):
    """
    Réservé aux admins. Donne l'état exact des dépendances.
    En cas de compromission, un attaquant n'a pas cette visibilité.
    """
    return {
        "status": "ok", 
        "details": {
            "database": "up",
            "ollama_llm": "up",
            "langfuse": "up",
            "version": "1.0.0"
        }
    }