import json
import logging
import requests

# Configuration du logger pour ce module
logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODELE_IA = "qwen2.5-coder:3b"


def analyser_mail_avec_llm(texte_email: str) -> dict:
    prompt = f"""
    Tu es un assistant d'extraction de donnees.
    Analyse le texte de l'e-mail suivant et extrait les informations au format JSON strict avec les clefs :
    - client (chaine de caracteres)
    - numero_commande (chaine de caracteres)
    - montant_total_eur (nombre flottant)
    - statut_livraison (chaine : "urgent" ou "normal")
    - articles (liste d'objets avec : nom, quantite, prix_unitaire)

    Texte de l'e-mail :
    \"\"\"{texte_email}\"\"\"

    Reponds UNIQUEMENT avec le JSON, sans texte d'introduction ni explications.
    """

    payload = {
        "model": MODELE_IA,
        "prompt": prompt,
        "stream": False,
        "format": "json",
    }

    try:
        logger.info("Envoi de la requete a Ollama...")
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        response.raise_for_status()

        resultat = response.json()
        contenu_json = json.loads(resultat.get("response", "{}"))
        logger.info("Analyse IA terminee avec succes.")
        return contenu_json

    except requests.exceptions.RequestException as e:
        logger.error("Erreur de communication avec Ollama : %s", e)
        return {}
    except json.JSONDecodeError as e:
        logger.error("Erreur de decodage du JSON renvoye par l'IA : %s", e)
        return {}