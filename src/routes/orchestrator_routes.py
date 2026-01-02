"""API routes for Light Orchestrator"""
from flask import Blueprint, request, jsonify, session
from ..database import db_manager
import json

orchestrator_bp = Blueprint('orchestrator', __name__, url_prefix='/api/orchestrator')

def require_auth():
    """Check if user is authenticated"""
    if 'user_id' not in session:
        return False
    return True

def require_admin():
    """Check if user is admin"""
    if not require_auth():
        return False
    
    user = db_manager.execute_query(
        'SELECT username FROM users WHERE id = ?', 
        (session['user_id'],), fetch_one=True
    )
    
    return user and user[0] == 'admin'

@orchestrator_bp.route('/services', methods=['GET'])
def list_services():
    """List all services and their status"""
    if not require_auth():
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        from ..orchestrator import orchestrator
        services = orchestrator.get_service_status()
        return jsonify(services)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestrator_bp.route('/services/<service_name>', methods=['GET'])
def get_service(service_name):
    """Get specific service status"""
    if not require_auth():
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        from ..orchestrator import orchestrator
        services = orchestrator.get_service_status(service_name)
        if not services:
            return jsonify({'error': 'Service not found'}), 404
        return jsonify(services[0])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestrator_bp.route('/services', methods=['POST'])
def create_service():
    """Create a new service"""
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        from ..orchestrator import orchestrator
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'image']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Extract parameters
        name = data['name']
        image = data['image']
        desired_replicas = data.get('desired_replicas', 1)
        ports = data.get('ports', {})
        environment = data.get('environment', {})
        volumes = data.get('volumes', [])
        health_check_path = data.get('health_check_path', '/health')
        
        # Create service
        orchestrator.create_service(
            name=name,
            image=image,
            desired_replicas=desired_replicas,
            ports=ports,
            environment=environment,
            volumes=volumes,
            health_check_path=health_check_path
        )
        
        return jsonify({'message': f'Service {name} created successfully'}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestrator_bp.route('/services/<service_name>', methods=['PUT'])
def update_service(service_name):
    """Update service configuration"""
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        from ..orchestrator import orchestrator
        data = request.get_json()
        
        # For now, only support scaling
        if 'desired_replicas' in data:
            replicas = data['desired_replicas']
            if not isinstance(replicas, int) or replicas < 0:
                return jsonify({'error': 'desired_replicas must be a non-negative integer'}), 400
            
            orchestrator.scale_service(service_name, replicas)
            return jsonify({'message': f'Service {service_name} scaled to {replicas} replicas'})
        
        return jsonify({'error': 'No valid update parameters provided'}), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestrator_bp.route('/services/<service_name>/scale', methods=['POST'])
def scale_service(service_name):
    """Scale a service"""
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        from ..orchestrator import orchestrator
        data = request.get_json()
        replicas = data.get('replicas')
        
        if replicas is None:
            return jsonify({'error': 'Missing replicas parameter'}), 400
        
        if not isinstance(replicas, int) or replicas < 0:
            return jsonify({'error': 'replicas must be a non-negative integer'}), 400
        
        orchestrator.scale_service(service_name, replicas)
        return jsonify({'message': f'Service {service_name} scaled to {replicas} replicas'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestrator_bp.route('/services/<service_name>', methods=['DELETE'])
def delete_service(service_name):
    """Delete a service and all its instances"""
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        from ..orchestrator import orchestrator
        orchestrator.delete_service(service_name)
        return jsonify({'message': f'Service {service_name} deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestrator_bp.route('/health-check', methods=['POST'])
def trigger_health_check():
    """Manually trigger health check for all instances"""
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        from ..orchestrator import orchestrator
        orchestrator.health_check_instances()
        return jsonify({'message': 'Health check completed'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestrator_bp.route('/nginx/config', methods=['GET'])
def get_nginx_config():
    """Get generated Nginx upstream configuration"""
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        from ..orchestrator import orchestrator
        config = orchestrator.generate_nginx_config()
        return jsonify({'config': config})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestrator_bp.route('/nginx/reload', methods=['POST'])
def reload_nginx():
    """Reload Nginx configuration"""
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        from ..orchestrator import orchestrator
        success = orchestrator.reload_nginx()
        if success:
            return jsonify({'message': 'Nginx reloaded successfully'})
        else:
            return jsonify({'error': 'Failed to reload Nginx'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestrator_bp.route('/reconcile', methods=['POST'])
def trigger_reconciliation():
    """Manually trigger reconciliation for all services"""
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        from ..orchestrator import orchestrator
        
        with db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM services')
            services = cursor.fetchall()
            
            for service in services:
                orchestrator._reconcile_service(service[0])
        
        return jsonify({'message': 'Reconciliation completed'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestrator_bp.route('/status', methods=['GET'])
def orchestrator_status():
    """Get orchestrator status and statistics"""
    if not require_auth():
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        with db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Count services
            cursor.execute('SELECT COUNT(*) FROM services')
            total_services = cursor.fetchone()[0]
            
            # Count instances by status
            cursor.execute('''
                SELECT status, COUNT(*) 
                FROM instances 
                GROUP BY status
            ''')
            instance_stats = dict(cursor.fetchall())
            
            # Count healthy vs unhealthy instances
            cursor.execute('''
                SELECT health_status, COUNT(*) 
                FROM instances 
                WHERE status = 'running'
                GROUP BY health_status
            ''')
            health_stats = dict(cursor.fetchall())
            
            # Server utilization
            cursor.execute('''
                SELECT s.SERVER_NAME, s.SERVER_CAPACITY_APPLI_MAX, COUNT(i.id) as current_instances
                FROM servers s
                LEFT JOIN instances i ON s.id = i.server_id AND i.status = 'running'
                GROUP BY s.id, s.SERVER_NAME, s.SERVER_CAPACITY_APPLI_MAX
            ''')
            server_stats = []
            for row in cursor.fetchall():
                server_stats.append({
                    'name': row[0],
                    'capacity': row[1],
                    'current_instances': row[2],
                    'utilization': round((row[2] / row[1]) * 100, 2) if row[1] > 0 else 0
                })
        
        from ..orchestrator import orchestrator
        return jsonify({
            'total_services': total_services,
            'instance_stats': instance_stats,
            'health_stats': health_stats,
            'server_stats': server_stats,
            'reconciliation_running': orchestrator._running
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500