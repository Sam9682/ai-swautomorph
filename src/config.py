"""Configuration settings for AI-SwAutoMorph"""
import os

# Database configuration
DB_PATH = 'ai_swautomorph.db'

# Flask configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
FLASK_ENV = os.environ.get('FLASK_ENV', 'development')

# CORS configuration
CORS_ORIGINS = [
    'https://ai-haccp.swautomorph.com:8102', 
    'https://ai-haccp.swautomorph.com'
]

# Language translations
TRANSLATIONS = {
    'en': {
        'login': 'Login',
        'register': 'Register',
        'username': 'Username',
        'email': 'Email',
        'password': 'Password',
        'first_name': 'First Name',
        'last_name': 'Last Name',
        'dashboard': 'Dashboard',
        'logout': 'Logout',
        'welcome': 'Welcome',
        'available_applications': 'Available Applications',
        'add_new_application': 'Add New Application',
        'application_name': 'Application Name',
        'url': 'URL',
        'description': 'Description',
        'add_application': 'Add Application',
        'no_apps': 'No applications available yet.',
        'already_account': 'Already have an account?',
        'no_account': "Don't have an account?",
        'login_here': 'Login here',
        'register_here': 'Register here',
        'open_application': 'Open Application',
        'no_description': 'No description available'
    },
    'fr': {
        'login': 'Connexion',
        'register': 'Inscription',
        'username': "Nom d'utilisateur",
        'email': 'Email',
        'password': 'Mot de passe',
        'first_name': 'Prénom',
        'last_name': 'Nom',
        'dashboard': 'Tableau de bord',
        'logout': 'Déconnexion',
        'welcome': 'Bienvenue',
        'available_applications': 'Applications disponibles',
        'add_new_application': 'Ajouter une nouvelle application',
        'application_name': "Nom de l'application",
        'url': 'URL',
        'description': 'Description',
        'add_application': 'Ajouter une application',
        'no_apps': 'Aucune application disponible pour le moment.',
        'already_account': 'Vous avez déjà un compte ?',
        'no_account': "Vous n'avez pas de compte ?",
        'login_here': 'Connectez-vous ici',
        'register_here': 'Inscrivez-vous ici',
        'open_application': "Ouvrir l'application",
        'no_description': 'Aucune description disponible'
    }
}