# app.py - Version avec la route DELETE /msg/<id> fonctionnelle

import os
from datetime import datetime
from functools import wraps
from flask import Flask, jsonify, request
from dotenv import load_dotenv

# ... (le début du fichier ne change pas) ...
# ... (les fonctions health_check, post_message, get_channel_messages, update_message ne changent pas) ...

load_dotenv()
app = Flask(__name__)
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'default-super-secret-key-for-dev')
app.config['SECRET_KEY'] = JWT_SECRET_KEY
messages_db = []
message_id_counter = 1

def require_jwt(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print("INFO: Route protégée par @require_jwt (vérification à implémenter)")
        return f(*args, **kwargs)
    return decorated_function

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "service": "message-service"}), 200

@app.route('/msg', methods=['POST'])
@require_jwt
def post_message():
    global message_id_counter
    data = request.get_json()
    if not data or 'channel' not in data or 'text' not in data:
        return jsonify({"error": "Payload invalide. 'channel' et 'text' sont requis."}), 400
    author = "user_from_jwt"
    new_message = {
        "id": message_id_counter, "from_user": author, "channel": data['channel'],
        "text": data['text'], "timestamp": datetime.utcnow().isoformat() + "Z", "reactions": []
    }
    messages_db.append(new_message)
    message_id_counter += 1
    print(f"INFO: Nouveau message stocké : {new_message}")
    return jsonify(new_message), 201

@app.route('/msg', methods=['GET'])
def get_channel_messages():
    channel_name = request.args.get('channel')
    if not channel_name:
        return jsonify({"error": "Le paramètre 'channel' est requis."}), 400
    try:
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
    except ValueError:
        return jsonify({"error": "Les paramètres 'limit' et 'offset' doivent être des nombres entiers."}), 400
    channel_messages = [msg for msg in messages_db if msg['channel'] == channel_name]
    paginated_messages = channel_messages[offset : offset + limit]
    return jsonify({"messages": paginated_messages}), 200

@app.route('/msg/<int:id>', methods=['PUT'])
@require_jwt
def update_message(id):
    current_user_pseudo = "user_from_jwt" 
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "Le champ 'text' est manquant dans le corps de la requête."}), 400
    message_to_update = next((msg for msg in messages_db if msg['id'] == id), None)
    if not message_to_update:
        return jsonify({"error": f"Message avec l'ID {id} non trouvé."}), 404
    if message_to_update['from_user'] != current_user_pseudo:
        return jsonify({"error": "Action non autorisée. Vous n'êtes pas l'auteur de ce message."}), 403
    message_to_update['text'] = data['text']
    print(f"INFO: Message {id} mis à jour : {message_to_update}")
    return jsonify(message_to_update), 200


# --- VERSION MISE À JOUR ---
@app.route('/msg/<int:id>', methods=['DELETE'])
@require_jwt
def delete_message(id):
    """
    Supprime un message existant.
    Vérifie que l'utilisateur est bien l'auteur du message.
    """
    # TODO: Cette information viendra du décorateur @require_jwt
    current_user_pseudo = "user_from_jwt"

    message_to_delete = next((msg for msg in messages_db if msg['id'] == id), None)

    if not message_to_delete:
        return jsonify({"error": f"Message avec l'ID {id} non trouvé."}), 404

    if message_to_delete['from_user'] != current_user_pseudo:
        return jsonify({"error": "Action non autorisée. Vous n'êtes pas l'auteur de ce message."}), 403

    messages_db.remove(message_to_delete)
    
    print(f"INFO: Message {id} supprimé.")
    return jsonify({}), 204

# ... (le reste du fichier ne change pas) ...

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
