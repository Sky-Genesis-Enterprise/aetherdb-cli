# Utiliser une image de base officiel de Python
FROM python:3.11-slim-bookworm

# Définir les variables d'environnement
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier les fichiers de requirements et les installer
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste de l'application
COPY . /app/

# Exposer le port sur lequel l'application va tourner
EXPOSE 8000

# Commande pour démarrer l'application
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
