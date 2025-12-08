#!/usr/bin/env python3
"""WSGI entry point for production"""
from src.app import create_app
from src.database import init_db

init_db()
app = create_app()

if __name__ == '__main__':
    app.run()
