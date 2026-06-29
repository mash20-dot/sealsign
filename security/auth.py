from flask import Flask, Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from app.extensions import db
from app.models import User
import re
import resend
import secrets
from datetime import datetime, timedelta


security = Blueprint('security', __name__)


#Validating email format
EMAIL_REGEX = r'^[\w\.-]+@[\w\.-]+\.\w+$'


def send_magic_link_email(user_email, user_name, magic_link):
    try:
        params = {
            "from": "business@vynfy.com",
            "to": [user_email],
            "subject": "Your SealSign login link",
            "html": f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h1 style="color: #534AB7;">SealSign</h1>
                    <p>Hi {user_name},</p>
                    <p>Click the button below to log in. This link expires in 15 minutes and can only be used once.</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{magic_link}"
                           style="background-color: #534AB7; color: white; padding: 12px 28px;
                                  border-radius: 6px; text-decoration: none; font-size: 15px;
                                  font-weight: bold;">
                            Log in to SealSign →
                        </a>
                    </div>
                    <p style="font-size: 13px; color: #888;">If you didn't request this, ignore this email.</p>
                    <p style="font-size: 14px; color: #666;">— The SealSign Team</p>
                </div>
            """
        }
        resend.Emails.send(params)
        return True
    except Exception as e:
        print(f"Error sending magic link email: {e}")
        return False



def send_welcome_email(user_email, user_name):
    """Send welcome email to new user after successful signup"""
    try:
        params = {
            "from": "business@vynfy.com",
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
    



def send_welcome_email_to_admin(user_email):
    """Send welcome email to new user after successful signup"""
    try:
        params = {
            "from": "business@vynfy.com",
            "to": "sakyimustapha5@gmail.com",
            "subject": f"someone signed up on SealSign, {user_email}!",
            "html": f"""


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
        
        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            return jsonify({
                "message": "email already exist"
            }), 400
        
        new_user = User(
            email=email,
            name=name
        )

        db.session.add(new_user)
        db.session.commit()

        send_welcome_email(email, name)
        send_welcome_email_to_admin(email)

        return jsonify({
            "message": "signup completed"
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "message": f"Signup failed: {str(e)}"
        }), 500
 
@security.route('/login', methods=['POST'])
def securitylogin():

    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({"message": "email is required"}), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"message": "Invalid email"}), 400

    # Generate magic link token
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(minutes=15)

    # Save token to user record
    user.magic_link_token = token
    user.magic_link_expires = expires_at
    db.session.commit()

    # Build the magic link
    magic_link = f"https://yourdomain.com/auth/verify-magic-link?token={token}"

    # Send email
    send_magic_link_email(user.email, user.name, magic_link)

    return jsonify({
        "message": "Magic link sent to your email. It expires in 15 minutes."
    }), 200


@security.route('/verify-magic-link', methods=['GET'])
def verify_magic_link():

    token = request.args.get('token')

    if not token:
        return jsonify({"message": "Token is required"}), 400

    user = User.query.filter_by(magic_link_token=token).first()

    if not user:
        return jsonify({"message": "Invalid or expired token"}), 400

    if datetime.utcnow() > user.magic_link_expires:
        # Clear expired token
        user.magic_link_token = None
        user.magic_link_expires = None
        db.session.commit()
        return jsonify({"message": "Magic link has expired, request a new one"}), 400

    # Clear token after use — one time only
    user.magic_link_token = None
    user.magic_link_expires = None
    db.session.commit()

    # Now issue the JWT
    access_token = create_access_token(identity=user.email)

    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
        }
    }), 200
    

    
    
        
