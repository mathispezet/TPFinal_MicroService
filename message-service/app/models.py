# message-service/app/models.py

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    from_user = db.Column(db.String(80), nullable=False)
    # Le canal peut être null pour les messages privés
    channel = db.Column(db.String(80), nullable=True, index=True) 
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    reply_to = db.Column(db.String(36), db.ForeignKey('messages.id'), nullable=True)
    # Le champ reactions sera un dictionnaire JSON
    reactions = db.Column(db.JSON, nullable=False, default=lambda: {})
    # Ajout d'une colonne pour les messages privés
    to_user = db.Column(db.String(80), nullable=True)

    def to_dict(self):
        """Convertit l'objet Message en un dictionnaire pour les réponses API JSON."""
        return {
            "id": self.id,
            "from_user": self.from_user,
            "channel": self.channel,
            "to_user": self.to_user,
            "text": self.text,
            "timestamp": self.timestamp.isoformat() + "Z",
            "reply_to": self.reply_to,
            "reactions": self.reactions
        }
