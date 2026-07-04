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


class DocumentField(db.Model):
    __tablename__ = 'document_fields'

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    field_type = db.Column(db.String(50), nullable=False)  # signature, initials, date, text
    page = db.Column(db.Integer, nullable=False, default=1)
    x = db.Column(db.Float, nullable=False)
    y = db.Column(db.Float, nullable=False)
    width = db.Column(db.Float, nullable=False)
    height = db.Column(db.Float, nullable=False)
    value = db.Column(db.Text, nullable=True)  # filled in after signing
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    document = db.relationship('Document', backref=db.backref('fields', lazy=True))


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    event = db.Column(db.String(100), nullable=False)  # signed, voided
    ip_address = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    document = db.relationship('Document', backref=db.backref('audit_logs', lazy=True))
