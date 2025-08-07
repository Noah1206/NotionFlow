/**
 * 🔐 Unified Authentication Service for NotionFlow
 * Handles login, registration, and session management
 */

class AuthService {
    constructor() {
        this.baseURL = window.location.hostname === 'localhost' ? 'http://localhost:5003' : '';
        this.apiURL = `${this.baseURL}/api/auth`;
    }

    /**
     * 🔐 User login - supports email or username
     */
    async login(loginIdentifier, password) {
        try {
            const response = await fetch(`${this.apiURL}/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email: loginIdentifier, password }),
                credentials: 'include'
            });

            const result = await response.json();

            if (response.ok && result.success) {
                // Store user info in session storage
                sessionStorage.setItem('user_id', result.user.id);
                sessionStorage.setItem('user_email', result.user.email);
                if (result.user.username) {
                    sessionStorage.setItem('username', result.user.username);
                }
                
                return {
                    success: true,
                    message: '로그인 성공!',
                    user: result.user,
                    token: result.token
                };
            } else {
                return {
                    success: false,
                    message: result.error || '로그인에 실패했습니다.'
                };
            }
        } catch (error) {
            console.error('Login error:', error);
            return {
                success: false,
                message: '서버 연결 오류. 잠시 후 다시 시도해주세요.'
            };
        }
    }

    /**
     * 📝 User registration
     */
    async register(email, password, username = '', displayName = '') {
        try {
            const response = await fetch(`${this.apiURL}/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    email, 
                    password, 
                    username, 
                    display_name: displayName 
                }),
                credentials: 'include'
            });

            const result = await response.json();

            if (response.ok && result.success) {
                // Store user info in session storage
                sessionStorage.setItem('user_id', result.user.id);
                sessionStorage.setItem('user_email', result.user.email);
                if (result.user.username) {
                    sessionStorage.setItem('username', result.user.username);
                }
                
                return {
                    success: true,
                    message: '회원가입 성공!',
                    user: result.user,
                    token: result.token
                };
            } else {
                return {
                    success: false,
                    message: result.error || '회원가입에 실패했습니다.'
                };
            }
        } catch (error) {
            console.error('Registration error:', error);
            return {
                success: false,
                message: '서버 연결 오류. 잠시 후 다시 시도해주세요.'
            };
        }
    }

    /**
     * 🚪 User logout
     */
    async logout() {
        try {
            await fetch(`${this.apiURL}/logout`, {
                method: 'POST',
                credentials: 'include'
            });

            // Clear session storage
            sessionStorage.clear();
            
            return {
                success: true,
                message: '로그아웃 되었습니다.'
            };
        } catch (error) {
            console.error('Logout error:', error);
            // Clear session storage even if server request fails
            sessionStorage.clear();
            return {
                success: true,
                message: '로그아웃 되었습니다.'
            };
        }
    }

    /**
     * 🔍 Check authentication status
     */
    async isAuthenticated() {
        try {
            // Check if we're in a redirect loop prevention state
            if (sessionStorage.getItem('redirect_from_login') === 'true') {
                sessionStorage.removeItem('redirect_from_login');
                return false;
            }
            
            const response = await fetch(`${this.apiURL}/status`, {
                method: 'GET',
                credentials: 'include'
            });

            const result = await response.json();
            return result.authenticated || false;
        } catch (error) {
            console.error('Auth status check error:', error);
            return false;
        }
    }

    /**
     * 👤 Get current user info
     */
    async getCurrentUser() {
        try {
            const response = await fetch(`${this.apiURL}/profile`, {
                method: 'GET',
                credentials: 'include'
            });

            const result = await response.json();
            
            if (response.ok && result.success) {
                return result.profile;
            }
            
            // Return a fallback user profile to prevent infinite loops
            console.warn('API profile failed, using fallback');
            return {
                id: sessionStorage.getItem('user_id') || 'unknown',
                email: sessionStorage.getItem('user_email') || 'unknown@example.com',
                username: sessionStorage.getItem('username') || 'user',
                display_name: 'User'
            };
        } catch (error) {
            console.error('Get current user error:', error);
            // Return fallback profile
            return {
                id: sessionStorage.getItem('user_id') || 'unknown',
                email: sessionStorage.getItem('user_email') || 'unknown@example.com',
                username: sessionStorage.getItem('username') || 'user',
                display_name: 'User'
            };
        }
    }

    /**
     * 🏠 Get user dashboard URL (Enhanced with User ID caching)
     */
    async getUserDashboardURL(user = null) {
        try {
            // Try to get cached user dashboard URL from session
            const response = await fetch(`${this.baseURL}/api/user/dashboard-url`, {
                method: 'GET',
                credentials: 'include'
            });

            if (response.ok) {
                const result = await response.json();
                if (result.success && result.dashboard_url) {
                    
                    // Store in sessionStorage for quick access
                    sessionStorage.setItem('dashboard_url', result.dashboard_url);
                    sessionStorage.setItem('cached_user_id', result.user_id);
                    sessionStorage.setItem('encrypted_user_id', result.encrypted_user_id);
                    
                    // Return the dashboard URL as is
                    return result.dashboard_url;
                }
            }
            
            // If API fails, return fallback dashboard URL to prevent infinite loops
            console.warn('Dashboard URL API failed, using fallback');
            return '/dashboard';

            // Fallback: If API fails, try to get user info and generate URL
            if (!user) {
                user = await this.getCurrentUser();
            }

            if (user && user.email) {
                // Try the old email-based URL generation as fallback
                const response = await fetch(`${this.baseURL}/api/dashboard-url`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ email: user.email }),
                    credentials: 'include'
                });
                
                const result = await response.json();
                if (result.success) {
                    // Return the dashboard URL as is
                    return result.dashboard_url;
                }
            }
            
            // Final fallback to dashboard with calendar section
            return '/dashboard?section=calendar';
            
        } catch (error) {
            console.error('Error getting dashboard URL:', error);
            return '/dashboard?section=calendar';
        }
    }

    /**
     * 📊 Get user dashboard information (NEW)
     */
    async getDashboardInfo() {
        try {
            const response = await fetch(`${this.baseURL}/api/user/dashboard-url`, {
                method: 'GET',
                credentials: 'include'
            });

            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    return {
                        success: true,
                        user_id: result.user_id,
                        dashboard_url: result.dashboard_url,
                        encrypted_user_id: result.encrypted_user_id
                    };
                }
            }

            return { success: false };
        } catch (error) {
            console.error('Error getting dashboard info:', error);
            return { success: false };
        }
    }

    /**
     * 📱 Display dashboard URL to user (NEW)
     */
    async showDashboardURL() {
        try {
            const info = await this.getDashboardInfo();
            if (info.success) {
                
                return info;
            }
        } catch (error) {
            console.error('Error showing dashboard URL:', error);
        }
        
        return null;
    }

    /**
     * 🔄 Refresh session
     */
    async refreshSession() {
        try {
            const response = await fetch(`${this.apiURL}/refresh`, {
                method: 'POST',
                credentials: 'include'
            });

            const result = await response.json();
            return result.success || false;
        } catch (error) {
            console.error('Session refresh error:', error);
            return false;
        }
    }

    /**
     * 📧 Check username availability
     */
    async checkUsernameAvailability(username) {
        try {
            const response = await fetch(`${this.baseURL}/api/username/check`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username }),
                credentials: 'include'
            });

            const result = await response.json();
            return result;
        } catch (error) {
            console.error('Username check error:', error);
            return {
                success: false,
                available: false,
                message: '사용자명 확인 중 오류가 발생했습니다.'
            };
        }
    }

    /**
     * 💡 Get username suggestions
     */
    async getUsernameSuggestions(email) {
        try {
            const response = await fetch(`${this.baseURL}/api/username/suggestions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email }),
                credentials: 'include'
            });

            const result = await response.json();
            return result;
        } catch (error) {
            console.error('Username suggestions error:', error);
            return {
                success: false,
                suggestions: []
            };
        }
    }

    /**
     * 👤 Create user profile
     */
    async createUserProfile(userId, username, displayName = '') {
        try {
            const response = await fetch(`${this.baseURL}/api/profile`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    user_id: userId, 
                    username, 
                    display_name: displayName 
                }),
                credentials: 'include'
            });

            const result = await response.json();
            return result;
        } catch (error) {
            console.error('Create profile error:', error);
            return {
                success: false,
                message: '프로필 생성 중 오류가 발생했습니다.'
            };
        }
    }
}

// Create and make available globally
const authService = new AuthService();
window.authService = authService;