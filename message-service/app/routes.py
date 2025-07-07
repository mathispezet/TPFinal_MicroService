# message-service/app/routes.py

from flask import Blueprint, jsonify, request, g
from sqlalchemy import or_
from .models import db, Message
from .auth import jwt_required

# Création d'un Blueprint pour organiser les routes du service de messages
messages_bp = Blueprint('messages', __name__)

# =================================================================
# Route de Santé
# =================================================================

@messages_bp.route('/health', methods=['GET'])
def health_check():
    """Route de santé pour vérifier que le service est en ligne."""
    return jsonify({"status": "ok", "service": "message-service"}), 200

# =================================================================
# Routes pour les Messages Publics
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
        reply_to=data.get('reply_to') # gère le cas où la clé est absente
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
# Routes pour la Gestion d'un Message Spécifique
# =================================================================

@messages_bp.route('/msg/<string:id>', methods=['PUT'])
@jwt_required
def update_message(id):
    """Modifie le contenu d'un de ses propres messages."""
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "Le champ 'text' est manquant."}), 400

    message_to_update = Message.query.get(id)
    if not message_to_update:
        return jsonify({"error": f"Message avec l'ID {id} non trouvé."}), 404

    if message_to_update.from_user != g.user['pseudo']:
        return jsonify({"error": "Action non autorisée. Vous n'êtes pas l'auteur de ce message."}), 403

    message_to_update.text = data['text']
    db.session.commit()
    return jsonify({"status": "success", "message": "Message mis à jour avec succès."}), 200

@messages_bp.route('/msg/<string:id>', methods=['DELETE'])
@jwt_required
def delete_message(id):
    """Supprime un de ses propres messages."""
    message_to_delete = Message.query.get(id)
    if not message_to_delete:
        return jsonify({"error": f"Message avec l'ID {id} non trouvé."}), 404

    if message_to_delete.from_user != g.user['pseudo']:
        return jsonify({"error": "Action non autorisée. Vous n'êtes pas l'auteur de ce message."}), 403

    db.session.delete(message_to_delete)
    db.session.commit()
    return jsonify({"status": "success", "message": "Message supprimé avec succès."}), 200

# =================================================================
# Routes pour les Messages Privés
# =================================================================

@messages_bp.route('/msg/private', methods=['POST'])
@jwt_required
def post_private_message():
    """Envoie un message privé à un autre utilisateur."""
    data = request.get_json()
    if not data or 'to' not in data or 'text' not in data:
        return jsonify({"error": "Payload invalide. 'to' et 'text' sont requis."}), 400

    new_private_message = Message(
        from_user=g.user['pseudo'],
        to_user=data['to'],
        channel=None, # Marque le message comme privé
        text=data['text']
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
        or_(
            (Message.from_user == user1) & (Message.to_user == user2),
            (Message.from_user == user2) & (Message.to_user == user1)
        )
    ).order_by(Message.timestamp.asc()).all()

    messages_list = [msg.to_dict() for msg in conversation_query]
    return jsonify({"messages": messages_list}), 200

# =================================================================
# Squelettes des Fonctionnalités Restantes
# =================================================================

@messages_bp.route('/msg/reaction', methods=['POST', 'DELETE'])
@jwt_required
def manage_reaction():
    """Ajoute ou retire une réaction à un message."""
    # TODO: Implémenter la logique de cette fonction.
    # 1. Valider le payload : { "message_id": "string", "emoji": "string" }
    # 2. Récupérer le message : message = Message.query.get(message_id)
    # 3. Vérifier que le message existe.
    # 4. Cloner le dictionnaire de réactions pour le modifier : reactions = dict(message.reactions)
    # 5. Si POST :
    #    - S'assurer que la liste pour l'emoji existe : reactions.setdefault(emoji, [])
    #    - Ajouter le pseudo de l'utilisateur (g.user['pseudo']) s'il n'y est pas déjà.
    # 6. Si DELETE :
    #    - Si l'emoji existe et que l'utilisateur est dans la liste, le retirer.
    # 7. Mettre à jour le champ du message : message.reactions = reactions
    # 8. Sauvegarder : db.session.commit()
    # 9. Renvoyer une réponse de succès.
    return jsonify({"message": "Route pour les réactions à implémenter"}), 501

@messages_bp.route('/msg/pinned', methods=['GET'])
@jwt_required # Probablement requis pour les canaux privés
def get_pinned_messages():
    """Récupère les messages épinglés d'un canal."""
    # TODO: Implémenter la logique de cette fonction.
    # Cette logique dépendra de comment vous décidez de marquer un message comme "épinglé".
    # (par exemple, via un nouveau champ booléen `is_pinned` dans le modèle Message)
    return jsonify({"message": "Route pour les messages épinglés à implémenter"}), 501

@messages_bp.route('/msg/thread/<string:id>', methods=['GET'])
def get_message_thread(id):
    """Récupère toutes les réponses à un message spécifique (fil de discussion)."""
    # TODO: Implémenter la logique de cette fonction.
    # Il faudra requêter tous les messages où `reply_to` est égal à `id`.
    # Pensez à trier par timestamp.
    return jsonify({"message": f"Route pour le thread du message {id} à implémenter"}), 501

@messages_bp.route('/msg/search', methods=['GET'])
@jwt_required
def search_messages():
    """Recherche un mot-clé dans les messages."""
    # TODO: Implémenter la logique de cette fonction.
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "Le paramètre de requête 'q' est requis."}), 400
    # Utiliser `Message.query.filter(Message.text.ilike(f'%{query}%'))` pour la recherche.
    # Pensez à ne chercher que dans les canaux auxquels l'utilisateur a accès.
    return jsonify({"message": "Route de recherche à implémenter"}), 501
