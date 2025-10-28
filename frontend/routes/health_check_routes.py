"""
🔍 Platform Health Check Routes
Automated health monitoring and status updates for registered platforms
"""

import os
import sys
import json
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from typing import Dict, List

# Add parent directory to path for backend services
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend'))
from services.sync_tracking_service import sync_tracker, EventType
sys.path.append(os.path.join(os.path.dirname(__file__), '../../utils'))
from utils.config import config

health_bp = Blueprint('health', __name__, url_prefix='/api/health')

def get_current_user_id():
    """Get current authenticated user ID"""
    from utils.auth_manager import AuthManager
    return AuthManager.get_current_user_id()

@health_bp.route('/platforms/check', methods=['POST'])
def check_all_platforms():
    """Check health status of all registered platforms for the current user"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        supabase = config.get_client_for_user(user_id)
        
        # Get all registered platforms
        result = supabase.table('registered_platforms').select('*').eq('user_id', user_id).eq('is_registered', True).execute()
        
        if not result.data:
            return jsonify({
                'success': True,
                'message': 'No registered platforms found',
                'results': []
            })
        
        from routes.platform_registration_routes import test_platform_connection
        
        check_results = []
        updated_count = 0
        
        for platform_data in result.data:
            platform = platform_data['platform']
            credentials = platform_data['credentials']
            
            # Test connection
            test_result = test_platform_connection(platform, credentials)
            
            # Determine health status
            if test_result.get('success'):
                health_status = 'healthy'
            elif test_result.get('requires_reauth'):
                health_status = 'warning'
            else:
                health_status = 'error'
            
            # Update database
            try:
                supabase.table('registered_platforms').update({
                    'health_status': health_status,
                    'last_test_at': datetime.now().isoformat(),
                    'last_error': test_result.get('error') if not test_result.get('success') else None
                }).eq('user_id', user_id).eq('platform', platform).execute()
                
                updated_count += 1
            except Exception as e:
                print(f"Failed to update platform {platform} status: {e}")
            
            check_results.append({
                'platform': platform,
                'platform_name': platform_data['platform_name'],
                'health_status': health_status,
                'success': test_result.get('success', False),
                'message': test_result.get('message', ''),
                'error': test_result.get('error'),
                'requires_reauth': test_result.get('requires_reauth', False),
                'last_test_at': datetime.now().isoformat()
            })
        
        # Track bulk health check event
        sync_tracker.track_sync_event(
            user_id=user_id,
            event_type=EventType.SYNC_STATUS_UPDATE,
            platform='system',
            status='success',
            metadata={
                'action': 'bulk_health_check',
                'platforms_checked': len(check_results),
                'platforms_updated': updated_count,
                'healthy_count': len([r for r in check_results if r['health_status'] == 'healthy']),
                'error_count': len([r for r in check_results if r['health_status'] == 'error']),
                'warning_count': len([r for r in check_results if r['health_status'] == 'warning'])
            }
        )
        
        return jsonify({
            'success': True,
            'message': f'Health check completed for {len(check_results)} platforms',
            'results': check_results,
            'summary': {
                'total_platforms': len(check_results),
                'healthy': len([r for r in check_results if r['health_status'] == 'healthy']),
                'errors': len([r for r in check_results if r['health_status'] == 'error']),
                'warnings': len([r for r in check_results if r['health_status'] == 'warning']),
                'updated_count': updated_count
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Health check failed: {str(e)}'}), 500

@health_bp.route('/platforms/auto-check', methods=['POST'])
def auto_check_platforms():
    """Automatically check platforms that haven't been tested recently"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        supabase = config.get_client_for_user(user_id)
        
        # Get platforms that haven't been tested in the last hour
        cutoff_time = (datetime.now() - timedelta(hours=1)).isoformat()
        
        result = supabase.table('registered_platforms').select('*').eq('user_id', user_id).eq('is_registered', True).or_(
            f'last_test_at.is.null,last_test_at.lt.{cutoff_time}'
        ).execute()
        
        if not result.data:
            return jsonify({
                'success': True,
                'message': 'All platforms recently tested',
                'results': []
            })
        
        from routes.platform_registration_routes import test_platform_connection
        
        check_results = []
        for platform_data in result.data:
            platform = platform_data['platform']
            credentials = platform_data['credentials']
            
            # Test connection
            test_result = test_platform_connection(platform, credentials)
            
            # Determine health status
            if test_result.get('success'):
                health_status = 'healthy'
            elif test_result.get('requires_reauth'):
                health_status = 'warning'
            else:
                health_status = 'error'
            
            # Update database
            try:
                supabase.table('registered_platforms').update({
                    'health_status': health_status,
                    'last_test_at': datetime.now().isoformat(),
                    'last_error': test_result.get('error') if not test_result.get('success') else None
                }).eq('user_id', user_id).eq('platform', platform).execute()
            except:
                pass  # Don't fail if update fails
            
            check_results.append({
                'platform': platform,
                'health_status': health_status,
                'success': test_result.get('success', False)
            })
        
        return jsonify({
            'success': True,
            'message': f'Auto-checked {len(check_results)} platforms',
            'results': check_results
        })
        
    except Exception as e:
        return jsonify({'error': f'Auto health check failed: {str(e)}'}), 500

@health_bp.route('/platforms/status', methods=['GET'])
def get_platforms_status():
    """Get current health status of all registered platforms"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        supabase = config.get_client_for_user(user_id)
        
        result = supabase.table('registered_platforms').select('''
            platform, platform_name, health_status, last_test_at, 
            last_error, created_at, credential_type
        ''').eq('user_id', user_id).eq('is_registered', True).execute()
        
        platforms_status = {}
        for platform in result.data:
            platform_id = platform['platform']
            platforms_status[platform_id] = {
                'name': platform['platform_name'],
                'health_status': platform['health_status'],
                'last_test_at': platform['last_test_at'],
                'last_error': platform['last_error'],
                'credential_type': platform['credential_type'],
                'created_at': platform['created_at']
            }
        
        # Calculate summary
        total_platforms = len(platforms_status)
        healthy_count = len([p for p in platforms_status.values() if p['health_status'] == 'healthy'])
        error_count = len([p for p in platforms_status.values() if p['health_status'] == 'error'])
        warning_count = len([p for p in platforms_status.values() if p['health_status'] == 'warning'])
        
        return jsonify({
            'success': True,
            'platforms': platforms_status,
            'summary': {
                'total': total_platforms,
                'healthy': healthy_count,
                'errors': error_count,
                'warnings': warning_count,
                'health_percentage': round((healthy_count / total_platforms * 100) if total_platforms > 0 else 0, 1)
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get platforms status: {str(e)}'}), 500

# Error handlers
@health_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Health check endpoint not found'}), 404

@health_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500