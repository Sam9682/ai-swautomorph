"""Database health monitoring utilities"""
import sqlite3
import time
from .config import DB_PATH
from .database import db_manager

def check_database_health():
    """Check database health and return status"""
    try:
        # Test basic connectivity
        result = db_manager.execute_query('SELECT 1', fetch_one=True)
        if result and result[0] == 1:
            # Test table access
            tables = db_manager.execute_query(
                "SELECT name FROM sqlite_master WHERE type='table'",
                fetch_all=True
            )
            
            # Check WAL mode
            wal_mode = db_manager.execute_query('PRAGMA journal_mode', fetch_one=True)
            
            return {
                'status': 'healthy',
                'tables_count': len(tables),
                'journal_mode': wal_mode[0] if wal_mode else 'unknown',
                'timestamp': time.time()
            }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': time.time()
        }

def optimize_database():
    """Optimize database performance"""
    try:
        # Run VACUUM to optimize database
        with db_manager.get_db_connection() as conn:
            conn.execute('VACUUM')
            conn.execute('ANALYZE')
        return {'status': 'optimized', 'timestamp': time.time()}
    except Exception as e:
        return {'status': 'failed', 'error': str(e), 'timestamp': time.time()}

def get_database_stats():
    """Get database statistics"""
    try:
        stats = {}
        
        # Get table row counts
        tables = ['users', 'applications', 'deployments', 'auth_tokens', 'billing_activities']
        for table in tables:
            count = db_manager.execute_query(f'SELECT COUNT(*) FROM {table}', fetch_one=True)
            stats[f'{table}_count'] = count[0] if count else 0
        
        # Get database size
        size_result = db_manager.execute_query('PRAGMA page_count', fetch_one=True)
        page_size_result = db_manager.execute_query('PRAGMA page_size', fetch_one=True)
        
        if size_result and page_size_result:
            stats['database_size_bytes'] = size_result[0] * page_size_result[0]
        
        return stats
    except Exception as e:
        return {'error': str(e)}