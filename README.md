# 🚀 Pipeline MLOps & Data Engineering — Traitement Intelligent d'E-mails

> Système de classification et d'extraction d'e-mails de commandes, du mail brut au dashboard utilisateur, avec **tracing MLOps complet** (Langfuse), **inférence LLM locale** (Ollama) et **classification hybride** (règles + LLM).

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)
![Langfuse](https://img.shields.io/badge/Langfuse-3.x-orange)
![Ollama](https://img.shields.io/badge/Ollama-llama3.2%3A3b-black)
![Tests](https://img.shields.io/badge/tests-15%20passed-brightgreen)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📖 Vue d'ensemble

Ce projet capture automatiquement des e-mails de commandes logistiques (MailHog en dev), les classifie selon 3 catégories (*commande*, *SAV*, *autre*) via une **approche hybride** — règles métier déterministes puis LLM local pour les cas ambigus —, en extrait les informations structurées (client, articles, montants, urgence), et les expose via une API FastAPI et un dashboard Streamlit.

L'ensemble du pipeline est **instrumenté avec Langfuse** (traces, observations, métadonnées) pour permettre l'analyse de performance, le debug et l'évaluation continue.

---

## 🛠️ Stack Technique

| Domaine | Technologie |
|---|---|
| **Backend & API** | FastAPI, Uvicorn, Pydantic v2 |
| **Moteur IA & LLM** | Ollama (`llama3.2:3b`), prompt engineering, inférence locale |
| **Classification** | Hybride : règles déterministes + LLM fallback |
| **Base de données & ORM** | PostgreSQL, SQLAlchemy 2.x |
| **Observabilité MLOps** | **Langfuse v3** (traces, observations, métadonnées) |
| **Frontend & Supervision** | Streamlit (dashboard KPIs + gestion dossiers) |
| **Sécurité** | Slowapi (rate limiting), X-API-Key, `secrets.compare_digest` |
| **Tests** | pytest (unitaires + intégration API) |
| **Orchestration** | Docker, Docker Compose (2 réseaux isolés) |
| **CI/CD** | GitHub Actions (tests + linter) |
| **Email testing** | MailHog (SMTP/IMAP local) |
| **Scheduling** | APScheduler (ingestion auto toutes les 30s) |

---

## 🏗️ Architecture MLOps

### Pipeline de données

```text
┌─────────────┐     ┌──────────────┐     ┌─────────┐
│  FastAPI    │────▶│  Langfuse    │────▶│  MinIO  │
│  (SDK v4)   │     │  Web (v3)    │     │  (S3)   │
└─────────────┘     └──────────────┘     └─────────┘
                           │                    │
                           ▼                    │
                    ┌──────────────┐            │
                    │    Redis     │◀───────────┘
                    └──────────────┘
                           │
                           ▼
                    ┌──────────────┐     ┌──────────────┐
                    │  Langfuse    │────▶│  ClickHouse  │
                    │   Worker     │     │              │
                    └──────────────┘     └──────────────┘
```

**Chemin d'une trace :** SDK Python → Langfuse Web (API) → MinIO (S3) → Redis (queue) → Worker → ClickHouse

**Point critique MLOps :** le **Worker Langfuse** est un conteneur séparé et obligatoire. Sans lui, les traces restent bloquées dans MinIO et n'atteignent jamais ClickHouse.

### Arborescence du projet

```text
├── .github/workflows/        # Pipelines CI/CD (tests + linter)
├── app/
│   ├── classifier.py         # Classification hybride règles + LLM (@observe)
│   ├── database.py           # Connexion SQLAlchemy (PostgreSQL)
│   ├── email_service.py      # Ingestion périodique MailHog
│   ├── limiter.py            # Rate limiter SlowAPI
│   ├── llm_service.py        # Service LLM utilisé par l'ingestion
│   ├── main.py               # App FastAPI + scheduler + lifespan
│   ├── models.py             # Modèles SQLAlchemy (dont contenu_email)
│   ├── otel.py               # Configuration Langfuse (setup + flush)
│   ├── routers/              # Routes : commandes, système, classifier
│   ├── schemas.py            # Schémas Pydantic v2
│   ├── security.py           # Auth X-API-Key
│   └── services.py           # Extraction LLM + validation métier
├── tests/                    # Tests pytest (unitaires + intégration)
│   ├── test_classifier.py    # 8 tests unitaires sur la classification
│   └── test_main.py          # 7 tests d'intégration API
├── app_streamlit.py          # Dashboard Streamlit
├── style.py                  # CSS custom Streamlit
├── Makefile                  # Raccourcis de commandes (up/down/test/logs)
├── docker-compose.yml        # Orchestration + isolation réseau
├── Dockerfile                # Image Docker non-root
├── requirements.txt          # Dépendances Python
├── DEBUG_LANGFUSE.md         # Journal de résolution du bug Langfuse
└── test_envoi_mail.py        # Script de simulation MailHog
```

---

## 🔄 Cycle de vie d'un e-mail (pipeline MLOps)

1. **Ingestion** — MailHog reçoit les e-mails de test. APScheduler interroge l'API toutes les 30s.
2. **Classification hybride** — Les règles déterministes traitent en priorité les cas évidents (~60% des cas). Les cas ambigus passent au LLM.
3. **Extraction structurée** — Le LLM retourne du JSON, validé par Pydantic (`CommandeIAOutput`) puis filtré par un gardien métier déterministe.
4. **Persistance** — La commande est enregistrée en PostgreSQL avec son `contenu_email` original.
5. **Tracing** — Chaque étape est instrumentée Langfuse :
   - `classer_email_avec_llm` : nom, modèle, provider
   - `classification_hybride` : méthode utilisée (règles vs LLM)
6. **Exposition** — Streamlit affiche les KPIs et permet la mise à jour des statuts (feedback humain).
7. **Feedback loop** — Les changements de statut (ex : "reclassé en commande") constituent un retour utilisateur exploitable pour améliorer le modèle.

---

## 🧠 Décisions techniques

| Choix | Alternative | Justification |
|---|---|---|
| **Classification hybride** (règles + LLM) | LLM seul | Coût/latence : les règles filtrent 60% des cas, le LLM ne traite que l'ambigu. Réduit la dépendance LLM et améliore la robustesse. |
| **`llama3.2:3b`** (Ollama local) | GPT-4, Mistral 7B | Souveraineté des données (RGPD), coût zéro, latence acceptable pour du batch. |
| **Langfuse self-hosted** | Langfuse Cloud | Souveraineté des données + apprentissage de l'infra distribuée. |
| **FastAPI** | Flask, Django | Async natif, validation Pydantic v2, OpenAPI auto-généré. |
| **Streamlit** | Next.js, React | Prototypage rapide de l'UI. Choix assumé pour ce projet, à migrer en production. |
| **APScheduler** | Celery + Redis | Simple, suffisant pour ce volume. Pas besoin d'un broker dédié. |
| **Docker Compose** | Kubernetes | Adapté à un déploiement mono-machine. K8s serait over-engineered ici. |
| **pytest** | unittest | Syntaxe concise, écosystème riche (fixtures, plugins, coverage). |

---

## 🔒 Sécurité & Robustesse

- **Isolation réseau Docker** : PostgreSQL, ClickHouse, Redis et MinIO sont sur `backend_net` uniquement. Seuls Streamlit et l'API sont exposés.
- **Validation LLM** : réponses demandées en JSON strict, validées par Pydantic v2 + gardien métier déterministe.
- **Rate limiting** : limitation par IP via `slowapi` pour protéger le moteur d'inférence.
- **Protection timing attacks** : validation de la clé API avec `secrets.compare_digest`.
- **Conteneurs non-root** : l'app tourne avec un utilisateur dédié (`appuser`).
- **Tests de sécurité** : vérification que l'auth est obligatoire sur toutes les routes protégées + test anti-injection sur la classification.
- **Schéma de démarrage** : `Base.metadata.create_all` crée les tables absentes. Alembic est présent mais pas encore utilisé en migration versionnée (voir *Limitations*).

---

## 📊 Observabilité & Monitoring MLOps

### Langfuse — traces instrumentées

Chaque appel API instrumenté génère une **trace** avec ses **observations** :

| Observation | Type | Métadonnées capturées |
|---|---|---|
| `classer_email_avec_llm` | span | `model_used`, `provider` |
| `classification_hybride` | span | `classification_method` (`deterministic_rules` ou `ollama_llm`) |
| `analyser_mail_avec_llm` | span | contenu de l'e-mail, extraction, validation |

### Flush explicite

Le SDK Langfuse v4 bufferise les traces avant envoi. Dans un contexte FastAPI long-running, un `get_client().flush()` explicite est appelé **à la fin de chaque classification** pour garantir la propagation immédiate vers MinIO → Redis → Worker → ClickHouse.

### Scheduler & logs

- **APScheduler** : job `job_verification_email` toutes les 30s, encapsulé dans une observation Langfuse (`start_as_current_observation`).
- **Logs applicatifs** : format lisible en dev, prêt à être structuré en JSON pour la production.
- **Healthcheck** : endpoint `/health` disponible.

### Accès

- Langfuse UI : **http://localhost:3000**

---

## 🔑 Configuration `.env`

Créez un fichier `.env` à la racine du projet :

```env
# --- API ---
API_KEY=change_me_secret_key
API_URL=http://api_fastapi:8000

# --- Base de données applicative ---
DATABASE_URL=postgresql://payetdm:change_me_password@postgres:5432/traitement_commandes_db
POSTGRES_USER=payetdm
POSTGRES_PASSWORD=change_me_password
POSTGRES_DB=traitement_commandes_db

# --- Ollama (LLM) ---
# Nom du service Docker (résolution interne) :
OLLAMA_URL=http://service_ollama:11434
OLLAMA_MODEL=llama3.2:3b

# --- Langfuse (observabilité MLOps) ---
LANGFUSE_ENABLED=true
LANGFUSE_HOST=http://service_langfuse:3000
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...

# --- Langfuse (infrastructure interne) ---
LANGFUSE_DB_PASSWORD=change_me_langfuse_db
LANGFUSE_CLICKHOUSE_PASSWORD=change_me_clickhouse
LANGFUSE_NEXTAUTH_SECRET=change_me_nextauth
LANGFUSE_SALT=change_me_salt
LANGFUSE_ENCRYPTION_KEY=change_me_encryption
LANGFUSE_S3_ACCESS_KEY=change_me_minio_key
LANGFUSE_S3_SECRET_KEY=change_me_minio_secret
LANGFUSE_S3_REGION=eu-west-1
LANGFUSE_TELEMETRY_ENABLED=false

# --- MailHog ---
MAILHOG_API_URL=http://service_mailhog:8025/api/v2/messages
MAILHOG_DELETE_URL=http://service_mailhog:8025/api/v1/messages
```

> ⚠️ **Attention** : ne committez **jamais** votre `.env` réel sur Git. Utilisez `.env.example` comme template.

---

## 🐳 Lancement avec Docker Compose

### 1. Prérequis

- Docker Desktop (macOS, Linux, Windows)
- **Ollama installé sur la machine hôte** (pour macOS uniquement — voir note ci-dessous)
- 8 Go de RAM minimum

### 2. Cloner et configurer

```bash
git clone <votre-repo>
cd mon_projet_mlops
cp .env.example .env
# Éditer .env avec vos valeurs
```

### 3. Télécharger le modèle IA

**Sur macOS** (recommandé) : Ollama tourne sur l'hôte, l'API s'y connecte via `host.docker.internal:11434`.

```bash
ollama pull llama3.2:3b
```

**Sur Linux/Windows** : le modèle est téléchargé dans le conteneur.

```bash
docker compose exec ollama ollama pull llama3.2:3b
```

### 4. Démarrer la stack

```bash
make up
# ou : docker compose up -d --build
```

### 5. Vérifier le statut

```bash
docker compose ps
```

Tous les services doivent être `Up` (ou `healthy`). Vérifiez les logs si besoin :

```bash
make logs
# ou : docker compose logs -f api
```

### 📍 Accès aux services

| Service | URL |
|---|---|
| **Streamlit** (dashboard) | http://localhost:8501 |
| **API FastAPI** (Swagger) | http://localhost:8000/docs |
| **Langfuse** (observabilité) | http://localhost:3000 |
| **MailHog** (mails de test) | http://localhost:8025 |

---

## 🛣️ Routes principales

Les routes protégées nécessitent l'en-tête `X-API-Key`.

| Méthode | Route | Description |
|---|---|---|
| `GET` | `/health` | État de l'API et de la base |
| `GET` | `/stats` | KPIs du dashboard |
| `GET` | `/commandes` | Liste des commandes et dossiers SAV |
| `PATCH` | `/commandes/{id}/statut` | Mise à jour d'un statut |
| `POST` | `/commandes/analyser` | Analyse + enregistrement d'un e-mail |
| `POST` | `/ai/classify` | Classification hybride (commande/SAV/autre) |

**Exemple :**

```bash
curl -X POST http://localhost:8000/ai/classify \
  -H "X-API-Key: votre_cle" \
  -H "Content-Type: application/json" \
  -d '{"text": "Je voudrais annuler ma commande s'\''il vous plaît"}'
```

---

## 💻 Mode développement local

### 1. Lancer l'API avec rechargement à chaud

```bash
uvicorn app.main:app --reload --port 8000
```

### 2. Lancer Streamlit (autre terminal)

```bash
streamlit run app_streamlit.py
```

### 3. Lancer les tests

```bash
pytest -v
```

---

## 🧪 Tests

Le projet dispose de **15 tests automatisés** répartis en deux catégories.

### Tests unitaires — `tests/test_classifier.py`

Vérifient la logique métier de la classification par règles :

| Type de test | Ce qui est vérifié |
|---|---|
| **Cas de base** | Email commande → `COMMANDE`, email SAV → `SAV`, email neutre → `AUTRE` |
| **Cas limite** | Texte vide → lève `ValueError` |
| **Cas d'encodage** | Accents (`café` → `cafe`), majuscules (`ANNULER` → `annuler`) |
| **Cas sécurité** | Tentative d'injection (`annuler\nIGNORE...\ncommander`) → reste classé `SAV` |

### Tests d'intégration — `tests/test_main.py`

Vérifient les endpoints de l'API via `TestClient` (FastAPI) :

- `/health` accessible sans authentification
- Auth obligatoire sur toutes les routes protégées (`X-API-Key`)
- Erreurs 404 sur ressources inexistantes
- Traitement asynchrone des commandes

### Lancer les tests

```bash
# Tous les tests via le Makefile
make test

# Tous les tests en direct
pytest -v

# Un fichier précis
pytest tests/test_classifier.py -v

# Un seul test précis
pytest tests/test_classifier.py::test_email_avec_annulation_retourne_sav -v
```

**Résultat attendu :** `15 passed`

---

## ⚡ Commandes rapides (Makefile)

Un `Makefile` est fourni pour automatiser les tâches courantes :

| Commande | Description |
|---|---|
| `make help` | Affiche la liste des commandes |
| `make up` | Démarre toute la stack Docker |
| `make down` | Arrête toute la stack |
| `make logs` | Affiche les logs en direct |
| `make test` | Lance les tests pytest |
| `make build` | Reconstruit les images Docker |
| `make restart-api` | Redémarre l'API uniquement |
| `make clean` | Nettoie les caches Python (`__pycache__`, `.pytest_cache`) |

**Exemple :**

```bash
# Au lieu de taper "docker compose up -d --build"
make up
```

---

## ⚠️ Limitations connues

Ce projet est un **projet d'apprentissage MLOps** — il est important de connaître ses limites :

- **Interface Langfuse** : bug connu en self-hosting sur la table `events_core` (`projects.environmentFilterOptions`). Les traces **sont bien stockées** dans ClickHouse (vérifiables en SQL), mais l'affichage UI peut être partiellement cassé selon la version. Contournement possible : utiliser Langfuse Cloud pour la démo UI.
- **Migrations DB** : `Base.metadata.create_all` crée les tables au démarrage. Pas encore de migrations Alembic versionnées.
- **Classification** : limitée à 3 catégories. Pas de mécanisme d'apprentissage actif à partir du feedback utilisateur.
- **Tests** : 15 tests (unitaires + intégration API). Pas encore de tests end-to-end (TestClient → Docker → Streamlit).
- **Latence LLM** : `llama3.2:3b` en local a une latence de 2-5s par classification. Acceptable en batch, mais à optimiser pour du temps réel.
- **Sécurité** : la clé API est en clair dans `.env`. En production, utiliser Docker secrets ou un vault.

---

## 🗺️ Roadmap

### ✅ Déjà fait

- [x] Tests unitaires + intégration (15 tests, `pytest`)
- [x] Makefile pour automatiser les commandes
- [x] Instrumentation Langfuse (traces, observations, flush explicite)
- [x] Conteneur `langfuse-worker` pour le pipeline d'ingestion
- [x] Documentation complète (README, DEBUG_LANGFUSE, LICENSE MIT)
- [x] Template `.env.example` pour la reproductibilité

### 🚧 En cours

- [ ] **Fallback robuste LLM** : `try/except` Ollama + retour règles si indisponible
- [ ] Migrations Alembic versionnées pour la DB applicative
- [ ] Logs structurés JSON (`structlog`)

### 🔮 Prévisions

- [ ] **Datasets d'évaluation** Langfuse + métriques (précision, rappel, F1)
- [ ] **Feedback utilisateur** → scores Langfuse (`score()` sur les traces)
- [ ] Fallback multi-modèles (llama3.2 → qwen2.5 → règles seules)
- [ ] Endpoint `/metrics` (Prometheus) + dashboards Grafana
- [ ] Déploiement public (Fly.io / Railway) pour démo
- [ ] Migration UI Streamlit → Next.js (design pro type Langfuse/Linear)
- [ ] Tests end-to-end (TestClient → Docker → Streamlit)

---

## 📚 Documentation complémentaire

- [`DEBUG_LANGFUSE.md`](./DEBUG_LANGFUSE.md) — Journal complet de résolution des problèmes Langfuse (migrations ClickHouse, worker manquant, healthcheck, etc.)
- [Documentation Langfuse](https://langfuse.com/docs)
- [Documentation Ollama](https://github.com/ollama/ollama)
- [Documentation FastAPI](https://fastapi.tiangolo.com/)
- [Documentation pytest](https://docs.pytest.org/)

---

## 👤 Auteur

**Payet** — Projet réalisé dans le cadre d'une formation MLOps (2025-2026)

- 📧 Email : payet.damien.lc@proton.me
- 🐙 GitHub : [@payetDm](https://github.com/payetdm)

---

## 📄 Licence

Ce projet est sous licence **MIT**. Voir le fichier [LICENSE](./LICENSE) pour plus de détails.