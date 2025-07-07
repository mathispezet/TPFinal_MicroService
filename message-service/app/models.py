# app/models.py

from datetime import datetime
from . import db # On importe l'instance db depuis le __init__.py du package

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_user = db.Column(db.String(80), nullable=False)
    channel = db.Column(db.String(80), nullable=False)
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    reply_to = db.Column(db.Integer, nullable=True)
    reactions = db.Column(db.String(255), default='')
    # Bientôt : un champ pour les messages épinglés !
    # is_pinned = db.Column(db.Boolean, default=False, nullable=False)

    def to_dict(self):
        """Convertit l'objet Message en dictionnaire pour la réponse JSON."""
        return {
            "id": self.id,
            "from_user": self.from_user,
            "channel": self.channel,
            "text": self.text,
            "timestamp": self.timestamp.isoformat() + "Z",
            "reply_to": self.reply_to,
            "reactions": self.reactions.split(',') if self.reactions else []
        }