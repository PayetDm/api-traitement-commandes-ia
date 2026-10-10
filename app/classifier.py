import os
import re
import unicodedata
from enum import Enum
import httpx
import logging
from langfuse import observe, get_client

import nltk
nltk.download('snowball_data', quiet=True)
from nltk.stem.snowball import FrenchStemmer

logger = logging.getLogger(__name__)

stemmer = FrenchStemmer()


# ============================================================
# Catégories d'emails
# ============================================================

class TypeEmail(str, Enum):
    COMMANDE = "commande"
    SAV = "sav"
    SERVICE_CLIENT = "service_client"
    AUTRE = "autre"


# ============================================================
# Dictionnaires de mots-clés métier (bricolage)
# ⚠️ Les mots sont en forme "stemmée" (racine)
# ============================================================

MOTS_COMMANDE = {
    stemmer.stem(mot) for mot in {
        "acheter", "achat", "commande", "commander", "livraison",
        "produit", "article", "facture", "paiement", "confirmation",
        "reception", "expedition", "suivi", "panier", "tarifs", "prix",
        "devis", "disponibilite", "stock", "catalogue", "reference",
    }
}

MOTS_SAV = {
    stemmer.stem(mot) for mot in {
        "defaut", "casse", "dysfonctionnement", "garantie",
        "panne", "endommage", "defectueux", "brise", "hs",
        "hors service", "defaillant",
    }
}

MOTS_SERVICE_CLIENT = {
    stemmer.stem(mot) for mot in {
        "retour", "remboursement", "echange", "annulation", "annuler",
        "reclamation", "probleme", "erreur", "renseignement", "information",
        "question", "aide", "conseil", "avis", "satisfaction",
        "mecontentement", "perdu",
    }
}

MOTS_LOGISTIQUE = {
    stemmer.stem(mot) for mot in {
        "retard", "colis", "tourne", "tracking",
    }
}

MOTS_PRODUIT = {
    stemmer.stem(mot) for mot in {
        "perceuse", "visseuse", "meuleuse", "scie", "ponceuse",
        "marteau", "tournevis", "cle", "pince", "rape",
        "peinture", "pinceau", "rouleau", "enduit", "colle",
        "vis", "boulon", "clou", "cheville", "ecrou",
        "cable", "rallonge", "multiprise", "ampoule", "led",
        "echelle", "escabeau", "etabli", "etagere", "rangement",
        "gant", "lunette", "casque", "masque", "protection",
    }
}


# ============================================================
# Utilitaires
# ============================================================

RE_MOTS = re.compile(r"[a-z0-9]+")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://service_ollama:11434")
MODEL_NAME = os.getenv("OLLAMA_MODEL", "llama3.2:3b")


def _normaliser(texte: str) -> str:
    """
    Normalisation robuste pour le français :
    1. Décompose les accents (NFKD)
    2. Supprime les diacritiques
    3. Met en minuscules
    4. Réduit les voyelles doublées (ee → e, aa → a, etc.)
       pour que "cassée" (→ "cassee") redevienne "casse".
    """
    texte_sans_accents = unicodedata.normalize("NFKD", texte)
    texte_sans_accents = "".join(
        caractere for caractere in texte_sans_accents if not unicodedata.combining(caractere)
    )
    texte_sans_accents = texte_sans_accents.lower()
    # Réduction des voyelles doublées (gestion des accents composés)
    texte_sans_accents = re.sub(r'([aeiou])\1', r'\1', texte_sans_accents)
    return texte_sans_accents


def _extraire_stems(texte: str) -> set[str]:
    """Extrait les mots du texte ET les réduit à leur racine (stemming)."""
    texte_normalise = _normaliser(texte)
    mots = RE_MOTS.findall(texte_normalise)
    return {stemmer.stem(mot) for mot in mots}


# ============================================================
# Classification par règles (déterministe)
# ============================================================

def classer_email_par_regles(texte: str) -> TypeEmail:
    """
    Classification par règles déterministes, dans l'ordre de priorité :
    1. SAV (technique produit)
    2. Service Client (relationnel)
    3. Commande (achat / logistique)
    4. AUTRE (fallback)
    """
    if not isinstance(texte, str) or not texte.strip():
        raise ValueError("Le texte de l'e-mail doit être une chaîne non vide.")

    stems = _extraire_stems(texte)

    # RÈGLE SPÉCIALE : "probleme" + mot produit → SAV
    if "problem" in stems and (stems & MOTS_PRODUIT):
        return TypeEmail.SAV

    # 1. SAV (technique)
    if stems & MOTS_SAV:
        return TypeEmail.SAV

    # 2. Service Client (relationnel)
    if stems & MOTS_SERVICE_CLIENT:
        return TypeEmail.SERVICE_CLIENT

    # 3. Commande (achat ou logistique)
    if stems & MOTS_COMMANDE:
        return TypeEmail.COMMANDE
    if stems & MOTS_LOGISTIQUE:
        return TypeEmail.COMMANDE

    # 4. Fallback
    return TypeEmail.AUTRE


# ============================================================
# Classification via LLM (Ollama)
# ============================================================

@observe(name="classer_email_avec_llm")
async def classer_email_avec_llm(texte: str) -> str:
    """Classification via Ollama. En cas d'échec, lève une exception."""
    langfuse = get_client()
    langfuse.update_current_span(
        metadata={"model_used": MODEL_NAME, "provider": "ollama"}
    )

    async with httpx.AsyncClient(timeout=30.0) as client:
        prompt_content = (
            "Tu es un classificateur d'e-mails strict. Analyse le texte ci-dessous et "
            "réponds UNIQUEMENT par un de ces quatre mots exacts : "
            "commande, sav, service_client, ou autre. "
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


# ============================================================
# Classification hybride (règles + LLM + fallback fail-safe)
# ============================================================

@observe(name="classification_hybride")
async def classer_email_hybride(texte: str) -> tuple[str, str]:
    """
    Classifie l'email.
    Retourne (categorie, method).
    """
    categorie = classer_email_par_regles(texte)

    if categorie != TypeEmail.AUTRE:
        method = "deterministic_rules"
        res = categorie.value
    else:
        try:
            res = await classer_email_avec_llm(texte)
            method = "ollama_llm"
        except Exception as e:
            logger.warning(
                f"LLM indisponible, fallback fail-safe sur 'autre' : {e}"
            )
            res = "autre"
            method = "llm_unavailable_fallback"

    langfuse = get_client()
    langfuse.update_current_span(
        metadata={"classification_method": method}
    )
    langfuse.flush()

    return res, method