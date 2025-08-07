"""
🎯 Dashboard API Routes
RESTful API endpoints for dashboard data with real Supabase integration
"""

import os
import sys
from flask import Blueprint, request, jsonify, session
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../utils'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../utils'))
from utils.config import config
from utils.dashboard_data import dashboard_data

dashboard_api_bp = Blueprint('dashboard_api', __name__, url_prefix='/api/dashboard')

def get_current_user_id():
    """Get current authenticated user ID from session"""
    # This would be replaced with proper JWT token validation
    return session.get('user_id')

def require_auth():
    """Decorator to require authentication"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    return None

@dashboard_api_bp.route('/user/profile', methods=['GET'])
def get_user_profile():
    """Get current user's profile data"""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    user_id = get_current_user_id()
    
    try:
        profile = dashboard_data.get_user_profile(user_id)
        
        if profile:
            # Remove sensitive information
            safe_profile = {
                'user_id': profile.get('user_id'),
                'username': profile.get('username'),
                'display_name': profile.get('display_name'),
                'avatar_url': profile.get('avatar_url'),
                'bio': profile.get('bio'),
                'is_public': profile.get('is_public', False),
                'created_at': profile.get('created_at'),
                'updated_at': profile.get('updated_at')
            }
            
            return jsonify({
                'success': True,
                'profile': safe_profile
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Profile not found'
            }), 404
            
    except Exception as e:
        print(f"Error getting user profile: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load profile'
        }), 500

@dashboard_api_bp.route('/calendar/events', methods=['GET'])
def get_calendar_events():
    """Get user's calendar events"""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    user_id = get_current_user_id()
    
    try:
        # Get query parameters
        start_date = request.args.get('start')
        end_date = request.args.get('end')
        limit = int(request.args.get('limit', 100))
        
        # Parse dates if provided
        if start_date and end_date:
            # Custom date range
            events = dashboard_data.get_user_calendar_events(user_id, 
                start_date=datetime.fromisoformat(start_date.replace('Z', '+00:00')),
                end_date=datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            )
        else:
            # Default: next 30 days
            events = dashboard_data.get_user_calendar_events(user_id)
        
        return jsonify({
            'success': True,
            'events': events[:limit],
            'count': len(events)
        })
        
    except Exception as e:
        print(f"Error getting calendar events: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load events'
        }), 500

@dashboard_api_bp.route('/calendar/events', methods=['POST'])
def create_calendar_event():
    """Create a new calendar event"""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    user_id = get_current_user_id()
    
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'start_datetime', 'end_datetime']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Create event data
        event_data = {
            'user_id': user_id,
            'title': data['title'],
            'description': data.get('description', ''),
            'start_datetime': data['start_datetime'],
            'end_datetime': data['end_datetime'],
            'is_all_day': data.get('is_all_day', False),
            'category': data.get('category', 'personal'),
            'priority': data.get('priority', 0),
            'status': data.get('status', 'confirmed'),
            'source_platform': data.get('source_platform', 'manual'),
            'location': data.get('location', ''),
            'attendees': data.get('attendees', []),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Save to database
        supabase = config.supabase_client
        result = supabase.table('calendar_events').insert(event_data).execute()
        
        if result.data:
            return jsonify({
                'success': True,
                'event': result.data[0]
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to create event'
            }), 500
            
    except Exception as e:
        print(f"Error creating calendar event: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to create event'
        }), 500

@dashboard_api_bp.route('/platforms', methods=['GET'])
def get_platform_status():
    """Get user's platform connection status"""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    user_id = get_current_user_id()
    
    try:
        platforms = dashboard_data.get_user_api_keys(user_id)
        platform_stats = dashboard_data.get_platform_coverage(user_id)
        
        # Combine platform configs with stats
        for platform_id, platform_info in platforms.items():
            if platform_id in platform_stats:
                stats = platform_stats[platform_id]
                platform_info.update({
                    'total_synced_items': stats.get('total_synced_items', 0),
                    'sync_success_rate': stats.get('sync_success_rate', 0),
                    'avg_sync_duration_ms': stats.get('avg_sync_duration_ms', 0),
                    'feature_coverage': stats.get('feature_coverage', {})
                })
        
        return jsonify({
            'success': True,
            'platforms': platforms,
            'summary': {
                'total_platforms': len(platforms),
                'configured_platforms': len([p for p in platforms.values() if p['configured']]),
                'enabled_platforms': len([p for p in platforms.values() if p['enabled']])
            }
        })
        
    except Exception as e:
        print(f"Error getting platform status: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load platform status'
        }), 500

@dashboard_api_bp.route('/sync/status', methods=['GET'])
def get_sync_status():
    """Get user's sync status and recent activity"""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    user_id = get_current_user_id()
    
    try:
        sync_status = dashboard_data.get_user_sync_status(user_id)
        recent_activity = dashboard_data.get_recent_activity(user_id, limit=20)
        
        return jsonify({
            'success': True,
            'sync_status': sync_status,
            'recent_activity': recent_activity
        })
        
    except Exception as e:
        print(f"Error getting sync status: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load sync status'
        }), 500

@dashboard_api_bp.route('/summary', methods=['GET'])
def get_dashboard_summary():
    """Get dashboard summary statistics"""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    user_id = get_current_user_id()
    
    try:
        summary = dashboard_data.get_dashboard_summary(user_id)
        
        return jsonify({
            'success': True,
            'summary': summary
        })
        
    except Exception as e:
        print(f"Error getting dashboard summary: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load summary'
        }), 500

@dashboard_api_bp.route('/sync/trigger/<platform>', methods=['POST'])
def trigger_platform_sync(platform):
    """Trigger sync for a specific platform"""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    user_id = get_current_user_id()
    
    try:
        # TODO: Implement actual sync trigger logic
        # For now, just return success
        
        # Log the sync trigger event
        from services.sync_tracking_service import sync_tracker, EventType
        
        sync_tracker.track_sync_event(
            user_id=user_id,
            event_type=EventType.SYNC_STARTED,
            platform=platform,
            status='pending',
            metadata={
                'trigger': 'manual',
                'source': 'dashboard'
            }
        )
        
        return jsonify({
            'success': True,
            'message': f'{platform} sync triggered successfully'
        })
        
    except Exception as e:
        print(f"Error triggering sync for {platform}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to trigger sync'
        }), 500

@dashboard_api_bp.route('/activity', methods=['GET'])
def get_user_activity():
    """Get user's recent activity"""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    user_id = get_current_user_id()
    
    try:
        limit = int(request.args.get('limit', 10))
        activity = dashboard_data.get_recent_activity(user_id, limit=limit)
        
        return jsonify({
            'success': True,
            'activity': activity
        })
        
    except Exception as e:
        print(f"Error getting user activity: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load activity'
        }), 500

# Error handlers
@dashboard_api_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Dashboard API endpoint not found'}), 404

@dashboard_api_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500