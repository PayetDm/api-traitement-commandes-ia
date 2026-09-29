import os
import re
import unicodedata
from enum import Enum
import httpx
import logging
from langfuse import observe, get_client, propagate_attributes

logger = logging.getLogger(__name__)


class TypeEmail(str, Enum):
    COMMANDE = "commande"
    SAV = "sav"
    AUTRE = "autre"


MOTS_COMMANDE = {
    "acheter", "achat", "commande", "commander", "livraison",
    "produit", "quantite", "article", "facture", "paiement",
    "confirmation", "reception", "expedition", "suivi", "panier", "tarifs", "prix",
}

MOTS_SAV = {
    "annulation", "annuler", "defaut", "erreur", "remboursement",
    "retour", "reclamation", "sav", "probleme", "casse",
    "dysfonctionnement", "garantie", "incident", "panne", "retard", "colis", "echange", "endommagé",
}

RE_MOTS = re.compile(r"[a-z0-9]+")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://service_ollama:11434")
MODEL_NAME = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:3b")


def _normaliser(texte: str) -> str:
    texte_sans_accents = unicodedata.normalize("NFKD", texte)
    texte_sans_accents = "".join(
        caractere for caractere in texte_sans_accents if not unicodedata.combining(caractere)
    )
    return texte_sans_accents.lower()


def classer_email_par_regles(texte: str) -> TypeEmail:
    if not isinstance(texte, str) or not texte.strip():
        raise ValueError("Le texte de l'e-mail doit être une chaîne non vide.")

    texte_normalise = _normaliser(texte)
    mots = set(RE_MOTS.findall(texte_normalise))

    score_commande = len(mots & MOTS_COMMANDE)
    score_sav = len(mots & MOTS_SAV)

    if score_sav > 0:
        return TypeEmail.SAV
    if score_commande > 0:
        return TypeEmail.COMMANDE
    return TypeEmail.AUTRE


@observe(name="classer_email_avec_llm")
async def classer_email_avec_llm(texte: str) -> str:
    # Récupération du client pour mettre à jour l'observation en v4
    langfuse = get_client()
    langfuse.update_current_span(
        metadata={"model_used": MODEL_NAME, "provider": "ollama"}
    )

    async with httpx.AsyncClient(timeout=30.0) as client:
        prompt_content = (
            "Tu es un classificateur d'e-mails strict. Analyse le texte ci-dessous et "
            "réponds UNIQUEMENT par un de ses trois mots exacts : commande, sav, ou autre. "
            "Aucune phrase, aucun mot superflu.\n"
            f"Texte : {texte}"
        )
        response = await client.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": MODEL_NAME,
                "prompt": prompt_content,
                "stream": False,
                "options": {"temperature": 0.0}
            }
        )
        response.raise_for_status()
        result = response.json()
        return result.get("response", "autre").strip().lower()


@observe(name="classification_hybride")
async def classer_email_hybride(texte: str) -> str:
    categorie = classer_email_par_regles(texte)

    if categorie != TypeEmail.AUTRE:
        method = "deterministic_rules"
        res = categorie.value
    else:
        # Fallback : si le LLM plante, on retourne "autre" (fail-safe)
        try:
            res = await classer_email_avec_llm(texte)
            method = "ollama_llm"
        except Exception as e:
            logger.warning(
                f"LLM indisponible, fallback fail-safe sur 'autre' : {e}"
            )
            res = "autre"
            method = "llm_unavailable_fallback"

    # Mise à jour de l'observation courante avec la méthode utilisée
    langfuse = get_client()
    langfuse.update_current_span(
        metadata={"classification_method": method}
    )

    # ✅ Force l'envoi immédiat des traces à Langfuse
    langfuse.flush()

    return res