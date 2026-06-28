from flask import Flask
from flask_jwt_extended import JWTManager
from datetime import timedelta
from app.extentions import db
import os
from dotenv import load_dotenv
load_dotenv()
import sys
from flask_cors import CORS
sys.path.append('.')

from security.auth import security
from follow.followers import follow
from music.links import music

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

# Flask Secret Key (Required for sessions in OAuth)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Session Configuration Required for OAuth state management
app.config['SESSION_COOKIE_SECURE'] = True  
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
"pool_pre_ping": True,
"pool_recycle": 300,
"pool_size": 5,
"max_overflow": 0,
}

app.config['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID')
app.config['GOOGLE_CLIENT_SECRET'] = os.getenv('GOOGLE_CLIENT_SECRET')
app.config['GOOGLE_REDIRECT_URI'] = os.getenv('GOOGLE_REDIRECT_URI')  

app.config['FACEBOOK_APP_ID'] = os.getenv('FACEBOOK_APP_ID')
app.config['FACEBOOK_APP_SECRET'] = os.getenv('FACEBOOK_APP_SECRET')
app.config['FACEBOOK_REDIRECT_URI'] = os.getenv('FACEBOOK_REDIRECT_URI') 


app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

app_logger.init_app(app)

# Register Blueprints
app.register_blueprint(security, url_prefix='/security')
app.register_blueprint(follow, url_prefix='/follow')
app.register_blueprint(music, url_prefix='/music')

db.init_app(app)
jwt = JWTManager(app)

with app.app_context():

    db.create_all()


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port)