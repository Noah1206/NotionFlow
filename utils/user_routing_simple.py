"""
🚀 Simple User Routing - No Encrypted URLs
All dashboard routes now use /dashboard
"""

def get_dashboard_url():
    """Get simple dashboard URL"""
    return "/dashboard"

def get_dashboard_subpath_url(path):
    """Get dashboard subpath URL"""
    return f"/dashboard/{path}"

def validate_dashboard_access(user_id=None):
    """Simple dashboard access validation"""
    from flask import session
    return 'user_id' in session, "Authentication required"