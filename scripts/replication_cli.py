#!/usr/bin/env python3
"""
CLI tool for managing database replication
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database_postgres import db_manager
from src.replication_manager import REPLICATED_TABLES
import argparse

def check_sync_status():
    """Check replication sync status across servers"""
    print("\n=== Replication Status ===\n")
    
    # Get all peer servers
    servers = db_manager.execute_query(
        "SELECT server_ip, server_name, server_type, server_status FROM servers",
        fetch_all=True
    )
    
    print(f"Peer Servers: {len(servers)}")
    for server in servers:
        print(f"  - {server[1]} ({server[0]}) [{server[2]}] - {server[3]}")
    
    print(f"\nReplicated Tables: {', '.join(REPLICATED_TABLES)}")
    
    # Check record counts
    print("\n=== Record Counts ===")
    for table in REPLICATED_TABLES:
        try:
            result = db_manager.execute_query(f"SELECT COUNT(*) FROM {table}", fetch_one=True)
            print(f"  {table}: {result[0]} records")
        except Exception as e:
            print(f"  {table}: Error - {e}")

def manual_sync(table, server_ip):
    """Manually trigger sync for a specific table to a server"""
    if table not in REPLICATED_TABLES:
        print(f"Error: Table '{table}' is not configured for replication")
        print(f"Available tables: {', '.join(REPLICATED_TABLES)}")
        return
    
    print(f"\n=== Manual Sync: {table} -> {server_ip} ===\n")
    
    # Get all records from table
    try:
        records = db_manager.execute_query(f"SELECT * FROM {table}", fetch_all=True)
        print(f"Found {len(records)} records to sync")
        
        # Get column names
        columns = db_manager.execute_query(
            f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}' ORDER BY ordinal_position",
            fetch_all=True
        )
        col_names = [c[0] for c in columns]
        
        # Send each record
        import requests
        import urllib3
        import time
        from datetime import datetime
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        sync_secret = os.getenv('SYNC_SECRET', 'default-sync-secret-change-me')
        success_count = 0
        
        # Detect protocol
        protocol = 'https'
        try:
            requests.get(f"https://{server_ip}/api/sync/health", timeout=2, verify=False)
        except:
            protocol = 'http'
        
        for record in records:
            data = dict(zip(col_names, record))
            event = {
                'event_id': f"manual-{table}-{time.time()}",
                'timestamp': datetime.utcnow().isoformat(),
                'table': table,
                'operation': 'INSERT',
                'data': data,
                'primary_key': {'id': data.get('id')},
                'version': int(time.time() * 1000)
            }
            
            try:
                response = requests.post(
                    f"{protocol}://{server_ip}/api/sync/replicate",
                    json=event,
                    headers={'X-Sync-Token': sync_secret},
                    timeout=5,
                    verify=False
                )
                if response.status_code == 200:
                    success_count += 1
            except Exception as e:
                print(f"  Error syncing record {data.get('id')}: {e}")
        
        print(f"\nSync complete: {success_count}/{len(records)} records synced successfully")
        
    except Exception as e:
        print(f"Error: {e}")

def test_connectivity(server_ip):
    """Test connectivity to a peer server"""
    import requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    print(f"\n=== Testing Connectivity: {server_ip} ===\n")
    
    # Try HTTPS first, then HTTP
    for protocol in ['https', 'http']:
        try:
            url = f"{protocol}://{server_ip}/api/sync/health"
            print(f"Trying {protocol.upper()}...")
            
            response = requests.get(
                url,
                timeout=5,
                verify=False
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Server is reachable via {protocol.upper()}")
                print(f"  Status: {data.get('status')}")
                print(f"  Queue Size: {data.get('queue_size')}")
                print(f"  Timestamp: {data.get('timestamp')}")
                return
            else:
                print(f"  Server returned status {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"  Connection refused on {protocol.upper()}")
        except Exception as e:
            print(f"  Error: {e}")
    
    print(f"\n✗ Could not connect to {server_ip} on HTTPS or HTTP")
    print(f"  Possible issues:")
    print(f"  - Server is not running")
    print(f"  - Firewall blocking ports 80/443")
    print(f"  - Wrong IP address")

def main():
    parser = argparse.ArgumentParser(description='Database Replication Management')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Status command
    subparsers.add_parser('status', help='Check replication status')
    
    # Manual sync command
    sync_parser = subparsers.add_parser('sync', help='Manually sync table to server')
    sync_parser.add_argument('table', help='Table name to sync')
    sync_parser.add_argument('server_ip', help='Target server IP')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test connectivity to server')
    test_parser.add_argument('server_ip', help='Server IP to test')
    
    args = parser.parse_args()
    
    if args.command == 'status':
        check_sync_status()
    elif args.command == 'sync':
        manual_sync(args.table, args.server_ip)
    elif args.command == 'test':
        test_connectivity(args.server_ip)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
