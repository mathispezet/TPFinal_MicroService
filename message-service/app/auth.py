# message-service/app/auth.py

from functools import wraps
import jwt
from flask import request, jsonify, g, current_app

def jwt_required(f):
    """
    Décorateur pour valider le token JWT.
    Extrait l'identité de l'utilisateur et la stocke dans `g.user`.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]

        if not token:
            return jsonify({"error": "Token d'authentification manquant."}), 401

        try:
            # PyJWT vérifie automatiquement la signature et la clé 'exp' si elle existe.
            # On utilise la clé secrète de la configuration de l'app.
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            
            # Stocker les informations de l'utilisateur dans l'objet `g` de Flask.
            # `g` est un objet global à la requête, accessible partout dans le code de la route.
            g.user = {
                'pseudo': payload['pseudo'],
                'roles': payload.get('roles', [])
            }

        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Le token a expiré."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token invalide."}), 401

        return f(*args, **kwargs)
    return decorated_function
