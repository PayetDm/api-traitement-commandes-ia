from unittest.mock import patch
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app

# Création explicite des tables pour l'environnement de test
Base.metadata.create_all(bind=engine)

client = TestClient(app)


@patch("app.main.analyser_mail_avec_llm")
def test_analyser_commande_succes(mock_ollama):
    # Simulation de la réponse JSON exacte d'Ollama
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

    response = client.post("/commandes/analyser", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["client"] == "Jean Dupont"
    assert data["montant_total"] == 150.0
    assert data["urgente"] is True
    assert len(data["articles"]) == 1


def test_lire_commande_non_trouvee():
    response = client.get("/commandes/999999")
    assert response.status_code == 404