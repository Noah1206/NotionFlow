// Calendar View Controller - Manages switching between different calendar views

class CalendarViewController {
    constructor() {
        this.currentView = 'week'; // Default to Google Calendar Grid
        this.googleCalendarGrid = null;
        this.init();
    }
    
    init() {
        this.setupViewToggle();
        this.initializeDefaultView();
        // Console log removed
    }
    
    setupViewToggle() {
        // Add view toggle functionality - 연동하기 버튼은 제외
        document.querySelectorAll('.view-option').forEach(button => {
            // 연동하기 버튼은 스킵
            if (button.id === 'unified-sync-button') {
                return;
            }
            
            button.addEventListener('click', () => {
                const view = button.dataset.view;
                
                // data-view가 없는 버튼은 무시
                if (!view) {
                    // Console warn removed
                    return;
                }
                
                // Remove active from all view buttons (연동하기 버튼 제외)
                document.querySelectorAll('.view-option:not(#unified-sync-button)').forEach(btn => {
                    btn.classList.remove('active');
                });
                
                // Add active to clicked button
                button.classList.add('active');
                
                // Console log removed
                this.switchView(view);
            });
        });
    }
    
    initializeDefaultView() {
        // calendar-detail.js에서 이미 초기화를 처리하므로 여기서는 중복 처리하지 않음
        // calendar-detail.js의 initializeCalendar()가 기본 뷰를 설정함
        // Console log removed
    }
    
    switchView(view) {
        // undefined나 null 체크 추가
        if (!view) {
            // Console warn removed
            return;
        }
        
        this.currentView = view;
        
        switch (view) {
            case 'week':
                this.showGoogleCalendarGrid();
                break;
            case 'month':
                this.showMonthView();
                break;
            case 'agenda':
                this.showAgendaView();
                break;
            default:
                // Console warn removed
        }
    }
    
    showGoogleCalendarGrid() {
        // Hide main calendar view
        const mainCalendar = document.getElementById('main-calendar');
        if (mainCalendar) {
            mainCalendar.style.display = 'none';
        }

        // Hide fallback time grid completely
        const fallbackGrid = document.getElementById('fallback-time-grid');
        if (fallbackGrid) {
            fallbackGrid.style.display = 'none';
        }
        
        // Show Google Calendar container
        const container = document.getElementById('calendar-grid-container');
        if (container) {
            container.style.display = 'block';
            
            // Initialize Google Calendar Grid if not already done
            if (!this.googleCalendarGrid) {
                // Wait for GoogleCalendarGrid class to be available
                if (typeof GoogleCalendarGrid !== 'undefined') {
                    this.googleCalendarGrid = new GoogleCalendarGrid(container);
                } else {
                    // Console warn removed
                    setTimeout(() => {
                        if (typeof GoogleCalendarGrid !== 'undefined') {
                            this.googleCalendarGrid = new GoogleCalendarGrid(container);
                        }
                    }, 500);
                }
            }
        }
    }
    
    showMonthView() {
        // Hide Google Calendar Grid
        const container = document.getElementById('google-calendar-container');
        if (container) {
            container.style.display = 'none';
        }

        // Hide fallback time grid completely (never show it)
        const fallbackGrid = document.getElementById('fallback-time-grid');
        if (fallbackGrid) {
            fallbackGrid.style.display = 'none';
        }

        // Call proper month view from calendar-detail.js
        if (typeof switchView === 'function') {
            switchView('month');
        } else if (typeof renderMainCalendar === 'function') {
            renderMainCalendar();
        }
    }
    
    showAgendaView() {
        // Console log removed
        
        // Hide other views
        const container = document.getElementById('google-calendar-container');
        if (container) {
            container.style.display = 'none';
        }
        
        const fallbackGrid = document.getElementById('fallback-time-grid');
        if (fallbackGrid) {
            fallbackGrid.style.display = 'none';
        }
        
        // TODO: Implement agenda view
        showNotification('일정 보기는 곧 추가될 예정입니다', 'info');
    }
    
    // Public methods to interact with current view
    getCurrentView() {
        return this.currentView;
    }
    
    refreshCurrentView() {
        this.switchView(this.currentView);
    }
    
    // Navigate to specific date in current view
    navigateToDate(date) {
        if (this.currentView === 'week' && this.googleCalendarGrid) {
            // Update Google Calendar Grid to show the specified week
            this.googleCalendarGrid.currentDate = new Date(date);
            this.googleCalendarGrid.weekStart = this.googleCalendarGrid.getWeekStart(date);
            this.googleCalendarGrid.render();
            this.googleCalendarGrid.attachEventListeners();
            this.googleCalendarGrid.updateCurrentTimeIndicator();
        }
    }
    
    // Add event to current view
    addEventToCurrentView(eventData) {
        if (this.currentView === 'week' && this.googleCalendarGrid) {
            this.googleCalendarGrid.events.push(eventData);
            this.googleCalendarGrid.renderEvent(eventData);
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Wait for other scripts to load
    setTimeout(() => {
        window.calendarViewController = new CalendarViewController();
    }, 200);
});

// Export for global access
window.CalendarViewController = CalendarViewController;