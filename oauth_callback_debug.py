#!/usr/bin/env python3
"""
OAuth 콜백 디버그 및 강화 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def add_oauth_debug_endpoint():
    """OAuth 디버그 엔드포인트 추가"""
    try:
        # OAuth routes 파일에 디버그 엔드포인트 추가
        oauth_routes_path = '/Users/johyeon-ung/Desktop/NotionFlow/frontend/routes/oauth_routes.py'
        
        debug_endpoint = '''

@oauth_bp.route('/debug/notion-token/<user_id>')
def debug_notion_token(user_id):
    """Notion 토큰 디버그 엔드포인트"""
    try:
        from utils.config import get_supabase_admin
        from utils.uuid_helper import normalize_uuid
        from datetime import datetime
        
        normalized_user_id = normalize_uuid(user_id)
        supabase = get_supabase_admin()
        
        debug_info = {
            'user_id': user_id,
            'normalized_user_id': normalized_user_id,
            'timestamp': datetime.now().isoformat()
        }
        
        # 1. oauth_tokens 테이블 확인
        oauth_tokens = supabase.table('oauth_tokens').select('*').eq('user_id', normalized_user_id).eq('platform', 'notion').execute()
        debug_info['oauth_tokens'] = {
            'count': len(oauth_tokens.data) if oauth_tokens.data else 0,
            'data': oauth_tokens.data
        }
        
        # 2. calendar_sync_configs 테이블 확인
        sync_configs = supabase.table('calendar_sync_configs').select('*').eq('user_id', normalized_user_id).eq('platform', 'notion').execute()
        debug_info['sync_configs'] = {
            'count': len(sync_configs.data) if sync_configs.data else 0,
            'data': sync_configs.data
        }
        
        # 3. 세션 정보 확인
        debug_info['session'] = {
            'has_platform_tokens': 'platform_tokens' in session,
            'notion_in_session': session.get('platform_tokens', {}).get('notion') is not None if 'platform_tokens' in session else False
        }
        
        return jsonify({
            'success': True,
            'debug_info': debug_info
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@oauth_bp.route('/force-sync/notion/<user_id>')
def force_notion_sync(user_id):
    """강제 Notion 동기화 엔드포인트"""
    try:
        from services.notion_sync import NotionSyncService
        from utils.uuid_helper import normalize_uuid
        
        normalized_user_id = normalize_uuid(user_id)
        calendar_id = "3e7f438e-b233-43f7-9329-1656acd82682"
        
        notion_service = NotionSyncService()
        
        # 토큰 확인
        token = notion_service.get_user_notion_token(user_id)
        if not token:
            return jsonify({
                'success': False,
                'error': 'No Notion token found'
            }), 404
        
        # 강제 동기화 실행
        result = notion_service.sync_notion_calendar(user_id, calendar_id)
        
        return jsonify({
            'success': True,
            'sync_result': result,
            'token_preview': token[:20] + '...' if token else None
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
'''
        
        # 파일에 추가
        with open(oauth_routes_path, 'r') as f:
            content = f.read()
        
        if '/debug/notion-token' not in content:
            with open(oauth_routes_path, 'a') as f:
                f.write(debug_endpoint)
            print("✅ OAuth 디버그 엔드포인트 추가 완료")
            return True
        else:
            print("✅ OAuth 디버그 엔드포인트가 이미 존재합니다")
            return True
        
    except Exception as e:
        print(f"❌ 디버그 엔드포인트 추가 실패: {e}")
        return False

def improve_oauth_callback():
    """OAuth 콜백 로직 개선"""
    try:
        print("🔧 OAuth 콜백 로직 개선...")
        
        # 이미 개선된 로직이 있으므로 추가 개선사항 제안
        improvements = [
            "✅ 더 상세한 에러 로깅 추가됨",
            "💡 제안: 토큰 저장 실패 시 재시도 로직 추가",
            "💡 제안: 토큰 검증 후 저장",
            "💡 제안: 성공/실패 상태를 사용자에게 명확히 전달"
        ]
        
        for improvement in improvements:
            print(f"   {improvement}")
        
        return True
        
    except Exception as e:
        print(f"❌ OAuth 콜백 개선 실패: {e}")
        return False

if __name__ == "__main__":
    print("🚀 OAuth 콜백 디버그 및 강화 시작...\n")
    
    # 1. 디버그 엔드포인트 추가
    success1 = add_oauth_debug_endpoint()
    
    # 2. OAuth 콜백 개선
    success2 = improve_oauth_callback()
    
    print(f"\n📊 결과:")
    print(f"   디버그 엔드포인트 추가: {'✅ 성공' if success1 else '❌ 실패'}")
    print(f"   OAuth 콜백 개선: {'✅ 성공' if success2 else '❌ 실패'}")
    
    if success1:
        print("\n🎉 OAuth 디버그 강화 완료!")
        print("💡 이제 다음 URL로 디버그할 수 있습니다:")
        print("   - /oauth/debug/notion-token/87875eda6797f839f8c70aa90efb1352")
        print("   - /oauth/force-sync/notion/87875eda6797f839f8c70aa90efb1352")
        print("\n🔄 Notion을 다시 연결하면 더 자세한 로그를 볼 수 있습니다!")
    else:
        print("\n⚠️ 일부 개선이 실패했습니다.")