# Debug Langfuse - Journal de résolution

**Projet** : mon_projet_mlops  
**Date** : Septembre 2026  
**Durée** : ~1 semaine  
**Statut** : ✅ Résolu

---

## 🎯 Objectif

Intégrer Langfuse dans un projet MLOps (FastAPI + Streamlit + Ollama) pour tracer les classifications d'emails par IA, avec un déploiement 100% local via Docker Compose.

---

## 🏗️ Architecture finale

```
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

**Chemin d'une trace** : SDK Python → Langfuse Web (API) → MinIO (S3) → Redis (queue) → Worker → ClickHouse

**Point critique** : le **Worker** est obligatoire. Sans lui, les traces restent bloquées dans MinIO et n'arrivent jamais dans ClickHouse.

---

## 🐛 Problèmes rencontrés et solutions

### Problème 1 : Healthcheck Langfuse cassé

**Symptôme** : `service_langfuse unhealthy`, API bloquée en `Created`.

**Cause** : le healthcheck utilisait `node -e "require('http').get(...)"`, mais `node` n'est pas dans le PATH du conteneur Langfuse (image basée sur Alpine, sans Node.js accessible).

**Solution** :
```yaml
healthcheck:
  test: ["CMD", "wget", "--spider", "-q", "http://localhost:3000/api/public/health"]
  interval: 10s
  timeout: 5s
  retries: 10
  start_period: 120s
```

Ou désactivation complète si nécessaire :
```yaml
healthcheck:
  disable: true
```

---

### Problème 2 : Migrations ClickHouse "dirty"

**Symptôme** : `error: Dirty database version 40. Fix and force version.`

**Cause** : une migration interrompue marque la base comme "sale". Langfuse refuse de continuer pour éviter la corruption.

**Tentatives infructueuses** :
- `migrate force 39` → `no migration found for version 39`
- `migrate force 0` → `no migration found for version 0`
- Correction SQL manuelle → nouvelles erreurs en cascade

**Solution finale** : réinitialisation complète des volumes Langfuse.
```bash
docker compose down
docker volume rm mon_projet_mlops_langfuse_clickhouse_data \
                 mon_projet_mlops_langfuse_clickhouse_logs \
                 mon_projet_mlops_langfuse_postgres_data \
                 mon_projet_mlops_langfuse_minio_data \
                 mon_projet_mlops_langfuse_redis_data
docker compose up -d
```

**Leçon** : sur un environnement de dev sans données critiques, réinitialiser est souvent plus rapide que réparer.

---

### Problème 3 : `update_current_observation` n'existe pas

**Symptôme** : `AttributeError: 'Langfuse' object has no attribute 'update_current_observation'`

**Cause** : le SDK Langfuse Python v4 a renommé cette méthode.

**Solution** :
```python
# ❌ Obsolète (SDK v3)
langfuse.update_current_observation(metadata={...})

# ✅ Correct (SDK v4)
langfuse.update_current_span(metadata={...})
```

**Note importante** : le SDK Python et le serveur Docker ont des numérotations **indépendantes**. Ici :
- SDK Python : `v4.15.4`
- Serveur Langfuse (Docker) : `v3.225.8`

---

### Problème 4 : Ollama 404 Not Found

**Symptôme** : `httpx.HTTPStatusError: Client error '404 Not Found' for url 'http://service_ollama:11434/api/generate'`

**Cause double** :
1. Le modèle `llama3.2:3b` n'était pas téléchargé dans Ollama
2. Incohérence entre `.env` (`OLLAMA_URL=http://ollama:11434`) et `docker-compose.yml` (`http://service_ollama:11434`)

**Solution** :
```bash
# Télécharger le modèle
docker exec -it service_ollama ollama pull llama3.2:3b

# Corriger le .env
OLLAMA_URL=http://service_ollama:11434
OLLAMA_MODEL=llama3.2:3b
```

**Leçon** : le nom du service Docker (`service_ollama`) est le nom DNS sur le réseau interne. Toujours utiliser ce nom, pas `localhost` ni un nom inventé.

---

### Problème 5 : `healthcheck: disable: true` + `depends_on: service_healthy`

**Symptôme** : `api_fastapi` reste en `Created` indéfiniment.

**Cause** : si le healthcheck est désactivé (`disable: true`), la condition `service_healthy` **n'est jamais satisfaite** — car il n'y a plus de statut "healthy" à attendre.

**Solution** : remplacer la condition dans `depends_on`.
```yaml
# ❌ Bloque indéfiniment
depends_on:
  langfuse:
    condition: service_healthy

# ✅ Démarre dès que langfuse est Up
depends_on:
  langfuse:
    condition: service_started
```

**Leçon** : `disable: true` et `condition: service_healthy` sont incompatibles.

---

### Problème 6 : Traces invisibles dans ClickHouse ⭐ LE PROBLÈME PRINCIPAL

**Symptômes** :
- `auth_check = True` ✅
- Swagger répond `200` ✅
- Mais `SELECT count() FROM default.traces` → `0` ❌
- Dossier `/data/langfuse-events/otel` créé dans MinIO, mais vide

**Diagnostic progressif** :
1. Vérification MinIO : dossier `otel` existe mais aucun fichier traité
2. Vérification `docker ps` : **aucun conteneur worker**
3. Compréhension : `langfuse/langfuse:3` = serveur web uniquement
4. **Le Worker est un conteneur séparé obligatoire** dans l'architecture Langfuse v3

**Solution** : ajout du service `langfuse-worker` dans `docker-compose.yml`.

```yaml
langfuse-worker:
  image: langfuse/langfuse-worker:3
  container_name: service_langfuse_worker
  restart: always
  depends_on:
    langfuse_db:
      condition: service_started
    langfuse_clickhouse:
      condition: service_started
    langfuse_redis:
      condition: service_started
    langfuse_minio:
      condition: service_started
  environment:
    - DATABASE_URL=postgresql://langfuse:${LANGFUSE_DB_PASSWORD}@langfuse_db:5432/langfuse
    - SALT=${LANGFUSE_SALT}
    - ENCRYPTION_KEY=${LANGFUSE_ENCRYPTION_KEY}
    - CLICKHOUSE_URL=http://langfuse_clickhouse:8123
    - CLICKHOUSE_MIGRATION_URL=clickhouse://langfuse_clickhouse:9000
    - CLICKHOUSE_USER=langfuse
    - CLICKHOUSE_PASSWORD=${LANGFUSE_CLICKHOUSE_PASSWORD}
    - CLICKHOUSE_CLUSTER_ENABLED=false
    - REDIS_CONNECTION_STRING=redis://langfuse_redis:6379
    - LANGFUSE_S3_EVENT_UPLOAD_BUCKET=langfuse-events
    - LANGFUSE_S3_EVENT_UPLOAD_ENDPOINT=http://langfuse-minio:9000
    - LANGFUSE_S3_EVENT_UPLOAD_ACCESS_KEY_ID=${LANGFUSE_S3_ACCESS_KEY}
    - LANGFUSE_S3_EVENT_UPLOAD_SECRET_ACCESS_KEY=${LANGFUSE_S3_SECRET_KEY}
    - LANGFUSE_S3_EVENT_UPLOAD_REGION=${LANGFUSE_S3_REGION}
    - LANGFUSE_S3_EVENT_UPLOAD_FORCE_PATH_STYLE=true
    - TELEMETRY_ENABLED=${LANGFUSE_TELEMETRY_ENABLED:-false}
  networks:
    - backend_net
```

**Résultat** : les traces arrivent enfin dans ClickHouse. ✅

**Leçon majeure** : Langfuse v3 est une **architecture distribuée**. Le serveur web accepte les traces et les stocke dans MinIO. Le Worker les traite ensuite (MinIO → Redis → ClickHouse). **Sans Worker, rien n'arrive dans ClickHouse.**

---

## 🛠️ Commandes de diagnostic utiles

### Vérifier le nombre de traces dans ClickHouse

```bash
docker exec -it bdd_langfuse_clickhouse clickhouse-client \
  --user langfuse --password Cookies430 \
  --query "SELECT 'traces' as t, count() FROM default.traces 
           UNION ALL SELECT 'observations', count() FROM default.observations 
           UNION ALL SELECT 'scores', count() FROM default.scores"
```

### Voir les dernières traces

```bash
docker exec -it bdd_langfuse_clickhouse clickhouse-client \
  --user langfuse --password Cookies430 \
  --query "SELECT id, name, timestamp FROM default.traces ORDER BY timestamp DESC LIMIT 5"
```

### Vérifier l'authentification du SDK

```bash
docker exec -it api_fastapi python -c "
from langfuse import Langfuse
import os
lf = Langfuse(
    public_key=os.environ['LANGFUSE_PUBLIC_KEY'],
    secret_key=os.environ['LANGFUSE_SECRET_KEY'],
    host=os.environ['LANGFUSE_HOST'],
)
print('auth_check =', lf.auth_check())
"
```

### Voir les logs du Worker

```bash
docker compose logs -f langfuse-worker
```

### Vérifier les tables ClickHouse

```bash
docker exec -it bdd_langfuse_clickhouse clickhouse-client \
  --user langfuse --password Cookies430 \
  --query "SHOW TABLES FROM default"
```

### Vérifier Redis

```bash
docker exec -it cache_langfuse redis-cli ping
# Réponse : PONG
```

### Vérifier MinIO (buckets et fichiers)

```bash
# Lister les buckets
docker exec -it langfuse-minio sh -c "ls -la /data/"

# Voir les fichiers du bucket langfuse-events
docker exec -it langfuse-minio sh -c "ls -la /data/langfuse-events/"
```

---

## 📦 Configuration finale (`docker-compose.yml`)

### Services Langfuse (extrait clé)

```yaml
langfuse:
  image: langfuse/langfuse:3
  container_name: service_langfuse
  ports:
    - "3000:3000"
  environment:
    - PORT=3000
    - DATABASE_URL=postgresql://langfuse:${LANGFUSE_DB_PASSWORD}@langfuse_db:5432/langfuse
    - HOSTNAME=0.0.0.0
    - NEXTAUTH_URL=http://localhost:3000
    - NEXTAUTH_SECRET=${LANGFUSE_NEXTAUTH_SECRET}
    - SALT=${LANGFUSE_SALT}
    - ENCRYPTION_KEY=${LANGFUSE_ENCRYPTION_KEY}
    - CLICKHOUSE_URL=http://langfuse_clickhouse:8123
    - CLICKHOUSE_MIGRATION_URL=clickhouse://langfuse_clickhouse:9000
    - CLICKHOUSE_USER=langfuse
    - CLICKHOUSE_PASSWORD=${LANGFUSE_CLICKHOUSE_PASSWORD}
    - CLICKHOUSE_CLUSTER_ENABLED=false
    - REDIS_CONNECTION_STRING=redis://langfuse_redis:6379
    - LANGFUSE_S3_EVENT_UPLOAD_BUCKET=langfuse-events
    - LANGFUSE_S3_EVENT_UPLOAD_ENDPOINT=http://langfuse-minio:9000
    - LANGFUSE_S3_EVENT_UPLOAD_ACCESS_KEY_ID=${LANGFUSE_S3_ACCESS_KEY}
    - LANGFUSE_S3_EVENT_UPLOAD_SECRET_ACCESS_KEY=${LANGFUSE_S3_SECRET_KEY}
    - LANGFUSE_S3_EVENT_UPLOAD_REGION=${LANGFUSE_S3_REGION}
    - LANGFUSE_S3_EVENT_UPLOAD_FORCE_PATH_STYLE=true
    - TELEMETRY_ENABLED=${LANGFUSE_TELEMETRY_ENABLED:-false}
  healthcheck:
    disable: true
  depends_on:
    langfuse_db:
      condition: service_started
    langfuse_clickhouse:
      condition: service_started
    langfuse_redis:
      condition: service_started
    langfuse_minio:
      condition: service_started
    langfuse_minio_init:
      condition: service_completed_successfully
  networks:
    - backend_net
  restart: always

langfuse-worker:
  image: langfuse/langfuse-worker:3
  container_name: service_langfuse_worker
  restart: always
  depends_on:
    langfuse_db:
      condition: service_started
    langfuse_clickhouse:
      condition: service_started
    langfuse_redis:
      condition: service_started
    langfuse_minio:
      condition: service_started
  environment:
    - DATABASE_URL=postgresql://langfuse:${LANGFUSE_DB_PASSWORD}@langfuse_db:5432/langfuse
    - SALT=${LANGFUSE_SALT}
    - ENCRYPTION_KEY=${LANGFUSE_ENCRYPTION_KEY}
    - CLICKHOUSE_URL=http://langfuse_clickhouse:8123
    - CLICKHOUSE_MIGRATION_URL=clickhouse://langfuse_clickhouse:9000
    - CLICKHOUSE_USER=langfuse
    - CLICKHOUSE_PASSWORD=${LANGFUSE_CLICKHOUSE_PASSWORD}
    - CLICKHOUSE_CLUSTER_ENABLED=false
    - REDIS_CONNECTION_STRING=redis://langfuse_redis:6379
    - LANGFUSE_S3_EVENT_UPLOAD_BUCKET=langfuse-events
    - LANGFUSE_S3_EVENT_UPLOAD_ENDPOINT=http://langfuse-minio:9000
    - LANGFUSE_S3_EVENT_UPLOAD_ACCESS_KEY_ID=${LANGFUSE_S3_ACCESS_KEY}
    - LANGFUSE_S3_EVENT_UPLOAD_SECRET_ACCESS_KEY=${LANGFUSE_S3_SECRET_KEY}
    - LANGFUSE_S3_EVENT_UPLOAD_REGION=${LANGFUSE_S3_REGION}
    - LANGFUSE_S3_EVENT_UPLOAD_FORCE_PATH_STYLE=true
    - TELEMETRY_ENABLED=${LANGFUSE_TELEMETRY_ENABLED:-false}
  networks:
    - backend_net

api:
  depends_on:
    langfuse:
      condition: service_started   # ⚠️ PAS service_healthy (healthcheck désactivé)
```

---

## 📚 Leçons apprises

1. **Langfuse v3 = architecture distribuée**
   - Serveur web ≠ Worker ≠ Bases de données
   - Le Worker est **obligatoire** pour que les traces arrivent dans ClickHouse

2. **SDK Python vs Serveur Docker**
   - Numérotations **indépendantes** (SDK v4.x, serveur v3.x)
   - Toujours vérifier la version du SDK : `python -c "import langfuse; print(langfuse.__version__)"`

3. **`healthcheck: disable: true` ≠ `condition: service_healthy`**
   - Ces deux configurations sont incompatibles
   - Utiliser `condition: service_started` si le healthcheck est désactivé

4. **Noms de services Docker**
   - Sur le réseau interne, utiliser le **nom du service** (`service_ollama`), pas `localhost`
   - Le `container_name` (`service_langfuse`) n'est utilisé que pour `docker exec`

5. **Réinitialiser > réparer (en dev)**
   - Sur un environnement sans données critiques, `docker compose down -v` + `up -d` est souvent plus rapide que de déboguer des migrations corrompues

6. **Debug méthodique**
   - Suivre le chemin des données étape par étape : SDK → Web → MinIO → Redis → Worker → ClickHouse
   - Vérifier chaque maillon avec les commandes appropriées

---

## ✅ Statut final

- [x] Langfuse Web démarré et accessible (http://localhost:3000)
- [x] Langfuse Worker démarré et fonctionnel
- [x] API FastAPI connectée à Langfuse (`auth_check = True`)
- [x] Ollama opérationnel avec `llama3.2:3b`
- [x] Endpoint `/ai/classify` répond en 200
- [x] Traces visibles dans ClickHouse
- [x] Traces visibles dans l'interface Langfuse

**Projet validé** ✅

---

*Document généré le 28 septembre 2026*