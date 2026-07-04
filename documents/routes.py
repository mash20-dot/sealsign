import os
import uuid
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models import Document, User
from storage.s3 import upload_file, delete_file, get_presigned_url

documents = Blueprint('documents', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'docx'}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_docx_to_pdf(file_bytes):
    import subprocess, tempfile
    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp_in:
        tmp_in.write(file_bytes)
        tmp_in_path = tmp_in.name

    tmp_out_dir = tempfile.mkdtemp()
    subprocess.run([
        'libreoffice', '--headless', '--convert-to', 'pdf',
        '--outdir', tmp_out_dir, tmp_in_path
    ], check=True)

    pdf_filename = os.path.basename(tmp_in_path).replace('.docx', '.pdf')
    pdf_path = os.path.join(tmp_out_dir, pdf_filename)

    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()

    os.unlink(tmp_in_path)
    os.unlink(pdf_path)

    return pdf_bytes


@documents.route('/upload', methods=['POST'])
@jwt_required()
def upload_document():
    current_email = get_jwt_identity()

    current_user = User.query.filter_by(email=current_email).first()

    if not current_user:
        return jsonify({
            "message": "user not found"
        }), 400

    if 'file' not in request.files:
        return jsonify({"message": "No file provided"}), 400

    file = request.files['file']

    if not file.filename:
        return jsonify({"message": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"message": "Only PDF and DOCX files are allowed"}), 400

    file_bytes = file.read()

    if len(file_bytes) > MAX_FILE_SIZE:
        return jsonify({"message": "File size exceeds 20MB limit"}), 400

    original_filename = secure_filename(file.filename)
    extension = original_filename.rsplit('.', 1)[1].lower()

    # Convert DOCX to PDF
    if extension == 'docx':
        file_bytes = convert_docx_to_pdf(file_bytes)
        mime_type = 'application/pdf'
        stored_filename = original_filename.replace('.docx', '.pdf')
    else:
        mime_type = 'application/pdf'
        stored_filename = original_filename

    # Generate unique key for R2
    file_key = f"documents/{current_user.id}/{uuid.uuid4()}/{stored_filename}"

    upload_file(file_bytes, file_key, mime_type)

    # Save to DB
    title = request.form.get('title') or original_filename.rsplit('.', 1)[0]

    doc = Document(
        user_id=current_user.id,
        title=title,
        original_filename=original_filename,
        file_key=file_key,
        file_size=len(file_bytes),
        mime_type=mime_type,
        status='draft'
    )
    db.session.add(doc)
    db.session.commit()

    return jsonify({
        "message": "Document uploaded successfully",
        "document": {
            "id": doc.id,
            "title": doc.title,
            "status": doc.status,
            "created_at": doc.created_at.isoformat()
        }
    }), 201


@documents.route('/all', methods=['GET'])
@jwt_required()
def list_documents():
    current_email = get_jwt_identity()

    current_user = User.query.filter_by(email=current_email).first()

    if not current_user:
        return jsonify({
            "user": "user not found"
        }), 400
    

    status = request.args.get('status')
    search = request.args.get('search')

    query = Document.query.filter_by(user_id=current_user.id)

    if status:
        query = query.filter_by(status=status)
    if search:
        query = query.filter(Document.title.ilike(f'%{search}%'))

    docs = query.order_by(Document.created_at.desc()).all()

    return jsonify({
        "documents": [
            {
                "id": d.id,
                "title": d.title,
                "original_filename": d.original_filename,
                "status": d.status,
                "file_size": d.file_size,
                "created_at": d.created_at.isoformat()
            } for d in docs
        ]
    }), 200


@documents.route('/<int:doc_id>', methods=['GET'])
@jwt_required()
def get_document(doc_id):
    current_email = get_jwt_identity()

    current_user = User.query.filter_by(email=current_email).first()
    doc = Document.query.filter_by(id=doc_id, user_id=current_user.id).first()

    if not doc:
        return jsonify({"message": "Document not found"}), 404

    return jsonify({
        "id": doc.id,
        "title": doc.title,
        "original_filename": doc.original_filename,
        "status": doc.status,
        "file_size": doc.file_size,
        "mime_type": doc.mime_type,
        "created_at": doc.created_at.isoformat(),
        "updated_at": doc.updated_at.isoformat()
    }), 200


@documents.route('/<int:doc_id>/download', methods=['GET'])
@jwt_required()
def download_document(doc_id):
    current_email = get_jwt_identity()

    current_user = User.query.filter_by(email=current_email).first()

    if not current_user:
        return jsonify({
            "message": "user not found"
        }), 400
    
    doc = Document.query.filter_by(id=doc_id, user_id=current_user.id).first()

    if not doc:
        return jsonify({"message": "Document not found"}), 404

    url = get_presigned_url(doc.file_key)

    return jsonify({"download_url": url}), 200


@documents.route('/<int:doc_id>', methods=['DELETE'])
@jwt_required()
def delete_document(doc_id):
    current_email = get_jwt_identity()

    current_user = User.query.filter_by(email=current_email).first()

    if not current_user:
        return jsonify({

            "message": "user not found"
        }), 400
    
    
    doc = Document.query.filter_by(id=doc_id, user_id=current_user.id).first()

    if not doc:
        return jsonify({"message": "Document not found"}), 404

    delete_file(doc.file_key)
    db.session.delete(doc)
    db.session.commit()

    return jsonify({"message": "Document deleted"}), 200