"""Main application routes"""
from flask import Blueprint, render_template, session, redirect, url_for, request
import sqlite3
from ..config import DB_PATH

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
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get username for admin check
    cursor.execute('SELECT username FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    username = user[0] if user else ''
    
    # Get applications based on user role
    if username == 'admin':
        # Admin sees all applications
        cursor.execute('SELECT id, name, url, description FROM applications ORDER BY name')
    else:
        # Regular users see only assigned applications
        cursor.execute('''
            SELECT a.id, a.name, a.url, a.description 
            FROM applications a
            JOIN user_applications ua ON a.id = ua.application_id
            WHERE ua.user_id = ?
            ORDER BY a.name
        ''', (session['user_id'],))
    
    applications = cursor.fetchall()
    conn.close()
    
    # Get SSO token for the user
    sso_token = session.get('sso_token', '')
    
    return render_template('dashboard.html', applications=applications, username=username, sso_token=sso_token)

@main_bp.route('/set_language/<language>')
def set_language(language):
    if language in ['en', 'fr']:
        session['language'] = language
    return redirect(request.referrer or url_for('main.index'))