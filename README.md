# 🚀 Pipeline MLOps Sécurisé — Traitement Intelligent d'E-mails

> Système de classification et d'extraction d'e-mails de commandes, du mail brut au dashboard utilisateur, avec **tracing MLOps complet** (Langfuse), **inférence LLM locale** (Ollama), **classification hybride** et **sécurité de bout en bout (RBAC, Threat Model STRIDE, Fail-Closed)**.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)
![Langfuse](https://img.shields.io/badge/Langfuse-3.x-orange)
![Ollama](https://img.shields.io/badge/Ollama-llama3.2%3A3b-black)
![Tests](https://img.shields.io/badge/tests-15%2B%20passed-brightgreen)
![Security](https://img.shields.io/badge/Security-RBAC%20%7C%20STRIDE-red)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📖 Vue d'ensemble

Ce projet capture automatiquement des e-mails de commandes logistiques (MailHog en dev), les classifie selon **4 catégories** via une **approche hybride** (règles métier déterministes + stemming NLP + LLM local pour les cas ambigus), en extrait les informations structurées, et les expose via une API FastAPI et un dashboard Streamlit.

L'ensemble du pipeline est **instrumenté avec Langfuse** pour l'évaluation continue (traces, observations, scores). Une **boucle de feedback Humain-in-the-Loop (HITL)** permet aux opérateurs de corriger l'IA, chaque correction étant tracée comme un signal de qualité.

**Le plus de ce projet :** L'infrastructure a été pensée avec une approche **"Security by Design"**. L'API est protégée par un système de **RBAC (Role-Based Access Control)** hiérarchique, et les menaces ont été modélisées via la méthode **STRIDE**.

---

## 🏗️ Architecture & Frontières de Confiance

Le système est découpé en zones de confiance distinctes pour limiter la surface d'attaque (principe de défense en profondeur).

```text
┌────────────────────────────────────────────────────────────────────┐
│  ZONE 0 — Utilisateur final (non fiable)                           │
│    → Navigateur Streamlit, envoi d'e-mails via MailHog             │
└───────────────────────────┬────────────────────────────────────────┘
                            │  Frontière ① (AuthN/AuthZ via X-API-Key)
┌───────────────────────────▼────────────────────────────────────────┐
│  ZONE 1 — Surface exposée (semi-fiable)                            │
│    → Streamlit :8501, API FastAPI :8000 (RBAC)                     │
└───────────────────────────┬────────────────────────────────────────┘
                            │  Frontière ② (réseau backend_net)
┌───────────────────────────▼────────────────────────────────────────┐
│  ZONE 2 — Services internes (fiables)                              │
│    → PostgreSQL, Redis, MinIO, ClickHouse, Langfuse Worker         │
└───────────────────────────┬────────────────────────────────────────┘
                            │  Frontière ③ (Contenu LLM = non fiable)
┌───────────────────────────▼────────────────────────────────────────┐
│  ZONE 3 — LLM (NON FIABLE — traité comme une entrée hostile)       │
│    → Ollama :11434 (Inférence locale)                              │
│    → Validation stricte Pydantic + nettoyage JSON (fail-safe)      │
└────────────────────────────────────────────────────────────────────┘
```

---

## 🔒 Sécurité & Robustesse (Focus MLOps Security)

La sécurité de ce projet ne repose pas sur une seule brique, mais sur une approche multicouche documentée dans un [**`THREAT_MODEL.md`**](./THREAT_MODEL.md) (méthode STRIDE).

- **RBAC Hiérarchique** : L'accès à l'API est segmenté en 3 rôles (`Reader` < `Operator` < `Admin`). Chaque rôle possède sa propre clé API (`secrets.compare_digest`).
- **Séparation stricte AuthN / AuthZ** : Authentification (qui es-tu ?) et Autorisation (as-tu le droit ?) gérées proprement via l'injection de dépendances FastAPI (`Depends`).
- **Fail-Closed (Fermé par défaut)** : Toute route non explicitement publique (comme `/health`) rejette les requêtes sans clé valide. Un test automatisé (`test_security_fail_closed.py`) empêche tout développeur d'oublier de protéger une future route.
- **Défense contre les LLM (OWASP LLM Top 10)** : Le LLM est considéré comme une source non fiable. Le JSON produit est nettoyé et strictement validé par Pydantic avant toute persistance.
- **Isolation réseau Docker** : Cloisonnement entre `frontend_net` (exposé) et `backend_net` (base de données, LLM, observabilité).
- **Résilience (Circuit Breaker)** : Si le LLM (Ollama) tombe, l'API bascule automatiquement sur un système de règles déterministes pour ne pas interrompre le service.

---

## 🛠️ Stack Technique

| Domaine | Technologie |
|---|---|
| **Backend & API** | FastAPI, Uvicorn, Pydantic v2 |
| **Sécurité** | RBAC, X-API-Key, `secrets.compare_digest`, slowapi |
| **Moteur IA & LLM** | Ollama (`llama3.2:3b`), prompt engineering, inférence locale |
| **Classification** | Hybride : règles métier + stemming (NLTK) + LLM fallback |
| **Base de données** | PostgreSQL, SQLAlchemy 2.x |
| **Observabilité MLOps** | Langfuse v3/v4 (traces, observations, scores HITL) |
| **Frontend** | Streamlit (dashboard 4 onglets) |
| **Tests & CI/CD** | pytest, GitHub Actions (tests + linter) |
| **Orchestration** | Docker, Docker Compose |

---

## 🚀 Démarrage Rapide

### 1. Prérequis
- Docker Desktop
- Ollama installé sur la machine hôte (macOS)
- 8 Go de RAM minimum

### 2. Configuration de la sécurité (RBAC)
Créez un fichier `.env` à la racine à partir du `.env.example` et configurez vos **trois** clés d'API :

```env
# --- RBAC & API Keys ---
# Attention : utilisez des chaînes complexes en production
READER_API_KEY=cle_lecture_secrete
OPERATOR_API_KEY=cle_operateur_secrete
ADMIN_API_KEY=cle_admin_secrete
```

### 3. Lancement
```bash
make up
```

### 📍 Accès aux services
| Service | URL |
|---|---|
| **Streamlit** (dashboard) | http://localhost:8501 |
| **API FastAPI** (Swagger) | http://localhost:8000/docs |
| **Langfuse** (observabilité) | http://localhost:3000 |

---

## 🧪 Tests & Qualité

Le projet inclut des tests automatisés garantissant la stabilité du pipeline et la sécurité de l'API.

- **Tests unitaires (NLP)** : Vérification des règles déterministes, du stemming et des cas limites.
- **Tests d'intégration API** : Vérification des codes HTTP (200, 401, 403, 404).
- **Tests de sécurité (RBAC)** : Vérification de la hiérarchie des rôles.
- **Test "Fail-Closed"** : Scan automatique de l'application FastAPI pour s'assurer qu'aucune route n'a été laissée sans protection.

```bash
make test
# ou
python -m pytest -v
```

---

## 🗺️ Roadmap

### ✅ Déjà fait
- [x] Pipeline MLOps complet (Ingestion → Classification → Persistance)
- [x] Boucle de feedback Humain-in-the-Loop (HITL)
- [x] Dashboard Streamlit 4 onglets
- [x] **Threat Model STRIDE documenté**
- [x] **RBAC Hiérarchique (Reader/Operator/Admin)**
- [x] **Tests de sécurité "Fail-Closed"**

### 🚧 Prochaines étapes (Phase 2 & 3)
- [ ] **Supply Chain** : Génération de SBOM (Syft), signature d'images (Cosign) et scan de vulnérabilités (Trivy) dans la CI.
- [ ] **Défense Prompt Injection** : Tests adversariaux automatisés pour le LLM.
- [ ] **Secrets Management** : Remplacement du `.env` par SOPS + age (ou HashiCorp Vault).
- [ ] Migrations Alembic versionnées.
- [ ] Endpoint `/metrics` (Prometheus).

---

## 👤 Auteur

**Payet** — Projet réalisé dans le cadre d'une formation MLOps (2025-2026)

- 🐙 GitHub : [@payetDm](https://github.com/payetdm)

## 📄 Licence
Ce projet est sous licence **MIT**.
```

---