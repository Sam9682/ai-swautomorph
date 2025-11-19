"""Main Flask application"""
from flask import Flask, session
from flask_cors import CORS
from .config import SECRET_KEY, CORS_ORIGINS, TRANSLATIONS
from .database import init_db
from .routes.main_routes import main_bp
from .routes.auth_routes import auth_bp
from .routes.sso_routes import sso_bp
from .routes.api_routes import api_bp

def create_app():
    """Application factory"""
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.secret_key = SECRET_KEY
    
    # Configure CORS
    CORS(app, origins=CORS_ORIGINS, supports_credentials=True)
    
    # Language support
    def get_language():
        return session.get('language', 'en')

    def get_text(key):
        lang = get_language()
        return TRANSLATIONS.get(lang, {}).get(key, TRANSLATIONS['en'].get(key, key))

    @app.context_processor
    def inject_language():
        return {'get_text': get_text, 'current_lang': get_language()}
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(sso_bp)
    app.register_blueprint(api_bp)
    
    return app