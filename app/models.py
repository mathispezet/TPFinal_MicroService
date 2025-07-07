# app/models.py

# 1. On importe l'instance partagée de SQLAlchemy depuis le __init__.py de l'app
#    Ceci est crucial pour le bon fonctionnement avec le pattern create_app().
from . import db
from datetime import datetime, timezone
import uuid

class Message(db.Model):
    """
    Modèle SQLAlchemy pour un message, utilisant une colonne JSON pour les réactions.
    """
    __tablename__ = 'messages'

    # --- Colonnes de la table ---

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    from_user = db.Column(db.String(80), nullable=False)
    channel = db.Column(db.String(80), nullable=False, index=True)
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    reply_to = db.Column(db.String(36), db.ForeignKey('messages.id'), nullable=True)

    # 2. Correction clé : Utilisation de `default=lambda: {}` pour la colonne JSON.
    #    Ceci évite qu'un même dictionnaire soit partagé par erreur entre tous les nouveaux messages.
    reactions = db.Column(db.JSON, nullable=False, default=lambda: {})


    # --- Méthode de sérialisation ---

    def to_dict(self):
        """Convertit l'objet Message en un dictionnaire pour les réponses API JSON."""
        return {
            "id": self.id,
            "from_user": self.from_user,
            "channel": self.channel,
            "text": self.text,
            # 3. Amélioration : Formatage robuste pour garantir le format ISO 8601 avec 'Z'.
            "timestamp": self.timestamp.replace(tzinfo=timezone.utc).isoformat().replace('+00:00', 'Z'),
            "reply_to": self.reply_to,
            "reactions": self.reactions
        }