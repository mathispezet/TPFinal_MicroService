# app.py

import os
from datetime import datetime
from flask import Flask, jsonify, request
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

app = Flask(__name__)

# --- Configuration (à externaliser plus tard) ---
# Clé secrète pour vérifier les JWT. DOIT être la même que celle du user-service.
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'default-super-secret-key-for-dev')

# --- Simulation de la base de données ---
# Une liste en mémoire pour commencer. À remplacer par une vraie BDD.
messages_db = []
message_id_counter = 1

# --- Routes ---

@app.route('/', methods=['GET'])
def health_check():
    """Route simple pour vérifier que le service est bien en ligne."""
    return jsonify({"status": "ok", "service": "message-service"}), 200

@app.route('/msg', methods=['POST'])
def post_message():
    """
    Route pour envoyer un message dans un canal.
    Le payload doit contenir 'channel' et 'text'.
    L'auteur du message sera extrait du token JWT (à implémenter).
    """
    global message_id_counter
    
    data = request.get_json()
    if not data or 'channel' not in data or 'text' not in data:
        return jsonify({"error": "Payload invalide. 'channel' et 'text' sont requis."}), 400

    # TODO: Étape 2 - Vérifier le token JWT ici
    # 1. Récupérer le header 'Authorization: Bearer <token>'
    # 2. Décoder le token avec PyJWT et la clé secrète
    # 3. Extraire le 'pseudo' de l'utilisateur depuis le payload du token
    # author = decoded_token['pseudo']
    
    # Pour l'instant, on utilise un auteur par défaut
    author = "user_from_jwt" # À remplacer par le vrai pseudo du token

    new_message = {
        "id": message_id_counter,
        "from": author,
        "channel": data['channel'],
        "text": data['text'],
        "timestamp": datetime.utcnow().isoformat(),
        "reactions": {} # ex: {"👍": ["roger", "ginette"]}
    }
    
    # TODO: Étape 3 - Vérifier que le canal existe en appelant le channel-service
    # Par exemple : response = requests.get(f"http://channel-service:5003/channel/{data['channel']}")
    
    messages_db.append(new_message)
    message_id_counter += 1
    
    print(f"Nouveau message stocké : {new_message}")

    return jsonify(new_message), 201

@app.route('/msg', methods=['GET'])
def get_messages():
    """
    Route pour récupérer les messages d'un canal.
    Utilise un paramètre de requête : /msg?channel=tech
    """
    channel_name = request.args.get('channel')
    if not channel_name:
        return jsonify({"error": "Le paramètre 'channel' est requis."}), 400

    # Filtre les messages pour le canal demandé
    channel_messages = [msg for msg in messages_db if msg['channel'] == channel_name]

    # TODO: Ajouter la pagination (offset, limit) comme suggéré dans le TP
    
    return jsonify(channel_messages), 200


if __name__ == '__main__':
    # Le port 5002 est celui spécifié dans le document pour le message-service
    app.run(host='0.0.0.0', port=5002, debug=True)