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

        // Console log removed
    }

    /**
     * Main connection flow entry point
     */
    async connect() {
        try {
            // Console log removed

            // Check current OAuth status
            const status = await this.checkOAuthStatus();
            // Console log removed

            if (status.oauth_connected && status.calendars_available) {
                // Already authenticated, show Google calendar selection (Step 1)
                await this.showGoogleCalendarSelection();
            } else {
                // Need OAuth first
                await this.startOAuthFlow();
            }
        } catch (error) {
            // Console error removed
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
        // Console log removed

        try {
            // Open OAuth popup directly (no fetch to avoid CORS)
            this.oauthWindow = window.open(
                '/auth/google',
                'GoogleOAuth',
                'width=500,height=600,scrollbars=yes,resizable=yes'
            );

            // Wait for OAuth completion
            // Console log removed
            await this.waitForOAuthCompletion();
            // Console log removed

            // Show Google calendar selection first (Step 1)
            await this.showGoogleCalendarSelection();
            // Console log removed
        } catch (error) {
            // Console error removed
            throw error;
        }
    }

    /**
     * Wait for OAuth popup to complete
     */
    async waitForOAuthCompletion() {
        // Console log removed
        return new Promise((resolve, reject) => {
            let authCompleted = false;

            // Poll OAuth status using API calls instead of window.closed
            const pollOAuthStatus = setInterval(async () => {
                try {
                    // Console log removed
                    const response = await fetch('/api/google-calendar/calendar-state');
                    const data = await response.json();
                    // Console log removed

                    if (data.oauth_connected && !authCompleted) {
                        // Console log removed
                        clearInterval(pollOAuthStatus);
                        authCompleted = true;

                        // OAuth 완료 후 잠깐 대기하여 토큰이 완전히 저장되도록 함 (2초로 증가)
                        // Console log removed
                        setTimeout(() => {
                            // Console log removed
                            resolve();
                        }, 2000);
                    }
                } catch (error) {
                    // Console log removed
                }
            }, 2000); // Check every 2 seconds

            // Backup: Listen for postMessage
            const messageHandler = (event) => {
                if (event.origin !== window.location.origin) return;

                if ((event.data.type === 'GOOGLE_OAUTH_SUCCESS' || event.data.type === 'oauth_success') && event.data.platform === 'google' && !authCompleted) {
                    // Console log removed
                    clearInterval(pollOAuthStatus);
                    window.removeEventListener('message', messageHandler);
                    authCompleted = true;

                    // OAuth 완료 후 잠깐 대기하여 토큰이 완전히 저장되도록 함 (2초로 증가)
                    // Console log removed
                    setTimeout(() => {
                        // Console log removed
                        resolve();
                    }, 2000);
                } else if (event.data.type === 'GOOGLE_OAUTH_ERROR' || (event.data.type === 'oauth_error' && event.data.platform === 'google')) {
                    // Console error removed
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
        // Console log removed

        try {
            // Fetch Google calendars
            const response = await fetch('/api/google-calendars');
            const data = await response.json();

            if (!data.success || !data.calendars?.length) {
                throw new Error('Google 캘린더를 찾을 수 없습니다.');
            }

            // Console log removed

            // Show selection modal
            this.createGoogleCalendarModal(data.calendars);

        } catch (error) {
            // Console error removed
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
        // Console log removed
    }

    /**
     * Handle Google calendar selection (Step 1 complete)
     */
    async selectGoogleCalendar(calendarId, calendarName) {
        // Console log removed

        // Store selection
        this.selectedGoogleCalendarId = calendarId;
        this.selectedGoogleCalendarName = calendarName;

        // Close Google calendar modal
        this.closeModal('google-calendar-modal');

        // Show NotionFlow calendar selection (Step 2)
        setTimeout(() => {
            // Console log removed
            this.showNotionFlowCalendarSelection();
        }, 300);
    }

    /**
     * Select primary Google calendar automatically
     */
    async selectPrimaryGoogleCalendar() {
        // Console log removed

        try {
            // Fetch Google calendars
            const response = await fetch('/api/google-calendars');
            const data = await response.json();

            if (data.success && data.calendars && data.calendars.length > 0) {
                // Find primary calendar or use first one
                const primaryCalendar = data.calendars.find(cal => cal.primary) || data.calendars[0];

                this.selectedGoogleCalendarId = primaryCalendar.id;
                this.selectedGoogleCalendarName = primaryCalendar.summary;

                // Console log removed
            } else {
                throw new Error('No Google calendars found');
            }
        } catch (error) {
            // Console error removed
            // 기본값 설정
            this.selectedGoogleCalendarId = 'primary';
            this.selectedGoogleCalendarName = 'Primary';
            // Console log removed
        }
    }

    /**
     * Show NotionFlow Calendar selection modal (Step 2 of 2)
     */
    async showNotionFlowCalendarSelection() {
        // Console log removed

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

            // Console log removed

            // Show selection modal
            this.createNotionFlowCalendarModal(calendars);

        } catch (error) {
            // Console error removed
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
        // Console log removed
    }

    /**
     * Handle NotionFlow calendar selection and perform final connection (Step 2 complete)
     */
    async selectNotionFlowCalendar(calendarId, calendarName) {
        // Console log removed

        if (!this.selectedGoogleCalendarId) {
            // Console error removed
            this.showNotification('Google 캘린더가 선택되지 않았습니다.', 'error');
            return;
        }

        try {
            // Console log removed

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
                // Console log removed

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
            // Console error removed
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
            // Console log removed
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

        // Console log removed
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

// Console log removed