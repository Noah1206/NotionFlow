#!/usr/bin/env python3
"""
calendar_events 테이블 직접 분석
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def analyze_calendar_events_table():
    """calendar_events 테이블 구조 및 데이터 분석"""
    try:
        from utils.config import get_supabase_admin
        from utils.uuid_helper import normalize_uuid
        
        print("🔧 calendar_events 테이블 직접 분석...")
        
        # Test user ID (from logs)
        test_user_id = "87875eda6797f839f8c70aa90efb1352"
        normalized_user_id = normalize_uuid(test_user_id)
        
        print(f"📋 분석할 사용자 ID: {test_user_id}")
        print(f"📋 정규화된 사용자 ID: {normalized_user_id}")
        
        # Get Supabase admin client
        supabase = get_supabase_admin()
        if not supabase:
            print("❌ Supabase admin client를 가져올 수 없습니다")
            return False
        
        print("✅ Supabase admin client 획득 완료")
        
        # 1. 테이블 구조 확인
        print("\n🔍 1. calendar_events 테이블 구조 확인...")
        try:
            # 샘플 레코드 하나만 가져와서 구조 확인
            sample_result = supabase.table('calendar_events').select('*').limit(1).execute()
            
            if sample_result.data:
                print("✅ 테이블이 존재하고 데이터가 있습니다")
                print("📋 테이블 컬럼 구조:")
                for key in sample_result.data[0].keys():
                    print(f"   - {key}: {type(sample_result.data[0][key])}")
            else:
                print("⚠️ 테이블은 존재하지만 데이터가 없습니다")
        
        except Exception as structure_error:
            print(f"❌ 테이블 구조 확인 실패: {structure_error}")
            return False
        
        # 2. 특정 사용자의 이벤트 확인 (정규화된 ID)
        print(f"\n🔍 2. 사용자 {normalized_user_id}의 이벤트 확인...")
        try:
            user_events = supabase.table('calendar_events').select('*').eq('user_id', normalized_user_id).execute()
            print(f"📊 정규화된 ID로 찾은 이벤트: {len(user_events.data) if user_events.data else 0}개")
            
            if user_events.data:
                print("📋 첫 번째 이벤트 샘플:")
                event = user_events.data[0]
                for key, value in event.items():
                    print(f"   - {key}: {value}")
                    
        except Exception as user_error:
            print(f"❌ 정규화된 사용자 ID 검색 실패: {user_error}")
        
        # 3. 원본 사용자 ID로도 확인
        print(f"\n🔍 3. 사용자 {test_user_id}의 이벤트 확인 (원본 형식)...")
        try:
            original_events = supabase.table('calendar_events').select('*').eq('user_id', test_user_id).execute()
            print(f"📊 원본 ID로 찾은 이벤트: {len(original_events.data) if original_events.data else 0}개")
            
        except Exception as original_error:
            print(f"❌ 원본 사용자 ID 검색 실패: {original_error}")
        
        # 4. 모든 이벤트 수 확인
        print(f"\n🔍 4. 전체 calendar_events 테이블 레코드 수...")
        try:
            all_events = supabase.table('calendar_events').select('id', count='exact').execute()
            print(f"📊 전체 이벤트 수: {all_events.count}개")
            
        except Exception as count_error:
            print(f"❌ 전체 이벤트 수 확인 실패: {count_error}")
        
        # 5. 최근 이벤트들 확인 (Notion sync 로그 시간대 기준)
        print(f"\n🔍 5. 최근 생성된 이벤트 확인...")
        try:
            recent_events = supabase.table('calendar_events').select('*').order('created_at', desc=True).limit(10).execute()
            print(f"📊 최근 이벤트: {len(recent_events.data) if recent_events.data else 0}개")
            
            if recent_events.data:
                for i, event in enumerate(recent_events.data[:3], 1):  # 최근 3개만
                    print(f"📅 이벤트 {i}:")
                    print(f"   - ID: {event.get('id')}")
                    print(f"   - Title: {event.get('title')}")
                    print(f"   - User ID: {event.get('user_id')}")
                    print(f"   - Calendar ID: {event.get('calendar_id')}")
                    print(f"   - Start: {event.get('start_date')}")
                    print(f"   - Created: {event.get('created_at')}")
                    print()
                    
        except Exception as recent_error:
            print(f"❌ 최근 이벤트 확인 실패: {recent_error}")
        
        return True
        
    except Exception as e:
        print(f"❌ calendar_events 테이블 분석 실패: {e}")
        return False

def check_calendar_query_logic():
    """캘린더 이벤트 조회 로직 확인"""
    try:
        print("\n🔧 캘린더 이벤트 조회 로직 확인...")
        
        # dashboard_data.py의 get_user_calendar_events 함수 확인
        with open('/Users/johyeon-ung/Desktop/NotionFlow/utils/dashboard_data.py', 'r') as f:
            content = f.read()
        
        # calendar_events 테이블 쿼리 부분 찾기
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'calendar_events' in line and 'select' in line.lower():
                print(f"📋 Line {i+1}: {line.strip()}")
                # 주변 컨텍스트도 출력
                context_start = max(0, i-3)
                context_end = min(len(lines), i+8)
                print("📋 컨텍스트:")
                for j in range(context_start, context_end):
                    marker = ">>> " if j == i else "    "
                    print(f"{marker}{lines[j]}")
                print()
        
        return True
        
    except Exception as e:
        print(f"❌ 조회 로직 확인 실패: {e}")
        return False

if __name__ == "__main__":
    print("🚀 calendar_events 테이블 분석 시작...\n")
    
    # 분석 1: 테이블 직접 분석
    success1 = analyze_calendar_events_table()
    
    # 분석 2: 조회 로직 확인  
    success2 = check_calendar_query_logic()
    
    print("\n📊 분석 결과:")
    print(f"   calendar_events 테이블 분석: {'✅ 성공' if success1 else '❌ 실패'}")
    print(f"   조회 로직 확인: {'✅ 성공' if success2 else '❌ 실패'}")
    
    if success1 and success2:
        print("\n🎉 분석 완료! 위의 결과를 바탕으로 문제를 파악할 수 있습니다.")
    else:
        print("\n⚠️ 일부 분석이 실패했습니다. 로그를 확인해주세요.")