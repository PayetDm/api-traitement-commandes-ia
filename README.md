# 🚀 API de Traitement de Commandes par IA & Interface Streamlit (V2)

Système d'analyse et de tri automatique d'e-mails construit avec **FastAPI**, **Streamlit**, **SQLAlchemy (ORM)**, **SQLite** et **Ollama** (LLM local).  
L'application analyse en arrière-plan le contenu des e-mails, extrait les informations clés via un LLM local, applique un gardien métier Python anti-faux-positifs, et oriente les demandes vers le flux **Logistique** ou **Service Client (SAV)**.

---

## 🛠️ Tech Stack

* **Framework Web & API :** FastAPI (Python 3.11+) & Uvicorn
* **Dashboard & Interface UI :** Streamlit & Pandas
* **ORM & Persistance :** SQLAlchemy & SQLite
* **Validation & Schémas :** Pydantic v2
* **LLM Local :** Ollama (qwen2.5-coder:3b / llama3.2)
* **Sécurité :** Authentification par clé API (X-API-Key)
* **Tests Automatisés :** Pytest & HTTPX
* **Conteneurisation :** Docker & Docker Compose

---

## 🏗️ Architecture du Projet

├── app/
│   ├── database.py    # Configuration ORM SQLite & Modèles BDD
│   ├── main.py        # Endpoints FastAPI & Tâches d'arrière-plan
│   ├── schemas.py     # Schémas de validation Pydantic
│   ├── security.py    # Authentification X-API-Key
│   └── services.py    # Intégration Ollama & Gardien métier Python
├── app_streamlit.py   # Interface utilisateur Streamlit
├── docker-compose.yml # Orchestration multi-conteneurs
├── Dockerfile         # Image Docker Python
├── requirements.txt   # Dépendances du projet
└── tests/             # Suite de tests unitaires (pytest)

---

## 🔑 Configuration (.env)

Créez un fichier `.env` à la racine du projet :

API_KEY=mon_secret_123
API_URL=http://127.0.0.1:8000
OLLAMA_URL=http://localhost:11434/api/generate

---

## 🐳 Lancement avec Docker Compose (Recommandé)

Lancez l'ensemble des services (FastAPI, Streamlit, Ollama) en une seule commande :

# 1. Démarrer les conteneurs
docker-compose up -d --build

# 2. Télécharger le modèle IA dans Ollama (au 1er démarrage)
docker exec -it service_ollama ollama pull qwen2.5-coder:3b

Accès aux services :
* **Interface Streamlit :** http://localhost:8501
* **Documentation API (Swagger) :** http://localhost:8000/docs
* **Moteur Ollama :** http://localhost:11434

---

## 💻 Lancement en Mode Développement Local

# 1. Lancer l'API FastAPI
uvicorn app.main:app --reload --port 8000

# 2. Lancer l'interface Streamlit (dans un autre terminal)
streamlit run app_streamlit.py

---

## 🔒 Sécurité & Endpoints

Pour exécuter une requête d'écriture ou d'analyse, le header `X-API-Key` est obligatoire.

* `GET /health` : Vérification de l'état de santé de l'API et de la BDD SQLite.
* `POST /commandes/analyser` : Reçoit le texte de l'e-mail, renvoie `202 Accepted` et lance l'analyse IA + gardien Python en tâche de fond. *(Nécessite `X-API-Key`)*
* `GET /commandes` : Récupère l'ensemble des e-mails enregistrés (Commandes et SAV).
* `GET /commandes/{id}` : Récupère le détail d'une commande par son ID.
* `PATCH /commandes/{id}/statut` : Met à jour le statut d'une commande (`en_attente`, `en_preparation`, `expediee`, `annulee`, `transfere_sav`).

---

## 🧠 Tri Intelligent & Gardien Python

L'application combine la puissance d'Ollama et la robustesse de Python :
1. **Extraction par LLM :** Extraction JSON (client, montant, urgence, articles).
2. **Gardien Python :** Si le message ne contient ni articles ni montant > 0 € (ex: demandes de stage, questions générales), Python force la réorientation vers le statut `transfere_sav`.
3. **Séparation UI Streamlit :** Les commandes logistiques apparaissent dans le tableau principal, tandis que les demandes hors-sujet sont automatiquement routées vers le tableau **Service Client**.

---

## 🧪 Tests Automatisés

python -m pytest