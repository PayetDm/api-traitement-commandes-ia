# 🚀 Pipeline MLOps & Data Engineering - Traitement Intelligent d'E-mails

Ce projet est une infrastructure de niveau production permettant de capturer, analyser et structurer automatiquement des e-mails de commandes logistiques à l'aide d'un Modèle de Langage (LLM) local et d'un gardien métier déterministe.

---

## 🛠️ Tech Stack

* **Backend & API :** FastAPI, Uvicorn, Pydantic v2
* **Moteur IA & LLM :** Ollama (`qwen2.5:1.5b`), Inférence locale & Prompt Engineering
* **Base de données & ORM :** PostgreSQL 15, SQLAlchemy, Alembic (Migrations)
* **Frontend & Supervision :** Streamlit
* **Sécurité & Observabilité :** Slowapi (Rate Limiting), Secrets (Timing attack protection), Logging natif
* **Orchestration & DevOps :** Docker, Docker Compose (Segmentation réseau), GitHub Actions (CI/CD)
* **Email Testing :** MailHog (Serveur SMTP/IMAP local)
* **Scheduling :** APScheduler (Ingestion automatique en arrière-plan)

---

## 🏗️ Architecture du Projet

```text
├── .github/workflows/   # Pipelines CI/CD (Tests automatisés & Linter)
├── alembic/             # Migrations de base de données (SQLAlchemy / Alembic)
├── app/
│   ├── database.py       # Configuration ORM PostgreSQL & Connexion BDD
│   ├── email_service.py  # Ingestion asynchrone MailHog & Nettoyage
│   ├── llm_service.py    # Client API Ollama & Inférence LLM (Sanitization & Anti-Prompt Injection)
│   ├── main.py           # Endpoints FastAPI, Rate Limiting & Scheduler
│   ├── models.py         # Modèles de données SQLAlchemy
│   ├── schemas.py        # Schémas de validation Pydantic v2
│   ├── security.py       # Authentification X-API-Key (secrets.compare_digest)
│   └── services.py       # Gardien métier Python & Logique d'aiguillage
├── tests/                # Suite de tests unitaires (pytest)
├── alembic.ini           # Configuration d'Alembic
├── app_streamlit.py      # Interface utilisateur & Supervision Streamlit
├── docker-compose.yml    # Orchestration multi-conteneurs & Isolation réseau
├── Dockerfile            # Image Docker sécurisée (User Non-Root)
├── README.md             # Documentation du projet
├── requirements.txt      # Dépendances du projet
└── test_envoi_mail.py    # Script de simulation d'envoi de mail

```

---

## 🔒 Sécurité & Robustesse Production

* **Isolation Réseau Docker :** Segmentation stricte via `backend_net` et `frontend_net`. Les services internes (PostgreSQL, Ollama) ne sont pas exposés sur la machine hôte.
* **Hardening du LLM :** Protection contre les injections de prompt grâce au balisage XML strict (`<email_body>`), la sanitization du texte et la température fixée à 0.0.
* **Rate Limiting & DoS :** Limitation du débit des requêtes par IP via `slowapi` sur FastAPI pour protéger le moteur d'inférence.
* **Protection Timing Attacks :** Validation de la clé API avec `secrets.compare_digest`.
* **Conteneurs Non-Root :** Exécution du processus applicatif avec un utilisateur système dédié à faible privilège (`appuser`).
* **Gestion des Migrations :** Contrôle de version du schéma de base de données assuré par Alembic.

---

## 🔑 Configuration (.env)

Créez un fichier `.env` à la racine du projet :

```env
API_KEY=votre_cle_api_secrete_ici
API_URL=http://api_fastapi:8000
DATABASE_URL=postgresql://dev_user:dev_password@postgres:5432/commandes_db
OLLAMA_URL=http://ollama:11434/api/generate
MAILHOG_API_URL=http://service_mailhog:8025/api/v2/messages
MAILHOG_DELETE_URL=http://service_mailhog:8025/api/v1/messages

```

---

## 🐳 Lancement avec Docker Compose (Recommandé)

### 1. Démarrer et reconstruire la stack

```bash
docker-compose up -d --build

```

### 2. Télécharger le modèle IA Qwen 2.5 dans Ollama (au 1er démarrage)

```bash
docker-compose exec ollama ollama pull qwen2.5:1.5b

```

### 📍 Accès aux services :

* **Interface Streamlit :** http://localhost:8501
* **Documentation API (Swagger) :** http://localhost:8000/docs
* **Interface MailHog (Boîte mail de test) :** http://localhost:8025

---

## 💻 Lancement en Mode Développement Local

### 1. Lancer l'API FastAPI avec rechargement chaud

```bash
uvicorn app.main:app --reload --port 8000

```

### 2. Lancer l'interface Streamlit (dans un autre terminal)

```bash
streamlit run app_streamlit.py

```

```

```