"""Main Flask application for AI-SwAutoMorph with PostgreSQL support"""
import os
import sys

# Determine which database to use based on environment
USE_POSTGRES = os.environ.get('USE_POSTGRES', 'false').lower() == 'true'

if USE_POSTGRES:
    # Use PostgreSQL
    from src.database_postgres import db_manager, init_db
    from src.config_postgres import *
    print("Using PostgreSQL database")
else:
    # Use SQLite (legacy)
    from src.database_postgres import db_manager, init_db
    from src.config import *
    print("Using SQLite database")

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_cors import CORS
import logging
from datetime import datetime
import threading

# Import route blueprints
from src.routes.main_routes import main_bp
from src.routes.auth_routes import auth_bp
from src.routes.sso_routes import sso_bp
from src.routes.api_routes import api_bp
from src.routes.genai_routes import genai_bp
from src.routes.billing_routes import billing_bp

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['FLASK_ENV'] = FLASK_ENV
    
    # CORS configuration
    CORS(app, origins=CORS_ORIGINS, supports_credentials=True)
    
    # Logging configuration
    if not app.debug:
        logs_dir = get_logs_dir()
        os.makedirs(logs_dir, exist_ok=True)
        
        # Create file handler
        log_file = os.path.join(logs_dir, f'app_logs_{datetime.now().strftime("%Y%m%d")}.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )
        file_handler.setFormatter(formatter)
        
        # Add handler to app logger
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('AI-SwAutoMorph startup')
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(sso_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(genai_bp)
    app.register_blueprint(billing_bp)
    
    # Initialize database
    with app.app_context():
        try:
            init_db()
            app.logger.info('Database initialized successfully')
        except Exception as e:
            app.logger.error(f'Database initialization failed: {e}')
            raise
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Health check endpoint for load balancer"""
        try:
            # Test database connection
            if USE_POSTGRES:
                with db_manager.get_db_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute('SELECT 1')
                        cursor.fetchone()
            else:
                with db_manager.get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT 1')
                    cursor.fetchone()
            
            return jsonify({
                'status': 'healthy',
                'database': 'postgresql' if USE_POSTGRES else 'sqlite',
                'instance_id': os.environ.get('INSTANCE_ID', '1'),
                'timestamp': datetime.now().isoformat()
            }), 200
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'error': str(e),
                'database': 'postgresql' if USE_POSTGRES else 'sqlite',
                'instance_id': os.environ.get('INSTANCE_ID', '1'),
                'timestamp': datetime.now().isoformat()
            }), 503
    
    return app

def main():
    """Main entry point"""
    app = create_app()
    
    # Get instance configuration
    instance_id = os.environ.get('INSTANCE_ID', '1')
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_ENV', 'production') == 'development'
    
    print(f"Starting AI-SwAutoMorph Instance {instance_id}")
    print(f"Database: {'PostgreSQL' if USE_POSTGRES else 'SQLite'}")
    print(f"Listening on {host}:{port}")
    
    # Run the application
    app.run(host=host, port=port, debug=debug, threaded=True)

if __name__ == '__main__':
    main()