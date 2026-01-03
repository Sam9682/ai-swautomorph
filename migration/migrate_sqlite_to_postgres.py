#!/usr/bin/env python3
"""
SQLite to PostgreSQL Migration Script for AI-SwAutoMorph
Migrates all data from SQLite database to PostgreSQL
"""

import sqlite3
import psycopg2
import sys
import os
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config_postgres import get_database_config

def connect_sqlite(db_path):
    """Connect to SQLite database"""
    if not os.path.exists(db_path):
        print(f"SQLite database not found: {db_path}")
        return None
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn

def connect_postgresql():
    """Connect to PostgreSQL database"""
    config = get_database_config()
    try:
        conn = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['user'],
            password=config['password']
        )
        return conn
    except Exception as e:
        print(f"Failed to connect to PostgreSQL: {e}")
        return None

def migrate_table(sqlite_conn, pg_conn, table_name, column_mapping=None):
    """Migrate a single table from SQLite to PostgreSQL"""
    print(f"Migrating table: {table_name}")
    
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    # Get data from SQLite
    sqlite_cursor.execute(f"SELECT * FROM {table_name}")
    rows = sqlite_cursor.fetchall()
    
    if not rows:
        print(f"  No data found in {table_name}")
        return
    
    # Get column names
    columns = [description[0] for description in sqlite_cursor.description]
    
    # Apply column mapping if provided
    if column_mapping:
        pg_columns = [column_mapping.get(col, col) for col in columns]
    else:
        pg_columns = columns
    
    # Prepare INSERT statement
    placeholders = ', '.join(['%s'] * len(pg_columns))
    insert_sql = f"INSERT INTO {table_name} ({', '.join(pg_columns)}) VALUES ({placeholders})"
    
    # Convert and insert data
    converted_rows = []
    for row in rows:
        converted_row = []
        for i, value in enumerate(row):
            # Convert SQLite data types to PostgreSQL compatible types
            if columns[i] in ['suspended', 'is_default'] and value is not None:
                # Convert integer boolean to actual boolean
                converted_row.append(bool(value))
            elif columns[i] in ['created_at', 'updated_at', 'expires_at', 'started_at', 'stopped_at', 'payment_date', 'datetime'] and value:
                # Convert timestamp strings to proper format
                try:
                    if isinstance(value, str):
                        # Try to parse the timestamp
                        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        converted_row.append(dt)
                    else:
                        converted_row.append(value)
                except:
                    converted_row.append(value)
            elif columns[i] == 'server_ip' and value:
                # Ensure IP address is properly formatted
                converted_row.append(str(value))
            else:
                converted_row.append(value)
        converted_rows.append(converted_row)
    
    try:
        pg_cursor.executemany(insert_sql, converted_rows)
        pg_conn.commit()
        print(f"  Migrated {len(converted_rows)} rows")
    except Exception as e:
        print(f"  Error migrating {table_name}: {e}")
        pg_conn.rollback()
        raise

def reset_sequences(pg_conn):
    """Reset PostgreSQL sequences to match the migrated data"""
    pg_cursor = pg_conn.cursor()
    
    tables_with_sequences = [
        'users', 'applications', 'auth_tokens', 'user_applications',
        'servers', 'deployments', 'application_costs', 'billing_activities',
        'users_logs', 'payment_modes', 'invoicing'
    ]
    
    for table in tables_with_sequences:
        try:
            # Get the maximum ID from the table
            pg_cursor.execute(f"SELECT COALESCE(MAX(id), 0) FROM {table}")
            max_id = pg_cursor.fetchone()[0]
            
            # Reset the sequence
            sequence_name = f"{table}_id_seq"
            pg_cursor.execute(f"SELECT setval('{sequence_name}', {max_id + 1})")
            print(f"  Reset sequence {sequence_name} to {max_id + 1}")
        except Exception as e:
            print(f"  Warning: Could not reset sequence for {table}: {e}")
    
    pg_conn.commit()

def main():
    """Main migration function"""
    print("AI-SwAutoMorph: SQLite to PostgreSQL Migration")
    print("=" * 50)
    
    # Paths
    sqlite_db_path = os.path.join(os.path.dirname(__file__), '..', 'softfluid', 'db', 'ai_swautomorph.db')
    
    # Connect to databases
    print("Connecting to databases...")
    sqlite_conn = connect_sqlite(sqlite_db_path)
    if not sqlite_conn:
        print("Failed to connect to SQLite database")
        return 1
    
    pg_conn = connect_postgresql()
    if not pg_conn:
        print("Failed to connect to PostgreSQL database")
        return 1
    
    print("Connected successfully to both databases")
    
    # Define migration order (respecting foreign key constraints)
    migration_order = [
        'users',
        'applications', 
        'auth_tokens',
        'user_applications',
        'servers',
        'deployments',
        'application_costs',
        'billing_activities',
        'users_logs',
        'payment_modes',
        'invoicing'
    ]
    
    # Column mappings for tables with renamed columns
    column_mappings = {
        'servers': {
            'SERVER_IP': 'server_ip',
            'SERVER_NAME': 'server_name',
            'SERVER_CAPACITY_USER_MAX': 'server_capacity_user_max',
            'SERVER_CAPACITY_APPLI_MAX': 'server_capacity_appli_max',
            'SERVER_STATUS': 'server_status',
            'SERVER_TYPE': 'server_type'
        }
    }
    
    try:
        # Clear existing data in PostgreSQL (in reverse order)
        print("\nClearing existing PostgreSQL data...")
        pg_cursor = pg_conn.cursor()
        for table in reversed(migration_order):
            pg_cursor.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")
        pg_conn.commit()
        print("Existing data cleared")
        
        # Migrate tables
        print("\nMigrating tables...")
        for table in migration_order:
            column_mapping = column_mappings.get(table)
            migrate_table(sqlite_conn, pg_conn, table, column_mapping)
        
        # Reset sequences
        print("\nResetting sequences...")
        reset_sequences(pg_conn)
        
        print("\n" + "=" * 50)
        print("Migration completed successfully!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\nMigration failed: {e}")
        return 1
    
    finally:
        sqlite_conn.close()
        pg_conn.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())