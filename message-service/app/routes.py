# message-service/app/routes.py

from flask import Blueprint, jsonify, request, g
from sqlalchemy import or_
from .models import db, Message
from .auth import jwt_required

# On utilise un nom de Blueprint descriptif
messages_bp = Blueprint('messages', __name__)

# =================================================================
# Route de Santé
# =================================================================

@messages_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "service": "message-service"}), 200

# =================================================================
# Routes pour les Messages Publics
# =================================================================

@messages_bp.route('/msg', methods=['POST'])
@jwt_required
def post_message():
    data = request.get_json()
    if not data or 'channel' not in data or 'text' not in data:
        return jsonify({"error": "Payload invalide. 'channel' et 'text' sont requis."}), 400

    new_message = Message(
        from_user=g.user['pseudo'],
        channel=data['channel'],
        text=data['text'],
        reply_to=data.get('reply_to')
    )
    db.session.add(new_message)
    db.session.commit()
    return jsonify(new_message.to_dict()), 201

@messages_bp.route('/msg', methods=['GET'])
def get_channel_messages():
    channel_name = request.args.get('channel')
    if not channel_name:
        return jsonify({"error": "Le paramètre 'channel' est requis."}), 400
    
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))

    # Logique fusionnée : on exclut les messages épinglés de la vue normale
    messages_query = Message.query.filter_by(channel=channel_name, is_pinned=False)\
                                  .order_by(Message.timestamp.desc())\
                                  .offset(offset)\
                                  .limit(limit).all()
    
    return jsonify({"messages": [msg.to_dict() for msg in messages_query]}), 200

# =================================================================
# Routes pour la Gestion d'un Message Spécifique (Update, Delete, Pin)
# =================================================================

@messages_bp.route('/msg/<string:id>', methods=['PUT'])
@jwt_required
def update_message(id):
    # Logique restaurée et complète
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "Le champ 'text' est manquant."}), 400

    message = Message.query.get_or_404(id)
    if message.from_user != g.user['pseudo']:
        return jsonify({"error": "Action non autorisée."}), 403

    message.text = data['text']
    db.session.commit()
    return jsonify({"status": "success", "message": "Message mis à jour avec succès."}), 200

@messages_bp.route('/msg/<string:id>', methods=['DELETE'])
@jwt_required
def delete_message(id):
    # Logique restaurée et complète
    message = Message.query.get_or_404(id)
    if message.from_user != g.user['pseudo']:
        return jsonify({"error": "Action non autorisée."}), 403

    db.session.delete(message)
    db.session.commit()
    return jsonify({"status": "success", "message": "Message supprimé avec succès."}), 200

@messages_bp.route('/msg/<string:id>/pin', methods=['POST'])
@jwt_required
def pin_message(id):
    # Logique conservée de votre code
    message = Message.query.get_or_404(id)
    # TODO: Ajouter une vérification des droits (seul un modérateur peut épingler)
    message.is_pinned = True
    db.session.commit()
    return jsonify(message.to_dict()), 200

@messages_bp.route('/msg/<string:id>/pin', methods=['DELETE'])
@jwt_required
def unpin_message(id):
    # Logique conservée de votre code
    message = Message.query.get_or_404(id)
    # TODO: Ajouter une vérification des droits
    message.is_pinned = False
    db.session.commit()
    return jsonify(message.to_dict()), 200

# =================================================================
# Routes Avancées (Private, Pinned, Thread, Search)
# =================================================================

@messages_bp.route('/msg/private', methods=['POST'])
@jwt_required
def post_private_message():
    # Logique restaurée et complète
    data = request.get_json()
    if not data or 'to' not in data or 'text' not in data:
        return jsonify({"error": "Payload invalide. 'to' et 'text' sont requis."}), 400

    new_message = Message(from_user=g.user['pseudo'], to_user=data['to'], text=data['text'])
    db.session.add(new_message)
    db.session.commit()
    return jsonify(new_message.to_dict()), 201

@messages_bp.route('/msg/private', methods=['GET'])
@jwt_required
def get_private_messages():
    # Logique restaurée et complète
    user1 = request.args.get('from')
    user2 = request.args.get('to')
    if not user1 or not user2:
        return jsonify({"error": "Les paramètres 'from' et 'to' sont requis."}), 400

    if g.user['pseudo'] not in [user1, user2]:
        return jsonify({"error": "Accès non autorisé."}), 403

    conversation = Message.query.filter(or_((Message.from_user == user1) & (Message.to_user == user2), (Message.from_user == user2) & (Message.to_user == user1))).order_by(Message.timestamp.asc()).all()
    return jsonify({"messages": [msg.to_dict() for msg in conversation]}), 200

@messages_bp.route('/msg/pinned', methods=['GET'])
def get_pinned_messages():
    # Logique conservée de votre code
    channel_name = request.args.get('channel')
    if not channel_name:
        return jsonify({"error": "Le paramètre 'channel' est requis."}), 400
    
    pinned_messages = Message.query.filter_by(channel=channel_name, is_pinned=True).order_by(Message.timestamp.desc()).all()
    return jsonify({"messages": [msg.to_dict() for msg in pinned_messages]}), 200

@messages_bp.route('/msg/thread/<string:id>', methods=['GET'])
def get_message_thread(id):
    # Logique conservée et adaptée aux UUIDs
    parent_message = Message.query.get_or_404(id)
    thread_messages = Message.query.filter_by(reply_to=id).order_by(Message.timestamp.asc()).all()
    response_data = {
        "parent_message": parent_message.to_dict(),
        "replies": [msg.to_dict() for msg in thread_messages]
    }
    return jsonify(response_data), 200

@messages_bp.route('/msg/search', methods=['GET'])
def search_messages():
    # Logique conservée de votre code
    query = request.args.get('q')
    if not query or len(query) < 3:
        return jsonify({"error": "Le paramètre 'q' doit contenir au moins 3 caractères."}), 400
    
    search_pattern = f"%{query}%"
    channel_name = request.args.get('channel')
    
    query_builder = Message.query.filter(Message.text.ilike(search_pattern))
    if channel_name:
        query_builder = query_builder.filter_by(channel=channel_name)
        
    search_results = query_builder.order_by(Message.timestamp.desc()).all()
    return jsonify({"messages": [msg.to_dict() for msg in search_results]}), 200

# =================================================================
# Squelette Final
# =================================================================

@messages_bp.route('/msg/reaction', methods=['POST', 'DELETE'])
@jwt_required
def manage_reaction():
    """Ajoute ou retire une réaction à un message."""
    # TODO: Implémenter la logique de cette fonction
    return jsonify({"message": "Route pour les réactions à implémenter"}), 501
