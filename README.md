# 🚀 API de Traitement de Commandes par IA (V2)

API REST construite avec **FastAPI**, **SQLAlchemy (ORM)**, **SQLite** et **Ollama** (LLM local).  
Elle permet d'analyser le contenu d'un e-mail de commande en arrière-plan (Background Tasks), d'en extraire les informations clés via l'IA, et de les enregistrer en base de données.

---

## 🛠️ Tech Stack

* **Framework Web :** FastAPI (Python 3.11+)
* **ORM & Persistance :** SQLAlchemy & SQLite
* **Validation & Schémas :** Pydantic v2
* **LLM Local :** Ollama (Qwen2.5 / Llama3 / Mistral)
* **Sécurité :** Authentification par clé API (`X-API-Key`)
* **Tests Automatisés :** Pytest & HTTPX
* **Conteneurisation :** Docker

---

## 🔑 Configuration (.env)

Créez un fichier `.env` à la racine du projet :

API_KEY=mon_secret_123

---

## 🚀 Lancement rapide avec Docker

# Build de l'image
docker build -t api-commandes-ia .

# Lancement du conteneur
docker run -d -p 8000:8000 -e API_KEY="mon_secret_123" -e OLLAMA_HOST=http://host.docker.internal:11434 --name mon-api-ia api-commandes-ia

---

## 🔒 Sécurité & Endpoints

Pour exécuter une requête sur l'endpoint d'analyse, le header `X-API-Key` est obligatoire.

* `POST /commandes/analyser` : Reçoit l'e-mail, renvoie `202 Accepted` et lance l'analyse IA en tâche de fond. (Nécessite `X-API-Key`)
* `GET /commandes/{id}` : Récupère les détails d'une commande enregistrée.

---

## 🧪 Tests Automatisés

python -m pytest