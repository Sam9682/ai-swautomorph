#!/usr/bin/env python3
"""API Testing Script for AI-SwAutoMorph"""

import requests
import json

BASE_URL = 'http://www.swautomorph.com:5000'

def test_registration():
    """Test user registration"""
    print("Testing user registration...")
    data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpass123',
        'first_name': 'Test',
        'last_name': 'User'
    }
    
    response = requests.post(f'{BASE_URL}/register', json=data)
    print(f"Registration: {response.status_code} - {response.text}")
    return response.status_code in [201, 409]  # 409 if user already exists

def test_login():
    """Test user login"""
    print("Testing user login...")
    data = {
        'username': 'testuser',
        'password': 'testpass123'
    }
    
    session = requests.Session()
    response = session.post(f'{BASE_URL}/login', json=data)
    print(f"Login: {response.status_code} - {response.text}")
    return session if response.status_code == 200 else None

def test_applications(session=None):
    """Test applications API"""
    print("Testing applications API...")
    
    # List applications
    response = requests.get(f'{BASE_URL}/api/applications')
    print(f"List apps: {response.status_code}")
    if response.status_code == 200:
        apps = response.json()
        print(f"Found {len(apps)} applications")
        for app in apps:
            print(f"  - {app['name']}: {app['url']}")
    
    # Add application (requires authentication)
    if session:
        new_app = {
            'name': 'Test Application',
            'url': 'http://test-app.swautomorph.com',
            'description': 'Test application for API testing'
        }
        response = session.post(f'{BASE_URL}/api/applications', json=new_app)
        print(f"Add app: {response.status_code} - {response.text}")

def test_auth_status():
    """Test authentication status"""
    print("Testing auth status...")
    response = requests.get(f'{BASE_URL}/api/auth/status')
    print(f"Auth status: {response.status_code} - {response.text}")

def main():
    """Run all API tests"""
    print("🧪 Starting API Tests for AI-SwAutoMorph\n")
    
    try:
        # Test registration
        test_registration()
        print()
        
        # Test login
        session = test_login()
        print()
        
        # Test applications
        test_applications(session)
        print()
        
        # Test auth status
        test_auth_status()
        print()
        
        print("✅ API tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to server. Make sure the application is running on http://www.swautomorph.com:5000")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == '__main__':
    main()