#!/usr/bin/env python3
"""Test calendar creation and redirect functionality"""

import requests
import json

# Base URL
BASE_URL = "http://localhost:5003"

def test_calendar_creation():
    """Test creating a calendar via API"""
    
    # Test data
    calendar_data = {
        "name": "테스트 캘린더",
        "platform": "custom",
        "color": "#2563eb",
        "is_shared": False
    }
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    # First, we need to simulate a logged-in user
    # For testing, we'll directly call the API endpoint
    print("Creating test calendar...")
    
    try:
        response = session.post(
            f"{BASE_URL}/api/calendar/simple-create",
            json=calendar_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                calendar_id = result['calendar']['id']
                print(f"✅ Calendar created successfully with ID: {calendar_id}")
                print(f"📍 Redirect URL would be: /dashboard/calendar/{calendar_id}")
                return calendar_id
            else:
                print(f"❌ Failed: {result.get('error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return None

if __name__ == "__main__":
    test_calendar_creation()