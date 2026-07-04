from flask import Flask
from flask_jwt_extended import JWTManager
from datetime import timedelta
from app.extensions import db, migrate
import os
from dotenv import load_dotenv
load_dotenv()
import sys
from flask_cors import CORS
sys.path.append('.')

from security.auth import security
from documents.routes import documents


app = Flask(__name__)



# CORS Configuration
CORS(app, resources={
    r"/*": {
        "origins": [
            "http://localhost:3000",
            "http://localhost:4000",
            "http://localhost:5173",
            "https://beta.celestifan.com",
            "https://www.celestifan.com",
        ],
        "supports_credentials": True,
        "allow_headers": ["Content-Type", "Authorization"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    }
})



app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=5) 
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')


# Session Configuration Required for OAuth state management
app.config['SESSION_COOKIE_SECURE'] = True  
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False



app.config['JJWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')



# Register Blueprints
app.register_blueprint(security, url_prefix='/security')
app.register_blueprint(documents, url_prefix='/documents')

db.init_app(app)
migrate.init_app(app, db)
jwt = JWTManager(app)

with app.app_context():

    db.create_all()










if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port)