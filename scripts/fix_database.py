#!/usr/bin/env python3
"""
SQLite Database Recovery Script for AI-SwAutoMorph
Fixes corrupted database using multiple recovery methods
"""

import sqlite3
import os
import shutil
from datetime import datetime

def backup_database(db_path):
    """Create backup of corrupted database"""
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_path, backup_path)
    print(f"Backup created: {backup_path}")
    return backup_path

def recover_with_dot_recover(db_path):
    """Use SQLite .recover command (most effective)"""
    recovered_path = f"{db_path}.recovered"
    
    try:
        # Use sqlite3 command line tool
        import subprocess
        result = subprocess.run([
            'sqlite3', db_path, 
            f'.recover | sqlite3 {recovered_path}'
        ], shell=True, capture_output=True, text=True)
        
        if result.returncode == 0 and os.path.exists(recovered_path):
            print("Recovery successful with .recover command")
            return recovered_path
    except Exception as e:
        print(f"Recovery failed: {e}")
    
    return None

def recover_with_dump(db_path):
    """Use .dump command as fallback"""
    dump_path = f"{db_path}.sql"
    recovered_path = f"{db_path}.recovered2"
    
    try:
        import subprocess
        
        # Dump readable data
        with open(dump_path, 'w') as f:
            result = subprocess.run([
                'sqlite3', db_path, '.dump'
            ], stdout=f, stderr=subprocess.PIPE, text=True)
        
        if os.path.exists(dump_path):
            # Recreate database from dump
            subprocess.run([
                'sqlite3', recovered_path, f'.read {dump_path}'
            ], check=True)
            
            print("Recovery successful with .dump method")
            return recovered_path
            
    except Exception as e:
        print(f"Dump recovery failed: {e}")
    
    return None

def main():
    db_path = "/home/ubuntu/ai-swautomorph/users.db"
    
    if not os.path.exists(db_path):
        print("Database file not found!")
        return
    
    print("Starting database recovery...")
    
    # 1. Create backup
    backup_path = backup_database(db_path)
    
    # 2. Try .recover method first
    recovered_db = recover_with_dot_recover(db_path)
    
    # 3. If that fails, try .dump method
    if not recovered_db:
        recovered_db = recover_with_dump(db_path)
    
    # 4. Replace original if recovery successful
    if recovered_db and os.path.exists(recovered_db):
        shutil.move(db_path, f"{db_path}.corrupted")
        shutil.move(recovered_db, db_path)
        print(f"Database recovered successfully!")
        print(f"Original corrupted file: {db_path}.corrupted")
    else:
        print("Recovery failed. You may need to reinitialize the database.")
        print("Run: python3 ./scripts/cli.py init-db")

if __name__ == "__main__":
    main()