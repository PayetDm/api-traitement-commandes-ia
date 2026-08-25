import json
import logging
import requests
from app.schemas import CommandeIAOutput

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODELE_IA = "qwen2.5-coder:3b"


def analyser_mail_avec_llm(texte_email: str) -> dict:
    prompt = f"""
    Tu es un assistant de tri et d'extraction de données.
    Analyse le texte de l'e-mail suivant et extrais les informations au format JSON strict avec les clefs :
    - est_une_commande (booleen : true si c'est une intention d'achat/commande, false sinon)
    - client (chaine de caracteres)
    - montant_total (nombre flottant)
    - urgente (booleen)
    - articles (liste d'objets avec : nom, quantite, prix_unitaire)

    Texte de l'e-mail :
    \"\"\"{texte_email}\"\"\"

    Reponds UNIQUEMENT avec le JSON valide, sans texte d'introduction ni explications.
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
        raw_json = json.loads(resultat.get("response", "{}"))
        
        # 1. Validation Pydantic Stricte
        data_validee = CommandeIAOutput(**raw_json)
        data_dict = data_validee.model_dump()

        # 2. Gardien Python (Correction des faux positifs du LLM)
        if data_dict["est_une_commande"] and len(data_dict["articles"]) == 0 and data_dict["montant_total"] == 0.0:
            logger.info("Gardien Python : Redirection SAV (aucun article ni montant).")
            data_dict["est_une_commande"] = False

        logger.info("Analyse IA terminee avec succes.")
        return data_dict

    except requests.exceptions.RequestException as e:
        logger.error("Erreur HTTP/Ollama : %s", e)
        return {"est_une_commande": False, "client": "Erreur Ollama"}
    except Exception as e:
        logger.error("Erreur lors du parsing du JSON IA : %s", e)
        return {"est_une_commande": False, "client": "Message non structuré (SAV)", "articles": [], "montant_total": 0.0}