// Calendar Detail - Modern Notion Style
let currentDate = new Date();
let currentView = 'month';
let selectedDate = null;
let calendarEvents = [];

// Calendar initialization
document.addEventListener('DOMContentLoaded', function() {
    initializeCalendar();
    loadEvents();
    setupEventListeners();
    initializeMiniCalendar();
    initializeMediaPlayer();
});

function initializeCalendar() {
    updateDateDisplay();
    renderMonthView();
    updateStats();
}

function setupEventListeners() {
    // View switcher
    document.querySelectorAll('.view-option').forEach(option => {
        option.addEventListener('click', function() {
            switchView(this.dataset.view);
        });
    });

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

function updateDateDisplay() {
    const dateElement = document.getElementById('current-date');
    if (dateElement) {
        const year = currentDate.getFullYear();
        const month = currentDate.getMonth() + 1;
        dateElement.textContent = `${year}년 ${month}월`;
    }
}

function switchView(viewType) {
    // Update active button
    document.querySelectorAll('.view-option').forEach(btn => btn.classList.remove('active'));
    document.querySelector(`[data-view="${viewType}"]`).classList.add('active');
    
    // Hide all views
    document.querySelectorAll('.calendar-view-container').forEach(view => {
        view.classList.remove('active');
    });
    
    // Show selected view
    const targetView = document.getElementById(`${viewType}-view`);
    if (targetView) {
        targetView.classList.add('active');
        currentView = viewType;
        
        // Render appropriate content
        switch(viewType) {
            case 'month':
                renderMonthView();
                break;
            case 'week':
                renderWeekView();
                break;
            case 'agenda':
                renderAgendaView();
                break;
        }
    }
}

// Media player functionality
let audioPlayer = null;
let currentPlaylist = [];
let currentTrackIndex = 0;
let isPlaying = false;

function initializeMediaPlayer() {
    audioPlayer = document.getElementById('audio-player');
    if (audioPlayer) {
        audioPlayer.addEventListener('loadedmetadata', updateTotalTime);
        audioPlayer.addEventListener('timeupdate', updateProgress);
        audioPlayer.addEventListener('ended', nextTrack);
        
        // Check if calendar has media files
        checkForMediaFiles();
    }
}

function checkForMediaFiles() {
    // This would check the calendar data for any attached media files
    // For demo purposes, we'll show the player if calendar has media
    const hasMediaFiles = true; // This should come from calendar data
    
    if (hasMediaFiles) {
        document.getElementById('media-player').style.display = 'flex';
        // Load sample track
        loadTrack({
            title: '캘린더 배경음악',
            artist: '집중음악',
            src: '/static/audio/sample.mp3' // This would be actual media file path
        });
    }
}

function loadTrack(track) {
    if (audioPlayer && track.src) {
        audioPlayer.src = track.src;
        document.getElementById('media-title').textContent = track.title || 'Unknown';
        document.getElementById('media-artist').textContent = track.artist || 'Unknown Artist';
    }
}

function togglePlay() {
    if (!audioPlayer) return;
    
    if (isPlaying) {
        audioPlayer.pause();
        isPlaying = false;
        document.getElementById('play-icon').style.display = 'block';
        document.getElementById('pause-icon').style.display = 'none';
    } else {
        audioPlayer.play();
        isPlaying = true;
        document.getElementById('play-icon').style.display = 'none';
        document.getElementById('pause-icon').style.display = 'block';
    }
}

function previousTrack() {
    if (currentPlaylist.length > 0) {
        currentTrackIndex = (currentTrackIndex - 1 + currentPlaylist.length) % currentPlaylist.length;
        loadTrack(currentPlaylist[currentTrackIndex]);
        if (isPlaying) audioPlayer.play();
    }
}

function nextTrack() {
    if (currentPlaylist.length > 0) {
        currentTrackIndex = (currentTrackIndex + 1) % currentPlaylist.length;
        loadTrack(currentPlaylist[currentTrackIndex]);
        if (isPlaying) audioPlayer.play();
    }
}

function seekTo(event) {
    if (!audioPlayer) return;
    
    const progressBar = event.currentTarget;
    const clickX = event.offsetX;
    const width = progressBar.offsetWidth;
    const duration = audioPlayer.duration;
    
    if (duration) {
        const newTime = (clickX / width) * duration;
        audioPlayer.currentTime = newTime;
    }
}

function updateProgress() {
    if (!audioPlayer) return;
    
    const current = audioPlayer.currentTime;
    const duration = audioPlayer.duration;
    
    if (duration) {
        const percentage = (current / duration) * 100;
        document.getElementById('progress-fill').style.width = percentage + '%';
        document.getElementById('current-time').textContent = formatTime(current);
    }
}

function updateTotalTime() {
    if (!audioPlayer) return;
    
    const duration = audioPlayer.duration;
    if (duration) {
        document.getElementById('total-time').textContent = formatTime(duration);
    }
}

function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}

function toggleMute() {
    if (!audioPlayer) return;
    
    audioPlayer.muted = !audioPlayer.muted;
    updateVolumeIcon();
}

function setVolume(event) {
    if (!audioPlayer) return;
    
    const volumeBar = event.currentTarget;
    const clickX = event.offsetX;
    const width = volumeBar.offsetWidth;
    const volume = clickX / width;
    
    audioPlayer.volume = volume;
    document.getElementById('volume-fill').style.width = (volume * 100) + '%';
    updateVolumeIcon();
}

function updateVolumeIcon() {
    const volumeIcon = document.getElementById('volume-icon');
    if (audioPlayer.muted || audioPlayer.volume === 0) {
        volumeIcon.innerHTML = '<path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z"/>';
    } else if (audioPlayer.volume < 0.5) {
        volumeIcon.innerHTML = '<path d="M18.5 12c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM5 9v6h4l5 5V4L9 9H5z"/>';
    } else {
        volumeIcon.innerHTML = '<path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z"/>';
    }
}

// Month view rendering (both main and compact)
function renderMonthView() {
    renderMainCalendar();
    renderCompactCalendar();
}

function renderMainCalendar() {
    const grid = document.getElementById('month-grid');
    if (!grid) return;
    
    // This would render the main calendar view
    // For now, we'll focus on the compact calendar
}

function renderCompactCalendar() {
    const grid = document.querySelector('.compact-month-grid');
    if (!grid) return;

    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    
    // Clear previous content
    grid.innerHTML = '';
    
    // Get first day of month and number of days
    const firstDay = new Date(year, month, 1);
    const startDate = new Date(firstDay);
    startDate.setDate(startDate.getDate() - firstDay.getDay());
    
    // Generate 42 cells (6 weeks)
    for (let i = 0; i < 42; i++) {
        const cellDate = new Date(startDate);
        cellDate.setDate(startDate.getDate() + i);
        
        const dayCell = createCompactDayCell(cellDate, month);
        grid.appendChild(dayCell);
    }
}

function createCompactDayCell(date, currentMonth) {
    const cell = document.createElement('div');
    cell.className = 'compact-calendar-day';
    
    const isCurrentMonth = date.getMonth() === currentMonth;
    const isToday = isDateToday(date);
    
    if (!isCurrentMonth) {
        cell.classList.add('other-month');
    }
    if (isToday) {
        cell.classList.add('today');
    }
    
    // Check if this date has events
    const dayEvents = getEventsForDate(date);
    if (dayEvents.length > 0) {
        cell.classList.add('has-event');
    }
    
    cell.textContent = date.getDate();
    
    // Click handler
    cell.addEventListener('click', () => {
        selectedDate = new Date(date);
        openDayModal(date);
    });
    
    return cell;
}

function createDayCell(date, currentMonth) {
    const cell = document.createElement('div');
    cell.className = 'calendar-day';
    
    const isCurrentMonth = date.getMonth() === currentMonth;
    const isToday = isDateToday(date);
    
    if (!isCurrentMonth) {
        cell.classList.add('other-month');
    }
    if (isToday) {
        cell.classList.add('today');
    }
    
    // Day number
    const dayNumber = document.createElement('div');
    dayNumber.className = 'day-number';
    dayNumber.textContent = date.getDate();
    cell.appendChild(dayNumber);
    
    // Events container
    const eventsContainer = document.createElement('div');
    eventsContainer.className = 'day-events';
    
    // Add sample events for demo
    const dayEvents = getEventsForDate(date);
    dayEvents.forEach(event => {
        const eventElement = document.createElement('div');
        eventElement.className = 'day-event';
        eventElement.textContent = event.title;
        eventElement.style.background = event.color || '#dbeafe';
        eventsContainer.appendChild(eventElement);
    });
    
    cell.appendChild(eventsContainer);
    
    // Click handler
    cell.addEventListener('click', () => {
        selectedDate = new Date(date);
        openDayModal(date);
    });
    
    return cell;
}

function renderWeekView() {
    const container = document.getElementById('week-days-grid');
    if (!container) return;
    
    container.innerHTML = '<div class="week-view-placeholder">주간 뷰는 개발 중입니다.</div>';
}

function renderAgendaView() {
    // Agenda view is already populated in HTML template
    console.log('Agenda view rendered');
}

// Mini Calendar
function initializeMiniCalendar() {
    renderMiniCalendar();
}

function renderMiniCalendar() {
    const miniDays = document.getElementById('mini-days');
    if (!miniDays) return;
    
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    
    // Update mini calendar title
    const title = document.querySelector('.mini-month-title');
    if (title) {
        title.textContent = `${month + 1}월 ${year}`;
    }
    
    // Clear previous content
    miniDays.innerHTML = '';
    
    // Get first day of month
    const firstDay = new Date(year, month, 1);
    const startDate = new Date(firstDay);
    startDate.setDate(startDate.getDate() - firstDay.getDay());
    
    // Generate mini calendar days
    for (let i = 0; i < 42; i++) {
        const cellDate = new Date(startDate);
        cellDate.setDate(startDate.getDate() + i);
        
        const dayElement = document.createElement('div');
        dayElement.className = 'mini-day';
        dayElement.textContent = cellDate.getDate();
        
        if (cellDate.getMonth() !== month) {
            dayElement.style.color = '#cbd5e1';
        }
        
        if (isDateToday(cellDate)) {
            dayElement.classList.add('today');
        }
        
        dayElement.addEventListener('click', () => {
            currentDate = new Date(cellDate);
            updateDateDisplay();
            renderMonthView();
            renderMiniCalendar();
        });
        
        miniDays.appendChild(dayElement);
    }
}

// Navigation functions
function changeMonth(direction) {
    currentDate.setMonth(currentDate.getMonth() + direction);
    updateDateDisplay();
    renderMonthView();
    renderMiniCalendar();
}

function changeMiniMonth(direction) {
    changeMonth(direction);
}

function goToToday() {
    currentDate = new Date();
    updateDateDisplay();
    renderMonthView();
    renderMiniCalendar();
}

// Event management
function loadEvents() {
    // Sample events for demo
    calendarEvents = [
        {
            id: 1,
            title: '팀 미팅',
            date: new Date(2025, 2, 21), // March 21, 2025
            time: '14:00',
            color: '#dbeafe'
        },
        {
            id: 2,
            title: '프로젝트 발표',
            date: new Date(2025, 2, 25), // March 25, 2025
            time: '10:00',
            color: '#dcfce7'
        }
    ];
}

function getEventsForDate(date) {
    return calendarEvents.filter(event => 
        event.date.getDate() === date.getDate() &&
        event.date.getMonth() === date.getMonth() &&
        event.date.getFullYear() === date.getFullYear()
    );
}

function isDateToday(date) {
    const today = new Date();
    return date.getDate() === today.getDate() &&
           date.getMonth() === today.getMonth() &&
           date.getFullYear() === today.getFullYear();
}

// Modal functions
function openEventModal() {
    const modal = document.getElementById('event-modal');
    if (modal) {
        modal.style.display = 'flex';
        
        // Set default date if a date is selected
        if (selectedDate) {
            const startInput = document.getElementById('event-start');
            const endInput = document.getElementById('event-end');
            if (startInput && endInput) {
                const dateStr = selectedDate.toISOString().slice(0, 16);
                startInput.value = dateStr;
                endInput.value = dateStr;
            }
        }
    }
}

function closeEventModal() {
    const modal = document.getElementById('event-modal');
    if (modal) {
        modal.style.display = 'none';
        clearEventForm();
    }
}

function openDayModal(date) {
    const modal = document.getElementById('day-modal');
    const title = document.getElementById('modal-date');
    
    if (modal && title) {
        const year = date.getFullYear();
        const month = date.getMonth() + 1;
        const day = date.getDate();
        
        title.textContent = `${year}년 ${month}월 ${day}일`;
        modal.style.display = 'flex';
        
        // Load events for this day
        loadDayEvents(date);
    }
}

function closeDayModal() {
    const modal = document.getElementById('day-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function loadDayEvents(date) {
    const container = document.getElementById('day-events');
    if (!container) return;
    
    const events = getEventsForDate(date);
    
    if (events.length === 0) {
        container.innerHTML = '<div class="no-events">이 날짜에 일정이 없습니다.</div>';
    } else {
        container.innerHTML = events.map(event => `
            <div class="day-event-item">
                <div class="event-time">${event.time}</div>
                <div class="event-title">${event.title}</div>
            </div>
        `).join('');
    }
}

function saveEvent() {
    const title = document.getElementById('event-title').value;
    const start = document.getElementById('event-start').value;
    const end = document.getElementById('event-end').value;
    const description = document.getElementById('event-description').value;
    const allDay = document.getElementById('event-allday').checked;
    const color = document.querySelector('.color-option.active')?.style.background || '#dbeafe';
    
    if (!title || !start) {
        alert('제목과 시작일은 필수입니다.');
        return;
    }
    
    const newEvent = {
        id: Date.now(),
        title: title,
        date: new Date(start),
        time: allDay ? '종일' : new Date(start).toLocaleTimeString('ko-KR', {hour: '2-digit', minute: '2-digit'}),
        description: description,
        color: color,
        allDay: allDay
    };
    
    calendarEvents.push(newEvent);
    renderMonthView();
    closeEventModal();
    updateStats();
    
    // Show success message
    showNotification('이벤트가 추가되었습니다.');
}

function clearEventForm() {
    document.getElementById('event-title').value = '';
    document.getElementById('event-start').value = '';
    document.getElementById('event-end').value = '';
    document.getElementById('event-description').value = '';
    document.getElementById('event-allday').checked = false;
    
    // Reset color picker
    document.querySelectorAll('.color-option').forEach(opt => opt.classList.remove('active'));
    document.querySelector('.color-option').classList.add('active');
}

function addEventToDay() {
    closeEventModal();
    openEventModal();
}

// Stats and utility functions
function updateStats() {
    const monthEvents = document.getElementById('month-events');
    const weekEvents = document.getElementById('week-events');
    
    if (monthEvents) {
        const thisMonth = calendarEvents.filter(event => 
            event.date.getMonth() === currentDate.getMonth() &&
            event.date.getFullYear() === currentDate.getFullYear()
        ).length;
        monthEvents.textContent = thisMonth;
    }
    
    if (weekEvents) {
        weekEvents.textContent = '3'; // Sample data
    }
}

function showNotification(message) {
    // Create and show a simple notification
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #10b981;
        color: white;
        padding: 12px 20px;
        border-radius: 6px;
        z-index: 2000;
        font-size: 14px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Close modals when clicking overlay
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal-overlay')) {
        e.target.style.display = 'none';
    }
});

// Sync and settings functions (placeholder)
function syncCalendar() {
    showNotification('캘린더 동기화 완료');
}

function openSettings() {
    showNotification('설정 기능은 개발 중입니다.');
}