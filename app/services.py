import asyncio
import json
import logging
import os

import requests

from app.classifier import classer_email_hybride
from app.schemas import CommandeIAOutput

try:
    from langfuse import get_client, observe
except ImportError:  # Permet de lancer l'API avant l'installation des dépendances.
    get_client = None
    observe = None

logger = logging.getLogger(__name__)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
if not OLLAMA_URL.endswith("/api/generate"):
    OLLAMA_URL = f"{OLLAMA_URL.rstrip('/')}/api/generate"
MODELE_IA = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
LANGFUSE_ENABLED = os.getenv("LANGFUSE_ENABLED", "false").lower() == "true"
LANGFUSE_CONFIGURED = bool(
    os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")
)
LANGFUSE_CLIENT = (
    get_client()
    if LANGFUSE_ENABLED and LANGFUSE_CONFIGURED and get_client is not None
    else None
)


def _observe_analyse(fonction):
    if observe is None or LANGFUSE_CLIENT is None:
        return fonction
    return observe(
        name="analyser_mail_avec_llm",
        as_type="generation",
        capture_input=True,
        capture_output=True,
    )(fonction)


def _classifier_email(texte_email: str) -> tuple[str, str | None]:
    """
    Classifie l'email en 4 catégories.
    Retourne (categorie, langfuse_trace_id).
    """
    try:
        # Récupère le client Langfuse AVANT l'appel pour capturer l'ID de trace
        from langfuse import get_client
        langfuse = get_client()
        
        categorie = asyncio.run(classer_email_hybride(texte_email))
        logger.info("Classification IA : %s", categorie)
        
        # Récupère l'ID de la trace courante
        trace_id = None
        try:
            current_trace = langfuse.get_current_trace_id()
            trace_id = current_trace
            logger.debug("Trace Langfuse : %s", trace_id)
        except Exception as e:
            logger.debug("Impossible de récupérer l'ID de trace : %s", e)
        
        if categorie == "autre":
            return "service_client", trace_id
        return categorie, trace_id
    except Exception as e:
        logger.warning(
            "Echec de la classification, fallback sur 'service_client' : %s", e
        )
        return "service_client", None
    

def _nettoyer_json_llm(raw: dict) -> dict:
    """
    Nettoie le JSON renvoyé par le LLM avant validation Pydantic.
    Corrige les valeurs invalides (None, manquantes, hors bornes).
    """
    corrections = []

    articles = raw.get("articles", [])
    for i, article in enumerate(articles):
        if not isinstance(article, dict):
            articles[i] = {"nom": "Article non identifié", "quantite": 1, "prix_unitaire": 0.0}
            corrections.append(f"article #{i} non-dict remplacé")
            continue

        if not article.get("nom"):
            article["nom"] = "Article non identifié"
            corrections.append(f"article #{i} nom manquant")

        if article.get("quantite") is None:
            article["quantite"] = 1
            corrections.append(f"article #{i} quantite=None → 1")
        elif not isinstance(article["quantite"], int):
            try:
                article["quantite"] = int(article["quantite"])
            except (ValueError, TypeError):
                article["quantite"] = 1
                corrections.append(f"article #{i} quantite invalide → 1")

        if article.get("prix_unitaire") is None:
            article["prix_unitaire"] = 0.0
            corrections.append(f"article #{i} prix=None → 0.0")
        elif not isinstance(article["prix_unitaire"], (int, float)):
            try:
                article["prix_unitaire"] = float(article["prix_unitaire"])
            except (ValueError, TypeError):
                article["prix_unitaire"] = 0.0
                corrections.append(f"article #{i} prix invalide → 0.0")

    if corrections:
        logger.warning(
            "Corrections appliquées au JSON LLM : %s", " | ".join(corrections)
        )

    return raw

@_observe_analyse
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
    {texte_email}

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
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()

        resultat = response.json()
        raw_json = json.loads(resultat.get("response", "{}"))
        raw_json = _nettoyer_json_llm(raw_json)
        data_validee = CommandeIAOutput(**raw_json)
        
        data_dict = data_validee.model_dump()

        if (
            data_dict["est_une_commande"]
            and not data_dict["articles"]
            and data_dict["montant_total"] == 0.0
        ):
            logger.info("Gardien Python : Redirection SAV (aucun article ni montant).")
            data_dict["est_une_commande"] = False

        # Classification via le classifieur hybride (règles + stemming + LLM)
        categorie, trace_id = _classifier_email(texte_email)
        data_dict["categorie"] = categorie
        data_dict["langfuse_trace_id"] = trace_id

        logger.info("Analyse IA terminee avec succes.")
        return data_dict
    except requests.exceptions.RequestException as error:
        logger.error("Erreur HTTP/Ollama : %s", error)
        return {
            "est_une_commande": False,
            "client": "Erreur Ollama",
            "categorie": "service_client",
        }
    except Exception as error:
        logger.error("Erreur lors du parsing du JSON IA : %s", error)
        return {
            "est_une_commande": False,
            "client": "Message non structure (SAV)",
            "articles": [],
            "montant_total": 0.0,
            "categorie": "service_client",
        }