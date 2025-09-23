#!/usr/bin/env python3
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

def get_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_API_KEY")
    if not url or not key:
        raise ValueError("Supabase credentials not found")
    return create_client(url, key)

def check_events_distribution():
    supabase = get_supabase()
    user_id = '87875eda-6797-f839-f8c7-0aa90efb1352'
    selected_calendar_id = '6db7a044-c84b-4e4d-b23f-482cde1f80fc'  # 내 새 캘린더
    
    print("=" * 60)
    print("📊 이벤트 분포 확인")
    print("=" * 60)
    
    # 1. 모든 캘린더 정보 가져오기
    calendars_response = supabase.table('calendars').select('*').eq('owner_id', user_id).execute()
    calendars = {cal['id']: cal for cal in calendars_response.data}
    
    # 2. 모든 이벤트 가져오기
    events_response = supabase.table('calendar_events').select('*').eq('user_id', user_id).execute()
    
    # 3. 캘린더별 이벤트 수 계산
    calendar_event_counts = {}
    for event in events_response.data:
        cal_id = event['calendar_id']
        if cal_id not in calendar_event_counts:
            calendar_event_counts[cal_id] = []
        calendar_event_counts[cal_id].append(event)
    
    # 4. 결과 출력
    print("\n📅 캘린더별 이벤트 현황:")
    print("-" * 60)
    
    for cal_id, cal_info in calendars.items():
        event_count = len(calendar_event_counts.get(cal_id, []))
        marker = " ⬅️  선택한 캘린더" if cal_id == selected_calendar_id else ""
        print(f"  {cal_info['name']}: {event_count}개 이벤트{marker}")
        print(f"    ID: {cal_id}")
        
        # 선택한 캘린더의 경우 최근 이벤트 몇 개 보여주기
        if cal_id == selected_calendar_id and cal_id in calendar_event_counts:
            events = calendar_event_counts[cal_id]
            print(f"\n    최근 이벤트 (최대 5개):")
            for event in events[:5]:
                print(f"      - {event['title']}")
                print(f"        시작: {event['start_datetime']}")
    
    print("\n" + "=" * 60)
    print(f"📈 전체 통계:")
    print(f"  - 총 캘린더 수: {len(calendars)}개")
    print(f"  - 총 이벤트 수: {len(events_response.data)}개")
    
    # 5. 선택한 캘린더에 이벤트가 있는지 특별 체크
    if selected_calendar_id in calendar_event_counts:
        selected_cal_events = calendar_event_counts[selected_calendar_id]
        print(f"\n✅ '내 새 캘린더'에 {len(selected_cal_events)}개의 이벤트가 있습니다!")
    else:
        print(f"\n⚠️  '내 새 캘린더'에 이벤트가 없습니다.")
        
        # 이벤트가 어디에 있는지 확인
        print("\n🔍 이벤트가 있는 캘린더:")
        for cal_id, events in calendar_event_counts.items():
            if events:
                cal_name = calendars[cal_id]['name'] if cal_id in calendars else 'Unknown Calendar'
                print(f"  - {cal_name}: {len(events)}개")

if __name__ == "__main__":
    check_events_distribution()