# message-service/app/__init__.py

from flask import Flask
from .models import db

def create_app():
    """Crée et configure l'application Flask."""
    app = Flask(__name__)
    app.config.from_object('app.config.Config')

    # Initialiser la base de données avec l'application
    db.init_app(app)

    # Enregistrer le Blueprint qui contient les routes
    from .routes import messages_bp
    app.register_blueprint(messages_bp)

    # Créer les tables de la base de données si elles n'existent pas
    with app.app_context():
        db.create_all()

    return app
