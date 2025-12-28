"""Billing management routes"""
from flask import Blueprint, request, jsonify, session
import sqlite3
import logging
import os
from datetime import datetime, timedelta
from ..config import DB_PATH, get_logs_dir
from ..database import db_manager

# Configure logging for billing activities
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(get_logs_dir(), 'billing_activities.log')),
        logging.StreamHandler()
    ]
)

billing_bp = Blueprint('billing', __name__)

@billing_bp.route('/api/billing/activities')
def get_billing_activities():
    """Get billing activities based on user role"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Check if user is admin
    user = db_manager.execute_query(
        'SELECT username FROM users WHERE id = ?', 
        (session['user_id'],), fetch_one=True
    )
    is_admin = user and user[0] == 'admin'
    
    if is_admin:
        # Admin sees all activities
        activities = db_manager.execute_query('''
            SELECT ba.id, u.username, a.name, ba.action, ba.started_at, ba.stopped_at, 
                   ba.duration_seconds, ba.cost_amount, ba.created_at
            FROM billing_activities ba
            JOIN users u ON ba.user_id = u.id
            JOIN applications a ON ba.application_id = a.id
            ORDER BY ba.created_at DESC
        ''', fetch_all=True)
    else:
        # Regular user sees only their activities
        activities = db_manager.execute_query('''
            SELECT ba.id, u.username, a.name, ba.action, ba.started_at, ba.stopped_at, 
                   ba.duration_seconds, ba.cost_amount, ba.created_at
            FROM billing_activities ba
            JOIN users u ON ba.user_id = u.id
            JOIN applications a ON ba.application_id = a.id
            WHERE ba.user_id = ?
            ORDER BY ba.created_at DESC
        ''', (session['user_id'],), fetch_all=True)
    
    return jsonify([{
        'id': row[0],
        'username': row[1],
        'application': row[2],
        'action': row[3],
        'started_at': row[4],
        'stopped_at': row[5],
        'duration_seconds': row[6],
        'cost_amount': row[7],
        'created_at': row[8]
    } for row in activities])

@billing_bp.route('/api/billing/summary')
def get_billing_summary():
    """Get billing summary by period"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    period = request.args.get('period', 'month')  # day, week, month
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if user is admin
    cursor.execute('SELECT username FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    is_admin = user and user[0] == 'admin'
    
    # Calculate date range
    now = datetime.now()
    if period == 'day':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == 'week':
        start_date = now - timedelta(days=now.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    else:  # month
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    if is_admin:
        # Admin sees all users' summary
        cursor.execute('''
            SELECT u.username, a.name, SUM(ba.duration_seconds), SUM(ba.cost_amount)
            FROM billing_activities ba
            JOIN users u ON ba.user_id = u.id
            JOIN applications a ON ba.application_id = a.id
            WHERE ba.created_at >= ?
            GROUP BY u.username, a.name
            ORDER BY u.username, a.name
        ''', (start_date.isoformat(),))
    else:
        # Regular user sees only their summary
        cursor.execute('''
            SELECT u.username, a.name, SUM(ba.duration_seconds), SUM(ba.cost_amount)
            FROM billing_activities ba
            JOIN users u ON ba.user_id = u.id
            JOIN applications a ON ba.application_id = a.id
            WHERE ba.user_id = ? AND ba.created_at >= ?
            GROUP BY u.username, a.name
            ORDER BY a.name
        ''', (session['user_id'], start_date.isoformat()))
    
    summary = cursor.fetchall()
    conn.close()
    
    return jsonify([{
        'username': row[0],
        'application': row[1],
        'total_duration_seconds': row[2] or 0,
        'total_cost': row[3] or 0.0
    } for row in summary])

@billing_bp.route('/api/billing/costs')
def get_application_costs():
    """Get application costs (admin only)"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if user is admin
    cursor.execute('SELECT username FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    if not user or user[0] != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    cursor.execute('''
        SELECT a.id, a.name, ac.cost_per_day, ac.updated_at
        FROM applications a
        LEFT JOIN application_costs ac ON a.id = ac.application_id
        ORDER BY a.name
    ''')
    
    costs = cursor.fetchall()
    conn.close()
    
    return jsonify([{
        'application_id': row[0],
        'application_name': row[1],
        'cost_per_day': row[2] or 1.0,
        'updated_at': row[3]
    } for row in costs])

@billing_bp.route('/api/billing/costs/<int:app_id>', methods=['PUT'])
def update_application_cost(app_id):
    """Update application cost (admin only)"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if user is admin
    cursor.execute('SELECT username FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    if not user or user[0] != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.get_json()
    cost_per_day = data.get('cost_per_day', 1.0)
    
    # Update or insert cost
    cursor.execute('SELECT COUNT(*) FROM application_costs WHERE application_id = ?', (app_id,))
    if cursor.fetchone()[0] > 0:
        cursor.execute('''
            UPDATE application_costs 
            SET cost_per_day = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE application_id = ?
        ''', (cost_per_day, app_id))
    else:
        cursor.execute('''
            INSERT INTO application_costs (application_id, cost_per_day) 
            VALUES (?, ?)
        ''', (app_id, cost_per_day))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Cost updated successfully'})

def record_billing_activity(user_id, application_name, action):
    """Record billing activity for application start/stop"""
    logger = logging.getLogger('billing_activities')
    
    try:
        logger.info(f"Recording billing activity: user_id={user_id}, app={application_name}, action={action}")
        
        # Get application ID
        app_result = db_manager.execute_query(
            'SELECT id FROM applications WHERE name = ?', 
            (application_name,), fetch_one=True
        )
        if not app_result:
            logger.error(f"record_billing_activity(): Application not found: {application_name}")
            return False
        
        application_id = app_result[0]
        logger.debug(f"record_billing_activity(): Found application_id: {application_id}")
        
        if action.upper() == 'START':
            # Record start activity
            result = db_manager.execute_query('''
                INSERT INTO billing_activities (user_id, application_id, action, started_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, application_id, action))
            
            if result is not None:
                logger.info(f"record_billing_activity(): Successfully recorded start activity for {application_name}")
                return True
            else:
                logger.error(f"record_billing_activity(): Failed to record start activity for {application_name}")
                return False
        
        elif action.upper()  == 'STOP':
            # Find the most recent start activity for this user and app
            start_activity = db_manager.execute_query('''
                SELECT id, started_at FROM billing_activities
                WHERE user_id = ? AND application_id = ? AND action = 'start' AND stopped_at IS NULL
                ORDER BY created_at DESC LIMIT 1
            ''', (user_id, application_id), fetch_one=True)
            
            if start_activity:
                start_id, started_at = start_activity
                logger.debug(f"record_billing_activity(): Found matching start activity: {start_id}")
                
                # Calculate duration and cost
                start_time = datetime.fromisoformat(started_at)
                stop_time = datetime.now()
                duration_seconds = int((stop_time - start_time).total_seconds())
                
                # Get cost per day for this application
                cost_result = db_manager.execute_query(
                    'SELECT cost_per_day FROM application_costs WHERE application_id = ?', 
                    (application_id,), fetch_one=True
                )
                cost_per_day = cost_result[0] if cost_result else 1.0
                
                # Calculate cost (cost per day / 86400 seconds * duration)
                cost_amount = (cost_per_day / 86400) * duration_seconds
                
                logger.info(f"Calculated billing: duration={duration_seconds}s, cost=${cost_amount:.4f}")
                
                # Update the start activity with stop information
                update_result = db_manager.execute_query('''
                    UPDATE billing_activities 
                    SET stopped_at = CURRENT_TIMESTAMP, duration_seconds = ?, cost_amount = ?
                    WHERE id = ?
                ''', (duration_seconds, cost_amount, start_id))
                
                if update_result is None:
                    logger.error(f"record_billing_activity(): Failed to update START activity {start_id} with STOP information")
            else:
                logger.warning(f"record_billing_activity(): No matching START activity found for STOP action: {application_name}")
            
            # Also record the stop activity
            result = db_manager.execute_query('''
                INSERT INTO billing_activities (user_id, application_id, action, stopped_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, application_id, action))
            
            if result is not None:
                logger.info(f"record_billing_activity(): Successfully recorded STOP activity for {application_name}")
                return True
            else:
                logger.error(f"record_billing_activity(): Failed to record STOP activity for {application_name}")
                return False
        
        else:
            logger.warning(f"record_billing_activity(): Unknown action: {action}")
            return False
            
    except Exception as e:
        logger.error(f"record_billing_activity(): Error recording billing activity: {str(e)}")
        return False