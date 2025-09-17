"""
Notion Sync API Routes
Endpoints for triggering and managing Notion synchronization
"""

from flask import Blueprint, jsonify, request, session
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend'))
from services.notion_sync_service import notion_sync_service

notion_sync_bp = Blueprint('notion_sync', __name__, url_prefix='/api/notion')

def get_current_user_id():
    """Get current user ID from session"""
    return session.get('user_id')

@notion_sync_bp.route('/sync', methods=['POST'])
def trigger_notion_sync():
    """Manually trigger Notion sync for current user"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'Authentication required'
            }), 401
        
        data = request.get_json()
        calendar_id = data.get('calendar_id')
        
        if not calendar_id:
            return jsonify({
                'success': False,
                'error': 'Calendar ID is required'
            }), 400
        
        # Trigger sync
        result = notion_sync_service.sync_notion_to_calendar(user_id, calendar_id)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@notion_sync_bp.route('/databases', methods=['GET'])
def get_notion_databases():
    """Get list of Notion databases for current user"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'Authentication required'
            }), 401
        
        # Get Notion token
        token = notion_sync_service.get_user_notion_token(user_id)
        if not token:
            return jsonify({
                'success': False,
                'error': 'Notion not connected',
                'databases': []
            })
        
        # Get databases
        from notion_client import Client as NotionClient
        notion = NotionClient(auth=token)
        
        databases = notion_sync_service._find_calendar_databases(notion)
        
        # Format response
        formatted_dbs = []
        for db in databases:
            formatted_dbs.append({
                'id': db['id'],
                'title': notion_sync_service._get_database_title(db),
                'url': db.get('url', ''),
                'has_dates': notion_sync_service._has_date_properties(db)
            })
        
        return jsonify({
            'success': True,
            'databases': formatted_dbs
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'databases': []
        }), 500

@notion_sync_bp.route('/sync-status', methods=['GET'])
def get_sync_status():
    """Get Notion sync status for current user"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'Authentication required'
            }), 401
        
        # Get sync status from database
        from utils.config import get_supabase_admin
        supabase = get_supabase_admin()
        
        # Get last sync info
        result = supabase.table('sync_status').select('*').eq(
            'user_id', user_id
        ).eq('platform', 'notion').execute()
        
        if result.data:
            status = result.data[0]
            return jsonify({
                'success': True,
                'status': status['status'],
                'last_sync': status.get('last_sync_at'),
                'details': status.get('details', {})
            })
        else:
            return jsonify({
                'success': True,
                'status': 'never_synced',
                'last_sync': None,
                'details': {}
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@notion_sync_bp.route('/events/<calendar_id>', methods=['GET'])
def get_notion_events(calendar_id):
    """Get Notion-synced events for a calendar"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'Authentication required'
            }), 401
        
        # Get events from database
        from utils.config import get_supabase_admin
        supabase = get_supabase_admin()
        
        result = supabase.table('calendar_events').select('*').eq(
            'calendar_id', calendar_id
        ).eq('external_platform', 'notion').order(
            'start_date', desc=False
        ).execute()
        
        return jsonify({
            'success': True,
            'events': result.data,
            'count': len(result.data)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'events': []
        }), 500