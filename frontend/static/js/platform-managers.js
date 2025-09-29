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
        
        // Hide sync button for Google Calendar (like Notion - sync happens automatically)
        if (this.syncBtn) {
            this.syncBtn.style.display = 'none';
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
                
                // Show calendar selection modal for fresh connections
                this.showNotification('Google OAuth 연결 완료 - 캘린더 선택 중...', 'success');

                // Mark OAuth as connected in backend first (like Notion)
                await this.markOAuthConnected();

                // FORCE CLEAR ALL BLUR OVERLAYS before showing calendar selection
                this.clearAllBlurOverlays();

                // Wait a bit for the OAuth status to be properly set
                await new Promise(resolve => setTimeout(resolve, 500));

                try {
                    await this.showCalendarSelection();
                } catch (calendarError) {
                    console.error('Calendar selection failed:', calendarError);
                    // OAuth는 성공했으므로 logged_in 상태 유지
                    this.updateStatus('logged_in');
                    // 에러는 showCalendarSelection에서 이미 표시됨
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

    // Override showConnectedState to add calendar selection button
    showConnectedState() {
        // Call parent method first
        super.showConnectedState();

        // Show calendar selection button for Google Calendar
        if (this.syncBtn) {
            this.syncBtn.style.display = 'inline-flex';
            this.syncBtn.style.visibility = 'visible';
            this.syncBtn.innerHTML = `
                <span class="sync-text">캘린더 선택</span>
                <span class="sync-status"></span>
            `;
            this.syncBtn.onclick = () => this.showCalendarSelection();
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
                // Clear connection state from localStorage (like Notion)
                localStorage.setItem('google_manually_disconnected', 'true');
                localStorage.removeItem('google_calendar_connected');
                localStorage.removeItem('google_calendar_id');
                localStorage.removeItem('google_last_connected');

                console.log('🔓 [GOOGLE] Calendar disconnection saved to localStorage');

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
            // Check localStorage for persistent Google Calendar connection (like Notion OAuth logic)
            const isConnected = localStorage.getItem('google_calendar_connected');
            const calendarId = localStorage.getItem('google_calendar_id');
            const lastConnected = localStorage.getItem('google_last_connected');
            const manuallyDisconnected = localStorage.getItem('google_manually_disconnected');

            // If manually disconnected, don't restore connection
            if (manuallyDisconnected === 'true') {
                console.log('🔒 [GOOGLE] Manual disconnection detected - keeping disconnected state');
                this.updateStatus('disconnected');
                return;
            }

            // Check server-side OAuth token status first (like Notion)
            const googleStateResponse = await fetch('/api/google-calendar/calendar-state');
            if (googleStateResponse.ok) {
                const googleStateData = await googleStateResponse.json();
                if (googleStateData.success) {
                    if (googleStateData.oauth_connected && googleStateData.calendar_connected) {
                        // Fully connected (OAuth + calendar selected)
                        console.log('✅ [GOOGLE] Server confirms full connection - restoring connected state');
                        this.updateStatus('connected');

                        // Sync localStorage with server state
                        if (!isConnected) {
                            localStorage.setItem('google_calendar_connected', 'true');
                            localStorage.setItem('google_last_connected', new Date().toISOString());
                        }
                        return;
                    } else if (googleStateData.oauth_connected && googleStateData.needs_calendar_selection) {
                        // OAuth connected but needs calendar selection
                        console.log('🔄 [GOOGLE] OAuth connected, calendar selection needed');
                        this.updateStatus('logged_in');

                        // Clear localStorage connection state but keep OAuth
                        localStorage.removeItem('google_calendar_connected');
                        localStorage.removeItem('google_calendar_id');
                        return;
                    }
                }
            }

            // Fallback: If localStorage shows connected state, try to restore it
            if (isConnected === 'true' && calendarId && lastConnected) {
                console.log('🔄 [GOOGLE] Attempting to restore connection from localStorage:', {
                    calendar_id: calendarId,
                    last_connected: lastConnected
                });

                // Additional check with dashboard API for compatibility
                const response = await fetch('/api/dashboard/platforms');
                if (response.ok) {
                    const data = await response.json();
                    const status = data.platforms?.google;

                    if (status && status.configured && status.enabled) {
                        console.log('✅ [GOOGLE] Backend confirms connection - restoring connected state');
                        this.updateStatus('connected');
                        return;
                    } else {
                        console.log('⚠️ [GOOGLE] Backend connection lost - clearing localStorage');
                        // Clear stale localStorage data
                        localStorage.removeItem('google_calendar_connected');
                        localStorage.removeItem('google_calendar_id');
                        localStorage.removeItem('google_last_connected');
                    }
                }
            }

            // Fallback: Check backend status only
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
    
    clearAllBlurOverlays() {
        console.log('🧹 [BLUR CLEANUP] Removing ALL blur overlays from the page');

        // Remove all modal-related elements
        const elementsToRemove = [
            '.modal-overlay',
            '.modal-backdrop',
            '.backdrop',
            '.calendar-selection-modal',
            '.calendar-sync-modal',
            '[class*="modal"]:not(#google-calendar-modal-ultimate)',
            '[style*="backdrop"]',
            '[style*="blur"]'
        ];

        elementsToRemove.forEach(selector => {
            document.querySelectorAll(selector).forEach(el => {
                console.log('🗑️ [BLUR CLEANUP] Removing blur element:', el.className || el.id);
                el.remove();
            });
        });

        // Reset body and html styles
        document.body.style.overflow = '';
        document.body.style.position = '';
        document.body.style.filter = '';
        document.documentElement.style.overflow = '';
        document.documentElement.style.filter = '';

        // Remove backdrop-filter and blur from all elements
        document.querySelectorAll('*').forEach(el => {
            if (el.style.backdropFilter) {
                el.style.backdropFilter = '';
            }
            if (el.style.filter && el.style.filter.includes('blur')) {
                el.style.filter = '';
            }
            // Remove any position fixed that might be causing overlay
            if (el.style.position === 'fixed' && (el.style.background || el.style.backgroundColor)) {
                const bgColor = el.style.background || el.style.backgroundColor;
                if (bgColor.includes('rgba') && el !== document.getElementById('google-calendar-modal-ultimate')) {
                    console.log('🗑️ [BLUR CLEANUP] Removing fixed overlay:', el.className || el.id);
                    el.remove();
                }
            }
        });

        console.log('✅ [BLUR CLEANUP] All blur overlays removed');
    }

    async showCalendarSelection() {
        try {
            console.log('📅 [GOOGLE] Starting calendar selection...');

            // Fetch Google Calendars using the API
            const response = await fetch('/api/google-calendars');
            if (!response.ok) {
                throw new Error(`Failed to fetch calendars: ${response.status}`);
            }

            const data = await response.json();
            if (!data.success || !data.calendars || data.calendars.length === 0) {
                throw new Error('Google 계정에 캘린더가 없습니다');
            }

            // Use the Ultimate Google Calendar Modal
            this.createFallbackCalendarModal(data.calendars);

        } catch (error) {
            console.error('Calendar selection error:', error);

            // 에러 타입에 따라 다른 알림 표시
            if (error.message.includes('캘린더가 없습니다')) {
                this.showNotification('Google 계정에 사용 가능한 캘린더가 없습니다.', 'warning');
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
            console.log(`🔗 [GOOGLE] Connecting user calendar: ${calendarId}`);

            // Connect to user's calendar (not Google calendar ID) - similar to Notion
            const response = await fetch(`/api/google-calendar/connect-calendar`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ calendar_id: calendarId })
            });

            const result = await response.json();

            if (response.ok && result.success) {
                // Store connection state in localStorage for persistence (like Notion)
                localStorage.setItem('google_calendar_connected', 'true');
                localStorage.setItem('google_calendar_id', calendarId);
                localStorage.setItem('google_last_connected', new Date().toISOString());
                localStorage.removeItem('google_manually_disconnected');

                console.log('✅ [GOOGLE] Calendar connection completed:', result);

                this.updateStatus('connected');

                // Show success message with sync count if available
                const message = result.synced_count !== undefined ?
                    `Google Calendar 연결 완료! ${result.synced_count}개 이벤트 동기화됨` :
                    'Google Calendar 연결 완료!';

                this.showNotification(message, 'success');

                // Trigger calendar refresh if needed
                if (result.trigger_calendar_refresh && typeof window.refreshCalendar === 'function') {
                    window.refreshCalendar();
                }
            } else {
                throw new Error(result.error || `연결 실패: ${response.status}`);
            }

        } catch (error) {
            console.error('Calendar connection error:', error);
            this.showNotification(`캘린더 연결 중 오류: ${error.message}`, 'error');
        }
    }

    async showUserCalendarSelection(googleCalendarId) {
        try {
            console.log('📅 [GOOGLE] Step 2: Showing user calendars for Google calendar:', googleCalendarId);

            // Fetch user's NotionFlow calendars
            const response = await fetch('/api/calendars');
            if (!response.ok) {
                throw new Error(`Failed to fetch user calendars: ${response.status}`);
            }

            const calendarData = await response.json();
            console.log('📅 [GOOGLE] Calendar data:', calendarData);

            // Extract all calendars from the response (personal + shared)
            const allCalendars = [
                ...(calendarData.personal_calendars || []),
                ...(calendarData.shared_calendars || [])
            ];

            console.log('📅 [GOOGLE] All user calendars:', allCalendars);

            // Close the first modal and show the second step
            const existingModal = document.getElementById('google-calendar-modal-ultimate');
            if (existingModal) {
                existingModal.remove();
            }

            // Create step 2 modal for user calendar selection
            this.createUserCalendarSelectionModal(allCalendars, googleCalendarId);

        } catch (error) {
            console.error('Error in showUserCalendarSelection:', error);
            alert(`사용자 캘린더 목록을 가져오는 중 오류가 발생했습니다: ${error.message}`);
        }
    }

    createUserCalendarSelectionModal(userCalendars, googleCalendarId) {
        console.log('🚀 [GOOGLE] Creating Step 2 Modal - User Calendar Selection');
        console.log('📅 [GOOGLE] User calendars for modal:', userCalendars);

        // Check if userCalendars is empty or not an array
        if (!userCalendars || !Array.isArray(userCalendars) || userCalendars.length === 0) {
            console.log('⚠️ [GOOGLE] No user calendars available');
            alert('연결할 캘린더가 없습니다. 먼저 캘린더를 생성해주세요.');
            return;
        }

        // Create modal for step 2
        const modal = document.createElement('div');
        modal.id = 'user-calendar-selection-modal';
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 10000;
            backdrop-filter: blur(8px);
        `;

        modal.innerHTML = `
            <div style="
                background: white;
                border-radius: 16px;
                padding: 32px;
                max-width: 500px;
                width: 90%;
                max-height: 80vh;
                overflow-y: auto;
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
                border: 1px solid #e5e7eb;
            ">
                <div style="text-align: center; margin-bottom: 24px;">
                    <h2 style="
                        font-size: 24px;
                        font-weight: 700;
                        color: #1f2937;
                        margin: 0 0 8px 0;
                    ">내 캘린더 선택</h2>
                    <p style="
                        color: #6b7280;
                        margin: 0;
                        font-size: 16px;
                    ">Google Calendar를 연결할 캘린더를 선택하세요</p>
                </div>
                <div style="margin-bottom: 24px;">
                    ${userCalendars.map(cal => `
                        <div onclick="selectUserCalendar('${cal.id}', this)" style="
                            border: 2px solid #e5e7eb;
                            border-radius: 12px;
                            padding: 16px;
                            margin-bottom: 12px;
                            cursor: pointer;
                            transition: all 0.2s ease;
                            background: white;
                        " onmouseover="this.style.backgroundColor='#f9fafb'"
                           onmouseout="if (!this.classList.contains('selected')) this.style.backgroundColor='white'">
                            <div style="display: flex; align-items: center; gap: 12px;">
                                <div style="
                                    width: 16px;
                                    height: 16px;
                                    background: ${cal.color || '#3b82f6'};
                                    border-radius: 50%;
                                    flex-shrink: 0;
                                "></div>
                                <div style="flex: 1;">
                                    <div style="font-weight: 600; font-size: 16px; color: #1f2937; margin-bottom: 4px;">
                                        ${cal.name || 'Untitled Calendar'}
                                    </div>
                                    <div style="font-size: 14px; color: #6b7280;">
                                        ${cal.description || '설명 없음'}
                                    </div>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
                <div style="display: flex; gap: 12px; justify-content: flex-end;">
                    <button onclick="document.getElementById('user-calendar-selection-modal').remove()" style="
                        padding: 12px 24px;
                        background: #f3f4f6;
                        color: #374151;
                        border: none;
                        border-radius: 8px;
                        cursor: pointer;
                        font-weight: 500;
                        font-size: 14px;
                    " onmouseover="this.style.backgroundColor='#e5e7eb'"
                       onmouseout="this.style.backgroundColor='#f3f4f6'">취소</button>
                    <button id="connect-user-calendar-btn" onclick="connectToUserCalendar()" disabled style="
                        padding: 12px 24px;
                        background: #3b82f6;
                        color: white;
                        border: none;
                        border-radius: 8px;
                        cursor: pointer;
                        font-weight: 500;
                        font-size: 14px;
                        opacity: 0.5;
                    ">연결하기</button>
                </div>
            </div>
        `;

        // Add global functions for user calendar selection
        window.selectedUserCalendarId = null;
        window.selectedGoogleCalendarId = googleCalendarId;

        window.selectUserCalendar = function(calendarId, element) {
            console.log('📅 [GOOGLE] User calendar selected:', calendarId);
            // Remove previous selection
            document.querySelectorAll('#user-calendar-selection-modal [onclick*="selectUserCalendar"]').forEach(el => {
                el.style.borderColor = '#e5e7eb';
                el.style.backgroundColor = 'white';
                el.classList.remove('selected');
            });
            // Add selection to clicked element
            element.style.borderColor = '#3b82f6';
            element.style.backgroundColor = '#eff6ff';
            element.classList.add('selected');
            window.selectedUserCalendarId = calendarId;
            // Enable connect button
            const connectBtn = document.getElementById('connect-user-calendar-btn');
            connectBtn.disabled = false;
            connectBtn.style.opacity = '1';
            connectBtn.style.cursor = 'pointer';
        };

        window.connectToUserCalendar = async function() {
            if (window.selectedUserCalendarId && window.selectedGoogleCalendarId) {
                console.log('🔗 [GOOGLE] Connecting Google calendar to user calendar:',
                           window.selectedGoogleCalendarId, '->', window.selectedUserCalendarId);
                try {
                    const googleManager = PlatformManagerFactory.get('google');
                    if (googleManager) {
                        // Store the Google calendar ID for the connection
                        const requestData = {
                            calendar_id: window.selectedUserCalendarId,
                            google_calendar_id: window.selectedGoogleCalendarId
                        };

                        const response = await fetch('/api/google-calendar/connect-calendar', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(requestData)
                        });

                        const result = await response.json();

                        if (response.ok && result.success) {
                            // Store connection state
                            localStorage.setItem('google_calendar_connected', 'true');
                            localStorage.setItem('google_calendar_id', window.selectedUserCalendarId);
                            localStorage.setItem('google_last_connected', new Date().toISOString());
                            localStorage.removeItem('google_manually_disconnected');

                            console.log('✅ [GOOGLE] Calendar connection completed:', result);
                            googleManager.updateStatus('connected');

                            const message = result.synced_count !== undefined ?
                                `Google Calendar 연결 완료! ${result.synced_count}개 이벤트 동기화됨` :
                                'Google Calendar 연결 완료!';
                            googleManager.showNotification(message, 'success');

                            // Close modal
                            const modal = document.getElementById('user-calendar-selection-modal');
                            if (modal) {
                                modal.remove();
                            }

                            // Trigger calendar refresh if needed
                            if (result.trigger_calendar_refresh && typeof window.refreshCalendar === 'function') {
                                window.refreshCalendar();
                            }
                        } else {
                            throw new Error(result.error || `연결 실패: ${response.status}`);
                        }
                    }
                } catch (error) {
                    console.error('User calendar connection error:', error);
                    alert('캘린더 연결 중 오류가 발생했습니다: ' + error.message);
                }
            }
        };

        document.body.appendChild(modal);
    }

    createFallbackCalendarModal(calendars) {
        console.log('🚀 [GOOGLE] Creating Ultimate Google Calendar Modal with calendars:', calendars);

        // Remove any existing modals more aggressively
        const existingModals = [
            document.getElementById('google-calendar-modal'),
            document.getElementById('calendar-selection-modal'),
            document.querySelector('.calendar-selection-modal'),
            document.querySelector('.google-calendar-modal'),
            document.querySelector('[id*="calendar"]'),
            document.querySelector('[class*="modal"]')
        ];

        existingModals.forEach(modal => {
            if (modal && modal.remove) {
                console.log('🗑️ [GOOGLE] Removing existing modal:', modal.id || modal.className);
                modal.remove();
            }
        });

        // Wait a moment for cleanup
        setTimeout(() => {

        console.log('🚀 [GOOGLE] Creating ULTIMATE modal with nuclear approach...');

        // Create modal HTML with COMPLETE inline styling (no CSS classes)
        const modal = document.createElement('div');
        modal.id = 'google-calendar-modal-ultimate';
        // FORCE REMOVE ALL BLUR OVERLAYS AND MODALS
        console.log('🧹 [CLEANUP] Removing ALL blur overlays and modal elements');

        // Remove all modal-related elements that could cause blur
        const elementsToRemove = [
            '.modal-overlay',
            '.modal-backdrop',
            '.backdrop',
            '.calendar-selection-modal',
            '.calendar-sync-modal',
            '[class*="modal"]',
            '[style*="backdrop"]',
            '[style*="blur"]',
            '[style*="position: fixed"]'
        ];

        elementsToRemove.forEach(selector => {
            document.querySelectorAll(selector).forEach(el => {
                if (el !== modal) {
                    console.log('🗑️ [CLEANUP] Removing element:', el.className || el.id);
                    el.remove();
                }
            });
        });

        // Force remove any remaining overlay styles on body and html
        document.body.style.overflow = '';
        document.body.style.position = '';
        document.documentElement.style.overflow = '';

        // Remove any backdrop-filter from all elements
        document.querySelectorAll('*').forEach(el => {
            if (el.style.backdropFilter) {
                el.style.backdropFilter = '';
            }
            if (el.style.filter && el.style.filter.includes('blur')) {
                el.style.filter = '';
            }
        });

        modal.style.cssText = `
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            right: 0 !important;
            bottom: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            background: rgba(0, 0, 0, 0.85) !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            z-index: 2147483647 !important;
            backdrop-filter: blur(10px) !important;
            animation: fadeIn 0.3s ease-out !important;
            pointer-events: all !important;
            visibility: visible !important;
            opacity: 1 !important;
        `;

        const modalContent = document.createElement('div');
        modalContent.style.cssText = `
            background: white !important;
            border-radius: 16px !important;
            padding: 32px !important;
            max-width: 600px !important;
            width: 90% !important;
            max-height: 80vh !important;
            overflow-y: auto !important;
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5) !important;
            position: relative !important;
            transform: scale(1) !important;
            animation: slideInScale 0.3s ease-out !important;
            z-index: 2147483647 !important;
            pointer-events: all !important;
            visibility: visible !important;
            opacity: 1 !important;
            display: block !important;
            margin: auto !important;
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

        // Add aggressive CSS overrides to document
        if (!document.querySelector('#google-modal-override-styles')) {
            const style = document.createElement('style');
            style.id = 'google-modal-override-styles';
            style.textContent = `
                /* Hide all existing modals and overlays */
                .modal-overlay:not(#google-calendar-modal),
                .calendar-selection-modal:not(#google-calendar-modal),
                [class*="modal"]:not(#google-calendar-modal),
                [class*="backdrop"]:not(#google-calendar-modal) {
                    display: none !important;
                    visibility: hidden !important;
                    z-index: -9999 !important;
                }

                /* Force our modal to be visible */
                #google-calendar-modal {
                    position: fixed !important;
                    top: 0 !important;
                    left: 0 !important;
                    width: 100vw !important;
                    height: 100vh !important;
                    z-index: 2147483647 !important;
                    display: flex !important;
                    visibility: visible !important;
                    opacity: 1 !important;
                    pointer-events: all !important;
                }

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

        // Create complete modal structure with inline styles only
        modal.innerHTML = `
            <div style="
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                background: rgba(0, 0, 0, 0.9);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 2147483647;
                backdrop-filter: blur(8px);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            ">
                <div style="
                    background: white;
                    border-radius: 20px;
                    padding: 40px;
                    max-width: 600px;
                    width: 90%;
                    max-height: 80vh;
                    overflow-y: auto;
                    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);
                    position: relative;
                    z-index: 2147483647;
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
                        <h2 style="margin: 0; font-size: 24px; font-weight: 600; color: #1f2937;">📅 Google Calendar 선택</h2>
                        <button onclick="document.getElementById('google-calendar-modal-ultimate').remove()" style="
                            background: none;
                            border: none;
                            font-size: 24px;
                            cursor: pointer;
                            color: #6b7280;
                            padding: 8px;
                            border-radius: 50%;
                            width: 40px;
                            height: 40px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                        ">×</button>
                    </div>
                    <p style="color: #6b7280; margin-bottom: 24px; font-size: 16px;">동기화할 Google Calendar를 선택해주세요:</p>
                    <div style="margin-bottom: 24px; max-height: 400px; overflow-y: auto;">
                        ${calendars.map((cal, index) => `
                            <div onclick="selectGoogleCalendar('${cal.id}', this)" style="
                                padding: 16px;
                                margin-bottom: 12px;
                                border: 2px solid #e5e7eb;
                                border-radius: 12px;
                                cursor: pointer;
                                transition: all 0.2s;
                                background: white;
                            " onmouseover="this.style.borderColor='#3b82f6'; this.style.backgroundColor='#f8fafc';"
                               onmouseout="if(!this.classList.contains('selected')) { this.style.borderColor='#e5e7eb'; this.style.backgroundColor='white'; }">
                                <div style="display: flex; align-items: center; gap: 12px;">
                                    <div style="
                                        width: 16px;
                                        height: 16px;
                                        background: ${cal.color || '#3b82f6'};
                                        border-radius: 50%;
                                        flex-shrink: 0;
                                    "></div>
                                    <div style="flex: 1;">
                                        <div style="font-weight: 600; font-size: 16px; color: #1f2937; margin-bottom: 4px;">
                                            ${cal.name || 'Untitled Calendar'}
                                            ${cal.is_primary ? '<span style="background: #3b82f6; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; margin-left: 8px;">기본</span>' : ''}
                                        </div>
                                        <div style="font-size: 14px; color: #6b7280;">
                                            ${cal.description || '설명 없음'}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                    <div style="display: flex; gap: 12px; justify-content: flex-end;">
                        <button onclick="document.getElementById('google-calendar-modal-ultimate').remove()" style="
                            padding: 12px 24px;
                            background: #f3f4f6;
                            color: #374151;
                            border: none;
                            border-radius: 8px;
                            cursor: pointer;
                            font-weight: 500;
                            font-size: 14px;
                        " onmouseover="this.style.backgroundColor='#e5e7eb'"
                           onmouseout="this.style.backgroundColor='#f3f4f6'">취소</button>
                        <button id="ultimate-confirm-btn" onclick="connectSelectedCalendar()" disabled style="
                            padding: 12px 24px;
                            background: #3b82f6;
                            color: white;
                            border: none;
                            border-radius: 8px;
                            cursor: pointer;
                            font-weight: 500;
                            font-size: 14px;
                            opacity: 0.5;
                        ">연결하기</button>
                    </div>
                </div>
            </div>
        `;

        // Add global functions for calendar selection
        window.selectedCalendarId = null;
        window.selectGoogleCalendar = function(calendarId, element) {
            console.log('📅 [GOOGLE] Calendar selected:', calendarId);

            // Remove previous selection
            document.querySelectorAll('#google-calendar-modal-ultimate [onclick*="selectGoogleCalendar"]').forEach(el => {
                el.style.borderColor = '#e5e7eb';
                el.style.backgroundColor = 'white';
                el.classList.remove('selected');
            });

            // Add selection to clicked element
            element.style.borderColor = '#3b82f6';
            element.style.backgroundColor = '#eff6ff';
            element.classList.add('selected');
            window.selectedCalendarId = calendarId;

            // Enable confirm button
            const confirmBtn = document.getElementById('ultimate-confirm-btn');
            confirmBtn.disabled = false;
            confirmBtn.style.opacity = '1';
            confirmBtn.style.cursor = 'pointer';
        };

        window.connectSelectedCalendar = async function() {
            if (window.selectedCalendarId) {
                console.log('🔗 [GOOGLE] Moving to step 2 - showing user calendars for Google calendar:', window.selectedCalendarId);

                try {
                    const googleManager = PlatformManagerFactory.get('google');
                    if (googleManager) {
                        // Step 2: Show user's NotionFlow calendars
                        await googleManager.showUserCalendarSelection(window.selectedCalendarId);
                    }
                } catch (error) {
                    console.error('Step 2 error:', error);
                    alert('캘린더 목록을 가져오는 중 오류가 발생했습니다: ' + error.message);
                }
            }
        };

        document.body.appendChild(modal);

        // Force display after append with multiple methods
        modal.style.display = 'flex !important';
        modal.style.visibility = 'visible !important';
        modal.style.opacity = '1 !important';

        // Force all conflicting elements to be hidden
        setTimeout(() => {
            document.querySelectorAll('.modal-overlay, .calendar-selection-modal, [class*="modal"]:not(#google-calendar-modal)').forEach(el => {
                if (el !== modal) {
                    el.style.setProperty('display', 'none', 'important');
                    el.style.setProperty('visibility', 'hidden', 'important');
                    el.style.setProperty('z-index', '-9999', 'important');
                }
            });

            // Re-force our modal to be visible
            modal.style.setProperty('display', 'flex', 'important');
            modal.style.setProperty('visibility', 'visible', 'important');
            modal.style.setProperty('opacity', '1', 'important');
            modal.style.setProperty('z-index', '2147483647', 'important');

            console.log('🔥 [GOOGLE] FORCE DISPLAYED - Modal should now be visible!');
            console.log('📅 [GOOGLE] Modal element:', modal);
            console.log('📅 [GOOGLE] Modal computed style:', getComputedStyle(modal).display);
            console.log('📅 [GOOGLE] Modal z-index:', getComputedStyle(modal).zIndex);
        }, 50);

        console.log('✅ [GOOGLE] Fallback modal created and displayed');

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

        // Prevent modal background click from closing
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                e.preventDefault();
                e.stopPropagation();
                console.log('🔒 [GOOGLE] Modal background click prevented');
            }
        });

        // Prevent any overlay interference
        modalContent.addEventListener('click', (e) => {
            e.stopPropagation();
        });

        }, 100); // End of setTimeout
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

    async markOAuthConnected() {
        try {
            // Get the Google calendar email from localStorage (stored during OAuth)
            const googleCalendarId = localStorage.getItem('google_oauth_email') || 'unknown@gmail.com';
            console.log('🔍 [GOOGLE-OAUTH] DEBUG googleCalendarId from localStorage:', googleCalendarId);

            const requestData = { calendar_id: googleCalendarId };
            console.log('🔍 [GOOGLE-OAUTH] DEBUG request data:', requestData);
            console.log('🔍 [GOOGLE-OAUTH] DEBUG JSON string:', JSON.stringify(requestData));

            const response = await fetch(`/api/platform/google/connect`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestData)
            });

            console.log('🔍 [GOOGLE-OAUTH] Response status:', response.status);
            const result = await response.json();
            console.log('🔍 [GOOGLE-OAUTH] Response data:', result);

            if (response.ok) {
                console.log('✅ [GOOGLE] OAuth marked as connected in backend');
            } else {
                console.error('❌ [GOOGLE] Failed to mark OAuth as connected:', result);
            }
        } catch (error) {
            console.error('Error marking Google OAuth as connected:', error);
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

// Global function to clear all blur overlays
window.clearAllBlurOverlays = function() {
    console.log('🧹 [GLOBAL BLUR CLEANUP] Removing ALL blur overlays from the page');

    // Remove all modal-related elements
    const elementsToRemove = [
        '.modal-overlay',
        '.modal-backdrop',
        '.backdrop',
        '.calendar-selection-modal',
        '.calendar-sync-modal',
        '[class*="modal"]:not(#google-calendar-modal-ultimate)',
        '[style*="backdrop"]',
        '[style*="blur"]'
    ];

    let removedCount = 0;
    elementsToRemove.forEach(selector => {
        document.querySelectorAll(selector).forEach(el => {
            console.log('🗑️ [GLOBAL BLUR CLEANUP] Removing blur element:', el.className || el.id);
            el.remove();
            removedCount++;
        });
    });

    // Reset body and html styles
    document.body.style.overflow = '';
    document.body.style.position = '';
    document.body.style.filter = '';
    document.documentElement.style.overflow = '';
    document.documentElement.style.filter = '';

    // Remove backdrop-filter and blur from all elements
    document.querySelectorAll('*').forEach(el => {
        if (el.style.backdropFilter) {
            el.style.backdropFilter = '';
        }
        if (el.style.filter && el.style.filter.includes('blur')) {
            el.style.filter = '';
        }
        // Remove any position fixed that might be causing overlay
        if (el.style.position === 'fixed' && (el.style.background || el.style.backgroundColor)) {
            const bgColor = el.style.background || el.style.backgroundColor;
            if (bgColor.includes('rgba') && el !== document.getElementById('google-calendar-modal-ultimate')) {
                console.log('🗑️ [GLOBAL BLUR CLEANUP] Removing fixed overlay:', el.className || el.id);
                el.remove();
                removedCount++;
            }
        }
    });

    console.log(`✅ [GLOBAL BLUR CLEANUP] Removed ${removedCount} blur overlay elements`);
    return removedCount;
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