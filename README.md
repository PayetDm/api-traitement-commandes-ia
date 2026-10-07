# 🚀 Pipeline MLOps & Data Engineering — Traitement Intelligent d'E-mails

> Système de classification et d'extraction d'e-mails de commandes, du mail brut au dashboard utilisateur, avec **tracing MLOps complet** (Langfuse), **inférence LLM locale** (Ollama), **classification hybride** (règles + stemming + LLM) et **boucle de feedback Humain-in-the-Loop**.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)
![Langfuse](https://img.shields.io/badge/Langfuse-3.x-orange)
![Ollama](https://img.shields.io/badge/Ollama-llama3.2%3A3b-black)
![Tests](https://img.shields.io/badge/tests-15%20passed-brightgreen)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📖 Vue d'ensemble

Ce projet capture automatiquement des e-mails de commandes logistiques (MailHog en dev), les classifie selon **4 catégories** (*commande*, *SAV*, *service client*, *autre*) via une **approche hybride** — règles métier déterministes + stemming français + LLM local pour les cas ambigus —, en extrait les informations structurées (client, articles, montants, urgence), et les expose via une API FastAPI et un dashboard Streamlit.

L'ensemble du pipeline est **instrumenté avec Langfuse** (traces, observations, métadonnées, scores) pour permettre l'analyse de performance, le debug et l'évaluation continue. Une **boucle de feedback Humain-in-the-Loop** permet aux opérateurs de corriger les classifications de l'IA, chaque correction étant automatiquement tracée comme un signal de qualité.

---

## 🛠️ Stack Technique

| Domaine | Technologie |
|---|---|
| **Backend & API** | FastAPI, Uvicorn, Pydantic v2 |
| **Moteur IA & LLM** | Ollama (`llama3.2:3b`), prompt engineering, inférence locale |
| **Classification** | Hybride : règles + stemming (NLTK Snowball) + LLM fallback |
| **Base de données & ORM** | PostgreSQL, SQLAlchemy 2.x |
| **Observabilité MLOps** | **Langfuse v3/v4** (traces, observations, scores HITL) |
| **Frontend & Supervision** | Streamlit (dashboard 4 onglets + badges) |
| **Sécurité** | Slowapi (rate limiting), X-API-Key, `secrets.compare_digest` |
| **Résilience** | Circuit breaker LLM + fallback fail-safe |
| **Tests** | pytest (15 tests unitaires + intégration API) |
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

### Boucle de feedback Humain-in-the-Loop

```text
                  ┌──────────────────────┐
                  │   Classification IA  │
                  │   (règles + LLM)     │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │   Trace Langfuse     │
                  │   ID enregistré en DB│
                  └──────────┬───────────┘
                             │
                  ┌──────────┴───────────┐
                  │                      │
                  ▼                      ▼
          ┌───────────────┐      ┌───────────────┐
          │  IA correcte  │      │  IA trompée   │
          │  Pas d'action │      │  Opérateur    │
          │               │      │  redirige     │
          └───────────────┘      └───────┬───────┘
                                         │
                                         ▼
                                ┌───────────────┐
                                │ Score Langfuse│
                                │ accuracy = 0.0│
                                └───────────────┘
```

**Principe :** chaque correction humaine envoie un score `0.0` sur la trace d'origine. Langfuse calcule alors le **taux de précision réel** de l'IA, identifie les catégories les plus confondues, et permet d'itérer sur les règles et le prompt.

### Arborescence du projet

```text
├── .github/workflows/        # Pipelines CI/CD (tests + linter)
├── app/
│   ├── classifier.py         # Classification hybride (règles + stemming + LLM)
│   ├── database.py           # SQLAlchemy + persistance des articles
│   ├── email_service.py      # Ingestion MailHog (utilise services.py)
│   ├── limiter.py            # Rate limiter SlowAPI
│   ├── main.py               # App FastAPI + scheduler + lifespan
│   ├── models.py             # Modèles SQLAlchemy (avec langfuse_trace_id)
│   ├── otel.py               # Configuration Langfuse (setup + flush)
│   ├── routers/              # Routes : commandes, système, classifier
│   ├── schemas.py            # Schémas Pydantic v2
│   ├── security.py           # Auth X-API-Key
│   └── services.py           # Extraction LLM + classification + nettoyage JSON
├── tests/                    # Tests pytest (unitaires + intégration)
│   ├── test_classifier.py    # 8 tests unitaires sur la classification
│   └── test_main.py          # 7 tests d'intégration API
├── app_streamlit.py          # Dashboard Streamlit (4 onglets + badges)
├── style.py                  # CSS custom Streamlit
├── Makefile                  # Raccourcis de commandes
├── docker-compose.yml        # Orchestration + isolation réseau
├── Dockerfile                # Image Docker non-root
├── requirements.txt          # Dépendances Python (inclut nltk)
├── DEBUG_LANGFUSE.md         # Journal de résolution du bug Langfuse
└── test_envoi_mail.py        # Script de simulation MailHog
```

---

## 🔄 Cycle de vie d'un e-mail (pipeline MLOps)

1. **Ingestion** — MailHog reçoit les e-mails. APScheduler interroge l'API toutes les 30s.
2. **Classification hybride** :
   - **Normalisation Unicode** : suppression des accents, réduction des voyelles doublées (`cassée` → `casse`)
   - **Stemming français** (NLTK Snowball) : `cassée` → `cass` (racine commune)
   - **Règles déterministes** : match sur dictionnaires métier (SAV, Service Client, Commande, Logistique, Produits)
   - **Règle contextuelle** : `probleme + produit` → SAV
   - **Fallback LLM** pour les cas ambigus (via Ollama)
3. **Extraction structurée** — Le LLM retourne du JSON, **nettoyé** (correction des `null`, types invalides) puis validé par Pydantic (`CommandeIAOutput`).
4. **Persistance** — La commande et ses articles sont enregistrés en PostgreSQL avec son `contenu_email` original et l'ID de trace Langfuse.
5. **Tracing** — Chaque étape est instrumentée Langfuse :
   - `classer_email_avec_llm` : modèle, provider
   - `classification_hybride` : méthode utilisée (`deterministic_rules`, `ollama_llm`, `llm_unavailable_fallback`)
6. **Exposition** — Streamlit affiche les KPIs et permet la mise à jour des statuts.
7. **Feedback HITL** — Les redirections manuelles (correction de l'IA) envoient un **score de qualité** à Langfuse.

---

## 🧠 Décisions techniques

| Choix | Alternative | Justification |
|---|---|---|
| **Classification hybride** (règles + stemming + LLM) | LLM seul | Coût/latence : les règles filtrent 60% des cas. Le stemming permet de matcher les variantes (`cassé`/`cassée`/`casser`). |
| **Stemming Snowball** (NLTK) | Regex manuelles | Gestion native des variantes françaises, standard NLP académique. |
| **`llama3.2:3b`** (Ollama local) | GPT-4, Mistral 7B | Souveraineté des données (RGPD), coût zéro, latence acceptable pour du batch. |
| **Circuit breaker LLM** | Appel direct | En cas de panne Ollama, l'app reste fonctionnelle (fail-safe). |
| **Langfuse self-hosted** | Langfuse Cloud | Souveraineté des données + apprentissage de l'infra distribuée. |
| **Boucle HITL** | Pas de feedback | Permet de mesurer la précision réelle et d'améliorer le système. |
| **FastAPI** | Flask, Django | Async natif, validation Pydantic v2, OpenAPI auto-généré. |
| **Streamlit** | Next.js, React | Prototypage rapide de l'UI. Choix assumé pour ce projet. |
| **APScheduler** | Celery + Redis | Simple, suffisant pour ce volume. |
| **Docker Compose** | Kubernetes | Adapté à un déploiement mono-machine. |
| **pytest** | unittest | Syntaxe concise, écosystème riche. |

---

## 🔒 Sécurité & Robustesse

- **Isolation réseau Docker** : PostgreSQL, ClickHouse, Redis, MinIO sur `backend_net`. Seuls Streamlit et l'API sont exposés.
- **Validation LLM** : JSON strict + nettoyage automatique (`_nettoyer_json_llm`) + validation Pydantic.
- **Rate limiting** : limitation par IP via `slowapi`.
- **Protection timing attacks** : `secrets.compare_digest` pour la clé API.
- **Conteneurs non-root** : utilisateur dédié (`appuser`).
- **Tests de sécurité** : auth obligatoire sur toutes les routes + test anti-injection.
- **Circuit breaker** : si Ollama est down, l'API bascule sur les règles (fail-safe).
- **Fail-safe sur score Langfuse** : une panne Langfuse ne bloque pas la redirection.

---

## 📊 Observabilité & Monitoring MLOps

### Langfuse — traces instrumentées

| Observation | Type | Métadonnées capturées |
|---|---|---|
| `classer_email_avec_llm` | span | `model_used`, `provider` |
| `classification_hybride` | span | `classification_method` |
| `analyser_mail_avec_llm` | span | contenu de l'e-mail, extraction, validation |

### Scores de qualité (boucle HITL)

| Score | Valeur | Signification |
|---|---|---|
| `classification_accuracy` | `0.0` | Correction humaine : l'IA s'est trompée |

Chaque redirection manuelle dans Streamlit envoie ce score à Langfuse **sur la trace d'origine** (via `langfuse_trace_id` stocké en base).

### Métriques exploitables

- **Taux de précision réel** : ratio de classifications non corrigées
- **Catégories les plus confondues** : SAV ↔ Service Client, etc.
- **Taux de fallback** : % de classifications n'ayant pas utilisé le LLM

### Scheduler & logs

- **APScheduler** : job `job_verification_email` toutes les 30s.
- **Healthcheck** : endpoint `/health`.

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

> ⚠️ **Attention** : ne committez **jamais** votre `.env` réel sur Git.

---

## 🐳 Lancement avec Docker Compose

### 1. Prérequis

- Docker Desktop (macOS, Linux, Windows)
- **Ollama installé sur la machine hôte** (macOS)
- 8 Go de RAM minimum

### 2. Cloner et configurer

```bash
git clone <votre-repo>
cd mon_projet_mlops
cp .env.example .env
# Éditer .env avec vos valeurs
```

### 3. Télécharger le modèle IA

**Sur macOS** : Ollama tourne sur l'hôte.
```bash
ollama pull llama3.2:3b
```

**Sur Linux/Windows** : le modèle est dans le conteneur.
```bash
docker compose exec ollama ollama pull llama3.2:3b
```

### 4. Démarrer la stack

```bash
make up
```

### 5. Vérifier le statut

```bash
docker compose ps
```

Tous les services doivent être `Up` (ou `healthy`).

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
| `GET` | `/commandes` | Liste des commandes |
| `PATCH` | `/commandes/{id}/statut` | Mise à jour d'un statut |
| `POST` | `/commandes/{id}/rediriger` | **Redirection HITL** (avec score Langfuse) |
| `POST` | `/commandes/analyser` | Analyse + enregistrement d'un e-mail |
| `POST` | `/ai/classify` | Classification hybride |

**Exemple :**

```bash
curl -X POST http://localhost:8000/ai/classify \
  -H "X-API-Key: votre_cle" \
  -H "Content-Type: application/json" \
  -d '{"text": "Je voudrais annuler ma commande"}'
```

---

## 🎨 Dashboard Streamlit

Interface organisée en **4 onglets** :

| Onglet | Contenu |
|---|---|
| 🛒 **Commandes** | 3 sous-sections (En cours / Expédiées / Terminées) |
| 🎧 **Service Client** | Dossiers relationnels (retours, remboursements, questions) |
| 🛠️ **SAV** | Dossiers techniques (casse, panne, garantie) |
| 🧪 **Zone de Test** | Simulation d'analyse d'e-mail |

**Boucle HITL** : chaque dossier a 3 boutons de redirection (🛒 🎧 🛠️) + boutons d'avancement logistique (📦 Expédiée, ✅ Terminée).

---

## 🧪 Tests

**15 tests automatisés** répartis en deux catégories.

### Tests unitaires (`tests/test_classifier.py`)

| Type | Ce qui est vérifié |
|---|---|
| **Cas de base** | Commande, SAV, Service Client, AUTRE |
| **Cas limite** | Texte vide → `ValueError` |
| **Encodage** | Accents (`café` → `cafe`), majuscules |
| **Sécurité** | Injection (`annuler\nIGNORE...`) |
| **Contexte** | `probleme + produit` → SAV |
| **Logistique** | `retard + colis` → COMMANDE |

### Tests d'intégration (`tests/test_main.py`)

- `/health` sans auth
- Auth obligatoire sur les routes protégées
- Erreurs 404
- Traitement asynchrone

### Lancer

```bash
make test          # Tous les tests
pytest -v          # En direct
```

**Résultat :** `15 passed`

---

## ⚡ Commandes rapides (Makefile)

| Commande | Description |
|---|---|
| `make help` | Liste des commandes |
| `make up` | Démarre la stack |
| `make down` | Arrête la stack |
| `make logs` | Logs en direct |
| `make test` | Tests pytest |
| `make build` | Reconstruit les images |
| `make restart-api` | Redémarre l'API |
| `make clean` | Nettoie les caches |

---

## ⚠️ Limitations connues

- **Interface Langfuse** : bug connu `events_core` en self-hosting. Les traces sont bien stockées dans ClickHouse (vérifiables en SQL), mais l'UI peut être partiellement cassée. Contournement : Langfuse Cloud.
- **Migrations DB** : `Base.metadata.create_all` au démarrage. Pas encore de migrations Alembic versionnées.
- **Classification** : 4 catégories fixes. Pas d'apprentissage actif à partir du feedback (les scores sont enregistrés mais non utilisés pour réentraîner).
- **Tests** : 15 tests (unitaires + intégration API). Pas de tests end-to-end (TestClient → Docker → Streamlit).
- **Latence LLM** : `llama3.2:3b` en local : 2-5s par classification. Acceptable en batch.
- **Sécurité** : clé API en clair dans `.env`. En production : Docker secrets ou Vault.

---

## 🗺️ Roadmap

### ✅ Déjà fait

- [x] Classification hybride 4 catégories + stemming NLP
- [x] Circuit breaker LLM (fallback fail-safe)
- [x] Nettoyage JSON du LLM (`_nettoyer_json_llm`)
- [x] Persistance des articles extraits
- [x] Boucle de feedback Humain-in-the-Loop avec scores Langfuse
- [x] Dashboard Streamlit 4 onglets avec badges
- [x] 15 tests (unitaires + intégration API)
- [x] Makefile pour automatiser
- [x] Documentation complète (README, DEBUG_LANGFUSE, LICENSE MIT)
- [x] Template `.env.example`

### 🚧 En cours

- [ ] Migrations Alembic versionnées
- [ ] Logs structurés JSON (`structlog`)
- [ ] Endpoint `/metrics` (Prometheus)

### 🔮 Prévisions

- [ ] **Datasets d'évaluation** Langfuse + métriques (précision, rappel, F1)
- [ ] **Exploitation des scores HITL** pour améliorer les règles
- [ ] Fallback multi-modèles (llama3.2 → qwen2.5 → règles seules)
- [ ] Dashboards Grafana (métriques Prometheus)
- [ ] Déploiement public (Fly.io / Railway)
- [ ] Migration UI Streamlit → Next.js
- [ ] Tests end-to-end (TestClient → Docker → Streamlit)

---

## 📚 Documentation complémentaire

- [`DEBUG_LANGFUSE.md`](./DEBUG_LANGFUSE.md) — Journal complet de résolution des problèmes Langfuse (migrations ClickHouse, worker manquant, healthcheck, etc.)
- [Documentation Langfuse](https://langfuse.com/docs)
- [Documentation Ollama](https://github.com/ollama/ollama)
- [Documentation FastAPI](https://fastapi.tiangolo.com/)
- [Documentation pytest](https://docs.pytest.org/)
- [NLTK Snowball Stemmer](https://www.nltk.org/howto/stem.html)

---

## 👤 Auteur

**Payet** — Projet réalisé dans le cadre d'une formation MLOps (2025-2026)

- 📧 Email : payet.damien.lc@proton.me
- 🐙 GitHub : [@payetDm](https://github.com/payetdm)

---

## 📄 Licence

Ce projet est sous licence **MIT**. Voir le fichier [LICENSE](./LICENSE) pour plus de détails.