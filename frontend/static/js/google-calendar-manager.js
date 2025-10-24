/**
 * 🗓️ Google Calendar Manager
 * Clean and simple Google Calendar integration
 *
 * Flow:
 * 1. OAuth Authentication
 * 2. Google Calendar Selection
 * 3. NotionFlow Calendar Selection
 * 4. Connection & Sync
 */

class GoogleCalendarManager {
    constructor() {
        this.selectedGoogleCalendarId = null;
        this.selectedNotionFlowCalendarId = null;
        this.oauthWindow = null;

        console.log('🔧 [GOOGLE-MANAGER] Initialized');
    }

    /**
     * Main connection flow entry point
     */
    async connect() {
        try {
            console.log('🚀 [GOOGLE-MANAGER] Starting connection flow...');

            // Check current OAuth status
            const status = await this.checkOAuthStatus();
            console.log('📊 [GOOGLE-MANAGER] Current status:', status);

            if (status.oauth_connected && status.calendars_available) {
                // Already authenticated, show Google calendar selection (Step 1)
                await this.showGoogleCalendarSelection();
            } else {
                // Need OAuth first
                await this.startOAuthFlow();
            }
        } catch (error) {
            console.error('❌ [GOOGLE-MANAGER] Connection failed:', error);
            this.showNotification('Google Calendar 연결 중 오류가 발생했습니다.', 'error');
        }
    }

    /**
     * Check OAuth status via API
     */
    async checkOAuthStatus() {
        const response = await fetch('/api/google-calendar/calendar-state');
        return await response.json();
    }

    /**
     * Start OAuth authentication flow
     */
    async startOAuthFlow() {
        console.log('🔐 [GOOGLE-MANAGER] Starting OAuth flow...');

        try {
            // Open OAuth popup directly (no fetch to avoid CORS)
            this.oauthWindow = window.open(
                '/auth/google',
                'GoogleOAuth',
                'width=500,height=600,scrollbars=yes,resizable=yes'
            );

            // Wait for OAuth completion
            console.log('⏳ [GOOGLE-MANAGER] Waiting for OAuth to complete...');
            await this.waitForOAuthCompletion();
            console.log('✅ [GOOGLE-MANAGER] OAuth completed! Now showing Google calendar selection...');

            // Show Google calendar selection first (Step 1)
            await this.showGoogleCalendarSelection();
            console.log('✅ [GOOGLE-MANAGER] Google calendar selection modal shown - Step 1 of 2');
        } catch (error) {
            console.error('❌ [GOOGLE-MANAGER] OAuth failed:', error);
            throw error;
        }
    }

    /**
     * Wait for OAuth popup to complete
     */
    async waitForOAuthCompletion() {
        console.log('🔄 [GOOGLE-MANAGER] waitForOAuthCompletion started');
        return new Promise((resolve, reject) => {
            let authCompleted = false;

            // Poll OAuth status using API calls instead of window.closed
            const pollOAuthStatus = setInterval(async () => {
                try {
                    console.log('🔍 [GOOGLE-MANAGER] Checking OAuth status...');
                    const response = await fetch('/api/google-calendar/calendar-state');
                    const data = await response.json();
                    console.log('📊 [GOOGLE-MANAGER] OAuth status:', data);

                    if (data.oauth_connected && !authCompleted) {
                        console.log('✅ [GOOGLE-MANAGER] OAuth completed via polling');
                        clearInterval(pollOAuthStatus);
                        authCompleted = true;

                        // OAuth 완료 후 잠깐 대기하여 토큰이 완전히 저장되도록 함 (2초로 증가)
                        console.log('⏳ [GOOGLE-MANAGER] Waiting 2 seconds for OAuth tokens to be fully saved...');
                        setTimeout(() => {
                            console.log('✅ [GOOGLE-MANAGER] OAuth delay completed, proceeding with calendar loading');
                            resolve();
                        }, 2000);
                    }
                } catch (error) {
                    console.log('⏳ [GOOGLE-MANAGER] Still waiting for OAuth...', error);
                }
            }, 2000); // Check every 2 seconds

            // Backup: Listen for postMessage
            const messageHandler = (event) => {
                if (event.origin !== window.location.origin) return;

                if ((event.data.type === 'GOOGLE_OAUTH_SUCCESS' || event.data.type === 'oauth_success') && event.data.platform === 'google' && !authCompleted) {
                    console.log('✅ [GOOGLE-MANAGER] OAuth success via postMessage');
                    clearInterval(pollOAuthStatus);
                    window.removeEventListener('message', messageHandler);
                    authCompleted = true;

                    // OAuth 완료 후 잠깐 대기하여 토큰이 완전히 저장되도록 함 (2초로 증가)
                    console.log('⏳ [GOOGLE-MANAGER] Waiting 2 seconds for OAuth tokens to be fully saved...');
                    setTimeout(() => {
                        console.log('✅ [GOOGLE-MANAGER] OAuth delay completed, proceeding with calendar loading');
                        resolve();
                    }, 2000);
                } else if (event.data.type === 'GOOGLE_OAUTH_ERROR' || (event.data.type === 'oauth_error' && event.data.platform === 'google')) {
                    console.error('❌ [GOOGLE-MANAGER] OAuth error:', event.data.error);
                    clearInterval(pollOAuthStatus);
                    window.removeEventListener('message', messageHandler);
                    reject(new Error(event.data.error));
                }
            };

            window.addEventListener('message', messageHandler);

            // Timeout after 3 minutes
            setTimeout(() => {
                if (!authCompleted) {
                    clearInterval(pollOAuthStatus);
                    window.removeEventListener('message', messageHandler);
                    reject(new Error('OAuth timeout - please try again'));
                }
            }, 180000);
        });
    }

    /**
     * Show Google Calendar selection modal (Step 1 of 2)
     */
    async showGoogleCalendarSelection() {
        console.log('📅 [GOOGLE-MANAGER] Loading Google calendars for Step 1...');

        try {
            // Fetch Google calendars
            const response = await fetch('/api/google-calendars');
            const data = await response.json();

            if (!data.success || !data.calendars?.length) {
                throw new Error('Google 캘린더를 찾을 수 없습니다.');
            }

            console.log(`📅 [GOOGLE-MANAGER] Found ${data.calendars.length} Google calendars for Step 1`);

            // Show selection modal
            this.createGoogleCalendarModal(data.calendars);

        } catch (error) {
            console.error('❌ [GOOGLE-MANAGER] Failed to load Google calendars:', error);
            throw error;
        }
    }

    /**
     * Create Google Calendar selection modal
     */
    createGoogleCalendarModal(calendars) {
        // Remove existing modal
        const existingModal = document.getElementById('google-calendar-modal');
        if (existingModal) existingModal.remove();

        // Create calendar list
        const calendarItems = calendars.map(cal => `
            <div class="calendar-item" onclick="window.googleManager.selectGoogleCalendar('${cal.id}', '${cal.summary || cal.name}')">
                <div class="calendar-name">${cal.summary || cal.name}</div>
                <div class="calendar-description">${cal.description || ''}</div>
                <div class="calendar-meta">Google Calendar</div>
            </div>
        `).join('');

        // Create modal HTML for Step 1
        const modalHtml = `
            <div class="modal-overlay" id="google-calendar-modal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h2>Google 캘린더 선택 (1/2단계)</h2>
                        <button class="modal-close" onclick="window.googleManager.closeModal('google-calendar-modal')">&times;</button>
                    </div>
                    <div class="modal-body">
                        <p>동기화할 Google 캘린더를 선택하세요:</p>
                        <div class="calendar-list">
                            ${calendarItems}
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
        console.log('✅ [GOOGLE-MANAGER] Google calendar modal shown');
    }

    /**
     * Handle Google calendar selection (Step 1 complete)
     */
    async selectGoogleCalendar(calendarId, calendarName) {
        console.log(`📅 [GOOGLE-MANAGER] Step 1 complete - Selected Google calendar: ${calendarId} (${calendarName})`);

        // Store selection
        this.selectedGoogleCalendarId = calendarId;
        this.selectedGoogleCalendarName = calendarName;

        // Close Google calendar modal
        this.closeModal('google-calendar-modal');

        // Show NotionFlow calendar selection (Step 2)
        setTimeout(() => {
            console.log('🔄 [GOOGLE-MANAGER] Moving to Step 2 - NotionFlow calendar selection');
            this.showNotionFlowCalendarSelection();
        }, 300);
    }

    /**
     * Select primary Google calendar automatically
     */
    async selectPrimaryGoogleCalendar() {
        console.log('📅 [GOOGLE-MANAGER] Selecting primary Google calendar...');

        try {
            // Fetch Google calendars
            const response = await fetch('/api/google-calendars');
            const data = await response.json();

            if (data.success && data.calendars && data.calendars.length > 0) {
                // Find primary calendar or use first one
                const primaryCalendar = data.calendars.find(cal => cal.primary) || data.calendars[0];

                this.selectedGoogleCalendarId = primaryCalendar.id;
                this.selectedGoogleCalendarName = primaryCalendar.summary;

                console.log(`✅ [GOOGLE-MANAGER] Auto-selected Google calendar: ${primaryCalendar.id} (${primaryCalendar.summary})`);
            } else {
                throw new Error('No Google calendars found');
            }
        } catch (error) {
            console.error('❌ [GOOGLE-MANAGER] Failed to select primary Google calendar:', error);
            // 기본값 설정
            this.selectedGoogleCalendarId = 'primary';
            this.selectedGoogleCalendarName = 'Primary';
            console.log('🔄 [GOOGLE-MANAGER] Using fallback primary calendar');
        }
    }

    /**
     * Show NotionFlow Calendar selection modal (Step 2 of 2)
     */
    async showNotionFlowCalendarSelection() {
        console.log('📅 [GOOGLE-MANAGER] Step 2 - Loading NotionFlow calendars...');

        try {
            // Fetch NotionFlow calendars
            const response = await fetch('/api/calendars');
            const data = await response.json();

            // API 응답 구조 확인 (Notion 방식과 동일)
            const calendars = data.personal_calendars || data.calendars || [];

            if (!data.success || !calendars.length) {
                this.showNotification('NotionFlow 캘린더가 없습니다. 캘린더를 먼저 생성해주세요.', 'warning');
                return;
            }

            console.log(`📅 [GOOGLE-MANAGER] Step 2 - Found ${calendars.length} NotionFlow calendars`);

            // Show selection modal
            this.createNotionFlowCalendarModal(calendars);

        } catch (error) {
            console.error('❌ [GOOGLE-MANAGER] Failed to load NotionFlow calendars:', error);
            throw error;
        }
    }

    /**
     * Create NotionFlow Calendar selection modal
     */
    createNotionFlowCalendarModal(calendars) {
        // Remove existing modal
        const existingModal = document.getElementById('notionflow-calendar-modal');
        if (existingModal) existingModal.remove();

        // Create calendar list
        const calendarItems = calendars.map(cal => `
            <div class="calendar-item" onclick="window.googleManager.selectNotionFlowCalendar('${cal.id}', '${cal.name}')">
                <div class="calendar-name">${cal.name}</div>
                <div class="calendar-description">이벤트: ${cal.event_count || 0}개</div>
                <div class="calendar-meta">NotionFlow Calendar</div>
            </div>
        `).join('');

        // Create modal HTML for Step 2
        const modalHtml = `
            <div class="modal-overlay" id="notionflow-calendar-modal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h2>NotionFlow 캘린더 선택 (2/2단계)</h2>
                        <button class="modal-close" onclick="window.googleManager.closeModal('notionflow-calendar-modal')">&times;</button>
                    </div>
                    <div class="modal-body">
                        <p><strong>${this.selectedGoogleCalendarName}</strong>을(를) 어느 NotionFlow 캘린더와 동기화할까요?</p>
                        <div class="calendar-list">
                            ${calendarItems}
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
        console.log('✅ [GOOGLE-MANAGER] NotionFlow calendar modal shown');
    }

    /**
     * Handle NotionFlow calendar selection and perform final connection (Step 2 complete)
     */
    async selectNotionFlowCalendar(calendarId, calendarName) {
        console.log(`📅 [GOOGLE-MANAGER] Step 2 complete - Selected NotionFlow calendar: ${calendarId} (${calendarName})`);

        if (!this.selectedGoogleCalendarId) {
            console.error('❌ [GOOGLE-MANAGER] No Google calendar selected!');
            this.showNotification('Google 캘린더가 선택되지 않았습니다.', 'error');
            return;
        }

        try {
            console.log(`🔗 [GOOGLE-MANAGER] Final connection: ${this.selectedGoogleCalendarName} → ${calendarName}`);

            // Perform connection
            const response = await fetch('/api/platform/google/connect', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    calendar_id: this.selectedGoogleCalendarId,
                    notionflow_calendar_id: calendarId
                })
            });

            const result = await response.json();

            if (result.success) {
                console.log('✅ [GOOGLE-MANAGER] 2-step connection completed successfully!');

                // Close modal
                this.closeModal('notionflow-calendar-modal');

                // Show success notification
                this.showNotification(`Google Calendar "${this.selectedGoogleCalendarName}"가 "${calendarName}" 캘린더와 성공적으로 연결되었습니다!`, 'success');

                // Update UI using existing dashboard function
                if (window.markPlatformConnected) {
                    window.markPlatformConnected('google');
                }
                if (window.updatePlatformStatus) {
                    window.updatePlatformStatus();
                }

                // Reset selections
                this.selectedGoogleCalendarId = null;
                this.selectedNotionFlowCalendarId = null;

            } else {
                throw new Error(result.error || '연결에 실패했습니다.');
            }

        } catch (error) {
            console.error('❌ [GOOGLE-MANAGER] Connection failed:', error);
            this.showNotification(`연결 실패: ${error.message}`, 'error');
        }
    }


    /**
     * Close modal by ID
     */
    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.remove();
            console.log(`🗑️ [GOOGLE-MANAGER] Closed modal: ${modalId}`);
        }
    }

    /**
     * Show notification
     */
    showNotification(message, type = 'info') {
        // Use existing notification system if available
        if (window.showNotification) {
            window.showNotification(message, type);
        } else {
            // Fallback alert
            alert(message);
        }

        console.log(`📢 [GOOGLE-MANAGER] Notification (${type}): ${message}`);
    }
}

// Initialize Google Calendar Manager
window.googleManager = new GoogleCalendarManager();

// CSS styles for modals
const styles = `
<style>
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 10000;
    display: flex;
    align-items: center;
    justify-content: center;
}

.modal-content {
    background: white;
    border-radius: 12px;
    padding: 0;
    max-width: 500px;
    width: 90%;
    max-height: 70vh;
    overflow: hidden;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}

.modal-header {
    padding: 20px 24px;
    border-bottom: 1px solid #e5e7eb;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.modal-header h2 {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 600;
    color: #111827;
}

.modal-close {
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    color: #6b7280;
    padding: 0;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.modal-close:hover {
    color: #374151;
}

.modal-body {
    padding: 24px;
    overflow-y: auto;
}

.calendar-list {
    margin-top: 16px;
}

.calendar-item {
    padding: 16px;
    margin-bottom: 8px;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
}

.calendar-item:hover {
    border-color: #3b82f6;
    background-color: #f8fafc;
}

.calendar-name {
    font-weight: 500;
    color: #111827;
    margin-bottom: 4px;
}

.calendar-description {
    font-size: 0.875rem;
    color: #6b7280;
    margin-bottom: 4px;
}

.calendar-meta {
    font-size: 0.75rem;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
</style>
`;

// Add styles to document
document.head.insertAdjacentHTML('beforeend', styles);

// Initialize Google Calendar Manager
window.googleManager = new GoogleCalendarManager();

console.log('✅ [GOOGLE-MANAGER] Loaded and initialized successfully');