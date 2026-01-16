"""Light Orchestrator for multi-instance application management"""
# import sqlite3  # COMMENTED OUT - Using PostgreSQL now
import threading
import time
import json
import subprocess
import requests
from contextlib import contextmanager
from .database_postgres import db_manager

class LightOrchestrator:
    """Simple orchestrator for managing multi-instance applications"""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._reconcile_thread = None
        self._running = False
    
    def init_orchestrator_tables(self):
        """Initialize orchestrator-specific tables (now handled by postgresql_schema.sql)"""
        # Tables are now created via postgresql_schema.sql
        # This method kept for backward compatibility
        pass
    
    def create_service(self, name, image, desired_replicas=1, ports=None, environment=None, volumes=None, health_check_path='/health'):
        """Create a new service"""
        print(f"[ORCHESTRATOR DEBUG] Creating service {name} with {desired_replicas} replicas")
        
        ports_json = json.dumps(ports) if ports else None
        env_json = json.dumps(environment) if environment else None
        volumes_json = json.dumps(volumes) if volumes else None
        
        with db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO services 
                (name, image, desired_replicas, ports, environment, volumes, health_check_path, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (name) DO UPDATE SET
                image = EXCLUDED.image,
                desired_replicas = EXCLUDED.desired_replicas,
                ports = EXCLUDED.ports,
                environment = EXCLUDED.environment,
                volumes = EXCLUDED.volumes,
                health_check_path = EXCLUDED.health_check_path,
                updated_at = CURRENT_TIMESTAMP
            ''', (name, image, desired_replicas, ports_json, env_json, volumes_json, health_check_path))
            conn.commit()
            print(f"[ORCHESTRATOR DEBUG] Service {name} created in database")
        
        # Trigger reconciliation
        try:
            self._reconcile_service(name)
            print(f"[ORCHESTRATOR DEBUG] Reconciliation triggered for {name}")
        except Exception as e:
            print(f"[ORCHESTRATOR ERROR] Reconciliation failed for {name}: {e}")
    
    def scale_service(self, service_name, replicas):
        """Scale a service to desired number of replicas"""
        with db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE services SET desired_replicas = %s, updated_at = CURRENT_TIMESTAMP 
                WHERE name = %s
            ''', (replicas, service_name))
            conn.commit()
        
        self._reconcile_service(service_name)
    
    def delete_service(self, service_name):
        """Delete a service and all its instances"""
        # Stop all instances first
        self._stop_all_instances(service_name)
        
        with db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM instances WHERE service_name = %s', (service_name,))
            cursor.execute('DELETE FROM services WHERE name = %s', (service_name,))
            conn.commit()
    
    def get_service_status(self, service_name=None):
        """Get status of services and their instances"""
        with db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            
            if service_name:
                cursor.execute('SELECT * FROM services WHERE name = %s', (service_name,))
                services = cursor.fetchall()
            else:
                cursor.execute('SELECT * FROM services')
                services = cursor.fetchall()
            
            result = []
            for service in services:
                service_data = {
                    'name': service[1],
                    'image': service[2],
                    'desired_replicas': service[3],
                    'ports': json.loads(service[4]) if service[4] else {},
                    'instances': []
                }
                
                # Get instances for this service
                cursor.execute('''
                    SELECT i.*, s.server_name, s.server_ip 
                    FROM instances i 
                    JOIN servers s ON i.server_id = s.id 
                    WHERE i.service_name = %s
                ''', (service[1],))
                instances = cursor.fetchall()
                
                for instance in instances:
                    service_data['instances'].append({
                        'instance_id': instance[2],
                        'server_name': instance[11],
                        'server_ip': instance[12],
                        'container_id': instance[4],
                        'status': instance[5],
                        'port': instance[6],
                        'health_status': instance[7]
                    })
                
                result.append(service_data)
            
            return result
    
    def _reconcile_service(self, service_name):
        """Reconcile desired vs actual state for a service"""
        with self._lock:
            with db_manager.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Get service configuration
                cursor.execute('SELECT * FROM services WHERE name = %s', (service_name,))
                service = cursor.fetchone()
                if not service:
                    return
                
                desired_replicas = service[3]
                
                # Get current running instances
                cursor.execute('''
                    SELECT * FROM instances 
                    WHERE service_name = %s AND status IN ('running', 'pending')
                ''', (service_name,))
                current_instances = cursor.fetchall()
                
                current_count = len(current_instances)
                
                if current_count < desired_replicas:
                    # Need to create more instances
                    for i in range(current_count, desired_replicas):
                        self._create_instance(service, i + 1)
                elif current_count > desired_replicas:
                    # Need to remove instances
                    instances_to_remove = current_instances[desired_replicas:]
                    for instance in instances_to_remove:
                        self._stop_instance(instance[0])  # instance id
    
    def _create_instance(self, service, replica_num):
        """Create a new instance of a service"""
        service_name = service[1]
        image = service[2]
        ports = json.loads(service[4]) if service[4] else {}
        environment = json.loads(service[5]) if service[5] else {}
        volumes = json.loads(service[6]) if service[6] else []
        
        print(f"[ORCHESTRATOR DEBUG] Creating instance for service {service_name}")
        
        # Select best server using simple scheduler
        server_id = self._select_server()
        if not server_id:
            print(f"[ORCHESTRATOR ERROR] No available server for {service_name}")
            return
        
        print(f"[ORCHESTRATOR DEBUG] Selected server {server_id} for {service_name}")
        
        instance_id = f"{service_name}-replica-{replica_num}"
        
        # Find available port
        port = self._find_available_port(server_id)
        print(f"[ORCHESTRATOR DEBUG] Assigned port {port} to {instance_id}")
        
        # Create instance record
        with db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO instances 
                (service_name, instance_id, server_id, status, port)
                VALUES (%s, %s, %s, 'pending', %s) RETURNING id
            ''', (service_name, instance_id, server_id, port))
            db_instance_id = cursor.fetchone()[0]
            conn.commit()
            print(f"[ORCHESTRATOR DEBUG] Created instance record {db_instance_id}")
        
        # Start container
        try:
            container_id = self._start_container(
                server_id, instance_id, image, port, ports, environment, volumes
            )
            
            print(f"[ORCHESTRATOR DEBUG] Started container {container_id} for {instance_id}")
            
            # Update instance with container ID
            with db_manager.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE instances 
                    SET container_id = %s, status = 'running', updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                ''', (container_id, db_instance_id))
                conn.commit()
                
        except Exception as e:
            print(f"[ORCHESTRATOR ERROR] Failed to start instance {instance_id}: {e}")
            # Mark as failed
            with db_manager.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE instances 
                    SET status = 'failed', updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                ''', (db_instance_id,))
                conn.commit()
    
    def _start_container(self, server_id, instance_id, image, port, ports, environment, volumes):
        """Start a Docker container"""
        # Get server info
        with db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT server_ip FROM servers WHERE id = %s', (server_id,))
            server_ip = cursor.fetchone()[0]
        
        # Build docker run command
        cmd = ['docker', 'run', '-d', '--name', instance_id]
        
        # Add port mappings
        if ports:
            for container_port, host_port in ports.items():
                cmd.extend(['-p', f'{port}:{container_port}'])
        
        # Add environment variables
        if environment:
            for key, value in environment.items():
                cmd.extend(['-e', f'{key}={value}'])
        
        # Add volumes
        if volumes:
            for volume in volumes:
                cmd.extend(['-v', volume])
        
        # Add restart policy
        cmd.extend(['--restart', 'unless-stopped'])
        
        # Add image
        cmd.append(image)
        
        # Execute command (locally for now, could be extended for remote servers)
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Docker run failed: {result.stderr}")
        
        return result.stdout.strip()
    
    def _stop_instance(self, instance_db_id):
        """Stop and remove an instance"""
        with db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT container_id, instance_id FROM instances WHERE id = %s', (instance_db_id,))
            instance = cursor.fetchone()
            
            if instance and instance[0]:  # has container_id
                container_id = instance[0]
                instance_id = instance[1]
                
                try:
                    # Stop and remove container
                    subprocess.run(['docker', 'stop', container_id], check=True)
                    subprocess.run(['docker', 'rm', container_id], check=True)
                except subprocess.CalledProcessError as e:
                    print(f"Failed to stop container {container_id}: {e}")
            
            # Remove instance record
            cursor.execute('DELETE FROM instances WHERE id = %s', (instance_db_id,))
            conn.commit()
    
    def _stop_all_instances(self, service_name):
        """Stop all instances of a service"""
        with db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM instances WHERE service_name = %s', (service_name,))
            instances = cursor.fetchall()
            
            for instance in instances:
                self._stop_instance(instance[0])
    
    def _select_server(self):
        """Simple scheduler - select server with least instances"""
        with db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Debug: Check all servers
            cursor.execute('SELECT id, server_name, server_status, server_capacity_appli_max FROM servers')
            all_servers = cursor.fetchall()
            print(f"[ORCHESTRATOR DEBUG] All servers: {all_servers}")
            
            cursor.execute('''
                SELECT s.id, s.server_capacity_appli_max, COUNT(i.id) as current_instances
                FROM servers s
                LEFT JOIN instances i ON s.id = i.server_id AND i.status = 'running'
                WHERE s.server_status IN ('STAND_BY', 'ACTIVE')
                GROUP BY s.id
                HAVING current_instances < s.server_capacity_appli_max
                ORDER BY current_instances ASC
                LIMIT 1
            ''')
            result = cursor.fetchone()
            print(f"[ORCHESTRATOR DEBUG] Selected server query result: {result}")
            return result[0] if result else None
    
    def _find_available_port(self, server_id, start_port=8000):
        """Find an available port on a server"""
        with db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT port FROM instances 
                WHERE server_id = %s AND status = 'running'
                ORDER BY port
            ''', (server_id,))
            used_ports = {row[0] for row in cursor.fetchall()}
        
        port = start_port
        while port in used_ports:
            port += 1
        return port
    
    def health_check_instances(self):
        """Check health of all running instances"""
        with db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT i.id, i.instance_id, i.port, s.health_check_path, srv.server_ip
                FROM instances i
                JOIN services s ON i.service_name = s.name
                JOIN servers srv ON i.server_id = srv.id
                WHERE i.status = 'running'
            ''')
            instances = cursor.fetchall()
            
            for instance in instances:
                instance_id, name, port, health_path, server_ip = instance
                
                try:
                    # Health check via HTTP
                    url = f"http://{server_ip}:{port}{health_path}"
                    response = requests.get(url, timeout=5)
                    
                    if response.status_code == 200:
                        health_status = 'healthy'
                    else:
                        health_status = 'unhealthy'
                        
                except Exception:
                    health_status = 'unhealthy'
                
                # Update health status
                cursor.execute('''
                    UPDATE instances 
                    SET health_status = %s, last_health_check = CURRENT_TIMESTAMP
                    WHERE id = %s
                ''', (health_status, instance_id))
            
            conn.commit()
    
    def generate_nginx_config(self):
        """Generate Nginx upstream configuration for all services"""
        config_lines = []
        
        with db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT service_name FROM instances WHERE status = %s', ('running',))
            services = cursor.fetchall()
            
            for service in services:
                service_name = service[0]
                
                # Get healthy instances
                cursor.execute('''
                    SELECT srv.server_ip, i.port
                    FROM instances i
                    JOIN servers srv ON i.server_id = srv.id
                    WHERE i.service_name = %s AND i.status = 'running' 
                    AND (i.health_status = 'healthy' OR i.health_status = 'unknown')
                ''', (service_name,))
                instances = cursor.fetchall()
                
                if instances:
                    config_lines.append(f"upstream {service_name} {{")
                    config_lines.append("    least_conn;")
                    
                    for instance in instances:
                        server_ip, port = instance
                        config_lines.append(f"    server {server_ip}:{port};")
                    
                    config_lines.append("}")
                    config_lines.append("")
        
        return "\n".join(config_lines)
    
    def reload_nginx(self):
        """Reload Nginx configuration"""
        try:
            subprocess.run(['nginx', '-s', 'reload'], check=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def start_reconciliation_loop(self, interval=30):
        """Start background reconciliation loop"""
        if self._running:
            return
        
        self._running = True
        
        def reconcile_loop():
            while self._running:
                try:
                    # Health check all instances
                    self.health_check_instances()
                    
                    # Reconcile all services
                    with db_manager.get_db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute('SELECT name FROM services')
                        services = cursor.fetchall()
                        
                        for service in services:
                            self._reconcile_service(service[0])
                    
                    # Update Nginx config if needed
                    self.generate_nginx_config()
                    
                except Exception as e:
                    print(f"Reconciliation error: {e}")
                
                time.sleep(interval)
        
        self._reconcile_thread = threading.Thread(target=reconcile_loop, daemon=True)
        self._reconcile_thread.start()
    
    def stop_reconciliation_loop(self):
        """Stop background reconciliation loop"""
        self._running = False
        if self._reconcile_thread:
            self._reconcile_thread.join()

# Global orchestrator instance
orchestrator = LightOrchestrator()