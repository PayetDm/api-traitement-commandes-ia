import os
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# ==========================================
# 1. DÉFINITION DES VARIABLES D'ENV DE TEST
# (DOIT ÊTRE FAIT AVANT LES IMPORTS DE L'APP)
# ==========================================
os.environ["READER_API_KEY"] = "test_reader_key"
os.environ["OPERATOR_API_KEY"] = "test_operator_key"
os.environ["ADMIN_API_KEY"] = "test_admin_key"

from app.database import Base, get_db
from app.main import app

# Base de données SQLite isolée en mémoire pour les tests
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine_test = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine_test
)


@pytest.fixture(autouse=True)
def setup_test_db():
    """Crée les tables en mémoire avant chaque test et les nettoie après."""
    Base.metadata.create_all(bind=engine_test)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    # Redirection de la dépendance BDD de FastAPI vers la BDD de test
    app.dependency_overrides[get_db] = override_get_db

    yield

    Base.metadata.drop_all(bind=engine_test)
    app.dependency_overrides.clear()


client = TestClient(app)

# --- Headers de test ---
HEADERS_READER = {"X-API-Key": "test_reader_key"}
HEADERS_OPERATOR = {"X-API-Key": "test_operator_key"}


# ==========================================
# LES TESTS
# ==========================================

# Le patch pointe désormais vers le routeur où la fonction est réellement appelée
@patch("app.routers.commandes.analyser_mail_avec_llm")
def test_analyser_commande_asynchrone(mock_ollama):
    mock_ollama.return_value = {
        "client": "Jean Dupont",
        "numero_commande": "CMD123",
        "montant_total_eur": 150.0,
        "statut_livraison": "urgent",
        "articles": [
            {"nom": "Clavier RGB", "quantite": 1, "prix_unitaire": 150.0}
        ],
    }

    payload = {
        "contenu_email": "Commande urgente de Jean Dupont pour 1 Clavier RGB a 150 euros."
    }
    # <-- Utilisation de la clé OPERATOR (car la route est protégée par OPERATOR)
    response = client.post("/commandes/analyser", json=payload, headers=HEADERS_OPERATOR)

    assert response.status_code == 202
    data = response.json()
    assert data["statut"] == "en_cours"


def test_analyser_commande_sans_cle_api():
    """Vérifie que l'accès est refusé sans clé API."""
    payload = {"contenu_email": "Mail sans autorisation."}
    response = client.post("/commandes/analyser", json=payload)
    assert response.status_code == 401


def test_lire_commande_non_trouvee():
    """La lecture nécessite le rôle READER."""
    response = client.get(
        "/commandes/99999", 
        headers=HEADERS_READER
    )
    assert response.status_code == 404


def test_lister_commandes_sans_cle_api():
    """Les données métier ne doivent pas être accessibles anonymement."""
    response = client.get("/commandes")
    assert response.status_code == 401


def test_stats_sans_cle_api():
    """Les indicateurs ne doivent pas être accessibles anonymement."""
    response = client.get("/stats")
    assert response.status_code == 401


def test_classification_sans_cle_api():
    """Le moteur IA ne doit pas être utilisable anonymement."""
    response = client.post("/ai/classify", json={"text": "test"})
    assert response.status_code == 401


def test_health_check():
    """Vérifie la route de santé de l'API."""
    response = client.get("/health")
    assert response.status_code == 200
    # <-- CORRIGÉ : c'est "status" avec un S, pas "statut"
    assert response.json() == {"status": "ok"}