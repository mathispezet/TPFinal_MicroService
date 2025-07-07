# app/routes.py

from flask import Blueprint, jsonify, request
from .models import Message
from . import db
from .auth import require_jwt

# Création d'un Blueprint. Toutes les routes définies ici commenceront par ce préfixe si on le souhaite.
main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "service": "message-service"}), 200

@main_bp.route('/msg', methods=['POST'])
@require_jwt
def post_message():
    # ... (le code de la fonction est exactement le même)
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

@main_bp.route('/msg', methods=['GET'])
def get_channel_messages():
    # ... (le code de la fonction est exactement le même)
    channel_name = request.args.get('channel')
    if not channel_name:
        return jsonify({"error": "Le paramètre 'channel' est requis."}), 400
    messages_query = Message.query.filter_by(channel=channel_name)
    offset = request.args.get('offset', 0, type=int)
    limit = request.args.get('limit', 20, type=int)
    channel_messages = messages_query.order_by(Message.timestamp.desc()).offset(offset).limit(limit).all()
    return jsonify({"messages": [msg.to_dict() for msg in channel_messages]}), 200

@main_bp.route('/msg/thread/<int:id>', methods=['GET'])
def get_message_thread(id):
    # ... (le code de la fonction est exactement le même)
    parent_message = Message.query.get(id)
    if not parent_message:
        return jsonify({"error": f"Le message parent avec l'ID {id} n'existe pas."}), 404
    thread_messages = Message.query.filter_by(reply_to=id).order_by(Message.timestamp.asc()).all()
    response_data = {
        "parent_message": parent_message.to_dict(),
        "replies": [msg.to_dict() for msg in thread_messages]
    }
    return jsonify(response_data), 200

# ... (Ajoutez ici les autres squelettes de routes de la même manière, en utilisant @main_bp.route)