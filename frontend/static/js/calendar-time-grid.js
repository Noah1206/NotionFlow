// Google Calendar Style Time Grid JavaScript

// Time grid configuration
const TIME_GRID_CONFIG = {
    startHour: 1,   // Start at 1 AM (full range)
    endHour: 23,    // End at 11 PM
    defaultViewStart: 7, // Default visible start at 7 AM
    hourHeight: 60, // Pixels per hour
    snapMinutes: 15 // Snap to 15-minute intervals
};

// Current view state
let timeGridView = 'week'; // 'week' or 'day'
let currentWeekStart = null;
let selectedEvent = null;
let isDragging = false;
let isResizing = false;
let dragStartY = 0;
let dragStartTime = null;
let originalEventData = null;

// Initialize time grid
function initializeTimeGrid() {
    console.log('🕒 Initializing time grid view...');
    
    // Set current week start
    currentWeekStart = getWeekStart(currentDate);
    
    // Render the time grid
    renderTimeGrid();
    
    // Load events
    loadTimeGridEvents();
    
    // Set default scroll position to 7 AM
    setTimeout(() => {
        scrollToTime(TIME_GRID_CONFIG.defaultViewStart);
    }, 100);
    
    // Update current time indicator
    updateCurrentTimeIndicator();
    setInterval(updateCurrentTimeIndicator, 60000); // Update every minute
    
    // Initialize drag and drop
    initializeDragAndDrop();
    
    // Initialize context menu
    initializeContextMenu();
}

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
    if (!timeGridBody) return;
    
    // Calculate scroll position
    const hoursFromStart = hour - TIME_GRID_CONFIG.startHour;
    const scrollTop = hoursFromStart * TIME_GRID_CONFIG.hourHeight;
    
    // Smooth scroll to position
    timeGridBody.scrollTo({
        top: Math.max(0, scrollTop),
        behavior: 'smooth'
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

// Render time labels
function renderTimeLabels() {
    const labelsContainer = document.querySelector('.time-labels-column');
    if (!labelsContainer) return;
    
    labelsContainer.innerHTML = '';
    
    for (let hour = TIME_GRID_CONFIG.startHour; hour <= TIME_GRID_CONFIG.endHour; hour++) {
        const label = document.createElement('div');
        label.className = 'time-label';
        
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
        
        label.textContent = `${displayHour} ${ampm}`;
        labelsContainer.appendChild(label);
    }
}

// Render grid lines
function renderGridLines() {
    const gridContainer = document.getElementById('time-grid-lines');
    if (!gridContainer) return;
    
    gridContainer.innerHTML = '';
    
    // Add horizontal lines for each hour
    const hoursCount = TIME_GRID_CONFIG.endHour - TIME_GRID_CONFIG.startHour + 1;
    for (let i = 0; i < hoursCount; i++) {
        const line = document.createElement('div');
        line.className = 'hour-line';
        line.style.top = `${i * TIME_GRID_CONFIG.hourHeight}px`;
        gridContainer.appendChild(line);
    }
    
    // Add vertical lines for each day
    for (let i = 0; i < 7; i++) {
        const column = document.createElement('div');
        column.className = 'day-column';
        column.style.left = `${(i * 100) / 7}%`;
        column.style.width = `${100 / 7}%`;
        gridContainer.appendChild(column);
    }
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
    }
}

// Render events on the grid
function renderEvents(events) {
    const eventsLayer = document.getElementById('events-layer');
    if (!eventsLayer) return;
    
    // Clear existing events
    eventsLayer.innerHTML = '';
    
    events.forEach(event => {
        if (!event.start_time || event.all_day) return; // Skip all-day events for now
        
        const eventElement = createEventElement(event);
        if (eventElement) {
            eventsLayer.appendChild(eventElement);
        }
    });
}

// Create an event element
function createEventElement(event) {
    const startDate = new Date(event.start_time);
    const endDate = new Date(event.end_time || event.start_time);
    
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
    
    // Create event block
    const eventBlock = document.createElement('div');
    eventBlock.className = `event-block ${event.color || 'blue'}`;
    eventBlock.dataset.eventId = event.id;
    eventBlock.style.top = `${top}px`;
    eventBlock.style.height = `${height}px`;
    eventBlock.style.left = `${left}%`;
    eventBlock.style.width = `calc(${width}% - 4px)`;
    
    // Format time
    const startTimeStr = startDate.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
    const endTimeStr = endDate.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
    
    eventBlock.innerHTML = `
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
    const eventsGrid = document.getElementById('events-grid');
    if (!eventsGrid) return;
    
    // Grid click to create new event
    eventsGrid.addEventListener('mousedown', handleGridMouseDown);
    
    // Global mouse events for dragging
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
}

// Handle grid mouse down (create new event)
function handleGridMouseDown(e) {
    if (e.target.closest('.event-block')) return; // Ignore if clicking on event
    
    const rect = e.currentTarget.getBoundingClientRect();
    const relativeY = e.clientY - rect.top;
    const relativeX = e.clientX - rect.left;
    
    // Calculate time from Y position
    const hourOffset = relativeY / TIME_GRID_CONFIG.hourHeight;
    const minutes = Math.floor((hourOffset % 1) * 60 / TIME_GRID_CONFIG.snapMinutes) * TIME_GRID_CONFIG.snapMinutes;
    const hour = Math.floor(hourOffset) + TIME_GRID_CONFIG.startHour;
    
    // Calculate day from X position
    const dayIndex = Math.floor((relativeX / rect.width) * 7);
    
    // Create new event at this position
    const eventDate = new Date(currentWeekStart);
    eventDate.setDate(eventDate.getDate() + dayIndex);
    eventDate.setHours(hour, minutes, 0, 0);
    
    // Open event creation modal with pre-filled time
    openEventModalWithTime(eventDate);
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

// Handle mouse move (dragging or resizing)
function handleMouseMove(e) {
    if (!isDragging && !isResizing) return;
    
    if (isDragging && selectedEvent) {
        const deltaY = e.clientY - dragStartY;
        const newTop = originalEventData.top + deltaY;
        
        // Snap to grid
        const snappedTop = Math.round(newTop / (TIME_GRID_CONFIG.hourHeight / 4)) * (TIME_GRID_CONFIG.hourHeight / 4);
        selectedEvent.style.top = `${snappedTop}px`;
        
        // Update time display
        updateEventTimeDisplay(selectedEvent);
    } else if (isResizing && selectedEvent) {
        const rect = selectedEvent.parentElement.getBoundingClientRect();
        const relativeY = e.clientY - rect.top;
        const newHeight = relativeY - parseInt(selectedEvent.style.top);
        
        // Minimum height (15 minutes)
        const minHeight = TIME_GRID_CONFIG.hourHeight / 4;
        if (newHeight >= minHeight) {
            selectedEvent.style.height = `${newHeight}px`;
            updateEventTimeDisplay(selectedEvent);
        }
    }
}

// Handle mouse up (end drag or resize)
async function handleMouseUp(e) {
    if (!isDragging && !isResizing) return;
    
    if (selectedEvent) {
        selectedEvent.classList.remove('dragging', 'selected');
        
        // Save the new position/size
        await saveEventChanges(selectedEvent);
    }
    
    isDragging = false;
    isResizing = false;
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
        const response = await fetch(`/api/calendars/${calendarId}/events/${eventId}`, {
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

// Update current time indicator
function updateCurrentTimeIndicator() {
    const indicator = document.getElementById('current-time-indicator');
    if (!indicator) return;
    
    const now = new Date();
    const currentHour = now.getHours() + now.getMinutes() / 60;
    
    // Check if current time is within grid range
    if (currentHour < TIME_GRID_CONFIG.startHour || currentHour > TIME_GRID_CONFIG.endHour) {
        indicator.style.display = 'none';
        return;
    }
    
    // Calculate position from the start hour (1 AM)
    const top = (currentHour - TIME_GRID_CONFIG.startHour) * TIME_GRID_CONFIG.hourHeight;
    indicator.style.top = `${top}px`;
    indicator.style.display = 'block';
}

// Open event modal with pre-filled time
function openEventModalWithTime(date) {
    const modal = document.getElementById('event-modal');
    if (!modal) return;
    
    // Set start time
    const startInput = document.getElementById('event-start');
    const endInput = document.getElementById('event-end');
    
    const endDate = new Date(date);
    endDate.setHours(endDate.getHours() + 1); // Default 1 hour duration
    
    startInput.value = formatDateTimeLocal(date);
    endInput.value = formatDateTimeLocal(endDate);
    
    // Show modal
    modal.style.display = 'flex';
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
        const response = await fetch(`/api/calendars/${calendarId}/events/${eventId}/duplicate`, {
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
        const response = await fetch(`/api/calendars/${calendarId}/events/${eventId}`, {
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

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Check if we're on the calendar detail page
    const calendarWorkspace = document.querySelector('.calendar-workspace');
    if (calendarWorkspace) {
        initializeTimeGrid();
    }
});