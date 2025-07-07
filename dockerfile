# Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le dossier de l'application
COPY . .

# Définir la variable d'environnement pour que Flask trouve l'app via la factory
ENV FLASK_APP=run:app

# Exposer le port
EXPOSE 5002

# Lancer avec Gunicorn (meilleur pour la prod) ou Flask
CMD ["flask", "run", "--host=0.0.0.0", "--port=5002"]