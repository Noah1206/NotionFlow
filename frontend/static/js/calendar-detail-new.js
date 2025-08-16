// Calendar Detail New - Notion Style Calendar
let currentDate = new Date();
let currentView = 'month';
let selectedDate = null;
let calendarEvents = [];

// Calendar initialization
document.addEventListener('DOMContentLoaded', function() {
    initializeCalendar();
    loadEvents();
    setupEventListeners();
});

function initializeCalendar() {
    updateMonthDisplay();
    renderCalendar();
    updateStats();
}

function setupEventListeners() {
    // Color picker for events
    document.querySelectorAll('.color-option').forEach(option => {
        option.addEventListener('click', function() {
            document.querySelectorAll('.color-option').forEach(opt => opt.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // All day checkbox
    const allDayCheckbox = document.getElementById('event-allday');
    const startInput = document.getElementById('event-start');
    const endInput = document.getElementById('event-end');
    
    if (allDayCheckbox) {
        allDayCheckbox.addEventListener('change', function() {
            if (this.checked) {
                startInput.type = 'date';
                endInput.type = 'date';
            } else {
                startInput.type = 'datetime-local';
                endInput.type = 'datetime-local';
            }
        });
    }
}

// Calendar rendering
function renderCalendar() {
    const grid = document.getElementById('calendar-grid');
    if (!grid) return;

    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    
    // Get first day of month and number of days
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startDate = new Date(firstDay);
    startDate.setDate(startDate.getDate() - firstDay.getDay());

    grid.innerHTML = '';

    // Render 6 weeks (42 days)
    for (let i = 0; i < 42; i++) {
        const cellDate = new Date(startDate);
        cellDate.setDate(startDate.getDate() + i);
        
        const dayCell = createDayCell(cellDate, month);
        grid.appendChild(dayCell);
    }
}

function createDayCell(date, currentMonth) {
    const cell = document.createElement('div');
    cell.className = 'calendar-day';
    
    const isToday = isDateToday(date);
    const isCurrentMonth = date.getMonth() === currentMonth;
    const isSelected = selectedDate && isSameDate(date, selectedDate);
    
    if (!isCurrentMonth) cell.classList.add('other-month');
    if (isToday) cell.classList.add('today');
    if (isSelected) cell.classList.add('selected');
    
    // Day number
    const dayNumber = document.createElement('div');
    dayNumber.className = 'day-number';
    dayNumber.textContent = date.getDate();
    cell.appendChild(dayNumber);
    
    // Events container
    const eventsContainer = document.createElement('div');
    eventsContainer.className = 'day-events';
    
    // Add events for this day
    const dayEvents = getEventsForDate(date);
    const maxVisibleEvents = 3;
    
    dayEvents.slice(0, maxVisibleEvents).forEach(event => {
        const eventElement = document.createElement('div');
        eventElement.className = `event-item ${getEventColorClass(event.color)}`;
        eventElement.textContent = event.title;
        eventElement.addEventListener('click', (e) => {
            e.stopPropagation();
            openEventDetail(event);
        });
        eventsContainer.appendChild(eventElement);
    });
    
    // Show "more" indicator if there are more events
    if (dayEvents.length > maxVisibleEvents) {
        const moreElement = document.createElement('div');
        moreElement.className = 'more-events';
        moreElement.textContent = `+${dayEvents.length - maxVisibleEvents} more`;
        eventsContainer.appendChild(moreElement);
    }
    
    cell.appendChild(eventsContainer);
    
    // Click handler for day
    cell.addEventListener('click', () => openDayModal(date));
    
    return cell;
}

// Date utilities
function isDateToday(date) {
    const today = new Date();
    return isSameDate(date, today);
}

function isSameDate(date1, date2) {
    return date1.getFullYear() === date2.getFullYear() &&
           date1.getMonth() === date2.getMonth() &&
           date1.getDate() === date2.getDate();
}

function formatDate(date) {
    return date.toLocaleDateString('ko-KR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

function formatDateTime(date) {
    return date.toLocaleString('ko-KR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Navigation
function goToToday() {
    currentDate = new Date();
    updateMonthDisplay();
    renderCalendar();
}

function changeMonth(delta) {
    currentDate.setMonth(currentDate.getMonth() + delta);
    updateMonthDisplay();
    renderCalendar();
}

function updateMonthDisplay() {
    const monthElement = document.getElementById('current-month');
    if (monthElement) {
        monthElement.textContent = currentDate.toLocaleDateString('ko-KR', {
            year: 'numeric',
            month: 'long'
        });
    }
}

// View switching
function switchView(view) {
    currentView = view;
    
    // Update active button
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.view === view) {
            btn.classList.add('active');
        }
    });
    
    // Show/hide views
    document.querySelectorAll('.calendar-view').forEach(viewEl => {
        viewEl.classList.remove('active');
    });
    
    const targetView = document.getElementById(`${view}-view`);
    if (targetView) {
        targetView.classList.add('active');
    }
    
    // Render appropriate view
    switch (view) {
        case 'month':
            renderCalendar();
            break;
        case 'week':
            renderWeekView();
            break;
        case 'day':
            renderDayView();
            break;
        case 'list':
            renderListView();
            break;
    }
}

// Event management
function loadEvents() {
    // Mock events data
    calendarEvents = [
        {
            id: 1,
            title: '팀 미팅',
            start: new Date(2025, 7, 17, 14, 0), // August 17, 2025, 2:00 PM
            end: new Date(2025, 7, 17, 15, 30),
            description: '주간 팀 미팅',
            color: '#3B82F6',
            allDay: false
        },
        {
            id: 2,
            title: '프로젝트 발표',
            start: new Date(2025, 7, 20, 10, 0),
            end: new Date(2025, 7, 20, 12, 0),
            description: 'Q3 프로젝트 최종 발표',
            color: '#10B981',
            allDay: false
        },
        {
            id: 3,
            title: '휴가',
            start: new Date(2025, 7, 25),
            end: new Date(2025, 7, 27),
            description: '여름 휴가',
            color: '#F59E0B',
            allDay: true
        }
    ];
    
    renderCalendar();
    updateSidebarEvents();
}

function getEventsForDate(date) {
    return calendarEvents.filter(event => {
        if (event.allDay) {
            return date >= new Date(event.start.getFullYear(), event.start.getMonth(), event.start.getDate()) &&
                   date <= new Date(event.end.getFullYear(), event.end.getMonth(), event.end.getDate());
        } else {
            return isSameDate(date, event.start);
        }
    });
}

function getEventColorClass(color) {
    const colorMap = {
        '#3B82F6': 'blue',
        '#10B981': 'green',
        '#F59E0B': 'yellow',
        '#EF4444': 'red',
        '#8B5CF6': 'purple',
        '#EC4899': 'pink'
    };
    return colorMap[color] || 'blue';
}

// Modals
function openDayModal(date) {
    selectedDate = date;
    const modal = document.getElementById('day-modal');
    const dateTitle = document.getElementById('modal-date');
    const eventsContainer = document.getElementById('day-events');
    
    if (!modal || !dateTitle || !eventsContainer) return;
    
    dateTitle.textContent = formatDate(date);
    
    // Load events for this day
    const dayEvents = getEventsForDate(date);
    eventsContainer.innerHTML = '';
    
    if (dayEvents.length === 0) {
        eventsContainer.innerHTML = '<div class="no-events">이 날짜에 일정이 없습니다</div>';
    } else {
        dayEvents.forEach(event => {
            const eventElement = document.createElement('div');
            eventElement.className = 'event-item';
            eventElement.innerHTML = `
                <div class="event-time">${formatDateTime(event.start)}</div>
                <div class="event-title">${event.title}</div>
            `;
            eventElement.addEventListener('click', () => openEventDetail(event));
            eventsContainer.appendChild(eventElement);
        });
    }
    
    modal.style.display = 'flex';
    renderCalendar(); // Re-render to show selected date
}

function closeDayModal() {
    const modal = document.getElementById('day-modal');
    if (modal) {
        modal.style.display = 'none';
    }
    selectedDate = null;
    renderCalendar();
}

function openEventModal(date = null) {
    const modal = document.getElementById('event-modal');
    if (!modal) return;
    
    // Reset form
    document.getElementById('event-title').value = '';
    document.getElementById('event-description').value = '';
    document.getElementById('event-allday').checked = false;
    
    // Set default date
    if (date || selectedDate) {
        const targetDate = date || selectedDate;
        const dateStr = targetDate.toISOString().slice(0, 16);
        document.getElementById('event-start').value = dateStr;
        
        // Set end time 1 hour later
        const endDate = new Date(targetDate);
        endDate.setHours(endDate.getHours() + 1);
        document.getElementById('event-end').value = endDate.toISOString().slice(0, 16);
    }
    
    modal.style.display = 'flex';
}

function closeEventModal() {
    const modal = document.getElementById('event-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function addEventToDay() {
    if (selectedDate) {
        closeDayModal();
        openEventModal(selectedDate);
    }
}

function saveEvent() {
    const title = document.getElementById('event-title').value.trim();
    const start = document.getElementById('event-start').value;
    const end = document.getElementById('event-end').value;
    const description = document.getElementById('event-description').value.trim();
    const allDay = document.getElementById('event-allday').checked;
    const color = document.querySelector('.color-option.active').dataset.color;
    
    if (!title || !start || !end) {
        alert('제목, 시작시간, 종료시간을 모두 입력해주세요.');
        return;
    }
    
    const newEvent = {
        id: Date.now(),
        title,
        start: new Date(start),
        end: new Date(end),
        description,
        color,
        allDay
    };
    
    calendarEvents.push(newEvent);
    
    closeEventModal();
    renderCalendar();
    updateSidebarEvents();
    updateStats();
    
    showNotification('이벤트가 성공적으로 추가되었습니다.', 'success');
}

function openEventDetail(event) {
    // Implementation for event detail modal
    console.log('Opening event detail:', event);
}

// Sidebar updates
function updateSidebarEvents() {
    updateTodayEvents();
    updateUpcomingEvents();
}

function updateTodayEvents() {
    const container = document.getElementById('today-events');
    if (!container) return;
    
    const today = new Date();
    const todayEvents = getEventsForDate(today);
    
    container.innerHTML = '';
    
    if (todayEvents.length === 0) {
        container.innerHTML = '<div class="no-events">오늘 일정이 없습니다</div>';
    } else {
        todayEvents.forEach(event => {
            const eventElement = document.createElement('div');
            eventElement.className = 'event-item';
            eventElement.innerHTML = `
                <div class="event-time">${event.allDay ? '종일' : formatDateTime(event.start)}</div>
                <div class="event-title">${event.title}</div>
            `;
            eventElement.addEventListener('click', () => openEventDetail(event));
            container.appendChild(eventElement);
        });
    }
}

function updateUpcomingEvents() {
    const container = document.getElementById('upcoming-events');
    if (!container) return;
    
    const today = new Date();
    const nextWeek = new Date(today);
    nextWeek.setDate(today.getDate() + 7);
    
    const upcomingEvents = calendarEvents.filter(event => {
        return event.start > today && event.start <= nextWeek;
    }).sort((a, b) => a.start - b.start);
    
    container.innerHTML = '';
    
    if (upcomingEvents.length === 0) {
        container.innerHTML = '<div class="no-events">다가오는 일정이 없습니다</div>';
    } else {
        upcomingEvents.forEach(event => {
            const eventElement = document.createElement('div');
            eventElement.className = 'event-item';
            eventElement.innerHTML = `
                <div class="event-time">${formatDateTime(event.start)}</div>
                <div class="event-title">${event.title}</div>
            `;
            eventElement.addEventListener('click', () => openEventDetail(event));
            container.appendChild(eventElement);
        });
    }
}

function updateStats() {
    // Update month events count
    const monthEventsEl = document.getElementById('month-events');
    if (monthEventsEl) {
        const monthStart = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
        const monthEnd = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
        
        const monthEvents = calendarEvents.filter(event => {
            return event.start >= monthStart && event.start <= monthEnd;
        });
        
        monthEventsEl.textContent = monthEvents.length;
    }
    
    // Update week events count
    const weekEventsEl = document.getElementById('week-events');
    if (weekEventsEl) {
        const today = new Date();
        const weekStart = new Date(today);
        weekStart.setDate(today.getDate() - today.getDay());
        const weekEnd = new Date(weekStart);
        weekEnd.setDate(weekStart.getDate() + 6);
        
        const weekEvents = calendarEvents.filter(event => {
            return event.start >= weekStart && event.start <= weekEnd;
        });
        
        weekEventsEl.textContent = weekEvents.length;
    }
}

// Other view renders (simplified for now)
function renderWeekView() {
    console.log('Rendering week view');
}

function renderDayView() {
    console.log('Rendering day view');
}

function renderListView() {
    console.log('Rendering list view');
}

// Action handlers
function syncCalendar() {
    showNotification('캘린더 동기화를 시작합니다...', 'info');
    
    // Simulate sync
    setTimeout(() => {
        showNotification('캘린더 동기화가 완료되었습니다.', 'success');
    }, 2000);
}

function openSettings() {
    showNotification('설정 페이지는 곧 제공될 예정입니다.', 'info');
}

// Notification system
function showNotification(message, type = 'info') {
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

// Close modals when clicking outside
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal-overlay')) {
        e.target.style.display = 'none';
        if (e.target.id === 'day-modal') {
            selectedDate = null;
            renderCalendar();
        }
    }
});