#!/usr/bin/env python3
"""
Test script for deployment functionality
"""
import requests
import json
import time

BASE_URL = 'http://localhost:5002'

def test_deployment():
    # First, login as admin
    login_data = {
        'username': 'admin',
        'password': 'password'
    }
    
    session = requests.Session()
    
    # Login
    response = session.post(f'{BASE_URL}/login', json=login_data)
    if response.status_code != 200:
        print(f"Login failed: {response.text}")
        return
    
    print("✅ Login successful")
    
    # Test clone deployment
    deployment_data = {
        'action': 'clone',
        'application_name': 'AI HACCP',
        'git_url': 'https://github.com/Sam9682/ai-haccp.git'
    }
    
    response = session.post(f'{BASE_URL}/api/deployments', json=deployment_data)
    if response.status_code == 202:
        print("✅ Clone deployment started")
        deployment_id = response.json().get('deployment_id')
        
        # Wait a bit and check status
        time.sleep(3)
        
        # Get deployments
        response = session.get(f'{BASE_URL}/api/deployments')
        if response.status_code == 200:
            deployments = response.json()
            print(f"📊 Found {len(deployments)} deployments")
            for dep in deployments:
                print(f"   - {dep['application_name']}: {dep['status']}")
        
    else:
        print(f"❌ Clone deployment failed: {response.text}")
    
    # Test other deployment commands
    for action in ['status', 'start', 'stop']:
        deployment_data = {
            'action': action,
            'application_name': 'AI HACCP'
        }
        
        response = session.post(f'{BASE_URL}/api/deployments', json=deployment_data)
        if response.status_code == 202:
            print(f"✅ {action.capitalize()} command started")
        else:
            print(f"❌ {action.capitalize()} command failed: {response.text}")

if __name__ == '__main__':
    test_deployment()