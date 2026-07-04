from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models import Document, DocumentField, AuditLog, User
from datetime import datetime

sign = Blueprint('sign', __name__)


# 1. Save field positions
@sign.route('/documents/<int:doc_id>/fields', methods=['POST'])
@jwt_required()
def place_fields(doc_id):
    current_email = get_jwt_identity()
    current_user = User.query.filter_by(email=current_email).first()

    if not current_user:
        return jsonify({"message": "User not found"}), 404

    doc = Document.query.filter_by(id=doc_id, user_id=current_user.id).first()

    if not doc:
        return jsonify({"message": "Document not found"}), 404

    if doc.status != 'draft':
        return jsonify({"message": "Document is not in draft"}), 400

    data = request.get_json()
    fields = data.get('fields', [])

    if not fields:
        return jsonify({"message": "No fields provided"}), 400

    DocumentField.query.filter_by(document_id=doc_id).delete()

    for f in fields:
        field = DocumentField(
            document_id=doc_id,
            field_type=f.get('field_type'),
            page=f.get('page', 1),
            x=f.get('x'),
            y=f.get('y'),
            width=f.get('width'),
            height=f.get('height')
        )
        db.session.add(field)

    db.session.commit()

    return jsonify({
        "message": "Fields saved",
        "count": len(fields)
    }), 200


# 2. Get fields for a document
@sign.route('/documents/<int:doc_id>/fields', methods=['GET'])
@jwt_required()
def get_fields(doc_id):
    current_email = get_jwt_identity()
    current_user = User.query.filter_by(email=current_email).first()

    if not current_user:
        return jsonify({"message": "User not found"}), 404

    doc = Document.query.filter_by(id=doc_id, user_id=current_user.id).first()

    if not doc:
        return jsonify({"message": "Document not found"}), 404

    fields = DocumentField.query.filter_by(document_id=doc_id).all()

    return jsonify({
        "fields": [
            {
                "id": f.id,
                "field_type": f.field_type,
                "page": f.page,
                "x": f.x,
                "y": f.y,
                "width": f.width,
                "height": f.height,
                "value": f.value
            } for f in fields
        ]
    }), 200


# 3. Sign the document
@sign.route('/documents/<int:doc_id>/sign', methods=['POST'])
@jwt_required()
def sign_document(doc_id):
    current_email = get_jwt_identity()
    current_user = User.query.filter_by(email=current_email).first()

    if not current_user:
        return jsonify({"message": "User not found"}), 404

    doc = Document.query.filter_by(id=doc_id, user_id=current_user.id).first()

    if not doc:
        return jsonify({"message": "Document not found"}), 404

    if doc.status == 'completed':
        return jsonify({"message": "Document already signed"}), 400

    if doc.status == 'voided':
        return jsonify({"message": "Document has been voided"}), 400

    data = request.get_json()
    consent = data.get('consent', False)
    field_values = data.get('fields', [])

    if not consent:
        return jsonify({"message": "Consent is required to sign"}), 400

    if not field_values:
        return jsonify({"message": "No field values provided"}), 400

    for fv in field_values:
        field = DocumentField.query.filter_by(
            id=fv.get('id'),
            document_id=doc_id
        ).first()
        if field:
            field.value = fv.get('value')

    doc.status = 'completed'

    log = AuditLog(
        document_id=doc_id,
        event='signed',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({
        "message": "Document signed successfully",
        "document_id": doc_id,
        "signed_at": datetime.utcnow().isoformat()
    }), 200