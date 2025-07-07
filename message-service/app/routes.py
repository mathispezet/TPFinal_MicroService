# app/routes.py

from flask import Blueprint, jsonify, request
from .models import Message
from . import db
from .auth import require_jwt

main_bp = Blueprint('main', __name__)

# =================================================================
# Routes de Base et Gestion des Messages
# =================================================================

@main_bp.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "service": "message-service"}), 200

@main_bp.route('/msg', methods=['POST'])
@require_jwt
def post_message():
    # ... (code inchangé)
    data = request.get_json()
    if not data or 'channel' not in data or 'text' not in data:
        return jsonify({"error": "Payload invalide. 'channel' et 'text' sont requis."}), 400
    author = "user_from_jwt"
    new_message = Message(from_user=author, channel=data['channel'], text=data['text'])
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
    # ... (code inchangé)
    channel_name = request.args.get('channel')
    if not channel_name:
        return jsonify({"error": "Le paramètre 'channel' est requis."}), 400
    messages_query = Message.query.filter_by(channel=channel_name, is_pinned=False) # On exclut les épinglés de la vue normale
    offset = request.args.get('offset', 0, type=int)
    limit = request.args.get('limit', 20, type=int)
    channel_messages = messages_query.order_by(Message.timestamp.desc()).offset(offset).limit(limit).all()
    return jsonify({"messages": [msg.to_dict() for msg in channel_messages]}), 200

# =================================================================
# Actions sur un message spécifique (Pin, Update, Delete)
# =================================================================

@main_bp.route('/msg/<int:id>/pin', methods=['POST'])
@require_jwt
def pin_message(id):
    """Route pour épingler un message."""
    message = Message.query.get_or_404(id)
    message.is_pinned = True
    db.session.commit()
    return jsonify(message.to_dict()), 200

@main_bp.route('/msg/<int:id>/pin', methods=['DELETE'])
@require_jwt
def unpin_message(id):
    """Route pour désépingler un message."""
    message = Message.query.get_or_404(id)
    message.is_pinned = False
    db.session.commit()
    return jsonify(message.to_dict()), 200

@main_bp.route('/msg/<int:id>', methods=['PUT'])
@require_jwt
def update_message(id):
    # TODO: Implémenter la logique de modification d'un message
    return jsonify({"message": f"Route PUT /msg/{id} à implémenter"}), 501

@main_bp.route('/msg/<int:id>', methods=['DELETE'])
@require_jwt
def delete_message(id):
    # TODO: Implémenter la logique de suppression d'un message
    return jsonify({}), 204

# =================================================================
# Fonctions Avancées (Thread, Pinned, Search)
# =================================================================

@main_bp.route('/msg/thread/<int:id>', methods=['GET'])
def get_message_thread(id):
    # ... (code inchangé)
    parent_message = Message.query.get_or_404(id)
    thread_messages = Message.query.filter_by(reply_to=id).order_by(Message.timestamp.asc()).all()
    response_data = {
        "parent_message": parent_message.to_dict(),
        "replies": [msg.to_dict() for msg in thread_messages]
    }
    return jsonify(response_data), 200

@main_bp.route('/msg/pinned', methods=['GET'])
def get_pinned_messages():
    """Récupère les messages épinglés pour un canal donné."""
    channel_name = request.args.get('channel')
    if not channel_name:
        return jsonify({"error": "Le paramètre 'channel' est requis."}), 400
    
    pinned_messages = Message.query.filter_by(
        channel=channel_name, 
        is_pinned=True
    ).order_by(Message.timestamp.desc()).all()
    
    return jsonify({"messages": [msg.to_dict() for msg in pinned_messages]}), 200

@main_bp.route('/msg/search', methods=['GET'])
def search_messages():
    """Recherche un mot-clé dans le texte de tous les messages."""
    query = request.args.get('q')
    if not query or len(query) < 3:
        return jsonify({"error": "Le paramètre de recherche 'q' est requis et doit contenir au moins 3 caractères."}), 400
    
    # Le pattern '%%' permet de trouver le mot n'importe où dans le texte
    search_pattern = f"%{query}%"
    
    # On peut aussi filtrer par canal si le paramètre est fourni
    channel_name = request.args.get('channel')
    
    query_builder = Message.query.filter(Message.text.like(search_pattern))
    
    if channel_name:
        query_builder = query_builder.filter_by(channel=channel_name)
        
    search_results = query_builder.order_by(Message.timestamp.desc()).all()
    
    return jsonify({"messages": [msg.to_dict() for msg in search_results]}), 200


# Squelettes restants
@main_bp.route('/msg/private', methods=['GET'])
@require_jwt
def get_private_messages():
    return jsonify({"message": "Route /msg/private à implémenter"}), 501
    
@main_bp.route('/msg/reaction', methods=['POST', 'DELETE'])
@require_jwt
def manage_reaction():
    return jsonify({"message": "Route pour les réactions à implémenter"}), 501