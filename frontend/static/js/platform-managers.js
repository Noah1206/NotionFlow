/**
 * Platform-specific managers for clean separation of logic
 * Each platform has its own independent state management
 */

// Base Platform Manager class
class PlatformManager {
    constructor(platform) {
        this.platform = platform;
        this.card = document.querySelector(`[data-platform="${platform}"]`);
        if (!this.card) {
            console.error(`Platform card not found for: ${platform}`);
            return;
        }
        
        // DOM elements
        this.statusElement = this.card.querySelector('.platform-status');
        this.connectBtn = this.card.querySelector('.platform-connect-btn');
        this.oneClickBtn = this.card.querySelector('.one-click-btn-small');
        this.syncBtn = this.card.querySelector('.platform-sync-btn');
        
        // Bind methods
        this.updateStatus = this.updateStatus.bind(this);
        this.connect = this.connect.bind(this);
        this.disconnect = this.disconnect.bind(this);
        this.checkStatus = this.checkStatus.bind(this);
    }
    
    // Update platform status display
    updateStatus(status) {
        if (!this.statusElement) return;
        
        this.statusElement.className = `platform-status ${status}`;
        
        switch (status) {
            case 'connected':
                this.statusElement.innerHTML = '<span class="status-dot"></span>연결됨';
                this.showConnectedState();
                break;
            case 'logged_in':
                this.statusElement.innerHTML = '<span class="status-dot"></span>로그인됨';
                this.showLoggedInState();
                break;
            case 'disconnected':
            default:
                this.statusElement.innerHTML = '<span class="status-dot"></span>연결되지 않음';
                this.showDisconnectedState();
                break;
        }
    }
    
    // Show connected state UI
    showConnectedState() {
        // Hide connect button
        if (this.connectBtn) {
            this.connectBtn.style.display = 'none';
            this.connectBtn.style.visibility = 'hidden';
        }
        
        // Change one-click button to disconnect
        if (this.oneClickBtn) {
            this.oneClickBtn.className = 'one-click-disconnect-btn';
            this.oneClickBtn.onclick = () => this.disconnect();
            this.oneClickBtn.innerHTML = `
                <span class="btn-text">연결해제</span>
                <div class="btn-loader" style="display: none;">
                    <div class="loader-spinner"></div>
                </div>
            `;
        }
        
        // Show sync button
        if (this.syncBtn) {
            this.syncBtn.style.display = 'inline-flex';
        }
    }
    
    // Show logged in state UI
    showLoggedInState() {
        // Show connect button
        if (this.connectBtn) {
            this.connectBtn.style.display = 'inline-flex';
            this.connectBtn.style.visibility = 'visible';
            this.connectBtn.disabled = false;
        }
        
        // Keep one-click button as is
        if (this.oneClickBtn) {
            this.oneClickBtn.className = 'one-click-btn-small';
            this.oneClickBtn.onclick = () => this.connect();
        }
        
        // Hide sync button
        if (this.syncBtn) {
            this.syncBtn.style.display = 'none';
        }
    }
    
    // Show disconnected state UI
    showDisconnectedState() {
        // Show connect button
        if (this.connectBtn) {
            this.connectBtn.style.display = 'inline-flex';
            this.connectBtn.style.visibility = 'visible';
            this.connectBtn.disabled = false;
        }
        
        // Reset one-click button
        if (this.oneClickBtn) {
            this.oneClickBtn.className = 'one-click-btn-small';
            this.oneClickBtn.onclick = () => this.connect();
            this.oneClickBtn.innerHTML = `
                <span class="btn-text">원클릭</span>
                <div class="btn-loader" style="display: none;">
                    <div class="loader-spinner"></div>
                </div>
            `;
        }
        
        // Hide sync button
        if (this.syncBtn) {
            this.syncBtn.style.display = 'none';
        }
    }
    
    // Show loading state
    showLoading(button) {
        if (!button) return;
        const buttonText = button.querySelector('.btn-text');
        const loader = button.querySelector('.btn-loader');
        
        button.disabled = true;
        if (buttonText) buttonText.style.display = 'none';
        if (loader) loader.style.display = 'inline-block';
    }
    
    // Hide loading state
    hideLoading(button) {
        if (!button) return;
        const buttonText = button.querySelector('.btn-text');
        const loader = button.querySelector('.btn-loader');
        
        button.disabled = false;
        if (buttonText) buttonText.style.display = 'inline';
        if (loader) loader.style.display = 'none';
    }
    
    // Show notification
    showNotification(message, type = 'info') {
        if (typeof showNotification === 'function') {
            showNotification(message, type);
        } else {
            console.log(`${type.toUpperCase()}: ${message}`);
        }
    }
    
    // Get Korean platform name
    getKoreanName() {
        const names = {
            'notion': 'Notion',
            'google': 'Google Calendar',
            'apple': 'Apple Calendar',
            'outlook': 'Microsoft Outlook',
            'slack': 'Slack'
        };
        return names[this.platform] || this.platform;
    }
    
    // Abstract methods to be overridden
    async connect() {
        throw new Error('connect() method must be implemented');
    }
    
    async disconnect() {
        throw new Error('disconnect() method must be implemented');
    }
    
    async checkStatus() {
        throw new Error('checkStatus() method must be implemented');
    }
}

// Notion Platform Manager
class NotionManager extends PlatformManager {
    constructor() {
        super('notion');
    }
    
    async connect() {
        this.showLoading(this.oneClickBtn);
        
        try {
            // Start OAuth process
            const authUrl = `/auth/notion`;
            const popup = window.open(authUrl, 'notion_auth', 'width=500,height=600,scrollbars=yes,resizable=yes');
            
            const result = await this.waitForOAuth(popup);
            
            if (result.success) {
                this.updateStatus('connected');
                this.showNotification(`${this.getKoreanName()} 연결 완료!`, 'success');
                
                // Mark as connected in backend
                await this.markConnected();
            } else {
                throw new Error(result.error || 'OAuth 실패');
            }
            
        } catch (error) {
            console.error('Notion connection error:', error);
            this.showNotification(`${this.getKoreanName()} 연결 실패: ${error.message}`, 'error');
            this.updateStatus('disconnected');
        } finally {
            this.hideLoading(this.oneClickBtn);
        }
    }
    
    async disconnect() {
        if (!confirm(`${this.getKoreanName()} 연결을 해제하시겠습니까?`)) {
            return;
        }
        
        this.showLoading(this.oneClickBtn);
        
        try {
            const response = await fetch(`/api/platform/notion/disconnect`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            if (response.ok) {
                this.updateStatus('disconnected');
                this.showNotification(`${this.getKoreanName()} 연결이 해제되었습니다.`, 'success');
            } else {
                const error = await response.json();
                throw new Error(error.error || '연결 해제 실패');
            }
            
        } catch (error) {
            console.error('Notion disconnection error:', error);
            this.showNotification(`연결 해제 중 오류: ${error.message}`, 'error');
        } finally {
            this.hideLoading(this.oneClickBtn);
        }
    }
    
    async checkStatus() {
        try {
            const response = await fetch('/api/dashboard/platforms');
            if (response.ok) {
                const data = await response.json();
                const status = data.platforms?.notion;
                
                if (status && status.configured && status.enabled) {
                    this.updateStatus('connected');
                } else {
                    this.updateStatus('disconnected');
                }
            }
        } catch (error) {
            console.error('Error checking Notion status:', error);
            this.updateStatus('disconnected');
        }
    }
    
    async waitForOAuth(popup) {
        return new Promise((resolve, reject) => {
            const messageHandler = (event) => {
                if (event.origin !== window.location.origin) return;
                
                if (event.data.type === 'oauth_success' && event.data.platform === 'notion') {
                    window.removeEventListener('message', messageHandler);
                    popup.close();
                    resolve({ success: true });
                } else if (event.data.type === 'oauth_error' && event.data.platform === 'notion') {
                    window.removeEventListener('message', messageHandler);
                    popup.close();
                    resolve({ success: false, error: event.data.error });
                }
            };
            
            window.addEventListener('message', messageHandler);
            
            // Check if popup is closed
            const checkClosed = setInterval(() => {
                if (popup.closed) {
                    clearInterval(checkClosed);
                    window.removeEventListener('message', messageHandler);
                    reject(new Error('OAuth 창이 닫혔습니다'));
                }
            }, 1000);
        });
    }
    
    async markConnected() {
        try {
            await fetch(`/api/platform/notion/connect`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
        } catch (error) {
            console.error('Error marking Notion as connected:', error);
        }
    }
}

// Google Calendar Platform Manager
class GoogleManager extends PlatformManager {
    constructor() {
        super('google');
    }
    
    async connect() {
        this.showLoading(this.oneClickBtn);
        
        // Clear manual disconnect flag when user explicitly clicks connect
        localStorage.removeItem('google_manually_disconnected');
        console.log('User clicked connect - cleared manual disconnect flag');
        
        try {
            // Start OAuth process
            const authUrl = `/auth/google`;
            const popup = window.open(authUrl, 'google_auth', 'width=500,height=600,scrollbars=yes,resizable=yes');
            
            const result = await this.waitForOAuth(popup);
            
            if (result.success) {
                // Check if user manually disconnected Google Calendar
                const manuallyDisconnected = localStorage.getItem('google_manually_disconnected');
                if (manuallyDisconnected === 'true') {
                    console.log('Google Calendar was manually disconnected - skipping auto-connection');
                    this.showNotification('Google OAuth 연결 완료 (캘린더 연동 해제 상태 유지)', 'info');
                } else {
                    // Show calendar selection modal only if not manually disconnected
                    await this.showCalendarSelection();
                }
            } else {
                throw new Error(result.error || 'OAuth 실패');
            }
            
        } catch (error) {
            console.error('Google connection error:', error);
            this.showNotification(`${this.getKoreanName()} 연결 실패: ${error.message}`, 'error');
            this.updateStatus('disconnected');
        } finally {
            this.hideLoading(this.oneClickBtn);
        }
    }
    
    async disconnect() {
        if (!confirm(`${this.getKoreanName()} 연결을 해제하시겠습니까?`)) {
            return;
        }
        
        this.showLoading(this.oneClickBtn);
        
        try {
            const response = await fetch(`/api/platform/google/disconnect`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            if (response.ok) {
                this.updateStatus('disconnected');
                this.showNotification(`${this.getKoreanName()} 연결이 해제되었습니다.`, 'success');
            } else {
                const error = await response.json();
                throw new Error(error.error || '연결 해제 실패');
            }
            
        } catch (error) {
            console.error('Google disconnection error:', error);
            this.showNotification(`연결 해제 중 오류: ${error.message}`, 'error');
        } finally {
            this.hideLoading(this.oneClickBtn);
        }
    }
    
    async checkStatus() {
        try {
            const response = await fetch('/api/dashboard/platforms');
            if (response.ok) {
                const data = await response.json();
                const status = data.platforms?.google;
                
                if (status && status.configured && status.enabled) {
                    this.updateStatus('connected');
                } else {
                    this.updateStatus('disconnected');
                }
            }
        } catch (error) {
            console.error('Error checking Google status:', error);
            this.updateStatus('disconnected');
        }
    }
    
    async waitForOAuth(popup) {
        return new Promise((resolve, reject) => {
            const messageHandler = (event) => {
                if (event.origin !== window.location.origin) return;
                
                if (event.data.type === 'oauth_success' && event.data.platform === 'google') {
                    window.removeEventListener('message', messageHandler);
                    popup.close();
                    resolve({ success: true });
                } else if (event.data.type === 'oauth_error' && event.data.platform === 'google') {
                    window.removeEventListener('message', messageHandler);
                    popup.close();
                    resolve({ success: false, error: event.data.error });
                }
            };
            
            window.addEventListener('message', messageHandler);
            
            // Check if popup is closed
            const checkClosed = setInterval(() => {
                if (popup.closed) {
                    clearInterval(checkClosed);
                    window.removeEventListener('message', messageHandler);
                    reject(new Error('OAuth 창이 닫혔습니다'));
                }
            }, 1000);
        });
    }
    
    async showCalendarSelection() {
        try {
            // Load calendars
            const response = await fetch('/api/google-calendars');
            if (!response.ok) {
                throw new Error('캘린더 목록을 불러올 수 없습니다');
            }
            
            const data = await response.json();
            if (!data.success || !data.calendars.length) {
                throw new Error('사용 가능한 캘린더가 없습니다');
            }
            
            // Show modal (assuming modal exists)
            if (typeof showCalendarSelectionModal === 'function') {
                showCalendarSelectionModal('google');
            } else {
                // Auto-select primary calendar
                const primaryCalendar = data.calendars.find(cal => cal.primary) || data.calendars[0];
                await this.connectCalendar(primaryCalendar.id);
            }
            
        } catch (error) {
            console.error('Calendar selection error:', error);
            this.showNotification(`캘린더 선택 중 오류: ${error.message}`, 'error');
        }
    }
    
    async connectCalendar(calendarId) {
        try {
            // Mark as connected in backend
            await fetch(`/api/platform/google/connect`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ calendar_id: calendarId })
            });
            
            this.updateStatus('connected');
            this.showNotification(`${this.getKoreanName()} 연결 완료!`, 'success');
            
        } catch (error) {
            console.error('Calendar connection error:', error);
            this.showNotification(`캘린더 연결 중 오류: ${error.message}`, 'error');
        }
    }
}

// Apple Calendar Platform Manager  
class AppleManager extends PlatformManager {
    constructor() {
        super('apple');
    }
    
    async connect() {
        this.showNotification('Apple Calendar 연결은 준비 중입니다.', 'info');
    }
    
    async disconnect() {
        this.showNotification('Apple Calendar 연결해제는 준비 중입니다.', 'info');
    }
    
    async checkStatus() {
        this.updateStatus('disconnected');
    }
}

// Outlook Platform Manager
class OutlookManager extends PlatformManager {
    constructor() {
        super('outlook');
    }
    
    async connect() {
        this.showNotification('Microsoft Outlook 연결은 준비 중입니다.', 'info');
    }
    
    async disconnect() {
        this.showNotification('Microsoft Outlook 연결해제는 준비 중입니다.', 'info');
    }
    
    async checkStatus() {
        this.updateStatus('disconnected');
    }
}

// Slack Platform Manager
class SlackManager extends PlatformManager {
    constructor() {
        super('slack');
    }
    
    async connect() {
        this.showNotification('Slack 연결은 준비 중입니다.', 'info');
    }
    
    async disconnect() {
        this.showNotification('Slack 연결해제는 준비 중입니다.', 'info');
    }
    
    async checkStatus() {
        this.updateStatus('disconnected');
    }
}

// Platform Manager Factory
class PlatformManagerFactory {
    static managers = {};
    
    static create(platform) {
        if (this.managers[platform]) {
            return this.managers[platform];
        }
        
        switch (platform) {
            case 'notion':
                this.managers[platform] = new NotionManager();
                break;
            case 'google':
                this.managers[platform] = new GoogleManager();
                break;
            case 'apple':
                this.managers[platform] = new AppleManager();
                break;
            case 'outlook':
                this.managers[platform] = new OutlookManager();
                break;
            case 'slack':
                this.managers[platform] = new SlackManager();
                break;
            default:
                console.error(`Unknown platform: ${platform}`);
                return null;
        }
        
        return this.managers[platform];
    }
    
    static get(platform) {
        return this.managers[platform] || null;
    }
    
    static checkAllStatuses() {
        const platforms = ['notion', 'google', 'apple', 'outlook', 'slack'];
        platforms.forEach(platform => {
            const manager = this.create(platform);
            if (manager) {
                manager.checkStatus();
            }
        });
    }
}

// Global functions for backward compatibility
window.connectPlatform = function(platform) {
    const manager = PlatformManagerFactory.create(platform);
    if (manager) {
        if (manager.connectBtn) {
            manager.connect();
        } else {
            console.error(`Connect button not found for platform: ${platform}`);
        }
    }
};

window.oneClickConnect = function(platform) {
    const manager = PlatformManagerFactory.create(platform);
    if (manager) {
        manager.connect();
    }
};

window.oneClickDisconnect = function(platform) {
    const manager = PlatformManagerFactory.create(platform);
    if (manager) {
        manager.disconnect();
    }
};

// Initialize all platform managers on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing platform managers...');
    
    // Check status for all platforms
    setTimeout(() => {
        PlatformManagerFactory.checkAllStatuses();
    }, 1000);
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        PlatformManager,
        NotionManager,
        GoogleManager,
        AppleManager,
        OutlookManager,
        SlackManager,
        PlatformManagerFactory
    };
}