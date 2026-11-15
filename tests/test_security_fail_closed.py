import pytest
from fastapi.routing import APIRoute
from app.main import app

# Liste blanche des routes qui n'ont PAS besoin d'être protégées
PUBLIC_ROUTES = {
    "/health",
    "/",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/docs/oauth2-redirect",
}

def test_all_routes_are_protected():
    """
    Test de sécurité 'Fail-Closed'.
    Vérifie que chaque route de l'API (sauf exceptions) exige une authentification.
    """
    unprotected_routes = []

    # On parcourt toutes les routes de l'application
    for route in app.routes:
        if isinstance(route, APIRoute):
            # Si la route est dans la liste blanche, on l'ignore
            if route.path in PUBLIC_ROUTES:
                continue
            
            # On vérifie si la route a une dépendance de sécurité
            has_security = False
            
            # On inspecte les dépendances de la route
            # FastAPI stocke les dépendances de sécurité dans route.dependant.security_requirements
            if route.dependant.security_requirements:
                has_security = True
            else:
                # On vérifie aussi les sous-dépendances (ex: require_role)
                for dep in route.dependant.dependencies:
                    if dep.security_requirements:
                        has_security = True
                        break
                    for sub_dep in dep.dependencies:
                        if sub_dep.security_requirements:
                            has_security = True
                            break

            if not has_security:
                unprotected_routes.append(f"{route.methods} {route.path}")

    # Si la liste n'est pas vide, le test échoue et affiche les routes oubliées
    assert not unprotected_routes, (
        f"🚨 FAILLE DE SÉCURITÉ : Les routes suivantes n'ont pas de protection RBAC : {unprotected_routes}"
    )