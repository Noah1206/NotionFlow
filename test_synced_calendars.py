#!/usr/bin/env python3
"""
Test script for the /api/synced-calendars endpoint
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from frontend.app import app
import json

def test_synced_calendars_endpoint():
    """Test the synced calendars endpoint"""
    with app.test_client() as client:
        # Test without authentication (should return 401)
        response = client.get('/api/synced-calendars')
        print(f"Without auth - Status: {response.status_code}")
        print(f"Without auth - Response: {response.get_json()}")
        
        # Test with session (simulating logged in user)
        with client.session_transaction() as sess:
            sess['user_id'] = 'test_user_123'
        
        response = client.get('/api/synced-calendars')
        print(f"With auth - Status: {response.status_code}")
        print(f"With auth - Response: {response.get_json()}")
        
        if response.status_code == 200:
            print("✅ Endpoint is working correctly!")
            return True
        else:
            print("❌ Endpoint returned an error")
            return False

if __name__ == '__main__':
    print("Testing /api/synced-calendars endpoint...")
    success = test_synced_calendars_endpoint()
    sys.exit(0 if success else 1)