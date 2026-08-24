# 📦 API REST - Traitement & Extraction Automatique de Commandes (IA Locale)

Une API Backend moderne et robuste conçue avec **FastAPI**, **Pydantic** et **SQLite**, intégrée à un modèle de langage local (**Qwen 2.5 via Ollama**). 

L'application automatise la lecture d'e-mails de commandes non structurés, extrait les données clés (client, articles, montants, urgence) au format JSON, valide la donnée et assure sa persistance en base de données.

---

## 🛠️ Stack Technique

* **Framework Backend :** FastAPI (Python 3.11+)
* **Moteur d'IA / LLM :** Ollama (`qwen2.5-coder:3b`)
* **Validation & Typage :** Pydantic v2
* **Base de données :** SQLite3
* **Serveur ASGI :** Uvicorn

---

## 💡 Fonctionnalités

- **Extraction Intelligente :** Analyse automatique de texte brut par LLM avec garantie de sortie au format JSON.
- **Validation Stricte :** Rejet immédiat des requêtes invalides (prix négatifs, champs manquants) via Pydantic (`HTTP 422`).
- **Gestion des Erreurs & Doublons :** Capture des erreurs d'intégrité SQL (`HTTP 409`) et des timeouts du service IA (`HTTP 504`).
- **Architecture Modulaire :** Séparation claire des responsabilités (`database`, `models`, `services`, `main`).

---

## 🚀 Installation & Lancement

### 1. Prérequis
* Python 3.10+
* [Ollama](https://ollama.com/) installé avec le modèle Qwen :
  ```bash
  ollama pull qwen2.5-coder:3b