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
                    clearInterval(checkClosed);
                    try {
                        popup.close();
                    } catch (e) {
                        // Cross-Origin 에러 무시 (정상)
                    }
                    resolve({ success: true });
                } else if (event.data.type === 'oauth_error' && event.data.platform === 'notion') {
                    window.removeEventListener('message', messageHandler);
                    clearInterval(checkClosed);
                    try {
                        popup.close();
                    } catch (e) {
                        // Cross-Origin 에러 무시 (정상)
                    }
                    resolve({ success: false, error: event.data.error });
                }
            };

            window.addEventListener('message', messageHandler);

            // Check if popup is closed (with timeout)
            let timeoutCount = 0;
            const maxTimeout = 120; // 2분 타임아웃

            const checkClosed = setInterval(() => {
                timeoutCount++;

                try {
                    if (popup.closed) {
                        clearInterval(checkClosed);
                        window.removeEventListener('message', messageHandler);
                        reject(new Error('OAuth 창이 닫혔습니다'));
                        return;
                    }
                } catch (e) {
                    // Cross-Origin Policy로 popup.closed 접근이 차단됨 (정상 동작)
                    // 메시지 핸들러가 있으므로 계속 대기
                }

                // 타임아웃 체크
                if (timeoutCount >= maxTimeout) {
                    clearInterval(checkClosed);
                    window.removeEventListener('message', messageHandler);
                    try {
                        if (popup && !popup.closed) {
                            popup.close();
                        }
                    } catch (e) {
                        // Cross-Origin 에러 무시
                    }
                    reject(new Error('OAuth 인증 시간이 초과되었습니다'));
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
                // Clear manual disconnection flag on fresh OAuth connection
                localStorage.removeItem('google_manually_disconnected');
                localStorage.removeItem('google_last_connected');
                console.log('Google OAuth success - cleared disconnection flags');
                
                // Check if user manually disconnected Google Calendar
                const manuallyDisconnected = localStorage.getItem('google_manually_disconnected');
                if (manuallyDisconnected === 'true') {
                    console.log('Google Calendar was manually disconnected - skipping auto-connection');
                    this.showNotification('Google OAuth 연결 완료 (캘린더 연동 해제 상태 유지)', 'info');
                } else {
                    // Show calendar selection modal for fresh connections
                    this.showNotification('Google OAuth 연결 완료 - 캘린더 선택 중...', 'success');

                    try {
                        await this.showCalendarSelection();
                    } catch (calendarError) {
                        console.error('Calendar selection failed:', calendarError);
                        // OAuth는 성공했으므로 logged_in 상태 유지
                        this.updateStatus('logged_in');
                        // 에러는 showCalendarSelection에서 이미 표시됨
                    }
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
                    clearInterval(checkClosed);
                    try {
                        popup.close();
                    } catch (e) {
                        // Cross-Origin 에러 무시 (정상)
                    }
                    resolve({ success: true });
                } else if (event.data.type === 'oauth_error' && event.data.platform === 'google') {
                    window.removeEventListener('message', messageHandler);
                    clearInterval(checkClosed);
                    try {
                        popup.close();
                    } catch (e) {
                        // Cross-Origin 에러 무시 (정상)
                    }
                    resolve({ success: false, error: event.data.error });
                }
            };

            window.addEventListener('message', messageHandler);

            // Check if popup is closed (with timeout)
            let timeoutCount = 0;
            const maxTimeout = 120; // 2분 타임아웃

            const checkClosed = setInterval(() => {
                timeoutCount++;

                try {
                    if (popup.closed) {
                        clearInterval(checkClosed);
                        window.removeEventListener('message', messageHandler);
                        reject(new Error('OAuth 창이 닫혔습니다'));
                        return;
                    }
                } catch (e) {
                    // Cross-Origin Policy로 popup.closed 접근이 차단됨 (정상 동작)
                    // 메시지 핸들러가 있으므로 계속 대기
                }

                // 타임아웃 체크
                if (timeoutCount >= maxTimeout) {
                    clearInterval(checkClosed);
                    window.removeEventListener('message', messageHandler);
                    try {
                        if (popup && !popup.closed) {
                            popup.close();
                        }
                    } catch (e) {
                        // Cross-Origin 에러 무시
                    }
                    reject(new Error('OAuth 인증 시간이 초과되었습니다'));
                }
            }, 1000);
        });
    }
    
    async showCalendarSelection() {
        try {
            console.log('📅 [GOOGLE] Fetching calendar list...');

            // Load calendars
            const response = await fetch('/api/google-calendars');
            console.log('📅 [GOOGLE] Calendar API response status:', response.status);

            if (!response.ok) {
                console.error('❌ [GOOGLE] Calendar API request failed:', response.status, response.statusText);
                throw new Error(`캘린더 목록을 불러올 수 없습니다 (${response.status})`);
            }

            const data = await response.json();
            console.log('📅 [GOOGLE] Calendar API response data:', data);

            if (!data.success) {
                console.error('❌ [GOOGLE] Calendar API returned error:', data.error);

                // OAuth 토큰 관련 오류인 경우 재인증 요청
                if (data.error && data.error.includes('OAuth token')) {
                    throw new Error('Google Calendar 인증이 만료되었습니다. 다시 연결해주세요.');
                }

                throw new Error(data.error || '캘린더 목록을 불러오는데 실패했습니다');
            }

            if (!data.calendars || !data.calendars.length) {
                console.warn('⚠️ [GOOGLE] No calendars found');

                // 캘린더가 없는 경우 사용자에게 안내
                this.showNotification(
                    'Google 계정에 캘린더가 없습니다. Google Calendar에서 캘린더를 생성한 후 다시 연결해주세요.',
                    'warning'
                );

                // OAuth는 성공했지만 캘린더가 없으므로 logged_in 상태로 변경
                this.updateStatus('logged_in');
                return;
            }

            console.log(`✅ [GOOGLE] Found ${data.calendars.length} calendars`);

            
            // Enhanced modal display with fallback strategy
            console.log('📅 [GOOGLE] Attempting to show calendar selection modal...');

            // Strategy 1: Try existing modal function
            let modalShown = false;
            if (typeof showCalendarSelectionModal === 'function') {
                try {
                    console.log('📅 [GOOGLE] Using existing showCalendarSelectionModal function');
                    showCalendarSelectionModal('google');

                    // Verify modal is actually visible after a short delay
                    setTimeout(() => {
                        const modal = document.getElementById('calendar-selection-modal');
                        if (!modal || modal.style.display === 'none' || getComputedStyle(modal).display === 'none') {
                            console.log('⚠️ [GOOGLE] Existing modal not visible, creating fallback');
                            this.createFallbackCalendarModal(data.calendars);
                        } else {
                            console.log('✅ [GOOGLE] Existing modal is visible');
                            modalShown = true;
                        }
                    }, 300);

                } catch (modalError) {
                    console.error('❌ [GOOGLE] Error with existing modal function:', modalError);
                    this.createFallbackCalendarModal(data.calendars);
                }
            } else if (typeof window.showCalendarSelectionModal === 'function') {
                try {
                    console.log('📅 [GOOGLE] Using window scope modal function');
                    window.showCalendarSelectionModal('google');

                    // Verify modal visibility
                    setTimeout(() => {
                        const modal = document.getElementById('calendar-selection-modal');
                        if (!modal || modal.style.display === 'none' || getComputedStyle(modal).display === 'none') {
                            console.log('⚠️ [GOOGLE] Window modal not visible, creating fallback');
                            this.createFallbackCalendarModal(data.calendars);
                        } else {
                            console.log('✅ [GOOGLE] Window modal is visible');
                            modalShown = true;
                        }
                    }, 300);
                } catch (modalError) {
                    console.error('❌ [GOOGLE] Error with window modal function:', modalError);
                    this.createFallbackCalendarModal(data.calendars);
                }
            } else {
                // No modal function found, create fallback immediately
                console.log('📅 [GOOGLE] No modal function found, creating fallback...');
                this.createFallbackCalendarModal(data.calendars);
            }
            
        } catch (error) {
            console.error('Calendar selection error:', error);

            // 에러 타입에 따라 다른 알림 표시
            if (error.message.includes('캘린더가 없습니다')) {
                // 캘린더 없음 에러는 이미 처리됨
                return;
            } else if (error.message.includes('인증이 만료')) {
                this.showNotification('Google 인증이 만료되었습니다. 다시 연결해주세요.', 'warning');
            } else {
                this.showNotification(`캘린더 연결 중 오류: ${error.message}`, 'error');
            }

            // 에러 발생 시 예외를 다시 던져서 상위에서 처리할 수 있도록 함
            throw error;
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

    createFallbackCalendarModal(calendars) {
        // Remove any existing modal
        const existingModal = document.getElementById('google-calendar-modal');
        if (existingModal) {
            existingModal.remove();
        }

        // Create modal HTML
        const modal = document.createElement('div');
        modal.id = 'google-calendar-modal';
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.6);
            display: flex !important;
            justify-content: center;
            align-items: center;
            z-index: 999999;
            backdrop-filter: blur(4px);
            animation: fadeIn 0.3s ease-out;
        `;

        const modalContent = document.createElement('div');
        modalContent.style.cssText = `
            background: white;
            border-radius: 16px;
            padding: 32px;
            max-width: 600px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
            position: relative;
            transform: scale(1);
            animation: slideInScale 0.3s ease-out;
        `;

        modalContent.innerHTML = `
            <h2 style="margin: 0 0 16px 0;">📅 Google Calendar 선택</h2>
            <p style="color: #666; margin-bottom: 20px;">동기화할 Google Calendar를 선택해주세요:</p>
            <div id="calendar-list" style="margin-bottom: 20px;">
                ${calendars.map((cal, index) => `
                    <div style="
                        padding: 12px;
                        margin-bottom: 8px;
                        border: 1px solid #e0e0e0;
                        border-radius: 8px;
                        cursor: pointer;
                        transition: all 0.2s;
                    " class="calendar-item" data-calendar-id="${cal.id}" data-index="${index}"
                       onmouseover="this.style.backgroundColor='#f5f5f5'"
                       onmouseout="this.style.backgroundColor='white'">
                        <div style="font-weight: 500;">${cal.name || 'Untitled Calendar'}</div>
                        ${cal.description ? `<div style="color: #666; font-size: 14px; margin-top: 4px;">${cal.description}</div>` : ''}
                        ${cal.is_primary ? '<span style="color: #4285f4; font-size: 12px;">기본 캘린더</span>' : ''}
                    </div>
                `).join('')}
            </div>
            <div style="display: flex; gap: 12px; justify-content: flex-end;">
                <button id="google-modal-cancel" style="
                    background: #f5f5f5;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 6px;
                    cursor: pointer;
                ">취소</button>
                <button id="google-modal-confirm" style="
                    background: #4285f4;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 6px;
                    cursor: pointer;
                    opacity: 0.5;
                " disabled>연결</button>
            </div>
        `;

        // Add CSS animations to document if not already present
        if (!document.querySelector('#google-modal-animations')) {
            const style = document.createElement('style');
            style.id = 'google-modal-animations';
            style.textContent = `
                @keyframes fadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
                @keyframes slideInScale {
                    from {
                        opacity: 0;
                        transform: scale(0.9) translateY(-20px);
                    }
                    to {
                        opacity: 1;
                        transform: scale(1) translateY(0);
                    }
                }
            `;
            document.head.appendChild(style);
        }

        modal.appendChild(modalContent);
        document.body.appendChild(modal);

        // Force display after append
        modal.style.display = 'flex';

        console.log('✅ [GOOGLE] Fallback modal created and displayed');
        console.log('📅 [GOOGLE] Modal element:', modal);
        console.log('📅 [GOOGLE] Modal visibility:', getComputedStyle(modal).display);

        // Add event listeners
        let selectedCalendarId = null;
        const confirmBtn = modalContent.querySelector('#google-modal-confirm');
        const cancelBtn = modalContent.querySelector('#google-modal-cancel');

        modalContent.querySelectorAll('.calendar-item').forEach(item => {
            item.addEventListener('click', () => {
                // Remove previous selection
                modalContent.querySelectorAll('.calendar-item').forEach(el => {
                    el.style.border = '1px solid #e0e0e0';
                });

                // Add selection
                item.style.border = '2px solid #4285f4';
                selectedCalendarId = item.dataset.calendarId;

                // Enable confirm button
                confirmBtn.disabled = false;
                confirmBtn.style.opacity = '1';
            });
        });

        confirmBtn.addEventListener('click', async () => {
            if (selectedCalendarId) {
                await this.connectCalendar(selectedCalendarId);
                modal.remove();
            }
        });

        cancelBtn.addEventListener('click', () => {
            modal.remove();
            this.updateStatus('logged_in');
            this.showNotification('Google Calendar 연결이 취소되었습니다.', 'info');
        });

        // Auto-select primary calendar if exists
        const primaryCalendar = calendars.find(cal => cal.is_primary);
        if (primaryCalendar) {
            const primaryItem = modalContent.querySelector(`[data-calendar-id="${primaryCalendar.id}"]`);
            if (primaryItem) {
                primaryItem.click();
            }
        }
    }
    
    // Google Calendar 동기화 메서드 추가
    async syncCalendarEvents() {
        if (!this.syncBtn) {
            console.error('Sync button not found');
            return;
        }
        
        this.showLoading(this.syncBtn);
        
        try {
            console.log('🔄 Starting Google Calendar sync...');
            
            const response = await fetch('/api/google-calendar/sync', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const result = await response.json();
            
            if (response.ok && result.success) {
                const message = result.message || `Google Calendar 동기화 완료: ${result.events_processed || 0}개 이벤트`;
                this.showNotification(message, 'success');
                
                // 페이지 새로고침으로 캘린더 업데이트
                if (typeof window.googleCalendarGrid?.loadFromBackend === 'function') {
                    await window.googleCalendarGrid.loadFromBackend();
                }
                
                console.log('✅ Google Calendar sync completed:', result);
                
            } else {
                const error = result.error || 'Google Calendar 동기화 실패';
                throw new Error(error);
            }
            
        } catch (error) {
            console.error('Google Calendar sync error:', error);
            this.showNotification(`Google Calendar 동기화 실패: ${error.message}`, 'error');
        } finally {
            this.hideLoading(this.syncBtn);
        }
    }
    
    // 동기화 상태 확인
    async checkSyncStatus() {
        try {
            const response = await fetch('/api/google-calendar/status');
            if (response.ok) {
                const data = await response.json();
                return {
                    last_sync: data.last_sync,
                    events_count: data.events_count,
                    sync_enabled: data.sync_enabled
                };
            }
        } catch (error) {
            console.error('Error checking Google Calendar sync status:', error);
        }
        return null;
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