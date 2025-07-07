# app.py - Version avec base de données et gestion de 'reply_to'

import os
from datetime import datetime
from functools import wraps
from flask import Flask, jsonify, request
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy

# --- Chargement des variables d'environnement ---
load_dotenv()

# --- Configuration de l'application Flask ---
app = Flask(__name__)

# --- Configuration de la base de données ---
DB_USER = os.getenv('DB_USER', 'user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = os.getenv('DB_NAME', 'message_db')

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialisation de l'extension SQLAlchemy
db = SQLAlchemy(app)

# --- Modèle de données pour les messages (MODIFIÉ) ---
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_user = db.Column(db.String(80), nullable=False)
    channel = db.Column(db.String(80), nullable=False)
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    reply_to = db.Column(db.Integer, nullable=True) # Champ pour la réponse
    reactions = db.Column(db.String(255), default='')

    def to_dict(self):
        """Convertit l'objet Message en dictionnaire pour la réponse JSON."""
        return {
            "id": self.id,
            "from_user": self.from_user,
            "channel": self.channel,
            "text": self.text,
            "timestamp": self.timestamp.isoformat() + "Z",
            "reply_to": self.reply_to, # Champ ajouté à la réponse
            "reactions": self.reactions.split(',') if self.reactions else []
        }

# --- Décorateur JWT (inchangé) ---
def require_jwt(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print("INFO: Route protégée par @require_jwt (vérification à implémenter)")
        return f(*args, **kwargs)
    return decorated_function

# --- Routes ---
@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "service": "message-service"}), 200

@app.route('/msg', methods=['POST'])
@require_jwt
def post_message():
    """Route pour envoyer un message (MODIFIÉE pour 'reply_to')"""
    data = request.get_json()
    if not data or 'channel' not in data or 'text' not in data:
        return jsonify({"error": "Payload invalide. 'channel' et 'text' sont requis."}), 400

    author = "user_from_jwt"

    new_message = Message(
        from_user=author,
        channel=data['channel'],
        text=data['text']
    )

    # Gestion du champ facultatif 'reply_to'
    if 'reply_to' in data:
        try:
            # On s'assure que la valeur est bien un entier
            reply_to_id = int(data['reply_to'])
            # Optionnel : vérifier si le message parent existe vraiment
            # parent_message = Message.query.get(reply_to_id)
            # if not parent_message:
            #     return jsonify({"error": f"Le message avec l'ID {reply_to_id} n'existe pas."}), 404
            new_message.reply_to = reply_to_id
        except (ValueError, TypeError):
             return jsonify({"error": "'reply_to' doit être un ID de message valide (entier)."}), 400

    try:
        db.session.add(new_message)
        db.session.commit()
        print(f"INFO: Nouveau message stocké en BDD : {new_message.to_dict()}")
        return jsonify(new_message.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        print(f"ERREUR: {e}")
        return jsonify({"error": "Erreur lors de la sauvegarde du message."}), 500

@app.route('/msg', methods=['GET'])
def get_channel_messages():
    """Route pour récupérer les messages d'un canal depuis la BDD."""
    channel_name = request.args.get('channel')
    if not channel_name:
        return jsonify({"error": "Le paramètre 'channel' est requis."}), 400
    
    messages_query = Message.query.filter_by(channel=channel_name)
    
    # Pagination
    offset = request.args.get('offset', 0, type=int)
    limit = request.args.get('limit', 20, type=int)
    
    channel_messages = messages_query.order_by(Message.timestamp.desc()).offset(offset).limit(limit).all()
    
    return jsonify({"messages": [msg.to_dict() for msg in channel_messages]}), 200


# --- Point d'entrée pour lancer le serveur ---
if __name__ == '__main__':
    with app.app_context():
        # Crée les tables si elles n'existent pas
        db.create_all()
    app.run(host='0.0.0.0', port=5002, debug=True)