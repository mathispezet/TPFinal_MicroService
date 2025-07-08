# message-service/app/routes.py

from flask import Blueprint, jsonify, request, g
from sqlalchemy import or_
from sqlalchemy.orm.attributes import flag_modified # Nécessaire pour modifier les champs JSON
from .models import db, Message
from .auth import jwt_required

# Création d'un Blueprint pour organiser les routes du service de messages
messages_bp = Blueprint('messages', __name__)

# =================================================================
# Route de Santé (inchangée)
# =================================================================

@messages_bp.route('/health', methods=['GET'])
def health_check():
    """Route de santé pour vérifier que le service est en ligne."""
    return jsonify({"status": "ok", "service": "message-service"}), 200

# =================================================================
# Routes pour les Messages Publics (inchangées)
# =================================================================

@messages_bp.route('/msg', methods=['POST'])
@jwt_required
def post_message():
    """Crée un nouveau message public dans un canal."""
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
    """Récupère les messages d'un canal public avec pagination."""
    channel_name = request.args.get('channel')
    if not channel_name:
        return jsonify({"error": "Le paramètre 'channel' est requis."}), 400
    
    try:
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
    except ValueError:
        return jsonify({"error": "Les paramètres 'limit' et 'offset' doivent être des entiers."}), 400

    messages_query = Message.query.filter_by(channel=channel_name)\
                                  .order_by(Message.timestamp.desc())\
                                  .offset(offset)\
                                  .limit(limit)\
                                  .all()
    
    messages_list = [msg.to_dict() for msg in messages_query]
    return jsonify({"messages": messages_list}), 200

# =================================================================
# Routes pour la Gestion d'un Message Spécifique (inchangées)
# =================================================================

@messages_bp.route('/msg/<string:id>', methods=['PUT'])
@jwt_required
def update_message(id):
    """Modifie le contenu d'un de ses propres messages."""
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "Le champ 'text' est manquant."}), 400
    message_to_update = Message.query.get_or_404(id)
    if message_to_update.from_user != g.user['pseudo']:
        return jsonify({"error": "Action non autorisée. Vous n'êtes pas l'auteur de ce message."}), 403
    message_to_update.text = data['text']
    db.session.commit()
    return jsonify(message_to_update.to_dict()), 200

@messages_bp.route('/msg/<string:id>', methods=['DELETE'])
@jwt_required
def delete_message(id):
    """Supprime un de ses propres messages."""
    message_to_delete = Message.query.get_or_404(id)
    if message_to_delete.from_user != g.user['pseudo']:
        return jsonify({"error": "Action non autorisée. Vous n'êtes pas l'auteur de ce message."}), 403
    db.session.delete(message_to_delete)
    db.session.commit()
    return jsonify({}), 204 # Code 204 No Content est standard pour un DELETE réussi

# =================================================================
# Routes pour les Messages Privés (inchangées)
# =================================================================

@messages_bp.route('/msg/private', methods=['POST'])
@jwt_required
def post_private_message():
    """Envoie un message privé à un autre utilisateur."""
    data = request.get_json()
    if not data or 'to' not in data or 'text' not in data:
        return jsonify({"error": "Payload invalide. 'to' et 'text' sont requis."}), 400

    new_private_message = Message(
        from_user=g.user['pseudo'], to_user=data['to'], channel=None, text=data['text']
    )
    db.session.add(new_private_message)
    db.session.commit()
    return jsonify(new_private_message.to_dict()), 201

@messages_bp.route('/msg/private', methods=['GET'])
@jwt_required
def get_private_messages():
    """Récupère la conversation privée entre deux utilisateurs."""
    user1 = request.args.get('from')
    user2 = request.args.get('to')
    if not user1 or not user2:
        return jsonify({"error": "Les paramètres 'from' et 'to' sont requis."}), 400
    if g.user['pseudo'] not in [user1, user2]:
        return jsonify({"error": "Accès non autorisé à cette conversation privée."}), 403

    conversation_query = Message.query.filter(
        or_((Message.from_user == user1) & (Message.to_user == user2),
            (Message.from_user == user2) & (Message.to_user == user1))
    ).order_by(Message.timestamp.asc()).all()

    messages_list = [msg.to_dict() for msg in conversation_query]
    return jsonify({"messages": messages_list}), 200

# =================================================================
# Routes Complétées
# =================================================================

@messages_bp.route('/msg/reaction', methods=['POST', 'DELETE'])
@jwt_required
def manage_reaction():
    """Ajoute (POST) ou retire (DELETE) une réaction à un message."""
    data = request.get_json()
    if not data or 'message_id' not in data or 'emoji' not in data:
        return jsonify({"error": "Payload invalide. 'message_id' et 'emoji' sont requis."}), 400
    
    message = Message.query.get_or_404(data['message_id'])
    emoji = data['emoji']
    user_pseudo = g.user['pseudo']
    
    # Assurer que le champ reactions est un dictionnaire
    if message.reactions is None:
        message.reactions = {}
        
    if request.method == 'POST':
        users_reacted = message.reactions.get(emoji, [])
        if user_pseudo not in users_reacted:
            users_reacted.append(user_pseudo)
            message.reactions[emoji] = users_reacted
            flag_modified(message, "reactions") # Notifie SQLAlchemy du changement dans le JSON
            db.session.commit()
    
    elif request.method == 'DELETE':
        if emoji in message.reactions and user_pseudo in message.reactions[emoji]:
            message.reactions[emoji].remove(user_pseudo)
            if not message.reactions[emoji]: # Si la liste est vide, on supprime la clé emoji
                del message.reactions[emoji]
            flag_modified(message, "reactions")
            db.session.commit()
            
    return jsonify(message.to_dict()), 200

@messages_bp.route('/msg/pinned', methods=['GET'])
def get_pinned_messages():
    """Récupère les messages épinglés d'un canal."""
    channel_name = request.args.get('channel')
    if not channel_name:
        return jsonify({"error": "Le paramètre 'channel' est requis."}), 400
        
    pinned_messages = Message.query.filter_by(channel=channel_name, is_pinned=True)\
                                   .order_by(Message.timestamp.desc()).all()
    
    return jsonify({"messages": [msg.to_dict() for msg in pinned_messages]}), 200

@messages_bp.route('/msg/thread/<string:id>', methods=['GET'])
def get_message_thread(id):
    """Récupère toutes les réponses à un message spécifique (fil de discussion)."""
    parent_message = Message.query.get_or_404(id)
    
    replies = Message.query.filter_by(reply_to=id)\
                           .order_by(Message.timestamp.asc()).all()
                           
    return jsonify({
        "parent": parent_message.to_dict(),
        "replies": [reply.to_dict() for reply in replies]
    }), 200

@messages_bp.route('/msg/search', methods=['GET'])
@jwt_required
def search_messages():
    """Recherche un mot-clé dans les messages."""
    query = request.args.get('q')
    if not query or len(query) < 2:
        return jsonify({"error": "Le paramètre de requête 'q' est requis (2 caractères min)."}), 400
    
    search_pattern = f"%{query}%"
    results = Message.query.filter(Message.text.ilike(search_pattern))\
                           .order_by(Message.timestamp.desc()).limit(100).all()
                           
    return jsonify({"messages": [msg.to_dict() for msg in results]}), 200

# Bonus : Routes pour épingler/désépingler
@messages_bp.route('/msg/<string:id>/pin', methods=['POST'])
@jwt_required
def pin_message(id):
    """Épingle un message. Seuls les administrateurs peuvent effectuer cette action."""
    message = Message.query.get_or_404(id)
    
    # Vérification des permissions : on vérifie si l'utilisateur a le rôle 'admin' dans son token.
    user_roles = g.user.get('roles', [])
    if 'admin' not in user_roles:
        return jsonify({"error": "Action non autorisée. Seuls les administrateurs peuvent épingler des messages."}), 403

    message.is_pinned = True
    db.session.commit()
    
    # Renvoie le message mis à jour pour confirmer l'action.
    return jsonify(message.to_dict()), 200

@messages_bp.route('/msg/<string:id>/pin', methods=['DELETE'])
@jwt_required
def unpin_message(id):
    """Désépingle un message. Seuls les administrateurs peuvent effectuer cette action."""
    message = Message.query.get_or_404(id)
    
    # Vérification des permissions : identique à la fonction d'épinglage.
    user_roles = g.user.get('roles', [])
    if 'admin' not in user_roles:
        return jsonify({"error": "Action non autorisée. Seuls les administrateurs peuvent désépingler des messages."}), 403

    message.is_pinned = False
    db.session.commit()
    
    # Renvoie le message mis à jour pour confirmer l'action.
    return jsonify(message.to_dict()), 200