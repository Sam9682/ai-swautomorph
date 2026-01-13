#!/usr/bin/env python3
import click
import requests
import json
# import sqlite3  # COMMENTED OUT - Using PostgreSQL now
import subprocess
import os
import sys
from werkzeug.security import generate_password_hash

# Add the parent directory to the path so we can import from src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = 'http://www.swautomorph.com:80'

# Determine database type based on environment
USE_POSTGRES = os.environ.get('USE_POSTGRES', 'true').lower() == 'true'

@click.group()
def cli():
    """AI-SwAutoMorph CLI Tool"""
    pass

@cli.command()
@click.option('--username', prompt=True, help='Username')
@click.option('--email', prompt=True, help='Email address')
@click.option('--password', prompt=True, hide_input=True, help='Password')
@click.option('--first-name', help='First name')
@click.option('--last-name', help='Last name')
def register(username, email, password, first_name, last_name):
    """Register a new user"""
    data = {
        'username': username,
        'email': email,
        'password': password,
        'first_name': first_name or '',
        'last_name': last_name or ''
    }
    
    try:
        response = requests.post(f'{BASE_URL}/register', json=data)
        if response.status_code == 201:
            click.echo('User registered successfully!')
        else:
            click.echo(f'Error: {response.json().get("error", "Unknown error")}')
    except requests.exceptions.ConnectionError:
        click.echo('Error: Cannot connect to server. Make sure the application is running.')

@cli.command()
def list_apps():
    """List all available applications"""
    try:
        response = requests.get(f'{BASE_URL}/api/applications')
        if response.status_code == 200:
            apps = response.json()
            if apps:
                click.echo('\nAvailable Applications:')
                for app in apps:
                    click.echo(f"- {app['name']}: {app['url']}")
                    if app['description']:
                        click.echo(f"  Description: {app['description']}")
            else:
                click.echo('No applications found.')
        else:
            click.echo('Error fetching applications')
    except requests.exceptions.ConnectionError:
        click.echo('Error: Cannot connect to server. Make sure the application is running.')

@cli.command()
@click.option('--name', prompt=True, help='Application name')
@click.option('--url', prompt=True, help='Application URL')
@click.option('--description', help='Application description')
def add_app(name, url, description):
    """Add a new application (requires authentication)"""
    data = {
        'name': name,
        'url': url,
        'description': description or ''
    }
    
    try:
        if USE_POSTGRES:
            from src.database_postgres import db_manager
            db_manager.execute_query(
                'INSERT INTO applications (name, git_url, description) VALUES (%s, %s, %s)',
                (name, url, description or '')
            )
        else:
            click.echo('Error: SQLite operations are deprecated. Use PostgreSQL database instead.')
            return
        click.echo('Application added successfully!')
    except Exception as e:
        click.echo(f'Error: {str(e)}')

@cli.command()
@click.option('--token', prompt=True, help='SSO token to validate')
def validate_token(token):
    """Validate an SSO token"""
    data = {'token': token}
    
    try:
        response = requests.post(f'{BASE_URL}/sso/validate', json=data)
        if response.status_code == 200:
            result = response.json()
            if result['valid']:
                user = result['user']
                click.echo(f'Token is valid for user: {user["username"]} ({user["email"]})')
                click.echo(f'Expires at: {user["expires_at"]}')
            else:
                click.echo('Token is invalid or expired')
        else:
            click.echo('Token validation failed')
    except requests.exceptions.ConnectionError:
        click.echo('Error: Cannot connect to server. Make sure the application is running.')

@cli.command()
def init_db():
    """Initialize the database"""
    try:
        if USE_POSTGRES:
            from src.database_postgres import init_db as app_init_db
            click.echo('Initializing PostgreSQL database...')
        else:
            from src.database import init_db as app_init_db
            click.echo('Initializing SQLite database...')
        
        app_init_db()
        click.echo('Database initialized successfully!')
    except Exception as e:
        click.echo(f'Error initializing database: {str(e)}')
        sys.exit(1)

@cli.command()
def db_health():
    """Check database health"""
    try:
        from src.db_health import check_database_health, get_database_stats
        health = check_database_health()
        stats = get_database_stats()
        
        click.echo('\nDatabase Health Status:')
        click.echo(f"Status: {health['status']}")
        if health['status'] == 'healthy':
            click.echo(f"Tables: {health['tables_count']}")
            click.echo(f"Journal Mode: {health['journal_mode']}")
        else:
            click.echo(f"Error: {health.get('error', 'Unknown error')}")
        
        if 'error' not in stats:
            click.echo('\nDatabase Statistics:')
            for key, value in stats.items():
                if key.endswith('_count'):
                    table_name = key.replace('_count', '')
                    click.echo(f"{table_name.title()}: {value} records")
                elif key == 'database_size_bytes':
                    size_mb = value / (1024 * 1024)
                    click.echo(f"Database Size: {size_mb:.2f} MB")
        
    except Exception as e:
        click.echo(f'Error checking database health: {str(e)}')

@cli.command()
@click.argument('bucket_name')
@click.argument('mount_point')
@click.option('--passwd-file', default='.passwd-s3fs', help='S3FS password file')
def mount_s3fs(bucket_name, mount_point, passwd_file):
    """Mount OVH Cloud S3 storage using s3fs"""
    os.makedirs(mount_point, exist_ok=True)
    
    cmd = [
        "s3fs", bucket_name, mount_point,
        "-o", f"passwd_file={passwd_file}",
        "-o", "url=https://s3.gra.cloud.ovh.net",
        "-o", "use_path_request_style"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        click.echo(f"Successfully mounted {bucket_name} to {mount_point}")
    except subprocess.CalledProcessError as e:
        click.echo(f"Mount failed: {e}")

@cli.command()
@click.option('--show-env', is_flag=True, help='Show current environment settings')
def status(show_env):
    """Show application status and configuration"""
    db_type = "PostgreSQL" if USE_POSTGRES else "SQLite"
    click.echo(f'Database Type: {db_type}')
    
    if show_env:
        click.echo('\nEnvironment Variables:')
        click.echo(f'USE_POSTGRES: {os.environ.get("USE_POSTGRES", "false")}')
        if USE_POSTGRES:
            click.echo(f'POSTGRES_HOST: {os.environ.get("POSTGRES_HOST", "localhost")}')
            click.echo(f'POSTGRES_DB: {os.environ.get("POSTGRES_DB", "ai_swautomorph")}')
            click.echo(f'POSTGRES_USER: {os.environ.get("POSTGRES_USER", "swautomorph")}')
            click.echo(f'POSTGRES_PASSWORD: {"***" if os.environ.get("POSTGRES_PASSWORD") else "not set"}')
    
    try:
        if USE_POSTGRES:
            from src.database_postgres import db_manager
        else:
            from src.database import db_manager
        
        # Test connection
        result = db_manager.execute_query("SELECT 1", fetch_one=True)
        if result:
            click.echo(f'✅ Database connection: OK')
        else:
            click.echo(f'❌ Database connection: Failed')
    except Exception as e:
        click.echo(f'❌ Database connection: Failed - {str(e)}')

if __name__ == '__main__':
    cli()