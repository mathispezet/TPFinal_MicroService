# app.py - Version avec gestion des fils de discussion (threads)

import os
from datetime import datetime
from functools import wraps
from flask import Flask, jsonify, request
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy

# ... (Toute la configuration du début reste identique) ...
load_dotenv()
app = Flask(__name__)
DB_USER = os.getenv('DB_USER', 'user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = os.getenv('DB_NAME', 'message_db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Modèle de données pour les messages (inchangé) ---
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_user = db.Column(db.String(80), nullable=False)
    channel = db.Column(db.String(80), nullable=False)
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    reply_to = db.Column(db.Integer, nullable=True)
    reactions = db.Column(db.String(255), default='')

    def to_dict(self):
        return {
            "id": self.id,
            "from_user": self.from_user,
            "channel": self.channel,
            "text": self.text,
            "timestamp": self.timestamp.isoformat() + "Z",
            "reply_to": self.reply_to,
            "reactions": self.reactions.split(',') if self.reactions else []
        }

# --- Décorateur JWT (inchangé) ---
def require_jwt(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print("INFO: Route protégée par @require_jwt (vérification à implémenter)")
        return f(*args, **kwargs)
    return decorated_function

# --- Routes de base et de gestion des messages (inchangées) ---
@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "service": "message-service"}), 200

@app.route('/msg', methods=['POST'])
@require_jwt
def post_message():
    # ... (code de post_message inchangé)
    data = request.get_json()
    if not data or 'channel' not in data or 'text' not in data:
        return jsonify({"error": "Payload invalide. 'channel' et 'text' sont requis."}), 400
    author = "user_from_jwt"
    new_message = Message(
        from_user=author, channel=data['channel'], text=data['text']
    )
    if 'reply_to' in data:
        try:
            new_message.reply_to = int(data['reply_to'])
        except (ValueError, TypeError):
             return jsonify({"error": "'reply_to' doit être un ID de message valide (entier)."}), 400
    try:
        db.session.add(new_message)
        db.session.commit()
        return jsonify(new_message.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Erreur lors de la sauvegarde du message."}), 500

@app.route('/msg', methods=['GET'])
def get_channel_messages():
    # ... (code de get_channel_messages inchangé)
    channel_name = request.args.get('channel')
    if not channel_name:
        return jsonify({"error": "Le paramètre 'channel' est requis."}), 400
    messages_query = Message.query.filter_by(channel=channel_name)
    offset = request.args.get('offset', 0, type=int)
    limit = request.args.get('limit', 20, type=int)
    channel_messages = messages_query.order_by(Message.timestamp.desc()).offset(offset).limit(limit).all()
    return jsonify({"messages": [msg.to_dict() for msg in channel_messages]}), 200

# ... (Les autres routes à implémenter restent inchangées) ...
@app.route('/msg/<int:id>', methods=['PUT'])
@require_jwt
def update_message(id):
    return jsonify({"message": f"Route PUT /msg/{id} à implémenter"}), 501
@app.route('/msg/<int:id>', methods=['DELETE'])
@require_jwt
def delete_message(id):
    return jsonify({}), 204
@app.route('/msg/reaction', methods=['POST', 'DELETE'])
@require_jwt
def manage_reaction():
    return jsonify({"message": "Route pour les réactions à implémenter"}), 501

# =================================================================
# Avancé : Fonctions Supplémentaires
# =================================================================

# === NOUVELLE FONCTIONNALITÉ IMPLÉMENTÉE ===
@app.route('/msg/thread/<int:id>', methods=['GET'])
def get_message_thread(id):
    """Récupère toutes les réponses à un message donné (un fil de discussion)."""
    
    # 1. Vérifier que le message parent existe
    parent_message = Message.query.get(id)
    if not parent_message:
        return jsonify({"error": f"Le message parent avec l'ID {id} n'existe pas."}), 404

    # 2. Récupérer tous les messages qui répondent à cet ID
    thread_messages = Message.query.filter_by(reply_to=id).order_by(Message.timestamp.asc()).all()

    # 3. Formater la réponse
    # On peut inclure le message parent pour le contexte, et la liste des réponses.
    response_data = {
        "parent_message": parent_message.to_dict(),
        "replies": [msg.to_dict() for msg in thread_messages]
    }
    
    return jsonify(response_data), 200

# ... (Les autres routes avancées restent à faire) ...
@app.route('/msg/private', methods=['GET'])
@require_jwt
def get_private_messages():
    return jsonify({"message": "Route /msg/private à implémenter"}), 501

@app.route('/msg/pinned', methods=['GET'])
def get_pinned_messages():
    return jsonify({"message": "Route /msg/pinned à implémenter"}), 501

@app.route('/msg/search', methods=['GET'])
def search_messages():
    return jsonify({"message": "Route /msg/search à implémenter"}), 501


# --- Point d'entrée pour lancer le serveur ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5002, debug=True)