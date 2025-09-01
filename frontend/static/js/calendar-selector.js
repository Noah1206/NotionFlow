/**
 * Calendar Selector Module
 * 캘린더 목록을 표시하고 선택된 캘린더의 이벤트를 가져오는 모듈
 */

class CalendarSelector {
    constructor() {
        this.selectedCalendars = new Set();
        this.calendars = [];
        this.events = [];
        this.onSelectionChange = null;
    }

    /**
     * Initialize calendar selector
     */
    async init(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error('Calendar selector container not found');
            return;
        }

        this.onSelectionChange = options.onSelectionChange || null;
        
        // Load calendars
        await this.loadCalendars();
        
        // Render UI
        this.render();
        
        // Load initial events
        await this.loadEvents();
    }

    /**
     * Load user calendars
     */
    async loadCalendars() {
        try {
            const response = await fetch('/api/user/calendars');
            if (!response.ok) throw new Error('Failed to load calendars');
            
            const data = await response.json();
            this.calendars = [...(data.personal_calendars || []), ...(data.shared_calendars || [])];
            
            // Select all calendars by default
            this.calendars.forEach(cal => this.selectedCalendars.add(cal.id));
            
            return this.calendars;
        } catch (error) {
            console.error('Error loading calendars:', error);
            return [];
        }
    }

    /**
     * Load events for selected calendars
     */
    async loadEvents() {
        if (this.selectedCalendars.size === 0) {
            this.events = [];
            if (this.onSelectionChange) {
                this.onSelectionChange([], []);
            }
            return [];
        }

        try {
            const calendarIds = Array.from(this.selectedCalendars);
            const params = new URLSearchParams();
            calendarIds.forEach(id => params.append('calendar_ids[]', id));
            params.append('days_ahead', '30');
            
            const response = await fetch(`/api/calendar/events?${params}`);
            if (!response.ok) throw new Error('Failed to load events');
            
            const data = await response.json();
            this.events = data.events || [];
            
            // Notify listener
            if (this.onSelectionChange) {
                this.onSelectionChange(this.events, calendarIds);
            }
            
            return this.events;
        } catch (error) {
            console.error('Error loading events:', error);
            return [];
        }
    }

    /**
     * Render calendar selector UI
     */
    render() {
        if (!this.container) return;

        const html = `
            <div class="calendar-selector">
                <div class="calendar-selector-header">
                    <h3>내 캘린더</h3>
                    <div class="selector-actions">
                        <button class="btn-select-all" onclick="calendarSelector.selectAll()">
                            전체 선택
                        </button>
                        <button class="btn-select-none" onclick="calendarSelector.selectNone()">
                            선택 해제
                        </button>
                    </div>
                </div>
                <div class="calendar-list">
                    ${this.calendars.map(cal => this.renderCalendarItem(cal)).join('')}
                </div>
                ${this.calendars.length === 0 ? `
                    <div class="no-calendars">
                        <p>캘린더가 없습니다.</p>
                        <a href="/dashboard/calendars" class="btn-create-calendar">캘린더 만들기</a>
                    </div>
                ` : ''}
            </div>
        `;

        this.container.innerHTML = html;
        
        // Add event listeners
        this.attachEventListeners();
    }

    /**
     * Render individual calendar item
     */
    renderCalendarItem(calendar) {
        const isChecked = this.selectedCalendars.has(calendar.id);
        const eventCount = calendar.event_count || 0;
        
        return `
            <div class="calendar-item ${isChecked ? 'selected' : ''}" data-calendar-id="${calendar.id}">
                <label class="calendar-checkbox-label">
                    <input type="checkbox" 
                           class="calendar-checkbox" 
                           value="${calendar.id}"
                           ${isChecked ? 'checked' : ''}
                           onchange="calendarSelector.toggleCalendar('${calendar.id}')">
                    <div class="calendar-info">
                        <div class="calendar-color-dot" style="background-color: ${calendar.color || '#3B82F6'}"></div>
                        <span class="calendar-name">${calendar.name}</span>
                        <span class="calendar-event-count">${eventCount}개 이벤트</span>
                    </div>
                </label>
            </div>
        `;
    }

    /**
     * Toggle calendar selection
     */
    toggleCalendar(calendarId) {
        if (this.selectedCalendars.has(calendarId)) {
            this.selectedCalendars.delete(calendarId);
        } else {
            this.selectedCalendars.add(calendarId);
        }
        
        // Update UI
        const item = this.container.querySelector(`[data-calendar-id="${calendarId}"]`);
        if (item) {
            item.classList.toggle('selected');
        }
        
        // Reload events
        this.loadEvents();
    }

    /**
     * Select all calendars
     */
    selectAll() {
        this.calendars.forEach(cal => this.selectedCalendars.add(cal.id));
        this.render();
        this.loadEvents();
    }

    /**
     * Deselect all calendars
     */
    selectNone() {
        this.selectedCalendars.clear();
        this.render();
        this.loadEvents();
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Already handled inline for simplicity
    }

    /**
     * Get selected calendar IDs
     */
    getSelectedCalendarIds() {
        return Array.from(this.selectedCalendars);
    }

    /**
     * Get current events
     */
    getEvents() {
        return this.events;
    }
}

// Create global instance
const calendarSelector = new CalendarSelector();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CalendarSelector;
}