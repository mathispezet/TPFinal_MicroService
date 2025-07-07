# message-service/app/routes.py

from flask import Blueprint, jsonify, request
from datetime import datetime
from .auth import require_jwt

# Création d'un Blueprint pour organiser les routes du service de messages
messages_bp = Blueprint('messages', __name__)

# --- Simulation de la base de données (temporaire) ---
# NOTE : Normalement, on ne met pas d'état global ici. C'est une mesure
# temporaire pour adapter votre code actuel. L'objectif est de remplacer
# ceci par des appels à la base de données via les modèles (models.py).
messages_db = []
message_id_counter = 1


# --- Routes ---

@messages_bp.route('/health', methods=['GET'])
def health_check():
    """Route de santé pour vérifier que le service est en ligne."""
    return jsonify({"status": "ok", "service": "message-service"}), 200

# ... (Toutes vos autres routes vont ici, mais avec `@messages_bp.route(...)`)

@messages_bp.route('/msg', methods=['POST'])
@require_jwt
def post_message():
    """Route pour envoyer un message dans un canal public."""
    global message_id_counter
    data = request.get_json()
    if not data or 'channel' not in data or 'text' not in data:
        return jsonify({"error": "Payload invalide. 'channel' et 'text' sont requis."}), 400

    author = "user_from_jwt" # TODO: Extraire du JWT
    new_message = {
        "id": message_id_counter, "from_user": author, "to_user": None,
        "channel": data['channel'], "text": data['text'],
        "timestamp": datetime.utcnow().isoformat() + "Z", "reactions": []
    }
    messages_db.append(new_message)
    message_id_counter += 1
    return jsonify(new_message), 201

@messages_bp.route('/msg', methods=['GET'])
def get_channel_messages():
    """Récupère les messages d'un canal public avec pagination."""
    channel_name = request.args.get('channel')
    if not channel_name:
        return jsonify({"error": "Le paramètre 'channel' est requis."}), 400
    try:
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
    except ValueError:
        return jsonify({"error": "Les paramètres 'limit' et 'offset' doivent être des entiers."}), 400
    
    channel_messages = [msg for msg in messages_db if msg['channel'] == channel_name]
    paginated_messages = channel_messages[offset : offset + limit]
    return jsonify({"messages": paginated_messages}), 200

@messages_bp.route('/msg/<int:id>', methods=['PUT'])
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
    return jsonify(message_to_update), 200

@messages_bp.route('/msg/<int:id>', methods=['DELETE'])
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
    return jsonify({}), 204

@messages_bp.route('/msg/private', methods=['POST'])
@require_jwt
def post_private_message():
    """Envoie un message privé à un autre utilisateur."""
    global message_id_counter
    sender_pseudo = "user_from_jwt" # TODO: Extraire du JWT
    data = request.get_json()
    if not data or 'to' not in data or 'text' not in data:
        return jsonify({"error": "Payload invalide. 'to' et 'text' sont requis."}), 400

    new_private_message = {
        "id": message_id_counter, "from_user": sender_pseudo, "to_user": data['to'],
        "channel": None, "text": data['text'],
        "timestamp": datetime.utcnow().isoformat() + "Z", "reactions": []
    }
    messages_db.append(new_private_message)
    message_id_counter += 1
    return jsonify(new_private_message), 201

@messages_bp.route('/msg/private', methods=['GET'])
@require_jwt
def get_private_messages():
    """Récupère la conversation privée entre deux utilisateurs."""
    user1 = request.args.get('from')
    user2 = request.args.get('to')
    if not user1 or not user2:
        return jsonify({"error": "Les paramètres 'from' et 'to' sont requis."}), 400

    current_user_pseudo = "user_from_jwt" # TODO: Extraire du JWT
    if current_user_pseudo not in [user1, user2]:
        return jsonify({"error": "Accès non autorisé à cette conversation privée."}), 403

    conversation = [
        msg for msg in messages_db 
        if (msg.get('from_user') == user1 and msg.get('to_user') == user2) or \
           (msg.get('from_user') == user2 and msg.get('to_user') == user1)
    ]
    sorted_conversation = sorted(conversation, key=lambda m: m['timestamp'])
    return jsonify({"messages": sorted_conversation}), 200

# Ajoutez ici les autres squelettes de routes (reaction, pinned, etc.) de la même manière
