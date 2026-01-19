#!/usr/bin/env python3
import click
import requests
import json
import subprocess
import os
import sys
from werkzeug.security import generate_password_hash

# Add the parent directory to the path so we can import from src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = 'http://www.swautomorph.com:80'

def select_from_list(items, title="Select an option"):
    """Interactive selection using arrow keys"""
    try:
        from simple_term_menu import TerminalMenu
        terminal_menu = TerminalMenu(
            items,
            title=title,
            menu_cursor="▶ ",
            menu_cursor_style=("fg_cyan", "bold"),
            menu_highlight_style=("bg_cyan", "fg_black"),
            cycle_cursor=True
        )
        choice = terminal_menu.show()
        return items[choice] if choice is not None else None
    except ImportError:
        # Fallback to numbered selection
        click.echo(f"\n{title}")
        for idx, item in enumerate(items, 1):
            click.echo(f"{idx}. {item}")
        choice = click.prompt('Select number', type=int)
        if 1 <= choice <= len(items):
            return items[choice - 1]
        return None

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
                nb = 1
                for app in apps:
                    url = app.get('git_url') or app.get('url', 'N/A')
                    click.echo(f"{nb}- {app['name']}: {url}")
                    if app.get('description'):
                        click.echo(f"  Description: {app['description']}")
                    nb = nb + 1
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
    try:
        from src.database_postgres import db_manager
        db_manager.execute_query(
            'INSERT INTO applications (name, git_url, description) VALUES (%s, %s, %s)',
            (name, url, description or '')
        )
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
    """Initialize the PostgreSQL database"""
    try:
        from src.database_postgres import init_db as app_init_db
        click.echo('Initializing PostgreSQL database...')
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
        
        click.echo('\n' + '='*60)
        click.echo('DATABASE HEALTH STATUS')
        click.echo('='*60)
        click.echo(f"Status: {health['status']}")
        if health['status'] == 'healthy':
            click.echo(f"Tables: {health['tables_count']}")
            click.echo(f"Journal Mode: {health['journal_mode']}")
        else:
            click.echo(f"Error: {health.get('error', 'Unknown error')}")
        
        if 'error' not in stats:
            click.echo('\n' + '='*60)
            click.echo('DATABASE STATISTICS')
            click.echo('='*60)
            click.echo(f"{'Table':<30} {'Records':>10}")
            click.echo('-'*60)
            for key, value in sorted(stats.items()):
                if key.endswith('_count'):
                    table_name = key.replace('_count', '').replace('_', ' ').title()
                    click.echo(f"{table_name:<30} {value:>10,}")
            click.echo('-'*60)
            if 'database_size_bytes' in stats:
                size_mb = stats['database_size_bytes'] / (1024 * 1024)
                click.echo(f"{'Database Size':<30} {size_mb:>9.2f} MB")
            click.echo('='*60)
        
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
    click.echo('Database Type: PostgreSQL')
    
    if show_env:
        click.echo('\nEnvironment Variables:')
        click.echo(f'POSTGRES_HOST: {os.environ.get("POSTGRES_HOST", "localhost")}')
        click.echo(f'POSTGRES_DB: {os.environ.get("POSTGRES_DB", "ai_swautomorph")}')
        click.echo(f'POSTGRES_USER: {os.environ.get("POSTGRES_USER", "swautomorph")}')
        click.echo(f'POSTGRES_PASSWORD: {"***" if os.environ.get("POSTGRES_PASSWORD") else "not set"}')
    
    try:
        from src.database_postgres import db_manager
        result = db_manager.execute_query("SELECT 1", fetch_one=True)
        if result:
            click.echo(f'✅ Database connection: OK')
        else:
            click.echo(f'❌ Database connection: Failed')
    except Exception as e:
        click.echo(f'❌ Database connection: Failed - {str(e)}')

@cli.command()
@click.confirmation_option(prompt='⚠️  This will permanently delete PostgreSQL database. Continue?')
def delete_db():
    """Delete PostgreSQL database completely"""
    import shutil
    from src.database_postgres import db_manager
    
    deleted = []
    errors = []
    
    # Drop all tables in the database
    try:
        click.echo('Dropping all tables...')
        tables_query = "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        tables = db_manager.execute_query(tables_query, fetch_all=True)
        
        for (table_name,) in tables:
            try:
                db_manager.execute_query(f'DROP TABLE IF EXISTS {table_name} CASCADE')
                deleted.append(f'Table: {table_name}')
            except Exception as e:
                errors.append(f'Table {table_name}: {str(e)}')
    except Exception as e:
        errors.append(f'Database operation: {str(e)}')
    
    # PostgreSQL data directory (Docker)
    postgres_data = 'softfluid/postgres_data'
    if os.path.exists(postgres_data):
        try:
            shutil.rmtree(postgres_data)
            deleted.append(f'Directory: {postgres_data}')
        except Exception as e:
            errors.append(f'{postgres_data}: {str(e)}')
    
    if deleted:
        click.echo('\n✅ Deleted:')
        for item in deleted:
            click.echo(f'  - {item}')
    
    if errors:
        click.echo('\n❌ Errors:')
        for error in errors:
            click.echo(f'  - {error}')
    
    if not deleted and not errors:
        click.echo('No PostgreSQL database or tables found.')

@cli.command()
def list_tables():
    """List all tables with record counts"""
    try:
        from src.database_postgres import db_manager
        
        tables_query = "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
        tables = db_manager.execute_query(tables_query, fetch_all=True)
        
        if not tables:
            click.echo('No tables found in database.')
            return
        
        click.echo('\n' + '='*60)
        click.echo('DATABASE TABLES')
        click.echo('='*60)
        click.echo(f"{'Table Name':<40} {'Records':>15}")
        click.echo('-'*60)
        
        for (table_name,) in tables:
            count_query = f"SELECT COUNT(*) FROM {table_name}"
            result = db_manager.execute_query(count_query, fetch_one=True)
            count = result[0] if result else 0
            click.echo(f"{table_name:<40} {count:>15,}")
        
        click.echo('='*60)
        
    except Exception as e:
        click.echo(f'Error: {str(e)}')

@cli.command()
@click.argument('sql_query')
@click.confirmation_option(prompt='⚠️  This will execute an SQL query. Continue?')
def exec_sql_request(sql_query):
    """Execute SQL query on database"""
    try:
        from src.database_postgres import db_manager
        
        result = db_manager.execute_query(sql_query)
        click.echo(f'✅ Query executed successfully. Rows affected: {result if result else 0}')
        
    except Exception as e:
        click.echo(f'❌ Error: {str(e)}')

@cli.command()
@click.argument('table_name', required=False)
def describe_table(table_name):
    """Describe table structure"""
    try:
        from src.database_postgres import db_manager
        
        # Get all tables if no table specified
        if not table_name:
            tables_query = "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
            tables = db_manager.execute_query(tables_query, fetch_all=True)
            
            if not tables:
                click.echo('No tables found in database.')
                return
            
            table_list = [tbl[0] for tbl in tables]
            table_name = select_from_list(table_list, "Select table to describe:")
            
            if not table_name:
                click.echo('No table selected.')
                return
        
        # Get table structure
        structure_query = """
            SELECT column_name, data_type, character_maximum_length, 
                   is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
        """
        columns = db_manager.execute_query(structure_query, (table_name,), fetch_all=True)
        
        if not columns:
            click.echo(f'Table "{table_name}" not found.')
            return
        
        click.echo('\n' + '='*80)
        click.echo(f'TABLE: {table_name}')
        click.echo('='*80)
        click.echo(f"{'Column':<25} {'Type':<20} {'Nullable':<10} {'Default':<20}")
        click.echo('-'*80)
        
        for col_name, data_type, max_len, nullable, default in columns:
            type_str = f"{data_type}({max_len})" if max_len else data_type
            default_str = str(default)[:18] if default else '-'
            click.echo(f"{col_name:<25} {type_str:<20} {nullable:<10} {default_str:<20}")
        
        click.echo('='*80)
        
    except Exception as e:
        click.echo(f'Error: {str(e)}')

@cli.command()
@click.argument('table_name', required=False)
@click.option('--limit', default=10, help='Number of rows to display')
def select_table(table_name, limit):
    """Display table content"""
    try:
        from src.database_postgres import db_manager
        
        # Get all tables if no table specified
        if not table_name:
            tables_query = "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
            tables = db_manager.execute_query(tables_query, fetch_all=True)
            
            if not tables:
                click.echo('No tables found in database.')
                return
            
            table_list = [tbl[0] for tbl in tables]
            table_name = select_from_list(table_list, "Select table to view:")
            
            if not table_name:
                click.echo('No table selected.')
                return
        
        # Get column names
        columns_query = """
            SELECT column_name FROM information_schema.columns
            WHERE table_name = %s ORDER BY ordinal_position
        """
        columns = db_manager.execute_query(columns_query, (table_name,), fetch_all=True)
        
        if not columns:
            click.echo(f'Table "{table_name}" not found.')
            return
        
        col_names = [col[0] for col in columns]
        
        # Get table data
        data_query = f"SELECT * FROM {table_name} LIMIT %s"
        rows = db_manager.execute_query(data_query, (limit,), fetch_all=True)
        
        if not rows:
            click.echo(f'\nTable "{table_name}" is empty.')
            return
        
        # Calculate column widths
        col_widths = [len(name) for name in col_names]
        for row in rows:
            for i, val in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(val)) if val is not None else 4)
        
        # Limit column width to 30 characters
        col_widths = [min(w, 30) for w in col_widths]
        
        total_width = sum(col_widths) + len(col_widths) * 3 + 1
        
        click.echo('\n' + '='*total_width)
        click.echo(f'TABLE: {table_name} (showing {len(rows)} of {len(rows)} rows)')
        click.echo('='*total_width)
        
        # Print header
        header = ' | '.join(name[:w].ljust(w) for name, w in zip(col_names, col_widths))
        click.echo(header)
        click.echo('-'*total_width)
        
        # Print rows
        for row in rows:
            row_str = ' | '.join(
                str(val)[:w].ljust(w) if val is not None else 'NULL'.ljust(w)
                for val, w in zip(row, col_widths)
            )
            click.echo(row_str)
        
        click.echo('='*total_width)
        
    except Exception as e:
        click.echo(f'Error: {str(e)}')

@cli.command()
def sync_nginx_locations():
    """Sync nginx locations from database"""
    try:
        from src.database_postgres import db_manager
        from src.nginx_manager import sync_all_locations
        
        click.echo('Synchronizing nginx locations from database...')
        
        if sync_all_locations(db_manager):
            click.echo('✓ Nginx locations synced successfully')
        else:
            click.echo('✗ Failed to sync nginx locations')
            sys.exit(1)
    except Exception as e:
        click.echo(f'✗ Error: {str(e)}')
        sys.exit(1)

@cli.command()
def platform_status():
    """Show platform status and server roles"""
    try:
        from src.platform_discovery import get_current_server_ip
        from src.database_postgres import db_manager
        
        current_ip = get_current_server_ip()
        server = db_manager.execute_query(
            'SELECT server_type, server_name FROM servers WHERE server_ip = %s',
            (current_ip,), fetch_one=True
        )
        
        if server:
            click.echo(f"Platform Role: {server[0]}")
            click.echo(f"Server Name: {server[1]}")
            click.echo(f"Server IP: {current_ip}")
        else:
            click.echo("Server not registered in database")
        
        servers = db_manager.execute_query(
            'SELECT server_ip, server_name, server_type, server_status FROM servers ORDER BY id',
            fetch_all=True
        )
        
        click.echo("\nAll Servers:")
        for s in servers:
            click.echo(f"  - {s[1]} ({s[0]}): {s[2]} [{s[3]}]")
    except Exception as e:
        click.echo(f'Error: {str(e)}')

@cli.command()
@click.argument('remote_ip')
def discover_server(remote_ip):
    """Discover remote SwAutoMorph server"""
    try:
        from src.platform_discovery import get_current_server_ip, check_remote_platform, determine_role, update_server_role
        from src.database_postgres import db_manager
        
        click.echo(f"Checking {remote_ip} for SwAutoMorph...")
        
        remote_status = check_remote_platform(remote_ip)
        
        if remote_status:
            click.echo(f"✓ SwAutoMorph found!")
            click.echo(f"  Role: {remote_status.get('role')}")
            click.echo(f"  Version: {remote_status.get('version')}")
            click.echo(f"  Server: {remote_status.get('server_name')}")
            
            current_ip = get_current_server_ip()
            our_role = determine_role(current_ip, remote_ip, remote_status, db_manager)
            
            click.echo(f"\nRole determination:")
            click.echo(f"  Current server will be: {our_role}")
            click.echo(f"  Remote server is: {remote_status.get('role')}")
            
            update_server_role(current_ip, our_role, db_manager)
            click.echo(f"\n✓ Local server role updated to {our_role}")
        else:
            click.echo("✗ No SwAutoMorph detected at this IP")
    except Exception as e:
        click.echo(f'Error: {str(e)}')

if __name__ == '__main__':
    cli()