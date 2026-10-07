import base64
import logging
import requests
from sqlalchemy.orm import Session

from app.database import sauvegarder_commande
from app.services import analyser_mail_avec_llm

logger = logging.getLogger(__name__)

MAILHOG_API_URL = "http://service_mailhog:8025/api/v2/messages"
MAILHOG_DELETE_URL = "http://service_mailhog:8025/api/v1/messages"


def decoder_corps_mail(msg: dict) -> str:
    """Extrait et décode le corps du message selon son encodage."""
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
    """Extrait l'adresse e-mail de l'expéditeur depuis la structure MailHog."""
    from_data = msg.get("From", {})

    mailbox = from_data.get("Mailbox", "")
    domain = from_data.get("Domain", "")

    if mailbox and domain:
        return f"{mailbox}@{domain}"

    headers = msg.get("Content", {}).get("Headers", {})
    from_header = headers.get("From", [""])
    if from_header and from_header[0]:
        return from_header[0]

    return "client.inconnu@exemple.com"


def _statut_depuis_categorie(categorie: str) -> str:
    """Convertit la catégorie IA en statut de commande."""
    mapping = {
        "commande": "en_attente",
        "sav": "transfere_sav",
        "service_client": "transfere_service_client",
    }
    return mapping.get(categorie, "transfere_service_client")


def relever_et_traiter_emails(db: Session):
    """Récupère les e-mails MailHog, les analyse et les enregistre."""
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

            # --- ANALYSE LLM (extraction + classification) ---
            logger.info("Envoi du contenu du mail à Ollama pour structuration...")
            data_llm = analyser_mail_avec_llm(corps_mail)

            # Utilise le nom extrait par le LLM, fallback sur l'email
            client_final = data_llm.get("client") or expediteur

            donnees_commande = {
                "client": client_final,
                "message_id": msg_id,
                "contenu_email": corps_mail,
                "email_client": expediteur,
                "montant_total": data_llm.get("montant_total", 0.0),
                "urgente": data_llm.get("urgente", False) or ("URGENT" in sujet.upper()),
                "statut": _statut_depuis_categorie(data_llm.get("categorie", "autre")),
                "articles": data_llm.get("articles", []),
            }

            sauvegarder_commande(db, donnees_commande)
            logger.info(
                f"Commande de {client_final} enregistrée ({donnees_commande['statut']})"
            )

            # Suppression du message dans MailHog
            if msg_id:
                res_del = requests.delete(f"{MAILHOG_DELETE_URL}/{msg_id}", timeout=5)
                if res_del.status_code == 200:
                    logger.info(f"E-mail {msg_id} supprimé de MailHog.")

    except Exception as e:
        logger.error(f"Erreur pendant l'exécution du service mail : {str(e)}")