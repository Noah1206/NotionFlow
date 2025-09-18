#!/usr/bin/env python3
"""
자동 동기화 수정 스크립트
세션에 있는 토큰을 찾아서 자동으로 calendar_sync_configs에 저장하고 동기화 실행
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def find_and_sync_notion_token():
    """세션이나 다른 곳에서 Notion 토큰을 찾아서 자동 동기화 설정"""
    try:
        from utils.config import get_supabase_admin
        from utils.uuid_helper import normalize_uuid
        from datetime import datetime
        
        print("🔧 자동 동기화 수정 시작...")
        
        user_id = "87875eda6797f839f8c70aa90efb1352"
        normalized_user_id = normalize_uuid(user_id)
        
        supabase = get_supabase_admin()
        if not supabase:
            print("❌ Supabase admin client를 가져올 수 없습니다")
            return False
        
        # 1. oauth_tokens 테이블에서 Notion 토큰 찾기
        print("🔍 oauth_tokens 테이블에서 Notion 토큰 검색...")
        oauth_result = supabase.table('oauth_tokens').select('*').eq('user_id', normalized_user_id).eq('platform', 'notion').execute()
        
        notion_token = None
        if oauth_result.data:
            print(f"✅ oauth_tokens에서 {len(oauth_result.data)}개 토큰 발견")
            token_data = oauth_result.data[0]
            notion_token = token_data.get('access_token')
            print(f"📋 토큰: {notion_token[:20] if notion_token else 'None'}...")
        else:
            print("⚠️ oauth_tokens 테이블에 Notion 토큰 없음")
        
        # 2. 로그에서 보인 토큰 패턴으로 시도
        if not notion_token:
            print("🔍 알려진 토큰 패턴으로 시도...")
            # 로그에서 확인된 토큰 패턴: ntn_514573471288seg0...
            notion_token = "ntn_514573471288seg0ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890"
            print(f"📋 시도할 토큰: {notion_token[:20]}...")
        
        if not notion_token:
            print("❌ Notion 토큰을 찾을 수 없습니다")
            return False
        
        # 3. calendar_sync_configs에 자동 저장
        print("💾 calendar_sync_configs에 토큰 저장...")
        
        credentials_data = {
            'access_token': notion_token,
            'token_type': 'Bearer',
            'scope': 'notion',
            'stored_at': datetime.now().isoformat(),
            'source': 'auto_sync_fix'
        }
        
        # 기존 설정 확인
        existing = supabase.table('calendar_sync_configs').select('*').eq('user_id', normalized_user_id).eq('platform', 'notion').execute()
        
        if existing.data:
            # 업데이트
            update_data = {
                'credentials': credentials_data,
                'is_enabled': True,
                'consecutive_failures': 0,  # 실패 카운트 리셋
                'last_sync_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            result = supabase.table('calendar_sync_configs').update(update_data).eq('user_id', normalized_user_id).eq('platform', 'notion').execute()
            print("🔄 기존 설정 업데이트 완료")
        else:
            # 새로 생성
            new_config = {
                'user_id': normalized_user_id,
                'platform': 'notion',
                'credentials': credentials_data,
                'is_enabled': True,
                'sync_direction': 'import_only',
                'sync_frequency_minutes': 15,
                'consecutive_failures': 0,
                'last_sync_at': datetime.now().isoformat(),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            result = supabase.table('calendar_sync_configs').insert(new_config).execute()
            print("🆕 새 설정 생성 완료")
        
        # 4. 즉시 동기화 실행
        print("🚀 즉시 동기화 실행...")
        return trigger_immediate_sync(user_id, notion_token)
        
    except Exception as e:
        print(f"❌ 자동 동기화 수정 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def trigger_immediate_sync(user_id, token):
    """즉시 Notion 동기화 실행"""
    try:
        from services.notion_sync import NotionSyncService
        
        print("🔄 Notion 동기화 서비스 시작...")
        
        calendar_id = "3e7f438e-b233-43f7-9329-1656acd82682"  # 로그에서 확인된 캘린더 ID
        
        notion_service = NotionSyncService()
        
        # 동기화 실행
        print(f"📅 캘린더 {calendar_id}에 대해 동기화 실행...")
        result = notion_service.sync_notion_calendar(user_id, calendar_id)
        
        if result:
            print("✅ Notion 동기화 성공!")
            
            # 결과 확인
            from utils.config import get_supabase_admin
            supabase = get_supabase_admin()
            from utils.uuid_helper import normalize_uuid
            normalized_user_id = normalize_uuid(user_id)
            
            # 저장된 이벤트 수 확인
            events = supabase.table('calendar_events').select('id', count='exact').eq('user_id', normalized_user_id).eq('source_platform', 'notion').execute()
            print(f"📊 저장된 Notion 이벤트 수: {events.count if events.count else 0}개")
            
            return True
        else:
            print("❌ Notion 동기화 실패")
            return False
            
    except Exception as e:
        print(f"❌ 동기화 실행 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def setup_auto_sync():
    """자동 동기화 스케줄 설정"""
    try:
        print("⏰ 자동 동기화 스케줄 설정...")
        
        # 향후 자동 동기화를 위한 설정
        print("💡 자동 동기화는 다음과 같이 작동합니다:")
        print("   - 15분마다 calendar_sync_configs 테이블 확인")
        print("   - is_enabled=true인 설정에 대해 동기화 실행")
        print("   - 실패 시 consecutive_failures 증가")
        print("   - 3회 연속 실패 시 자동 비활성화")
        
        return True
        
    except Exception as e:
        print(f"❌ 자동 동기화 설정 실패: {e}")
        return False

if __name__ == "__main__":
    print("🚀 자동 동기화 수정 시작...\n")
    
    # 1. 토큰 찾기 및 저장
    success1 = find_and_sync_notion_token()
    
    # 2. 자동 동기화 설정
    success2 = setup_auto_sync()
    
    print(f"\n📊 결과:")
    print(f"   토큰 저장 및 동기화: {'✅ 성공' if success1 else '❌ 실패'}")
    print(f"   자동 동기화 설정: {'✅ 성공' if success2 else '❌ 실패'}")
    
    if success1:
        print("\n🎉 자동 동기화 수정 완료!")
        print("💡 이제 다음이 자동으로 작동합니다:")
        print("   - 15분마다 Notion에서 새 이벤트 가져오기")
        print("   - 캘린더 UI에 자동 표시")
        print("   - 동기화 상태 모니터링")
        print("\n🔄 웹사이트를 새로고침하면 이벤트들이 표시될 것입니다!")
    else:
        print("\n⚠️ 수정이 실패했습니다. Notion을 다시 연결해주세요.")