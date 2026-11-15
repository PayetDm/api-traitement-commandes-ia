import logging
import os
import secrets
from dataclasses import dataclass

from dotenv import load_dotenv
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.security.roles import Role

logger = logging.getLogger(__name__)
load_dotenv()

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


@dataclass(frozen=True)
class User:
    """Représente l'utilisateur authentifié."""
    role: Role


# On fait le lien entre la variable d'environnement et le rôle
ROLE_MAPPING = {
    os.getenv("READER_API_KEY"): Role.READER,
    os.getenv("OPERATOR_API_KEY"): Role.OPERATOR,
    os.getenv("ADMIN_API_KEY"): Role.ADMIN,
}


def get_current_user(api_key: str = Security(api_key_header)) -> User:
    """
    Dépendance FastAPI pour l'authentification (AuthN).
    Vérifie la clé API et retourne un objet User avec son rôle.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="En-tête X-API-Key manquant.",
        )

    # On parcourt le dictionnaire de correspondance
    for cle_attendue, role in ROLE_MAPPING.items():
        # Si la clé n'est pas configurée dans le .env, on ignore
        if not cle_attendue:
            continue
            
        # Comparaison sécurisée
        if secrets.compare_digest(api_key, cle_attendue):
            return User(role=role)

    # Si aucune clé ne correspond, on rejette (Fail-Closed)
    logger.warning("Tentative d'accès avec une clé API inconnue.")
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Clé API invalide.",
    )


def require_role(required_role: Role):
    """
    Factory de dépendance pour l'autorisation (AuthZ).
    Vérifie que l'utilisateur a le niveau requis.
    """
    def role_checker(user: User = Security(get_current_user)) -> User:
        if not user.role.allows(required_role):
            logger.warning(
                f"Accès refusé : rôle {user.role.name} insuffisant "
                f"pour {required_role.name}."
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Privilèges insuffisants.",
            )
        return user

    return role_checker