/**
 * 📅 CalendarDropdown Component
 * Calendar selection dropdown with platform connection status
 */

class CalendarDropdown {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            placeholder: '캘린더를 선택하세요',
            showConnectionStatus: true,
            allowMultiSelect: false,
            onSelect: null,
            onConnectionClick: null,
            ...options
        };
        
        this.calendars = [];
        this.selectedCalendar = null;
        this.isOpen = false;
        
        this.init();
    }
    
    async init() {
        await this.loadCalendars();
        this.render();
        this.attachEventListeners();
    }
    
    async loadCalendars() {
        try {
            // Load user calendars with connection info
            const response = await fetch('/api/calendars/connections/summary');
            const data = await response.json();
            
            if (data.success) {
                this.calendars = Object.entries(data.connections_by_calendar).map(([calendarId, calendarData]) => {
                    return {
                        id: calendarId,
                        name: calendarData.calendar_name,
                        platforms: calendarData.platforms,
                        total_connections: calendarData.platforms.length,
                        active_connections: calendarData.platforms.filter(p => p.is_connected && p.sync_enabled).length,
                        health_status: this.calculateHealthStatus(calendarData.platforms)
                    };
                });
            }
        } catch (error) {
            console.error('Failed to load calendars:', error);
            // Fallback: load basic calendar list
            await this.loadBasicCalendars();
        }
    }
    
    async loadBasicCalendars() {
        try {
            // This would be a basic calendar endpoint without connection info
            // For now, create mock data structure
            this.calendars = [
                {
                    id: 'default',
                    name: '기본 캘린더',
                    platforms: [],
                    total_connections: 0,
                    active_connections: 0,
                    health_status: 'no_connections'
                }
            ];
        } catch (error) {
            console.error('Failed to load basic calendars:', error);
        }
    }
    
    calculateHealthStatus(platforms) {
        if (!platforms || platforms.length === 0) return 'no_connections';
        
        const healthyPlatforms = platforms.filter(p => p.health_status === 'healthy' && p.is_connected);
        const totalConnected = platforms.filter(p => p.is_connected).length;
        
        if (totalConnected === 0) return 'no_connections';
        if (healthyPlatforms.length === totalConnected) return 'healthy';
        if (healthyPlatforms.length > 0) return 'partial';
        return 'error';
    }
    
    render() {
        if (!this.container) return;
        
        const selectedText = this.selectedCalendar 
            ? this.selectedCalendar.name 
            : this.options.placeholder;
        
        const dropdownItems = this.calendars.map(calendar => this.createDropdownItem(calendar)).join('');
        
        this.container.innerHTML = `
            <div class="calendar-dropdown ${this.isOpen ? 'open' : ''}" data-dropdown>
                <div class="dropdown-trigger" role="button" tabindex="0" aria-haspopup="listbox" aria-expanded="${this.isOpen}">
                    <div class="trigger-content">
                        <div class="trigger-icon">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                                <line x1="16" y1="2" x2="16" y2="6"></line>
                                <line x1="8" y1="2" x2="8" y2="6"></line>
                                <line x1="3" y1="10" x2="21" y2="10"></line>
                            </svg>
                        </div>
                        <span class="trigger-text">${selectedText}</span>
                        ${this.selectedCalendar && this.options.showConnectionStatus ? this.createConnectionBadge(this.selectedCalendar) : ''}
                    </div>
                    <div class="trigger-arrow">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="6,9 12,15 18,9"></polyline>
                        </svg>
                    </div>
                </div>
                
                <div class="dropdown-menu" role="listbox">
                    <div class="dropdown-header">
                        <span class="dropdown-title">캘린더 선택</span>
                        <span class="dropdown-subtitle">${this.calendars.length}개의 캘린더</span>
                    </div>
                    
                    <div class="dropdown-items">
                        ${dropdownItems}
                    </div>
                    
                    <div class="dropdown-footer">
                        <button class="btn-add-calendar" type="button">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <line x1="12" y1="5" x2="12" y2="19"></line>
                                <line x1="5" y1="12" x2="19" y2="12"></line>
                            </svg>
                            새 캘린더 추가
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Re-attach event listeners after re-render
        this.attachEventListeners();
    }
    
    createDropdownItem(calendar) {
        const isSelected = this.selectedCalendar && this.selectedCalendar.id === calendar.id;
        const healthBadge = this.options.showConnectionStatus ? this.createConnectionBadge(calendar) : '';
        
        return `
            <div class="dropdown-item ${isSelected ? 'selected' : ''}" 
                 data-calendar-id="${calendar.id}" 
                 role="option" 
                 aria-selected="${isSelected}">
                <div class="item-content">
                    <div class="item-main">
                        <div class="item-icon">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                                <line x1="16" y1="2" x2="16" y2="6"></line>
                                <line x1="8" y1="2" x2="8" y2="6"></line>
                                <line x1="3" y1="10" x2="21" y2="10"></line>
                            </svg>
                        </div>
                        <div class="item-details">
                            <div class="item-name">${calendar.name}</div>
                            <div class="item-stats">${calendar.active_connections}/${calendar.total_connections} 연결됨</div>
                        </div>
                    </div>
                    
                    <div class="item-actions">
                        ${healthBadge}
                        ${calendar.total_connections > 0 ? `
                            <button class="btn-manage-connections" data-calendar-id="${calendar.id}" title="연결 관리">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <circle cx="12" cy="12" r="3"></circle>
                                    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1 -1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
                                </svg>
                            </button>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    }
    
    createConnectionBadge(calendar) {
        const { health_status, active_connections, total_connections } = calendar;
        
        let badgeClass = 'connection-badge';
        let badgeText = '';
        let badgeIcon = '';
        
        switch (health_status) {
            case 'healthy':
                badgeClass += ' healthy';
                badgeText = '정상';
                badgeIcon = '✓';
                break;
            case 'partial':
                badgeClass += ' warning';
                badgeText = '일부';
                badgeIcon = '⚠';
                break;
            case 'error':
                badgeClass += ' error';
                badgeText = '오류';
                badgeIcon = '✗';
                break;
            case 'no_connections':
                badgeClass += ' inactive';
                badgeText = '미연결';
                badgeIcon = '○';
                break;
            default:
                badgeClass += ' inactive';
                badgeText = '알 수 없음';
                badgeIcon = '?';
        }
        
        return `<span class="${badgeClass}" title="${active_connections}/${total_connections} 플랫폼 연결됨">${badgeIcon} ${badgeText}</span>`;
    }
    
    attachEventListeners() {
        // Main dropdown events
        const trigger = this.container.querySelector('.dropdown-trigger');
        const menu = this.container.querySelector('.dropdown-menu');
        
        if (trigger) {
            trigger.addEventListener('click', this.toggleDropdown.bind(this));
            trigger.addEventListener('keydown', this.handleTriggerKeydown.bind(this));
        }
        
        // Item selection events
        const items = this.container.querySelectorAll('.dropdown-item');
        items.forEach(item => {
            item.addEventListener('click', this.handleItemClick.bind(this));
            item.addEventListener('keydown', this.handleItemKeydown.bind(this));
        });
        
        // Connection management events
        const connectionButtons = this.container.querySelectorAll('.btn-manage-connections');
        connectionButtons.forEach(button => {
            button.addEventListener('click', this.handleConnectionClick.bind(this));
        });
        
        // Add calendar button
        const addCalendarBtn = this.container.querySelector('.btn-add-calendar');
        if (addCalendarBtn) {
            addCalendarBtn.addEventListener('click', this.handleAddCalendar.bind(this));
        }
        
        // Outside click to close dropdown
        document.addEventListener('click', this.handleOutsideClick.bind(this));
        
        // Escape key to close dropdown
        document.addEventListener('keydown', this.handleEscape.bind(this));
    }
    
    toggleDropdown() {
        this.isOpen = !this.isOpen;
        this.render();
    }
    
    closeDropdown() {
        if (this.isOpen) {
            this.isOpen = false;
            this.render();
        }
    }
    
    handleTriggerKeydown(event) {
        if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            this.toggleDropdown();
        } else if (event.key === 'ArrowDown') {
            event.preventDefault();
            if (!this.isOpen) {
                this.toggleDropdown();
            }
            // Focus first item
            setTimeout(() => {
                const firstItem = this.container.querySelector('.dropdown-item');
                if (firstItem) firstItem.focus();
            }, 0);
        }
    }
    
    handleItemClick(event) {
        // Don't close dropdown if clicking on action buttons
        if (event.target.closest('.btn-manage-connections')) {
            return;
        }
        
        const item = event.currentTarget;
        const calendarId = item.dataset.calendarId;
        
        this.selectCalendar(calendarId);
    }
    
    handleItemKeydown(event) {
        if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            this.handleItemClick(event);
        } else if (event.key === 'ArrowDown') {
            event.preventDefault();
            const nextItem = event.currentTarget.nextElementSibling;
            if (nextItem) nextItem.focus();
        } else if (event.key === 'ArrowUp') {
            event.preventDefault();
            const prevItem = event.currentTarget.previousElementSibling;
            if (prevItem) prevItem.focus();
        }
    }
    
    handleConnectionClick(event) {
        event.stopPropagation();
        
        const calendarId = event.currentTarget.dataset.calendarId;
        const calendar = this.calendars.find(c => c.id === calendarId);
        
        if (this.options.onConnectionClick) {
            this.options.onConnectionClick(calendar);
        } else {
            // Default: open calendar connection management
            this.openConnectionManagement(calendar);
        }
    }
    
    handleAddCalendar(event) {
        event.stopPropagation();
        // This would typically open a calendar creation modal
        console.log('Add new calendar clicked');
        this.showNotification('새 캘린더 추가 기능은 곧 제공될 예정입니다', 'info');
    }
    
    handleOutsideClick(event) {
        if (this.isOpen && !this.container.contains(event.target)) {
            this.closeDropdown();
        }
    }
    
    handleEscape(event) {
        if (event.key === 'Escape' && this.isOpen) {
            this.closeDropdown();
        }
    }
    
    selectCalendar(calendarId) {
        const calendar = this.calendars.find(c => c.id === calendarId);
        if (calendar) {
            this.selectedCalendar = calendar;
            this.closeDropdown();
            
            if (this.options.onSelect) {
                this.options.onSelect(calendar);
            }
        }
    }
    
    openConnectionManagement(calendar) {
        // This would typically open a detailed connection management interface
        // For now, we'll show connection information
        this.showConnectionModal(calendar);
    }
    
    showConnectionModal(calendar) {
        const modalHtml = `
            <div class="calendar-connection-modal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>${calendar.name} 연결 관리</h3>
                        <button class="modal-close">&times;</button>
                    </div>
                    
                    <div class="modal-body">
                        <div class="connection-summary">
                            <div class="summary-stat">
                                <span class="stat-value">${calendar.active_connections}</span>
                                <span class="stat-label">활성 연결</span>
                            </div>
                            <div class="summary-stat">
                                <span class="stat-value">${calendar.total_connections}</span>
                                <span class="stat-label">총 연결</span>
                            </div>
                            <div class="summary-stat">
                                <span class="stat-value ${calendar.health_status}">${this.getHealthStatusText(calendar.health_status)}</span>
                                <span class="stat-label">상태</span>
                            </div>
                        </div>
                        
                        <div class="platform-connections">
                            ${calendar.platforms.map(platform => this.createPlatformConnectionItem(platform, calendar.id)).join('')}
                        </div>
                    </div>
                    
                    <div class="modal-footer">
                        <button class="btn-secondary modal-close">닫기</button>
                        <button class="btn-primary" onclick="window.location.href='/calendar/${calendar.id}'">상세 관리</button>
                    </div>
                </div>
            </div>
        `;
        
        // Add modal to document
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = modalHtml;
        document.body.appendChild(modal);
        
        // Add close event listeners
        const closeButtons = modal.querySelectorAll('.modal-close');
        closeButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                document.body.removeChild(modal);
            });
        });
        
        // Close on outside click
        modal.addEventListener('click', (event) => {
            if (event.target === modal) {
                document.body.removeChild(modal);
            }
        });
    }
    
    createPlatformConnectionItem(platform, calendarId) {
        const statusClass = platform.is_connected ? 'connected' : 'disconnected';
        const statusText = platform.is_connected ? '연결됨' : '연결 안됨';
        
        return `
            <div class="platform-connection-item ${statusClass}">
                <div class="platform-info">
                    <div class="platform-name">${platform.platform_name}</div>
                    <div class="platform-status">${statusText}</div>
                </div>
                <div class="platform-actions">
                    ${platform.is_connected ? `
                        <button class="btn-disconnect" data-platform="${platform.platform}" data-calendar="${calendarId}">연결 해제</button>
                    ` : `
                        <button class="btn-connect" data-platform="${platform.platform}" data-calendar="${calendarId}">연결</button>
                    `}
                </div>
            </div>
        `;
    }
    
    getHealthStatusText(status) {
        const statusTexts = {
            healthy: '정상',
            partial: '일부 문제',
            error: '오류',
            no_connections: '연결 없음'
        };
        return statusTexts[status] || '알 수 없음';
    }
    
    // Public methods
    getSelectedCalendar() {
        return this.selectedCalendar;
    }
    
    setSelectedCalendar(calendarId) {
        this.selectCalendar(calendarId);
    }
    
    refresh() {
        this.loadCalendars().then(() => {
            this.render();
        });
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
}

// Export for use in other files
window.CalendarDropdown = CalendarDropdown;