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
        'no_description': 'No description available',
        'clone': 'Clone',
        'start': 'Start',
        'stop': 'Stop',
        'restart': 'Restart',
        'status': 'Status',
        'logs': 'Logs',
        'deployment_logs': 'Deployment Logs',
        'clear_logs': 'Clear Logs',
        'hide': 'Hide',
        'select_application': 'Select Application',
        'qchat_title': 'Q Chat - GenAI Assistant to modify the code of the selected Application',
        'auto_approve': 'Auto-approve updates/writes',
        'send': 'Send',
        'qchat_placeholder': 'Type your message to Q Chat...',
        'cancel': 'Cancel',
        'edit': 'Edit',
        'delete': 'Delete',
        'users': 'Users',
        'applications': 'Applications',
        'qchat_ready': 'Your virtual developer assistant is waiting for you! Ask it for a modification to the selected software, for example: add the ability to clock in multiple times per day in the ai-haccp software.'
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
        'no_description': 'Aucune description disponible',
        'clone': 'Cloner',
        'start': 'Démarrer',
        'stop': 'Arrêter',
        'restart': 'Redémarrer',
        'status': 'Statut',
        'logs': 'Journaux',
        'deployment_logs': 'Journaux de déploiement',
        'clear_logs': 'Effacer les journaux',
        'hide': 'Masquer',
        'select_application': 'Sélectionner une application',
        'qchat_title': 'Q Chat - Assistant GenAI pour modifier le code de l\'application sélectionnée',
        'auto_approve': 'Approuver automatiquement les mises à jour/écritures',
        'send': 'Envoyer',
        'qchat_placeholder': 'Tapez votre message à Q Chat...',
        'cancel': 'Annuler',
        'edit': 'Modifier',
        'delete': 'Supprimer',
        'users': 'Utilisateurs',
        'applications': 'Applications',
        'qchat_ready': 'Votre assistant développeur virtuel vous attend ! Demandez-lui une modification pour le logiciel sélectionné, par exemple : ajoute la possibilité de pointer plusieurs fois par jour dans le logiciel ai-haccp.'
    }
}