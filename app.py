# app.py - Version complète avec gestion des messages publics et privés

import os
from datetime import datetime
from functools import wraps
from flask import Flask, jsonify, request
from dotenv import load_dotenv

# --- Chargement des variables d'environnement ---
load_dotenv()

# --- Configuration de l'application Flask ---
app = Flask(__name__)
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'default-super-secret-key-for-dev')
app.config['SECRET_KEY'] = JWT_SECRET_KEY

# --- Simulation de la base de données ---
messages_db = []
message_id_counter = 1

# --- Décorateur pour la vérification JWT (à compléter) ---
def require_jwt(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # TODO: Implémenter la vraie logique de décodage JWT ici
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
# 1. Cœur du Service : Messages Publics
# =================================================================

@app.route('/msg', methods=['POST'])
@require_jwt
def post_message():
    """Route pour envoyer un message dans un canal public."""
    global message_id_counter
    data = request.get_json()
    if not data or 'channel' not in data or 'text' not in data:
        return jsonify({"error": "Payload invalide. 'channel' et 'text' sont requis."}), 400

    # TODO: Extraire le vrai pseudo depuis le token JWT
    author = "user_from_jwt"

    new_message = {
        "id": message_id_counter,
        "from_user": author,
        "to_user": None,
        "channel": data['channel'],
        "text": data['text'],
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "reactions": []
    }
    messages_db.append(new_message)
    message_id_counter += 1
    print(f"INFO: Nouveau message public stocké : {new_message}")
    return jsonify(new_message), 201

@app.route('/msg', methods=['GET'])
def get_channel_messages():
    """Récupère les messages d'un canal public avec pagination."""
    channel_name = request.args.get('channel')
    if not channel_name:
        return jsonify({"error": "Le paramètre 'channel' est requis."}), 400
    try:
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
    except ValueError:
        return jsonify({"error": "Les paramètres 'limit' et 'offset' doivent être des nombres entiers."}), 400
    
    # On ne prend que les messages de canal (ceux où 'channel' n'est pas None)
    channel_messages = [msg for msg in messages_db if msg['channel'] == channel_name]
    paginated_messages = channel_messages[offset : offset + limit]
    return jsonify({"messages": paginated_messages}), 200

# =================================================================
# 2. Gestion des Messages (Modification, Suppression)
# =================================================================

@app.route('/msg/<int:id>', methods=['PUT'])
@require_jwt
def update_message(id):
    """Modifie le contenu d'un de ses propres messages."""
    current_user_pseudo = "user_from_jwt" # TODO: Remplacer par le pseudo du JWT
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "Le champ 'text' est manquant."}), 400

    message_to_update = next((msg for msg in messages_db if msg['id'] == id), None)
    if not message_to_update:
        return jsonify({"error": f"Message avec l'ID {id} non trouvé."}), 404

    if message_to_update['from_user'] != current_user_pseudo:
        return jsonify({"error": "Action non autorisée. Vous n'êtes pas l'auteur."}), 403

    message_to_update['text'] = data['text']
    print(f"INFO: Message {id} mis à jour.")
    return jsonify(message_to_update), 200

@app.route('/msg/<int:id>', methods=['DELETE'])
@require_jwt
def delete_message(id):
    """Supprime un de ses propres messages."""
    current_user_pseudo = "user_from_jwt" # TODO: Remplacer par le pseudo du JWT

    message_to_delete = next((msg for msg in messages_db if msg['id'] == id), None)
    if not message_to_delete:
        return jsonify({"error": f"Message avec l'ID {id} non trouvé."}), 404

    if message_to_delete['from_user'] != current_user_pseudo:
        return jsonify({"error": "Action non autorisée. Vous n'êtes pas l'auteur."}), 403

    messages_db.remove(message_to_delete)
    print(f"INFO: Message {id} supprimé.")
    return jsonify({}), 204

# =================================================================
# 3. Avancé : Messages Privés et autres fonctionnalités
# =================================================================

@app.route('/msg/private', methods=['POST'])
@require_jwt
def post_private_message():
    """Envoie un message privé à un autre utilisateur."""
    global message_id_counter
    sender_pseudo = "user_from_jwt" # TODO: Remplacer par le pseudo du JWT

    data = request.get_json()
    if not data or 'to' not in data or 'text' not in data:
        return jsonify({"error": "Payload invalide. 'to' et 'text' sont requis."}), 400

    new_private_message = {
        "id": message_id_counter, "from_user": sender_pseudo, "to_user": data['to'],
        "channel": None, "text": data['text'], "timestamp": datetime.utcnow().isoformat() + "Z",
        "reactions": []
    }
    messages_db.append(new_private_message)
    message_id_counter += 1
    print(f"INFO: Nouveau message privé stocké : {new_private_message}")
    return jsonify(new_private_message), 201

@app.route('/msg/private', methods=['GET'])
@require_jwt
def get_private_messages():
    """Récupère la conversation privée entre deux utilisateurs."""
    user1 = request.args.get('from')
    user2 = request.args.get('to')
    if not user1 or not user2:
        return jsonify({"error": "Les paramètres 'from' et 'to' sont requis."}), 400

    current_user_pseudo = "user_from_jwt" # TODO: Remplacer par le pseudo du JWT

    if current_user_pseudo not in [user1, user2]:
        return jsonify({"error": "Accès non autorisé à cette conversation privée."}), 403

    conversation = [
        msg for msg in messages_db 
        if (msg.get('from_user') == user1 and msg.get('to_user') == user2) or \
           (msg.get('from_user') == user2 and msg.get('to_user') == user1)
    ]
    sorted_conversation = sorted(conversation, key=lambda m: m['timestamp'])
    return jsonify({"messages": sorted_conversation}), 200


# --- Squelettes des fonctionnalités restantes ---

@app.route('/msg/reaction', methods=['POST', 'DELETE'])
@require_jwt
def manage_reaction():
    # TODO: Implémenter l'ajout/suppression d'une réaction
    return jsonify({"message": "Route pour les réactions à implémenter"}), 501

@app.route('/msg/pinned', methods=['GET'])
def get_pinned_messages():
    # TODO: Implémenter la logique pour récupérer les messages épinglés d'un canal.
    return jsonify({"message": "Route /msg/pinned à implémenter"}), 501

@app.route('/msg/thread/<int:id>', methods=['GET'])
def get_message_thread(id):
    # TODO: Récupérer tous les messages qui sont une réponse au message <id>.
    return jsonify({"message": f"Route /msg/thread/{id} à implémenter"}), 501

@app.route('/msg/search', methods=['GET'])
def search_messages():
    # TODO: Implémenter la recherche par mot-clé.
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "Le paramètre 'q' est requis"}), 400
    return jsonify({"message": "Route /msg/search à implémenter"}), 501


# --- Point d'entrée pour lancer le serveur ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
