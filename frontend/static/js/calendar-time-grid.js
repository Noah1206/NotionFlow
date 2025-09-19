// Google Calendar Style Time Grid JavaScript - Updated 2025-08-25 15:30 for height fix

// Force CSS override immediately on load
document.addEventListener('DOMContentLoaded', function() {
    const style = document.createElement('style');
    style.textContent = `
        .hour-line { 
            height: 60px !important; 
            min-height: 60px !important; 
            max-height: 60px !important; 
        }
    `;
    document.head.appendChild(style);
});

// Time grid configuration
const TIME_GRID_CONFIG = {
    startHour: 0,   // Start at 12 AM (midnight)
    endHour: 23,    // End at 11 PM
    defaultViewStart: 7, // Default visible start at 7 AM
    hourHeight: 60, // Fixed to match CSS styling (60px per hour)
    snapMinutes: 15, // Snap to 15-minute intervals
    showHalfHours: true, // Show 30-minute marks
    showQuarterHours: true, // Show 15-minute marks
    compactMode: false // More detailed view
};

// Professional event color schemes for Linear/Slack style
const EVENT_COLOR_SCHEMES = [
    { name: 'blue', color: '#3b82f6' },
    { name: 'green', color: '#10b981' },
    { name: 'orange', color: '#f59e0b' },
    { name: 'red', color: '#ef4444' },
    { name: 'purple', color: '#8b5cf6' },
    { name: 'pink', color: '#ec4899' },
    { name: 'indigo', color: '#6366f1' },
    { name: 'slate', color: '#64748b' }
];

// Get random color scheme from the palette
function getRandomEventColorScheme() {
    const scheme = EVENT_COLOR_SCHEMES[Math.floor(Math.random() * EVENT_COLOR_SCHEMES.length)];
    return scheme;
}

// Adjust color brightness for borders
function adjustColorBrightness(color, percent) {
    // Convert hex to RGB
    const num = parseInt(color.replace('#', ''), 16);
    const amt = Math.round(2.55 * percent);
    const R = (num >> 16) + amt;
    const G = (num >> 8 & 0x00FF) + amt;
    const B = (num & 0x0000FF) + amt;
    
    // Convert back to hex
    return '#' + (0x1000000 + (R < 255 ? R < 1 ? 0 : R : 255) * 0x10000 +
        (G < 255 ? G < 1 ? 0 : G : 255) * 0x100 +
        (B < 255 ? B < 1 ? 0 : B : 255))
        .toString(16)
        .slice(1);
}

// Current view state
let timeGridView = 'week'; // 'week' or 'day'
let currentWeekStart = null;
let selectedEvent = null;
let isDragging = false;
let isResizing = false;
let isCreatingEvent = false;
let dragStartY = 0;
let dragStartTime = null;
let originalEventData = null;
let newEventPreview = null;
let createStartY = 0;
let createStartX = 0;

// Initialize time grid with enhanced features
function initializeTimeGrid() {
    // console.log('🕒 Initializing enhanced time grid view...');
    
    // Set current week start - use today if currentDate is not defined
    const baseDate = (typeof currentDate !== 'undefined') ? currentDate : new Date();
    currentWeekStart = getWeekStart(baseDate);
    
    // console.log('📅 Base date for time grid:', baseDate.toDateString());
    // console.log('📅 Current week start:', currentWeekStart.toDateString());
    
    // Render the time grid
    renderTimeGrid();
    
    // Load events
    loadTimeGridEvents();
    
    // Enhanced initialization sequence
    setTimeout(() => {
        // Auto-scroll to current time or default (increased delay for DOM readiness)
        autoScrollToCurrentTime();
        
        // Update current time indicator
        updateCurrentTimeIndicator();
        
        // Initialize live clock
        const clockInterval = startLiveClock();
        
        // Store interval for cleanup
        window.timeGridClockInterval = clockInterval;
        
        // console.log('⏰ Live clock and time indicator initialized');
    }, 300);
    
    // Update current time indicator every minute
    setInterval(updateCurrentTimeIndicator, 60000);
    
    // Initialize enhanced features
    initializeDragAndDrop();
    initializeContextMenu();
    initializeKeyboardShortcuts();
    
    // Add dynamic time navigation buttons
    addTimeNavigationControls();
    
    // console.log('✅ Enhanced time grid initialization complete');
}

// Add time navigation controls to the interface
function addTimeNavigationControls() {
    const topbar = document.querySelector('.topbar-right');
    if (!topbar) return;
    
    // Create time navigation container
    const timeNavContainer = document.createElement('div');
    timeNavContainer.className = 'time-navigation-controls';
    timeNavContainer.style.cssText = `
        display: flex;
        gap: 4px;
        margin-right: 8px;
        align-items: center;
    `;
    
    // Current time button
    const currentTimeBtn = document.createElement('button');
    currentTimeBtn.className = 'btn-time-nav';
    currentTimeBtn.title = '현재 시간으로 이동 (T)';
    currentTimeBtn.onclick = goToCurrentTime;
    currentTimeBtn.style.cssText = `
        padding: 4px 8px;
        border: 1px solid #e5e7eb;
        border-radius: 6px;
        background: white;
        color: #374151;
        font-size: 11px;
        cursor: pointer;
        transition: all 0.2s;
        display: flex;
        align-items: center;
        gap: 4px;
    `;
    
    // Add hover effects
    [currentTimeBtn].forEach(btn => {
        btn.onmouseenter = () => {
            btn.style.borderColor = '#3b82f6';
            btn.style.color = '#3b82f6';
        };
        btn.onmouseleave = () => {
            btn.style.borderColor = '#e5e7eb';
            btn.style.color = '#374151';
        };
    });
    
    timeNavContainer.appendChild(currentTimeBtn);
    
    // Insert before existing buttons
    const addEventBtn = topbar.querySelector('.btn-add-event');
    if (addEventBtn) {
        topbar.insertBefore(timeNavContainer, addEventBtn);
    } else {
        topbar.appendChild(timeNavContainer);
    }
}

// Cleanup function for when leaving the page
function cleanupTimeGrid() {
    if (window.timeGridClockInterval) {
        clearInterval(window.timeGridClockInterval);
        window.timeGridClockInterval = null;
    }
}

// Add cleanup on page unload
window.addEventListener('beforeunload', cleanupTimeGrid);

// Get the start of the week (Sunday)
function getWeekStart(date) {
    const d = new Date(date);
    const day = d.getDay();
    const diff = d.getDate() - day;
    return new Date(d.setDate(diff));
}

// Scroll to specific time
function scrollToTime(hour) {
    const timeGridBody = document.querySelector('.time-grid-body');
    if (!timeGridBody) {
        // console.log('⚠️ Cannot scroll: time-grid-body element not found');
        return;
    }
    
    // console.log('⏰ Scrolling to hour:', hour);
    
    // Calculate scroll position
    const hoursFromStart = hour - TIME_GRID_CONFIG.startHour;
    const scrollTop = hoursFromStart * TIME_GRID_CONFIG.hourHeight;
    
    // console.log('📍 Scroll to time calculation:', {
        hour: hour,
        hoursFromStart: hoursFromStart,
        scrollTop: scrollTop
    });
    
    // Use requestAnimationFrame to ensure DOM is fully rendered
    requestAnimationFrame(() => {
        // Smooth scroll to position
        timeGridBody.scrollTo({
            top: Math.max(0, scrollTop),
            behavior: 'smooth'
        });
        
        // console.log('✅ Scrolled to hour', hour, 'at position:', scrollTop);
    });
}

// Render the time grid structure
function renderTimeGrid() {
    // Render week header
    renderWeekHeader();
    
    // Render time labels
    renderTimeLabels();
    
    // Render grid lines
    renderGridLines();
}

// Render week header with days
function renderWeekHeader() {
    const headerContainer = document.getElementById('week-days-header');
    if (!headerContainer) return;
    
    headerContainer.innerHTML = '';
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    for (let i = 0; i < 7; i++) {
        const date = new Date(currentWeekStart);
        date.setDate(date.getDate() + i);
        
        const isToday = date.getTime() === today.getTime();
        
        const dayHeader = document.createElement('div');
        dayHeader.className = `day-header${isToday ? ' today' : ''}`;
        dayHeader.dataset.date = date.toISOString().split('T')[0];
        dayHeader.dataset.dayIndex = i;
        
        const dayName = date.toLocaleDateString('ko-KR', { weekday: 'short' });
        const dayDate = date.getDate();
        
        dayHeader.innerHTML = `
            <div class="day-name">${dayName}</div>
            <div class="day-date">${dayDate}</div>
        `;
        
        headerContainer.appendChild(dayHeader);
    }
}

// Render time labels with enhanced detail
function renderTimeLabels() {
    const labelsContainer = document.querySelector('.time-labels-column');
    if (!labelsContainer) return;
    
    labelsContainer.innerHTML = '';
    
    for (let hour = TIME_GRID_CONFIG.startHour; hour <= TIME_GRID_CONFIG.endHour; hour++) {
        const hourOffset = hour - TIME_GRID_CONFIG.startHour;
        const baseTop = hourOffset * TIME_GRID_CONFIG.hourHeight;
        
        // Main hour label
        const hourLabel = document.createElement('div');
        hourLabel.className = 'time-label main-hour';
        hourLabel.dataset.hour = hour;
        hourLabel.style.top = `${baseTop}px`; // Position at the hour line
        
        // Format hour display (12-hour format with AM/PM)
        let displayHour = hour;
        let ampm = 'AM';
        
        if (hour === 0) {
            displayHour = 12;
            ampm = 'AM';
        } else if (hour === 12) {
            displayHour = 12;
            ampm = 'PM';
        } else if (hour > 12) {
            displayHour = hour - 12;
            ampm = 'PM';
        }
        
        hourLabel.innerHTML = `
            <span class="hour-text">${displayHour}</span>
            <span class="ampm-text">${ampm}</span>
        `;
        labelsContainer.appendChild(hourLabel);
        
        // Add 30-minute mark if not the last hour
        if (TIME_GRID_CONFIG.showHalfHours && hour < TIME_GRID_CONFIG.endHour) {
            const halfHourLabel = document.createElement('div');
            halfHourLabel.className = 'time-label half-hour';
            halfHourLabel.dataset.hour = hour;
            halfHourLabel.dataset.minutes = 30;
            halfHourLabel.style.top = `${baseTop + TIME_GRID_CONFIG.hourHeight / 2}px`; // Position at 30 min
            halfHourLabel.innerHTML = '<span class="minute-text">30</span>';
            labelsContainer.appendChild(halfHourLabel);
        }
        
        // Add 15-minute marks if quarter hours are enabled
        if (TIME_GRID_CONFIG.showQuarterHours && hour < TIME_GRID_CONFIG.endHour) {
            [15, 45].forEach(minute => {
                if (minute === 30 && TIME_GRID_CONFIG.showHalfHours) return; // Skip 30 if already shown
                
                const quarterLabel = document.createElement('div');
                quarterLabel.className = 'time-label quarter-hour';
                quarterLabel.dataset.hour = hour;
                quarterLabel.dataset.minutes = minute;
                const fraction = minute / 60;
                quarterLabel.style.top = `${baseTop + TIME_GRID_CONFIG.hourHeight * fraction}px`; // Position at quarter marks
                quarterLabel.innerHTML = `<span class="minute-text">${minute}</span>`;
                labelsContainer.appendChild(quarterLabel);
            });
        }
    }
}

// Render enhanced grid lines with sub-divisions
function renderGridLines() {
    const gridContainer = document.getElementById('time-grid-lines');
    if (!gridContainer) return;
    
    gridContainer.innerHTML = '';
    
    // Calculate and set proper container height
    const totalHeight = (TIME_GRID_CONFIG.endHour - TIME_GRID_CONFIG.startHour + 1) * TIME_GRID_CONFIG.hourHeight;
    gridContainer.style.minHeight = `${totalHeight}px`;
    gridContainer.style.height = 'auto';
    
    // Add horizontal lines for each hour and sub-divisions
    const hoursCount = TIME_GRID_CONFIG.endHour - TIME_GRID_CONFIG.startHour + 1;
    
    for (let i = 0; i < hoursCount; i++) {
        const hour = TIME_GRID_CONFIG.startHour + i;
        const baseTop = i * TIME_GRID_CONFIG.hourHeight;
        
        // Main hour line (thicker)
        const hourLine = document.createElement('div');
        hourLine.className = 'hour-line'; // Match CSS class exactly
        hourLine.style.top = `${baseTop}px`;
        hourLine.style.height = `${TIME_GRID_CONFIG.hourHeight}px`;
        hourLine.style.minHeight = `${TIME_GRID_CONFIG.hourHeight}px`;
        hourLine.style.maxHeight = `${TIME_GRID_CONFIG.hourHeight}px`;
        hourLine.setAttribute('data-height', TIME_GRID_CONFIG.hourHeight);
        gridContainer.appendChild(hourLine);
        
        // Sub-division lines (30 min, 15 min, 45 min)
        if (i < hoursCount - 1) { // Don't add sub-lines after the last hour
            // 30-minute line
            if (TIME_GRID_CONFIG.showHalfHours) {
                const halfLine = document.createElement('div');
                halfLine.className = 'hour-line half'; // Use existing CSS classes
                halfLine.style.top = `${baseTop + TIME_GRID_CONFIG.hourHeight / 2}px`;
                gridContainer.appendChild(halfLine);
            }
            
            // 15 and 45-minute lines
            if (TIME_GRID_CONFIG.showQuarterHours) {
                [0.25, 0.75].forEach(fraction => {
                    if (fraction === 0.5 && TIME_GRID_CONFIG.showHalfHours) return; // Skip if 30min already shown
                    
                    const quarterLine = document.createElement('div');
                    quarterLine.className = 'hour-line quarter'; // Use existing CSS pattern
                    quarterLine.style.top = `${baseTop + TIME_GRID_CONFIG.hourHeight * fraction}px`;
                    gridContainer.appendChild(quarterLine);
                });
            }
        }
    }
    
    // Add vertical lines for each day with enhanced styling
    for (let i = 0; i < 7; i++) {
        const column = document.createElement('div');
        column.className = 'day-column';
        column.style.left = `${(i * 100) / 7}%`;
        column.style.width = `${100 / 7}%`;
        column.dataset.dayIndex = i;
        
        // Add subtle day separator
        if (i > 0) {
            const separator = document.createElement('div');
            separator.className = 'day-separator';
            separator.style.left = `${(i * 100) / 7}%`;
            gridContainer.appendChild(separator);
        }
        
        gridContainer.appendChild(column);
    }
    
    // Add time period highlights (morning, afternoon, evening)
    addTimePeriodHighlights(gridContainer);
}

// Add time period highlights function
function addTimePeriodHighlights(gridContainer) {
    const timePeriods = [
        { name: 'early-morning', start: 0, end: 6, color: 'rgba(59, 130, 246, 0.05)' },
        { name: 'morning', start: 6, end: 12, color: 'rgba(16, 185, 129, 0.05)' },
        { name: 'afternoon', start: 12, end: 18, color: 'rgba(245, 158, 11, 0.05)' },
        { name: 'evening', start: 18, end: 24, color: 'rgba(139, 92, 246, 0.05)' }
    ];
    
    timePeriods.forEach(period => {
        if (period.end > TIME_GRID_CONFIG.startHour && period.start <= TIME_GRID_CONFIG.endHour) {
            const highlight = document.createElement('div');
            highlight.className = `time-period-highlight ${period.name}`;
            
            const startHour = Math.max(period.start, TIME_GRID_CONFIG.startHour);
            const endHour = Math.min(period.end, TIME_GRID_CONFIG.endHour + 1);
            
            const top = (startHour - TIME_GRID_CONFIG.startHour) * TIME_GRID_CONFIG.hourHeight;
            const height = (endHour - startHour) * TIME_GRID_CONFIG.hourHeight;
            
            highlight.style.top = `${top}px`;
            highlight.style.height = `${height}px`;
            highlight.style.backgroundColor = period.color;
            highlight.style.width = '100%';
            highlight.style.pointerEvents = 'none';
            highlight.style.zIndex = '1';
            
            gridContainer.appendChild(highlight);
        }
    });
}

// Load and render events
async function loadTimeGridEvents() {
    const calendarId = document.querySelector('.calendar-workspace').dataset.calendarId;
    
    try {
        const response = await fetch(`/api/calendars/${calendarId}/events?start=${currentWeekStart.toISOString()}`);
        if (response.ok) {
            const data = await response.json();
            renderEvents(data.events || []);
        }
    } catch (error) {
        console.error('Failed to load events:', error);
        // Load demo events for testing
        // console.log('⚠️ API failed, loading demo events instead');
        loadDemoEvents();
    }
}

// Demo events for testing the enhanced time grid
function loadDemoEvents() {
    const demoEvents = [
        {
            id: 'demo0',
            title: 'wpqkf',
            start_time: new Date(currentWeekStart.getTime() + 24*60*60*1000).toISOString().replace('T00:', 'T02:'),
            end_time: new Date(currentWeekStart.getTime() + 24*60*60*1000).toISOString().replace('T00:', 'T04:'),
            color: 'blue'
        },
        {
            id: 'demo1',
            title: '🌅 모닝 미팅',
            start_time: new Date(currentWeekStart.getTime() + 24*60*60*1000).toISOString().replace('T00:', 'T09:'),
            end_time: new Date(currentWeekStart.getTime() + 24*60*60*1000).toISOString().replace('T00:', 'T09:').replace(':00.000Z', ':30.000Z'),
            color: 'green'
        },
        {
            id: 'demo2', 
            title: '☕ 커피 브레이크',
            start_time: new Date(currentWeekStart.getTime() + 24*60*60*1000).toISOString().replace('T00:', 'T15:'),
            end_time: new Date(currentWeekStart.getTime() + 24*60*60*1000).toISOString().replace('T00:', 'T15:').replace(':00.000Z', ':15.000Z'),
            color: 'green'
        },
        {
            id: 'demo3',
            title: '📊 프레젠테이션',
            start_time: new Date(currentWeekStart.getTime() + 2*24*60*60*1000).toISOString().replace('T00:', 'T14:'),
            end_time: new Date(currentWeekStart.getTime() + 2*24*60*60*1000).toISOString().replace('T00:', 'T16:'),
            color: 'purple'
        }
    ];
    
    renderEvents(demoEvents);
    // console.log('📅 Demo events loaded for enhanced time grid');
}

// Render events on the grid
function renderEvents(events) {
    const eventsLayer = document.getElementById('events-layer');
    if (!eventsLayer) return;
    
    // Clear existing events
    eventsLayer.innerHTML = '';
    
    // console.log('📅 Rendering events:', events);
    
    events.forEach(event => {
        // console.log('🔍 Processing event:', event);
        
        // Handle different field naming patterns
        const hasStartTime = event.start_time || event.start_datetime;
        const isAllDay = event.all_day || event.is_all_day;
        
        if (!hasStartTime || isAllDay) {
            // console.log('⏭️ Skipping event (no start time or all-day):', event.title);
            return; // Skip all-day events for now
        }
        
        const eventElement = createEventElement(event);
        if (eventElement) {
            eventsLayer.appendChild(eventElement);
        }
    });
    
    // Update time label positions based on events
    adjustTimeLabelsForEvents(events);
}

// Adjust time label positions to avoid overlapping with events
function adjustTimeLabelsForEvents(events) {
    const timeLabels = document.querySelectorAll('.time-label');
    const labelsColumn = document.querySelector('.time-labels-column');
    if (!labelsColumn) return;
    
    // Reset all labels to default position
    timeLabels.forEach(label => {
        label.style.transform = '';
        label.style.opacity = '1';
    });
    
    // Check for events at the start of each hour in the first column
    events.forEach(event => {
        if (!event.start_time || event.all_day) return;
        
        const startDate = new Date(event.start_time);
        const dayIndex = startDate.getDay();
        
        // Only adjust for events in the first visible column
        if (dayIndex === 0 || dayIndex === 1) {
            const startHour = startDate.getHours();
            const startMinutes = startDate.getMinutes();
            
            // Find the corresponding time label
            timeLabels.forEach(label => {
                const labelHour = parseInt(label.dataset.hour);
                
                // If event starts near this hour label (within 15 minutes)
                if (labelHour === startHour && startMinutes < 15) {
                    // Shift the label up slightly or reduce opacity
                    label.style.transform = 'translateY(-8px)';
                    label.style.opacity = '0.7';
                }
            });
        }
    });
}

// Create an event element
function createEventElement(event) {
    // Handle different API response field names
    const startDateTime = event.start_datetime || event.start_time;
    const endDateTime = event.end_datetime || event.end_time || startDateTime;
    
    const startDate = new Date(startDateTime);
    const endDate = new Date(endDateTime);
    
    // console.log('🎯 Creating event element:', {
        title: event.title,
        startDateTime: startDateTime,
        endDateTime: endDateTime,
        startDate: startDate,
        endDate: endDate
    });
    
    // Check if event is in current week
    const weekEnd = new Date(currentWeekStart);
    weekEnd.setDate(weekEnd.getDate() + 7);
    
    if (startDate >= weekEnd || endDate < currentWeekStart) {
        return null; // Event not in current week
    }
    
    // Calculate position
    const dayIndex = startDate.getDay();
    const startHour = startDate.getHours() + startDate.getMinutes() / 60;
    const endHour = endDate.getHours() + endDate.getMinutes() / 60;
    
    const top = (startHour - TIME_GRID_CONFIG.startHour) * TIME_GRID_CONFIG.hourHeight;
    const height = (endHour - startHour) * TIME_GRID_CONFIG.hourHeight;
    const left = (dayIndex * 100) / 7;
    const width = 100 / 7;
    
    // console.log('📐 Position calculation:', {
        dayIndex: dayIndex,
        startHour: startHour,
        endHour: endHour,
        top: top,
        height: height,
        left: left,
        TIME_GRID_CONFIG: TIME_GRID_CONFIG
    });
    
    // Assign color scheme if not set
    let colorScheme;
    if (!event.color || !event.colorScheme) {
        colorScheme = getRandomEventColorScheme();
        event.colorScheme = colorScheme.name;
        event.color = colorScheme.color;
    } else if (event.color && !event.colorScheme) {
        // Find matching color scheme by color
        colorScheme = EVENT_COLOR_SCHEMES.find(s => s.color === event.color) || EVENT_COLOR_SCHEMES[0];
        event.colorScheme = colorScheme.name;
    } else {
        colorScheme = EVENT_COLOR_SCHEMES.find(s => s.name === event.colorScheme) || EVENT_COLOR_SCHEMES[0];
    }
    
    // Create event block with color scheme class
    const eventBlock = document.createElement('div');
    eventBlock.className = `event-block ${colorScheme.name}`;
    eventBlock.dataset.eventId = event.id;
    eventBlock.style.top = `${top}px`;
    eventBlock.style.height = `${height}px`;
    eventBlock.style.left = `${left}%`;
    eventBlock.style.width = `calc(${width}% - 2px)`; // Reduced margin for wider blocks
    
    // Format time
    const startTimeStr = startDate.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
    const endTimeStr = endDate.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
    
    eventBlock.innerHTML = `
        <div class="node-dot"></div>
        <div class="status-badge"></div>
        <div class="resize-handle top"></div>
        <div class="event-title">${event.title}</div>
        <div class="event-time">${startTimeStr} - ${endTimeStr}</div>
        <div class="resize-handle bottom"></div>
    `;
    
    // Add event listeners
    eventBlock.addEventListener('mousedown', handleEventMouseDown);
    eventBlock.addEventListener('contextmenu', handleEventContextMenu);
    
    return eventBlock;
}

// Initialize drag and drop
function initializeDragAndDrop() {
    // console.log('🔧 Initializing drag and drop...');
    const eventsGrid = document.getElementById('events-grid');
    if (!eventsGrid) {
        // console.log('❌ events-grid not found');
        return;
    }
    
    // console.log('✅ events-grid found, adding event listeners');
    
    // Remove existing listeners to avoid duplicates
    eventsGrid.removeEventListener('mousedown', handleGridMouseDown);
    document.removeEventListener('mousemove', handleMouseMove);
    document.removeEventListener('mouseup', handleMouseUp);
    
    // Grid click to create new event
    eventsGrid.addEventListener('mousedown', handleGridMouseDown);
    
    // Global mouse events for dragging
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    
    // console.log('✅ Drag and drop initialized');
}

// Handle grid mouse down (create new event with drag)
function handleGridMouseDown(e) {
    // console.log('🖱️ Grid mousedown triggered', e.target);
    
    if (e.target.closest('.event-block')) {
        // console.log('🚫 Clicked on event block, ignoring');
        return; // Ignore if clicking on event
    }
    
    // console.log('✅ Starting event creation...');
    
    const rect = e.currentTarget.getBoundingClientRect();
    const relativeY = e.clientY - rect.top - 10; // Subtract padding-top
    const relativeX = e.clientX - rect.left;
    
    // console.log('📍 Click position:', { relativeX, relativeY });
    
    // Start creating new event
    isCreatingEvent = true;
    createStartY = relativeY;
    createStartX = relativeX;
    
    // Calculate day from X position
    const dayIndex = Math.floor((relativeX / rect.width) * 7);
    const dayColumnWidth = rect.width / 7;
    const leftPosition = (dayIndex * dayColumnWidth / rect.width) * 100;
    
    // Snap to grid
    const snappedY = Math.round(relativeY / (TIME_GRID_CONFIG.hourHeight / 4)) * (TIME_GRID_CONFIG.hourHeight / 4);
    
    // Create preview event block
    newEventPreview = document.createElement('div');
    newEventPreview.className = 'event-block event-preview';
    newEventPreview.style.position = 'absolute';
    newEventPreview.style.left = `${leftPosition}%`;
    newEventPreview.style.top = `${snappedY}px`;
    newEventPreview.style.height = `${TIME_GRID_CONFIG.hourHeight / 4}px`; // Minimum 15 minutes
    newEventPreview.style.width = `${100/7}%`;
    newEventPreview.style.backgroundColor = 'rgba(66, 133, 244, 0.7)';
    newEventPreview.style.border = '2px dashed #4285f4';
    newEventPreview.style.borderRadius = '6px';
    newEventPreview.style.zIndex = '1000';
    newEventPreview.innerHTML = '<div style="padding: 4px; font-size: 12px; color: white;">새 일정</div>';
    
    e.currentTarget.appendChild(newEventPreview);
    
    // Prevent text selection
    e.preventDefault();
}

// Handle event mouse down (drag or resize)
function handleEventMouseDown(e) {
    e.stopPropagation();
    
    const eventBlock = e.currentTarget;
    const resizeHandle = e.target.closest('.resize-handle');
    
    if (resizeHandle) {
        // Start resizing
        isResizing = true;
        selectedEvent = eventBlock;
        originalEventData = {
            height: parseInt(eventBlock.style.height),
            top: parseInt(eventBlock.style.top)
        };
        eventBlock.classList.add('selected');
    } else {
        // Start dragging
        isDragging = true;
        selectedEvent = eventBlock;
        dragStartY = e.clientY;
        dragStartTime = new Date();
        originalEventData = {
            top: parseInt(eventBlock.style.top),
            left: parseFloat(eventBlock.style.left)
        };
        eventBlock.classList.add('dragging');
    }
}

// Handle mouse move (dragging, resizing, or creating)
function handleMouseMove(e) {
    if (!isDragging && !isResizing && !isCreatingEvent) return;
    
    if (isCreatingEvent && newEventPreview) {
        const eventsGrid = document.getElementById('events-grid');
        const rect = eventsGrid.getBoundingClientRect();
        const currentY = e.clientY - rect.top - 10;
        
        // Calculate height based on drag distance
        const startY = Math.min(createStartY, currentY);
        const endY = Math.max(createStartY, currentY);
        const height = endY - startY;
        
        // Snap to grid
        const snappedStartY = Math.round(startY / (TIME_GRID_CONFIG.hourHeight / 4)) * (TIME_GRID_CONFIG.hourHeight / 4);
        const snappedHeight = Math.max(
            TIME_GRID_CONFIG.hourHeight / 4, // Minimum 15 minutes
            Math.round(height / (TIME_GRID_CONFIG.hourHeight / 4)) * (TIME_GRID_CONFIG.hourHeight / 4)
        );
        
        // Update preview block
        newEventPreview.style.top = `${snappedStartY}px`;
        newEventPreview.style.height = `${snappedHeight}px`;
        
        // Update time display in preview
        const startHour = (snappedStartY / TIME_GRID_CONFIG.hourHeight) + TIME_GRID_CONFIG.startHour;
        const duration = snappedHeight / TIME_GRID_CONFIG.hourHeight;
        const endHour = startHour + duration;
        
        const startTime = formatTime(startHour);
        const endTime = formatTime(endHour);
        newEventPreview.innerHTML = `<div style="padding: 4px; font-size: 12px; color: white;">새 일정<br>${startTime} - ${endTime}</div>`;
        
    } else if (isDragging && selectedEvent) {
        const deltaY = e.clientY - dragStartY;
        const newTop = originalEventData.top + deltaY;
        
        // Snap to grid
        const snappedTop = Math.round(newTop / (TIME_GRID_CONFIG.hourHeight / 4)) * (TIME_GRID_CONFIG.hourHeight / 4);
        selectedEvent.style.top = `${snappedTop}px`;
        
        // Update time display
        updateEventTimeDisplay(selectedEvent);
    } else if (isResizing && selectedEvent) {
        const rect = selectedEvent.parentElement.getBoundingClientRect();
        const relativeY = e.clientY - rect.top - 10; // Subtract padding-top
        const newHeight = relativeY - parseInt(selectedEvent.style.top);
        
        // Minimum height (15 minutes)
        const minHeight = TIME_GRID_CONFIG.hourHeight / 4;
        if (newHeight >= minHeight) {
            selectedEvent.style.height = `${newHeight}px`;
            updateEventTimeDisplay(selectedEvent);
        }
    }
}

// Handle mouse up (end drag, resize, or create)
async function handleMouseUp(e) {
    if (!isDragging && !isResizing && !isCreatingEvent) return;
    
    if (isCreatingEvent && newEventPreview) {
        // Get the time range from the preview block
        const top = parseInt(newEventPreview.style.top);
        const height = parseInt(newEventPreview.style.height);
        const leftPercent = parseFloat(newEventPreview.style.left);
        
        // Calculate start and end time
        const startHour = (top / TIME_GRID_CONFIG.hourHeight) + TIME_GRID_CONFIG.startHour;
        const duration = height / TIME_GRID_CONFIG.hourHeight;
        const endHour = startHour + duration;
        
        // Calculate day index
        const dayIndex = Math.floor(leftPercent / (100 / 7));
        
        // Create event date
        const eventDate = new Date(currentWeekStart);
        eventDate.setDate(eventDate.getDate() + dayIndex);
        
        // Set start time
        const startTime = new Date(eventDate);
        const startMinutes = (startHour % 1) * 60;
        startTime.setHours(Math.floor(startHour), Math.floor(startMinutes), 0, 0);
        
        // Set end time  
        const endTime = new Date(eventDate);
        const endMinutes = (endHour % 1) * 60;
        endTime.setHours(Math.floor(endHour), Math.floor(endMinutes), 0, 0);
        
        // Remove preview
        newEventPreview.remove();
        newEventPreview = null;
        
        // Open event creation modal with pre-filled times
        openEventModalWithTime(startTime, endTime);
        
    } else if (selectedEvent) {
        selectedEvent.classList.remove('dragging', 'selected');
        
        // Save the new position/size
        await saveEventChanges(selectedEvent);
    }
    
    isDragging = false;
    isResizing = false;
    isCreatingEvent = false;
    selectedEvent = null;
    originalEventData = null;
}

// Update event time display during drag/resize
function updateEventTimeDisplay(eventBlock) {
    const top = parseInt(eventBlock.style.top);
    const height = parseInt(eventBlock.style.height);
    
    const startHour = (top / TIME_GRID_CONFIG.hourHeight) + TIME_GRID_CONFIG.startHour;
    const duration = height / TIME_GRID_CONFIG.hourHeight;
    const endHour = startHour + duration;
    
    const startTime = formatTime(startHour);
    const endTime = formatTime(endHour);
    
    const timeElement = eventBlock.querySelector('.event-time');
    if (timeElement) {
        timeElement.textContent = `${startTime} - ${endTime}`;
    }
}

// Format time from decimal hours
function formatTime(decimalHours) {
    const hours = Math.floor(decimalHours);
    const minutes = Math.round((decimalHours % 1) * 60);
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
}

// Save event changes to server
async function saveEventChanges(eventBlock) {
    const eventId = eventBlock.dataset.eventId;
    const calendarId = document.querySelector('.calendar-workspace').dataset.calendarId;
    
    // Calculate new time from position
    const top = parseInt(eventBlock.style.top);
    const height = parseInt(eventBlock.style.height);
    const left = parseFloat(eventBlock.style.left);
    
    const dayIndex = Math.round((left / 100) * 7);
    const startHour = (top / TIME_GRID_CONFIG.hourHeight) + TIME_GRID_CONFIG.startHour;
    const duration = height / TIME_GRID_CONFIG.hourHeight;
    
    const newStartDate = new Date(currentWeekStart);
    newStartDate.setDate(newStartDate.getDate() + dayIndex);
    newStartDate.setHours(Math.floor(startHour), Math.round((startHour % 1) * 60), 0, 0);
    
    const newEndDate = new Date(newStartDate);
    newEndDate.setHours(newEndDate.getHours() + Math.floor(duration), newEndDate.getMinutes() + Math.round((duration % 1) * 60));
    
    try {
        const response = await fetch(`/api/calendar/events/${eventId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                start_time: newStartDate.toISOString(),
                end_time: newEndDate.toISOString()
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to update event');
        }
        
        showNotification('일정이 업데이트되었습니다', 'success');
    } catch (error) {
        console.error('Failed to save event:', error);
        showNotification('일정 업데이트 실패', 'error');
        
        // Revert changes
        if (originalEventData) {
            eventBlock.style.top = `${originalEventData.top}px`;
            if (originalEventData.height) {
                eventBlock.style.height = `${originalEventData.height}px`;
            }
            if (originalEventData.left !== undefined) {
                eventBlock.style.left = `${originalEventData.left}%`;
            }
        }
    }
}

// Handle event context menu
function handleEventContextMenu(e) {
    e.preventDefault();
    
    const eventBlock = e.currentTarget;
    const eventId = eventBlock.dataset.eventId;
    
    // Show context menu
    showEventContextMenu(e.clientX, e.clientY, eventId);
}

// Show event context menu
function showEventContextMenu(x, y, eventId) {
    // Remove existing menu
    const existingMenu = document.querySelector('.event-context-menu');
    if (existingMenu) {
        existingMenu.remove();
    }
    
    // Create menu
    const menu = document.createElement('div');
    menu.className = 'event-context-menu';
    menu.style.left = `${x}px`;
    menu.style.top = `${y}px`;
    menu.style.display = 'block';
    
    menu.innerHTML = `
        <div class="context-menu-item" onclick="editEvent('${eventId}')">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
            편집
        </div>
        <div class="context-menu-item" onclick="duplicateEvent('${eventId}')">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
            </svg>
            복제
        </div>
        <div class="context-menu-divider"></div>
        <div class="context-menu-item danger" onclick="deleteEvent('${eventId}')">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m3 0v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6h14"/>
            </svg>
            삭제
        </div>
    `;
    
    document.body.appendChild(menu);
    
    // Close menu on click outside
    setTimeout(() => {
        document.addEventListener('click', closeContextMenu);
    }, 0);
}

// Close context menu
function closeContextMenu() {
    const menu = document.querySelector('.event-context-menu');
    if (menu) {
        menu.remove();
    }
    document.removeEventListener('click', closeContextMenu);
}

// Initialize context menu
function initializeContextMenu() {
    // Close on escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeContextMenu();
        }
    });
}

// Enhanced current time indicator with dynamic updates
function updateCurrentTimeIndicator() {
    const indicator = document.getElementById('current-time-indicator');
    if (!indicator) {
        // console.log('🚨 Current time indicator element not found');
        return;
    }
    
    const now = new Date();
    const currentHour = now.getHours() + now.getMinutes() / 60;
    
    // console.log('🕐 Current time:', now.toLocaleTimeString('ko-KR'), 'Hour decimal:', currentHour);
    
    // Check if current time is within grid range
    if (currentHour < TIME_GRID_CONFIG.startHour || currentHour > TIME_GRID_CONFIG.endHour) {
        // console.log('⏰ Current time outside grid range:', TIME_GRID_CONFIG.startHour, 'to', TIME_GRID_CONFIG.endHour);
        indicator.style.display = 'none';
        return;
    }
    
    // Check if it's today
    const today = new Date();
    const weekStart = getWeekStart(today);
    const dayIndex = Math.floor((today - weekStart) / (24 * 60 * 60 * 1000));
    
    // console.log('📅 Today:', today.toDateString());
    // console.log('📅 Week start:', weekStart.toDateString());
    // console.log('📅 Current week start:', currentWeekStart ? currentWeekStart.toDateString() : 'undefined');
    // console.log('📅 Day index:', dayIndex);
    // console.log('📅 Week comparison:', Math.abs(currentWeekStart.getTime() - weekStart.getTime()));
    
    // Only show if we're viewing the current week and it's today
    if (currentWeekStart && Math.abs(currentWeekStart.getTime() - weekStart.getTime()) < 24 * 60 * 60 * 1000 && dayIndex >= 0 && dayIndex < 7) {
        // Calculate position from the start hour
        const top = (currentHour - TIME_GRID_CONFIG.startHour) * TIME_GRID_CONFIG.hourHeight;
        indicator.style.top = `${top}px`;
        indicator.style.display = 'block';
        
        // console.log('✅ Showing time indicator at position:', top + 'px');
        
        // Update the time indicator with current time
        const timeText = now.toLocaleTimeString('ko-KR', { 
            hour: '2-digit', 
            minute: '2-digit',
            hour12: false
        });
        
        // Add or update time display
        let timeDisplay = indicator.querySelector('.current-time-display');
        if (!timeDisplay) {
            timeDisplay = document.createElement('div');
            timeDisplay.className = 'current-time-display';
            indicator.appendChild(timeDisplay);
        }
        timeDisplay.textContent = timeText;
        
        // Highlight current time column
        highlightCurrentTimeColumn(dayIndex);
    } else {
        // console.log('❌ Not showing time indicator - week mismatch or invalid day index');
        indicator.style.display = 'none';
    }
}

// Highlight the current time column
function highlightCurrentTimeColumn(dayIndex) {
    // Remove previous highlights
    document.querySelectorAll('.day-column.current-day').forEach(col => {
        col.classList.remove('current-day');
    });
    
    // Add highlight to current day column
    const currentDayColumn = document.querySelector(`.day-column[data-day-index="${dayIndex}"]`);
    if (currentDayColumn) {
        currentDayColumn.classList.add('current-day');
    }
}

// Enhanced time navigation with smooth animations
function scrollToTime(hour, animate = true) {
    const timeGridBody = document.querySelector('.time-grid-body');
    if (!timeGridBody) return;
    
    // Calculate scroll position
    const hoursFromStart = hour - TIME_GRID_CONFIG.startHour;
    const scrollTop = hoursFromStart * TIME_GRID_CONFIG.hourHeight;
    
    // Smooth scroll to position
    timeGridBody.scrollTo({
        top: Math.max(0, scrollTop),
        behavior: animate ? 'smooth' : 'auto'
    });
    
    // Flash the target time label
    flashTimeLabel(hour);
}

// Flash animation for time labels
function flashTimeLabel(hour) {
    const timeLabel = document.querySelector(`.time-label[data-hour="${hour}"]`);
    if (timeLabel) {
        timeLabel.style.transition = 'background-color 0.3s ease';
        timeLabel.style.backgroundColor = 'rgba(59, 130, 246, 0.1)';
        
        setTimeout(() => {
            timeLabel.style.backgroundColor = '';
        }, 1000);
    }
}

// Auto-scroll to current time on page load with current time line centered
function autoScrollToCurrentTime() {
    // Ensure DOM is ready for scrolling
    const timeGridBody = document.querySelector('.time-grid-body');
    if (!timeGridBody) {
        // console.log('⚠️ Auto-scroll failed: time-grid-body element not found');
        return;
    }
    
    const now = new Date();
    const currentHour = now.getHours() + now.getMinutes() / 60; // Include minutes for precise positioning
    
    // console.log('🔄 Auto-scroll check - Current time:', now.toLocaleTimeString('ko-KR'));
    // console.log('🔄 Current hour decimal:', currentHour);
    
    // Check if we're viewing today for current time line display
    const today = new Date();
    const weekStart = getWeekStart(today);
    const isCurrentWeek = currentWeekStart && Math.abs(currentWeekStart.getTime() - weekStart.getTime()) < 24 * 60 * 60 * 1000;
    
    // console.log('🔄 Today:', today.toDateString());
    // console.log('🔄 Week start:', weekStart.toDateString());
    // console.log('🔄 Current week start:', currentWeekStart ? currentWeekStart.toDateString() : 'undefined');
    // console.log('🔄 Is current week:', isCurrentWeek);
    // console.log('🔄 Hour range check:', currentHour >= TIME_GRID_CONFIG.startHour && currentHour <= TIME_GRID_CONFIG.endHour);
    
    // Always auto-scroll to show appropriate time range for better UX
    if (isCurrentWeek && currentHour >= TIME_GRID_CONFIG.startHour && currentHour <= TIME_GRID_CONFIG.endHour) {
        // If it's current week and current time is in range, center the current time line
        // console.log('✅ Auto-scrolling to current time:', now.toLocaleTimeString('ko-KR'));
        scrollToCurrentTimeCentered();
    } else {
        // For any other case (different week or out of range), scroll to show working hours
        // Calculate optimal view position (around 9AM-10AM area like in the screenshot)
        const optimalHour = 9; // 9 AM for good visibility
        // console.log('⏰ Auto-scrolling to optimal view around:', optimalHour + 'AM for better visibility');
        scrollToTime(optimalHour);
    }
}

// Scroll to current time with the red line centered in viewport
function scrollToCurrentTimeCentered() {
    const timeGridBody = document.querySelector('.time-grid-body');
    if (!timeGridBody) {
        // console.log('⚠️ Cannot scroll: time-grid-body element not found');
        return;
    }
    
    const now = new Date();
    const currentHour = now.getHours() + now.getMinutes() / 60;
    
    // console.log('🎯 Centering current time line - Hour:', currentHour);
    
    // Calculate exact position of current time
    const hoursFromStart = currentHour - TIME_GRID_CONFIG.startHour;
    const currentTimePosition = hoursFromStart * TIME_GRID_CONFIG.hourHeight;
    
    // Get viewport height to center the current time line
    const viewportHeight = timeGridBody.clientHeight;
    const centerOffset = viewportHeight / 2;
    
    // Calculate scroll position to center current time line
    const scrollTop = Math.max(0, currentTimePosition - centerOffset);
    
    // console.log('📍 Scroll calculation:', {
        currentHour: currentHour,
        hoursFromStart: hoursFromStart,
        currentTimePosition: currentTimePosition,
        viewportHeight: viewportHeight,
        centerOffset: centerOffset,
        scrollTop: scrollTop
    });
    
    // Use requestAnimationFrame to ensure DOM is fully rendered
    requestAnimationFrame(() => {
        // Smooth scroll to centered position
        timeGridBody.scrollTo({
            top: scrollTop,
            behavior: 'smooth'
        });
        
        // console.log('🎯 Centered current time line in viewport at scroll position:', scrollTop);
    });
}

// Live clock update for better user experience
function startLiveClock() {
    // Update time display in header or other locations
    const updateLiveClock = () => {
        const now = new Date();
        const timeString = now.toLocaleTimeString('ko-KR', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        });
        
        // Update any live clock displays
        const liveClocks = document.querySelectorAll('.live-clock');
        liveClocks.forEach(clock => {
            clock.textContent = timeString;
        });
        
        // Update current time indicator every minute
        if (now.getSeconds() === 0) {
            updateCurrentTimeIndicator();
        }
    };
    
    // Update immediately and then every second
    updateLiveClock();
    return setInterval(updateLiveClock, 1000);
}

// Keyboard shortcuts for time navigation
function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Only handle shortcuts when not in input fields
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
        
        switch (e.key) {
            case 'Home':
                e.preventDefault();
                scrollToTime(TIME_GRID_CONFIG.startHour);
                break;
            case 'End':
                e.preventDefault();
                scrollToTime(TIME_GRID_CONFIG.endHour);
                break;
            case 'PageUp':
                e.preventDefault();
                scrollToTime(Math.max(TIME_GRID_CONFIG.startHour, getCurrentVisibleHour() - 4));
                break;
            case 'PageDown':
                e.preventDefault();
                scrollToTime(Math.min(TIME_GRID_CONFIG.endHour, getCurrentVisibleHour() + 4));
                break;
            case 'ArrowUp':
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    scrollToTime(Math.max(TIME_GRID_CONFIG.startHour, getCurrentVisibleHour() - 1));
                }
                break;
            case 'ArrowDown':
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    scrollToTime(Math.min(TIME_GRID_CONFIG.endHour, getCurrentVisibleHour() + 1));
                }
                break;
            case 't':
            case 'T':
                if (!e.ctrlKey && !e.metaKey) {
                    e.preventDefault();
                    goToCurrentTime();
                }
                break;
        }
    });
}

// Get currently visible hour
function getCurrentVisibleHour() {
    const timeGridBody = document.querySelector('.time-grid-body');
    if (!timeGridBody) return TIME_GRID_CONFIG.defaultViewStart;
    
    const scrollTop = timeGridBody.scrollTop;
    const visibleHour = Math.floor(scrollTop / TIME_GRID_CONFIG.hourHeight) + TIME_GRID_CONFIG.startHour;
    return Math.max(TIME_GRID_CONFIG.startHour, Math.min(TIME_GRID_CONFIG.endHour, visibleHour));
}

// Go to current time function
function goToCurrentTime() {
    const now = new Date();
    const currentHour = now.getHours();
    
    if (currentHour >= TIME_GRID_CONFIG.startHour && currentHour <= TIME_GRID_CONFIG.endHour) {
        // Use the new centered scroll function instead of scrollToTime
        scrollToCurrentTimeCentered();
        
        // Flash current time indicator
        const indicator = document.getElementById('current-time-indicator');
        if (indicator && indicator.style.display !== 'none') {
            indicator.style.animation = 'pulse 0.5s ease-in-out 2';
            setTimeout(() => {
                indicator.style.animation = 'pulse 2s ease-in-out infinite';
            }, 1000);
        }
        
        // Show notification
        if (window.showNotification) {
            showNotification('현재 시간으로 이동했습니다', 'info');
        }
        
        // console.log('🎯 Navigated to current time (centered):', now.toLocaleTimeString('ko-KR'));
    } else {
        if (window.showNotification) {
            showNotification('현재 시간이 표시 범위를 벗어났습니다', 'warning');
        }
        // console.log('⚠️ Current time is outside working hours range');
    }
}

// Open event modal with pre-filled time
function openEventModalWithTime(startDate, endDate = null) {
    // console.log('🕐 Opening event modal with time:', { startDate, endDate });
    
    const modal = document.getElementById('calendar-overlay-form');
    if (!modal) {
        console.error('❌ calendar-overlay-form modal not found');
        return;
    }
    
    // Set start time inputs
    const startDateInput = document.querySelector('#calendar-overlay-form input[name="start_date"]');
    const startTimeInput = document.querySelector('#calendar-overlay-form input[name="start_time"]');
    const endDateInput = document.querySelector('#calendar-overlay-form input[name="end_date"]');
    const endTimeInput = document.querySelector('#calendar-overlay-form input[name="end_time"]');
    
    // If no end date provided, default to 1 hour later
    const finalEndDate = endDate || (() => {
        const defaultEnd = new Date(startDate);
        defaultEnd.setHours(defaultEnd.getHours() + 1);
        return defaultEnd;
    })();
    
    // console.log('📅 Setting form values:', { start: startDate, end: finalEndDate });
    
    // Set date and time values
    if (startDateInput) startDateInput.value = formatDateForInput(startDate);
    if (startTimeInput) startTimeInput.value = formatTimeForInput(startDate);
    if (endDateInput) endDateInput.value = formatDateForInput(finalEndDate);
    if (endTimeInput) endTimeInput.value = formatTimeForInput(finalEndDate);
    
    // Set modal title
    const titleElement = document.querySelector('#calendar-overlay-form #overlay-form-title');
    if (titleElement) {
        titleElement.textContent = '새 일정';
    }
    
    // Show modal
    modal.style.display = 'flex';
    // console.log('✅ Event modal opened');
}

// Helper functions for date/time formatting
function formatDateForInput(date) {
    return date.toISOString().split('T')[0];
}

function formatTimeForInput(date) {
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    return `${hours}:${minutes}`;
}

// Format date for datetime-local input
function formatDateTimeLocal(date) {
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    
    return `${year}-${month}-${day}T${hours}:${minutes}`;
}

// Event operations
async function editEvent(eventId) {
    closeContextMenu();
    // Load event data and open edit modal
    const calendarId = document.querySelector('.calendar-workspace').dataset.calendarId;
    
    try {
        const response = await fetch(`/api/calendars/${calendarId}/events/${eventId}`);
        if (response.ok) {
            const event = await response.json();
            openEventModalForEdit(event);
        }
    } catch (error) {
        console.error('Failed to load event:', error);
    }
}

async function duplicateEvent(eventId) {
    closeContextMenu();
    const calendarId = document.querySelector('.calendar-workspace').dataset.calendarId;
    
    try {
        const response = await fetch(`/api/calendar/events/${eventId}/duplicate`, {
            method: 'POST'
        });
        
        if (response.ok) {
            showNotification('일정이 복제되었습니다', 'success');
            loadTimeGridEvents();
        }
    } catch (error) {
        console.error('Failed to duplicate event:', error);
        showNotification('일정 복제 실패', 'error');
    }
}

async function deleteEvent(eventId) {
    closeContextMenu();
    
    if (!confirm('정말 이 일정을 삭제하시겠습니까?')) {
        return;
    }
    
    const calendarId = document.querySelector('.calendar-workspace').dataset.calendarId;
    
    try {
        const response = await fetch(`/api/calendar/events/${eventId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showNotification('일정이 삭제되었습니다', 'success');
            
            // Remove event from DOM
            const eventBlock = document.querySelector(`[data-event-id="${eventId}"]`);
            if (eventBlock) {
                eventBlock.remove();
            }
        }
    } catch (error) {
        console.error('Failed to delete event:', error);
        showNotification('일정 삭제 실패', 'error');
    }
}

// API Keys Management
function openAPISettingsModal() {
    const modal = document.getElementById('api-keys-modal');
    if (modal) {
        modal.style.display = 'flex';
        loadSavedAPIKeys();
    }
}

function closeAPISettingsModal() {
    const modal = document.getElementById('api-keys-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function toggleAPIKeyVisibility(inputId) {
    const input = document.getElementById(inputId);
    const button = input.nextElementSibling;
    
    if (input.type === 'password') {
        input.type = 'text';
        button.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                <line x1="1" y1="1" x2="23" y2="23"/>
            </svg>
        `;
    } else {
        input.type = 'password';
        button.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                <circle cx="12" cy="12" r="3"/>
            </svg>
        `;
    }
}

async function saveAPIKey(platform) {
    const input = document.getElementById(`${platform}-api-key`);
    const apiKey = input.value;
    
    if (!apiKey.trim()) {
        showNotification('API 키를 입력해주세요', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/settings/api-keys', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                platform: platform,
                api_key: apiKey
            })
        });
        
        if (response.ok) {
            showNotification(`${platform} API 키가 저장되었습니다`, 'success');
        } else {
            throw new Error('Failed to save API key');
        }
    } catch (error) {
        console.error('Failed to save API key:', error);
        showNotification('API 키 저장에 실패했습니다', 'error');
    }
}

async function loadSavedAPIKeys() {
    try {
        const response = await fetch('/api/settings/api-keys');
        if (response.ok) {
            const data = await response.json();
            
            // Fill saved API keys (masked for security)
            Object.keys(data.api_keys || {}).forEach(platform => {
                const input = document.getElementById(`${platform}-api-key`);
                if (input && data.api_keys[platform]) {
                    // Show masked version
                    input.value = '••••••••••••••••';
                    input.dataset.saved = 'true';
                }
            });
        }
    } catch (error) {
        console.error('Failed to load API keys:', error);
    }
}

// Import calendar functions with API key integration
async function importFromGoogle() {
    const apiKey = await getAPIKey('google');
    if (!apiKey) {
        showNotification('Google API 키를 먼저 설정해주세요', 'error');
        openAPISettingsModal();
        return;
    }
    
    showNotification('Google Calendar에서 일정을 가져오는 중...', 'info');
    
    try {
        const response = await fetch('/api/import/google', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ api_key: apiKey })
        });
        
        if (response.ok) {
            const result = await response.json();
            showNotification(`${result.imported}개의 일정을 가져왔습니다`, 'success');
            loadTimeGridEvents();
        } else {
            throw new Error('Import failed');
        }
    } catch (error) {
        console.error('Google import failed:', error);
        showNotification('Google Calendar 가져오기 실패', 'error');
    }
}

async function importFromOutlook() {
    const apiKey = await getAPIKey('outlook');
    if (!apiKey) {
        showNotification('Outlook API 키를 먼저 설정해주세요', 'error');
        openAPISettingsModal();
        return;
    }
    
    showNotification('Outlook에서 일정을 가져오는 중...', 'info');
    
    try {
        const response = await fetch('/api/import/outlook', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ api_key: apiKey })
        });
        
        if (response.ok) {
            const result = await response.json();
            showNotification(`${result.imported}개의 일정을 가져왔습니다`, 'success');
            loadTimeGridEvents();
        } else {
            throw new Error('Import failed');
        }
    } catch (error) {
        console.error('Outlook import failed:', error);
        showNotification('Outlook 가져오기 실패', 'error');
    }
}

async function importFromNotion() {
    const apiKey = await getAPIKey('notion');
    if (!apiKey) {
        showNotification('Notion API 키를 먼저 설정해주세요', 'error');
        openAPISettingsModal();
        return;
    }
    
    showNotification('Notion에서 일정을 가져오는 중...', 'info');
    // TODO: Implement Notion import
}

async function importFromApple() {
    showNotification('iCloud Calendar 연동을 위해 계정 연결이 필요합니다', 'info');
    // TODO: Implement Apple Calendar import (OAuth flow)
}

async function importFromZoom() {
    const apiKey = await getAPIKey('zoom');
    if (!apiKey) {
        showNotification('Zoom API 키를 먼저 설정해주세요', 'error');
        openAPISettingsModal();
        return;
    }
    
    showNotification('Zoom 미팅을 가져오는 중...', 'info');
    // TODO: Implement Zoom import
}

async function importFromSlack() {
    const apiKey = await getAPIKey('slack');
    if (!apiKey) {
        showNotification('Slack API 토큰을 먼저 설정해주세요', 'error');
        openAPISettingsModal();
        return;
    }
    
    showNotification('Slack 일정을 가져오는 중...', 'info');
    // TODO: Implement Slack import
}

async function importFromTrello() {
    const apiKey = await getAPIKey('trello');
    if (!apiKey) {
        showNotification('Trello API 키를 먼저 설정해주세요', 'error');
        openAPISettingsModal();
        return;
    }
    
    showNotification('Trello 카드를 가져오는 중...', 'info');
    // TODO: Implement Trello import
}

async function importFromAsana() {
    const apiKey = await getAPIKey('asana');
    if (!apiKey) {
        showNotification('Asana API 키를 먼저 설정해주세요', 'error');
        openAPISettingsModal();
        return;
    }
    
    showNotification('Asana 작업을 가져오는 중...', 'info');
    // TODO: Implement Asana import
}

// Helper function to get API key
async function getAPIKey(platform) {
    try {
        const response = await fetch('/api/settings/api-keys');
        if (response.ok) {
            const data = await response.json();
            return data.api_keys?.[platform];
        }
    } catch (error) {
        console.error('Failed to get API key:', error);
    }
    return null;
}

async function importFromICS() {
    // Create file input
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.ics';
    
    input.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        const formData = new FormData();
        formData.append('file', file);
        
        const calendarId = document.querySelector('.calendar-workspace').dataset.calendarId;
        
        try {
            const response = await fetch(`/api/calendars/${calendarId}/import/ics`, {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const result = await response.json();
                showNotification(`${result.imported} 개의 일정을 가져왔습니다`, 'success');
                loadTimeGridEvents();
            } else {
                throw new Error('Import failed');
            }
        } catch (error) {
            console.error('Failed to import ICS:', error);
            showNotification('ICS 파일 가져오기 실패', 'error');
        }
    };
    
    input.click();
}

// Form submission handlers
window.saveSidebarEvent = async function(event) {
    event.preventDefault(); // Prevent page refresh
    // console.log('💾 Saving sidebar event...');
    
    try {
        const form = event.target;
        const calendarId = document.querySelector('.calendar-workspace').dataset.calendarId;
        
        // Get form values directly from DOM elements
        const title = document.getElementById('sidebar-event-title').value.trim();
        const date = document.getElementById('sidebar-event-date').value;
        const startTime = document.getElementById('sidebar-start-time').value;
        const endTime = document.getElementById('sidebar-end-time').value;
        const description = document.getElementById('sidebar-event-description').value.trim();
        const youtubeUrl = document.getElementById('sidebar-youtube-url').value.trim();
        
        // Validate required fields
        if (!title) {
            alert('일정 제목을 입력해주세요.');
            return;
        }
        
        if (!date) {
            alert('날짜를 선택해주세요.');
            return;
        }
        
        // Validate YouTube URL format only if provided
        if (youtubeUrl && youtubeUrl.trim()) {
            const youtubePattern = /^(https?:\/\/)?(www\.)?(youtube\.com\/(watch\?v=|embed\/)|youtu\.be\/)[\w-]+/;
            if (!youtubePattern.test(youtubeUrl)) {
                alert('올바른 YouTube 링크를 입력해주세요.\n예시: https://www.youtube.com/watch?v=...');
                return;
            }
        }
        
        // Create datetime strings from date and time inputs
        const startDate = date;
        const endDate = date;
        
        const startDateTime = `${startDate}T${startTime}:00`;
        const endDateTime = `${endDate}T${endTime}:00`;
        
        // Create event data object matching API requirements
        const eventData = {
            title: title,
            description: description,
            start_datetime: startDateTime,
            end_datetime: endDateTime,
            color: form.querySelector('.color-option.active')?.dataset.color || '#3b82f6',
            is_all_day: false,
            youtube_url: youtubeUrl
        };
        
        // console.log('📤 Sending event data:', eventData);
        
        const response = await fetch(`/api/calendars/${calendarId}/events`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(eventData)
        });
        
        if (response.ok) {
            const result = await response.json();
            // console.log('✅ Event created successfully:', result);
            showNotification('일정이 생성되었습니다', 'success');
            closeEventForm();
            loadTimeGridEvents(); // Reload events
        } else {
            throw new Error('Failed to create event');
        }
        
    } catch (error) {
        console.error('❌ Failed to save event:', error);
        showNotification('일정 생성 실패', 'error');
    }
};

window.saveOverlayEvent = async function(event) {
    event.preventDefault(); // Prevent page refresh
    // console.log('💾 Saving overlay event...');
    
    try {
        const form = event.target;
        const formData = new FormData(form);
        const calendarId = document.querySelector('.calendar-workspace').dataset.calendarId;
        
        // Create datetime strings from date and time inputs
        const startDate = formData.get('start_date');
        const startTime = formData.get('start_time');
        const endDate = formData.get('end_date') || formData.get('start_date');
        const endTime = formData.get('end_time');
        
        const startDateTime = `${startDate}T${startTime}:00`;
        const endDateTime = `${endDate}T${endTime}:00`;
        
        // Create event data object matching API requirements
        const eventData = {
            title: formData.get('title') || 'New Event',
            description: formData.get('description') || '',
            start_datetime: startDateTime,
            end_datetime: endDateTime,
            color: formData.get('color') || '#3b82f6',
            is_all_day: formData.get('is_all_day') === 'on'
        };
        
        // console.log('📤 Sending overlay event data:', eventData);
        
        const response = await fetch(`/api/calendars/${calendarId}/events`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(eventData)
        });
        
        if (response.ok) {
            const result = await response.json();
            // console.log('✅ Overlay event created successfully:', result);
            showNotification('일정이 생성되었습니다', 'success');
            closeOverlayForm();
            loadTimeGridEvents(); // Reload events
        } else {
            throw new Error('Failed to create overlay event');
        }
        
    } catch (error) {
        console.error('❌ Failed to save overlay event:', error);
        showNotification('일정 생성 실패', 'error');
    }
};

// Helper functions for closing forms
function closeEventForm() {
    const widget = document.getElementById('event-form-widget');
    if (widget) {
        widget.style.display = 'none';
    }
}

function closeOverlayForm() {
    const overlay = document.getElementById('calendar-overlay-form');
    if (overlay) {
        overlay.style.display = 'none';
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Check if we're on the calendar detail page
    const calendarWorkspace = document.querySelector('.calendar-workspace');
    if (calendarWorkspace) {
        initializeTimeGrid();
        
        // Add additional fallback to ensure auto-scroll works
        setTimeout(() => {
            const timeGridBody = document.querySelector('.time-grid-body');
            if (timeGridBody && timeGridBody.scrollTop === 0) {
                // console.log('🔄 Fallback auto-scroll triggered');
                autoScrollToCurrentTime();
            }
        }, 1000);
    }
});