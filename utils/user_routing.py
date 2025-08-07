"""
🚀 User Routing Middleware
Centralized routing logic for user-specific dashboard routes
"""

import re
from typing import Optional, Tuple, Dict, Any
from flask import render_template, redirect, session
from functools import wraps

class UserRoutingMiddleware:
    """Middleware for handling user-specific routing with consistent validation"""
    
    @staticmethod
    def validate_username_route(username: str) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        Validate username-based route and return user profile
        Returns: (is_valid, error_message, user_profile)
        """
        try:
            # Import here to avoid circular imports
            from utils.auth_utils import security_validator, validate_dashboard_access
            from utils.user_profile_manager import UserProfileManager
            
            # Security validation
            is_valid_path, path_message = security_validator.validate_url_path(username)
            if not is_valid_path:
                return False, "Invalid path", None
                
            is_valid_username, username_message = security_validator.validate_username_format(username)
            if not is_valid_username:
                return False, "Invalid username format", None
            
            # Sanitize username
            clean_username = security_validator.sanitize_input(username, max_length=20)
            if clean_username != username:
                return False, "Username contains invalid characters", None
            
            # Get user profile
            profile = UserProfileManager.get_user_by_username(username)
            if not profile:
                return False, "User not found", None
            
            # Basic access validation
            access_allowed, access_message = validate_dashboard_access(username)
            if not access_allowed:
                return False, access_message, None
            
            return True, None, profile
            
        except Exception as e:
            print(f"Error validating username route: {e}")
            return False, "Internal error", None
    
    @staticmethod
    def validate_encrypted_id_route(encrypted_id: str) -> Tuple[bool, Optional[str]]:
        """
        Validate encrypted user ID route
        Returns: (is_valid, error_message)
        """
        if not re.match(r'^[a-zA-Z0-9_-]{8,12}$', encrypted_id):
            return False, "Invalid encrypted ID format"
        return True, None
    
    @staticmethod
    def create_username_route_handler(template_name: str, page_name: str, extra_params: callable = None):
        """
        Create a standardized username-based route handler
        extra_params: callable that takes (profile, username) and returns dict of extra template params
        """
        def route_handler(username: str):
            is_valid, error_msg, profile = UserRoutingMiddleware.validate_username_route(username)
            
            if not is_valid:
                if "not found" in error_msg.lower():
                    return render_template('404.html'), 404
                else:
                    return render_template('403.html'), 403
            
            template_params = {
                'user_profile': profile,
                'current_page': page_name,
                'username': username
            }
            
            # Add extra parameters if provided
            if extra_params and callable(extra_params):
                extra = extra_params(profile, username)
                if isinstance(extra, dict):
                    template_params.update(extra)
            
            return render_template(template_name, **template_params)
        
        return route_handler
    
    @staticmethod
    def create_encrypted_id_route_handler(template_name: str, page_name: str):
        """
        Create a standardized encrypted user ID route handler
        """
        def route_handler(encrypted_user_id: str):
            is_valid, error_msg = UserRoutingMiddleware.validate_encrypted_id_route(encrypted_user_id)
            
            if not is_valid:
                return render_template('404.html'), 404
            
            return render_template(template_name,
                                 current_page=page_name,
                                 encrypted_user_id=encrypted_user_id)
        
        return route_handler
    
    @staticmethod
    def create_encrypted_email_route_handler(template_name: str, page_name: str):
        """
        Create a standardized encrypted email route handler
        """
        def route_handler(encrypted_email: str):
            is_valid, error_msg = UserRoutingMiddleware.validate_encrypted_id_route(encrypted_email)
            
            if not is_valid:
                return render_template('404.html'), 404
            
            return render_template(template_name,
                                 current_page=page_name,
                                 encrypted_email=encrypted_email)
        
        return route_handler
    
    @staticmethod
    def require_user_access(f):
        """
        Decorator to require user access validation for routes
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Extract username from kwargs if present
            username = kwargs.get('username')
            encrypted_user_id = kwargs.get('encrypted_user_id') 
            encrypted_email = kwargs.get('encrypted_email')
            
            if username:
                is_valid, error_msg, profile = UserRoutingMiddleware.validate_username_route(username)
                if not is_valid:
                    if "not found" in error_msg.lower():
                        return render_template('404.html'), 404
                    else:
                        return render_template('403.html'), 403
                # Add profile to kwargs for use in route
                kwargs['user_profile'] = profile
                
            elif encrypted_user_id:
                is_valid, error_msg = UserRoutingMiddleware.validate_encrypted_id_route(encrypted_user_id)
                if not is_valid:
                    return render_template('404.html'), 404
                    
            elif encrypted_email:
                is_valid, error_msg = UserRoutingMiddleware.validate_encrypted_id_route(encrypted_email)
                if not is_valid:
                    return render_template('404.html'), 404
            
            return f(*args, **kwargs)
        return decorated_function

class DashboardRouteBuilder:
    """Builder class for creating consistent dashboard routes"""
    
    def __init__(self, app):
        self.app = app
        self.routes = []
    
    def add_username_route(self, path: str, template: str, page_name: str, endpoint_name: str, extra_params: callable = None):
        """Add a username-based dashboard route"""
        handler = UserRoutingMiddleware.create_username_route_handler(template, page_name, extra_params)
        self.app.add_url_rule(f'/u/<username>/dashboard/{path}', endpoint_name, handler)
        self.routes.append(f'/u/<username>/dashboard/{path}')
        return self
    
    def add_encrypted_id_route(self, path: str, template: str, page_name: str, endpoint_name: str):
        """Add an encrypted user ID dashboard route"""
        handler = UserRoutingMiddleware.create_encrypted_id_route_handler(template, page_name)
        self.app.add_url_rule(f'/u/<encrypted_user_id>/dashboard/{path}', endpoint_name, handler)
        self.routes.append(f'/u/<encrypted_user_id>/dashboard/{path}')
        return self
    
    def add_encrypted_email_route(self, path: str, template: str, page_name: str, endpoint_name: str):
        """Add an encrypted email dashboard route"""
        handler = UserRoutingMiddleware.create_encrypted_email_route_handler(template, page_name)
        self.app.add_url_rule(f'/<encrypted_email>/dashboard/{path}', endpoint_name, handler)
        self.routes.append(f'/<encrypted_email>/dashboard/{path}')
        return self
    
    def add_all_variants(self, path: str, template: str, page_name: str, base_endpoint: str, extra_params: callable = None):
        """Add all three variants of a dashboard route"""
        self.add_username_route(path, template, page_name, f'username_{base_endpoint}', extra_params)
        self.add_encrypted_id_route(path, template, page_name, f'encrypted_id_{base_endpoint}')
        self.add_encrypted_email_route(path, template, page_name, f'encrypted_email_{base_endpoint}')
        return self
    
    def build(self):
        """Return the list of created routes"""
        return self.routes

def get_user_dashboard_url(username: str = None, encrypted_user_id: str = None, encrypted_email: str = None) -> str:
    """
    Generate appropriate dashboard URL based on available user identifier
    """
    if username:
        return f'/u/{username}/dashboard'
    elif encrypted_user_id:
        return f'/u/{encrypted_user_id}/dashboard'
    elif encrypted_email:
        return f'/{encrypted_email}/dashboard'
    else:
        return '/dashboard'  # Fallback to generic

def get_user_specific_url(path: str, username: str = None, encrypted_user_id: str = None, encrypted_email: str = None) -> str:
    """
    Generate user-specific URL for any dashboard path
    """
    if username:
        return f'/u/{username}/dashboard/{path}'
    elif encrypted_user_id:
        return f'/u/{encrypted_user_id}/dashboard/{path}'
    elif encrypted_email:
        return f'/{encrypted_email}/dashboard/{path}'
    else:
        return f'/dashboard/{path}'  # Fallback to generic

def extract_user_context(request_path: str) -> Dict[str, Any]:
    """
    Extract user context from request path
    Returns dict with user identifier and route info
    """
    context = {
        'username': None,
        'encrypted_user_id': None,
        'encrypted_email': None,
        'route_type': 'generic',
        'dashboard_path': None
    }
    
    # Username pattern: /u/{username}/dashboard/{path}
    username_match = re.match(r'^/u/([a-zA-Z0-9_]{3,20})/dashboard(?:/(.+))?$', request_path)
    if username_match:
        context['username'] = username_match.group(1)
        context['route_type'] = 'username'
        context['dashboard_path'] = username_match.group(2) or 'settings'
        return context
    
    # Encrypted user ID pattern: /u/{encrypted_id}/dashboard/{path}
    encrypted_id_match = re.match(r'^/u/([a-zA-Z0-9_-]{8,12})/dashboard(?:/(.+))?$', request_path)
    if encrypted_id_match:
        context['encrypted_user_id'] = encrypted_id_match.group(1)
        context['route_type'] = 'encrypted_id'
        context['dashboard_path'] = encrypted_id_match.group(2) or 'settings'
        return context
    
    # Encrypted email pattern: /{encrypted_email}/dashboard/{path}
    encrypted_email_match = re.match(r'^/([a-zA-Z0-9_-]{8,12})/dashboard(?:/(.+))?$', request_path)
    if encrypted_email_match:
        context['encrypted_email'] = encrypted_email_match.group(1)
        context['route_type'] = 'encrypted_email'
        context['dashboard_path'] = encrypted_email_match.group(2) or 'settings'
        return context
    
    return context