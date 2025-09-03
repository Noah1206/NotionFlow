#!/usr/bin/env python3
"""
Test script to create a calendar with YouTube data
"""

import requests
import json

# Test data with YouTube information
test_data = {
    "name": "Test YouTube Calendar",
    "platform": "custom", 
    "color": "#FF0000",
    "is_shared": False,
    "youtube_data": {
        "video_id": "dQw4w9WgXcQ",
        "title": "Rick Astley - Never Gonna Give You Up (Official Music Video)",
        "channel_name": "Rick Astley",
        "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
        "duration_formatted": "3:33",
        "watch_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "embed_url": "https://www.youtube.com/embed/dQw4w9WgXcQ"
    }
}

def test_calendar_creation():
    """Test creating a calendar with YouTube data"""
    url = "http://127.0.0.1:5003/api/calendar/create"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print("🧪 Testing calendar creation with YouTube data...")
    print(f"📤 Sending to: {url}")
    print(f"📋 Data: {json.dumps(test_data, indent=2)}")
    
    try:
        response = requests.post(url, json=test_data, headers=headers)
        print(f"\n📨 Response Status: {response.status_code}")
        print(f"📨 Response Headers: {dict(response.headers)}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            result = response.json()
            print(f"📨 Response Data: {json.dumps(result, indent=2)}")
        else:
            print(f"📨 Response Text: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_calendar_creation()