from app.extensions import db
from datetime import datetime


class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    magic_link_token = db.Column(db.String(100), nullable=True)
    magic_link_expires = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Document(db.Model):
    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_key = db.Column(db.String(500), nullable=False)       # R2 object key
    file_size = db.Column(db.Integer, nullable=True)           # bytes
    mime_type = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='draft')  # draft, pending, completed, voided
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('documents', lazy=True))
