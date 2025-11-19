"""Application entry point"""
import os
from .app import create_app
from .database import init_db

def main():
    """Main entry point"""
    # Initialize database
    init_db()
    
    # Create Flask app
    app = create_app()
    
    # Run application
    app.run(
        host='0.0.0.0', 
        port=5002, 
        debug=os.environ.get('FLASK_ENV') == 'development'
    )

if __name__ == '__main__':
    main()