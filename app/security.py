import logging
import os
import secrets
from dotenv import load_dotenv
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

logger = logging.getLogger(__name__)

# Charge les variables du fichier .env
load_dotenv()

# Nom du header HTTP attendu
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


def verifier_cle_api(api_key: str = Security(api_key_header)):
    """Dépendance FastAPI pour valider la clé API présente dans le header."""
    cle_attendue = os.getenv("API_KEY")

    if not cle_attendue:
        logger.critical("API_KEY n'est pas configurée.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentification indisponible.",
        )

    # Si le client n'a pas fourni de clé dans le header
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="En-tête X-API-Key manquant.",
        )

    # Comparaison sécurisée en temps constant contre les timing attacks
    if not secrets.compare_digest(api_key, cle_attendue):
        logger.warning("Tentative d'accès non autorisée avec une clé API invalide.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Clé API invalide.",
        )

    return api_key