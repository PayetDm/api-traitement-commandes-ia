# Threat Model — Pipeline MLOps de traitement d'e-mails

**Version :** 1.1
**Date :** Février 2026
**Auteur :** Payet
**Méthode :** STRIDE par composant + frontières de confiance
**Périmètre :** Stack Docker Compose complète (API, Streamlit, PostgreSQL, Ollama, Langfuse, MailHog, Redis, MinIO, ClickHouse)
**Hors périmètre :** Sécurité de l'hôte macOS, sécurité physique, sécurité du fournisseur cloud (non applicable — self-hosted)

## 1. Actifs à protéger

| Actif | Sensibilité | Pourquoi |
|---|---|---|
| Contenu des e-mails clients | **Élevée** (PII, données commerciales) | RGPD, secret des affaires |
| Clés API (Reader, Operator, Admin) | **Critique** | Donnent accès aux routes de l'API selon le rôle |
| Secrets d'infra (DB, Langfuse, MinIO) | **Critique** | Compromission = pivot latéral |
| Traces Langfuse | **Élevée** | Contiennent du contenu d'e-mails (PII) et des scores de qualité |
| Base PostgreSQL | **Élevée** | Commandes + contenu e-mail brut |

---

## 2. Analyse par frontière de confiance

### Frontière ① : Internet → Zone exposée (Streamlit, API)

| STRIDE | Menace concrète | Mitigation actuelle | Statut |
|---|---|---|---|
| **S** | Vol de clé API | Clés séparées par rôle, `compare_digest` | ⚠️ Partiel (pas de rotation, clés en clair dans .env) |
| **T** | Injection dans le payload e-mail | Validation Pydantic + tests anti-injection | ⚠️ Partiel (défense prompt injection à renforcer) |
| **R** | Opérateur nie une redirection HITL | Logs d'application (logger) | ⚠️ Partiel (logs non structurés, pas d'audit trail immuable) |
| **I** | Accès non autorisé aux commandes | **RBAC implémenté** (`Reader`, `Operator`, `Admin`) | ✅ **Corrigé** |
| **D** | Flood de `/ai/classify` | Rate limiting (slowapi) + rôle `Operator` requis | ✅ Corrigé |
| **E** | Escalade via route admin | **RBAC multi-clés** (fini le "1 clé = tous droits") | ✅ **Corrigé** |

### Frontière ② : Zone exposée → Services internes (`backend_net`)

| STRIDE | Menace concrète | Mitigation actuelle | Statut |
|---|---|---|---|
| **S** | Service malveillant sur `backend_net` | Isolation réseau Docker (frontend/backend) | ⚠️ Partiel (pas de mTLS) |
| **T** | Modification des commandes en base | SQLAlchemy ORM (requêtes paramétrées) | ✅ |
| **R** | Modification silencieuse de statut | Logs applicatifs | ⚠️ Partiel |
| **I** | Lecture des secrets d'infra | `.env` monté de manière implicite dans les conteneurs | ⚠️ Partiel (Phase 1.3 : SOPS/Vault) |
| **D** | Saturation PostgreSQL | Pool SQLAlchemy par défaut | ⚠️ Partiel |
| **E** | Conteneur API lit MinIO/ClickHouse | L'API a accès aux secrets Langfuse | ❌ (Principe du moindre privilège à améliorer) |

### Frontière ③ : API → LLM (Ollama) — **le LLM est non fiable**

| STRIDE | Menace concrète | Mitigation actuelle | Statut |
|---|---|---|---|
| **S** | Prompt injection indirecte | Aucune défense dédiée (uniquement test basique) | ❌ (Priorité Phase 3) |
| **T** | Sortie LLM malformée / piégée | `_nettoyer_json_llm` + validation Pydantic (`CommandeIAOutput`) | ✅ |
| **I** | Exfiltration de PII par le LLM | LLM local = pas d'accès réseau | ✅ (Par design) |
| **D** | LLM surchargé / crash | Circuit breaker + fallback règles | ✅ |
| **E** | Le LLM contourne la classification | Règles déterministes prioritaires (hybride) | ✅ |

---

## 3. Matrice de risque (Mise à jour)

| # | Risque | Prob. | Impact | Sévérité | Priorité |
|---|---|---|---|---|---|
| R1 | Compromission clé API (pas de rotation, .env) | Moyenne | Critique | 🟠 Fort | **Phase 1.3** |
| R2 | Prompt injection LLM (pas de défense) | Haute | Élevé | 🔴 Critique | **Phase 3** |
| R3 | ~~Pas de RBAC (1 clé = tous droits)~~ | - | - | ✅ **Traité** | Terminé |
| R4 | PII en clair dans PostgreSQL + traces Langfuse | Haute | Élevé (RGPD) | 🟠 Fort | **Phase 3** |
| R5 | Pas d'audit log structuré (repudiation) | Haute | Moyen | 🟡 Moyen | **Phase 1.2** |
| R6 | Pivot latéral (pas de mTLS) | Basse | Élevé | 🟡 Moyen | **Phase 4** |
| R7 | Pas de SBOM / signature image | Moyenne | Moyen | 🟡 Moyen | **Phase 2** |

## 4. Contrôles de sécurité implémentés (Preuves)
- [x] **RBAC multi-rôles** (`READER`, `OPERATOR`, `ADMIN`) avec héritage via `IntEnum`.
- [x] **AuthN et AuthZ séparés** (via FastAPI `Depends`).
- [x] **Fail-Closed par défaut** sur les routes inconnues.
- [x] **Protection des routes critiques** (`/commandes/{id}/rediriger` est Admin-only).
- [x] **Principe du moindre privilège** sur l'exposition des routes (ex: `/health` est public mais minimaliste).