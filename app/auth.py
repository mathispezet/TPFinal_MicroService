# message-service/app/auth.py

import jwt
import os
from functools import wraps
from flask import request, jsonify, g

# =========================================================================
# ===                  CHARGEMENT DE LA CONFIGURATION                   ===
# =========================================================================
# On charge la configuration depuis les variables d'environnement ICI,
# au niveau du module. C'est la manière correcte de le faire en dehors
# du contexte d'une requête.

FLASK_ENV = os.environ.get('FLASK_ENV', 'production') # 'production' par défaut pour la sécurité
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'une-clé-secrète-par-défaut-pour-la-sécurité')


def jwt_required(f):
    """
    Décorateur pour vérifier la validité d'un token JWT.
    
    En mode 'development' (FL   ASK_ENV='development'), la vérification est
    contournée et un utilisateur factice est créé.
    
    Sinon, le token est vérifié et le payload est stocké dans g.user.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        
        print("auth",  request.headers, flush=True)

        # --- PARTIE POUR LE BYPASS EN DÉVELOPPEMENT ---
        if FLASK_ENV == 'development':
            # Créer un utilisateur factice pour les tests
            g.user = {
                'pseudo': 'dev-user',
                'roles': ['user', 'admin'],  # Donnez tous les droits pour faciliter les tests
                'message': 'JWT bypass is active for development'
            }
            # Exécuter directement la fonction de la route
            return f(*args, **kwargs)
        

        # --- PARTIE POUR LA VRAIE VÉRIFICATION EN PRODUCTION ---
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            parts = auth_header.split()

            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
            else:
                return jsonify({"error": "Malformed Authorization header. Use 'Bearer <token>'."}), 401

        if not token:
            return jsonify({"error": "Authentication token is missing from the Authorization header."}), 401

        try:
            # On utilise la clé secrète chargée au début du fichier
            # PyJWT s'occupe de TOUT : signature, expiration (champ 'exp'), et format.
            # L'option 'verify_exp' est True par défaut.
            payload = jwt.decode(
                token, 
                JWT_SECRET_KEY, 
                algorithms=["HS256"]
            )

            # Vérification simple que les champs attendus sont présents dans le payload
            if 'pseudo' not in payload or 'roles' not in payload:
                # Cette erreur est spécifique à notre application, pas une erreur JWT standard
                return jsonify({"error": "Token is malformed (missing 'pseudo' or 'roles' fields)."}), 401

            # Si tout est bon, on stocke le payload dans g.user
            g.user = payload

        except jwt.ExpiredSignatureError:
            # Cette exception est levée automatiquement par jwt.decode() si le champ 'exp' est dans le passé.
            return jsonify({"error": "Token has expired."}), 401
        except jwt.InvalidTokenError:
            # Ceci attrape toutes les autres erreurs JWT (mauvaise signature, token malformé, etc.)
            return jsonify({"error": "Invalid token."}), 401
        except Exception as e:
            # Attrape les erreurs imprévues pour le débogage
            # En production, on pourrait vouloir logger cette erreur sans l'exposer au client.
            print(f"Unexpected error during token validation: {e}")
            return jsonify({"error": "Internal server error during token validation."}), 500

        return f(*args, **kwargs)

    return decorated_function