# 🚀 AI Order Processing API

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Ollama-Local_LLM-black?style=for-the-badge" alt="Ollama" />
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker" />
  <img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite" />
</p>

---

## 📌 Présentation

Une **API REST intelligente** conçue pour automatiser le traitement des commandes entrantes.  
Elle extrait dynamiquement les informations clés contenues dans un e-mail brut (nom du client, articles, montants, statut d'urgence) grâce à un **LLM local (Ollama)**, puis les structure et les persiste dans une base de données **SQLite**.

### ✨ Fonctionnalités clés
* 🧠 **Extraction par IA locale :** Zéro donnée transmise à un service tiers payant.
* 🛡️ **Validation stricte :** Typage des données et schémas garantis par **Pydantic**.
* ⚡ **Performance & Sécurité :** Traitement asynchrone et requêtes SQL préparées.
* 📦 **Prêt pour le déploiement :** Conteneurisation complète via Docker.
* 🧪 **Fiabilité :** Suite de tests unitaires/intégration automatisés avec Mocks.

---

## 🛠️ Tech Stack

| Composant | Technologie |
| :--- | :--- |
| **Framework Web** | FastAPI (Python 3.11+) |
| **Moteur IA** | Ollama (llama3 / mistral) |
| **Base de données** | SQLite |
| **Tests & HTTP** | Pytest & HTTPX |
| **Conteneurisation** | Docker |

---

## 🚀 Démarrage rapide avec Docker (Recommandé)

### 1. Prérequis
* Docker Desktop en cours d'exécution.
* Ollama installé localement.

### 2. Démarrer Ollama
Autorisez le réseau à interroger le service Ollama :
OLLAMA_HOST=0.0.0.0 ollama serve

### 3. Build & Lancement du conteneur
À la racine du projet :

# Construction de l'image
docker build -t api-commandes-ia .

# Exécution du conteneur
docker run -d -p 8000:8000 -e OLLAMA_HOST=http://host.docker.internal:11434 --name mon-api-ia api-commandes-ia

📍 L'API est en ligne sur : http://localhost:8000

---

## 📖 Documentation Interactive (Swagger)

L'API intègre une interface OpenAPI d'exploration interactive disponible sur :  
👉 http://localhost:8000/docs

### Endpoints principaux :

| Méthode | Route | Description |
| :--- | :--- | :--- |
| POST | /commandes/analyser | Extrait les données d'un mail via LLM et enregistre la commande en BDD. |
| GET | /commandes/{id} | Récupère la fiche détaillée d'une commande par son ID. |

---

## 🧪 Tests Automatisés

Les tests s'appuient sur des mocks pour isoler le serveur du LLM et garantir une exécution instantanée.

# Exécution de la suite Pytest
python -m pytest

---

## 💻 Démarrage en local (sans Docker)

# 1. Environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Sur Mac/Linux

# 2. Dépendances
pip install -r requirements.txt

# 3. Lancement du serveur d'arrière-plan
uvicorn app.main:app --reload