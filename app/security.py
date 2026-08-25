import os
from dotenv import load_dotenv
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

# Charge les variables définies dans le fichier .env
load_dotenv()

# Nom du header HTTP attendu
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Récupère la clé depuis le .env, avec une clé de fallback
SECRET_API_KEY = os.getenv("API_KEY", "mon-secret-super-securise")


def verifier_cle_api(api_key: str = Security(api_key_header)):
    """Dépendance FastAPI pour valider la clé API présente dans le header."""
    if api_key == SECRET_API_KEY:
        return api_key

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Clé API invalide ou manquante.",
    )