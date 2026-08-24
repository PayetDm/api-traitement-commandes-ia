import json
import requests
import os
from fastapi import HTTPException, status


def analyser_mail_avec_llm(texte: str) -> dict:
    """Service dédié à l'interaction avec le modèle Ollama."""
    # Récupère l'adresse via l'environnement Docker, ou prends localhost par défaut
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    url = f"{ollama_host}/api/generate"

    prompt = f"""
    Tu es un assistant d'extraction de données de commandes.
    Analyse ce texte et réponds EXCLUSIVEMENT avec un objet JSON structuré comme suit :
    {{
        "client": "Nom du client",
        "numero_commande": "Code ou numéro identifié",
        "montant_total_eur": 0.0,
        "articles": [
            {{"nom": "Nom produit", "quantite": 1, "prix_unitaire": 0.0}}
        ],
        "statut_livraison": "urgent" ou "normal"
    }}

    Texte à analyser :
    {texte}
    """

    try:
        response = requests.post(
            url,
            json={
                "model": "qwen2.5-coder:3b",
                "prompt": prompt,
                "format": "json",
                "stream": False,
            },
            timeout=30,
        )
        response.raise_for_status()
        resultat_raw = response.json().get("response", "{}")
        return json.loads(resultat_raw)

    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Ollama ne répond pas (timeout).",
        )
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Erreur lors de la communication avec l'IA : {e}",
        )