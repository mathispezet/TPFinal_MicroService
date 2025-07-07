# app/config.py

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration de base pour l'application Flask."""
    # Clé secrète pour les sessions, JWT, etc.
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-super-secret-key')

    # Configuration de la base de données
    DB_USER = os.getenv('DB_USER', 'user')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_NAME = os.getenv('DB_NAME', 'message_db')
    
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False