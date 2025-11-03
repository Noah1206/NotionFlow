/**
 * 🗓️ Notion Calendar Manager
 * Clean and simple Notion Calendar integration with Google-style modals
 *
 * Flow:
 * 1. OAuth Authentication
 * 2. NodeFlow Calendar Selection
 * 3. Connection & Sync
 */

class NotionCalendarManager {
    constructor() {
        this.selectedNodeFlowCalendarId = null;
        this.selectedNodeFlowCalendarName = null;

        // Console log removed
    }

    /**
     * Main connection flow entry point (called after OAuth success)
     */
    async connect() {
        try {
            // Console log removed

            // Show NodeFlow calendar selection
            await this.showNodeFlowCalendarSelection();
        } catch (error) {
            // Console error removed
            this.showNotification('Notion 캘린더 선택 중 오류가 발생했습니다.', 'error');
        }
    }

    /**
     * Show NodeFlow Calendar selection modal
     */
    async showNodeFlowCalendarSelection() {
        // Console log removed

        try {
            // Fetch NodeFlow calendars
            const response = await fetch('/api/calendars');
            const data = await response.json();

            // API 응답 구조 확인
            const calendars = data.personal_calendars || data.calendars || [];

            if (!data.success || !calendars.length) {
                this.showNotification('NodeFlow 캘린더가 없습니다. 캘린더를 먼저 생성해주세요.', 'warning');
                return;
            }

            // Console log removed

            // Show selection modal
            this.createNodeFlowCalendarModal(calendars);

        } catch (error) {
            // Console error removed
            throw error;
        }
    }

    /**
     * Create NodeFlow Calendar selection modal (Google-style)
     */
    createNodeFlowCalendarModal(calendars) {
        // Remove existing modal
        const existingModal = document.getElementById('notion-calendar-modal');
        if (existingModal) existingModal.remove();

        // Create calendar list
        const calendarItems = calendars.map(cal => `
            <div class="calendar-item" onclick="window.notionManager.selectNodeFlowCalendar('${cal.id}', '${cal.name}')">
                <div class="calendar-name">${cal.name}</div>
                <div class="calendar-description">이벤트: ${cal.event_count || 0}개</div>
                <div class="calendar-meta">NodeFlow Calendar</div>
            </div>
        `).join('');

        // Create modal HTML (same structure as Google modal)
        const modalHtml = `
            <div class="modal-overlay" id="notion-calendar-modal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h2>NodeFlow 캘린더 선택</h2>
                        <button class="modal-close" onclick="window.notionManager.closeModal('notion-calendar-modal')">&times;</button>
                    </div>
                    <div class="modal-body">
                        <p><strong>Notion</strong>과 동기화할 NodeFlow 캘린더를 선택하세요:</p>
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
     * Handle NodeFlow calendar selection and perform final connection
     */
    async selectNodeFlowCalendar(calendarId, calendarName) {
        // Console log removed

        try {
            // Perform connection
            const response = await fetch('/api/platform/notion/connect', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    nodeflow_calendar_id: calendarId
                })
            });

            const result = await response.json();

            if (result.success) {
                // Console log removed

                // Close modal
                this.closeModal('notion-calendar-modal');

                // Show success notification
                this.showNotification(`Notion이 "${calendarName}" 캘린더와 성공적으로 연결되었습니다!`, 'success');

                // Update UI
                this.updateConnectionStatus();

                // Reset selections
                this.selectedNodeFlowCalendarId = null;

            } else {
                throw new Error(result.error || '연결에 실패했습니다.');
            }

        } catch (error) {
            // Console error removed
            this.showNotification(`연결 실패: ${error.message}`, 'error');
        }
    }

    /**
     * Update connection status in UI
     */
    updateConnectionStatus() {
        const notionCard = document.querySelector('[data-platform="notion"]');
        if (!notionCard) return;

        // Update button
        const connectBtn = notionCard.querySelector('.platform-connect-btn');
        if (connectBtn) {
            connectBtn.textContent = '연결됨';
            connectBtn.disabled = true;
            connectBtn.classList.add('connected');
        }

        // Update status
        const statusElement = notionCard.querySelector('.platform-status');
        if (statusElement) {
            statusElement.textContent = '연결됨';
            statusElement.className = 'platform-status connected';
        }

        // Console log removed
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

// Initialize Notion Calendar Manager
window.notionManager = new NotionCalendarManager();

// Console log removed