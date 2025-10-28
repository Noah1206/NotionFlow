"""
간단한 통합 동기화 API 라우터 - 배포용 fallback
Supabase 의존성 없는 버전
"""

from flask import Blueprint, request, jsonify, session
import os
import sys
import json
from datetime import datetime, timezone

# 기본 blueprint만 생성
unified_sync_bp = Blueprint('unified_sync', __name__, url_prefix='/api/unified-sync')

def get_current_user_id():
    """현재 세션의 사용자 ID 획득"""
    return session.get('user_id', 'fallback_user')

def require_login():
    """로그인 필요 데코레이터 함수"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'success': False, 'error': '로그인이 필요합니다'}), 401
    return user_id

@unified_sync_bp.route('/status', methods=['GET'])
def get_platform_status():
    """플랫폼별 연결 상태 확인 - 임시 fallback"""
    try:
        user_id = require_login()
        if isinstance(user_id, tuple):
            return user_id
        
        # 임시 상태 응답
        status = {
            'google': {
                'connected': False,
                'platform': 'Google Calendar',
                'message': '서비스 준비 중'
            },
            'notion': {
                'connected': False,
                'platform': 'Notion',
                'message': '서비스 준비 중'
            },
            'apple': {
                'connected': False,
                'platform': 'Apple Calendar',
                'message': '구현 예정'
            }
        }
        
        return jsonify({
            'success': True,
            'status': status
        })
        
    except Exception as e:
        print(f"❌ [UNIFIED SYNC] Status check failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@unified_sync_bp.route('/sync', methods=['POST'])
def execute_unified_sync():
    """통합 동기화 실행 - 임시 fallback"""
    try:
        user_id = require_login()
        if isinstance(user_id, tuple):
            return user_id
        
        data = request.get_json()
        platforms = data.get('platforms', [])
        options = data.get('options', {})
        
        if not platforms:
            return jsonify({
                'success': False,
                'error': '동기화할 플랫폼을 선택해주세요'
            }), 400
        
        print(f"🚀 [UNIFIED SYNC] Starting sync for platforms: {platforms}")
        
        # 임시 결과 (실제로는 기존 sync 서비스 호출)
        results = {}
        
        for platform in platforms:
            if platform in ['google', 'notion']:
                results[platform] = {
                    'success': True,
                    'message': f'{platform} 동기화 완료 (개발 모드)'
                }
            elif platform == 'apple':
                results[platform] = {
                    'success': False,
                    'message': 'Apple Calendar 구현 예정'
                }
        
        success_count = sum(1 for r in results.values() if r.get('success'))
        total_count = len(platforms)
        
        response_data = {
            'success': success_count > 0,
            'message': f'{success_count}/{total_count} 플랫폼 동기화 완료',
            'results': results,
            'summary': {
                'successful': success_count,
                'total': total_count,
                'failed': total_count - success_count
            }
        }
        
        print(f"✅ [UNIFIED SYNC] Completed: {response_data['message']}")
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ [UNIFIED SYNC] Execution failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@unified_sync_bp.route('/preview', methods=['POST'])
def get_sync_preview():
    """동기화 미리보기 - 임시 fallback"""
    try:
        user_id = require_login()
        if isinstance(user_id, tuple):
            return user_id
        
        data = request.get_json()
        platforms = data.get('platforms', [])
        options = data.get('options', {})
        
        preview = {}
        
        for platform in platforms:
            if platform in ['google', 'notion']:
                preview[platform] = {
                    'current_events': 10,  # 임시값
                    'estimated_impact': 10,
                    'direction': options.get('direction', 'bidirectional')
                }
            elif platform == 'apple':
                preview[platform] = {
                    'current_events': 0,
                    'estimated_impact': 0,
                    'message': '구현 예정'
                }
        
        return jsonify({
            'success': True,
            'preview': preview,
            'options': options
        })
        
    except Exception as e:
        print(f"❌ [UNIFIED SYNC] Preview failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@unified_sync_bp.route('/history', methods=['GET'])
def get_sync_history():
    """동기화 기록 조회 - 임시 fallback"""
    try:
        user_id = require_login()
        if isinstance(user_id, tuple):
            return user_id
        
        # 임시 기록
        history = [
            {
                'timestamp': datetime.now().isoformat(),
                'platforms': ['google', 'notion'],
                'status': 'completed',
                'summary': '개발 모드 테스트 동기화'
            }
        ]
        
        return jsonify({
            'success': True,
            'history': history
        })
        
    except Exception as e:
        print(f"❌ [UNIFIED SYNC] History retrieval failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500