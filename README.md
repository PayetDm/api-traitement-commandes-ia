# 🚀 API de Traitement de Commandes par IA

API REST construite avec **FastAPI**, **SQLite** et **Ollama** (LLM local). Elle permet d'analyser le contenu brut d'un e-mail de commande, d'en extraire les informations clés au format JSON grâce à l'IA, et de les enregistrer en base de données.

---

## 🛠️ Tech Stack

* **Framework :** FastAPI (Python 3.11+)
* **LLM Local :** Ollama (Llama3 / Mistral)
* **Base de données :** SQLite
* **Tests :** Pytest & HTTPX
* **Conteneurisation :** Docker

---

## 🚀 Lancement avec Docker (Recommandé)

### 1. Prérequis
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) installé et lancé.
* [Ollama](https://ollama.com/) installé sur votre machine avec le modèle souhaité.

### 2. Démarrage d'Ollama
Assurez-vous qu'Ollama accepte les requêtes réseau :
OLLAMA_HOST=0.0.0.0 ollama serve

### 3. Build & Exécution du conteneur
À la racine du projet :

# Construction de l'image
docker build -t api-commandes-ia .

# Lancement du conteneur
docker run -d -p 8000:8000 -e OLLAMA_HOST=http://host.docker.internal:11434 --name mon-api-ia api-commandes-ia

L'API est accessible sur http://localhost:8000.

---

## 🧪 Exécution des Tests Automatisés

Les tests unitaires et d'intégration utilisent des mocks pour le service LLM afin d'assurer une exécution instantanée.

# Lancement de la suite de tests
python -m pytest

---

## 📖 Documentation Interactive (Swagger)

Une fois l'application lancée, la documentation interactive Swagger est disponible à l'adresse :  
👉 http://localhost:8000/docs

### Endpoints principaux :
* POST /commandes/analyser : Analyse le texte d'un e-mail et enregistre la commande.
* GET /commandes/{id} : Récupère les détails d'une commande enregistrée.

---

## 💻 Lancement en local (sans Docker)

# 1. Création et activation du venv
python -m venv .venv
source .venv/bin/activate  # Sur Mac/Linux

# 2. Installation des dépendances
pip install -r requirements.txt

# 3. Lancement du serveur FastAPI
uvicorn app.main:app --reload