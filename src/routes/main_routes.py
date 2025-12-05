"""Main application routes"""
from flask import Blueprint, render_template, session, redirect, url_for, request, send_from_directory
import sqlite3
import os
from ..config import DB_PATH
from ..database import db_manager

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))
    return render_template('login.html')

@main_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('main.index'))
    
    # Get username for admin check
    user = db_manager.execute_query(
        'SELECT username FROM users WHERE id = ?', 
        (session['user_id'],), fetch_one=True
    )
    username = user[0] if user else ''
    
    # Get applications based on user role
    applications_raw = db_manager.execute_query('''
        SELECT a.id, a.name, ua.url, a.description, a.git_url 
        FROM applications a
        JOIN user_applications ua ON a.id = ua.application_id
        WHERE ua.user_id = ?
        ORDER BY a.name
    ''', (session['user_id'],), fetch_all=True)
    
    # Use URLs directly from the database table user_applications
    applications = []
    for app in applications_raw:
        app_id, app_name, db_url, description, git_url = app
        
        # Use the URL stored in the database instead of calculating it
        applications.append((app_id, app_name, db_url, description, git_url))
    
    # Get SSO token for the user
    sso_token = session.get('sso_token', '')
    
    return render_template('dashboard.html', applications=applications, username=username, sso_token=sso_token, user_id=session['user_id'])

@main_bp.route('/set_language/<language>')
def set_language(language):
    if language in ['en', 'fr']:
        session['language'] = language
    return redirect(request.referrer or url_for('main.index'))

@main_bp.route('/.well-known/pki-validation/<filename>')
def ssl_validation(filename):
    """Serve SSL certificate validation files"""
    static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static')
    validation_dir = os.path.join(static_dir, '.well-known', 'pki-validation')
    return send_from_directory(validation_dir, filename)