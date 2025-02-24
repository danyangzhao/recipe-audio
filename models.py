from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), unique=True, nullable=False)
    title = db.Column(db.String(200))
    introduction = db.Column(db.Text)
    ingredients = db.Column(db.JSON)
    instructions = db.Column(db.JSON)
    audio_filename = db.Column(db.String(500))
    views = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow) 