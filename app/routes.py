# message-service/app/routes.py

from flask import Blueprint, jsonify, request, g
from sqlalchemy import or_
from sqlalchemy.orm.attributes import flag_modified # Nécessaire pour modifier les champs JSON
from .models import db, Message
from .auth import jwt_required


# Création d'un Blueprint pour organiser les routes du service de messages
messages_bp = Blueprint('messages', __name__)

# =================================================================
# Route de Santé
# =================================================================

@messages_bp.route('/health', methods=['GET'])
def health_check():
    """Route de santé pour vérifier que le service est en ligne.
    ---
    tags:
      - Health
    summary: Vérifie la disponibilité du service.
    responses:
      200:
        description: Le service est opérationnel.
        content:
          application/json:
            schema:
              type: object
              properties:
                status:
                  type: string
                  example: "ok"
                service:
                  type: string
                  example: "message-service"
    """
    return jsonify({"status": "ok", "service": "message-service"}), 200

# =================================================================
# Routes pour les Messages Publics
# =================================================================

@messages_bp.route('/msg', methods=['POST'])
@jwt_required
def post_message():
    """Crée un nouveau message public dans un canal.
    ---
    tags:
      - Messages
    summary: Envoie un message dans un canal public.

    consumes:
      - application/json
    produces:
      - application/json

    description: >
      Crée un nouveau message dans la base de données.
      Nécessite une authentification JWT (sauf en mode développement).
      Le corps de la requête doit être un JSON contenant un canal et un texte.
    security:
      - bearerAuth: []

    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PostMessagePayload'
          example:            # <-- un exemple aide Swagger UI à pré-remplir le body
            channel: general
            text: "Hello world!"

    responses:
      201:
        description: Message créé avec succès. Le message nouvellement créé est retourné.
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Message'
      400:
        description: Payload invalide ou champs manquants.
      401:
        description: Token JWT manquant ou invalide.
      415:
        description: Média non supporté. Le header 'Content-Type' n'est pas 'application/json'.
    """
    try:
      print(request.headers)
      # 1. Lecture du corps de la requête en tant que JSON.
      # Cette ligne est le "gardien" du format. Elle renverra une erreur 415
      # si le client n'envoie pas le header 'Content-Type: application/json'.
      # C'est le comportement attendu et correct.
      data = request.get_json()

      print(data, flush=True)

      # 2. Validation des données métier.
      # On vérifie que les champs nécessaires sont bien présents dans le JSON reçu.
      if not data or 'channel' not in data or 'text' not in data:
          return jsonify({"error": "Payload invalide. Les champs 'channel' et 'text' sont requis."}), 400

      # 3. Création de l'objet Message avec les données validées.
      # Le pseudo de l'utilisateur est récupéré depuis `g.user`, qui est rempli
      # par le décorateur @jwt_required (soit depuis le token, soit avec le bypass).
      new_message = Message(
          from_user=g.user['pseudo'],
          channel=data['channel'],
          text=data['text'],
          reply_to=data.get('reply_to') # .get() pour gérer le cas où reply_to est optionnel
      )

      # 4. Sauvegarde en base de données.
      db.session.add(new_message)
      db.session.commit()

      # 5. Réponse de succès.
      # On renvoie le nouvel objet message complet (avec son ID et timestamp)
      # et le code de statut HTTP 201 Created, qui est le standard pour un POST réussi.
      return jsonify(new_message.to_dict()), 201
    except Exception as e:
        print(e)
        return jsonify({"error" : repr(e)}), 500

# =================================================================
# Routes pour la Gestion d'un Message Spécifique
# =================================================================

@messages_bp.route('/msg/<string:id>', methods=['PUT'])
@jwt_required
def update_message(id):
    """Modifie le contenu d'un de ses propres messages.
    ---
    tags:
      - Messages
    summary: Modifie un message existant.
    security:
      - bearerAuth: []
    parameters:
      - in: path
        name: id
        required: true
        schema:
          type: string
          format: uuid
        description: ID du message à modifier.
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required: [text]
            properties:
              text:
                type: string
                description: Le nouveau contenu du message.
    responses:
      200:
        description: Message modifié avec succès.
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Message'
      400:
        description: Données manquantes.
      401:
        description: Token JWT invalide.
      403:
        description: Action non autorisée (pas l'auteur).
      404:
        description: Message non trouvé.
    """
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
    """Supprime un de ses propres messages.
    ---
    tags:
      - Messages
    summary: Supprime un message existant.
    security:
      - bearerAuth: []
    parameters:
      - in: path
        name: id
        required: true
        schema:
          type: string
          format: uuid
        description: ID du message à supprimer.
    responses:
      204:
        description: Message supprimé avec succès.
      401:
        description: Token JWT invalide.
      403:
        description: Action non autorisée (pas l'auteur).
      404:
        description: Message non trouvé.
    """
    message_to_delete = Message.query.get_or_404(id)
    if message_to_delete.from_user != g.user['pseudo']:
        return jsonify({"error": "Action non autorisée. Vous n'êtes pas l'auteur de ce message."}), 403
    db.session.delete(message_to_delete)
    db.session.commit()
    return '', 204

# =================================================================
# Routes pour les Messages Privés
# =================================================================

@messages_bp.route('/msg/private', methods=['POST'])
@jwt_required
def post_private_message():
    """Envoie un message privé à un autre utilisateur.
    ---
    tags:
        - Messages Privés
    summary: Envoie un message privé.
    security:
        - bearerAuth: []
    requestBody:
        required: true
        content:
            application/json:
                schema:
                    type: object
                    required: [to, text]
                    properties:
                        to:
                            type: string
                            description: "Pseudo du destinataire."
                        text:
                            type: string
                            description: "Contenu du message."
    responses:
        201:
            description: Message privé envoyé avec succès.
            content:
                application/json:
                    schema:
                        $ref: '#/components/schemas/Message'
        400:
            description: Données manquantes.
    """
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
    """Récupère la conversation privée entre deux utilisateurs.
    ---
    tags:
        - Messages Privés
    summary: Récupère une conversation privée.
    security:
        - bearerAuth: []
    parameters:
        - name: from
          in: query
          required: true
          description: "Le pseudo de l'un des participants."
          schema:
            type: string
        - name: to
          in: query
          required: true
          description: "Le pseudo de l'autre participant."
          schema:
            type: string
    responses:
        200:
            description: Liste des messages de la conversation.
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            messages:
                                type: array
                                items:
                                    $ref: '#/components/schemas/Message'
        403:
            description: Accès non autorisé à cette conversation.
    """
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
# Routes Complémentaires (Réactions, Threads, etc.)
# =================================================================

@messages_bp.route('/msg/reaction', methods=['POST', 'DELETE'])
@jwt_required
def manage_reaction():
    """Ajoute (POST) ou retire (DELETE) une réaction à un message.
    ---
    tags:
      - Reactions
    summary: Gère les réactions emoji sur un message.
    description: Utiliser POST pour ajouter une réaction, et DELETE pour la retirer.
    security:
      - bearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ReactionPayload'
    responses:
      200:
        description: Réaction gérée avec succès.
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Message'
      400:
        description: Données manquantes.
      401:
        description: Token JWT invalide.
      404:
        description: Message non trouvé.
    """
    data = request.get_json()
    if not data or 'message_id' not in data or 'emoji' not in data:
        return jsonify({"error": "Payload invalide. 'message_id' et 'emoji' sont requis."}), 400
    
    message = Message.query.get_or_404(data['message_id'])
    emoji = data['emoji']
    user_pseudo = g.user['pseudo']
    
    if message.reactions is None: message.reactions = {}
        
    if request.method == 'POST':
        users_reacted = message.reactions.get(emoji, [])
        if user_pseudo not in users_reacted:
            users_reacted.append(user_pseudo)
            message.reactions[emoji] = users_reacted
            flag_modified(message, "reactions")
            db.session.commit()
    
    elif request.method == 'DELETE':
        if emoji in message.reactions and user_pseudo in message.reactions[emoji]:
            message.reactions[emoji].remove(user_pseudo)
            if not message.reactions[emoji]:
                del message.reactions[emoji]
            flag_modified(message, "reactions")
            db.session.commit()
            
    return jsonify(message.to_dict()), 200

@messages_bp.route('/msg/pinned', methods=['GET'])
def get_pinned_messages():
    """Récupère les messages épinglés d'un canal.
    ---
    tags:
      - Messages
    summary: Liste les messages épinglés d'un canal.
    parameters:
      - in: query
        name: channel
        required: true
        schema:
          type: string
        description: Le nom du canal.
    responses:
      200:
        description: Liste des messages épinglés.
        content:
          application/json:
            schema:
              type: object
              properties:
                messages:
                  type: array
                  items:
                    $ref: '#/components/schemas/Message'
      400:
        description: Paramètre 'channel' manquant.
    """
    channel_name = request.args.get('channel')
    if not channel_name:
        return jsonify({"error": "Le paramètre 'channel' est requis."}), 400
        
    pinned_messages = Message.query.filter_by(channel=channel_name, is_pinned=True)\
                                   .order_by(Message.timestamp.desc()).all()
    
    return jsonify({"messages": [msg.to_dict() for msg in pinned_messages]}), 200

@messages_bp.route('/msg/thread/<string:id>', methods=['GET'])
def get_message_thread(id):
    """Récupère toutes les réponses à un message spécifique (fil de discussion).
    ---
    tags:
      - Messages
    summary: Affiche un fil de discussion.
    parameters:
      - in: path
        name: id
        required: true
        schema:
          type: string
          format: uuid
        description: ID du message parent du fil.
    responses:
      200:
        description: Le message parent et ses réponses.
        content:
          application/json:
            schema:
              type: object
              properties:
                parent:
                  $ref: '#/components/schemas/Message'
                replies:
                  type: array
                  items:
                    $ref: '#/components/schemas/Message'
      404:
        description: Message parent non trouvé.
    """
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
    """Recherche un mot-clé dans les messages.
    ---
    tags:
      - Messages
    summary: Recherche des messages par mot-clé.
    security:
      - bearerAuth: []
    parameters:
      - in: query
        name: q
        required: true
        schema:
          type: string
        description: Le terme de recherche (2 caractères min).
    responses:
      200:
        description: Liste des messages correspondants.
        content:
          application/json:
            schema:
              type: object
              properties:
                messages:
                  type: array
                  items:
                    $ref: '#/components/schemas/Message'
      400:
        description: Paramètre de recherche 'q' manquant ou trop court.
      401:
        description: Token JWT invalide.
    """
    query = request.args.get('q')
    if not query or len(query) < 2:
        return jsonify({"error": "Le paramètre de requête 'q' est requis (2 caractères min)."}), 400
    
    search_pattern = f"%{query}%"
    results = Message.query.filter(Message.text.ilike(search_pattern))\
                           .order_by(Message.timestamp.desc()).limit(100).all()
                           
    return jsonify({"messages": [msg.to_dict() for msg in results]}), 200

@messages_bp.route('/msg/<string:id>/pin', methods=['POST', 'DELETE'])
@jwt_required
def pin_unpin_message(id):
    """Épingle (POST) ou désépingle (DELETE) un message. Admin requis.
    ---
    tags:
      - Admin
    summary: Gère l'épinglage des messages (Admin).
    description: POST pour épingler, DELETE pour désépingler. Nécessite le rôle 'admin' dans le JWT.
    security:
      - bearerAuth: []
    parameters:
      - in: path
        name: id
        required: true
        schema:
          type: string
          format: uuid
        description: ID du message à épingler/désépingler.
    responses:
      200:
        description: Action effectuée avec succès.
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Message'
      401:
        description: Token JWT invalide.
      403:
        description: Action non autorisée (pas administrateur).
      404:
        description: Message non trouvé.
    """
    message = Message.query.get_or_404(id)
    user_roles = g.user.get('roles', [])
    if 'admin' not in user_roles:
        return jsonify({"error": "Action non autorisée. Seuls les administrateurs peuvent épingler des messages."}), 403

    if request.method == 'POST':
        message.is_pinned = True
    elif request.method == 'DELETE':
        message.is_pinned = False
    
    db.session.commit()
    return jsonify(message.to_dict()), 200