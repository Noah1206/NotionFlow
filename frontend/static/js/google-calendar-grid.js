// Google Calendar Style Grid Implementation

class GoogleCalendarGrid {
    constructor(container) {
        this.container = container;
        this.currentDate = new Date(); // This should be current date
        // Console log removed
        this.weekStart = this.getWeekStart(this.currentDate);
        this.events = [];
        this.trashedEvents = this.loadTrashedEvents();

        // 영구 삭제 목록 정리
        this.cleanupPermanentlyDeleted();

        // 🔍 DEBUGGING: 컨테이너 크기 확인
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
            // Console error removed
            return [];
        }
    }

    isEventInTrash(eventId) {
        // 영구 삭제된 이벤트는 항상 숨김
        if (this.isPermanentlyDeleted(eventId)) {
            return true;
        }

        // Check if event is in trash (both new and old trash systems)
        const trashedEvents = this.loadTrashedEvents();
        const oldTrashedEvents = JSON.parse(localStorage.getItem('trashedEvents') || '[]');

        return trashedEvents.some(event => String(event.id) === String(eventId)) ||
               oldTrashedEvents.some(event => String(event.id) === String(eventId));
    }
    
    saveTrashedEvents() {
        const storageKey = 'calendar_trashed_events';
        try {
            localStorage.setItem(storageKey, JSON.stringify(this.trashedEvents));
        } catch (error) {
            // Console error removed
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
        
        // Console log removed
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
            if (emptyMessage) emptyMessage.style.display = 'block';
            if (emptyButton) emptyButton.style.display = 'none';
            return;
        }
        
        if (emptyMessage) emptyMessage.style.display = 'none';
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
            // Console log removed
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
        
        // Console log removed
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
            const eventsToDeleteCount = this.trashedEvents.length;

            // 1. 즉시 UI에서 제거 (사용자 경험 개선)
            const eventsToDeleteOnServer = this.trashedEvents.filter(event =>
                event.backendId || (event.id && !/^\d{13,}$/.test(String(event.id)))
            );

            // 영구 삭제 목록에 추가 (UI에서 숨김)
            this.trashedEvents.forEach(event => {
                this.addToPermanentlyDeleted(event.id);
            });

            // Clear all trashed events from memory and localStorage
            this.trashedEvents = [];
            this.saveTrashedEvents();

            // Update trash popup immediately
            this.populateTrashPopup();

            // Show success notification immediately
            if (window.showNotification) {
                showNotification('휴지통이 비워졌습니다', 'success');
            }

            // Console log removed

            // 2. 비동기로 서버에서 삭제 (백그라운드 처리)
            this.deleteEventsFromServerAsync(eventsToDeleteOnServer, calendarId);

        } catch (error) {
            // Console error removed
            if (window.showNotification) {
                showNotification('휴지통 비우기에 실패했습니다', 'error');
            }
        }
    }

    // 비동기 서버 삭제 처리 메서드
    async deleteEventsFromServerAsync(eventsToDelete, calendarId) {
        if (eventsToDelete.length === 0) {
            // Console log removed
            return;
        }

        // Console log removed

        let deletedCount = 0;
        let failedCount = 0;
        const deletePromises = [];

        for (const eventData of eventsToDelete) {
            // Use backendId if available, otherwise use id
            const dbEventId = eventData.backendId || eventData.id;

            const deletePromise = fetch(`/api/calendars/${calendarId}/events/${dbEventId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => {
                if (response.ok) {
                    deletedCount++;
                    // Console log removed
                } else if (response.status === 404) {
                    deletedCount++;
                    // Console log removed
                } else {
                    failedCount++;
                    // Console warn removed
                }
            })
            .catch(error => {
                failedCount++;
                // Console error removed
            });

            deletePromises.push(deletePromise);
        }

        // 모든 삭제 요청이 완료될 때까지 대기
        try {
            await Promise.allSettled(deletePromises);
            // Console log removed

            // 실패한 항목이 있으면 콘솔에만 로그 (사용자 경험을 방해하지 않음)
            if (failedCount > 0) {
                // Console warn removed
            }
        } catch (error) {
            // Console error removed
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
        
        // Add debounced resize listener for dynamic sizing
        window.addEventListener('resize', () => {
            if (this.resizeTimeout) {
                clearTimeout(this.resizeTimeout);
            }
            this.resizeTimeout = setTimeout(() => {
                this.handleResize();
            }, 150); // 150ms debounce
        });

        // Initial resize to set proper dimensions
        setTimeout(() => {
            this.handleResize();
        }, 100);
        
        // Update time indicator every 30 minutes
        setInterval(() => {
            this.updateCurrentTimeIndicator();
        }, 30 * 60 * 1000); // 30분 = 30 * 60 * 1000 밀리초
        
        // // Console log removed
    }
    
    getWeekStart(date) {
        const d = new Date(date.getTime()); // Create a copy to avoid mutating original
        const day = d.getDay(); // 0 = Sunday, 1 = Monday, ..., 6 = Saturday
        
        // Calculate days to subtract to get to Sunday
        const daysToSunday = day;
        const weekStart = new Date(d.getTime() - (daysToSunday * 24 * 60 * 60 * 1000));
        weekStart.setHours(12, 0, 0, 0); // Set to noon to avoid timezone issues
        
        // Console log removed
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
        
        // Re-render all events (excluding trashed events)
        this.events.forEach(event => {
            // Skip trashed events
            if (!this.isEventInTrash(event.id)) {
                this.renderEvent(event);
            }
        });
    }

    renderEvents() {
        // Alias for rerenderAllEvents
        this.rerenderAllEvents();
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
            // // Console log removed
        } else {
            // Console warn removed
        }
    }
    
    renderHeader() {
        const days = ['일', '월', '화', '수', '목', '금', '토'];
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        
        let headerHTML = `
            <div class="calendar-header">
                <div class="time-header">GMT+9</div>
        `;
        
        for (let i = 0; i < 7; i++) {
            const date = new Date(this.weekStart);
            date.setDate(date.getDate() + i);
            
            const isToday = date.getTime() === today.getTime();
            const isWeekend = i === 0 || i === 6;
            
            headerHTML += `
                <div class="day-header ${isToday ? 'today' : ''}" data-day="${i}">
                    <div class="day-name">${days[i]}</div>
                    <div class="day-date">${date.getDate()}</div>
                </div>
            `;
        }
        
        headerHTML += `</div>`;
        return headerHTML;
    }
    
    renderGrid() {
        let gridHTML = `
            <div class="calendar-grid-body">
                <div class="time-column">
                    ${this.renderTimeSlots()}
                </div>
        `;
        
        // Render day columns with proper grid positioning - each takes full available space
        for (let day = 0; day < 7; day++) {
            const isWeekend = day === 0 || day === 6;
            gridHTML += `
                <div class="day-column ${isWeekend ? 'weekend' : ''}" data-day="${day}">
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
        
        // Drag and drop events for event time editing (calendar events only)
        gridBody.addEventListener('dragover', (e) => {
            // 🛡️ 파일 드래그 차단
            if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                e.dataTransfer.dropEffect = 'none';
                return;
            }

            // 🛡️ 유효한 캘린더 이벤트만 허용
            const types = e.dataTransfer.types;
            if (!types.includes('text/plain')) {
                e.dataTransfer.dropEffect = 'none';
                return;
            }

            e.preventDefault(); // Allow valid calendar event drops only
            e.dataTransfer.dropEffect = 'move';
        });
        
        gridBody.addEventListener('drop', (e) => this.handleEventDrop(e));
        
        // Global mouse up to handle selections outside grid
        document.addEventListener('mouseup', () => {
            if (this.isSelecting) {
                this.finishSelection();
            }
        });

        // 🛡️ 전역 파일 드롭 방지 (캘린더 전체)
        document.addEventListener('dragover', (e) => {
            if (e.target.closest('.calendar-grid-container')) {
                if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                    e.preventDefault();
                    e.dataTransfer.dropEffect = 'none';
                }
            }
        });

        document.addEventListener('drop', (e) => {
            if (e.target.closest('.calendar-grid-container')) {
                if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                    e.preventDefault();
                    // Console log removed
                    if (window.showNotification) {
                        showNotification('캘린더 영역에는 파일을 드롭할 수 없습니다', 'warning');
                    }
                }
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
            e.preventDefault();
            e.stopPropagation();
            return;
        }
        
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
        
        // // Console log removed
        
        // Ensure weekStart is properly initialized
        if (!this.weekStart || !(this.weekStart instanceof Date)) {
            this.weekStart = this.getWeekStart(new Date());
            // // Console log removed
        }
        
        // // Console log removed
        
        // Calculate dates using milliseconds to avoid timezone issues
        const millisecondsPerDay = 24 * 60 * 60 * 1000;
        const startDate = new Date(this.weekStart.getTime() + (startDay * millisecondsPerDay));
        startDate.setHours(startHour, 0, 0, 0);
        
        const endDate = new Date(this.weekStart.getTime() + (endDay * millisecondsPerDay));
        endDate.setHours(endHour + 1, 0, 0, 0); // +1 for end time to include the full hour
        
        // // Console log removed
        // // Console log removed
        // // Console log removed
        
        // Check if this is a multi-day event
        const isMultiDay = startDay !== endDay;
        
        if (isMultiDay) {
            // Multi-day event: create time-based events for each day
            // // Console log removed
            
            const startDateStr = this.formatDateForInput(startDate);
            const endDateStr = this.formatDateForInput(endDate);
            const startTimeStr = startDate.toTimeString().slice(0, 5); // HH:MM format
            const endTimeStr = endDate.toTimeString().slice(0, 5); // HH:MM format
            
            // // Console log removed
            // // Console log removed
            
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
            // // Console log removed
            
            const dateStr = this.formatDateForInput(startDate);
            const startTimeStr = startDate.toTimeString().slice(0, 5); // HH:MM format
            const endTimeStr = endDate.toTimeString().slice(0, 5); // HH:MM format
            
            // // Console log removed
            
            // Use the existing overlay form with clicked cell information
            if (typeof showOverlayEventForm !== 'undefined') {
                // 간단한 팝업 차단 체크
                if (window.POPUP_BLOCKED) {
                    // Console log removed
                    return;
                }
                
                let cellElement = clickedCell;
                if (!cellElement) {
                    cellElement = document.querySelector(`.time-cell[data-day="${startDay}"][data-hour="${startHour}"]`);
                }
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
            
            // 타임스탬프 기반 ID는 클라이언트 전용이므로 서버 호출 안 함
            const isClientOnlyEvent = /^\d{13,}$/.test(String(eventData.id));
            
            if (!isClientOnlyEvent) {
                // 서버에 삭제 요청 보내기 (실제 서버 이벤트인 경우만)
                try {
                    const calendarId = window.location.pathname.split('/').pop();
                    const response = await fetch(`/api/calendar/${calendarId}/events/${eventData.id}`, {
                        method: 'DELETE',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    });
                    
                    if (response.ok || response.status === 404) {
                        if (response.status === 404) {
                            // Console log removed
                        } else {
                            // Console log removed
                        }
                    } else {
                        // Console error removed
                        // 서버 삭제 실패해도 클라이언트에서는 계속 진행
                    }
                } catch (error) {
                    // Console error removed
                    // 네트워크 오류가 있어도 클라이언트에서는 계속 진행
                }
            } else {
                // Console log removed
            }
            
            // Remove from events array
            this.events = this.events.filter(e => e.id !== eventData.id);
            
            // Update localStorage with current events
            const storageKey = 'calendar_events_backup';
            localStorage.setItem(storageKey, JSON.stringify(this.events));
            
            // Remove from DOM immediately - comprehensive search
            // Console log removed
            
            // 🎯 정확한 DOM 제거 - renderEvent에서 생성된 구조 기반
            // Console log removed
            let removedCount = 0;
            
            // 1. data-event-id 속성으로 직접 제거 (가장 정확함)
            const eventElements = document.querySelectorAll(`[data-event-id="${eventData.id}"]`);
            eventElements.forEach(element => {
                // Console log removed
                element.remove();
                removedCount++;
            });
            
            // 2. calendar-event 클래스이면서 제목이 일치하는 요소
            const calendarEvents = document.querySelectorAll('.calendar-event');
            calendarEvents.forEach(element => {
                if (element.textContent && element.textContent.includes(eventData.title)) {
                    // Console log removed
                    element.remove();
                    removedCount++;
                }
            });
            
            // 3. 삭제 버튼의 onclick에 해당 ID가 포함된 요소들
            const deleteButtons = document.querySelectorAll(`[onclick*="deleteEventById('${eventData.id}')"]`);
            deleteButtons.forEach(button => {
                // 삭제 버튼이 속한 calendar-event 요소 찾기
                const eventContainer = button.closest('.calendar-event');
                if (eventContainer) {
                    // Console log removed
                    eventContainer.remove();
                    removedCount++;
                }
            });
            
            // Console log removed
            
            // 🚨 IMMEDIATE FORCE REMOVAL - 즉시 강제 제거
            // Console log removed
            
            // 모든 .calendar-event 요소에서 해당 제목이 포함된 것들 제거
            let immediateRemovalCount = 0;
            document.querySelectorAll('.calendar-event').forEach(element => {
                if (element.textContent && element.textContent.includes(eventData.title)) {
                    element.style.display = 'none'; // 즉시 숨기기
                    element.remove(); // 그리고 제거
                    immediateRemovalCount++;
                    // Console log removed
                }
            });
            
            // 추가적으로 data-event-id로도 제거
            document.querySelectorAll(`[data-event-id="${eventData.id}"]`).forEach(element => {
                element.style.display = 'none';
                element.remove();
                immediateRemovalCount++;
                // Console log removed
            });
            
            // Console log removed
            
            // Update event list and refresh display
            this.updateEventList();
            
            // 🎯 선택적 이벤트 업데이트 (전체 새로고침 대신 최소한의 업데이트)
            setTimeout(() => {
                // Console log removed

                // 1. 삭제된 이벤트만 DOM에서 제거 (다른 이벤트는 그대로 유지)
                document.querySelectorAll(`[data-event-id="${eventData.id}"]`).forEach(element => {
                    element.remove();
                    // Console log removed
                });

                // 2. 이벤트 목록만 업데이트
                this.updateEventList();

                // Console log removed
            }, 50);
            
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
                // // Console log removed
            }
        } catch (error) {
            // Console error removed
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
            // // Console log removed
            
            // Update event list when saving
            this.updateEventList();
        } catch (error) {
            // Console error removed
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
        if (!eventListContainer) {
            // Console warn removed
            // Retry after DOM is ready
            setTimeout(() => {
                this.updateEventList();
            }, 100);
            return;
        }
        
        // Ensure events array is valid
        if (!this.events || !Array.isArray(this.events)) {
            this.events = [];
        }
        
        // Sort events by date and time, excluding trashed events
        const sortedEvents = [...this.events].filter(event => {
            if (!event || !event.id) return false;
            // Filter out trashed events from sidebar display
            if (this.isEventInTrash(event.id)) {
                return false;
            }
            return true;
        }).sort((a, b) => {
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
            ? '선택한 일정을 휴지통으로 이동하시겠습니까?' 
            : `선택한 ${eventIds.length}개의 일정을 휴지통으로 이동하시겠습니까?`;
            
        if (confirm(confirmMessage)) {
            let movedCount = 0;
            
            // Move each event to trash
            for (const eventId of eventIds) {
                const eventData = this.events.find(e => e.id === eventId);
                if (eventData) {
                    // Move to trash instead of deleting
                    this.moveEventToTrash(eventData);
                    movedCount++;
                    
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
                const message = movedCount === 1 
                    ? '일정이 휴지통으로 이동되었습니다' 
                    : `${movedCount}개의 일정이 휴지통으로 이동되었습니다`;
                showNotification(message, 'success');
            }
            
            // Console log removed
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
        // // Console log removed
        
        let cellToUse = clickedCell;
        
        // If no clickedCell provided, try to find the cell by day and hour
        if (!cellToUse) {
            // // Console log removed
            cellToUse = document.querySelector(`.time-cell[data-day="${day}"][data-hour="${hour}"]`);
            // // Console log removed
        }
        
        if (cellToUse) {
            const cellRect = cellToUse.getBoundingClientRect();
            // // Console log removed
            
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
            
            // // Console log removed
            
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
            // // Console log removed
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
            // Console error removed
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
            // Console error removed
            return;
        }

        // // Console log removed

        // Show the selected event in the sidebar events section
        const dayEventsContainer = document.getElementById('day-events');
        if (!dayEventsContainer) {
            // Console error removed
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
                
                // // Console log removed
            } else {
                throw new Error('Failed to save event');
            }
        } catch (error) {
            // Console error removed
            
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
                // // Console log removed
                this.renderEvent(localEventData);
            }, 100);
        }
        
        // Remove popup
        popup.remove();
    }
    
    renderEvent(eventData) {
        // Render event silently

        // Check for null/undefined event data
        if (!eventData || !eventData.id) {
            // Console warn removed
            return;
        }

        // Skip events that are in trash
        if (this.isEventInTrash(eventData.id)) {
            return;
        }

        // 🚫 중복 방지: 기존 이벤트 요소가 있으면 제거
        const existingEvent = this.container.querySelector(`[data-event-id="${eventData.id}"]`);
        if (existingEvent) {
            // Console log removed
            existingEvent.remove();
        }
        
        // Fix null date issue
        if (!eventData.date || eventData.date === null || eventData.date === undefined) {
            // Console warn removed
            const today = new Date();
            eventData.date = today.toISOString().split('T')[0];
        }
        
        // Ensure weekStart is properly initialized
        if (!this.weekStart || !(this.weekStart instanceof Date)) {
            this.weekStart = this.getWeekStart(new Date());
            // // Console log removed
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

        // 🎯 날짜 계산 정확성 개선: 현재 주 범위만 허용 (0-6)
        if (dayIndex < 0 || dayIndex > 6) {
            // Console log removed
            return;
        }

        
        // Check if this is a multi-day event - skip individual rendering
        if (eventData.isMultiDay) {
            // // Console log removed
            // // Console log removed
            return;
        }
        
        // Check if this is an all-day event
        if (eventData.isAllDay) {
            // // Console log removed
            // For all-day events, render them in a special all-day section or as full-day blocks
            this.renderAllDayEvent(eventData, dayIndex);
            return;
        }
        
        // Check if startTime and endTime exist for timed events
        if (!eventData.startTime || !eventData.endTime) {
            // Console warn removed
            this.renderAllDayEvent(eventData, dayIndex);
            return;
        }
        
        const [startHour, startMin] = eventData.startTime.split(':').map(Number);
        const [endHour, endMin] = eventData.endTime.split(':').map(Number);
        
        const startPosition = startHour + startMin / 60;
        const endPosition = endHour + endMin / 60;
        const duration = endPosition - startPosition;
        
        // dayIndex는 이미 0-6 범위로 검증됨
        const dayColumn = this.container.querySelector(`.day-column[data-day="${dayIndex}"]`);
        // Console log removed
        
        if (!dayColumn) {
            //     this.container.querySelectorAll('.day-column'));
            return;
        }
        
        const eventElement = document.createElement('div');
        eventElement.className = 'calendar-event';
        eventElement.dataset.eventId = eventData.id;
        
        // Apply color based on event source
        if (eventData.source === 'google_calendar') {
            // Google Calendar events - Green theme
            eventElement.style.backgroundColor = '#34a853'; // Google Green
            eventElement.style.borderLeft = '4px solid #1e7e34';
            eventElement.classList.add('google-calendar-event');
        } else if (eventData.source === 'notion') {
            // Notion events - Original blue theme
            eventElement.style.backgroundColor = '#3b82f6';
            eventElement.style.borderLeft = '4px solid #1d4ed8';
            eventElement.classList.add('notion-event');
        } else if (eventData.color && eventData.color.startsWith('#')) {
            // Custom color specified
            eventElement.style.backgroundColor = eventData.color;
        } else if (eventData.color) {
            // If it's a color class name
            eventElement.classList.add(eventData.color);
        } else {
            // Default color for other events
            eventElement.style.backgroundColor = '#6b7280'; // Gray for unknown sources
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
        
        // // Console log removed
        
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
        // // Console log removed
        // // Console log removed
    }
    
    renderAllDayEvent(eventData, dayIndex) {
        // // Console log removed

        // Check if this is a multi-day event - skip all-day rendering
        if (eventData.isMultiDay) {
            // // Console log removed
            // // Console log removed
            return;
        }

        // 🚫 중복 방지: 기존 all-day 이벤트 요소가 있으면 제거
        const existingAllDayEvent = this.container.querySelector(`[data-event-id="${eventData.id}"].all-day-event`);
        if (existingAllDayEvent) {
            // Console log removed
            existingAllDayEvent.remove();
        }

        // 🎯 날짜 범위 검증: dayIndex가 0-6 범위 내에 있는지 확인
        if (dayIndex < 0 || dayIndex > 6) {
            // Console log removed
            return;
        }

        const dayColumn = this.container.querySelector(`.day-column[data-day="${dayIndex}"]`);
        // Console log removed
        
        if (!dayColumn) {
            // // Console log removed
            return;
        }
        
        // Find or create all-day events container at the top of the column
        let allDayContainer = dayColumn.querySelector('.all-day-events-container');
        if (!allDayContainer) {
            allDayContainer = document.createElement('div');
            allDayContainer.className = 'all-day-events-container';
            allDayContainer.style.cssText = `
                position: relative;
                width: 100%;
                min-height: 30px;
                max-height: 120px;
                overflow-y: auto;
                background: rgba(59, 130, 246, 0.05);
                border-bottom: 1px solid rgba(59, 130, 246, 0.2);
                padding: 4px;
                z-index: 10;
                margin-bottom: 4px;
                border-radius: 4px;
            `;
            // All-day 컨테이너를 그리드 내 상단에 안전하게 배치
            dayColumn.insertBefore(allDayContainer, dayColumn.firstChild);
            // Console log removed
        }
        
        const eventElement = document.createElement('div');
        eventElement.className = 'calendar-event all-day-event';
        eventElement.dataset.eventId = eventData.id;
        
        // Apply color based on event source
        if (eventData.source === 'google_calendar') {
            // Google Calendar events - Green theme
            eventElement.style.backgroundColor = '#34a853';
            eventElement.style.borderLeft = '4px solid #1e7e34';
            eventElement.classList.add('google-calendar-event');
        } else if (eventData.source === 'notion') {
            // Notion events - Original blue theme
            eventElement.style.backgroundColor = '#3b82f6';
            eventElement.style.borderLeft = '4px solid #1d4ed8';
            eventElement.classList.add('notion-event');
        } else if (eventData.color && eventData.color.startsWith('#')) {
            eventElement.style.backgroundColor = eventData.color;
        } else {
            eventElement.style.backgroundColor = '#6b7280';
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
        // // Console log removed
    }
    
    renderMultiDayEvent(eventData) {
        // // Console log removed
        
        // Check for null/undefined event data
        if (!eventData || !eventData.id) {
            // Console warn removed
            return;
        }
        
        // Ensure we have start and end dates
        if (!eventData.date || !eventData.endDate) {
            // Console warn removed
            return;
        }
        
        // Ensure weekStart is properly initialized
        if (!this.weekStart || !(this.weekStart instanceof Date)) {
            this.weekStart = this.getWeekStart(new Date());
            // // Console log removed
        }
        
        // Parse start and end dates
        const [startYear, startMonth, startDay] = eventData.date.split('-').map(Number);
        const [endYear, endMonth, endDay] = eventData.endDate.split('-').map(Number);
        
        // Parse time for positioning (if available)
        let startHour = 9, startMin = 0, endHour = 10, endMin = 0;
        if (eventData.startTime && eventData.endTime) {
            [startHour, startMin] = eventData.startTime.split(':').map(Number);
            [endHour, endMin] = eventData.endTime.split(':').map(Number);
            // // Console log removed
        } else {
            // Console warn removed
            // Console warn removed
            // Console warn removed
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
        
        // // Console log removed
        // // Console log removed
        
        const startPosition = startHour + startMin / 60;
        const endPosition = endHour + endMin / 60;
        const duration = endPosition - startPosition;
        
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
            // // Console log removed
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
                //     spanDays,
                //     firstCol: firstColRect.left,
                //     lastCol: lastColRect.right,
                //     totalWidth
                // });
            } else {
                // Fallback calculation
                totalWidth = firstDayColumn.offsetWidth * spanDays - 4;
                // // Console log removed
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
        
        // // Console log removed
        
        // Remove the duplicate rendering - the spanning event already covers all days
        return;
        
        // DISABLED: Individual day rendering (causes duplicate events)
        /*
        for (let dayIndex = Math.max(0, startDayIndex); dayIndex <= Math.min(6, endDayIndex); dayIndex++) {
            const dayColumn = this.container.querySelector(`.day-column[data-day="${dayIndex}"]`);
            
            if (!dayColumn) {
                // // Console log removed
                continue;
            }
            
            const eventElement = document.createElement('div');
            eventElement.className = 'calendar-event multi-day-event';
            eventElement.dataset.eventId = eventData.id;
            
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
            
            // // Console log removed
        }
        */
    }
    
    handleEventDrop(e) {
        e.preventDefault();

        // 🛡️ 파일 드롭 완전 차단
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            // Console log removed
            if (window.showNotification) {
                showNotification('파일은 캘린더에 드롭할 수 없습니다', 'error');
            }
            return;
        }

        const eventId = e.dataTransfer.getData('text/plain');
        const targetCell = e.target.closest('.time-cell');

        // 🛡️ 파일 경로나 잘못된 데이터 차단
        if (!targetCell || !eventId ||
            eventId.includes('/Users/') ||
            eventId.includes('.png') ||
            eventId.includes('.jpg') ||
            eventId.includes('.jpeg') ||
            eventId.includes('file://') ||
            eventId.length > 100) {
            // Console log removed
            return;
        }
        
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
        
        // // Console log removed
        
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
                // // Console log removed
                
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
            // Console error removed
            
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
            // Console error removed
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
                // // Console log removed
            } else {
                // Console warn removed
            }
        } catch (error) {
            // Console error removed
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
        // Console log removed

        // First try: Find event by exact ID match
        let eventIndex = this.events.findIndex(e => String(e.id) === eventIdStr);
        if (eventIndex !== -1) {
            // Console log removed
            await this.deleteEvent(this.events[eventIndex]);
            return true;
        }
        
        // Clean events array of null values first
        this.events = this.events.filter(e => e && e.id);
        
        // FIX: 숫자 ID면 클릭된 요소에서 실제 이벤트 찾기
        if (/^\d+$/.test(eventIdStr)) {
            // Console log removed
            
            // 클릭된 삭제 버튼 찾기
            const clickedButton = document.querySelector(`[onclick*="${eventIdStr}"]`);
            if (clickedButton) {
                // 삭제 버튼이 속한 이벤트 요소 찾기
                const eventElement = clickedButton.closest('.event, .calendar-event, [class*="event"]');
                if (eventElement) {
                    // 이벤트 요소에서 제목 추출
                    const titleElement = eventElement.querySelector('.event-title, [class*="title"], h3, h4, span');
                    const eventTitle = titleElement ? titleElement.textContent.trim() : 'Unknown Event';
                    
                    // 제목으로 실제 이벤트 찾기 (여러 방법 시도)
                    let actualEvent = this.events.find(e => e.title === eventTitle);
                    
                    // 정확한 매치가 없으면 부분 매치 시도
                    if (!actualEvent) {
                        actualEvent = this.events.find(e => e.title && e.title.trim() === eventTitle.trim());
                    }
                    
                    // 여전히 없으면 부분 문자열 매치 시도
                    if (!actualEvent) {
                        actualEvent = this.events.find(e => e.title && e.title.includes(eventTitle.trim()));
                    }
                    
                    if (actualEvent) {
                        // Console log removed
                        
                        // 휴지통 확인 대화상자 표시
                        if (confirm(`"${actualEvent.title}" 일정을 휴지통으로 이동하시겠습니까?`)) {
                            return this.deleteEvent(actualEvent);
                        } else {
                            // Console log removed
                            return false;
                        }
                    }
                    
                    // 이벤트를 배열에서 전혀 찾을 수 없는 경우
                    // Console log removed
                    // Console log removed
                    // Console log removed
                    this.events.forEach((e, index) => {
                        // Console log removed
                    });
                    
                    if (confirm(`"${eventTitle}" 일정을 삭제하시겠습니까?`)) {
                        eventElement.remove();
                        // Console log removed
                        
                        // 🚨 강제로 배열에서도 제거 시도 (제목 기반)
                        // Console log removed
                        // Console log removed
                        
                        // 여러 방법으로 이벤트 찾기
                        let indexToRemove = -1;
                        
                        // 1. 정확한 제목 매칭
                        indexToRemove = this.events.findIndex(e => e && e.title && e.title.trim() === eventTitle.trim());
                        
                        // 2. 부분 제목 매칭
                        if (indexToRemove === -1) {
                            indexToRemove = this.events.findIndex(e => e && e.title && e.title.includes(eventTitle.trim()));
                        }
                        
                        // 3. 숫자 ID 매칭 (timestamp 기반)
                        if (indexToRemove === -1) {
                            indexToRemove = this.events.findIndex(e => e && String(e.id).includes(eventIdStr));
                        }
                        
                        if (indexToRemove !== -1) {
                            const removedEvent = this.events[indexToRemove];
                            
                            // 휴지통으로 보내기 (완전 삭제 아님)
                            this.moveEventToTrash(removedEvent);
                            
                            // 클라이언트에서 제거
                            this.events.splice(indexToRemove, 1);
                            this.saveToLocalStorage();
                            // Console log removed
                            
                            // DOM에서 즉시 제거 (여러 방법 시도)
                            this.removeEventFromDOM(removedEvent.id, removedEvent.title);
                            
                            // 선택적 업데이트 (전체 새로고침 대신)
                            // Console log removed
                            this.updateEventList();
                            // Console log removed
                        } else {
                            // Console log removed
                            // Console log removed
                            // Console log removed
                            this.events.slice(0, 5).forEach((e, i) => {
                                // Console log removed
                            });
                            
                            // 더 관대한 검색 시도
                            const relaxedIndex = this.events.findIndex(e => {
                                if (!e) return false;
                                const title = e.title || '';
                                const searchTitle = eventTitle || '';
                                
                                // 제목의 일부만 포함되어도 매칭
                                if (title.length > 0 && searchTitle.length > 0) {
                                    return title.toLowerCase().includes(searchTitle.toLowerCase()) ||
                                           searchTitle.toLowerCase().includes(title.toLowerCase());
                                }
                                
                                return false;
                            });
                                
                            if (relaxedIndex !== -1) {
                                // Console log removed
                                const removedEvent = this.events[relaxedIndex];
                                this.moveEventToTrash(removedEvent);
                                
                                // DOM에서 즉시 제거
                                this.removeEventFromDOM(removedEvent.id, removedEvent.title);
                                
                                this.events.splice(relaxedIndex, 1);
                                this.saveToLocalStorage();
                                this.updateEventList();
                                // Console log removed
                            } else {
                                // Console log removed
                                
                                // DOM에서 강제 제거
                                this.removeEventFromDOM(eventIdStr, eventTitle);
                                
                                // 배열에서 ID나 제목으로 강제 검색해서 제거
                                let foundAndRemoved = false;
                                
                                // 더 관대한 검색으로 배열에서 제거
                                for (let i = this.events.length - 1; i >= 0; i--) {
                                    const event = this.events[i];
                                    if (!event) continue;
                                    
                                    const matchesId = String(event.id) === eventIdStr || 
                                                     String(event.notion_id) === eventIdStr ||
                                                     String(event.uuid) === eventIdStr;
                                    
                                    const matchesTitle = eventTitle && event.title && 
                                                       event.title.includes(eventTitle);
                                    
                                    if (matchesId || matchesTitle) {
                                        // Console log removed
                                        
                                        // 휴지통으로 보내기
                                        this.moveEventToTrash(event);
                                        
                                        // 배열에서 제거
                                        this.events.splice(i, 1);
                                        foundAndRemoved = true;
                                            break;
                                        }
                                    }
                                    
                                    if (!foundAndRemoved) {
                                        // Console log removed
                                        const fakeEvent = {
                                            id: eventIdStr,
                                            title: eventTitle || `삭제된 이벤트 ${eventIdStr}`,
                                            date: new Date().toISOString().split('T')[0],
                                            start_time: '09:00',
                                            end_time: '10:00'
                                        };
                                        this.moveEventToTrash(fakeEvent);
                                    }
                                    
                                    // 배열 저장 및 선택적 업데이트 (전체 새로고침 대신)
                                    this.saveToLocalStorage();
                                    this.updateEventList();
                                    // Console log removed
                                    // Console log removed
                                }
                            }
                            
                            return true;
                        }
                        return false;
                    }
                }
            }
            
            // Last resort: find by DOM element data attributes
            const eventElements = document.querySelectorAll('.event, .calendar-event, [data-event-id]');
            for (const element of eventElements) {
                const elementEventId = element.getAttribute('data-event-id') ||
                                     element.getAttribute('data-id') ||
                                     element.id;

                if (elementEventId === eventId) {
                    // Try to find event in array by title or other attributes
                    const titleElement = element.querySelector('.event-title, .title, .event-name');
                    if (titleElement) {
                        const title = titleElement.textContent.trim();
                        const foundEvent = this.events.find(e => e.title === title);
                        if (foundEvent) {
                            // Console log removed
                            // Delete via DOM element
                            element.remove();
                            // Remove from events array
                            this.events = this.events.filter(e => e.id !== foundEvent.id);
                            return true;
                        }
                    }
                }
            }

            // Console log removed
            // Console log removed
            // Console log removed
            return false;
        }
        
        // 아래 코드는 함수 밖에 있어서 주석 처리
        /*
        const eventData = this.events.find(event => String(event.id) === eventIdStr);
        if (!eventData) {
            // Console error removed
            
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
                // Console log removed
                return this.deleteEvent(finalAttemptEvent);
            }
            
            // Console error removed
            // Console error removed
            
            // DOM에서 강제로 제거
            const eventElements = document.querySelectorAll(`[data-event-id="${eventId}"], [data-id="${eventId}"]`);
            eventElements.forEach(el => {
                el.remove();
                // Console log removed
            });
            return;
        }
        
        // Call the main delete function (휴지통 확인 포함)
        // Console log removed
        return this.deleteEvent(eventData);
    }
    */

    // 필터링된 이벤트로 그리드 업데이트
    updateWithFilteredEvents(filteredEvents, selectedCalendarIds) {
        // Console log removed
        
        // 현재 캘린더 ID 확인 
        const currentCalendarId = window.location.pathname.split('/').pop();
        
        // 필터링이 없거나 빈 경우 - 모든 이벤트 표시 (기본 동작)
        if (!selectedCalendarIds || selectedCalendarIds.length === 0) {
            // Console log removed
            this.showAllEvents();
            return;
        }
        
        // 현재 캘린더가 선택되지 않은 경우 - 여전히 모든 이벤트 표시 (사용자가 직접 현재 캘린더 페이지를 보고 있으므로)
        if (!selectedCalendarIds.includes(currentCalendarId)) {
            // Console log removed
            this.showAllEvents();
            return;
        }
        
        // 필터링된 이벤트가 있는 경우에만 필터링 적용
        if (filteredEvents && filteredEvents.length > 0) {
            // Console log removed
            this.showFilteredEvents(filteredEvents);
            this.updateEventList(filteredEvents);
        } else {
            // 필터링 결과가 없어도 현재 캘린더 페이지에서는 모든 이벤트 표시
            // Console log removed
            this.showAllEvents();
        }
    }
    
    // 모든 이벤트 숨기기
    hideAllEvents() {
        const eventElements = this.container.querySelectorAll('.calendar-event');
        eventElements.forEach(element => {
            element.style.display = 'none';
        });
    }
    
    // 모든 이벤트 표시 (휴지통 이벤트 제외)
    showAllEvents() {
        const eventElements = this.container.querySelectorAll('.calendar-event');
        eventElements.forEach(element => {
            const eventId = element.getAttribute('data-event-id') ||
                           element.getAttribute('data-id');

            // 휴지통에 있는 이벤트는 표시하지 않음
            if (eventId && this.isEventInTrash(eventId)) {
                element.style.display = 'none';
                // Console log removed
            } else {
                element.style.display = 'block';
            }
        });
        // 사이드바 이벤트 목록도 업데이트 (이미 trash 필터링이 적용됨)
        this.updateEventList(this.events);
    }
    
    // 필터링된 이벤트만 표시
    showFilteredEvents(filteredEvents) {
        // 먼저 모든 이벤트 숨기기
        this.hideAllEvents();

        // 필터링된 이벤트 ID 목록 생성 (휴지통 이벤트 제외)
        const filteredEventIds = new Set(
            filteredEvents
                .filter(e => !this.isEventInTrash(e.id))
                .map(e => String(e.id))
        );

        // 해당하는 이벤트들만 표시 (휴지통 이벤트 제외)
        const eventElements = this.container.querySelectorAll('.calendar-event');
        eventElements.forEach(element => {
            const eventId = element.getAttribute('data-event-id') ||
                           element.getAttribute('data-id');

            if (eventId && filteredEventIds.has(String(eventId)) && !this.isEventInTrash(eventId)) {
                element.style.display = '';
            }
        });
    }

    moveEventToTrash(event) {
        // 휴지통 배열에 추가 (LocalStorage 사용)
        let trashedEvents = JSON.parse(localStorage.getItem('trashedEvents') || '[]');

        // 이벤트에 삭제 시간 추가
        const trashedEvent = {
            ...event,
            deletedAt: new Date().toISOString(),
            calendarId: window.location.pathname.split('/').pop() // URL에서 calendarId 추출
        };

        trashedEvents.push(trashedEvent);
        localStorage.setItem('trashedEvents', JSON.stringify(trashedEvents));

        // Console log removed

        // 휴지통 UI 업데이트 (있다면)
        if (window.updateTrashUI) {
            window.updateTrashUI();
        }
    }

    // 영구 삭제된 이벤트 목록 관리
    addToPermanentlyDeleted(eventId) {
        let permanentlyDeleted = JSON.parse(localStorage.getItem('permanentlyDeletedEvents') || '[]');
        if (!permanentlyDeleted.includes(eventId)) {
            permanentlyDeleted.push(eventId);
            localStorage.setItem('permanentlyDeletedEvents', JSON.stringify(permanentlyDeleted));
            // Console log removed
        }
    }

    isPermanentlyDeleted(eventId) {
        const permanentlyDeleted = JSON.parse(localStorage.getItem('permanentlyDeletedEvents') || '[]');
        return permanentlyDeleted.includes(String(eventId));
    }

    cleanupPermanentlyDeleted() {
        // 너무 오래된 영구 삭제 기록은 정리 (30일 이후)
        const cutoffDate = new Date();
        cutoffDate.setDate(cutoffDate.getDate() - 30);

        // 현재는 단순히 30일 후에 전체 목록을 초기화
        const permanentlyDeleted = JSON.parse(localStorage.getItem('permanentlyDeletedEvents') || '[]');
        const lastCleanup = localStorage.getItem('lastPermanentDeleteCleanup');

        if (!lastCleanup || new Date(lastCleanup) < cutoffDate) {
            localStorage.setItem('permanentlyDeletedEvents', '[]');
            localStorage.setItem('lastPermanentDeleteCleanup', new Date().toISOString());
            // Console log removed
        }
    }

    // 휴지통에서 이벤트 복원
    restoreEventFromTrash(eventId) {
        let trashedEvents = JSON.parse(localStorage.getItem('trashedEvents') || '[]');
        const eventIndex = trashedEvents.findIndex(e => String(e.id) === String(eventId));
        
        if (eventIndex !== -1) {
            const eventToRestore = trashedEvents[eventIndex];
            
            // 휴지통에서 제거
            trashedEvents.splice(eventIndex, 1);
            localStorage.setItem('trashedEvents', JSON.stringify(trashedEvents));
            
            // 캘린더에 다시 추가
            delete eventToRestore.deletedAt;
            delete eventToRestore.calendarId;
            
            this.events.push(eventToRestore);
            this.saveToLocalStorage();
            this.renderEvent(eventToRestore);
            
            // Console log removed
            
            // 휴지통 UI 업데이트
            if (window.updateTrashUI) {
                window.updateTrashUI();
            }
            
            // 복원 후 휴지통 닫기
            if (window.hideTrashPopup) {
                setTimeout(() => window.hideTrashPopup(), 500);
            }
        }
    }

    // 휴지통에서 완전 삭제
    async permanentlyDeleteEvent(eventId) {
        let trashedEvents = JSON.parse(localStorage.getItem('trashedEvents') || '[]');
        const eventIndex = trashedEvents.findIndex(e => String(e.id) === String(eventId));
        
        if (eventIndex !== -1) {
            const event = trashedEvents[eventIndex];
            const eventTitle = event.title;
            
            // 타임스탬프 기반 ID는 클라이언트 전용이므로 서버 호출 안 함
            const isClientOnlyEvent = /^\d{13,}$/.test(String(eventId));
            
            // Check if this event needs DB deletion
            const needsDBDeletion = !isClientOnlyEvent || event.backendId;

            if (needsDBDeletion) {
                // 서버에 삭제 요청 (실제 서버 이벤트인 경우만)
                try {
                    const calendarId = event.calendarId || window.location.pathname.split('/').pop();
                    // Use backendId if available, otherwise use eventId
                    const dbEventId = event.backendId || eventId;

                    // Console log removed

                    const response = await fetch(`/api/calendars/${calendarId}/events/${dbEventId}`, {
                        method: 'DELETE',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    });
                    
                    if (response.ok || response.status === 404) {
                        if (response.status === 404) {
                            // Console log removed
                        } else {
                            // Console log removed
                        }
                    } else {
                        // Console error removed
                    }
                } catch (error) {
                    // Console error removed
                }
            } else {
                // Console log removed
            }
            
            // 영구 삭제 목록에 추가 (동기화 시 재가져오기 방지)
            this.addToPermanentlyDeleted(eventId);

            // 휴지통에서 완전 제거
            trashedEvents.splice(eventIndex, 1);
            localStorage.setItem('trashedEvents', JSON.stringify(trashedEvents));

            // Console log removed

            if (window.updateTrashUI) {
                window.updateTrashUI();
            }
        }
    }

    // 휴지통 이벤트 가져오기
    getTrashedEvents() {
        const currentCalendarId = window.location.pathname.split('/').pop();
        let trashedEvents = JSON.parse(localStorage.getItem('trashedEvents') || '[]');
        
        // 현재 캘린더의 휴지통 이벤트만 반환
        return trashedEvents.filter(event => event.calendarId === currentCalendarId);
    }

    // DOM에서 이벤트 완전 제거
    removeEventFromDOM(eventId, eventTitle) {
        let removedCount = 0;
        
        // 1. ID 기반 제거
        const idSelectors = [
            `[data-event-id="${eventId}"]`,
            `[data-id="${eventId}"]`,
            `#event-${eventId}`,
            `[id*="${eventId}"]`
        ];
        
        idSelectors.forEach(selector => {
            document.querySelectorAll(selector).forEach(el => {
                el.remove();
                removedCount++;
                // Console log removed
            });
        });
        
        // 2. 제목 기반 제거 (더 구체적인 셀렉터 사용)
        if (eventTitle) {
            // 캘린더 이벤트 요소만 대상으로 검색
            const eventSelectors = [
                '.calendar-event',
                '.event',
                '[class*="event"]',
                '.grid-event'
            ];

            eventSelectors.forEach(selector => {
                document.querySelectorAll(selector).forEach(el => {
                    const text = el.textContent || el.innerText || '';
                    const title = el.getAttribute('title') || '';
                    const dataTitle = el.getAttribute('data-title') || '';

                    // 정확한 매칭만 허용 (부분 매칭 방지)
                    if ((text.trim() === eventTitle.trim()) ||
                        (title === eventTitle) ||
                        (dataTitle === eventTitle)) {
                        el.remove();
                        removedCount++;
                        // Console log removed
                    }
                });
            });
        }
        
        // 3. 클래스 기반 제거 (일반적인 이벤트 클래스들)
        const eventClasses = [
            '.event', '.calendar-event', '.grid-event', 
            '.time-grid-event', '.event-block'
        ];
        
        eventClasses.forEach(className => {
            document.querySelectorAll(className).forEach(el => {
                const elText = el.textContent || '';
                const elId = el.dataset.eventId || el.dataset.id || el.id || '';
                
                if (elId.includes(eventId) || 
                    (eventTitle && elText.includes(eventTitle))) {
                    el.remove();
                    removedCount++;
                    // Console log removed
                }
            });
        });
        
        // Console log removed
        return removedCount;
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
        
        // // Console log removed
    }

    // Handle window resize events for dynamic grid sizing
    handleResize() {
        // Update main content dimensions first
        this.updateMainContentDimensions();

        // Ensure header visibility
        this.ensureHeaderVisibility();

        // Recalculate grid layout
        this.adjustGridLayout();

        // Update any open popups/modals
        this.repositionOpenPopups();

        // Console log removed
    }

    // Adjust grid layout for current viewport
    adjustGridLayout() {
        const grid = this.container.querySelector('.google-calendar-grid');
        const header = this.container.querySelector('.calendar-header');
        const body = this.container.querySelector('.calendar-grid-body');

        if (!grid || !header || !body) return;

        // Remove all inline styles to let CSS handle everything
        this.container.style.width = '';
        this.container.style.maxWidth = '';
        this.container.style.minWidth = '';

        grid.style.width = '';
        grid.style.maxWidth = '';
        grid.style.minWidth = '';

        header.style.width = '';
        header.style.maxWidth = '';
        header.style.minWidth = '';
        header.style.gridTemplateColumns = '75px repeat(7, 215px)';

        body.style.width = '';
        body.style.maxWidth = '';
        body.style.minWidth = '';
        body.style.gridTemplateColumns = '75px repeat(7, 215px)';

        // Just log for debugging
        const viewportWidth = window.innerWidth;
        const sidebarWidth = this.getSidebarWidth();
        const availableWidth = viewportWidth - sidebarWidth;

            viewportWidth,
            sidebarWidth,
            availableWidth
        });
    }

    // Get sidebar width
    getSidebarWidth() {
        const sidebar = document.querySelector('.sidebar');
        if (!sidebar) return 0;

        const sidebarStyles = window.getComputedStyle(sidebar);
        const isHidden = sidebarStyles.display === 'none' ||
                        sidebarStyles.visibility === 'hidden' ||
                        sidebar.classList.contains('collapsed') ||
                        sidebar.classList.contains('hidden');

        return isHidden ? 0 : sidebar.offsetWidth;
    }

    // Reposition any open popups after resize
    repositionOpenPopups() {
        const popups = document.querySelectorAll('.event-creation-popup');
        popups.forEach(popup => {
            // Find the associated cell if possible and reposition
            const dayData = popup.dataset.day;
            const hourData = popup.dataset.hour;

            if (dayData && hourData) {
                const cell = document.querySelector(`.time-cell[data-day="${dayData}"][data-hour="${hourData}"]`);
                if (cell) {
                    this.repositionPopup(popup, cell);
                }
            }
        });
    }

    // 서버에서 받은 이벤트 데이터를 직접 로드하는 메서드
    loadEvents(events) {
        // Console log removed
        
        if (!events || !Array.isArray(events)) {
            // Console warn removed
            return;
        }
        
        // 기존 이벤트 초기화
        this.events = [];
        
        // 이벤트 변환 및 렌더링
        events.forEach(event => {
            try {
                // 백엔드 이벤트를 프론트엔드 형식으로 변환
                const frontendEvent = this.convertBackendEventToFrontend(event);
                
                // 이벤트 저장
                this.events.push(frontendEvent);
                
                // 렌더링
                this.renderEvent(frontendEvent);
            } catch (error) {
                // Console error removed
            }
        });
        
        // 이벤트 목록 업데이트
        this.updateEventList();
        
        // localStorage에 백업
        this.saveToLocalStorage();
        
        // Console log removed
    }
    
    async loadExistingEvents() {
        // // Console log removed
        
        // Always load from localStorage first for immediate functionality
        this.loadBackupEvents();
        
        // Then try to sync with backend
        try {
            const calendarElement = document.querySelector('.calendar-workspace');
            if (!calendarElement?.dataset.calendarId) {
                // // Console log removed
                return;
            }
            
            const calendarId = calendarElement.dataset.calendarId;
            // // Console log removed
            
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
                // // Console log removed
                this.loadBackupEvents();
            }
            
        } catch (error) {
            // // Console log removed
            this.loadBackupEvents();
        }
        
        // TODO: Enable backend loading once API endpoints are implemented
        /*
        try {
            const calendarElement = document.querySelector('.calendar-workspace');
            if (!calendarElement?.dataset.calendarId) {
                // // Console log removed
                this.loadBackupEvents();
                return;
            }
            
            const calendarId = calendarElement.dataset.calendarId;
            // // Console log removed
            
            const response = await fetch(`/api/calendars/${calendarId}/events`);
            
            if (response.ok) {
                const events = await response.json();
                // // Console log removed
                
                // Clear existing events and render loaded ones
                this.events = [];
                
                if (events && events.length > 0) {
                    events.forEach(event => {
                        const frontendEvent = this.convertBackendEventToFrontend(event);
                        this.events.push(frontendEvent);
                        this.renderEvent(frontendEvent);
                    });
                    // // Console log removed
                    // Update the event list
                    this.updateEventList();
                } else {
                    // No backend events, try localStorage
                    this.loadBackupEvents();
                }
            } else {
                // // Console log removed
                this.loadBackupEvents();
            }
            
        } catch (error) {
            // // Console log removed
            this.loadBackupEvents();
        }
        */
    }
    
    loadBackupEvents() {
        const backupEvents = this.loadFromLocalStorage();

        if (backupEvents.length > 0) {
            backupEvents.forEach(event => {
                this.events.push(event);
                this.renderEvent(event);
            });
            this.updateEventList();
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
                // Console warn removed
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
                // Console warn removed
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
        
        // // Console log removed
        return convertedEvent;
    }
    
    saveToLocalStorage(eventData) {
        try {
            const storageKey = 'calendar_events_backup';
            const existing = JSON.parse(localStorage.getItem(storageKey) || '[]');
            existing.push(eventData);
            localStorage.setItem(storageKey, JSON.stringify(existing));
            // // Console log removed
        } catch (error) {
            // Console error removed
        }
    }
    
    loadFromLocalStorage() {
        try {
            const storageKey = 'calendar_events_backup';
            const rawData = localStorage.getItem(storageKey);

            if (!rawData || rawData === 'null' || rawData === 'undefined') {
                // Clear invalid localStorage data
                localStorage.removeItem(storageKey);
                return [];
            }

            const events = JSON.parse(rawData || '[]');

            // Filter out null/invalid events when loading
            const validEvents = events.filter(event =>
                event &&
                typeof event === 'object' &&
                event.id &&
                event.date &&
                event.title
            );

            // If all events were invalid, clear the storage
            if (events.length > 0 && validEvents.length === 0) {
                localStorage.removeItem(storageKey);
            }

            return validEvents;
        } catch (error) {
            // Console error removed
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
        
        // // Console log removed
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
        // // Console log removed
        const results = this.events.filter(event => 
            event.title.toLowerCase().includes(query.toLowerCase()) ||
            (event.description && event.description.toLowerCase().includes(query.toLowerCase()))
        );
        
        // // Console log removed
        this.displaySearchResults(results, query);
        return results;
    }
    
    displaySearchResults(results, query) {
        // // Console log removed
        
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
        // // Console log removed
        this.updateEventList();
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
    if (window.popupOpen) return;
    
    window.popupOpen = true;
    const overlayForm = document.getElementById('calendar-overlay-form');
    if (!overlayForm) return;
    
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
    window.popupOpen = false;
    const overlayForm = document.getElementById('calendar-overlay-form');
    if (overlayForm) {
        overlayForm.style.display = 'none';
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
        // Console error removed
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
    
    // // Console log removed
}

// Override the original click handlers to use overlay form
window.openEventForm = openEventForm;
window.closeEventForm = closeEventForm;
window.saveOverlayEvent = saveOverlayEvent;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('google-calendar-container');
    if (container) {
        window.googleCalendarGrid = new GoogleCalendarGrid(container);
    }
});

// Global trash functions - let calendar_detail.html handle these
// window.showTrashPopup is defined in calendar_detail.html

// window.hideTrashPopup is defined in calendar_detail.html

// window.emptyTrash is defined in calendar_detail.html

// 🚨 NUCLEAR DOM REMOVAL - 강력한 즉시 제거 함수
window.forceRemoveEventFromDOM = function(eventData) {
    // Console log removed
    
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
            // Console log removed
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
            // Console log removed
        }
    });
    
    // Console log removed
    return removedCount;
};


// 전역 휴지통 함수들 등록
window.restoreEventFromTrash = function(eventId) {
    if (window.googleCalendarGrid) {
        window.googleCalendarGrid.restoreEventFromTrash(eventId);
    }
};

window.permanentlyDeleteEvent = function(eventId) {
    if (window.googleCalendarGrid) {
        window.googleCalendarGrid.permanentlyDeleteEvent(eventId);
    }
};

window.getTrashedEvents = function() {
    if (window.googleCalendarGrid) {
        return window.googleCalendarGrid.getTrashedEvents();
    }
    return [];
};
