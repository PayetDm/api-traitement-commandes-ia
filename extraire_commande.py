import json
import requests


def extraire_donnees_commande(texte_email: str) -> dict:
    """Analyse un texte de commande et retourne un dictionnaire Python structuré."""
    url = "http://localhost:11434/api/generate"

    prompt = f"""
    Tu es un assistant chargé d'extraire les données d'une commande.
    Analyse le texte et réponds STRICTEMENT au format JSON avec cette structure exacte :
    {{
        "client": "Nom du client",
        "numero_commande": "Numéro identifié",
        "montant_total_eur": 0.0,
        "articles": [
            {{"nom": "Nom produit", "quantite": 0, "prix_unitaire": 0.0}}
        ],
        "statut_livraison": "urgent" ou "normal"
    }}

    Texte à analyser :
    {texte_email}
    """

    payload = {
        "model": "qwen2.5-coder:3b",
        "prompt": prompt,
        "format": "json",
        "stream": False,
    }

    try:
        response = requests.post(url, json=payload, timeout=60)
        if response.status_code == 200:
            contenu = response.json().get("response", "{}")
            return json.loads(contenu)
        else:
            print(f"⚠️ Erreur API : {response.status_code}")
            return {}
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de connexion : {e}")
        return {}


# --- DONNÉES DE TEST ---
email_reçu = """
Bonjour l'équipe,
C'est Damien Payet à l'appareil. Je valide la commande N° CMD-2026-892.
Il me faut 2 panneaux de chêne massif à 45.00€ l'unité et 1 lot de charnières inox à 12.50€.
Merci d'expédier ça en livraison urgente SVP.
Total réglé : 102.50€.
"""

if __name__ == "__main__":
    print("⏳ Extraction automatique des données par l'IA...\n")
    commande = extraire_donnees_commande(email_reçu)

    if commande:
        print("✅ **Données structurées extraites avec succès :**\n")
        print(f"👤 **Client :** {commande.get('client')}")
        print(f"📦 **N° Commande :** {commande.get('numero_commande')}")
        print(f"💳 **Montant total :** {commande.get('montant_total_eur')} €")
        print(f"🚀 **Urgence :** {commande.get('statut_livraison')}")

        print("\n🛒 **Détail du panier :**")
        for article in commande.get("articles", []):
            print(
                f"  • {article.get('quantite')}x {article.get('nom')} ({article.get('prix_unitaire')} €/u)"
            )