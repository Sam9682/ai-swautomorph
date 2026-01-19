#!/usr/bin/env python3
"""CLI tool for multi-platform SwAutoMorph management"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database_postgres import db_manager
from src.platform_discovery import get_current_server_ip, check_remote_platform, determine_role, update_server_role

def show_platform_status():
    """Show current platform status"""
    current_ip = get_current_server_ip()
    server = db_manager.execute_query(
        'SELECT server_type, server_name FROM servers WHERE server_ip = %s',
        (current_ip,), fetch_one=True
    )
    
    if server:
        print(f"Platform Role: {server[0]}")
        print(f"Server Name: {server[1]}")
        print(f"Server IP: {current_ip}")
    else:
        print("Server not registered in database")
    
    # List all servers
    servers = db_manager.execute_query(
        'SELECT server_ip, server_name, server_type, server_status FROM servers ORDER BY id',
        fetch_all=True
    )
    
    print("\nAll Servers:")
    for s in servers:
        print(f"  - {s[1]} ({s[0]}): {s[2]} [{s[3]}]")

def discover_server(remote_ip):
    """Discover remote SwAutoMorph server"""
    print(f"Checking {remote_ip} for SwAutoMorph...")
    
    remote_status = check_remote_platform(remote_ip)
    
    if remote_status:
        print(f"✓ SwAutoMorph found!")
        print(f"  Role: {remote_status.get('role')}")
        print(f"  Version: {remote_status.get('version')}")
        print(f"  Server: {remote_status.get('server_name')}")
        
        current_ip = get_current_server_ip()
        our_role = determine_role(current_ip, remote_ip, remote_status, db_manager)
        
        print(f"\nRole determination:")
        print(f"  Current server will be: {our_role}")
        print(f"  Remote server is: {remote_status.get('role')}")
        
        # Update our role
        update_server_role(current_ip, our_role, db_manager)
        print(f"\n✓ Local server role updated to {our_role}")
    else:
        print("✗ No SwAutoMorph detected at this IP")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  platform_cli.py status              - Show platform status")
        print("  platform_cli.py discover <ip>       - Discover remote server")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'status':
        show_platform_status()
    elif command == 'discover' and len(sys.argv) == 3:
        discover_server(sys.argv[2])
    else:
        print("Invalid command")
        sys.exit(1)
