# 1. Image de base : Python 3.11 version légère (slim)
FROM python:3.11-slim

# 2. Définir le dossier de travail dans le conteneur
WORKDIR /code

# 3. Copier le fichier des dépendances
COPY requirements.txt /code/requirements.txt

# 4. Installer les dépendances sans garder les fichiers d'installation en cache
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 5. Copier le dossier app dans le conteneur
COPY ./app /code/app

# 6. Exposer le port 8000 sur lequel tourne FastAPI
EXPOSE 8000

# 7. Commande par défaut pour démarrer Uvicorn quand le conteneur se lance
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]