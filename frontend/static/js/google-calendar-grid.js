// Google Calendar Style Grid Implementation

class GoogleCalendarGrid {
    constructor(container) {
        this.container = container;
        this.currentDate = new Date();
        this.weekStart = this.getWeekStart(this.currentDate);
        this.events = [];
        this.trashedEvents = this.loadTrashedEvents();
        
        // 🔍 DEBUGGING: 컨테이너 크기 확인
        // console.log('🏗️ GoogleCalendarGrid constructor:', {
        //     currentDate: this.currentDate,
        //     weekStart: this.weekStart,
        //     dayOfWeek: this.currentDate.getDay(),
        //     containerWidth: this.container.offsetWidth,
        //     containerHeight: this.container.offsetHeight,
        //     containerRect: this.container.getBoundingClientRect(),
        //     windowWidth: window.innerWidth,
        //     windowHeight: window.innerHeight
        // });
        
        // Initialize search and event list
        this.initializeEventSearch();
        this.initializeEventList();
        
        // Selection state
        this.isSelecting = false;
        this.selectionStart = null;
        this.selectionEnd = null;
        this.selectedCells = new Set();
        
        // Time configuration
        this.startHour = 0; // 12 AM
        this.endHour = 23;  // 11 PM
        this.timeSlotHeight = 100; // pixels - Larger size for better visibility
        
        this.init();
        
        // Monitor sidebar changes
        this.initSidebarMonitoring();
    }
    
    // Trash management methods
    loadTrashedEvents() {
        const storageKey = 'calendar_trashed_events';
        try {
            const saved = localStorage.getItem(storageKey);
            return saved ? JSON.parse(saved) : [];
        } catch (error) {
            console.error('Failed to load trashed events:', error);
            return [];
        }
    }
    
    saveTrashedEvents() {
        const storageKey = 'calendar_trashed_events';
        try {
            localStorage.setItem(storageKey, JSON.stringify(this.trashedEvents));
        } catch (error) {
            console.error('Failed to save trashed events:', error);
        }
    }
    
    moveEventToTrash(eventData) {
        // Add timestamp when moved to trash
        const trashedEvent = {
            ...eventData,
            trashedAt: new Date().toISOString()
        };
        
        this.trashedEvents.push(trashedEvent);
        this.saveTrashedEvents();
        
        console.log('Event moved to trash:', trashedEvent);
    }
    
    restoreEventFromTrash(eventId) {
        const eventIndex = this.trashedEvents.findIndex(event => event.id === eventId);
        
        if (eventIndex !== -1) {
            const restoredEvent = this.trashedEvents[eventIndex];
            // Remove trashedAt property
            const { trashedAt, ...cleanEvent } = restoredEvent;
            
            // Remove from trash
            this.trashedEvents.splice(eventIndex, 1);
            this.saveTrashedEvents();
            
            // Add back to active events
            this.events.push(cleanEvent);
            
            // Update localStorage with current events
            const storageKey = 'calendar_events_backup';
            localStorage.setItem(storageKey, JSON.stringify(this.events));
            
            return cleanEvent;
        }
        
        return null;
    }
    
    // Trash popup functionality
    showTrashPopup() {
        const popup = document.getElementById('trash-popup');
        if (popup) {
            popup.style.display = 'flex';
            this.populateTrashPopup();
        }
    }
    
    hideTrashPopup() {
        const popup = document.getElementById('trash-popup');
        if (popup) {
            popup.style.display = 'none';
        }
    }
    
    populateTrashPopup() {
        const content = document.getElementById('trash-popup-content');
        const emptyMessage = document.getElementById('trash-empty');
        const emptyButton = document.getElementById('trash-empty-all-btn');
        
        if (!content) return;
        
        // Clear existing content except empty message
        const existingItems = content.querySelectorAll('.trash-event-item');
        existingItems.forEach(item => item.remove());
        
        if (this.trashedEvents.length === 0) {
            emptyMessage.style.display = 'block';
            if (emptyButton) emptyButton.style.display = 'none';
            return;
        }
        
        emptyMessage.style.display = 'none';
        if (emptyButton) emptyButton.style.display = 'flex';
        
        this.trashedEvents.forEach(eventData => {
            const eventItem = this.createTrashEventItem(eventData);
            content.appendChild(eventItem);
        });
    }
    
    createTrashEventItem(eventData) {
        const item = document.createElement('div');
        item.className = 'trash-event-item';
        item.draggable = true;
        item.dataset.eventId = eventData.id;
        
        const eventDate = new Date(eventData.date);
        const startTime = eventData.startTime || '00:00';
        const endTime = eventData.endTime || '01:00';
        
        item.innerHTML = `
            <div class="event-title">${eventData.title}</div>
            <div class="event-time">${startTime} - ${endTime}</div>
            <div class="event-date">${eventDate.toLocaleDateString('ko-KR')}</div>
        `;
        
        // Add drag event listeners
        item.addEventListener('dragstart', (e) => {
            e.dataTransfer.setData('text/plain', eventData.id);
            e.dataTransfer.effectAllowed = 'move';
            console.log('Drag started for event:', eventData.id);
        });
        
        return item;
    }
    
    // Show confirmation dialog for event restoration
    showRestoreConfirmation(trashedEvent, newDay, newHour, targetCell) {
        const newDate = new Date(this.weekStart);
        newDate.setDate(newDate.getDate() + newDay);
        const dateStr = newDate.toLocaleDateString('ko-KR');
        const timeStr = `${newHour.toString().padStart(2, '0')}:00`;
        
        const confirmed = confirm(`"${trashedEvent.title}" 일정을 ${dateStr} ${timeStr}에 복원하시겠습니까?`);
        
        if (confirmed) {
            this.restoreEventToCalendar(trashedEvent, newDay, newHour);
        }
    }
    
    // Restore event from trash to calendar
    restoreEventToCalendar(trashedEvent, newDay, newHour) {
        // Update event data with new time and date
        const restoredEvent = { ...trashedEvent };
        delete restoredEvent.trashedAt;
        
        // Update date
        const newDate = new Date(this.weekStart);
        newDate.setDate(newDate.getDate() + newDay);
        restoredEvent.date = newDate.toISOString().split('T')[0];
        
        // Update time (keep original duration if possible)
        const originalStartTime = trashedEvent.startTime || '09:00';
        const originalEndTime = trashedEvent.endTime || '10:00';
        const [startHour, startMin] = originalStartTime.split(':').map(Number);
        const [endHour, endMin] = originalEndTime.split(':').map(Number);
        const duration = (endHour * 60 + endMin) - (startHour * 60 + startMin); // duration in minutes
        
        restoredEvent.startTime = `${newHour.toString().padStart(2, '0')}:00`;
        const newEndMinutes = newHour * 60 + duration;
        const newEndHour = Math.floor(newEndMinutes / 60);
        const newEndMin = newEndMinutes % 60;
        restoredEvent.endTime = `${newEndHour.toString().padStart(2, '0')}:${newEndMin.toString().padStart(2, '0')}`;
        
        // Restore from trash
        this.restoreEventFromTrash(trashedEvent.id);
        
        // Re-render events to show the restored event
        this.renderEvents();
        
        // Update event list
        this.updateEventList();
        
        // Update trash popup
        this.populateTrashPopup();
        
        // Show success notification
        if (window.showNotification) {
            showNotification(`일정 "${restoredEvent.title}"이 복원되었습니다`, 'success');
        }
        
        console.log('Event restored from trash:', restoredEvent);
    }
    
    // Empty trash functionality
    async emptyTrash() {
        if (this.trashedEvents.length === 0) {
            if (window.showNotification) {
                showNotification('휴지통이 이미 비어있습니다', 'info');
            }
            return;
        }
        
        const confirmed = confirm(`휴지통에 있는 ${this.trashedEvents.length}개의 일정을 영구적으로 삭제하시겠습니까?\n\n이 작업은 되돌릴 수 없습니다.`);
        
        if (!confirmed) return;
        
        try {
            const calendarId = document.querySelector('.calendar-workspace')?.dataset.calendarId || 'e3b088c5-58550';
            
            // Delete events from backend if they have backendId
            const eventsWithBackendId = this.trashedEvents.filter(event => event.backendId);
            
            if (eventsWithBackendId.length > 0) {
                for (const eventData of eventsWithBackendId) {
                    try {
                        const response = await fetch(`/api/calendar/${calendarId}/events/${eventData.backendId}`, {
                            method: 'DELETE',
                            headers: {
                                'Content-Type': 'application/json'
                            }
                        });
                        
                        if (!response.ok) {
                            console.warn(`Failed to delete event ${eventData.backendId} from backend`);
                        }
                    } catch (error) {
                        console.error(`Failed to delete event ${eventData.backendId}:`, error);
                    }
                }
            }
            
            // Clear all trashed events
            this.trashedEvents = [];
            this.saveTrashedEvents();
            
            // Update trash popup
            this.populateTrashPopup();
            
            // Show success notification
            if (window.showNotification) {
                showNotification('휴지통이 비워졌습니다', 'success');
            }
            
            console.log('Trash emptied successfully');
            
        } catch (error) {
            console.error('Failed to empty trash:', error);
            if (window.showNotification) {
                showNotification('휴지통 비우기에 실패했습니다', 'error');
            }
        }
    }
    
    initSidebarMonitoring() {
        // Update on window resize
        window.addEventListener('resize', () => {
            this.updateMainContentDimensions();
        });
        
        // Monitor for sidebar toggle changes
        const sidebarToggle = document.querySelector('.sidebar-toggle');
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => {
                // Delay to let the animation complete
                setTimeout(() => {
                    this.updateMainContentDimensions();
                }, 300);
            });
        }
        
        // Initial update
        setTimeout(() => {
            this.updateMainContentDimensions();
        }, 100);
    }
    
    init() {
        this.render();
        this.attachEventListeners();
        this.loadExistingEvents(); // Load existing events from backend
        this.updateCurrentTimeIndicator();
        
        // Add resize listener to maintain header visibility
        window.addEventListener('resize', () => {
            setTimeout(() => {
                this.ensureHeaderVisibility();
            }, 200);
        });
        
        // Update time indicator every 30 minutes
        setInterval(() => {
            this.updateCurrentTimeIndicator();
        }, 30 * 60 * 1000); // 30분 = 30 * 60 * 1000 밀리초
        
        // console.log('🎯 Google Calendar Grid initialized');
    }
    
    getWeekStart(date) {
        const d = new Date(date.getTime()); // Create a copy to avoid mutating original
        const day = d.getDay(); // 0 = Sunday, 1 = Monday, ..., 6 = Saturday
        
        // Calculate days to subtract to get to Sunday
        const daysToSunday = day;
        const weekStart = new Date(d.getTime() - (daysToSunday * 24 * 60 * 60 * 1000));
        weekStart.setHours(0, 0, 0, 0); // Set to beginning of day
        
        // console.log('🗓️ Week start calculated:', weekStart, 'from date:', date, 'day:', day, 'daysToSunday:', daysToSunday);
        return weekStart;
    }

    // Week navigation method
    navigateWeek(direction) {
        // Move current date by week
        this.currentDate.setDate(this.currentDate.getDate() + (direction * 7));
        
        // Recalculate week start
        this.weekStart = this.getWeekStart(this.currentDate);
        
        // Re-render the calendar
        this.render();
        
        // Re-render existing events for the new week
        this.rerenderAllEvents();
        
        // Update current time indicator
        this.updateCurrentTimeIndicator();
    }
    
    // Helper function to re-render all events
    rerenderAllEvents() {
        // Clear existing event elements from DOM
        const existingEvents = this.container.querySelectorAll('.calendar-event');
        existingEvents.forEach(event => event.remove());
        
        // Re-render all events
        this.events.forEach(event => {
            this.renderEvent(event);
        });
    }
    
    render() {
        // 🔧 DYNAMIC WIDTH: 컨테이너 너비에 맞게 동적으로 크기 조정
        let containerWidth = this.container.offsetWidth || this.container.getBoundingClientRect().width;
        
        // If container width is 0, try to get parent width or use fallback
        if (containerWidth === 0) {
            const parent = this.container.parentElement;
            if (parent) {
                containerWidth = parent.offsetWidth || parent.getBoundingClientRect().width;
            }
            // If still 0, use window width with sidebar consideration
            if (containerWidth === 0) {
                const sidebar = document.querySelector('.sidebar');
                const sidebarWidth = sidebar ? sidebar.offsetWidth : 320;
                containerWidth = window.innerWidth - sidebarWidth;
            }
        }
        
        const timeColumnWidth = 80; // 시간 컬럼 너비 최적화
        const availableWidth = containerWidth - timeColumnWidth; // 여백 완전 제거
        const dayColumnWidth = Math.max(250, Math.floor(availableWidth / 7)); // 최소 250px 보장, 7개 요일로 나누기 
        // console.log('🎯 Dynamic sizing:', {
        //     containerWidth,
        //     availableWidth,
        //     dayColumnWidth,
        //     totalWidth: timeColumnWidth + (dayColumnWidth * 7)
        // });
        
        // 동적 크기를 인스턴스 변수로 저장
        this.timeColumnWidth = timeColumnWidth;
        this.dayColumnWidth = dayColumnWidth;
        
        const html = `
            <div class="google-calendar-grid" style="width: 100%; height: 100%; display: flex; flex-direction: column;">
                ${this.renderHeader()}
                ${this.renderGrid()}
            </div>
        `;
        
        this.container.innerHTML = html;
        
        // Force layout recalculation after DOM update
        setTimeout(() => {
            this.ensureHeaderVisibility();
        }, 100);
    }
    
    ensureHeaderVisibility() {
        const header = this.container.querySelector('.calendar-header');
        if (header) {
            // Force header to be visible and properly positioned
            header.style.display = 'grid';
            header.style.visibility = 'visible';
            header.style.zIndex = '1000';
            header.style.position = 'sticky';
            header.style.top = '0';
            header.style.background = 'white';
            header.style.minHeight = '60px';
            header.style.height = '60px';
            // console.log('🔧 Header visibility ensured:', header.getBoundingClientRect());
        } else {
            console.warn('⚠️ Header not found for visibility check');
        }
    }
    
    renderHeader() {
        const days = ['일', '월', '화', '수', '목', '금', '토'];
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        
        let headerHTML = `
            <div class="calendar-header" style="display: grid; grid-template-columns: ${this.timeColumnWidth}px repeat(7, ${this.dayColumnWidth}px); width: 100%; height: 60px; min-height: 60px; box-sizing: border-box; padding: 0; margin: 0; background: white; border-bottom: 1px solid #e0e0e0; position: sticky; top: 0; z-index: 1000;">
                <div class="time-header" style="grid-column: 1; width: ${this.timeColumnWidth}px; height: 100%; display: flex; align-items: center; justify-content: center; border-right: 1px solid #e0e0e0;">GMT+9</div>
        `;
        
        for (let i = 0; i < 7; i++) {
            const date = new Date(this.weekStart);
            date.setDate(date.getDate() + i);
            
            const isToday = date.getTime() === today.getTime();
            const isWeekend = i === 0 || i === 6;
            
            headerHTML += `
                <div class="day-header ${isToday ? 'today' : ''}" data-day="${i}" style="grid-column: ${i + 2}; width: ${this.dayColumnWidth}px; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; border-right: ${i < 6 ? '1px solid #e0e0e0' : 'none'};">
                    <div class="day-name" style="font-size: 11px; color: #70757a; text-transform: uppercase; font-weight: 500; margin-bottom: 4px;">${days[i]}</div>
                    <div class="day-date" style="font-size: 26px; color: ${isToday ? 'white' : '#3c4043'}; font-weight: ${isToday ? '500' : '400'}; ${isToday ? 'background: #1a73e8; border-radius: 50%; width: 36px; height: 36px; display: flex; align-items: center; justify-content: center;' : ''}">${date.getDate()}</div>
                </div>
            `;
        }
        
        headerHTML += `</div>`;
        return headerHTML;
    }
    
    renderGrid() {
        let gridHTML = `
            <div class="calendar-grid-body" style="display: grid; grid-template-columns: ${this.timeColumnWidth}px repeat(7, ${this.dayColumnWidth}px); width: 100%; height: 100%; box-sizing: border-box; padding: 0; margin: 0; padding-top: 10px;">
                <div class="time-column" style="grid-column: 1; width: ${this.timeColumnWidth}px; flex-shrink: 0;">
                    ${this.renderTimeSlots()}
                </div>
        `;
        
        // Render day columns with proper grid positioning - each takes full available space
        for (let day = 0; day < 7; day++) {
            const isWeekend = day === 0 || day === 6;
            gridHTML += `
                <div class="day-column ${isWeekend ? 'weekend' : ''}" data-day="${day}" style="grid-column: ${day + 2}; width: ${this.dayColumnWidth}px; height: 100%;">
                    ${this.renderTimeCells(day)}
                </div>
            `;
        }
        
        gridHTML += `</div>`;
        return gridHTML;
    }
    
    renderTimeSlots() {
        let slotsHTML = '';
        
        for (let hour = this.startHour; hour <= this.endHour; hour++) {
            const timeLabel = this.formatHour(hour);
            slotsHTML += `
                <div class="time-slot" data-hour="${hour}">
                    <div class="time-label">${timeLabel}</div>
                </div>
            `;
        }
        
        return slotsHTML;
    }
    
    renderTimeCells(day) {
        let cellsHTML = '';
        
        for (let hour = this.startHour; hour <= this.endHour; hour++) {
            cellsHTML += `
                <div class="time-cell" 
                     data-day="${day}" 
                     data-hour="${hour}"
                     data-cell-id="${day}-${hour}">
                </div>
            `;
        }
        
        return cellsHTML;
    }
    
    formatHour(hour) {
        if (hour === 0) return '12AM';
        if (hour === 12) return '12PM';
        if (hour < 12) return `${hour}AM`;
        return `${hour - 12}PM`;
    }
    
    attachEventListeners() {
        const gridBody = this.container.querySelector('.calendar-grid-body');
        
        // Mouse events for selection
        gridBody.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        gridBody.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        gridBody.addEventListener('mouseup', (e) => this.handleMouseUp(e));
        
        // Prevent text selection during drag
        gridBody.addEventListener('selectstart', (e) => e.preventDefault());
        
        // Click events for quick event creation
        gridBody.addEventListener('click', (e) => this.handleCellClick(e));
        
        // Drag and drop events for event time editing
        gridBody.addEventListener('dragover', (e) => {
            e.preventDefault(); // Allow drop
        });
        
        gridBody.addEventListener('drop', (e) => this.handleEventDrop(e));
        
        // Global mouse up to handle selections outside grid
        document.addEventListener('mouseup', () => {
            if (this.isSelecting) {
                this.finishSelection();
            }
        });
    }
    
    handleMouseDown(e) {
        const cell = e.target.closest('.time-cell');
        if (!cell) return;
        
        e.preventDefault();
        this.startSelection(cell);
    }
    
    handleMouseMove(e) {
        if (!this.isSelecting) return;
        
        const cell = e.target.closest('.time-cell');
        if (!cell) return;
        
        this.updateSelection(cell);
    }
    
    handleMouseUp(e) {
        if (this.isSelecting) {
            this.finishSelection();
        }
    }
    
    handleCellClick(e) {
        const cell = e.target.closest('.time-cell');
        if (!cell || this.isSelecting) return;
        
        // Check if overlay is visible
        const overlay = document.getElementById('calendar-overlay-form');
        if (overlay && overlay.style.display !== 'none' && !overlay.classList.contains('hidden')) {
            console.log('🚫 Cell click prevented - overlay already visible');
            e.preventDefault();
            e.stopPropagation();
            return;
        }
        
        // console.log('🖱️ Cell clicked:', cell, {
        //     day: cell.dataset.day,
        //     hour: cell.dataset.hour,
        //     rect: cell.getBoundingClientRect()
        // });
        
        // Single cell click - create 1 hour event
        const day = parseInt(cell.dataset.day);
        const hour = parseInt(cell.dataset.hour);
        
        // Pass the actual clicked cell to createEvent
        this.createEvent(day, hour, day, hour, cell);
    }
    
    startSelection(cell) {
        this.isSelecting = true;
        this.selectionStart = {
            day: parseInt(cell.dataset.day),
            hour: parseInt(cell.dataset.hour)
        };
        this.selectionEnd = { ...this.selectionStart };
        
        this.clearSelection();
        this.updateSelectionDisplay();
    }
    
    updateSelection(cell) {
        this.selectionEnd = {
            day: parseInt(cell.dataset.day),
            hour: parseInt(cell.dataset.hour)
        };
        
        this.updateSelectionDisplay();
    }
    
    updateSelectionDisplay() {
        this.clearSelection();
        
        const startDay = Math.min(this.selectionStart.day, this.selectionEnd.day);
        const endDay = Math.max(this.selectionStart.day, this.selectionEnd.day);
        const startHour = Math.min(this.selectionStart.hour, this.selectionEnd.hour);
        const endHour = Math.max(this.selectionStart.hour, this.selectionEnd.hour);
        
        // Mark selected cells
        for (let day = startDay; day <= endDay; day++) {
            for (let hour = startHour; hour <= endHour; hour++) {
                const cellId = `${day}-${hour}`;
                const cell = this.container.querySelector(`[data-cell-id="${cellId}"]`);
                if (cell) {
                    cell.classList.add('selecting');
                    this.selectedCells.add(cellId);
                }
            }
        }
        
        this.showTimeRangeIndicator(startDay, startHour, endDay, endHour);
    }
    
    showTimeRangeIndicator(startDay, startHour, endDay, endHour) {
        // Remove existing indicator
        const existingIndicator = this.container.querySelector('.time-range-display');
        if (existingIndicator) {
            existingIndicator.remove();
        }
        
        // Create time range display
        const startDate = new Date(this.weekStart);
        startDate.setDate(startDate.getDate() + startDay);
        
        const timeRange = this.formatTimeRange(startHour, endHour + 1);
        const dateStr = startDate.toLocaleDateString('ko-KR', { 
            month: 'short', 
            day: 'numeric' 
        });
        
        const indicator = document.createElement('div');
        indicator.className = 'time-range-display';
        indicator.textContent = `${dateStr} ${timeRange}`;
        
        // Position near cursor or selection
        const firstSelectedCell = this.container.querySelector('.time-cell.selecting');
        if (firstSelectedCell) {
            const rect = firstSelectedCell.getBoundingClientRect();
            const containerRect = this.container.getBoundingClientRect();
            
            indicator.style.left = `${rect.left - containerRect.left + 10}px`;
            indicator.style.top = `${rect.top - containerRect.top - 30}px`;
        }
        
        this.container.appendChild(indicator);
    }
    
    formatTimeRange(startHour, endHour) {
        return `${this.formatHour(startHour)} - ${this.formatHour(endHour)}`;
    }
    
    clearSelection() {
        // Remove all selecting classes
        this.container.querySelectorAll('.time-cell.selecting').forEach(cell => {
            cell.classList.remove('selecting');
        });
        
        this.selectedCells.clear();
        
        // Remove time range indicator
        const indicator = this.container.querySelector('.time-range-display');
        if (indicator) {
            indicator.remove();
        }
    }
    
    finishSelection() {
        
        if (!this.isSelecting || this.selectedCells.size === 0) {
            this.isSelecting = false;
            this.clearSelection();
            return;
        }
        
        const startDay = Math.min(this.selectionStart.day, this.selectionEnd.day);
        const endDay = Math.max(this.selectionStart.day, this.selectionEnd.day);
        const startHour = Math.min(this.selectionStart.hour, this.selectionEnd.hour);
        const endHour = Math.max(this.selectionStart.hour, this.selectionEnd.hour);
        
        this.isSelecting = false;
        this.clearSelection();
        
        // Create event for selected time range
        this.createEvent(startDay, startHour, endDay, endHour);
    }
    
    createEvent(startDay, startHour, endDay, endHour, clickedCell = null) {
        
        // console.log('🎯 createEvent called:', {startDay, startHour, endDay, endHour});
        
        // Ensure weekStart is properly initialized
        if (!this.weekStart || !(this.weekStart instanceof Date)) {
            this.weekStart = this.getWeekStart(new Date());
            // console.log('⚠️ weekStart was undefined, recalculated:', this.weekStart);
        }
        
        // console.log('🗓️ Current weekStart:', this.weekStart);
        
        // Calculate dates using milliseconds to avoid timezone issues
        const millisecondsPerDay = 24 * 60 * 60 * 1000;
        const startDate = new Date(this.weekStart.getTime() + (startDay * millisecondsPerDay));
        startDate.setHours(startHour, 0, 0, 0);
        
        const endDate = new Date(this.weekStart.getTime() + (endDay * millisecondsPerDay));
        endDate.setHours(endHour + 1, 0, 0, 0); // +1 for end time to include the full hour
        
        // console.log('📅 Created dates - Start:', startDate, 'End:', endDate);
        // console.log('📍 Expected day column:', startDay, 'Actual date:', startDate.toDateString());
        // console.log('📍 Day of week - Start:', startDate.getDay(), 'Expected:', startDay);
        
        // Check if this is a multi-day event
        const isMultiDay = startDay !== endDay;
        
        if (isMultiDay) {
            // Multi-day event: create time-based events for each day
            // console.log('🗓️ Multi-day event detected, creating time-based events');
            
            const startDateStr = this.formatDateForInput(startDate);
            const endDateStr = this.formatDateForInput(endDate);
            const startTimeStr = startDate.toTimeString().slice(0, 5); // HH:MM format
            const endTimeStr = endDate.toTimeString().slice(0, 5); // HH:MM format
            
            // console.log('📅 Multi-day range - Start Date:', startDateStr, 'End Date:', endDateStr);
            // console.log('🕐 Time range - Start:', startTimeStr, 'End:', endTimeStr);
            
            // Use special handling for multi-day events with time
            if (typeof showOverlayEventFormMultiDay !== 'undefined') {
                let cellElement = clickedCell;
                if (!cellElement) {
                    cellElement = document.querySelector(`.time-cell[data-day="${startDay}"][data-hour="${startHour}"]`);
                }
                
                // Pass multi-day information with time to the form
                showOverlayEventFormMultiDay(startDateStr, endDateStr, cellElement, startHour, endHour + 1);
            }
        } else {
            // Single-day event: use existing time-based logic
            // console.log('📅 Single-day event, using time-based handling');
            
            const dateStr = this.formatDateForInput(startDate);
            const startTimeStr = startDate.toTimeString().slice(0, 5); // HH:MM format
            const endTimeStr = endDate.toTimeString().slice(0, 5); // HH:MM format
            
            // console.log('🕐 Single-day drag times - Start:', startTimeStr, 'End:', endTimeStr);
            
            // Use the existing overlay form with clicked cell information
            if (typeof showOverlayEventForm !== 'undefined') {
                // 간단한 팝업 차단 체크
                if (window.POPUP_BLOCKED) {
                    console.log('🚫 [Grid] Event creation blocked');
                    return;
                }
                
                // Find the clicked cell to pass position information
                let cellElement = clickedCell;
                if (!cellElement) {
                    // Try to find the cell by day and hour if not provided
                    cellElement = document.querySelector(`.time-cell[data-day="${startDay}"][data-hour="${startHour}"]`);
                }
                console.log('🎯 [Grid] Calling showOverlayEventForm with both times:', { startTimeStr, endTimeStr });
                showOverlayEventForm(dateStr, startTimeStr, cellElement, endTimeStr);
            }
        }
    }
    
    formatDateForInput(date) {
        // Format date as YYYY-MM-DD for input field
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }
    
    showEventContextMenu(e, eventData) {
        // Remove existing context menu
        const existingMenu = document.querySelector('.event-context-menu');
        if (existingMenu) {
            existingMenu.remove();
        }
        
        const menu = document.createElement('div');
        menu.className = 'event-context-menu';
        menu.style.cssText = `
            position: fixed;
            left: ${e.clientX}px;
            top: ${e.clientY}px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            padding: 4px 0;
            z-index: 1000;
            min-width: 120px;
        `;
        
        menu.innerHTML = `
            <div class="context-menu-item" data-action="edit" style="padding: 8px 16px; cursor: pointer; hover: background: #f0f0f0;">
                <span>✏️ 편집</span>
            </div>
            <div class="context-menu-item" data-action="duplicate" style="padding: 8px 16px; cursor: pointer; hover: background: #f0f0f0;">
                <span>📋 복제</span>
            </div>
            <div class="context-menu-item" data-action="delete" style="padding: 8px 16px; cursor: pointer; hover: background: #f0f0f0; color: #dc2626;">
                <span>🗑️ 삭제</span>
            </div>
        `;
        
        // Add hover effect
        menu.querySelectorAll('.context-menu-item').forEach(item => {
            item.addEventListener('mouseenter', () => {
                item.style.background = '#f0f0f0';
            });
            item.addEventListener('mouseleave', () => {
                item.style.background = 'white';
            });
        });
        
        // Handle menu item clicks
        menu.querySelectorAll('.context-menu-item').forEach(item => {
            item.addEventListener('click', () => {
                const action = item.dataset.action;
                switch(action) {
                    case 'edit':
                        this.editEvent(eventData);
                        break;
                    case 'duplicate':
                        this.duplicateEvent(eventData);
                        break;
                    case 'delete':
                        this.deleteEvent(eventData);
                        break;
                }
                menu.remove();
            });
        });
        
        document.body.appendChild(menu);
        
        // Remove menu when clicking elsewhere
        const removeMenu = (e) => {
            if (!menu.contains(e.target)) {
                menu.remove();
                document.removeEventListener('click', removeMenu);
            }
        };
        
        setTimeout(() => {
            document.addEventListener('click', removeMenu);
        }, 100);
    }
    
    editEvent(eventData) {
        // Open sidebar form for editing
        openEventForm(null, eventData);
    }
    
    async deleteEvent(eventData) {
        if (confirm(`"${eventData.title}" 일정을 휴지통으로 이동하시겠습니까?`)) {
            // Move event to trash instead of permanent deletion
            this.moveEventToTrash(eventData);
            
            // Remove from events array
            this.events = this.events.filter(e => e.id !== eventData.id);
            
            // Update localStorage with current events
            const storageKey = 'calendar_events_backup';
            localStorage.setItem(storageKey, JSON.stringify(this.events));
            
            // Remove from DOM immediately - comprehensive search
            console.log('🗑️ Removing event from display:', eventData.title, 'ID:', eventData.id);
            
            // 간단하고 효과적인 DOM 제거
            console.log('🔍 Looking for elements to remove...');
            let removedCount = 0;
            
            // 1. 모든 div 요소에서 제목이 포함된 것 찾기
            const allDivs = document.querySelectorAll('div');
            allDivs.forEach(div => {
                if (div.textContent && div.textContent.includes(eventData.title)) {
                    // 이벤트 관련 요소인지 확인
                    if (div.style.position === 'absolute' || 
                        div.querySelector('[onclick*="delete"]') ||
                        div.className.includes('event') ||
                        div.parentElement?.className.includes('event')) {
                        
                        console.log(`💀 Removing div containing: "${eventData.title}"`);
                        div.remove();
                        removedCount++;
                    }
                }
            });
            
            // 2. 모든 span 요소도 확인
            const allSpans = document.querySelectorAll('span');
            allSpans.forEach(span => {
                if (span.textContent && span.textContent.includes(eventData.title)) {
                    const container = span.closest('div');
                    if (container && (container.style.position === 'absolute' || 
                                   container.querySelector('[onclick*="delete"]'))) {
                        console.log(`💀 Removing span container for: "${eventData.title}"`);
                        container.remove();
                        removedCount++;
                    }
                }
            });
            
            console.log(`✅ Removed ${removedCount} elements from display`);
            
            // Update event list and refresh display
            this.updateEventList();
            
            // 🔄 강제 그리드 새로고침 - 모든 이벤트 다시 그리기
            console.log('🔄 Force refresh: clearing all rendered events and re-rendering...');
            
            // 1. 모든 렌더된 이벤트 완전히 제거
            this.clearRenderedEvents();
            
            // 2. 현재 남은 이벤트들만 다시 렌더링
            this.events.filter(event => event && event.id && event.date).forEach(event => {
                this.renderEvent(event);
                console.log('✅ Re-rendered event:', event.title);
            });
            
            // 3. 이벤트 목록도 업데이트
            this.updateEventList();
            
            // 4. 추가 새로고침 (안전장치)
            setTimeout(() => {
                console.log('🔄 Additional refresh...');
                if (this.renderEvents) {
                    this.renderEvents();
                } else if (this.render) {
                    this.render();
                }
                console.log('✅ Final refresh completed');
            }, 200);
            
            // Close any open popup
            const popups = document.querySelectorAll('.event-creation-popup');
            popups.forEach(popup => popup.remove());
            
            if (window.showNotification) {
                showNotification('일정이 휴지통으로 이동되었습니다', 'success');
            }
        }
    }
    
    duplicateEvent(eventData) {
        // Create a copy of the event with a new ID and modified title
        const newEvent = {
            ...eventData,
            id: Date.now().toString(),
            backendId: null, // New event doesn't have backend ID yet
            title: eventData.title + ' (복사본)'
        };
        
        // Add to events array
        this.events.push(newEvent);
        
        // Update localStorage with current events
        const storageKey = 'calendar_events_backup';
        localStorage.setItem(storageKey, JSON.stringify(this.events));
        
        // Render the new event
        this.renderEvent(newEvent);
        
        // Update event list
        this.updateEventList();
        
        // Try to save to backend
        this.saveEventToBackend(newEvent);
        
        if (window.showNotification) {
            showNotification(`"${newEvent.title}" 일정이 생성되었습니다`, 'success');
        }
    }
    
    async saveEventToBackend(eventData) {
        try {
            const calendarId = document.querySelector('.calendar-workspace')?.dataset.calendarId || 'default';
            const response = await fetch(`/api/calendars/${calendarId}/events`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(eventData)
            });
            
            if (response.ok) {
                // console.log('Event saved to backend successfully');
            }
        } catch (error) {
            console.error('Failed to save event to backend:', error);
        }
    }
    
    clearRenderedEvents() {
        // Remove all rendered events from the DOM
        this.container.querySelectorAll('.calendar-event').forEach(event => {
            event.remove();
        });
    }
    
    saveToLocalStorage() {
        try {
            const storageKey = 'calendar_events_backup';
            localStorage.setItem(storageKey, JSON.stringify(this.events));
            // console.log('💾 Events saved to localStorage');
            
            // Update event list when saving
            this.updateEventList();
        } catch (error) {
            console.error('Failed to save to localStorage:', error);
        }
    }
    
    initializeEventSearch() {
        const searchInput = document.getElementById('event-search-input');
        const searchClearBtn = document.getElementById('search-clear-btn');
        const searchResults = document.getElementById('search-results');
        
        if (!searchInput) return;
        
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.trim();
            
            if (query) {
                if (searchClearBtn) searchClearBtn.style.display = 'block';
                this.searchEvents(query);
            } else {
                if (searchClearBtn) searchClearBtn.style.display = 'none';
                if (searchResults) searchResults.style.display = 'none';
                // Clear search and show all events
                this.clearEventHighlighting();
                this.updateEventList();
                // Remove search feedback
                const existingFeedback = document.querySelector('.search-feedback');
                if (existingFeedback) {
                    existingFeedback.remove();
                }
            }
        });
        
        // Clear search function
        window.clearEventSearch = () => {
            searchInput.value = '';
            if (searchClearBtn) searchClearBtn.style.display = 'none';
            if (searchResults) searchResults.style.display = 'none';
            // Clear highlighting and show all events
            this.clearEventHighlighting();
            this.updateEventList();
            // Remove search feedback
            const existingFeedback = document.querySelector('.search-feedback');
            if (existingFeedback) {
                existingFeedback.remove();
            }
        };
    }
    
    searchEvents(query) {
        const searchResults = document.getElementById('search-results');
        if (!searchResults) return;
        
        const lowerQuery = query.toLowerCase();
        const filteredEvents = this.events.filter(event => 
            event.title.toLowerCase().includes(lowerQuery) ||
            (event.description && event.description.toLowerCase().includes(lowerQuery))
        );
        
        if (filteredEvents.length > 0) {
            searchResults.innerHTML = filteredEvents.map(event => {
                const eventDate = new Date(event.date);
                const dateStr = this.formatEventDate(eventDate);
                
                return `
                    <div class="search-result-item" onclick="window.googleCalendarGrid.highlightEvent('${event.id}')">
                        <div class="search-result-title">${event.title}</div>
                        <div class="search-result-date">${dateStr} ${event.startTime}-${event.endTime}</div>
                    </div>
                `;
            }).join('');
            searchResults.style.display = 'block';
        } else {
            searchResults.innerHTML = '<div class="no-results">검색 결과가 없습니다</div>';
            searchResults.style.display = 'block';
        }
    }
    
    initializeEventList() {
        // Initial load of event list
        this.updateEventList();
    }
    
    updateEventList() {
        const eventListContainer = document.getElementById('event-list');
        if (!eventListContainer) return;
        
        // Sort events by date and time
        const sortedEvents = [...this.events].sort((a, b) => {
            const dateA = new Date(a.date + 'T' + a.startTime);
            const dateB = new Date(b.date + 'T' + b.startTime);
            return dateA - dateB;
        });
        
        if (sortedEvents.length > 0) {
            // Add select all checkbox and action buttons
            eventListContainer.innerHTML = `
                <div style="padding: 8px; border-bottom: 1px solid #e0e0e0; margin-bottom: 8px;">
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                        <label style="display: flex; align-items: center; cursor: pointer;">
                            <input type="checkbox" id="select-all-events" onchange="window.googleCalendarGrid.toggleSelectAll(this)" style="margin-right: 8px;">
                            <span style="font-size: 14px; color: #666;">전체 선택</span>
                        </label>
                        <div id="bulk-actions" style="display: none; gap: 8px;">
                            <button onclick="window.googleCalendarGrid.bulkDeleteEvents()" style="padding: 4px 12px; background: #dc2626; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">
                                선택 삭제
                            </button>
                        </div>
                    </div>
                </div>
                ${sortedEvents.map(event => {
                    const eventDate = new Date(event.date);
                    const dateStr = this.formatEventDate(eventDate);
                    
                    return `
                        <div class="event-list-item" data-event-list-id="${event.id}" style="display: flex; align-items: center; padding: 8px; margin-bottom: 8px; border-radius: 4px; background: #f5f5f5; transition: background 0.2s;">
                            <input type="checkbox" class="event-checkbox" data-event-id="${event.id}" onchange="window.googleCalendarGrid.handleEventCheckbox(this)" onclick="event.stopPropagation()" style="margin-right: 12px; cursor: pointer;">
                            <div onclick="window.googleCalendarGrid.highlightEvent('${event.id}')" style="flex: 1; cursor: pointer;">
                                <div class="event-list-title" style="font-weight: 500; color: #333;">${event.title}</div>
                                <div class="event-list-date" style="font-size: 12px; color: #666; margin-top: 4px;">${dateStr}</div>
                            </div>
                        </div>
                    `;
                }).join('')}
            `;
            
            // Add hover effect
            eventListContainer.querySelectorAll('.event-list-item').forEach(item => {
                item.addEventListener('mouseenter', () => {
                    item.style.background = '#e0e0e0';
                });
                item.addEventListener('mouseleave', () => {
                    const checkbox = item.querySelector('.event-checkbox');
                    item.style.background = checkbox?.checked ? '#d0d0d0' : '#f5f5f5';
                });
            });
        } else {
            eventListContainer.innerHTML = '<div style="padding: 16px; text-align: center; color: #999;">일정이 없습니다</div>';
        }
    }
    
    formatEventDate(date) {
        const days = ['일', '월', '화', '수', '목', '금', '토'];
        const month = date.getMonth() + 1;
        const day = date.getDate();
        const dayOfWeek = days[date.getDay()];
        
        return `${month}월 ${day}일 ${dayOfWeek}요일`;
    }
    
    toggleSelectAll(checkbox) {
        const eventCheckboxes = document.querySelectorAll('.event-checkbox');
        eventCheckboxes.forEach(cb => {
            cb.checked = checkbox.checked;
            // Update item background
            const listItem = cb.closest('.event-list-item');
            if (listItem) {
                listItem.style.background = checkbox.checked ? '#d0d0d0' : '#f5f5f5';
            }
        });
        
        // Update bulk actions visibility
        this.updateBulkActions();
    }
    
    handleEventCheckbox(checkbox) {
        // Update select all checkbox state
        const allCheckboxes = document.querySelectorAll('.event-checkbox');
        const checkedCheckboxes = document.querySelectorAll('.event-checkbox:checked');
        const selectAllCheckbox = document.getElementById('select-all-events');
        
        if (selectAllCheckbox) {
            if (checkedCheckboxes.length === 0) {
                selectAllCheckbox.checked = false;
                selectAllCheckbox.indeterminate = false;
            } else if (checkedCheckboxes.length === allCheckboxes.length) {
                selectAllCheckbox.checked = true;
                selectAllCheckbox.indeterminate = false;
            } else {
                selectAllCheckbox.checked = false;
                selectAllCheckbox.indeterminate = true;
            }
        }
        
        // Update item background
        const listItem = checkbox.closest('.event-list-item');
        if (listItem) {
            listItem.style.background = checkbox.checked ? '#d0d0d0' : '#f5f5f5';
        }
        
        // Update bulk actions visibility
        this.updateBulkActions();
    }
    
    updateBulkActions() {
        const checkedCheckboxes = document.querySelectorAll('.event-checkbox:checked');
        const bulkActions = document.getElementById('bulk-actions');
        
        if (bulkActions) {
            if (checkedCheckboxes.length > 0) {
                bulkActions.style.display = 'flex';
                // Update button text with count
                const deleteBtn = bulkActions.querySelector('button');
                if (deleteBtn) {
                    deleteBtn.textContent = `선택 삭제 (${checkedCheckboxes.length})`;
                }
            } else {
                bulkActions.style.display = 'none';
            }
        }
    }
    
    async bulkDeleteEvents() {
        const checkedCheckboxes = document.querySelectorAll('.event-checkbox:checked');
        const eventIds = Array.from(checkedCheckboxes).map(cb => cb.dataset.eventId);
        
        if (eventIds.length === 0) return;
        
        const confirmMessage = eventIds.length === 1 
            ? '선택한 일정을 삭제하시겠습니까?' 
            : `선택한 ${eventIds.length}개의 일정을 삭제하시겠습니까?`;
            
        if (confirm(confirmMessage)) {
            // Delete each event
            for (const eventId of eventIds) {
                const eventData = this.events.find(e => e.id === eventId);
                if (eventData) {
                    // Try to delete from backend if it has a backend ID
                    if (eventData.backendId) {
                        try {
                            const calendarId = document.querySelector('.calendar-workspace')?.dataset.calendarId || 'e3b088c5-58550';
                            await fetch(`/api/calendar/${calendarId}/attendees/${eventData.backendId}`, {
                                method: 'DELETE',
                                headers: {
                                    'Content-Type': 'application/json'
                                }
                            });
                        } catch (error) {
                            console.error('Failed to delete from backend:', error);
                        }
                    }
                    
                    // Remove from DOM
                    const eventElements = document.querySelectorAll(`[data-event-id="${eventId}"]`);
                    eventElements.forEach(element => element.remove());
                }
            }
            
            // Remove from events array
            this.events = this.events.filter(e => !eventIds.includes(e.id));
            
            // Update localStorage
            const storageKey = 'calendar_events_backup';
            localStorage.setItem(storageKey, JSON.stringify(this.events));
            
            // Update event list
            this.updateEventList();
            
            if (window.showNotification) {
                const message = eventIds.length === 1 
                    ? '일정이 삭제되었습니다' 
                    : `${eventIds.length}개의 일정이 삭제되었습니다`;
                showNotification(message, 'success');
            }
        }
    }
    
    highlightEvent(eventId) {
        // Remove previous highlights
        document.querySelectorAll('.calendar-event.highlighted').forEach(el => {
            el.classList.remove('highlighted');
        });
        
        // Find and highlight the event
        const eventElement = document.querySelector(`[data-event-id="${eventId}"]`);
        if (eventElement) {
            eventElement.classList.add('highlighted');
            eventElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
            
            // Add temporary highlight effect
            eventElement.style.transition = 'all 0.3s';
            eventElement.style.transform = 'scale(1.05)';
            eventElement.style.boxShadow = '0 4px 12px rgba(0,0,0,0.3)';
            
            setTimeout(() => {
                eventElement.style.transform = 'scale(1)';
                eventElement.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
            }, 300);
        }
    }
    
    showEventCreationPopup(startDate, endDate, day, hour, clickedCell = null) {
        // Check if popup already exists - if so, reposition it instead of creating new one
        const existingPopup = document.querySelector('.event-creation-popup');
        if (existingPopup && window.eventCreationPopupActive && clickedCell) {
            // Reposition existing popup to new clicked cell location
            this.repositionPopup(existingPopup, clickedCell);
            // Update the time values in the existing popup
            this.updatePopupTimeValues(existingPopup, startDate, endDate, day);
            return;
        }
        
        // Set popup active flag
        window.eventCreationPopupActive = true;
        
        // Remove all existing popups from entire document
        const existingPopups = document.querySelectorAll('.event-creation-popup');
        existingPopups.forEach(popup => {
            popup.remove();
        });
        
        // Also remove any backdrop overlays that might still exist
        const existingBackdrops = document.querySelectorAll('.popup-backdrop');
        existingBackdrops.forEach(backdrop => {
            backdrop.remove();
        });
        
        const popup = document.createElement('div');
        popup.className = 'event-creation-popup';
        
        const startTimeStr = startDate.toLocaleTimeString('ko-KR', { 
            hour: '2-digit', 
            minute: '2-digit',
            hour12: false
        });
        const endTimeStr = endDate.toLocaleTimeString('ko-KR', { 
            hour: '2-digit', 
            minute: '2-digit',
            hour12: false 
        });
        const dateStr = startDate.toLocaleDateString('ko-KR', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            weekday: 'long'
        });
        
        // Generate random gradient colors
        const gradients = [
            'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
            'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
            'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
            'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
            'linear-gradient(135deg, #30cfd0 0%, #330867 100%)'
        ];
        const randomGradient = gradients[Math.floor(Math.random() * gradients.length)];
        
        popup.innerHTML = `
            <div class="popup-header" style="background: ${randomGradient};">
                <h2 class="popup-title">새 일정</h2>
                <button type="button" class="popup-close-btn" onclick="event.stopPropagation(); window.googleCalendarGrid.closeEventPopup()">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M6 18L18 6M6 6l12 12"/>
                    </svg>
                </button>
            </div>
            
            <div class="popup-content">
                <div class="event-form-wrapper">
                    <!-- Title Input -->
                    <div class="form-group title-group-compact">
                        <input type="text" name="title" class="event-title-input-compact" placeholder="제목을 입력하세요" required>
                    </div>
                    
                    <!-- Date & Time Row -->
                    <div class="form-group datetime-compact">
                        <div class="datetime-row-compact">
                            <div class="date-info">
                                <span class="date-label">📅</span>
                                <span class="date-text">${dateStr.split(' ').slice(1, 3).join(' ')}</span>
                            </div>
                            <div class="time-range-compact">
                                <button type="button" class="time-btn" data-type="start" onclick="window.googleCalendarGrid.showTimePicker(this, 'start')">
                                    ${startTimeStr}
                                </button>
                                <span class="time-separator">–</span>
                                <button type="button" class="time-btn" data-type="end" onclick="window.googleCalendarGrid.showTimePicker(this, 'end')">
                                    ${endTimeStr}
                                </button>
                            </div>
                            <div class="all-day-compact">
                                <label class="toggle-compact">
                                    <input type="checkbox" class="all-day-checkbox" onchange="window.googleCalendarGrid.toggleAllDay(this)">
                                    <span class="toggle-switch-compact"></span>
                                    <span class="toggle-text-compact">종일</span>
                                </label>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Description (Optional & Compact) -->
                    <div class="form-group description-compact">
                        <textarea name="description" class="description-input-compact" placeholder="설명 (선택사항)" rows="1"></textarea>
                    </div>
                    
                    <!-- Color Selection (Horizontal & Compact) -->
                    <div class="form-group color-compact">
                        <div class="color-row">
                            <span class="color-label">🎨</span>
                            <div class="color-options-compact">
                                <button type="button" class="color-dot active" style="background: #4285f4;" data-color="#4285f4" onclick="window.googleCalendarGrid.selectEventColor(this)"></button>
                                <button type="button" class="color-dot" style="background: #ea4335;" data-color="#ea4335" onclick="window.googleCalendarGrid.selectEventColor(this)"></button>
                                <button type="button" class="color-dot" style="background: #fbbc04;" data-color="#fbbc04" onclick="window.googleCalendarGrid.selectEventColor(this)"></button>
                                <button type="button" class="color-dot" style="background: #34a853;" data-color="#34a853" onclick="window.googleCalendarGrid.selectEventColor(this)"></button>
                                <button type="button" class="color-dot" style="background: #673ab7;" data-color="#673ab7" onclick="window.googleCalendarGrid.selectEventColor(this)"></button>
                                <button type="button" class="color-dot" style="background: #ff6b6b;" data-color="#ff6b6b" onclick="window.googleCalendarGrid.selectEventColor(this)"></button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="popup-footer-compact">
                    <button type="button" class="btn-cancel-compact" onclick="event.stopPropagation(); window.googleCalendarGrid.closeEventPopup()">
                        취소
                    </button>
                    <button type="button" class="btn-save-compact" onclick="window.googleCalendarGrid.saveEventFromFullScreen()">
                        저장
                    </button>
                </div>
                
                <form style="display: none;" id="event-creation-form">
                    <input type="hidden" name="date" value="${this.formatDateForInput(startDate)}">
                    <input type="hidden" name="startTime" value="${startTimeStr}">
                    <input type="hidden" name="endTime" value="${endTimeStr}">
                    <input type="hidden" name="color" value="#1a73e8">
                </form>
            </div>
        `;
        
        // Update main content dimensions before showing popup
        this.updateMainContentDimensions();
        
        // Position popup relative to clicked cell
        // console.log('🎯 Positioning popup, clickedCell:', clickedCell);
        
        let cellToUse = clickedCell;
        
        // If no clickedCell provided, try to find the cell by day and hour
        if (!cellToUse) {
            // console.log('⚠️ No clickedCell provided, searching for cell by day/hour:', day, hour);
            cellToUse = document.querySelector(`.time-cell[data-day="${day}"][data-hour="${hour}"]`);
            // console.log('🔍 Found cell by search:', cellToUse);
        }
        
        if (cellToUse) {
            const cellRect = cellToUse.getBoundingClientRect();
            // console.log('📍 Cell rect:', cellRect);
            
            // Calculate position
            let left = cellRect.right + 10;
            let top = cellRect.top;
            
            // Fixed popup positioning - always use clicked cell position
            const popupWidth = 360;
            const popupHeight = 400;
            
            // Ensure popup doesn't go off-screen
            if (left + popupWidth > window.innerWidth) {
                left = cellRect.left - popupWidth - 10; // Position to the left of cell
            }
            
            if (top + popupHeight > window.innerHeight) {
                top = window.innerHeight - popupHeight - 20; // Position above
            }
            
            // console.log('📍 Final position:', {left, top});
            
            // Always use fixed positioning with consistent size
            popup.style.cssText = `
                position: fixed;
                left: ${left}px;
                top: ${top}px;
                z-index: 1000;
                width: 360px !important;
                height: auto !important;
                transform: none !important;
            `;
        } else {
            // console.log('❌ No valid cell found, using center positioning');
            // Fallback to center positioning with fixed size
            popup.style.cssText = `
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                z-index: 1000;
                width: 360px !important;
                height: auto !important;
            `;
        }
        
        // Close popup when pressing Escape key
        const handleEscape = (event) => {
            if (event.key === 'Escape') {
                this.closeEventPopup();
                document.removeEventListener('keydown', handleEscape);
            }
        };
        document.addEventListener('keydown', handleEscape);
        
        // Append to body
        document.body.appendChild(popup);
        
        // Trigger slide-in animation after a brief delay
        setTimeout(() => {
            popup.classList.add('show');
        }, 10);
        
        // Focus on title input
        setTimeout(() => {
            const titleInput = popup.querySelector('input[name="title"]');
            titleInput.focus();
        }, 100);
        
        // Store popup reference for later use
        this.currentPopup = popup;
    }

    showEditEventPopup(eventId) {
        const eventData = this.events.find(event => event.id === eventId);
        if (!eventData) {
            console.error('Event not found:', eventId);
            return;
        }

        // Remove existing popup
        const existingPopup = document.querySelector('.event-creation-popup');
        if (existingPopup) {
            existingPopup.remove();
        }

        const popup = document.createElement('div');
        popup.className = 'event-creation-popup';
        
        const dateStr = new Date(eventData.date).toLocaleDateString('ko-KR');
        
        popup.innerHTML = `
            <div class="popup-header">
                <div class="popup-title">일정 편집</div>
                <button class="close-btn" onclick="event.stopPropagation(); window.googleCalendarGrid.closeEventPopup()">×</button>
            </div>
            <div class="popup-content">
                <div class="datetime-section">
                    <div class="datetime-row">
                        <div class="datetime-label">날짜</div>
                        <button type="button" class="datetime-button" id="edit-date-button" onclick="window.googleCalendarGrid.showEditDatePicker(this)">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                                <line x1="16" y1="2" x2="16" y2="6"/>
                                <line x1="8" y1="2" x2="8" y2="6"/>
                                <line x1="3" y1="10" x2="21" y2="10"/>
                            </svg>
                            <span class="date-display">${dateStr}</span>
                        </button>
                    </div>
                    <div class="datetime-row">
                        <div class="datetime-label">시간</div>
                        <button type="button" class="datetime-button" id="edit-start-time-button" onclick="window.googleCalendarGrid.showEditTimePicker(this, 'start')">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                <circle cx="12" cy="12" r="10"/>
                                <polyline points="12,6 12,12 16,14"/>
                            </svg>
                            <span class="time-display">${this.formatTimeDisplay(eventData.startTime)}</span>
                        </button>
                        <span class="time-range-separator">-</span>
                        <button type="button" class="datetime-button" id="edit-end-time-button" onclick="window.googleCalendarGrid.showEditTimePicker(this, 'end')">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                <circle cx="12" cy="12" r="10"/>
                                <polyline points="12,6 12,12 16,14"/>
                            </svg>
                            <span class="time-display">${this.formatTimeDisplay(eventData.endTime)}</span>
                        </button>
                    </div>
                </div>
                
                <form class="event-form" id="edit-event-form">
                    <div class="form-section">
                        <div class="form-field">
                            <label>제목</label>
                            <input type="text" name="title" class="title-input" placeholder="일정 제목 입력" required value="${eventData.title}">
                        </div>
                        <div class="form-field">
                            <label>설명</label>
                            <textarea name="description" placeholder="일정 설명 (선택사항)">${eventData.description || ''}</textarea>
                        </div>
                    </div>
                    
                    <input type="hidden" name="date" value="${eventData.date}">
                    <input type="hidden" name="startTime" value="${eventData.startTime}">
                    <input type="hidden" name="endTime" value="${eventData.endTime}">
                    <input type="hidden" name="eventId" value="${eventData.id}">
                </form>
            </div>
            
            <div class="form-actions">
                <button type="button" class="btn-secondary" onclick="window.googleCalendarGrid.deleteEventById('${eventData.id}')">
                    삭제
                </button>
                <button type="button" class="btn-secondary" onclick="event.stopPropagation(); this.closest('.event-creation-popup').remove()">
                    취소
                </button>
                <button type="button" class="btn-primary" onclick="window.googleCalendarGrid.updateEventFromForm()">
                    저장
                </button>
            </div>
        `;
        
        // Update main content dimensions before showing popup
        this.updateMainContentDimensions();
        
        // Add backdrop overlay
        const backdrop = document.createElement('div');
        backdrop.className = 'popup-backdrop';
        backdrop.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(0, 0, 0, 0.5);
            z-index: 999;
            opacity: 0;
            transition: opacity 0.3s ease;
        `;
        
        // Close popup when clicking backdrop
        backdrop.addEventListener('click', () => {
            this.closeEventPopup();
        });
        
        // Close popup when pressing Escape key
        const handleEscape = (event) => {
            if (event.key === 'Escape') {
                this.closeEventPopup();
                document.removeEventListener('keydown', handleEscape);
            }
        };
        document.addEventListener('keydown', handleEscape);
        
        // Append to body for modal overlay effect
        document.body.appendChild(backdrop);
        document.body.appendChild(popup);
        
        // Trigger slide-in animation after a brief delay
        setTimeout(() => {
            backdrop.style.opacity = '1';
            popup.classList.add('show');
        }, 10);
        
        // Focus on title input
        setTimeout(() => {
            const titleInput = popup.querySelector('input[name="title"]');
            titleInput.focus();
            titleInput.select();
        }, 100);
        
        // Store popup reference for later use
        this.currentPopup = popup;
    }

    selectEventInSidebar(eventId) {
        const eventData = this.events.find(event => event.id === eventId);
        if (!eventData) {
            console.error('Event not found:', eventId);
            return;
        }

        // console.log('🎯 Selecting event in sidebar:', eventData);

        // Show the selected event in the sidebar events section
        const dayEventsContainer = document.getElementById('day-events');
        if (!dayEventsContainer) {
            console.error('Day events container not found');
            return;
        }

        // Clear previous selections
        dayEventsContainer.querySelectorAll('.event-item').forEach(item => {
            item.classList.remove('selected');
        });

        // Add or update the event in the sidebar
        this.displayEventInSidebar(eventData);
        
        // Scroll sidebar to show the events section
        const eventsSection = document.querySelector('.events-section');
        if (eventsSection) {
            eventsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    displayEventInSidebar(eventData) {
        const dayEventsContainer = document.getElementById('day-events');
        if (!dayEventsContainer) return;

        // Check if event is already displayed
        let existingEvent = dayEventsContainer.querySelector(`[data-event-id="${eventData.id}"]`);
        
        if (!existingEvent) {
            // Create new event element
            existingEvent = document.createElement('div');
            existingEvent.className = 'event-item';
            existingEvent.setAttribute('data-event-id', eventData.id);
            
            const eventDate = new Date(eventData.date);
            const dateStr = eventDate.toLocaleDateString('ko-KR', { 
                month: 'short', 
                day: 'numeric'
            });
            
            const timeStr = eventData.allDay ? 'All Day' : 
                `${this.formatTimeDisplay(eventData.startTime)} - ${this.formatTimeDisplay(eventData.endTime)}`;
            
            existingEvent.innerHTML = `
                <div class="event-time">${timeStr}</div>
                <div class="event-title">${eventData.title || 'Untitled'}</div>
                <div class="event-date">${dateStr}</div>
                ${eventData.description ? `<div class="event-description">${eventData.description}</div>` : ''}
            `;
            
            dayEventsContainer.appendChild(existingEvent);
        }
        
        // Mark as selected
        existingEvent.classList.add('selected');
        
        // Scroll to the selected event
        existingEvent.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    
    async saveEvent(form, popup) {
        const formData = new FormData(form);
        
        // Use getRandomEventColor if function exists, otherwise use fallback colors
        const fallbackColors = [
            '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316', 
            '#06b6d4', '#84cc16', '#a855f7', '#6366f1', '#dc2626', '#059669', '#d97706', '#7c3aed',
            '#db2777', '#0891b2', '#65a30d', '#4f46e5', '#be123c', '#047857'
        ];
        const randomColor = typeof getRandomEventColor === 'function' ? 
            getRandomEventColor() : 
            fallbackColors[Math.floor(Math.random() * fallbackColors.length)];
        
        const eventData = {
            title: formData.get('title'),
            description: formData.get('description'),
            date: formData.get('date'),
            start_time: `${formData.get('date')}T${formData.get('startTime')}:00`,
            end_time: `${formData.get('date')}T${formData.get('endTime')}:00`,
            color: randomColor // Random color
        };
        
        try {
            // Get calendar ID
            const calendarId = document.querySelector('.calendar-workspace').dataset.calendarId;
            
            // Save to backend
            const response = await fetch(`/api/calendars/${calendarId}/events`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(eventData)
            });
            
            if (response.ok) {
                const savedEvent = await response.json();
                
                // Add ID from server response
                const fullEventData = {
                    ...eventData,
                    id: savedEvent.id || Date.now().toString(),
                    backendId: savedEvent.id,
                    date: formData.get('date'),
                    startTime: formData.get('startTime'),
                    endTime: formData.get('endTime')
                };
                
                // Add to events array
                this.events.push(fullEventData);
                
                // Update localStorage with current events
                const storageKey = 'calendar_events_backup';
                localStorage.setItem(storageKey, JSON.stringify(this.events));
                
                // Save to localStorage as well for persistence
                this.saveToLocalStorage(fullEventData);
                
                // Render the event on the grid
                this.renderEvent(fullEventData);
                
                // Update the event list
                this.updateEventList();
                
                // Show success notification
                if (window.showNotification) {
                    showNotification(`일정 "${eventData.title}"이 생성되었습니다`, 'success');
                }
                
                // console.log('📅 Event created and saved:', fullEventData);
            } else {
                throw new Error('Failed to save event');
            }
        } catch (error) {
            console.error('Failed to save event:', error);
            
            // Still show the event locally for user experience
            const localEventData = {
                ...eventData,
                id: Date.now().toString(),
                backendId: null,
                date: formData.get('date'),
                startTime: formData.get('startTime'),
                endTime: formData.get('endTime')
            };
            
            this.events.push(localEventData);
            this.renderEvent(localEventData);
            
            // Update localStorage with current events
            const storageKey = 'calendar_events_backup';
            localStorage.setItem(storageKey, JSON.stringify(this.events));
            
            // Update the event list
            this.updateEventList();
            
            // Show warning notification
            if (window.showNotification) {
                showNotification('일정이 로컬에만 저장되었습니다', 'warning');
            }
            
            // Force re-render after a short delay
            setTimeout(() => {
                // console.log('🔄 Force re-rendering event...');
                this.renderEvent(localEventData);
            }, 100);
        }
        
        // Remove popup
        popup.remove();
    }
    
    renderEvent(eventData) {
        // console.log('🎯 renderEvent called with data:', eventData);
        
        // Check for null/undefined event data
        if (!eventData || !eventData.id) {
            console.warn('⚠️ Skipping null or invalid event data:', eventData);
            return;
        }
        
        // Fix null date issue
        if (!eventData.date || eventData.date === null || eventData.date === undefined) {
            console.warn('⚠️ Event has null date, providing fallback:', eventData);
            const today = new Date();
            eventData.date = today.toISOString().split('T')[0];
        }
        
        // Ensure weekStart is properly initialized
        if (!this.weekStart || !(this.weekStart instanceof Date)) {
            this.weekStart = this.getWeekStart(new Date());
            // console.log('⚠️ weekStart was undefined in renderEvent, recalculated:', this.weekStart);
        }
        
        // Parse date more carefully to avoid timezone issues
        const eventDateStr = eventData.date;
        // Split the date string to get year, month, day
        const [year, month, day] = eventDateStr.split('-').map(Number);
        const eventDate = new Date(year, month - 1, day, 12, 0, 0); // month is 0-indexed
        
        const weekStart = new Date(this.weekStart);
        weekStart.setHours(12, 0, 0, 0);
        
        // Calculate day index more precisely
        const timeDiff = eventDate.getTime() - weekStart.getTime();
        const dayIndex = Math.round(timeDiff / (24 * 60 * 60 * 1000));
        
        // console.log('📅 Event date string:', eventDateStr);
        // console.log('📅 Event date (parsed):', eventDate);
        // console.log('📅 Week start (noon):', weekStart);
        // console.log('📅 Time difference (ms):', timeDiff);
        // console.log('📅 Day index:', dayIndex);
        
        if (dayIndex < -1 || dayIndex > 7) { // Allow more flexible range
            // console.log('❌ Event too far from current week, skipping render. DayIndex:', dayIndex);
            return; // Not in current week
        }
        
        // Adjust dayIndex if it's negative (previous week) or > 6 (next week)
        if (dayIndex < 0) {
            // console.log('⚠️ Event from previous week, adjusting...');
        } else if (dayIndex > 6) {
            // console.log('⚠️ Event from next week, adjusting...');
        }
        
        // Check if this is a multi-day event - skip individual rendering
        if (eventData.isMultiDay) {
            // console.log('🔄 Skipping individual render for multi-day event:', eventData.title);
            // console.log('   Multi-day events should be rendered via renderMultiDayEvent');
            return;
        }
        
        // Check if this is an all-day event
        if (eventData.isAllDay) {
            // console.log('📅 Rendering all-day event:', eventData.title);
            // For all-day events, render them in a special all-day section or as full-day blocks
            this.renderAllDayEvent(eventData, dayIndex);
            return;
        }
        
        // Check if startTime and endTime exist for timed events
        if (!eventData.startTime || !eventData.endTime) {
            console.warn('⚠️ Event missing time information, treating as all-day:', eventData);
            this.renderAllDayEvent(eventData, dayIndex);
            return;
        }
        
        const [startHour, startMin] = eventData.startTime.split(':').map(Number);
        const [endHour, endMin] = eventData.endTime.split(':').map(Number);
        
        const startPosition = startHour + startMin / 60;
        const endPosition = endHour + endMin / 60;
        const duration = endPosition - startPosition;
        
        // Ensure dayIndex is within valid range (0-6 for day columns)
        const validDayIndex = Math.max(0, Math.min(6, dayIndex));
        // console.log('🔍 Original dayIndex:', dayIndex, 'Adjusted to:', validDayIndex);
        
        const dayColumn = this.container.querySelector(`.day-column[data-day="${validDayIndex}"]`);
        // console.log('🔍 Looking for day column with dayIndex:', validDayIndex, 'Found:', dayColumn);
        
        if (!dayColumn) {
            // console.log('❌ Day column not found! Available columns:', 
            //     this.container.querySelectorAll('.day-column'));
            return;
        }
        
        const eventElement = document.createElement('div');
        eventElement.className = 'calendar-event';
        
        // Apply color as inline style if it's a hex color
        if (eventData.color && eventData.color.startsWith('#')) {
            eventElement.style.backgroundColor = eventData.color;
        } else if (eventData.color) {
            // If it's a color class name
            eventElement.classList.add(eventData.color);
        } else {
            // Default color if none specified
            eventElement.style.backgroundColor = '#3b82f6';
        }
        
        eventElement.innerHTML = `
            <div class="calendar-event-actions">
                <button class="calendar-event-edit" onclick="window.googleCalendarGrid.selectEventInSidebar('${eventData.id}'); event.stopPropagation();" title="편집">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                        <path d="m18.5 2.5 a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                    </svg>
                </button>
                <button class="calendar-event-delete" onclick="window.googleCalendarGrid.deleteEventById('${eventData.id}'); event.stopPropagation();" title="삭제">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <polyline points="3,6 5,6 21,6"/>
                        <path d="m19,6v14a2,2 0 0,1-2,2H7a2,2 0 0,1-2-2V6m3,0V4a2,2 0 0,1,2-2h4a2,2 0 0,1,2,2v2"/>
                    </svg>
                </button>
            </div>
            <div class="calendar-event-content">
                <div style="font-weight: 500; margin-bottom: 2px; padding-left: 2px;">${eventData.title}</div>
                ${eventData.description ? `<div style="font-size: 11px; opacity: 0.9; padding-left: 2px;">${eventData.description}</div>` : ''}
            </div>
        `;
        
        // console.log('🎨 Event color:', eventData.color, 'Background:', eventElement.style.backgroundColor);
        
        // Position the event
        const top = (startPosition - this.startHour) * this.timeSlotHeight;
        const height = duration * this.timeSlotHeight - 2; // -2 for spacing
        
        eventElement.style.position = 'absolute';
        eventElement.style.top = `${top}px`;
        eventElement.style.left = '2px';
        eventElement.style.right = '2px';
        eventElement.style.height = `${height}px`;
        eventElement.style.zIndex = '100'; // Increased z-index
        eventElement.style.cursor = 'move';
        eventElement.style.border = '1px solid rgba(0,0,0,0.1)'; // Add border for visibility
        eventElement.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)'; // Add shadow
        
        // Add drag functionality for real-time time editing
        eventElement.draggable = true;
        eventElement.dataset.eventId = eventData.id;
        eventElement.dataset.originalTop = top;
        eventElement.dataset.eventData = JSON.stringify(eventData);
        
        // Add right-click context menu
        eventElement.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            this.showEventContextMenu(e, eventData);
        });
        
        eventElement.addEventListener('dragstart', (e) => {
            eventElement.style.opacity = '0.7';
            e.dataTransfer.setData('text/plain', eventData.id);
        });
        
        eventElement.addEventListener('dragend', (e) => {
            eventElement.style.opacity = '1';
        });
        
        dayColumn.appendChild(eventElement);
        // console.log('✅ Event element added to DOM:', eventElement, 'Parent:', dayColumn);
        // console.log('📍 Event position - top:', eventElement.style.top, 'height:', eventElement.style.height);
    }
    
    renderAllDayEvent(eventData, dayIndex) {
        // console.log('🎯 renderAllDayEvent called with data:', eventData, 'dayIndex:', dayIndex);
        
        // Check if this is a multi-day event - skip all-day rendering
        if (eventData.isMultiDay) {
            // console.log('🔄 Skipping all-day render for multi-day event:', eventData.title);
            // console.log('   Multi-day events should be rendered via renderMultiDayEvent only');
            return;
        }
        
        // Ensure dayIndex is within valid range (0-6 for day columns)
        const validDayIndex = Math.max(0, Math.min(6, dayIndex));
        
        const dayColumn = this.container.querySelector(`.day-column[data-day="${validDayIndex}"]`);
        
        if (!dayColumn) {
            // console.log('❌ Day column not found for all-day event! DayIndex:', validDayIndex);
            return;
        }
        
        // Find or create all-day events container at the top of the column
        let allDayContainer = dayColumn.querySelector('.all-day-events-container');
        if (!allDayContainer) {
            allDayContainer = document.createElement('div');
            allDayContainer.className = 'all-day-events-container';
            allDayContainer.style.cssText = `
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                min-height: 30px;
                background: rgba(59, 130, 246, 0.1);
                border-bottom: 1px solid rgba(59, 130, 246, 0.3);
                padding: 4px;
                z-index: 10;
            `;
            dayColumn.insertBefore(allDayContainer, dayColumn.firstChild);
        }
        
        const eventElement = document.createElement('div');
        eventElement.className = 'calendar-event all-day-event';
        eventElement.dataset.eventId = eventData.id;
        
        // Apply color as inline style
        if (eventData.color && eventData.color.startsWith('#')) {
            eventElement.style.backgroundColor = eventData.color;
        } else {
            eventElement.style.backgroundColor = '#3b82f6';
        }
        
        eventElement.style.cssText += `
            position: relative;
            width: 100%;
            padding: 4px 8px;
            margin-bottom: 2px;
            border-radius: 4px;
            color: white;
            font-size: 12px;
            cursor: pointer;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        `;
        
        eventElement.innerHTML = `
            <div class="calendar-event-content">
                <div class="calendar-event-title">${eventData.title || 'Untitled'}</div>
                <div class="calendar-event-badge" style="display: inline-block; padding: 2px 6px; background: rgba(255,255,255,0.2); border-radius: 3px; font-size: 10px; margin-left: 4px;">All Day</div>
            </div>
            <div class="calendar-event-actions" style="position: absolute; top: 4px; right: 4px; display: none;">
                <button class="calendar-event-edit" onclick="window.googleCalendarGrid.selectEventInSidebar('${eventData.id}'); event.stopPropagation();" title="편집" style="background: none; border: none; color: white; cursor: pointer; padding: 2px;">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                        <path d="m18.5 2.5 a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                    </svg>
                </button>
                <button class="calendar-event-delete" onclick="window.googleCalendarGrid.deleteEventById('${eventData.id}'); event.stopPropagation();" title="삭제" style="background: none; border: none; color: white; cursor: pointer; padding: 2px;">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <polyline points="3,6 5,6 21,6"/>
                        <path d="m19,6v14a2,2 0 0,1-2,2H7a2,2 0 0,1-2-2V6m3,0V4a2,2 0 0,1,2-2h4a2,2 0 0,1,2,2v2"/>
                    </svg>
                </button>
            </div>
        `;
        
        // Show actions on hover
        eventElement.addEventListener('mouseenter', () => {
            const actions = eventElement.querySelector('.calendar-event-actions');
            if (actions) actions.style.display = 'flex';
        });
        
        eventElement.addEventListener('mouseleave', () => {
            const actions = eventElement.querySelector('.calendar-event-actions');
            if (actions) actions.style.display = 'none';
        });
        
        // Add click handler to select event in sidebar
        eventElement.addEventListener('click', (e) => {
            if (!e.target.closest('.calendar-event-actions')) {
                this.selectEventInSidebar(eventData.id);
            }
        });
        
        allDayContainer.appendChild(eventElement);
        // console.log('✅ All-day event element added to DOM:', eventElement);
    }
    
    renderMultiDayEvent(eventData) {
        // console.log('🎯 renderMultiDayEvent called with data:', eventData);
        
        // Check for null/undefined event data
        if (!eventData || !eventData.id) {
            console.warn('⚠️ Skipping null or invalid multi-day event data:', eventData);
            return;
        }
        
        // Ensure we have start and end dates
        if (!eventData.date || !eventData.endDate) {
            console.warn('⚠️ Multi-day event missing start or end date:', eventData);
            return;
        }
        
        // Ensure weekStart is properly initialized
        if (!this.weekStart || !(this.weekStart instanceof Date)) {
            this.weekStart = this.getWeekStart(new Date());
            // console.log('⚠️ weekStart was undefined in renderMultiDayEvent, recalculated:', this.weekStart);
        }
        
        // Parse start and end dates
        const [startYear, startMonth, startDay] = eventData.date.split('-').map(Number);
        const [endYear, endMonth, endDay] = eventData.endDate.split('-').map(Number);
        
        // Parse time for positioning (if available)
        let startHour = 9, startMin = 0, endHour = 10, endMin = 0;
        if (eventData.startTime && eventData.endTime) {
            [startHour, startMin] = eventData.startTime.split(':').map(Number);
            [endHour, endMin] = eventData.endTime.split(':').map(Number);
            // console.log('🕐 Time range:', eventData.startTime, 'to', eventData.endTime);
        } else {
            console.warn('⚠️ Multi-day event missing time info:', eventData);
            console.warn('   This event should have been created with time information');
            console.warn('   Using default 9AM-10AM as fallback');
        }
        
        const startDate = new Date(startYear, startMonth - 1, startDay, startHour, startMin, 0);
        const endDate = new Date(endYear, endMonth - 1, endDay, endHour, endMin, 0);
        
        const weekStart = new Date(this.weekStart);
        weekStart.setHours(12, 0, 0, 0);
        
        // Calculate start and end day indices
        const startTimeDiff = startDate.getTime() - weekStart.getTime();
        const endTimeDiff = endDate.getTime() - weekStart.getTime();
        
        const startDayIndex = Math.round(startTimeDiff / (24 * 60 * 60 * 1000));
        const endDayIndex = Math.round(endTimeDiff / (24 * 60 * 60 * 1000));
        
        // console.log('📅 Multi-day event - Start:', startDate, 'End:', endDate);
        // console.log('📅 Day indices - Start:', startDayIndex, 'End:', endDayIndex);
        
        const startPosition = startHour + startMin / 60;
        const endPosition = endHour + endMin / 60;
        const duration = endPosition - startPosition;
        
        // console.log('🎯 Multi-day position calculation:', {
        //     startHour, startMin, endHour, endMin,
        //     startPosition, endPosition, duration,
        //     timeSlotHeight: this.timeSlotHeight,
        //     calculatedTop: startPosition * this.timeSlotHeight,
        //     calculatedHeight: Math.max(duration * this.timeSlotHeight, 24)
        // });
        
        // Create a single continuous element that spans multiple days
        const firstDayIndex = Math.max(0, startDayIndex);
        const lastDayIndex = Math.min(6, endDayIndex);
        const spanDays = lastDayIndex - firstDayIndex + 1;
        
        // Find the first day column to start the event
        const firstDayColumn = this.container.querySelector(`.day-column[data-day="${firstDayIndex}"]`);
        
        if (!firstDayColumn) {
            // console.log('❌ First day column not found for dayIndex:', firstDayIndex);
            return;
        }
        
        // Calculate accurate width for spanning
        let totalWidth;
        if (spanDays === 1) {
            totalWidth = firstDayColumn.offsetWidth - 4; // Single day event
        } else {
            // Multi-day spanning: find the last column and calculate actual distance
            const lastDayColumn = this.container.querySelector(`.day-column[data-day="${lastDayIndex}"]`);
            if (lastDayColumn) {
                const firstColRect = firstDayColumn.getBoundingClientRect();
                const lastColRect = lastDayColumn.getBoundingClientRect();
                totalWidth = (lastColRect.right - firstColRect.left) - 4; // Actual span minus margins
                // console.log('📏 Spanning calculation:', {
                //     spanDays,
                //     firstCol: firstColRect.left,
                //     lastCol: lastColRect.right,
                //     totalWidth
                // });
            } else {
                // Fallback calculation
                totalWidth = firstDayColumn.offsetWidth * spanDays - 4;
                // console.log('⚠️ Using fallback width calculation');
            }
        }
        
        // Create the spanning event element
        const eventElement = document.createElement('div');
        eventElement.className = 'calendar-event multi-day-event spanning-event';
        eventElement.dataset.eventId = eventData.id;
        eventElement.dataset.eventData = JSON.stringify(eventData);
        eventElement.dataset.isMultiDay = 'true';
        
        // Apply color
        const bgColor = (eventData.color && eventData.color.startsWith('#')) ? eventData.color : '#3b82f6';
        
        eventElement.style.cssText = `
            position: absolute;
            top: ${startPosition * this.timeSlotHeight}px;
            left: 2px;
            width: ${totalWidth}px;
            height: ${Math.max(duration * this.timeSlotHeight, 24)}px;
            background-color: ${bgColor};
            z-index: 200;
            border-radius: 4px;
            padding: 4px;
            color: white;
            cursor: pointer;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.2);
            border: 1px solid rgba(255,255,255,0.2);
        `;
        
        // Add continuity indicators
        let continuityIndicator = '';
        if (startDayIndex < 0) continuityIndicator = '◀ ';
        if (endDayIndex > 6) continuityIndicator += ' ▶';
        
        eventElement.innerHTML = `
            <div class="calendar-event-actions" style="position: absolute; top: 2px; right: 2px; display: none; gap: 2px;">
                <button class="calendar-event-edit" onclick="window.googleCalendarGrid.selectEventInSidebar('${eventData.id}'); event.stopPropagation();" title="편집" style="background: rgba(0,0,0,0.3); border: none; color: white; cursor: pointer; padding: 4px; border-radius: 2px;">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                        <path d="m18.5 2.5 a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                    </svg>
                </button>
                <button class="calendar-event-delete" onclick="window.googleCalendarGrid.deleteEventById('${eventData.id}'); event.stopPropagation();" title="삭제" style="background: rgba(220,38,38,0.8); border: none; color: white; cursor: pointer; padding: 4px; border-radius: 2px;">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <polyline points="3,6 5,6 21,6"/>
                        <path d="m19,6v14a2,2 0 0,1-2,2H7a2,2 0 0,1-2-2V6m3,0V4a2,2 0 0,1,2-2h4a2,2 0 0,1,2,2v2"/>
                    </svg>
                </button>
            </div>
            <div class="calendar-event-content">
                <div style="font-weight: 600; font-size: 12px; line-height: 1.2;">${eventData.title}${continuityIndicator}</div>
                ${duration > 1 && eventData.startTime ? `<div style="font-size: 10px; opacity: 0.9; margin-top: 1px;">${eventData.startTime} - ${eventData.endTime}</div>` : ''}
                ${spanDays > 1 ? `<div style="font-size: 9px; opacity: 0.8; background: rgba(255,255,255,0.2); display: inline-block; padding: 1px 4px; border-radius: 2px; margin-top: 2px;">${spanDays}일간</div>` : ''}
            </div>
        `;
        
        // Add hover effects
        eventElement.addEventListener('mouseenter', () => {
            const actions = eventElement.querySelector('.calendar-event-actions');
            if (actions) actions.style.display = 'flex';
        });
        
        eventElement.addEventListener('mouseleave', () => {
            const actions = eventElement.querySelector('.calendar-event-actions');
            if (actions) actions.style.display = 'none';
        });
        
        // Add click handler to select event in sidebar
        eventElement.addEventListener('click', (e) => {
            if (!e.target.closest('.calendar-event-actions')) {
                this.selectEventInSidebar(eventData.id);
            }
        });
        
        // Add right-click context menu
        eventElement.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            this.showEventContextMenu(e, eventData);
        });
        
        // Add to the first day column
        firstDayColumn.appendChild(eventElement);
        
        // console.log(`✅ Multi-day spanning event "${eventData.title}" rendered across ${spanDays} days (${firstDayIndex} to ${lastDayIndex})`);
        
        // Remove the duplicate rendering - the spanning event already covers all days
        return;
        
        // DISABLED: Individual day rendering (causes duplicate events)
        /*
        for (let dayIndex = Math.max(0, startDayIndex); dayIndex <= Math.min(6, endDayIndex); dayIndex++) {
            const dayColumn = this.container.querySelector(`.day-column[data-day="${dayIndex}"]`);
            
            if (!dayColumn) {
                // console.log('❌ Day column not found for dayIndex:', dayIndex);
                continue;
            }
            
            const eventElement = document.createElement('div');
            eventElement.className = 'calendar-event multi-day-event';
            
            // Apply color as inline style
            if (eventData.color && eventData.color.startsWith('#')) {
                eventElement.style.backgroundColor = eventData.color;
            } else {
                eventElement.style.backgroundColor = '#3b82f6';
            }
            
            // Add visual indicator for multi-day span
            let titlePrefix = '';
            if (dayIndex === startDayIndex && startDayIndex >= 0) {
                titlePrefix = '▶ '; // Start indicator
            } else if (dayIndex === endDayIndex && endDayIndex <= 6) {
                titlePrefix = '◀ '; // End indicator  
            } else {
                titlePrefix = '─ '; // Middle indicator
            }
            
            eventElement.innerHTML = `
                <div class="calendar-event-actions">
                    <button class="calendar-event-edit" onclick="window.googleCalendarGrid.selectEventInSidebar('${eventData.id}'); event.stopPropagation();" title="편집">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                            <path d="m18.5 2.5 a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                        </svg>
                    </button>
                    <button class="calendar-event-delete" onclick="window.googleCalendarGrid.deleteEventById('${eventData.id}'); event.stopPropagation();" title="삭제">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                            <polyline points="3,6 5,6 21,6"/>
                            <path d="m19,6v14a2,2 0 0,1-2,2H7a2,2 0 0,1-2-2V6m3,0V4a2,2 0 0,1,2,2h4a2,2 0 0,1,2,2v2"/>
                        </svg>
                    </button>
                </div>
                <div class="calendar-event-content">
                    <div style="font-weight: 500; margin-bottom: 2px; padding-left: 2px;">${titlePrefix}${eventData.title}</div>
                    ${eventData.description ? `<div style="font-size: 11px; opacity: 0.9; padding-left: 2px;">${eventData.description}</div>` : ''}
                    <div style="font-size: 10px; opacity: 0.7; padding-left: 2px;">종일 일정</div>
                </div>
            `;
            
            // Position the event at the top of the day (all-day area)
            eventElement.style.position = 'absolute';
            eventElement.style.top = '5px';
            eventElement.style.left = '2px';
            eventElement.style.right = '2px';
            eventElement.style.height = '50px'; // Fixed height for all-day events
            eventElement.style.zIndex = '200'; // Higher z-index than timed events
            eventElement.style.cursor = 'pointer';
            eventElement.style.border = '1px solid rgba(0,0,0,0.1)';
            eventElement.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
            eventElement.style.borderRadius = '4px';
            
            // Add event data
            eventElement.dataset.eventId = eventData.id;
            eventElement.dataset.eventData = JSON.stringify(eventData);
            eventElement.dataset.isMultiDay = 'true';
            
            // Add right-click context menu
            eventElement.addEventListener('contextmenu', (e) => {
                e.preventDefault();
                this.showEventContextMenu(e, eventData);
            });
            
            dayColumn.appendChild(eventElement);
            
            // console.log(`✅ Multi-day event "${eventData.title}" rendered on day ${dayIndex}`);
        }
        */
    }
    
    handleEventDrop(e) {
        e.preventDefault();
        
        const eventId = e.dataTransfer.getData('text/plain');
        const targetCell = e.target.closest('.time-cell');
        
        if (!targetCell || !eventId) return;
        
        const newDay = parseInt(targetCell.dataset.day);
        const newHour = parseInt(targetCell.dataset.hour);
        
        // Check if this is a trash event restoration
        const trashedEvent = this.trashedEvents.find(event => event.id === eventId);
        
        if (trashedEvent) {
            // This is a trash restoration - show confirmation dialog
            this.showRestoreConfirmation(trashedEvent, newDay, newHour, targetCell);
            return;
        }
        
        // Find the event element and data (existing event move)
        const eventElement = this.container.querySelector(`[data-event-id="${eventId}"]`);
        const eventData = this.events.find(event => event.id === eventId);
        
        if (!eventElement || !eventData) return;
        
        // Calculate duration from original event
        const [startHour, startMin] = eventData.startTime.split(':').map(Number);
        const [endHour, endMin] = eventData.endTime.split(':').map(Number);
        const duration = (endHour * 60 + endMin) - (startHour * 60 + startMin); // duration in minutes
        
        // Update event data
        eventData.startTime = `${newHour.toString().padStart(2, '0')}:00`;
        const newEndMinutes = newHour * 60 + duration;
        const newEndHour = Math.floor(newEndMinutes / 60);
        const newEndMin = newEndMinutes % 60;
        eventData.endTime = `${newEndHour.toString().padStart(2, '0')}:${newEndMin.toString().padStart(2, '0')}`;
        
        // Update date if dropped on different day
        const newDate = new Date(this.weekStart);
        newDate.setDate(newDate.getDate() + newDay);
        eventData.date = newDate.toISOString().split('T')[0];
        
        // Update element position
        const newTop = (newHour - this.startHour) * this.timeSlotHeight;
        eventElement.style.top = `${newTop}px`;
        
        // Move element to correct day column
        const newDayColumn = this.container.querySelector(`.day-column[data-day="${newDay}"]`);
        if (newDayColumn && eventElement.parentNode !== newDayColumn) {
            newDayColumn.appendChild(eventElement);
        }
        
        // console.log('📅 Event time updated:', eventData);
        
        // Show notification
        if (window.showNotification) {
            showNotification(`일정 "${eventData.title}" 시간이 수정되었습니다`, 'success');
        }
    }

    // New methods for full screen event creation UI
    showDatePicker(button) {
        // Create date picker input element
        const dateInput = document.createElement('input');
        dateInput.type = 'date';
        dateInput.style.position = 'absolute';
        dateInput.style.left = '-9999px';
        dateInput.style.opacity = '0';
        
        // Get current date from hidden input
        const form = document.getElementById('event-creation-form');
        const currentDate = form.querySelector('input[name="date"]').value;
        dateInput.value = currentDate;
        
        document.body.appendChild(dateInput);
        dateInput.focus();
        dateInput.click();
        
        dateInput.addEventListener('change', (e) => {
            const selectedDate = new Date(e.target.value + 'T00:00:00');
            const formattedDate = selectedDate.toLocaleDateString('ko-KR');
            
            // Update button display
            button.querySelector('.date-display').textContent = formattedDate;
            
            // Update hidden input
            form.querySelector('input[name="date"]').value = e.target.value;
            
            // Remove temporary input
            document.body.removeChild(dateInput);
        });
        
        dateInput.addEventListener('blur', () => {
            setTimeout(() => {
                if (document.body.contains(dateInput)) {
                    document.body.removeChild(dateInput);
                }
            }, 100);
        });
    }
    
    showTimePicker(button, timeType) {
        // Create time picker input element
        const timeInput = document.createElement('input');
        timeInput.type = 'time';
        timeInput.style.position = 'absolute';
        timeInput.style.left = '-9999px';
        timeInput.style.opacity = '0';
        
        // Get current time from hidden input
        const form = document.getElementById('event-creation-form');
        const currentTime = form.querySelector(`input[name="${timeType}Time"]`).value;
        timeInput.value = currentTime;
        
        document.body.appendChild(timeInput);
        timeInput.focus();
        timeInput.click();
        
        timeInput.addEventListener('change', (e) => {
            const selectedTime = e.target.value;
            const [hours, minutes] = selectedTime.split(':');
            const hour24 = parseInt(hours);
            
            // Format display time with Korean AM/PM
            let displayTime;
            if (hour24 === 0) {
                displayTime = `오전 ${selectedTime}`;
            } else if (hour24 < 12) {
                displayTime = `오전 ${selectedTime}`;
            } else if (hour24 === 12) {
                displayTime = `오후 ${selectedTime}`;
            } else {
                displayTime = `오후 ${selectedTime}`;
            }
            
            // Update button display
            button.querySelector('.time-display').textContent = displayTime;
            button.classList.add('active');
            
            // Update hidden input
            form.querySelector(`input[name="${timeType}Time"]`).value = selectedTime;
            
            // Remove temporary input
            document.body.removeChild(timeInput);
        });
        
        timeInput.addEventListener('blur', () => {
            setTimeout(() => {
                if (document.body.contains(timeInput)) {
                    document.body.removeChild(timeInput);
                }
            }, 100);
        });
    }
    
    async saveEventFromFullScreen() {
        const popup = document.querySelector('.event-creation-popup');
        if (!popup) return;
        
        const titleInput = popup.querySelector('input[name="title"]');
        const descriptionInput = popup.querySelector('textarea[name="description"]');
        const form = document.getElementById('event-creation-form');
        
        if (!form || !titleInput) return;
        
        // Validate required fields
        if (!titleInput.value.trim()) {
            alert('일정 제목을 입력해주세요.');
            titleInput.focus();
            return;
        }
        
        // Use getRandomEventColor if function exists, otherwise use fallback colors
        const fallbackColors = [
            '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316', 
            '#06b6d4', '#84cc16', '#a855f7', '#6366f1', '#dc2626', '#059669', '#d97706', '#7c3aed',
            '#db2777', '#0891b2', '#65a30d', '#4f46e5', '#be123c', '#047857'
        ];
        const randomColor = typeof getRandomEventColor === 'function' ? 
            getRandomEventColor() : 
            fallbackColors[Math.floor(Math.random() * fallbackColors.length)];
        
        const formData = new FormData(form);
        
        const eventData = {
            title: titleInput.value.trim(),
            description: descriptionInput ? descriptionInput.value.trim() : '',
            date: formData.get('date'),
            startTime: formData.get('startTime'),
            endTime: formData.get('endTime'),
            color: randomColor,
            id: this.generateEventId()
        };
        
        try {
            // Save to server
            const response = await fetch(`/api/calendars/${this.calendarId}/events`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(eventData)
            });
            
            if (response.ok) {
                const savedEvent = await response.json();
                // console.log('✅ Event saved to server:', savedEvent);
                
                // Add to local events
                this.events.push(eventData);
                
                // Save to localStorage backup
                this.saveToLocalStorage();
                
                // Re-render calendar
                this.renderEvents();
                this.updateEventList();
                
                // Close popup
                if (this.currentPopup) {
                    this.currentPopup.remove();
                    this.currentPopup = null;
                }
                
                // Show success notification
                if (window.showNotification) {
                    showNotification(`일정 "${eventData.title}"이(가) 저장되었습니다`, 'success');
                }
            } else {
                throw new Error('Failed to save event to server');
            }
        } catch (error) {
            console.error('❌ Error saving event:', error);
            
            // Still save locally for offline functionality
            this.events.push(eventData);
            this.saveToLocalStorage();
            this.renderEvents();
            this.updateEventList();
            
            // Close popup
            if (this.currentPopup) {
                this.currentPopup.remove();
                this.currentPopup = null;
            }
            
            // Show warning notification
            if (window.showNotification) {
                showNotification(`일정이 로컬에 저장되었습니다 (서버 오류)`, 'warning');
            }
        }
    }

    // Edit mode helper methods
    formatTimeDisplay(time) {
        const [hours, minutes] = time.split(':');
        const hour24 = parseInt(hours);
        
        if (hour24 === 0) {
            return `오전 12:${minutes}`;
        } else if (hour24 < 12) {
            return `오전 ${time}`;
        } else if (hour24 === 12) {
            return `오후 ${time}`;
        } else {
            const hour12 = hour24 - 12;
            const displayHour = hour12 < 10 ? `0${hour12}` : hour12;
            return `오후 ${displayHour}:${minutes}`;
        }
    }

    showEditDatePicker(button) {
        // Create date picker input element
        const dateInput = document.createElement('input');
        dateInput.type = 'date';
        dateInput.style.position = 'absolute';
        dateInput.style.left = '-9999px';
        dateInput.style.opacity = '0';
        
        // Get current date from hidden input
        const form = document.getElementById('edit-event-form');
        const currentDate = form.querySelector('input[name="date"]').value;
        dateInput.value = currentDate;
        
        document.body.appendChild(dateInput);
        dateInput.focus();
        dateInput.click();
        
        dateInput.addEventListener('change', (e) => {
            const selectedDate = new Date(e.target.value + 'T00:00:00');
            const formattedDate = selectedDate.toLocaleDateString('ko-KR');
            
            // Update button display
            button.querySelector('.date-display').textContent = formattedDate;
            
            // Update hidden input
            form.querySelector('input[name="date"]').value = e.target.value;
            
            // Remove temporary input
            document.body.removeChild(dateInput);
        });
        
        dateInput.addEventListener('blur', () => {
            setTimeout(() => {
                if (document.body.contains(dateInput)) {
                    document.body.removeChild(dateInput);
                }
            }, 100);
        });
    }
    
    showEditTimePicker(button, timeType) {
        // Create time picker input element
        const timeInput = document.createElement('input');
        timeInput.type = 'time';
        timeInput.style.position = 'absolute';
        timeInput.style.left = '-9999px';
        timeInput.style.opacity = '0';
        
        // Get current time from hidden input
        const form = document.getElementById('edit-event-form');
        const currentTime = form.querySelector(`input[name="${timeType}Time"]`).value;
        timeInput.value = currentTime;
        
        document.body.appendChild(timeInput);
        timeInput.focus();
        timeInput.click();
        
        timeInput.addEventListener('change', (e) => {
            const selectedTime = e.target.value;
            const displayTime = this.formatTimeDisplay(selectedTime);
            
            // Update button display
            button.querySelector('.time-display').textContent = displayTime;
            button.classList.add('active');
            
            // Update hidden input
            form.querySelector(`input[name="${timeType}Time"]`).value = selectedTime;
            
            // Remove temporary input
            document.body.removeChild(timeInput);
        });
        
        timeInput.addEventListener('blur', () => {
            setTimeout(() => {
                if (document.body.contains(timeInput)) {
                    document.body.removeChild(timeInput);
                }
            }, 100);
        });
    }

    async updateEventFromForm() {
        const form = document.getElementById('edit-event-form');
        if (!form) return;
        
        const formData = new FormData(form);
        const eventId = formData.get('eventId');
        
        // Validate required fields
        if (!formData.get('title').trim()) {
            alert('일정 제목을 입력해주세요.');
            form.querySelector('input[name="title"]').focus();
            return;
        }
        
        // Find the event to update
        const eventIndex = this.events.findIndex(event => event.id === eventId);
        if (eventIndex === -1) {
            console.error('Event not found for update:', eventId);
            return;
        }
        
        // Update event data
        const updatedEvent = {
            ...this.events[eventIndex],
            title: formData.get('title'),
            description: formData.get('description'),
            date: formData.get('date'),
            startTime: formData.get('startTime'),
            endTime: formData.get('endTime')
        };
        
        try {
            // Try to update on server
            const calendarId = document.querySelector('.calendar-workspace')?.dataset.calendarId || 'default';
            const response = await fetch(`/api/calendars/${calendarId}/events/${eventId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(updatedEvent)
            });
            
            if (response.ok) {
                // console.log('✅ Event updated on server');
            } else {
                console.warn('⚠️ Server update failed, updating locally only');
            }
        } catch (error) {
            console.error('❌ Error updating event on server:', error);
        }
        
        // Update local event data
        this.events[eventIndex] = updatedEvent;
        
        // Save to localStorage backup
        this.saveToLocalStorage();
        
        // Re-render calendar
        this.clearRenderedEvents();
        this.events.filter(event => event && event.id && event.date).forEach(event => this.renderEvent(event));
        
        // Update event list
        this.updateEventList();
        
        // Close popup
        if (this.currentPopup) {
            this.currentPopup.remove();
            this.currentPopup = null;
        }
        
        // Show success notification
        if (window.showNotification) {
            showNotification(`일정 "${updatedEvent.title}"이(가) 수정되었습니다`, 'success');
        }
    }

    async deleteEventById(eventId) {
        // Convert eventId to string for consistent comparison
        const eventIdStr = String(eventId);
        console.log('🗑️ Attempting to delete event with ID:', eventIdStr);
        
        // Clean events array of null values first
        this.events = this.events.filter(e => e && e.id);
        
        // FIX: 숫자 ID면 클릭된 요소에서 실제 이벤트 찾기
        if (/^\d+$/.test(eventIdStr)) {
            console.log('🚨 NUMERIC ID: Finding clicked event to delete');
            
            // 클릭된 삭제 버튼 찾기
            const clickedButton = document.querySelector(`[onclick*="${eventIdStr}"]`);
            if (clickedButton) {
                // 삭제 버튼이 속한 이벤트 요소 찾기
                const eventElement = clickedButton.closest('.event, .calendar-event, [class*="event"]');
                if (eventElement) {
                    // 이벤트 요소에서 제목 추출
                    const titleElement = eventElement.querySelector('.event-title, [class*="title"], h3, h4, span');
                    const eventTitle = titleElement ? titleElement.textContent.trim() : 'Unknown Event';
                    
                    // 제목으로 실제 이벤트 찾기
                    const actualEvent = this.events.find(e => e.title === eventTitle);
                    if (actualEvent) {
                        console.log('✅ Found actual event to delete:', actualEvent.title);
                        
                        // 휴지통 확인 대화상자 표시
                        if (confirm(`"${actualEvent.title}" 일정을 휴지통으로 이동하시겠습니까?`)) {
                            return this.deleteEvent(actualEvent);
                        } else {
                            console.log('❌ Deletion cancelled by user');
                            return false;
                        }
                    }
                    
                    // 이벤트를 못 찾으면 제목으로 확인 후 DOM에서만 제거
                    console.log('⚠️ Event not found in array, removing from DOM only');
                    if (confirm(`"${eventTitle}" 일정을 삭제하시겠습니까?`)) {
                        eventElement.remove();
                        console.log('🗑️ Removed from DOM');
                        return true;
                    }
                    return false;
                }
            }
            
            console.log('⚠️ Could not find clicked event');
            return false;
        }
        
        const eventData = this.events.find(event => String(event.id) === eventIdStr);
        if (!eventData) {
            console.error('Event not found for deletion:', eventId, 'Available events:', this.events.slice(0, 5).map(e => ({id: e.id, notion_id: e.notion_id, title: e.title})));
            
            // Try all possible ID fields
            const altEventData = this.events.find(event => 
                String(event.id) === eventIdStr ||
                String(event.notion_id) === eventIdStr ||
                String(event.uuid) === eventIdStr ||
                String(event.event_id) === eventIdStr ||
                event.id == eventId || 
                event.notion_id == eventId ||
                event.uuid == eventId ||
                event.event_id == eventId
            );
            
            if (altEventData) {
                console.log('Found event with alternative search:', {
                    id: altEventData.id,
                    notion_id: altEventData.notion_id,
                    uuid: altEventData.uuid,
                    event_id: altEventData.event_id,
                    title: altEventData.title
                });
                return this.deleteEvent(altEventData);
            }
            
            // 마지막 시도: 모든 필드에서 숫자 ID 찾기
            const finalAttemptEvent = this.events.find(event => {
                const fields = [
                    event.id, event.notion_id, event.uuid, event.event_id, 
                    event.backendId, event.frontendId, event.tempId,
                    event.timestamp, event.created_at
                ];
                
                return fields.some(field => 
                    field && (String(field) === eventIdStr || String(field).includes(eventIdStr))
                );
            });
            
            if (finalAttemptEvent) {
                console.log('✅ Found event with final attempt:', finalAttemptEvent.title);
                return this.deleteEvent(finalAttemptEvent);
            }
            
            console.error('Event not found after all attempts. Searched ID:', eventIdStr);
            console.error('Sample event structure:', this.events[0]);
            
            // DOM에서 강제로 제거
            const eventElements = document.querySelectorAll(`[data-event-id="${eventId}"], [data-id="${eventId}"]`);
            eventElements.forEach(el => {
                el.remove();
                console.log('🗑️ Force removed from DOM');
            });
            return;
        }
        
        // Call the main delete function (휴지통 확인 포함)
        console.log('✅ Found event to delete:', eventData.title);
        return this.deleteEvent(eventData);
    }

    updateMainContentDimensions() {
        // Find main content area and calculate dimensions
        const sidebar = document.querySelector('.sidebar');
        const mainContent = document.querySelector('.main-content, .center-calendar-area, .calendar-workspace');
        
        let sidebarWidth = 250; // Default width
        let mainContentWidth = window.innerWidth - 250; // Default main content width
        
        if (sidebar) {
            // Check if sidebar is collapsed/hidden
            const sidebarStyles = window.getComputedStyle(sidebar);
            const isHidden = sidebarStyles.display === 'none' || 
                            sidebarStyles.visibility === 'hidden' ||
                            sidebar.classList.contains('collapsed') ||
                            sidebar.classList.contains('hidden');
            
            if (isHidden) {
                sidebarWidth = 0;
                mainContentWidth = window.innerWidth;
            } else {
                // Get actual width
                const actualWidth = sidebar.offsetWidth;
                if (actualWidth > 0) {
                    sidebarWidth = actualWidth;
                    mainContentWidth = window.innerWidth - actualWidth;
                }
            }
        } else if (mainContent) {
            // Calculate from main content area if sidebar not found
            const mainRect = mainContent.getBoundingClientRect();
            sidebarWidth = mainRect.left;
            mainContentWidth = mainRect.width;
        } else {
            // Fallback: assume full width if no main content found
            sidebarWidth = 0;
            mainContentWidth = window.innerWidth;
        }
        
        // Update CSS custom properties
        document.documentElement.style.setProperty('--sidebar-width', `${sidebarWidth}px`);
        document.documentElement.style.setProperty('--main-content-width', `${mainContentWidth}px`);
        
        // console.log('📏 Updated dimensions - Sidebar:', sidebarWidth, 'Main content:', mainContentWidth);
    }

    async loadExistingEvents() {
        // console.log('📥 Loading existing events...');
        
        // Always load from localStorage first for immediate functionality
        this.loadBackupEvents();
        
        // Then try to sync with backend
        try {
            const calendarElement = document.querySelector('.calendar-workspace');
            if (!calendarElement?.dataset.calendarId) {
                // console.log('⚠️ No calendar workspace or ID found, using localStorage only');
                return;
            }
            
            const calendarId = calendarElement.dataset.calendarId;
            // console.log('🔍 Fetching events for calendar:', calendarId);
            
            const response = await fetch(`/api/calendars/${calendarId}/events`);
            
            if (response.ok) {
                const data = await response.json();
                
                // Handle both array and object responses (same logic as calendar-detail.js)
                let events = [];
                if (Array.isArray(data)) {
                    events = data;
                } else if (typeof data === 'object' && data !== null) {
                    events = data.events || data.data || data.items || [];
                } else {
                    events = [];
                }
                
                // Clear existing events
                this.events = [];
                
                if (events && events.length > 0) {
                    // Distribute events across different time slots if they lack time info
                    let hourOffset = 0;
                    let minuteOffset = 0;
                    
                    events.forEach((event, index) => {
                        const frontendEvent = this.convertBackendEventToFrontend(event);
                        
                        // If the event has no specific time (default 09:00-10:00), distribute it
                        if (!event.start_datetime || (!event.start_time && !event.startTime)) {
                            // Distribute events from 8 AM to 6 PM in 30-minute intervals
                            const baseHour = 8;
                            const totalSlots = 20; // 10 hours * 2 slots per hour
                            const slotIndex = index % totalSlots;
                            
                            hourOffset = Math.floor(slotIndex / 2);
                            minuteOffset = (slotIndex % 2) * 30;
                            
                            const startHour = baseHour + hourOffset;
                            const startMinute = minuteOffset;
                            const endHour = startMinute === 30 ? startHour + 1 : startHour;
                            const endMinute = startMinute === 30 ? 0 : 30;
                            
                            frontendEvent.startTime = `${String(startHour).padStart(2, '0')}:${String(startMinute).padStart(2, '0')}`;
                            frontendEvent.endTime = `${String(endHour).padStart(2, '0')}:${String(endMinute).padStart(2, '0')}`;
                        }
                        
                        this.events.push(frontendEvent);
                        this.renderEvent(frontendEvent);
                    });
                } else {
                    // No backend events, try localStorage
                    this.loadBackupEvents();
                }
            } else {
                // console.log(`📝 Backend API returned ${response.status} - using localStorage`);
                this.loadBackupEvents();
            }
            
        } catch (error) {
            // console.log('📝 Backend connection failed - using localStorage:', error.message);
            this.loadBackupEvents();
        }
        
        // TODO: Enable backend loading once API endpoints are implemented
        /*
        try {
            const calendarElement = document.querySelector('.calendar-workspace');
            if (!calendarElement?.dataset.calendarId) {
                // console.log('⚠️ No calendar workspace or ID found, using localStorage only');
                this.loadBackupEvents();
                return;
            }
            
            const calendarId = calendarElement.dataset.calendarId;
            // console.log('🔍 Fetching events for calendar:', calendarId);
            
            const response = await fetch(`/api/calendars/${calendarId}/events`);
            
            if (response.ok) {
                const events = await response.json();
                // console.log('📅 Loaded events from backend:', events);
                
                // Clear existing events and render loaded ones
                this.events = [];
                
                if (events && events.length > 0) {
                    events.forEach(event => {
                        const frontendEvent = this.convertBackendEventToFrontend(event);
                        this.events.push(frontendEvent);
                        this.renderEvent(frontendEvent);
                    });
                    // console.log(`✅ Successfully loaded ${events.length} events from backend`);
                    // Update the event list
                    this.updateEventList();
                } else {
                    // No backend events, try localStorage
                    this.loadBackupEvents();
                }
            } else {
                // console.log(`📝 Backend API not available (${response.status}) - using localStorage`);
                this.loadBackupEvents();
            }
            
        } catch (error) {
            // console.log('📝 Backend connection failed - using localStorage:', error.message);
            this.loadBackupEvents();
        }
        */
    }
    
    loadBackupEvents() {
        // console.log('📱 Loading events from localStorage backup...');
        const backupEvents = this.loadFromLocalStorage();
        
        if (backupEvents.length > 0) {
            // Filter out null/invalid events before processing
            const validEvents = backupEvents.filter(event => event && event.id && event.date);
            
            validEvents.forEach(event => {
                this.events.push(event);
                this.renderEvent(event);
            });
            // console.log(`✅ Loaded ${backupEvents.length} events from localStorage backup`);
            // Update the event list
            this.updateEventList();
        } else {
            // console.log('📝 No backup events found in localStorage');
        }
    }
    
    convertBackendEventToFrontend(backendEvent) {
        // Convert backend event format to match frontend expectations
        let date = backendEvent.date;
        let startTime = backendEvent.startTime || backendEvent.start_time;
        let endTime = backendEvent.endTime || backendEvent.end_time;
        
        // Try to extract date from start_datetime or start_date (API response format)
        if (!date && (backendEvent.start_datetime || backendEvent.start_date)) {
            try {
                const startDateTime = backendEvent.start_datetime || backendEvent.start_date;
                const parsedDate = new Date(startDateTime);
                if (!isNaN(parsedDate.getTime())) {
                    date = parsedDate.toISOString().split('T')[0];
                    // Also extract time if not already set
                    if (!startTime) {
                        startTime = parsedDate.toTimeString().slice(0, 5);
                    }
                }
            } catch (e) {
                console.warn('Failed to parse start_datetime:', backendEvent.start_datetime);
            }
        }
        
        // Try to extract end time from end_datetime
        if (!endTime && backendEvent.end_datetime) {
            try {
                const endDateTime = new Date(backendEvent.end_datetime);
                if (!isNaN(endDateTime.getTime())) {
                    endTime = endDateTime.toTimeString().slice(0, 5);
                }
            } catch (e) {
                console.warn('Failed to parse end_datetime:', backendEvent.end_datetime);
            }
        }
        
        // Final fallbacks
        if (!date) {
            const today = new Date();
            date = today.toISOString().split('T')[0];
        }
        
        if (!startTime || startTime.length < 5) {
            startTime = '09:00';
        }
        if (!endTime || endTime.length < 5) {
            // Default to 1 hour duration
            const startHour = parseInt(startTime.split(':')[0]);
            const startMinute = parseInt(startTime.split(':')[1]);
            const endHour = startMinute >= 30 ? startHour + 1 : startHour;
            const endMinute = startMinute >= 30 ? 0 : 30;
            endTime = `${String(endHour).padStart(2, '0')}:${String(endMinute).padStart(2, '0')}`;
        }
        
        const convertedEvent = {
            id: backendEvent.id || Date.now().toString(),
            backendId: backendEvent.id, // Store the backend ID separately
            title: backendEvent.title || backendEvent.summary || 'Untitled',
            description: backendEvent.description || '',
            date: date,
            startTime: startTime,
            endTime: endTime,
            color: backendEvent.color || '#3b82f6'
        };
        
        // console.log('✅ Converted to frontend event:', convertedEvent);
        return convertedEvent;
    }
    
    saveToLocalStorage(eventData) {
        try {
            const storageKey = 'calendar_events_backup';
            const existing = JSON.parse(localStorage.getItem(storageKey) || '[]');
            existing.push(eventData);
            localStorage.setItem(storageKey, JSON.stringify(existing));
            // console.log('💾 Event saved to localStorage backup');
        } catch (error) {
            console.error('❌ Failed to save to localStorage:', error);
        }
    }
    
    loadFromLocalStorage() {
        try {
            const storageKey = 'calendar_events_backup';
            const events = JSON.parse(localStorage.getItem(storageKey) || '[]');
            // Filter out null/invalid events when loading
            const validEvents = events.filter(event => event && event.id && event.date);
            // console.log('📱 Loaded from localStorage backup:', validEvents.length, 'valid events out of', events.length, 'total');
            return validEvents;
        } catch (error) {
            console.error('❌ Failed to load from localStorage:', error);
            return [];
        }
    }

    updateCurrentTimeIndicator() {
        // Remove existing indicator
        const existingLine = this.container.querySelector('.current-time-line');
        if (existingLine) {
            existingLine.remove();
        }
        
        const now = new Date();
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        
        // Check if current week contains today
        const weekEnd = new Date(this.weekStart);
        weekEnd.setDate(weekEnd.getDate() + 6);
        
        if (today < this.weekStart || today > weekEnd) {
            return; // Not current week
        }
        
        // 30분 간격으로 반올림 (0분 또는 30분)
        const minutes = now.getMinutes();
        const roundedMinutes = minutes >= 30 ? 30 : 0;
        const currentHour = now.getHours() + roundedMinutes / 60;
        const dayIndex = now.getDay();
        
        if (currentHour < this.startHour || currentHour > this.endHour + 1) {
            return; // Outside visible hours
        }
        
        // Create time indicator line
        const timeLine = document.createElement('div');
        timeLine.className = 'current-time-line';
        
        const top = (currentHour - this.startHour) * this.timeSlotHeight + 10; // 40px 아래로 이동
        timeLine.style.top = `${top}px`;
        
        const gridBody = this.container.querySelector('.calendar-grid-body');
        gridBody.appendChild(timeLine);
    }

    closeEventPopup() {
        // Reset popup active flag first to prevent immediate reopening
        window.eventCreationPopupActive = false;
        
        const popup = document.querySelector('.event-creation-popup');
        if (popup) {
            // Start slide-out animation
            popup.classList.remove('show');
            
            // Wait for animation to complete before removing
            setTimeout(() => {
                if (popup && popup.parentNode) {
                    popup.remove();
                }
            }, 300); // Match CSS transition duration
        }
        
        // Also remove backdrop
        const backdrop = document.querySelector('.popup-backdrop');
        if (backdrop) {
            backdrop.remove();
        }
        
        // Clear popup reference
        if (this.currentPopup) {
            this.currentPopup = null;
        }
        
        // Temporarily disable cell clicks to prevent immediate reopening
        this.preventNextCellClick = true;
        setTimeout(() => {
            this.preventNextCellClick = false;
        }, 1000); // Increased delay to 1 second for better prevention
        
        // console.log('🚪 Event popup closed');
    }

    selectEventColor(color) {
        // Remove active class from all color options
        document.querySelectorAll('.color-option').forEach(option => {
            option.classList.remove('active');
        });
        
        // Add active class to selected color
        const selectedOption = document.querySelector(`.color-option[data-color="${color}"]`);
        if (selectedOption) {
            selectedOption.classList.add('active');
        }
        
        // Update the selected color value
        const colorInput = document.getElementById('event-color');
        if (colorInput) {
            colorInput.value = color;
        }
    }

    toggleAllDay() {
        const allDayToggle = document.getElementById('all-day-toggle');
        const timeInputs = document.querySelectorAll('.time-input-group');
        
        if (allDayToggle && allDayToggle.checked) {
            // Hide time inputs when all-day is selected
            timeInputs.forEach(group => {
                group.style.display = 'none';
            });
        } else {
            // Show time inputs when all-day is not selected
            timeInputs.forEach(group => {
                group.style.display = 'flex';
            });
        }
    }

    // Event Search and List Methods
    searchEvents(query) {
        // console.log('🔍 Searching events for:', query);
        const results = this.events.filter(event => 
            event.title.toLowerCase().includes(query.toLowerCase()) ||
            (event.description && event.description.toLowerCase().includes(query.toLowerCase()))
        );
        
        // console.log('🔍 Search results:', results);
        this.displaySearchResults(results, query);
        return results;
    }
    
    displaySearchResults(results, query) {
        // console.log('📊 Displaying search results:', results.length);
        
        // Clear previous highlighting
        this.clearEventHighlighting();
        
        // Highlight matching events in the calendar
        results.forEach(event => {
            this.highlightEvent(event.id);
        });
        
        // Update event list to show search results with count
        this.updateEventList(results, query);
        
        // Show search results feedback
        this.showSearchFeedback(results.length, query);
    }
    
    showSearchFeedback(count, query) {
        // Remove existing feedback
        const existingFeedback = document.querySelector('.search-feedback');
        if (existingFeedback) {
            existingFeedback.remove();
        }
        
        // Create feedback element
        const feedback = document.createElement('div');
        feedback.className = 'search-feedback';
        feedback.innerHTML = `
            <span class="search-results-badge">
                ${count > 0 ? `${count}개 일정 발견` : '검색 결과 없음'}
            </span>
        `;
        
        // Insert feedback after search input
        const searchContainer = document.querySelector('.event-search');
        if (searchContainer) {
            searchContainer.appendChild(feedback);
        }
        
        // Auto-hide feedback after 3 seconds if there are results
        if (count > 0) {
            setTimeout(() => {
                if (feedback && feedback.parentNode) {
                    feedback.style.opacity = '0';
                    setTimeout(() => feedback.remove(), 300);
                }
            }, 3000);
        }
    }
    
    clearEventHighlighting() {
        const highlightedEvents = document.querySelectorAll('.calendar-event.search-highlighted');
        highlightedEvents.forEach(event => {
            event.classList.remove('search-highlighted');
        });
    }
    
    highlightEvent(eventId) {
        const eventElements = document.querySelectorAll(`.calendar-event[data-event-id="${eventId}"]`);
        eventElements.forEach(element => {
            element.classList.add('search-highlighted');
        });
    }
    
    initializeEventList() {
        // console.log('📋 Initializing event list');
        this.updateEventList();
    }
    
    updateEventList(eventsToShow = null, searchQuery = null) {
        const eventList = document.getElementById('event-list');
        if (!eventList) {
            console.warn('Event list container not found');
            return;
        }
        
        const events = eventsToShow || this.events;
        // console.log('📋 Updating event list with', events.length, 'events');
        
        // Clear existing list
        eventList.innerHTML = '';
        
        if (events.length === 0) {
            const emptyMessage = searchQuery ? 
                `<div class="event-list-empty">
                    <div style="margin-bottom: 8px;">🔍</div>
                    <div>"${searchQuery}"에 대한 검색 결과가 없습니다</div>
                    <div style="font-size: 12px; margin-top: 4px; opacity: 0.7;">다른 키워드로 검색해보세요</div>
                </div>` : 
                `<div class="event-list-empty">
                    <div>등록된 일정이 없습니다</div>
                    <div style="font-size: 12px; margin-top: 4px; opacity: 0.7;">새 일정을 추가해보세요</div>
                </div>`;
            
            eventList.innerHTML = emptyMessage;
            return;
        }
        
        // Sort events by date and time
        const sortedEvents = [...events].sort((a, b) => {
            const dateA = new Date(a.date + 'T' + a.startTime);
            const dateB = new Date(b.date + 'T' + b.startTime);
            return dateA - dateB;
        });
        
        sortedEvents.forEach((event, index) => {
            const eventItem = this.createEventListItem(event);
            
            // Add search result styling if this is a search
            if (searchQuery) {
                eventItem.classList.add('search-result-item');
            }
            
            // Stagger animation for better visual effect
            setTimeout(() => {
                eventList.appendChild(eventItem);
            }, index * 50);
        });
    }
    
    createEventListItem(event) {
        const item = document.createElement('div');
        item.className = 'event-list-item';
        item.dataset.eventId = event.id;
        
        // Format date and time with enhanced formatting
        const eventDate = new Date(event.date);
        const today = new Date();
        const tomorrow = new Date(today);
        tomorrow.setDate(today.getDate() + 1);
        
        const dayNames = ['일', '월', '화', '수', '목', '금', '토'];
        const dayName = dayNames[eventDate.getDay()];
        
        let dateDisplay;
        if (eventDate.toDateString() === today.toDateString()) {
            dateDisplay = '오늘';
        } else if (eventDate.toDateString() === tomorrow.toDateString()) {
            dateDisplay = '내일';
        } else {
            dateDisplay = `${eventDate.getMonth() + 1}월 ${eventDate.getDate()}일 (${dayName})`;
        }
        
        // Format time range with improved display
        const startTime = event.startTime;
        const endTime = event.endTime;
        const timeRange = `${startTime} - ${endTime}`;
        
        item.innerHTML = `
            <div class="event-list-item-title">${event.title}</div>
            <div class="event-list-item-time">${dateDisplay} · ${timeRange}</div>
        `;
        
        // Add click handler to highlight event
        item.addEventListener('click', () => {
            this.highlightEventInCalendar(event.id);
        });
        
        // Add right-click context menu for list items
        item.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            this.showEventContextMenu(e, event);
        });
        
        // Add entry animation
        item.classList.add('event-list-item-enter');
        
        return item;
    }
    
    highlightEventInCalendar(eventId) {
        // Clear previous highlighting
        document.querySelectorAll('.event-list-item.highlighted').forEach(item => {
            item.classList.remove('highlighted');
        });
        
        // Highlight clicked item
        const clickedItem = document.querySelector(`[data-event-id="${eventId}"]`);
        if (clickedItem) {
            clickedItem.classList.add('highlighted');
        }
        
        // Find and highlight the event in calendar
        this.clearEventHighlighting();
        this.highlightEvent(eventId);
        
        // Scroll to the event if needed
        const eventElement = document.querySelector(`.calendar-event[data-event-id="${eventId}"]`);
        if (eventElement) {
            eventElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }

    // Reposition existing popup to new clicked cell location
    repositionPopup(popup, clickedCell) {
        if (!popup || !clickedCell) {
            return;
        }

        const cellRect = clickedCell.getBoundingClientRect();
        let left = cellRect.right + 10;
        let top = cellRect.top;
        
        // Fixed popup positioning - always use clicked cell position
        const popupWidth = 360;
        const popupHeight = 400;
        
        // Ensure popup doesn't go off-screen
        if (left + popupWidth > window.innerWidth) {
            left = cellRect.left - popupWidth - 10; // Position to the left of cell
        }
        
        if (top + popupHeight > window.innerHeight) {
            top = window.innerHeight - popupHeight - 20; // Position above
        }
        
        // Update popup position with smooth transition
        popup.style.transition = 'left 0.3s ease, top 0.3s ease';
        popup.style.left = `${left}px`;
        popup.style.top = `${top}px`;
        
        // Remove transition after animation completes
        setTimeout(() => {
            popup.style.transition = '';
        }, 300);
    }

    // Update time values in existing popup
    updatePopupTimeValues(popup, startDate, endDate, day) {
        if (!popup) {
            return;
        }

        const startTimeStr = startDate.toLocaleTimeString('ko-KR', { 
            hour: '2-digit', 
            minute: '2-digit',
            hour12: false
        });
        const endTimeStr = endDate.toLocaleTimeString('ko-KR', { 
            hour: '2-digit', 
            minute: '2-digit',
            hour12: false 
        });
        const dateStr = startDate.toLocaleDateString('ko-KR', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            weekday: 'long'
        });

        // Update popup subtitle with new date
        const popupSubtitle = popup.querySelector('.popup-subtitle');
        if (popupSubtitle) {
            popupSubtitle.textContent = dateStr;
        }

        // Update start time button
        const startTimeButton = popup.querySelector('.time-select-btn[data-type="start"]');
        if (startTimeButton) {
            startTimeButton.textContent = startTimeStr;
        }

        // Update end time button  
        const endTimeButton = popup.querySelector('.time-select-btn[data-type="end"]');
        if (endTimeButton) {
            endTimeButton.textContent = endTimeStr;
        }

        // Store new date/time values
        popup.setAttribute('data-start-date', startDate.toISOString());
        popup.setAttribute('data-end-date', endDate.toISOString());
        popup.setAttribute('data-day', day);
    }
}

// ============ SIDEBAR EVENT FORM FUNCTIONS ============

function openEventForm(date = null, eventData = null) {
    const overlayForm = document.getElementById('calendar-overlay-form');
    const formTitle = document.getElementById('overlay-form-title');
    const form = document.getElementById('overlay-event-form');
    
    if (!overlayForm) return;
    
    // 이미 팝업이 열려있으면 무시
    if (overlayForm.style.display === 'flex') {
        console.log('🚫 Popup already open, ignoring');
        return;
    }
    
    // Show the overlay form
    overlayForm.style.display = 'flex';
    
    // Reset form
    form.reset();
    
    // Set form mode (create or edit)
    if (eventData) {
        // Edit mode
        formTitle.textContent = '일정 수정';
        document.getElementById('overlay-event-title').value = eventData.title || '';
        document.getElementById('overlay-event-date').value = eventData.date || '';
        document.getElementById('overlay-start-time').value = eventData.startTime || '09:00';
        document.getElementById('overlay-end-time').value = eventData.endTime || '10:00';
        document.getElementById('overlay-event-description').value = eventData.description || '';
        document.getElementById('overlay-youtube-url').value = eventData.youtubeUrl || '';
        
        // 편집 모드에서는 기존 색상 유지 (색상 선택기 제거됨)
        
        // Store event ID for editing
        form.dataset.eventId = eventData.id;
    } else {
        // Create mode
        formTitle.textContent = '새 일정';
        if (date) {
            document.getElementById('overlay-event-date').value = date;
        }
        delete form.dataset.eventId;
    }
    
    // Focus on title input
    setTimeout(() => {
        document.getElementById('overlay-event-title').focus();
    }, 300);
}

function closeEventForm() {
    const overlayForm = document.getElementById('calendar-overlay-form');
    const overlayContent = overlayForm?.querySelector('.overlay-form-content');
    
    // 모든 팝업 생성 관련 상태 완전 초기화
    if (window.googleCalendarGrid) {
        // 선택 상태 완전 초기화
        window.googleCalendarGrid.isSelecting = false;
        window.googleCalendarGrid.selectedCells = new Set();
        window.googleCalendarGrid.selectionStart = null;
        window.googleCalendarGrid.selectionEnd = null;
        
        // 드래그 상태 초기화
        window.googleCalendarGrid.isDragging = false;
        window.googleCalendarGrid.isResizing = false;
        window.googleCalendarGrid.dragStartY = 0;
        window.googleCalendarGrid.dragStartTime = null;
        window.googleCalendarGrid.originalEventData = null;
        
        // 선택 표시 제거
        window.googleCalendarGrid.clearSelection();
        
        // 모든 이벤트 리스너 일시 비활성화 (300ms)
        const gridBody = window.googleCalendarGrid.container?.querySelector('.calendar-grid-body');
        if (gridBody) {
            gridBody.style.pointerEvents = 'none';
            setTimeout(() => {
                gridBody.style.pointerEvents = '';
            }, 300);
        }
    }
    
    // 전역 상태 플래그 초기화
    window.eventCreationPopupActive = false;
    window.isCreatingEvent = false;
    
    // 모든 관련 타임아웃 정리
    if (window.popupTimeoutId) {
        clearTimeout(window.popupTimeoutId);
        window.popupTimeoutId = null;
    }
    
    if (overlayForm && overlayContent) {
        // Add closing animation
        overlayContent.style.animation = 'slideDownToBottom 0.3s cubic-bezier(0.4, 0, 1, 1)';
        overlayForm.style.animation = 'fadeOut 0.3s ease';
        
        // Hide after animation completes
        setTimeout(() => {
            overlayForm.style.display = 'none';
            // Reset animations for next time
            overlayContent.style.animation = '';
            overlayForm.style.animation = '';
        }, 300);
    }
}

// Add keyboard shortcut support for the overlay form
document.addEventListener('keydown', function(event) {
    const overlayForm = document.getElementById('calendar-overlay-form');
    if (overlayForm && overlayForm.style.display !== 'none') {
        // Close form on Escape key
        if (event.key === 'Escape') {
            event.preventDefault();
            closeEventForm();
        }
        // Save form on Ctrl+Enter or Cmd+Enter
        else if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
            event.preventDefault();
            const saveButton = document.querySelector('#overlay-event-form button[type="submit"]');
            if (saveButton) {
                saveButton.click();
            }
        }
    }
});

function closeOverlayEventForm() {
    closeEventForm();
}

// Handle backdrop click to close overlay
function handleOverlayClick(event) {
    // Only close if clicking the backdrop, not the form content
    if (event.target === event.currentTarget) {
        closeEventForm();
    }
}

// setupOverlayColorPicker 함수 제거됨 (색상 선택기 제거로 인해 불필요)

function saveOverlayEvent(event) {
    event.preventDefault();
    
    const form = event.target;
    const eventId = form.dataset.eventId;
    
    // Get form data
    const title = document.getElementById('overlay-event-title').value.trim();
    const date = document.getElementById('overlay-event-date').value;
    const startTime = document.getElementById('overlay-start-time').value;
    const endTime = document.getElementById('overlay-end-time').value;
    const description = document.getElementById('overlay-event-description').value.trim();
    const youtubeUrl = document.getElementById('overlay-youtube-url').value.trim();
    
    // 색상 설정 (편집 모드에서는 기존 색상 유지, 새 이벤트는 랜덤)
    let color;
    if (eventId) {
        // 편집 모드: 기존 색상 유지
        const existingEvent = calendarInstance.events.find(e => e.id === eventId);
        color = existingEvent ? existingEvent.color : '#3b82f6';
    } else {
        // 새 이벤트: 랜덤 색상 생성
        const colors = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4', '#f97316', '#84cc16', '#ec4899', '#6366f1'];
        color = colors[Math.floor(Math.random() * colors.length)];
    }
    
    // Validation
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
    
    // Create/update event data
    const eventData = {
        id: eventId || Date.now().toString(),
        title,
        date,
        startTime,
        endTime,
        description,
        color,
        youtubeUrl: youtubeUrl
    };
    
    // Get calendar instance
    const calendarInstance = window.googleCalendarGrid;
    if (!calendarInstance) {
        console.error('Calendar instance not found');
        return;
    }
    
    if (eventId) {
        // Edit existing event
        const index = calendarInstance.events.findIndex(e => e.id === eventId);
        if (index !== -1) {
            calendarInstance.events[index] = eventData;
            
            // Remove old event from DOM
            const oldElements = document.querySelectorAll(`[data-event-id="${eventId}"]`);
            oldElements.forEach(el => el.remove());
        }
    } else {
        // Add new event
        calendarInstance.events.push(eventData);
    }
    
    // Update localStorage
    const storageKey = 'calendar_events_backup';
    localStorage.setItem(storageKey, JSON.stringify(calendarInstance.events));
    
    // Render the event
    calendarInstance.renderEvent(eventData);
    
    // Update event list
    calendarInstance.updateEventList();
    
    // Close form
    closeEventForm();
    
    // Show success message
    if (window.showNotification) {
        showNotification(eventId ? '일정이 수정되었습니다' : '일정이 생성되었습니다', 'success');
    }
    
    // console.log('📅 Event saved:', eventData);
}

// Override the original click handlers to use overlay form
window.openEventForm = openEventForm;
window.closeEventForm = closeEventForm;
window.closeOverlayEventForm = closeOverlayEventForm;
window.saveOverlayEvent = saveOverlayEvent;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('google-calendar-container');
    if (container) {
        window.googleCalendarGrid = new GoogleCalendarGrid(container);
    }
});

// Global trash functions
window.showTrashPopup = function() {
    if (window.googleCalendarGrid) {
        window.googleCalendarGrid.showTrashPopup();
    }
};

window.hideTrashPopup = function() {
    if (window.googleCalendarGrid) {
        window.googleCalendarGrid.hideTrashPopup();
    }
};

window.emptyTrash = function() {
    if (window.googleCalendarGrid) {
        window.googleCalendarGrid.emptyTrash();
    }
};

// 🚨 NUCLEAR DOM REMOVAL - 강력한 즉시 제거 함수
window.forceRemoveEventFromDOM = function(eventData) {
    console.log('🚨 NUCLEAR DOM REMOVAL for:', eventData.title, 'ID:', eventData.id);
    
    let removedCount = 0;
    
    // 1단계: ID 기반 모든 요소 즉시 제거
    const idSelectors = [
        `[data-event-id="${eventData.id}"]`,
        `[data-id="${eventData.id}"]`, 
        `[id*="${eventData.id}"]`,
        `[onclick*="${eventData.id}"]`
    ];
    
    idSelectors.forEach(selector => {
        document.querySelectorAll(selector).forEach(el => {
            el.style.display = 'none';
            el.remove();
            removedCount++;
            console.log(`💀 ID removal: ${selector}`);
        });
    });
    
    // 2단계: 제목 기반 브루트 포스 검색
    const allElements = document.querySelectorAll('*');
    allElements.forEach(el => {
        const text = el.textContent || '';
        if (text.includes(eventData.title) && 
            (el.className.includes('event') || 
             el.style.position === 'absolute' ||
             el.querySelector('[onclick*="delete"]'))) {
            el.style.display = 'none';
            el.remove();
            removedCount++;
            console.log(`💀 Title-based removal: "${eventData.title}"`);
        }
    });
    
    console.log(`✅ NUCLEAR REMOVAL: ${removedCount} elements removed`);
    return removedCount;
};
