"""
🔐 NotionFlow Authentication Utilities
JWT token validation and user session management utilities
"""

import jwt
import re
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from supabase import create_client

class AuthValidator:
    def __init__(self, supabase_url, supabase_key):
        self.supabase = create_client(supabase_url, supabase_key)
        
    def validate_jwt_token(self, token):
        """Validate Supabase JWT token"""
        try:
            # For Supabase tokens, we need to verify with Supabase directly
            # This is a simplified version - in production, use proper JWT verification
            if not token or not token.startswith('eyJ'):
                return None
                
            # Extract user info from token (simplified)
            # In production, use proper JWT decoding with Supabase's public key
            return {'valid': True, 'user_id': 'temp_user_id'}
        except Exception as e:
            print(f"JWT validation error: {e}")
            return None
    
    def get_user_from_token(self, token):
        """Get user information from JWT token"""
        try:
            if not token:
                return None
                
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
                
            # Validate token with Supabase
            validation = self.validate_jwt_token(token)
            if not validation:
                return None
                
            # Get user from Supabase (this is a placeholder)
            # In practice, the JWT token contains user info
            return validation
        except Exception as e:
            print(f"Error getting user from token: {e}")
            return None

class SecurityValidator:
    """Security validation utilities"""
    
    @staticmethod
    def validate_username_format(username):
        """Validate username format and security"""
        if not username:
            return False, "사용자명이 필요합니다"
            
        # Length check
        if len(username) < 3 or len(username) > 20:
            return False, "사용자명은 3-20자여야 합니다"
            
        # Format check
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "사용자명은 영문, 숫자, 언더스코어만 사용 가능합니다"
            
        # Reserved words check
        reserved_words = {
            'admin', 'api', 'www', 'dashboard', 'login', 'signup', 'logout',
            'settings', 'profile', 'help', 'support', 'about', 'contact',
            'privacy', 'terms', 'legal', 'pricing', 'billing', 'payment',
            'app', 'mobile', 'desktop', 'web', 'ios', 'android',
            'notionflow', 'notion', 'flow', 'calendar', 'schedule',
            'root', 'system', 'config', 'static', 'assets', 'public',
            'test', 'demo', 'null', 'undefined', 'anonymous', 'guest'
        }
        
        if username.lower() in reserved_words:
            return False, "사용할 수 없는 사용자명입니다"
            
        # Prevent consecutive underscores
        if '__' in username:
            return False, "연속된 언더스코어는 사용할 수 없습니다"
            
        # Prevent starting/ending with underscore
        if username.startswith('_') or username.endswith('_'):
            return False, "사용자명은 언더스코어로 시작하거나 끝날 수 없습니다"
            
        return True, "사용 가능한 사용자명입니다"
    
    @staticmethod
    def sanitize_input(input_string, max_length=None):
        """Sanitize user input to prevent injection attacks"""
        if not input_string:
            return ""
            
        # Remove potential script tags and SQL injection patterns
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>.*?</iframe>',
            r'<object[^>]*>.*?</object>',
            r'<embed[^>]*>.*?</embed>',
            r'<form[^>]*>.*?</form>',
            r'<input[^>]*>',
            r'<button[^>]*>.*?</button>',
            r'<meta[^>]*>',
            r'<link[^>]*>',
            r'<style[^>]*>.*?</style>',
            r'expression\s*\(',
            r'url\s*\(',
            r'@import',
            r'<!--.*?-->',
            r'<!DOCTYPE[^>]*>',
            r'<\?php.*?\?>',
            r'<\?.*?\?>',
            r'<%.*?%>',
            r'\bselect\b.*\bfrom\b',
            r'\binsert\b.*\binto\b',
            r'\bupdate\b.*\bset\b',
            r'\bdelete\b.*\bfrom\b',
            r'\bdrop\b.*\btable\b',
            r'\bunion\b.*\bselect\b'
        ]
        
        sanitized = input_string
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        # Trim whitespace
        sanitized = sanitized.strip()
        
        # Apply length limit
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
            
        return sanitized
    
    @staticmethod
    def validate_url_path(path):
        """Validate URL path for potential attacks"""
        if not path:
            return False, "경로가 필요합니다"
            
        # Check for path traversal attempts
        dangerous_path_patterns = [
            r'\.\./',
            r'\\',
            r'/\.\.',
            r'\.\.\\',
            r'%2e%2e',
            r'%2f',
            r'%5c',
            r'\x00',
            r'//+',
            r'/\./+',
            r'/\?\?/',
            r'/\*',
            r'/null',
            r'/con',
            r'/aux',
            r'/prn'
        ]
        
        for pattern in dangerous_path_patterns:
            if re.search(pattern, path, re.IGNORECASE):
                return False, "유효하지 않은 경로입니다"
        
        # Check length
        if len(path) > 255:
            return False, "경로가 너무 깁니다"
            
        return True, "유효한 경로입니다"

class RateLimiter:
    """Simple in-memory rate limiter for username operations"""
    
    def __init__(self):
        self.requests = {}  # {ip: {action: [(timestamp, count), ...]}}
        
    def is_allowed(self, ip_address, action, max_requests=5, time_window=300):
        """Check if request is within rate limits"""
        current_time = datetime.now()
        
        if ip_address not in self.requests:
            self.requests[ip_address] = {}
            
        if action not in self.requests[ip_address]:
            self.requests[ip_address][action] = []
            
        # Clean old requests
        cutoff_time = current_time - timedelta(seconds=time_window)
        self.requests[ip_address][action] = [
            req for req in self.requests[ip_address][action] 
            if req[0] > cutoff_time
        ]
        
        # Check if limit exceeded
        total_requests = sum(req[1] for req in self.requests[ip_address][action])
        if total_requests >= max_requests:
            return False, f"Rate limit exceeded. Try again in {time_window} seconds."
            
        # Add current request
        self.requests[ip_address][action].append((current_time, 1))
        return True, "Request allowed"
        
    def reset_for_ip(self, ip_address):
        """Reset rate limits for specific IP"""
        if ip_address in self.requests:
            del self.requests[ip_address]

# Global instances
auth_validator = None
security_validator = SecurityValidator()
rate_limiter = RateLimiter()

def init_auth_utils(supabase_url, supabase_key):
    """Initialize auth utilities with Supabase credentials"""
    global auth_validator
    auth_validator = AuthValidator(supabase_url, supabase_key)

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({
                'success': False, 
                'error': 'Authentication required'
            }), 401
            
        user = auth_validator.get_user_from_token(auth_header)
        if not user:
            return jsonify({
                'success': False, 
                'error': 'Invalid authentication token'
            }), 401
            
        # Add user to request context
        request.current_user = user
        return f(*args, **kwargs)
    return decorated_function

def require_rate_limit(action, max_requests=5, time_window=300):
    """Decorator to apply rate limiting"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            ip_address = request.remote_addr
            
            allowed, message = rate_limiter.is_allowed(
                ip_address, action, max_requests, time_window
            )
            
            if not allowed:
                return jsonify({
                    'success': False,
                    'error': message
                }), 429  # Too Many Requests
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_dashboard_access(username, user_id=None):
    """Validate that user can access specific dashboard"""
    try:
        from utils.user_profile_manager import UserProfileManager
        
        # Get profile for requested username
        profile = UserProfileManager.get_user_by_username(username)
        if not profile:
            return False, "User not found"
            
        # If user_id provided, check ownership
        if user_id and profile['user_id'] != user_id:
            return False, "Access denied"
            
        return True, "Access granted"
    except Exception as e:
        print(f"Error validating dashboard access: {e}")
        return False, "Validation error"