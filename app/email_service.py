import base64
import logging
import requests
from sqlalchemy.orm import Session
from app.database import sauvegarder_commande
from app.llm_service import analyser_commande_avec_llm # Import nvlle fonction

logger = logging.getLogger(__name__)

# URL de l'API de MailHog dans le réseau Docker
MAILHOG_API_URL = "http://service_mailhog:8025/api/v2/messages"
MAILHOG_DELETE_URL = "http://service_mailhog:8025/api/v1/messages"


def decoder_corps_mail(msg: dict) -> str:
    """Extrait et décode le corps du message selon son encodage (Base64 ou texte)."""
    content = msg.get("Content", {})
    body = content.get("Body", "")

    headers = content.get("Headers", {})
    encoding_list = headers.get("Content-Transfer-Encoding", [])
    encoding = encoding_list[0] if encoding_list else ""

    if "base64" in encoding.lower():
        try:
            return base64.b64decode(body).decode("utf-8", errors="ignore")
        except Exception:
            return body

    return body


def extraire_expediteur(msg: dict) -> str:
    """Extrait proprement l'adresse e-mail de l'expéditeur depuis la structure MailHog."""
    from_data = msg.get("From", {})

    # MailHog v2 fournit "Mailbox" et "Domain"
    mailbox = from_data.get("Mailbox", "")
    domain = from_data.get("Domain", "")

    if mailbox and domain:
        return f"{mailbox}@{domain}"

    # Fallback si le header From brut me disponible
    headers = msg.get("Content", {}).get("Headers", {})
    from_header = headers.get("From", [""])
    if from_header and from_header[0]:
        return from_header[0]

    return "client.inconnu@exemple.com"


def relever_et_traiter_emails(db: Session):
    """Récupère les e-mails reçus dans MailHog, enregistre la commande et supprime l'e-mail."""
    try:
        response = requests.get(MAILHOG_API_URL, timeout=5)
        if response.status_code != 200:
            logger.error(
                f"Erreur lors de la récupération des mails MailHog : {response.status_code}"
            )
            return

        data = response.json()
        messages = data.get("items", [])

        if not messages:
            return

        for msg in messages:
            msg_id = msg.get("ID")
            expediteur = extraire_expediteur(msg)
            sujet = msg.get("Content", {}).get("Headers", {}).get("Subject", [""])[0]
            corps_mail = decoder_corps_mail(msg)

            logger.info(f"Nouveau mail détecté de {expediteur} - Sujet: {sujet}")

            # --- INFERENCE MLOps via OLLAMA ---
            logger.info("Envoi du contenu du mail à Ollama pour structuration...")
            resultat_llm = analyser_commande_avec_llm(corps_mail)

            donnees_commande = {
                "client": expediteur,
                "email_client": expediteur,
                "montant_total": 0.0,
                "urgente": "URGENT" in sujet.upper(),
                "statut": "en_attente",
                "articles": [{"texte_raw": corps_mail}],
            }

            # Enregistrement en base de données PostgreSQL
            sauvegarder_commande(db, donnees_commande)
            logger.info(f"Commande de {expediteur} enregistrée en BDD avec succès !")

            # Suppression du message dans MailHog pour éviter qu'il ne soit relu
            if msg_id:
                res_del = requests.delete(f"{MAILHOG_DELETE_URL}/{msg_id}", timeout=5)
                if res_del.status_code == 200:
                    logger.info(f"E-mail {msg_id} supprimé de MailHog.")

    except Exception as e:
        logger.error(
            f"Erreur pendant l'exécution du service mail : {str(e)}"
        )