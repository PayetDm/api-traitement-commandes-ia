import json
import sqlite3
from app.database import get_db
from fastapi import FastAPI, HTTPException, status
from app.models import CommandeOut, EmailIn
from app.services import analyser_mail_avec_llm

app = FastAPI(
    title="API de Traitement de Commandes IA",
    description="Architecture modulaire Backend + Ollama + SQLite",
    version="2.0.0",
)


@app.post(
    "/commandes/analyser",
    response_model=CommandeOut,
    status_code=status.HTTP_201_CREATED,
)
def traiter_et_sauvegarder(payload: EmailIn):
    donnees = analyser_mail_avec_llm(payload.texte_email)

    if not donnees or "numero_commande" not in donnees:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Informations de commande incomplètes.",
        )

    conn = get_db()
    cursor = conn.cursor()

    try:
        articles_json = json.dumps(donnees.get("articles", []))
        cursor.execute(
            """
            INSERT INTO commandes (numero_commande, client, montant_total, urgence, articles_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                donnees.get("numero_commande"),
                donnees.get("client", "Inconnu"),
                donnees.get("montant_total_eur", 0.0),
                donnees.get("statut_livraison", "normal"),
                articles_json,
            ),
        )
        conn.commit()
        commande_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Commande '{donnees.get('numero_commande')}' existe déjà.",
        )
    finally:
        conn.close()

    return {
        "id": commande_id,
        "numero_commande": donnees.get("numero_commande"),
        "client": donnees.get("client"),
        "montant_total": donnees.get("montant_total_eur"),
        "urgence": donnees.get("statut_livraison"),
        "articles": donnees.get("articles", []),
    }


@app.get("/commandes/{commande_id}", response_model=CommandeOut)
def lire_commande(commande_id: int):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, numero_commande, client, montant_total, urgence, articles_json FROM commandes WHERE id = ?",
        (commande_id,),
    )
    ligne = cursor.fetchone()
    conn.close()

    if not ligne:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Commande ID {commande_id} introuvable.",
        )

    return {
        "id": ligne["id"],
        "numero_commande": ligne["numero_commande"],
        "client": ligne["client"],
        "montant_total": ligne["montant_total"],
        "urgence": ligne["urgence"],
        "articles": json.loads(ligne["articles_json"]),
    }