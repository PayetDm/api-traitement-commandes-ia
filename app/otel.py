import os
import logging
from langfuse import get_client

logger = logging.getLogger(__name__)

LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "http://service_langfuse:3000")
LANGFUSE_ENABLED = os.getenv("LANGFUSE_ENABLED", "true").lower() == "true"

langfuse_client = None


def setup_langfuse(app=None):
    global langfuse_client

    if not LANGFUSE_ENABLED:
        logger.info("Langfuse désactivé via LANGFUSE_ENABLED.")
        return None

    if not LANGFUSE_PUBLIC_KEY or not LANGFUSE_SECRET_KEY:
        logger.warning("Langfuse activé mais clés d'API manquantes.")
        return None

    # Configuration des variables d'environnement lues par get_client()
    os.environ["LANGFUSE_PUBLIC_KEY"] = LANGFUSE_PUBLIC_KEY
    os.environ["LANGFUSE_SECRET_KEY"] = LANGFUSE_SECRET_KEY
    os.environ["LANGFUSE_HOST"] = LANGFUSE_HOST

    try:
        # get_client() instancie le singleton et le mémorise
        langfuse_client = get_client()
        logger.info(f"Langfuse configuré sur {LANGFUSE_HOST}")
        return langfuse_client
    except Exception as e:
        logger.error(f"Erreur init Langfuse : {e}", exc_info=True)
        return None


def flush_langfuse():
    global langfuse_client
    try:
        if langfuse_client:
            langfuse_client.flush()
        else:
            get_client().flush()
        logger.info("Flush Langfuse exécuté.")
    except Exception as e:
        logger.error(f"Erreur flush Langfuse : {e}", exc_info=True)