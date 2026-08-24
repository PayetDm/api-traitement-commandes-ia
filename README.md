# 🚀 API de Traitement de Commandes par IA

API REST construite avec **FastAPI**, **SQLite** et **Ollama** (LLM local). Elle permet d'analyser le contenu brut d'un e-mail de commande, d'en extraire les informations clés au format JSON grâce à l'IA, et de les enregistrer en base de données.

---

## 🛠️ Tech Stack

* **Framework :** FastAPI (Python 3.11)
* **LLM Local :** Ollama (Llama3 / Mistral)
* **Base de données :** SQLite
* **Conteneurisation :** Docker

---

## 🚀 Lancement avec Docker (Recommandé)

### 1. Prérequis
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) installé et lancé.
* [Ollama](https://ollama.com/) installé sur votre machine avec le modèle souhaité.

### 2. Démarrage d'Ollama
Assurez-vous qu'Ollama accepte les requêtes réseau :
```bash
OLLAMA_HOST=0.0.0.0 ollama serve