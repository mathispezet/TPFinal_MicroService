# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .config import Config

# Initialiser les extensions (sans les lier à une app pour l'instant)
db = SQLAlchemy()

def create_app(config_class=Config):
    """Factory pour créer et configurer l'instance de l'application Flask."""
    app = Flask(__name__)
    
    # Charger la configuration depuis l'objet Config
    app.config.from_object(config_class)
    
    # Lier l'instance de la base de données à l'application
    db.init_app(app)
    
    # Importer et enregistrer les routes
    from . import routes
    app.register_blueprint(routes.bp) # Utiliser un Blueprint est encore plus propre

    # Créer les tables de la BDD si elles n'existent pas
    with app.app_context():
        db.create_all()

    return app