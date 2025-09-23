#!/usr/bin/env python3
"""
🔍 캘린더 이벤트 디버깅 스크립트
DB에 있는 이벤트와 선택한 캘린더의 매칭 상황을 분석합니다.
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def connect_to_db():
    """Supabase 연결"""
    try:
        from supabase import create_client
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_API_KEY")
        if not url or key:
            raise ValueError("Supabase credentials not found")
        return create_client(url, key)
    except ImportError:
        print("❌ supabase package not installed. Run: pip install supabase")
        return None

def analyze_calendar_events():
    """캘린더 이벤트 분석"""
    supabase = connect_to_db()
    if not supabase:
        return
    
    user_id = '87875eda-6797-f839-f8c7-0aa90efb1352'
    selected_calendar_id = '6db7a044-c84b-4e4d-b23f-482cde1f80fc'  # 내 새 캘린더
    
    print("=" * 80)
    print("🔍 캘린더 이벤트 매칭 분석")
    print("=" * 80)
    
    # 1. 전체 이벤트 수 확인
    try:
        all_events = supabase.table('calendar_events').select('*').eq('user_id', user_id).execute()
        total_events = len(all_events.data) if all_events.data else 0
        print(f"\n📊 전체 이벤트 수: {total_events}개")
        
        if total_events == 0:
            print("❌ 이벤트가 전혀 없습니다. 동기화 문제일 수 있습니다.")
            return
            
    except Exception as e:
        print(f"❌ 전체 이벤트 조회 실패: {e}")
        return
    
    # 2. 캘린더별 이벤트 분포 분석
    print(f"\n📅 캘린더별 이벤트 분포:")
    print("-" * 60)
    
    calendar_distribution = {}
    platform_distribution = {}
    
    for event in all_events.data:
        calendar_id = event.get('calendar_id')
        platform = event.get('source_platform', 'unknown')
        
        # 캘린더별 카운트
        if calendar_id not in calendar_distribution:
            calendar_distribution[calendar_id] = []
        calendar_distribution[calendar_id].append(event)
        
        # 플랫폼별 카운트  
        if platform not in platform_distribution:
            platform_distribution[platform] = []
        platform_distribution[platform].append(event)
    
    # 캘린더별 출력
    for cal_id, events in calendar_distribution.items():
        marker = " ⬅️ 선택한 캘린더" if cal_id == selected_calendar_id else ""
        cal_name = "null" if cal_id is None else cal_id
        print(f"  📂 {cal_name}: {len(events)}개{marker}")
        
        # 선택한 캘린더의 최근 이벤트 몇 개 보기
        if cal_id == selected_calendar_id:
            print(f"    최근 이벤트:")
            for event in events[:3]:
                print(f"      • {event.get('title')} ({event.get('start_datetime')})")
    
    # 3. 플랫폼별 분포
    print(f"\n🌐 플랫폼별 이벤트 분포:")
    print("-" * 60)
    for platform, events in platform_distribution.items():
        print(f"  {platform}: {len(events)}개")
    
    # 4. 핵심 문제 분석
    print(f"\n🔍 핵심 문제 분석:")
    print("-" * 60)
    
    selected_cal_events = calendar_distribution.get(selected_calendar_id, [])
    null_cal_events = calendar_distribution.get(None, [])
    
    print(f"  선택한 캘린더 이벤트: {len(selected_cal_events)}개")
    print(f"  calendar_id가 null인 이벤트: {len(null_cal_events)}개")
    
    if len(null_cal_events) > 0:
        print(f"\n⚠️  문제 발견: calendar_id가 null인 이벤트가 {len(null_cal_events)}개 있습니다!")
        print(f"   이 이벤트들이 선택한 캘린더에 표시되지 않는 원인일 수 있습니다.")
        
        # null 이벤트 샘플 보기
        print(f"\n   null calendar_id 이벤트 샘플:")
        for event in null_cal_events[:5]:
            print(f"     • {event.get('title')} (플랫폼: {event.get('source_platform')})")
    
    # 5. 해결책 제안
    print(f"\n💡 해결책:")
    print("-" * 60)
    
    if len(null_cal_events) > 0:
        print(f"  1. calendar_id가 null인 {len(null_cal_events)}개 이벤트를 선택한 캘린더로 업데이트")
        print(f"     UPDATE calendar_events SET calendar_id = '{selected_calendar_id}'")
        print(f"     WHERE user_id = '{user_id}' AND calendar_id IS NULL;")
    
    if len(selected_cal_events) < total_events * 0.8:  # 80% 미만이면 문제
        print(f"  2. 다른 캘린더 ID로 저장된 이벤트들을 확인하고 통합 고려")
    
    # 6. 실제 캘린더 테이블 확인
    print(f"\n📋 캘린더 테이블 확인:")
    print("-" * 60)
    
    try:
        calendars = supabase.table('calendars').select('*').eq('owner_id', user_id).execute()
        print(f"  사용자의 캘린더 수: {len(calendars.data) if calendars.data else 0}개")
        
        for cal in calendars.data or []:
            cal_id = cal.get('id')
            cal_name = cal.get('name')
            event_count = len(calendar_distribution.get(cal_id, []))
            marker = " ⬅️ 선택됨" if cal_id == selected_calendar_id else ""
            print(f"    {cal_name} ({cal_id}): {event_count}개 이벤트{marker}")
            
    except Exception as e:
        print(f"  ❌ 캘린더 테이블 조회 실패: {e}")

def fix_null_calendar_ids():
    """calendar_id가 null인 이벤트들을 선택한 캘린더로 업데이트"""
    supabase = connect_to_db()
    if not supabase:
        return
    
    user_id = '87875eda-6797-f839-f8c7-0aa90efb1352'
    selected_calendar_id = '6db7a044-c84b-4e4d-b23f-482cde1f80fc'
    
    print("\n" + "=" * 80)
    print("🔧 calendar_id null 이벤트 수정")
    print("=" * 80)
    
    try:
        # null calendar_id 이벤트 찾기
        null_events = supabase.table('calendar_events').select('id, title').eq('user_id', user_id).is_('calendar_id', 'null').execute()
        
        if not null_events.data:
            print("✅ calendar_id가 null인 이벤트가 없습니다.")
            return
        
        count = len(null_events.data)
        print(f"📝 {count}개의 null calendar_id 이벤트를 '{selected_calendar_id}'로 업데이트합니다...")
        
        # 업데이트 실행
        result = supabase.table('calendar_events').update({
            'calendar_id': selected_calendar_id
        }).eq('user_id', user_id).is_('calendar_id', 'null').execute()
        
        print(f"✅ 업데이트 완료: {count}개 이벤트의 calendar_id를 설정했습니다.")
        
    except Exception as e:
        print(f"❌ 업데이트 실패: {e}")

if __name__ == "__main__":
    analyze_calendar_events()
    
    # 수정 실행 여부 확인
    response = input("\n🔧 calendar_id가 null인 이벤트들을 수정하시겠습니까? (y/N): ")
    if response.lower() in ['y', 'yes']:
        fix_null_calendar_ids()
    else:
        print("수정을 취소했습니다.")