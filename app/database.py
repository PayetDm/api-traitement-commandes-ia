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