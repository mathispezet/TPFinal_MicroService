# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Classe de configuration pour l'application Flask."""
    # Clé secrète pour les JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'une-cle-secrete-par-defaut')
    
    # URL de la base de données
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    
    # Option pour désactiver une fonctionnalité de SQLAlchemy qui n'est pas nécessaire
    SQLALCHEMY_TRACK_MODIFICATIONS = False