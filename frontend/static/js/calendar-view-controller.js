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
        console.log('📋 Calendar View Controller initialized');
    }
    
    setupViewToggle() {
        // Add view toggle functionality
        document.querySelectorAll('.view-option').forEach(button => {
            button.addEventListener('click', () => {
                // Remove active from all buttons
                document.querySelectorAll('.view-option').forEach(btn => btn.classList.remove('active'));
                // Add active to clicked button
                button.classList.add('active');
                
                const view = button.dataset.view;
                console.log(`🔄 Switching to ${view} view`);
                this.switchView(view);
            });
        });
    }
    
    initializeDefaultView() {
        // Default to week view (Google Calendar Grid)
        setTimeout(() => {
            const weekButton = document.querySelector('.view-option[data-view="week"]');
            if (weekButton) {
                weekButton.classList.add('active');
                this.switchView('week');
            }
        }, 100);
    }
    
    switchView(view) {
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
                console.warn('Unknown view:', view);
        }
    }
    
    showGoogleCalendarGrid() {
        console.log('📅 Initializing Google Calendar Grid view');
        
        // Hide other views
        const fallbackGrid = document.getElementById('fallback-time-grid');
        if (fallbackGrid) {
            fallbackGrid.style.display = 'none';
        }
        
        // Show Google Calendar container
        const container = document.getElementById('google-calendar-container');
        if (container) {
            container.style.display = 'block';
            
            // Initialize Google Calendar Grid if not already done
            if (!this.googleCalendarGrid) {
                // Wait for GoogleCalendarGrid class to be available
                if (typeof GoogleCalendarGrid !== 'undefined') {
                    this.googleCalendarGrid = new GoogleCalendarGrid(container);
                } else {
                    console.warn('GoogleCalendarGrid class not available, trying again...');
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
        console.log('📅 Switching to month view');
        
        // Hide Google Calendar Grid
        const container = document.getElementById('google-calendar-container');
        if (container) {
            container.style.display = 'none';
        }
        
        // Show fallback time grid or create month view
        const fallbackGrid = document.getElementById('fallback-time-grid');
        if (fallbackGrid) {
            fallbackGrid.style.display = 'block';
            
            // Initialize original time grid if needed
            if (typeof initializeTimeGrid === 'function') {
                initializeTimeGrid();
            }
        }
        
        // TODO: Implement proper month view
        showNotification('월 보기는 곧 추가될 예정입니다', 'info');
    }
    
    showAgendaView() {
        console.log('📅 Switching to agenda view');
        
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