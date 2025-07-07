# message-service/app/config.py

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration de l'application Flask."""
    # Clé secrète convenue avec les autres groupes pour la signature des JWT
    SECRET_KEY = "on-ny-arrivera-jamais-enfin-peut-etre"

    # URI de la base de données (prêt pour quand vous l'activerez)
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'mysql+pymysql://user:pass@db/dbname')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
