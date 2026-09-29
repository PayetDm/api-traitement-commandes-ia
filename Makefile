# ==========================================
# Makefile — PyTechData MLOps
# ==========================================

.PHONY: help up down logs test build restart-api clean

help:
	@echo "Commandes disponibles :"
	@echo "  make up          → Démarre toute la stack Docker"
	@echo "  make down        → Arrête toute la stack"
	@echo "  make logs        → Affiche les logs en direct"
	@echo "  make test        → Lance les tests pytest"
	@echo "  make build       → Reconstruit les images Docker"
	@echo "  make restart-api → Redémarre l'API uniquement"
	@echo "  make clean       → Nettoie les caches Python"

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

test:
	pytest tests/ -v

build:
	docker compose up -d --build

restart-api:
	docker compose up -d --build api

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	rm -rf .coverage htmlcov/
