"""Main Flask application"""
from flask import Flask, session
from flask_cors import CORS
import sys
import os
from .config import SECRET_KEY, CORS_ORIGINS, TRANSLATIONS
from .database import init_db
from .routes.main_routes import main_bp
from .routes.auth_routes import auth_bp
from .routes.sso_routes import sso_bp
from .routes.api_routes import api_bp
from .routes.billing_routes import billing_bp

# Redirect all print() statements to log files
class PrintLogger:
    def __init__(self, log_file):
        self.log_file = log_file
        self.terminal = sys.stdout
        
    def write(self, message):
        if message.strip():  # Only log non-empty messages
            with open(self.log_file, 'a') as f:
                f.write(f"{message}")
                f.flush()
        self.terminal.write(message)
        
    def flush(self):
        self.terminal.flush()

# Setup print logging
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)
print_log_file = os.path.join(log_dir, 'print_output.log')
sys.stdout = PrintLogger(print_log_file)

def create_app():
    """Application factory"""
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.secret_key = SECRET_KEY
    
    # Configure CORS
    CORS(app, origins=CORS_ORIGINS, supports_credentials=True)
    
    # Language support
    def get_language():
        return session.get('language', 'fr')

    def get_text(key):
        lang = get_language()
        return TRANSLATIONS.get(lang, {}).get(key, TRANSLATIONS['en'].get(key, key))

    @app.context_processor
    def inject_language():
        from datetime import datetime
        return {
            'get_text': get_text, 
            'current_lang': get_language(),
            'moment': lambda: datetime.now()
        }
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(sso_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(billing_bp)
    
    return app