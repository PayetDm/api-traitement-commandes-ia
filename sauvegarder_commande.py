import json
import sqlite3
import requests


# 1. INITIALISATION DE LA BASE DE DONNÉES SQLITE
def initialiser_bdd():
    """Crée la table 'commandes' dans la base de données si elle n'existe pas déjà."""
    conn = sqlite3.connect("commandes.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS commandes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_commande TEXT UNIQUE,
            client TEXT,
            montant_total REAL,
            urgence TEXT,
            articles_json TEXT,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    conn.commit()
    conn.close()


# 2. EXTRACTION VIA LLM (Ollama)
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


# 3. INSERTION DANS SQLITE
def enregistrer_en_bdd(donnees: dict):
    """Insère la commande structurée dans le fichier SQLite 'commandes.db'."""
    if not donnees:
        print("❌ Aucune donnée à enregistrer.")
        return

    conn = sqlite3.connect("commandes.db")
    cursor = conn.cursor()

    try:
        # Conversion de la liste des articles en texte JSON pour le stockage SQL
        articles_str = json.dumps(donnees.get("articles", []))

        cursor.execute(
            """
            INSERT INTO commandes (numero_commande, client, montant_total, urgence, articles_json)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                donnees.get("numero_commande"),
                donnees.get("client"),
                donnees.get("montant_total_eur"),
                donnees.get("statut_livraison"),
                articles_str,
            ),
        )

        conn.commit()
        print(
            f"✅ Commande {donnees.get('numero_commande')} enregistrée avec succès dans SQLite !"
        )

    except sqlite3.IntegrityError:
        print(
            f"⚠️ La commande {donnees.get('numero_commande')} existe déjà en BDD."
        )
    finally:
        conn.close()


# 4. LECTURE / VÉRIFICATION
def afficher_commandes_bdd():
    """Lit et affiche toutes les commandes enregistrées dans SQLite."""
    conn = sqlite3.connect("commandes.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, numero_commande, client, montant_total, urgence, articles_json FROM commandes"
    )
    lignes = cursor.fetchall()

    print("\n📊 --- CONTENU DE LA BASE DE DONNÉES SQLITE ---")
    for ligne in lignes:
        id_cmd, num, client, total, urgence, articles_raw = ligne
        articles = json.loads(articles_raw)
        print(
            f"\n[ID {id_cmd}] Commande {num} | Client : {client} | Total : {total}€ | Urgence : {urgence}"
        )
        print("  Articles :")
        for art in articles:
            print(
                f"   - {art.get('quantite')}x {art.get('nom')} à {art.get('prix_unitaire')}€/u"
            )

    conn.close()


# --- EXÉCUTION DU PIPELINE ---
if __name__ == "__main__":
    # Étape A: Créer le fichier .db et la table s'ils n'existent pas
    initialiser_bdd()

    # Étape B: Un mail de test entrant
    email_entrant = """
    Bonjour,
    Commande de Damien Payet suite au devis CMD-2026-892.
    Je prends 2 panneaux de chêne massif à 45.00€ l'unité et 1 lot de charnières inox à 12.50€.
    Livraison urgente s'il vous plaît.
    Total : 102.50€.
    """

    print("⏳ 1. Extraction des données par le LLM...")
    donnees_extraites = extraire_donnees_commande(email_entrant)

    print("💾 2. Enregistrement dans SQLite...")
    enregistrer_en_bdd(donnees_extraites)

    # Étape C: Vérification du contenu stocké
    afficher_commandes_bdd()