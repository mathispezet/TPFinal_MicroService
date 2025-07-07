# message-service/app/routes.py (VERSION FUSIONNÉE ET FINALE)

from flask import Blueprint, jsonify, request, g
from sqlalchemy import or_
from .models import db, Message
from .auth import jwt_required

# RENOMMÉ : J'utilise 'messages_bp' pour la clarté, mais vous pouvez garder 'main_bp' si vous préférez.
messages_bp = Blueprint('messages', __name__)

# =================================================================
# Route de Santé
# .models import db, Message
from .auth import jwt_required

# On utilise le nom de Blueprint de votre équipe
main_bp = Blueprint('main', __name__)

# =================================================================
# Route de Santé
# =================================================================

@main_bp.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "service": "message-service"}), 200

# =================================================================
# Routes pour les Messages Publics
# =================================================================

@main_bp.route('/msg', methods=['POST'])
@jwt_required
def post_message():
    """Crée un nouveau message public dans un canal."""
    data = request.get_json()
    if not data or 'channel' not in data or 'text' not in data:
        return jsonify({"error": "Payload invalide. 'channel' et 'text' sont requis."}), 400

    try:
        new_message = Message(
            from_user=g.user['pseudo'], # MODIFIÉ : Utilise l'utilisateur authentifié
            channel=data['channel'],
            text=data['text'],
            reply_to=data.get('reply_to')
        )
        db.session.add(new_message)
        db.session.commit()
        # CONFORME : Réponse pour "Succès (création)"
        return jsonify(new_message.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        # Log de l'erreur pour le debug
        print(f"ERROR in post_message: {e}")
        return jsonify({"error": "Erreur interne lors de la sauvegarde du message."}), 500

@main_bp.route('/msg', methods=['GET'])
def get_channel_messages():
    """Récupère les messages d'un canal, en excluant les messages épinglés."""
    channel_name = request.args.get('channel')
    if not channel_name:
        return jsonify({"error": "Le paramètre 'channel' est requis."}), 400

    # On garde la bonne logique de votre équipe pour exclure les messages épinglés
    messages_query = Message.query.filter_by(channel=channel_name, is_pinned=False)
    
    offset = request.args.get('offset', 0, type=int)
    limit = request.args.get('limit', 50, type=int)
    channel_messages = messages_query.order_by(Message.timestamp.desc()).offset(offset).limit(limit).all()
    
    # CONFORME : Réponse pour "Succès (lecture)"
    return jsonify({"messages": [msg.to_dict() for msg in channel_messages]}), 200

# =================================================================
# Actions sur un message spécifique (Update, Delete, Pin)
# =================================================================

@main_bp.route('/msg/<string:id>', methods=['PUT'])
@jwt_required
def update_message(id):
    """(LOGIQUE COMPLÉTÉE) Modifie le contenu d'un de ses propres messages."""
    data = request.get_json()
    if not data =================================================================

@messages_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "service": "message-service"}), 200

# =================================================================
# Routes pour les Messages (Publics et Privés)
# =================================================================

@messages_bp.route('/msg', methods=['POST'])
@jwt_required
def post_message():
    """Crée un nouveau message public."""
    data = request.get_json()
    if not data or 'channel' not in data or 'text' not in data:
        return jsonify({"error": "Payload invalide. 'channel' et 'text' sont requis."}), 400

    # FIX: Utilisation de l'identité réelle du JWT
    new_message = Message(
        from_user=g.user['pseudo'],
        channel=data['channel'],
        text=data['text'],
        reply_to=data.get('reply_to') # .get() est plus sûr
    )
    
    # MERGED: Conservation de votre gestion d'erreur de base de données
    try:
        db.session.add(new_message)
        db.session.commit()
        return jsonify(new_message.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        # Loggez l'erreur pour le débogage : print(e)
        return jsonify({"error": "Erreur interne lors de la sauvegarde du message."}), 500

@messages_bp.route('/msg', methods=['GET'])
def get_channel_messages():
    """Récupère les messages d'un canal, en excluant les messages épinglés."""
    channel_name = request.args.get('channel')
    if not channel_name:
        return jsonify({"error": "Le paramètre 'channel' est requis."}), 400
    
    try:
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
    except ValueError:
        return jsonify({"error": "Les paramètres 'limit' et 'offset' doivent être des entiers."}), 400
    
    # MERGED: Conservation de votre logique pour exclure les messages épinglés
    messages_query = Message.query.filter_by(channel=channel_name, is_pinned=False)\
                                  .order_by(Message.timestamp.desc())\
                                  .offset(offset)\
                                  .limit(limit)\
                                  .all()
    
    return jsonify({"messages": [msg.to_dict() for msg in messages_query]}), 200

# =================================================================
# Actions sur un Message Spécifique
# =================================================================

@messages_bp.route('/msg/< or 'text' not in data:
        return jsonify({"error": "Le champ 'text' est manquant."}), 400

    message_to_update = Message.query.get_or_404(id)

    if message_to_update.from_user != g.user['pseudo']:
        return jsonify({"error": "Action non autorisée. Vous n'êtes pas l'auteur."}), 403

    message_to_update.text = data['text']
    db.session.commit()
    # CONFORME : Réponse standardisée pour "Succès (action)"
    return jsonify({"status": "success", "message": "Message mis à jour avec succès."}), 200

@main_bp.route('/msg/<string:id>', methods=['DELETE'])
@jwt_required
def delete_message(id):
    """(LOGIQUE COMPLÉTÉE) Supprime un de ses propres messages."""
    message_to_delete = Message.query.get_or_404(id)

    if message_to_delete.from_user != g.user['pseudo']:
        return jsonify({"error": "Action non autorisée. Vous n'êtes pas l'auteur."}), 403

    db.session.delete(message_to_delete)
    db.session.commit()
    # CONFORME : Réponse standardisée pour "Succès (action)"
    return jsonify({"status": "success", "message": "Message supprimé avec succès."}), 200

@main_bp.route('/msg/<string:id>/pin', methods=['POST'])
@jwt_required
def pin_message(id):
    """(LOGIQUE CONSERVÉE ETstring:id>', methods=['PUT'])
@jwt_required
def update_message(id):
    """Modifie le contenu d'un de ses propres messages."""
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "Le champ 'text' est manquant."}), 400

    message_to_update = Message.query.get_or_404(id) # get_or_404 gère le "non trouvé"
    if message_to_update.from_user != g.user['pseudo']:
        return jsonify({"error": "Action non autorisée."}), 403

    message_to_update.text = data['text']
    db.session.commit()
    # FIX: Réponse standardisée pour une action réussie
    return jsonify({"status": "success", "message": "Message mis à jour avec succès."}), 200

@messages_bp.route('/msg/<string:id>', methods=['DELETE'])
@jwt_required
def delete_message(id):
    """Supprime un de ses propres messages."""
    message_to_delete = Message.query.get_or_404(id)
    if message_to_delete.from_user != g.user['pseudo']:
        return jsonify({"error": "Action non autorisée."}), 403

    db.session.delete(message_to_delete)
    db.session.commit()
    return jsonify({"status": "success", "message": "Message supprimé avec succès."}), 200

@messages_bp.route('/msg/<string:id>/pin', methods=['POST', 'DELETE'])
@jwt_required
def pin_unpin_message(id):
    """Épingle ou désépingle un message."""
    # TODO: Ajouter une vérification des droits (seuls les modérateurs peuvent épingler)
    message = Message.query.get_or_404(id)
    
    if request.method == 'POST':
        message.is_pinned = True
        action_message = "Message épinglé avec succès."
    else: # DELETE
        message.is_pinned = False
        action_message = "Message désépinglé avec succès."
        
    db.session.commit()
    # FIX: Réponse standardisée pour CORRIGÉE) Épingle un message."""
    message = Message.query.get_or_404(id)
    # TODO: Ajouter une vérification des droits (ex: seul un modérateur peut épingler)
    message.is_pinned = True
    db.session.commit()
    return jsonify({"status": "success", "message": "Message épinglé avec succès."}), 200

@main_bp.route('/msg/<string:id>/pin', methods=['DELETE'])
@jwt_required
def unpin_message(id):
    """(LOGIQUE CONSERVÉE ET CORRIGÉE) Désépingle un message."""
    message = Message.query.get_or_404(id)
    # TODO: Ajouter une vérification des droits
    message.is_pinned = False
    db.session.commit()
    return jsonify({"status": "success", "message": "Message désépinglé avec succès."}), 200

# =================================================================
# Fonctions Avancées (Private, Reaction, Thread, Pinned, Search)
# =================================================================

@main_bp.route('/msg/private', methods=['POST'])
@jwt_required
def post_private_message():
    """(LOGIQUE COMPLÉTÉE) Envoie un message privé à un autre utilisateur."""
    data = request.get_json()
    if not data or 'to' not in data or 'text' not in data:
        return jsonify({"error": "Payload invalide. 'to' et 'text' sont requis."}), 400

    new_private_ une action réussie
    return jsonify({"status": "success", "message": action_message}), 200

# =================================================================
# Fonctions Avancées (Thread, Pinned, Search, Private)
# =================================================================

@messages_bp.route('/msg/thread/<string:id>', methods=['GET'])
def get_message_thread(id):
    """Récupère un message parent et toutes ses réponses."""
    parent_message = Message.query.get_or_404(id)
    thread_messages = Message.query.filter_by(reply_to=id).order_by(Message.timestamp.asc()).all()
    
    return jsonify({
        "parent_message": parent_message.to_dict(),
        "replies": [msg.to_dict() for msg in thread_messages]
    }), 200

@messages_bp.route('/msg/pinned', methods=['GET'])
def get_pinned_messages():
    """Récupère les messages épinglés pour un canal."""
    channel_name = request.args.get('channel')
    if not channel_name:
        return jsonify({"error": "Le paramètre 'channel' est requis."}), 400
    
    pinned_messages = Message.query.filtermessage = Message(
        from_user=g.user['pseudo'],
        to_user=data['to'],
        channel=None,
        text=data['text']
    )
    db.session.add(new_private_message)
    db.session.commit()
    return jsonify(new_private_message.to_dict()), 201

@main_bp.route('/msg/private', methods=['GET'])
@jwt_required
def get_private_messages():
    """(LOGIQUE COMPLÉTÉE) Récupère la conversation privée entre deux utilisateurs."""
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

    return jsonify({"messages": [msg.to_dict() for msg in conversation_query]}), 200

@main_bp_by(channel=channel_name, is_pinned=True)\
                                 .order_by(Message.timestamp.desc()).all()
    return jsonify({"messages": [msg.to_dict() for msg in pinned_messages]}), 200

@messages_bp.route('/msg/search', methods=['GET'])
def search_messages():
    """Recherche un mot-clé dans les messages."""
    query = request.args.get('q')
    if not query or len(query) < 3:
        return jsonify({"error": "Le paramètre de recherche 'q' est requis (3 caractères min)."}), 400
    
    search_pattern = f"%{query}%"
    channel_name = request.args.get('channel')
    
    query_builder = Message.query.filter(Message.text.like(search_pattern))
    if channel_name:
        query_builder = query_builder.filter_by(channel=channel_name)
        
    search_results = query_builder.order_by(Message.timestamp.desc())..route('/msg/reaction', methods=['POST', 'DELETE'])
@jwt_required
def manage_reaction():
    """(SQUELETTE DÉTAILLÉ) Ajoute ou retire une réaction à un message."""
    # TODO: Implémenter la logique de cette fonction.
    # 1. Valider le payload : { "message_id": "string", "emoji": "string" }
    # 2. Récupérer le message : message = Message.query.get_or_404(message_id)
    # ... etc.
    return jsonify({"message": "Route pour les réactions à implémenter"}), 501

@main_bp.route('/msg/thread/<string:id>', methods=['GET'])
def get_message_thread(id):
    """(LOGIQUE CONSERVÉE) Récupère un message et ses réponses."""
all()
    return jsonify({"messages": [msg.to_dict() for msg in search_results]}), 200

@messages_bp.route('/msg/private', methods=['POST'])
@jwt_required
def post_private_message():
    """Envoie un message privé."""
    data = request.get_json()
    if not data or 'to' not in data or 'text' not in data:
        return jsonify({"error": "Payload invalide. 'to' et 'text' sont requis."}), 400

    new_private_message = Message(
        from_user=g.user['pseudo'], to_user=data['to'], text=data['text']
    )
    db.session.add(    parent_message = Message.query.get_or_404(id)
    thread_messages = Message.query.filter_by(reply_to=id).order_by(Message.timestamp.asc()).all()
    response_data = {
        "parent_message": parent_message.to_dict(),
        "replies": [msg.to_dict() for msg in thread_messages]
    }
    new_private_message)
    db.session.commit()
    return jsonify(new_private_message.to_dict()), 201

@messages_bp.route('/msg/private', methods=['GET'])
@jwt_required
def get_private_messages():
    """Récupère une conversation privée."""
    user1 = request.args.get('from')
    user2 = request.args.get('to')
    if not user1 or not user2:
        return jsonify({"error": "Les paramètres 'from' et 'to' sont requis."}), 400

    if g.user['pseudo'] not inreturn jsonify(response_data), 200

@main_bp.route('/msg/pinned', methods=['GET'])
def get_pinned_messages():
    """(LOGIQUE CONSERVÉE) Récupère les messages épinglés pour un canal."""
    channel_name = request.args.get('channel')
    if not channel_name:
        return jsonify({"error": "Le paramètre 'channel' est requis."}), 400
    
    pinned_messages = Message.query.filter_by(
        channel=channel_name, is_pinned=True
    ).order_by(Message.timestamp.desc()).all [user1, user2]:
        return jsonify({"error": "Accès non autorisé."}), 403

    conversation = Message.query.filter(or_((Message.from_user == user1) & (Message.to_user == user2),(Message.from_user == user2) & (Message.to_user == user1)))\
                                .order_by(Message.timestamp.asc()).all()
    return jsonify({"messages": [()
    
    return jsonify({"messages": [msg.to_dict() for msg in pinned_messages]}), 200

@main_bp.route('/msg/search', methods=['GET'])
def search_messages():
    """(LOGIQUE CONSERVÉE) Recherche un mot-clé dans les messages."""
    query = request.args.get('q')
    if not query or len(query) < 3:
        return jsonify({"error": "Paramètre 'q' requis (3 caractères min)."}), 400
    
    search_pattern = f"%{query}%"
    channel_name = request.args.get('channel')
    
    query_builder = Message.query.filter(Message.text.like(search_pattern))
    ifmsg.to_dict() for msg in conversation]}), 200

# =================================================================
# Squelette restant
# =================================================================

@messages_bp.route('/msg/reaction', methods=['POST', 'DELETE'])
@jwt_required
def manage_reaction():
    """Ajoute ou retire une réaction à un message."""
    # TODO: Implémenter la logique des réactions.
    return jsonify({"message": "Route pour les réactions à implémenter"}), 501
