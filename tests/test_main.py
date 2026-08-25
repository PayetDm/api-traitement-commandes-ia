from unittest.mock import patch
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app
from app.security import SECRET_API_KEY

Base.metadata.create_all(bind=engine)

client = TestClient(app)


@patch("app.main.analyser_mail_avec_llm")
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

    # On passe la clé API valide dans les headers
    headers = {"X-API-Key": SECRET_API_KEY}
    response = client.post("/commandes/analyser", json=payload, headers=headers)

    assert response.status_code == 202
    data = response.json()
    assert data["statut"] == "en_cours"


def test_analyser_commande_sans_cle_api():
    """Vérifie que l'accès est refusé sans clé API."""
    payload = {"contenu_email": "Mail sans autorisation."}
    response = client.post("/commandes/analyser", json=payload)
    assert response.status_code == 401


def test_lire_commande_non_trouvee():
    response = client.get("/commandes/999999")
    assert response.status_code == 404


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"statut": "ok", "base_de_donnees": "connectee"}