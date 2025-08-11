/**
 * 🔗 ConnectButton Component
 * Smart connect/disconnect button with loading states and platform-specific logic
 */

class ConnectButton {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            calendarId: null,
            platform: null,
            platformName: null,
            initialState: 'disconnected', // 'connected', 'disconnected', 'loading'
            size: 'medium', // 'small', 'medium', 'large'
            variant: 'primary', // 'primary', 'secondary', 'outline'
            showIcon: true,
            showText: true,
            customText: null,
            onConnect: null,
            onDisconnect: null,
            onError: null,
            ...options
        };
        
        this.state = this.options.initialState;
        this.isLoading = false;
        
        this.init();
    }
    
    init() {
        if (!this.options.calendarId || !this.options.platform) {
            console.error('ConnectButton requires calendarId and platform options');
            return;
        }
        
        this.render();
        this.attachEventListeners();
    }
    
    render() {
        if (!this.container) return;
        
        const buttonClass = this.getButtonClass();
        const buttonText = this.getButtonText();
        const buttonIcon = this.getButtonIcon();
        
        this.container.innerHTML = `
            <button class="${buttonClass}" 
                    data-platform="${this.options.platform}"
                    data-calendar="${this.options.calendarId}"
                    ${this.isLoading || this.state === 'loading' ? 'disabled' : ''}>
                <div class="connect-btn-content">
                    ${this.options.showIcon ? `<span class="connect-btn-icon">${buttonIcon}</span>` : ''}
                    ${this.options.showText ? `<span class="connect-btn-text">${buttonText}</span>` : ''}
                    <div class="connect-btn-loader" style="display: ${this.isLoading ? 'flex' : 'none'};">
                        <div class="loader-spinner"></div>
                    </div>
                </div>
            </button>
        `;
        
        // Re-attach event listeners
        this.attachEventListeners();
    }
    
    getButtonClass() {
        const baseClass = 'connect-button';
        const stateClass = `connect-button-${this.state}`;
        const sizeClass = `connect-button-${this.options.size}`;
        const variantClass = `connect-button-${this.options.variant}`;
        
        return `${baseClass} ${stateClass} ${sizeClass} ${variantClass}`;
    }
    
    getButtonText() {
        if (this.options.customText) return this.options.customText;
        
        if (this.isLoading) {
            return this.state === 'connected' ? '연결 해제 중...' : '연결 중...';
        }
        
        switch (this.state) {
            case 'connected':
                return '연결 해제';
            case 'disconnected':
                return '연결';
            case 'error':
                return '재시도';
            default:
                return '연결';
        }
    }
    
    getButtonIcon() {
        if (this.isLoading) {
            return '';
        }
        
        switch (this.state) {
            case 'connected':
                return '🔗';
            case 'disconnected':
                return '🔌';
            case 'error':
                return '⚠️';
            default:
                return '🔌';
        }
    }
    
    attachEventListeners() {
        const button = this.container.querySelector('.connect-button');
        if (button) {
            button.addEventListener('click', this.handleClick.bind(this));
        }
    }
    
    async handleClick(event) {
        event.preventDefault();
        
        if (this.isLoading) return;
        
        if (this.state === 'connected') {
            await this.disconnect();
        } else {
            await this.connect();
        }
    }
    
    async connect() {
        this.setLoadingState(true);
        
        try {
            const response = await fetch(`/api/calendars/${this.options.calendarId}/connect`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    platform: this.options.platform,
                    sync_config: {
                        sync_enabled: true,
                        sync_direction: 'both',
                        sync_frequency: 15,
                        auto_sync: true
                    }
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.setState('connected');
                this.showNotification(data.message || '연결되었습니다', 'success');
                
                if (this.options.onConnect) {
                    this.options.onConnect({
                        platform: this.options.platform,
                        calendarId: this.options.calendarId,
                        response: data
                    });
                }
            } else {
                throw new Error(data.error || '연결에 실패했습니다');
            }
            
        } catch (error) {
            console.error('Connection failed:', error);
            this.setState('error');
            this.showNotification(error.message || '연결 중 오류가 발생했습니다', 'error');
            
            if (this.options.onError) {
                this.options.onError({
                    platform: this.options.platform,
                    calendarId: this.options.calendarId,
                    error: error.message,
                    action: 'connect'
                });
            }
            
            // Reset to disconnected state after a delay
            setTimeout(() => {
                if (this.state === 'error') {
                    this.setState('disconnected');
                }
            }, 3000);
            
        } finally {
            this.setLoadingState(false);
        }
    }
    
    async disconnect() {
        if (!confirm(`${this.options.platformName || this.options.platform} 연결을 해제하시겠습니까?`)) {
            return;
        }
        
        this.setLoadingState(true);
        
        try {
            const response = await fetch(`/api/calendars/${this.options.calendarId}/disconnect/${this.options.platform}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.setState('disconnected');
                this.showNotification(data.message || '연결이 해제되었습니다', 'success');
                
                if (this.options.onDisconnect) {
                    this.options.onDisconnect({
                        platform: this.options.platform,
                        calendarId: this.options.calendarId,
                        response: data
                    });
                }
            } else {
                throw new Error(data.error || '연결 해제에 실패했습니다');
            }
            
        } catch (error) {
            console.error('Disconnection failed:', error);
            this.setState('error');
            this.showNotification(error.message || '연결 해제 중 오류가 발생했습니다', 'error');
            
            if (this.options.onError) {
                this.options.onError({
                    platform: this.options.platform,
                    calendarId: this.options.calendarId,
                    error: error.message,
                    action: 'disconnect'
                });
            }
            
            // Reset to connected state after a delay
            setTimeout(() => {
                if (this.state === 'error') {
                    this.setState('connected');
                }
            }, 3000);
            
        } finally {
            this.setLoadingState(false);
        }
    }
    
    setState(newState) {
        this.state = newState;
        this.render();
    }
    
    setLoadingState(loading) {
        this.isLoading = loading;
        this.render();
    }
    
    // Public methods
    getState() {
        return this.state;
    }
    
    isConnected() {
        return this.state === 'connected';
    }
    
    isDisconnected() {
        return this.state === 'disconnected';
    }
    
    setConnected(connected = true) {
        this.setState(connected ? 'connected' : 'disconnected');
    }
    
    enable() {
        const button = this.container.querySelector('.connect-button');
        if (button) {
            button.disabled = false;
        }
    }
    
    disable() {
        const button = this.container.querySelector('.connect-button');
        if (button) {
            button.disabled = true;
        }
    }
    
    updateOptions(newOptions) {
        this.options = { ...this.options, ...newOptions };
        this.render();
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 16px 24px;
            border-radius: 12px;
            color: white;
            font-weight: 500;
            z-index: 10000;
            transform: translateX(400px);
            transition: transform 0.3s ease;
            ${type === 'success' ? 'background: linear-gradient(135deg, #10b981, #059669);' : ''}
            ${type === 'error' ? 'background: linear-gradient(135deg, #ef4444, #dc2626);' : ''}
            ${type === 'info' ? 'background: linear-gradient(135deg, #3b82f6, #2563eb);' : ''}
        `;
        
        document.body.appendChild(notification);
        
        // Animation
        setTimeout(() => notification.style.transform = 'translateX(0)', 100);
        setTimeout(() => notification.style.transform = 'translateX(400px)', 3000);
        setTimeout(() => document.body.removeChild(notification), 3500);
    }
    
    destroy() {
        // Cleanup event listeners and remove from DOM if needed
        const button = this.container.querySelector('.connect-button');
        if (button) {
            button.removeEventListener('click', this.handleClick);
        }
    }
}

/**
 * ConnectButtonGroup - Manage multiple connect buttons for different platforms
 */
class ConnectButtonGroup {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            calendarId: null,
            platforms: [], // Array of platform objects with {id, name, connected}
            layout: 'grid', // 'grid', 'list', 'inline'
            size: 'medium',
            variant: 'primary',
            onConnect: null,
            onDisconnect: null,
            onError: null,
            ...options
        };
        
        this.buttons = new Map();
        
        this.init();
    }
    
    async init() {
        if (!this.options.calendarId) {
            console.error('ConnectButtonGroup requires calendarId option');
            return;
        }
        
        // Load platform connections if not provided
        if (!this.options.platforms || this.options.platforms.length === 0) {
            await this.loadConnections();
        }
        
        this.render();
        this.createButtons();
    }
    
    async loadConnections() {
        try {
            const response = await fetch(`/api/calendars/${this.options.calendarId}/connections`);
            const data = await response.json();
            
            if (data.success) {
                // Merge connected and available platforms
                const allPlatforms = [];
                
                // Add connected platforms
                Object.entries(data.connected_platforms).forEach(([platformId, platform]) => {
                    allPlatforms.push({
                        id: platformId,
                        name: platform.platform_name,
                        connected: platform.is_connected
                    });
                });
                
                // Add available platforms
                Object.entries(data.available_platforms).forEach(([platformId, platform]) => {
                    allPlatforms.push({
                        id: platformId,
                        name: platform.platform_name,
                        connected: false
                    });
                });
                
                this.options.platforms = allPlatforms;
            }
        } catch (error) {
            console.error('Failed to load connections:', error);
        }
    }
    
    render() {
        if (!this.container) return;
        
        const layoutClass = `connect-button-group connect-button-group-${this.options.layout}`;
        
        const platformItems = this.options.platforms.map(platform => {
            return `
                <div class="connect-button-item" data-platform="${platform.id}">
                    <div class="platform-info">
                        <span class="platform-name">${platform.name}</span>
                        <span class="platform-status ${platform.connected ? 'connected' : 'disconnected'}">
                            ${platform.connected ? '연결됨' : '연결 안됨'}
                        </span>
                    </div>
                    <div class="button-container" id="connect-btn-${platform.id}"></div>
                </div>
            `;
        }).join('');
        
        this.container.innerHTML = `
            <div class="${layoutClass}">
                ${platformItems}
            </div>
        `;
    }
    
    createButtons() {
        this.options.platforms.forEach(platform => {
            const buttonContainer = `connect-btn-${platform.id}`;
            
            const button = new ConnectButton(buttonContainer, {
                calendarId: this.options.calendarId,
                platform: platform.id,
                platformName: platform.name,
                initialState: platform.connected ? 'connected' : 'disconnected',
                size: this.options.size,
                variant: this.options.variant,
                onConnect: (data) => {
                    // Update local state
                    platform.connected = true;
                    this.updatePlatformStatus(platform.id, 'connected');
                    
                    if (this.options.onConnect) {
                        this.options.onConnect(data);
                    }
                },
                onDisconnect: (data) => {
                    // Update local state
                    platform.connected = false;
                    this.updatePlatformStatus(platform.id, 'disconnected');
                    
                    if (this.options.onDisconnect) {
                        this.options.onDisconnect(data);
                    }
                },
                onError: this.options.onError
            });
            
            this.buttons.set(platform.id, button);
        });
    }
    
    updatePlatformStatus(platformId, status) {
        const statusElement = this.container.querySelector(`[data-platform="${platformId}"] .platform-status`);
        if (statusElement) {
            statusElement.className = `platform-status ${status}`;
            statusElement.textContent = status === 'connected' ? '연결됨' : '연결 안됨';
        }
    }
    
    // Public methods
    getButton(platformId) {
        return this.buttons.get(platformId);
    }
    
    getAllButtons() {
        return Array.from(this.buttons.values());
    }
    
    refresh() {
        this.loadConnections().then(() => {
            this.render();
            this.createButtons();
        });
    }
    
    destroy() {
        this.buttons.forEach(button => button.destroy());
        this.buttons.clear();
    }
}

// Export for use in other files
window.ConnectButton = ConnectButton;
window.ConnectButtonGroup = ConnectButtonGroup;