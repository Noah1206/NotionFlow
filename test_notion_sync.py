#!/usr/bin/env python3
"""
새로운 Notion 동기화 테스트 스크립트
"""

import os
import sys
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 경로 추가
sys.path.append(os.path.dirname(__file__))

def test_notion_sync():
    """새로운 Notion 동기화 테스트"""
    
    # 사용자 정보 (로그에서 확인된 실제 사용자 ID 사용)
    USER_ID = "272f2b1c-a770-4119-92bf-563276830b84"
    CALENDAR_ID = "26481b0a-ace7-4a9f-b821-e13e0896a03e"  # 해당 사용자의 캘린더 ID
    
    print("=" * 60)
    print("🔄 새로운 NOTION 동기화 테스트")
    print("=" * 60)
    print(f"사용자 ID: {USER_ID}")
    print(f"캘린더 ID: {CALENDAR_ID}")
    print("-" * 60)
    
    try:
        # 새로운 동기화 서비스 import
        from services.notion_sync import notion_sync
        
        print("✅ Notion 동기화 서비스 로드 성공")
        
        # 토큰 확인
        print("\n1️⃣ Notion 토큰 확인...")
        token = notion_sync.get_user_notion_token(USER_ID)
        
        if token:
            print(f"✅ Notion 토큰 발견: {token[:20]}...")
        else:
            print("❌ Notion 토큰 없음")
            print("대시보드에서 Notion을 먼저 연결해주세요.")
            return
        
        # 동기화 실행
        print("\n2️⃣ 동기화 실행...")
        result = notion_sync.sync_to_calendar(USER_ID, CALENDAR_ID)
        
        print("\n" + "=" * 60)
        print("📊 동기화 결과")
        print("=" * 60)
        
        if result['success']:
            print(f"✅ 성공!")
            print(f"📅 동기화된 이벤트: {result['synced_events']}개")
            print(f"📋 처리된 데이터베이스: {result.get('databases_processed', 0)}개")
        else:
            print(f"❌ 실패: {result.get('error', '알 수 없는 오류')}")
        
        # 캘린더 이벤트 확인
        print("\n3️⃣ 캘린더 이벤트 확인...")
        try:
            from utils.config import get_supabase_admin
            supabase = get_supabase_admin()
            
            events = supabase.table('calendar_events').select('*').eq(
                'user_id', USER_ID
            ).eq('source_platform', 'notion').execute()
            
            if events.data:
                print(f"✅ 캘린더에서 {len(events.data)}개 Notion 이벤트 발견:")
                for event in events.data[:5]:  # 처음 5개만 표시
                    print(f"  📅 {event['title']} - {event['start_date']}")
                if len(events.data) > 5:
                    print(f"  ... 그리고 {len(events.data) - 5}개 더")
            else:
                print("ℹ️ 캘린더에 Notion 이벤트가 없습니다.")
                print("Notion에 캘린더/일정 데이터베이스가 있는지 확인해주세요.")
                
        except Exception as e:
            print(f"⚠️ 이벤트 확인 중 오류: {e}")
        
    except ImportError as e:
        print(f"❌ Import 오류: {e}")
        print("필요한 패키지를 설치해주세요:")
        print("pip install notion-client requests")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("테스트 완료!")
    print("=" * 60)

if __name__ == "__main__":
    test_notion_sync()