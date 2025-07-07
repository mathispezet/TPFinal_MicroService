# app/routes.py
from flask import Blueprint, request, jsonify
from .models import Message
from . import db

# Créer un Blueprint. C'est comme un mini-Flask app.
bp = Blueprint('main', __name__)

@bp.route('/msg', methods=['POST'])
def post_message():
    data = request.get_json()
    if not data or 'channel' not in data or 'text' not in data:
        return jsonify({"error": "Payload invalide"}), 400
    
    # TODO: Extraire 'author' du JWT
    author_pseudo = "user_from_jwt" 

    new_message = Message(
        author_pseudo=author_pseudo,
        channel_name=data['channel'],
        text=data['text']
    )
    db.session.add(new_message)
    db.session.commit()
    
    return jsonify(new_message.to_dict()), 201

@bp.route('/msg', methods=['GET'])
def get_messages():
    channel_name = request.args.get('channel')
    if not channel_name:
        return jsonify({"error": "Le paramètre 'channel' est requis"}), 400

    messages = Message.query.filter_by(channel_name=channel_name).all()
    return jsonify([msg.to_dict() for msg in messages]), 200

# Ajoutez vos autres routes ici (PUT, DELETE, etc.)