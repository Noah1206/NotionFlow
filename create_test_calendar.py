#!/usr/bin/env python3
"""
Test calendar data creation script
"""

import os
import sys
from datetime import datetime
from supabase import create_client, Client

# Supabase credentials
SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://pzyyfhxftgkftqlxqxjd.supabase.co')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY')

if not SUPABASE_SERVICE_KEY:
    print("Error: SUPABASE_SERVICE_KEY environment variable not set")
    sys.exit(1)

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def create_test_calendars():
    """Create test calendars for testing"""
    
    test_user_id = "test-user-12345"
    
    test_calendars = [
        {
            "id": "cal-001",
            "name": "내 개인 캘린더",
            "color": "#3B82F6",
            "type": "custom",
            "description": "개인 일정 관리용 캘린더",
            "owner_id": test_user_id,
            "is_active": True,
            "public_access": False,
            "allow_editing": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        {
            "id": "cal-002", 
            "name": "업무 캘린더",
            "color": "#10B981",
            "type": "custom",
            "description": "업무 관련 일정",
            "owner_id": test_user_id,
            "is_active": True,
            "public_access": False,
            "allow_editing": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        {
            "id": "cal-003",
            "name": "공유 프로젝트",
            "color": "#F59E0B", 
            "type": "custom",
            "description": "팀 프로젝트 일정",
            "owner_id": test_user_id,
            "is_active": True,
            "public_access": True,
            "allow_editing": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    ]
    
    for calendar in test_calendars:
        try:
            print(f"Creating calendar: {calendar['name']}")
            result = supabase.table('calendars').insert(calendar).execute()
            print(f"✅ Calendar created: {result.data}")
        except Exception as e:
            print(f"❌ Error creating calendar {calendar['name']}: {e}")

def create_test_events():
    """Create test events for the calendars"""
    
    test_events = [
        {
            "id": "evt-001",
            "title": "팀 미팅",
            "description": "주간 팀 미팅",
            "start_datetime": "2025-09-01T10:00:00",
            "end_datetime": "2025-09-01T11:00:00", 
            "is_all_day": False,
            "calendar_id": "cal-001",
            "user_id": "test-user-12345",
            "category": "meeting",
            "priority": "high",
            "status": "confirmed",
            "source_platform": "custom",
            "location": "회의실 A",
            "attendees": ["user1@example.com", "user2@example.com"],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        {
            "id": "evt-002", 
            "title": "프로젝트 데드라인",
            "description": "프로젝트 최종 제출",
            "start_datetime": "2025-09-05T23:59:00",
            "end_datetime": "2025-09-05T23:59:00",
            "is_all_day": False,
            "calendar_id": "cal-002",
            "user_id": "test-user-12345", 
            "category": "work",
            "priority": "critical",
            "status": "confirmed",
            "source_platform": "custom",
            "location": "온라인",
            "attendees": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        {
            "id": "evt-003",
            "title": "점심 약속",
            "description": "친구와 점심",
            "start_datetime": "2025-09-02T12:00:00", 
            "end_datetime": "2025-09-02T13:30:00",
            "is_all_day": False,
            "calendar_id": "cal-003",
            "user_id": "test-user-12345",
            "category": "personal", 
            "priority": "normal",
            "status": "confirmed",
            "source_platform": "custom",
            "location": "레스토랑",
            "attendees": ["friend@example.com"],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    ]
    
    for event in test_events:
        try:
            print(f"Creating event: {event['title']}")
            result = supabase.table('calendar_events').insert(event).execute()
            print(f"✅ Event created: {result.data}")
        except Exception as e:
            print(f"❌ Error creating event {event['title']}: {e}")

if __name__ == "__main__":
    print("🚀 Creating test calendar data...")
    create_test_calendars()
    print("\n🎯 Creating test events...")  
    create_test_events()
    print("\n✅ Test data creation completed!")