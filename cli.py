#!/usr/bin/env python3
import click
import requests
import json
import sqlite3
from werkzeug.security import generate_password_hash

BASE_URL = 'http://www.swautomorph.com:5000'

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
        # Note: For CLI, we'd need to implement session handling or token-based auth
        # For now, this is a direct database operation
        conn = sqlite3.connect('ai_swautomorph.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO applications (name, url, description) VALUES (?, ?, ?)',
                      (name, url, description or ''))
        conn.commit()
        conn.close()
        click.echo('Application added successfully!')
    except Exception as e:
        click.echo(f'Error: {str(e)}')

@cli.command()
def init_db():
    """Initialize the database"""
    from app import init_db as app_init_db
    app_init_db()
    click.echo('Database initialized successfully!')

if __name__ == '__main__':
    cli()