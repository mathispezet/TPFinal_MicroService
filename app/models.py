# app/models.py
from . import db  # Importe l'objet 'db' depuis __init__.py
from datetime import datetime

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    author_pseudo = db.Column(db.String(80), nullable=False)
    channel_name = db.Column(db.String(80), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relation pour les réactions
    reactions = db.relationship('Reaction', backref='message', cascade="all, delete-orphan")

    def to_dict(self):
        # Fonction pratique pour convertir l'objet en dictionnaire
        return {
            "id": self.id,
            "text": self.text,
            "from": self.author_pseudo,
            "channel": self.channel_name,
            "timestamp": self.timestamp.isoformat(),
            "reactions": {r.emoji: r.user_pseudo for r in self.reactions} # Simplifié, à adapter
        }

class Reaction(db.Model):
    __tablename__ = 'reactions'
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('messages.id'), nullable=False)
    user_pseudo = db.Column(db.String(80), nullable=False)
    emoji = db.Column(db.String(16), nullable=False)

    __table_args__ = (db.UniqueConstraint('message_id', 'user_pseudo', 'emoji'),)