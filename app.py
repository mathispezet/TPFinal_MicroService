# app.py - Version fusionnée pour le message-service (Groupe 2)

import os
from datetime import datetime
from functools import wraps
from flask import Flask, jsonify, request
from dotenv import load_dotenv
# import jwt # À importer quand vous gérerez les JWT
# from sqlalchemy import ... # À importer pour la BDD

# --- Chargement des variables d'environnement ---
# Charge les variables depuis un fichier .env (très utile pour les secrets)
load_dotenv()

# --- Configuration de l'application Flask ---
app = Flask(__name__)
# On récupère la clé secrète depuis les variables d'environnement
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'default-super-secret-key-for-dev')
app.config['SECRET_KEY'] = JWT_SECRET_KEY

# --- Simulation de la base de données (on garde celle de votre camarade pour commencer) ---
messages_db = []
message_id_counter = 1

# --- Décorateur pour la vérification JWT (à compléter) ---
def require_jwt(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # ... (La logique de vérification du token ira ici) ...
        # Pour l'instant, on laisse passer pour pouvoir tester les routes.
        print("INFO: Route protégée par @require_jwt (vérification à implémenter)")
        return f(*args, **kwargs)
    return decorated_function

# =================================================================
# Routes de Base et de Santé
# =================================================================

@app.route('/', methods=['GET'])
def health_check():
    """Route simple pour vérifier que le service est bien en ligne."""
    return jsonify({"status": "ok", "service": "message-service"}), 200

# =================================================================
# 1. Cœur du Service (Routes déjà implémentées par votre camarade)
# =================================================================

@app.route('/msg', methods=['POST'])
@require_jwt
def post_message():
    """Route pour envoyer un message. Logique de votre camarade intégrée."""
    global message_id_counter
    
    data = request.get_json()
    if not data or 'channel' not in data or 'text' not in data:
        return jsonify({"error": "Payload invalide. 'channel' et 'text' sont requis."}), 400

    # TODO: Extraire le vrai pseudo depuis le token JWT
    author = "user_from_jwt"

    new_message = {
        "id": message_id_counter,
        "from_user": author,  # Renommé 'from_user' pour la clarté
        "channel": data['channel'],
        "text": data['text'],
        "timestamp": datetime.utcnow().isoformat() + "Z", # Format ISO 8601
        "reactions": []
    }
    
    messages_db.append(new_message)
    message_id_counter += 1
    
    print(f"INFO: Nouveau message stocké : {new_message}")
    return jsonify(new_message), 201

@app.route('/msg', methods=['GET'])
def get_channel_messages():
    """Route pour récupérer les messages d'un canal. Logique de votre camarade intégrée."""
    channel_name = request.args.get('channel')
    if not channel_name:
        return jsonify({"error": "Le paramètre 'channel' est requis."}), 400

    channel_messages = [msg for msg in messages_db if msg['channel'] == channel_name]

    # TODO: Ajouter la pagination (limit, offset)
    
    return jsonify({"messages": channel_messages}), 200

# =================================================================
# 2. Compléter : Gestion et Réactions (Squelette à implémenter)
# =================================================================

@app.route('/msg/<int:id>', methods=['PUT'])
@require_jwt
def update_message(id):
    # TODO: Implémenter la logique de modification d'un message
    return jsonify({"message": f"Route PUT /msg/{id} à implémenter"}), 501

@app.route('/msg/<int:id>', methods=['DELETE'])
@require_jwt
def delete_message(id):
    # TODO: Implémenter la logique de suppression d'un message
    return jsonify({}), 204

@app.route('/msg/reaction', methods=['POST', 'DELETE'])
@require_jwt
def manage_reaction():
    # TODO: Implémenter l'ajout/suppression d'une réaction
    return jsonify({"message": "Route pour les réactions à implémenter"}), 501

# =================================================================
# 3. Avancé : Fonctions Supplémentaires (Squelette à implémenter)
# =================================================================

@app.route('/msg/private', methods=['GET'])
@require_jwt
def get_private_messages():
    return jsonify({"message": "Route /msg/private à implémenter"}), 501

@app.route('/msg/pinned', methods=['GET'])
def get_pinned_messages():
    return jsonify({"message": "Route /msg/pinned à implémenter"}), 501

@app.route('/msg/thread/<int:id>', methods=['GET'])
def get_message_thread(id):
    return jsonify({"message": f"Route /msg/thread/{id} à implémenter"}), 501

@app.route('/msg/search', methods=['GET'])
def search_messages():
    return jsonify({"message": "Route /msg/search à implémenter"}), 501

# --- Point d'entrée pour lancer le serveur ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
