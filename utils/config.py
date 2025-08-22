"""
🔐 NotionFlow Configuration Manager
Secure configuration management with environment variables and validation
"""

import os
import sys
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
import base64
import json
# Supabase import will be done lazily to avoid blocking
from dotenv import load_dotenv

class Config:
    """Centralized configuration management"""
    
    def __init__(self):
        self._load_environment()
        self._validate_required_keys()
        self._init_encryption()
        self._init_supabase()
    
    def _load_environment(self):
        """Load environment variables"""
        # Load environment variables from .env file
        load_dotenv()
        
        # Supabase Configuration
        self.SUPABASE_URL = os.getenv('SUPABASE_URL')
        self.SUPABASE_ANON_KEY = os.getenv('SUPABASE_API_KEY')
        self.SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        # API Key Encryption
        self.API_KEY_ENCRYPTION_KEY = os.getenv('API_KEY_ENCRYPTION_KEY')
        
        # Flask Configuration
        self.FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
        self.FLASK_ENV = os.getenv('FLASK_ENV', 'production')
        
        # Feature flags
        self.DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
        
    def _validate_required_keys(self):
        """Validate that all required environment variables are present"""
        required_keys = [
            'SUPABASE_URL',
            'SUPABASE_API_KEY', 
            'SUPABASE_SERVICE_ROLE_KEY',
            'API_KEY_ENCRYPTION_KEY',
            'FLASK_SECRET_KEY'
        ]
        
        missing_keys = []
        for key in required_keys:
            # Handle special case where env var name differs from attribute name
            attr_name = 'SUPABASE_ANON_KEY' if key == 'SUPABASE_API_KEY' else key
            if not getattr(self, attr_name):
                missing_keys.append(key)
        
        if missing_keys:
            print(f"⚠️ Missing environment variables: {', '.join(missing_keys)}")
            print("💡 Please configure these in Render dashboard for full functionality.")
            print("🚨 Running in limited mode - some features may not work.")
            # Don't exit in production, allow fallback mode
            if self.FLASK_ENV != 'production':
                sys.exit(1)
    
    def _init_encryption(self):
        """Initialize encryption key for API credentials"""
        try:
            if not self.API_KEY_ENCRYPTION_KEY:
                # Generate fallback key for limited mode
                print("⚠️ No encryption key provided, using fallback")
                fallback_key = "fallback-key-for-testing-only-do-not-use-in-production"
                key_bytes = fallback_key.encode()[:32].ljust(32, b'0')
                self.encryption_key = base64.urlsafe_b64encode(key_bytes)
            elif len(self.API_KEY_ENCRYPTION_KEY) == 44:  # Base64 encoded 32 bytes
                self.encryption_key = self.API_KEY_ENCRYPTION_KEY.encode()
            else:
                # Generate key from provided string
                key_bytes = self.API_KEY_ENCRYPTION_KEY.encode()[:32].ljust(32, b'0')
                self.encryption_key = base64.urlsafe_b64encode(key_bytes)
            
            self.cipher_suite = Fernet(self.encryption_key)
            # Encryption initialized
            
        except Exception as e:
            print(f"❌ Failed to initialize encryption: {e}")
            print("💡 Using minimal encryption for fallback mode")
            # Create minimal encryption for fallback
            fallback_key = "minimal-fallback-key-for-emergency-only-not-secure"
            key_bytes = fallback_key.encode()[:32].ljust(32, b'0')
            self.encryption_key = base64.urlsafe_b64encode(key_bytes)
            self.cipher_suite = Fernet(self.encryption_key)
    
    def _init_supabase(self):
        """Initialize Supabase clients"""
        try:
            if not self.SUPABASE_URL or not self.SUPABASE_ANON_KEY:
                print("⚠️ Supabase configuration missing, using mock client")
                self.supabase_client = None
                self.supabase_admin = None
                return
            
            # Lazy import of supabase to avoid blocking at module load time
            try:
                from supabase import create_client
            except ImportError as e:
                print(f"⚠️ Supabase library not available: {e}")
                self.supabase_client = None
                self.supabase_admin = None
                return
                
            # Client for public operations (user-facing)
            self.supabase_client = create_client(
                self.SUPABASE_URL, 
                self.SUPABASE_ANON_KEY
            )
            
            # Admin client for server operations
            if self.SUPABASE_SERVICE_ROLE_KEY:
                self.supabase_admin = create_client(
                    self.SUPABASE_URL, 
                    self.SUPABASE_SERVICE_ROLE_KEY
                )
            else:
                self.supabase_admin = self.supabase_client
            
            # Supabase clients initialized
            
        except Exception as e:
            print(f"❌ Failed to initialize Supabase: {e}")
            print("💡 Running without database - limited functionality")
            self.supabase_client = None
            self.supabase_admin = None
    
    def encrypt_credentials(self, credentials: Dict[str, Any]) -> str:
        """Encrypt user credentials for secure storage"""
        try:
            credentials_json = json.dumps(credentials)
            encrypted_bytes = self.cipher_suite.encrypt(credentials_json.encode())
            return base64.urlsafe_b64encode(encrypted_bytes).decode()
        except Exception as e:
            raise ValueError(f"Failed to encrypt credentials: {e}")
    
    def decrypt_credentials(self, encrypted_credentials: str) -> Dict[str, Any]:
        """Decrypt user credentials from storage"""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_credentials.encode())
            decrypted_bytes = self.cipher_suite.decrypt(encrypted_bytes)
            return json.loads(decrypted_bytes.decode())
        except Exception as e:
            print(f"⚠️ Failed to decrypt credentials: {e}")
            return {}
    
    def encrypt_user_identifier(self, identifier: str) -> str:
        """Encrypt user identifier (email or user_id) for URL generation"""
        try:
            encrypted_bytes = self.cipher_suite.encrypt(identifier.encode())
            # Use URL-safe base64 encoding and remove padding for clean URLs
            encrypted_str = base64.urlsafe_b64encode(encrypted_bytes).decode().rstrip('=')
            return encrypted_str
        except Exception as e:
            raise ValueError(f"Failed to encrypt user identifier: {e}")
    
    def decrypt_user_identifier(self, encrypted_identifier: str) -> str:
        """Decrypt user identifier from URL parameter"""
        try:
            # Add back padding if needed
            padding = 4 - (len(encrypted_identifier) % 4)
            if padding != 4:
                encrypted_identifier += '=' * padding
            
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_identifier.encode())
            decrypted_bytes = self.cipher_suite.decrypt(encrypted_bytes)
            return decrypted_bytes.decode()
        except Exception as e:
            print(f"⚠️ Failed to decrypt user identifier: {e}")
            return ""
    
    def get_client_for_user(self, user_id: Optional[str] = None):
        """Get appropriate Supabase client based on context"""
        if user_id and self.FLASK_ENV == 'production':
            # Use user context for RLS
            return self.supabase_client
        else:
            # Use admin client for server operations
            return self.supabase_admin
    
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.FLASK_ENV == 'production'
    
    def print_config_status(self):
        """Print configuration status for debugging"""
        print("\n🔧 NotionFlow Configuration Status:")
        print(f"   Environment: {self.FLASK_ENV}")
        print(f"   Debug Mode: {self.DEBUG}")
        print(f"   Supabase URL: {self.SUPABASE_URL}")
        print(f"   Anon Key: {'✅ Set' if self.SUPABASE_ANON_KEY else '❌ Missing'}")
        print(f"   Service Key: {'✅ Set' if self.SUPABASE_SERVICE_ROLE_KEY else '❌ Missing'}")
        print(f"   Encryption: {'✅ Ready' if hasattr(self, 'cipher_suite') else '❌ Failed'}")
        print()

# Global configuration instance - lazy initialization
_config = None

def get_config():
    """Get or create the global configuration instance"""
    global _config
    if _config is None:
        _config = Config()
    return _config

# For backward compatibility, create a property-like access
class ConfigProxy:
    def __getattr__(self, name):
        return getattr(get_config(), name)

config = ConfigProxy()

# Helper functions for backward compatibility
def get_supabase_client():
    """Get Supabase client for general use"""
    return config.supabase_client

def get_supabase_admin():
    """Get Supabase admin client"""
    return config.supabase_admin

def encrypt_api_key(credentials: Dict[str, Any]) -> str:
    """Encrypt API credentials"""
    return config.encrypt_credentials(credentials)

def decrypt_api_key(encrypted_credentials: str) -> Dict[str, Any]:
    """Decrypt API credentials"""
    return config.decrypt_credentials(encrypted_credentials)

def encrypt_user_id(user_identifier: str) -> str:
    """Encrypt user identifier for URL generation"""
    return config.encrypt_user_identifier(user_identifier)

def decrypt_user_id(encrypted_identifier: str) -> str:
    """Decrypt user identifier from URL parameter"""
    return config.decrypt_user_identifier(encrypted_identifier)