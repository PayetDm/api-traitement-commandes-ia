from unittest.mock import patch
from fastapi.testclient import TestClient
import pytest

from app.main import app

# Mock de la réponse du service LLM pour isoler le test
MOCK_OLLAMA_RESPONSE = {
    "numero_commande": "CMD-999",
    "client": "Damien Test",
    "montant_total_eur": 120.0,
    "statut_livraison": "express",
    "articles": [{"nom": "Étagère chêne", "quantite": 1, "prix_unitaire": 120.0}],
}


def test_analyser_commande_succes():
    """Vérifie qu'un mail valide renvoie un statut 201 et enregistre la commande."""
    with patch("app.main.analyser_mail_avec_llm", return_value=MOCK_OLLAMA_RESPONSE):
        # Utilisation de 'with TestClient' pour activer le lifespan et exécuter init_db()
        with TestClient(app) as client:
            response = client.post(
                "/commandes/analyser",
                json={
                    "texte_email": "Bonjour, commande CMD-999 pour Damien Test : 1 étagère chêne à 120 euros."
                },
            )

            assert response.status_code == 201
            data = response.json()
            assert data["numero_commande"] == "CMD-999"
            assert data["client"] == "Damien Test"
            assert data["montant_total"] == 120.0


def test_analyser_commande_payload_invalide():
    """Vérifie qu'un texte trop court (<10 caractères) est rejeté avec un code 422."""
    with TestClient(app) as client:
        response = client.post(
            "/commandes/analyser",
            json={"texte_email": "Court"},
        )
        assert response.status_code == 422


def test_lire_commande_inexistante():
    """Vérifie qu'un ID inconnu renvoie un statut 404."""
    with TestClient(app) as client:
        response = client.get("/commandes/999999")
        assert response.status_code == 404