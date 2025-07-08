# message-service/app/auth.py

import jwt
from functools import wraps
from flask import request, jsonify, g, current_app
from datetime import datetime, timezone

def jwt_required(f):
    """
    Décorateur pour vérifier la validité d'un token JWT.
    
    Le token doit être fourni dans le header 'Authorization' sous la forme 'Bearer <token>'.
    Si le token est valide, ses informations (payload) sont stockées dans `g.user`
    et sont accessibles par la route décorée.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # 1. Récupérer le token depuis le header 'Authorization'
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            parts = auth_header.split()

            # Vérifier que le header est bien au format 'Bearer <token>'
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
            else:
                return jsonify({"error": "Format du header 'Authorization' invalide. Utilisez 'Bearer <token>'."}), 401

        if not token:
            return jsonify({"error": "Token manquant dans le header 'Authorization'."}), 401

        # 2. Essayer de décoder le token
        try:
            # Récupérer la clé secrète depuis la configuration de l'application Flask
            secret_key = current_app.config['JWT_SECRET_KEY']
            
            # Décoder le payload du token. L'algorithme HS256 est le plus courant.
            payload = jwt.decode(token, secret_key, algorithms=["HS256"])

            # 3. Vérification personnalisée de l'expiration (basée sur votre structure de token)
            if 'expiration' not in payload:
                 return jsonify({"error": "Le token est malformé (champ 'expiration' manquant)."}), 401
            
            expiration_timestamp = payload['expiration']
            current_timestamp = int(datetime.now(timezone.utc).timestamp())

            if current_timestamp > expiration_timestamp:
                # On peut lever l'erreur standard pour qu'elle soit attrapée par le 'except' ci-dessous
                raise jwt.ExpiredSignatureError("Le token a expiré.")

            # 4. Vérifier la présence des champs essentiels dans le payload
            if 'pseudo' not in payload or 'roles' not in payload:
                return jsonify({"error": "Le token est malformé (champs 'pseudo' ou 'roles' manquants)."}), 401

            # 5. Stocker les informations de l'utilisateur dans `g` pour un accès facile dans la route
            # `g` est un objet spécial de Flask qui ne persiste que pour une seule requête.
            g.user = payload

        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Le token a expiré."}), 401
        except jwt.InvalidTokenError:
            # Cette exception attrape les signatures invalides, les tokens malformés, etc.
            return jsonify({"error": "Token invalide."}), 401
        except Exception as e:
            # Attrape d'autres erreurs potentielles pour éviter de crasher le serveur
            print(f"Erreur inattendue lors de la validation du token: {e}")
            return jsonify({"error": "Erreur interne du serveur lors de la validation du token."}), 500

        # Si tout est OK, exécuter la fonction de la route originale
        return f(*args, **kwargs)

    return decorated_function