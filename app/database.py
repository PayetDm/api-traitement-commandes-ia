import sqlite3
from fastapi import HTTPException, status

DATABASE = "commandes.db"


def get_db():
    """Gère la connexion à la base SQLite."""
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur BDD : {e}",
        )

def init_db():
    """Crée la table commandes automatiquement si elle n'existe pas."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS commandes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_commande TEXT,
            client TEXT,
            montant_total REAL,
            urgence TEXT,
            articles TEXT,
            date_creation DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()