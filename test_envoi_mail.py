import smtplib
from email.mime.text import MIMEText

SMTP_SERVER = "localhost"
SMTP_PORT = 1025

def envoyer_faux_mail():
    expediteur = "jean.dupont@societe.com"
    destinataire = "commandes@entreprise.com"
    sujet = "URGENT - Commande de 5 tables et 10 chaises"
    corps = "Bonjour, nous souhaitons commander d'urgence 5 tables en chêne et 10 chaises. Merci !"

    msg = MIMEText(corps)
    msg['Subject'] = sujet
    msg['From'] = expediteur
    msg['To'] = destinataire

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.sendmail(expediteur, [destinataire], msg.as_string())
        print("Mail de test envoyé avec succès à MailHog !")

if __name__ == "__main__":
    envoyer_faux_mail()