from flask import Flask, Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from app.extentions import db
from app.models import User
import re
import resend

security = Blueprint('security', __name__)


#Validating email format
EMAIL_REGEX = r'^[\w\.-]+@[\w\.-]+\.\w+$'


def send_welcome_email(user_email, user_name):
    """Send welcome email to new user after successful signup"""
    try:
        params = {
            "from": "noreply@sealsign.com",
            "to": [user_email],
            "subject": f"Welcome to SealSign, {user_name}!",
            "html": f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #534AB7; margin-bottom: 6px;">SealSign</h1>
                        <p style="color: #888; font-size: 14px; margin: 0;">Secure document signing</p>
                    </div>

                    <p style="font-size: 16px;">Hi {user_name},</p>

                    <p style="font-size: 16px; line-height: 1.6;">
                        Your SealSign account is ready. You can now upload documents, add signers, and get
                        legally binding signatures all in one place.
                    </p>

                    <div style="background-color: #f8f8f6; padding: 20px; border-radius: 8px; margin: 24px 0;">
                        <h3 style="margin-top: 0; color: #1a1a18;">Get started in 3 steps:</h3>
                        <ol style="line-height: 2; color: #555; padding-left: 18px;">
                            <li>Upload a document (PDF or DOCX)</li>
                            <li>Place signature fields and add your signers</li>
                            <li>Send — signers get an email link instantly</li>
                        </ol>
                    </div>

                    <div style="text-align: center; margin: 30px 0;">
                        <a href="https://sealsign.com/dashboard"
                           style="background-color: #534AB7; color: white; padding: 12px 28px;
                                  border-radius: 6px; text-decoration: none; font-size: 15px;
                                  font-weight: bold;">
                            Go to your dashboard →
                        </a>
                    </div>

                    <p style="font-size: 14px; color: #666; margin-top: 30px; padding-top: 20px;
                               border-top: 1px solid #e5e5e0;">
                        Questions? Reach us at
                        <a href="mailto:business@sealsign.co" style="color: #534AB7;">business@sealsign.co</a>
                    </p>

                    <p style="font-size: 14px; color: #666;">
                        — The SealSign Team
                    </p>
                </div>
            """
        }

        resend.Emails.send(params)
        return True
    except Exception as e:
        print(f"Error sending welcome email: {e}")
        return False


@security.route('/signup', methods=['POST'])
def securitysignup():
    
    try:

        data = request.get_json()

        name = data.get('name')
        email = data.get('email')

        if not email or not name:
            return jsonify({
                "message": "email and name are required"
            }), 400
        
        if not re.match(EMAIL_REGEX, email):
                return jsonify({
                    "message": "Invalid email format"
                }), 400
        
        new_user = User(
            email=email,
            name=name
        )

        db.session.add(new_user)
        db.session.commit()

        send_welcome_email(email, name)

        return jsonify({
            "message": "signup completed"
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "message": f"Signup failed: {str(e)}"
        }), 500
        
