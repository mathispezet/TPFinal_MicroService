# app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .config import Config

# On initialise les extensions sans les lier à une application pour l'instant
db = SQLAlchemy()

def create_app(config_class=Config):
    """
    Fonction "factory" pour créer et configurer l'instance de l'application Flask.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Lier les extensions à l'instance de l'application
    db.init_app(app)

    # Importer et enregistrer les routes (Blueprints)
    from .routes import main_bp
    app.register_blueprint(main_bp)

    # Créer les tables de la base de données si elles n'existent pas
    with app.app_context():
        # Il faut importer les modèles ici pour que create_all les connaisse
        from . import models
        db.create_all()

    return app