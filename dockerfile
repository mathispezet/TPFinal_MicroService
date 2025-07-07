# Dockerfile

# 1. Utiliser une image Python de base, légère et officielle
FROM python:3.9-slim

# 2. Définir le répertoire de travail dans le conteneur
WORKDIR /app

# 3. Copier le fichier des dépendances et les installer
# On copie ce fichier en premier pour profiter du cache de Docker.
# Les dépendances ne seront réinstallées que si requirements.txt change.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copier le reste du code de l'application
COPY . .

# 5. Définir les variables d'environnement pour Flask
ENV FLASK_APP=run:app
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5002

# 6. Exposer le port que le service écoute
EXPOSE 5002

# 7. Commande pour lancer l'application
CMD ["flask", "run"]