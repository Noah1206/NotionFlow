// Google Calendar Style Grid Implementation

class GoogleCalendarGrid {
    constructor(container) {
        this.container = container;
        this.currentDate = new Date();
        this.weekStart = this.getWeekStart(this.currentDate);
        this.events = [];
        
        console.log('🏗️ GoogleCalendarGrid constructor:', {
            currentDate: this.currentDate,
            weekStart: this.weekStart,
            dayOfWeek: this.currentDate.getDay()
        });
        
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
        this.timeSlotHeight = 90; // pixels - Compact size with dynamic drag creation
        
        this.init();
    }
    
    init() {
        this.render();
        this.attachEventListeners();
        this.loadExistingEvents(); // Load existing events from backend
        this.updateCurrentTimeIndicator();
        
        // Update time indicator every minute
        setInterval(() => {
            this.updateCurrentTimeIndicator();
        }, 60000);
        
        console.log('🎯 Google Calendar Grid initialized');
    }
    
    getWeekStart(date) {
        const d = new Date(date.getTime()); // Create a copy to avoid mutating original
        const day = d.getDay(); // 0 = Sunday, 1 = Monday, ..., 6 = Saturday
        
        // Calculate days to subtract to get to Sunday
        const daysToSunday = day;
        const weekStart = new Date(d.getTime() - (daysToSunday * 24 * 60 * 60 * 1000));
        weekStart.setHours(0, 0, 0, 0); // Set to beginning of day
        
        console.log('🗓️ Week start calculated:', weekStart, 'from date:', date, 'day:', day, 'daysToSunday:', daysToSunday);
        return weekStart;
    }
    
    render() {
        const html = `
            <div class="google-calendar-grid">
                ${this.renderHeader()}
                ${this.renderGrid()}
            </div>
        `;
        
        this.container.innerHTML = html;
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
        
        // Render day columns
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
        
        // Single cell click - create 1 hour event
        const day = parseInt(cell.dataset.day);
        const hour = parseInt(cell.dataset.hour);
        
        this.createEvent(day, hour, day, hour);
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
    
    createEvent(startDay, startHour, endDay, endHour) {
        console.log('🎯 createEvent called:', {startDay, startHour, endDay, endHour});
        
        // Ensure weekStart is properly initialized
        if (!this.weekStart || !(this.weekStart instanceof Date)) {
            this.weekStart = this.getWeekStart(new Date());
            console.log('⚠️ weekStart was undefined, recalculated:', this.weekStart);
        }
        
        console.log('🗓️ Current weekStart:', this.weekStart);
        
        // Calculate dates using milliseconds to avoid timezone issues
        const millisecondsPerDay = 24 * 60 * 60 * 1000;
        const startDate = new Date(this.weekStart.getTime() + (startDay * millisecondsPerDay));
        startDate.setHours(startHour, 0, 0, 0);
        
        const endDate = new Date(this.weekStart.getTime() + (endDay * millisecondsPerDay));
        endDate.setHours(endHour + 1, 0, 0, 0); // +1 for end time
        
        console.log('📅 Created dates - Start:', startDate, 'End:', endDate);
        console.log('📍 Expected day column:', startDay, 'Actual date:', startDate.toDateString());
        console.log('📍 Day of week - Start:', startDate.getDay(), 'Expected:', startDay);
        
        this.showEventCreationPopup(startDate, endDate, startDay, startHour);
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
        // Show edit popup similar to creation popup
        const popup = document.createElement('div');
        popup.className = 'event-creation-popup';
        
        const eventDate = new Date(eventData.date);
        const dateStr = this.formatDateForInput(eventDate);
        
        popup.innerHTML = `
            <div class="popup-header">
                <div class="popup-title">일정 편집</div>
                <button class="close-btn" onclick="this.closest('.event-creation-popup').remove()">&times;</button>
            </div>
            <form class="event-form">
                <div class="form-field">
                    <label>제목</label>
                    <input type="text" name="title" value="${eventData.title}" required>
                </div>
                <div class="form-field">
                    <label>날짜</label>
                    <input type="date" name="date" value="${dateStr}">
                </div>
                <div class="form-field">
                    <label>시간</label>
                    <div style="display: flex; gap: 8px; align-items: center;">
                        <input type="time" name="startTime" value="${eventData.startTime}" required>
                        <span>~</span>
                        <input type="time" name="endTime" value="${eventData.endTime}" required>
                    </div>
                </div>
                <div class="form-field">
                    <label>설명</label>
                    <textarea name="description" rows="3">${eventData.description || ''}</textarea>
                </div>
                <button type="submit" class="submit-btn">수정</button>
            </form>
        `;
        
        this.container.appendChild(popup);
        
        popup.querySelector('form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            
            // Update event data
            eventData.title = formData.get('title');
            eventData.date = formData.get('date');
            eventData.startTime = formData.get('startTime');
            eventData.endTime = formData.get('endTime');
            eventData.description = formData.get('description');
            
            // Update in events array
            const index = this.events.findIndex(e => e.id === eventData.id);
            if (index !== -1) {
                this.events[index] = eventData;
            }
            
            // Update localStorage
            this.saveToLocalStorage();
            
            // Re-render all events
            this.clearRenderedEvents();
            this.events.forEach(event => this.renderEvent(event));
            
            popup.remove();
            
            if (window.showNotification) {
                showNotification('일정이 수정되었습니다', 'success');
            }
        });
    }
    
    async deleteEvent(eventData) {
        if (confirm(`"${eventData.title}" 일정을 삭제하시겠습니까?`)) {
            try {
                // Try to delete from backend
                const calendarId = document.querySelector('.calendar-workspace')?.dataset.calendarId || 'default';
                const response = await fetch(`/api/calendars/${calendarId}/events/${eventData.id}`, {
                    method: 'DELETE'
                });
                
                if (!response.ok) {
                    console.warn('Backend delete failed, removing locally only');
                }
            } catch (error) {
                console.error('Failed to delete from backend:', error);
            }
            
            // Remove from events array
            this.events = this.events.filter(e => e.id !== eventData.id);
            
            // Update localStorage
            this.saveToLocalStorage();
            
            // Remove from DOM
            const eventElement = this.container.querySelector(`[data-event-id="${eventData.id}"]`);
            if (eventElement) {
                eventElement.remove();
            }
            
            // Update event list
            this.updateEventList();
            
            if (window.showNotification) {
                showNotification('일정이 삭제되었습니다', 'success');
            }
        }
    }
    
    duplicateEvent(eventData) {
        // Create a copy of the event with a new ID and modified title
        const newEvent = {
            ...eventData,
            id: Date.now().toString(),
            title: eventData.title + ' (복사본)'
        };
        
        // Add to events array
        this.events.push(newEvent);
        
        // Render the new event
        this.renderEvent(newEvent);
        
        // Update localStorage
        this.saveToLocalStorage();
        
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
                console.log('Event saved to backend successfully');
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
            console.log('💾 Events saved to localStorage');
            
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
            eventListContainer.innerHTML = sortedEvents.map(event => {
                const eventDate = new Date(event.date);
                const dateStr = this.formatEventDate(eventDate);
                
                return `
                    <div class="event-list-item" onclick="window.googleCalendarGrid.highlightEvent('${event.id}')" style="cursor: pointer; padding: 8px; margin-bottom: 8px; border-radius: 4px; background: #f5f5f5; hover: background: #e0e0e0;">
                        <div class="event-list-title" style="font-weight: 500; color: #333;">${event.title}</div>
                        <div class="event-list-date" style="font-size: 12px; color: #666; margin-top: 4px;">${dateStr}</div>
                    </div>
                `;
            }).join('');
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
    
    showEventCreationPopup(startDate, endDate, day, hour) {
        // Remove existing popup
        const existingPopup = this.container.querySelector('.event-creation-popup');
        if (existingPopup) {
            existingPopup.remove();
        }
        
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
        const dateStr = startDate.toLocaleDateString('ko-KR');
        
        popup.innerHTML = `
            <div class="popup-header">
                <div class="popup-title">새 일정</div>
                <button class="close-btn" onclick="this.closest('.event-creation-popup').remove()">×</button>
            </div>
            <div class="popup-content">
                <div class="datetime-section">
                    <div class="datetime-row">
                        <div class="datetime-label">날짜</div>
                        <button type="button" class="datetime-button" id="date-button" onclick="window.googleCalendarGrid.showDatePicker(this)">
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
                        <button type="button" class="datetime-button" id="start-time-button" onclick="window.googleCalendarGrid.showTimePicker(this, 'start')">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                <circle cx="12" cy="12" r="10"/>
                                <polyline points="12,6 12,12 16,14"/>
                            </svg>
                            <span class="time-display">오전 ${startTimeStr}</span>
                        </button>
                        <span class="time-range-separator">-</span>
                        <button type="button" class="datetime-button" id="end-time-button" onclick="window.googleCalendarGrid.showTimePicker(this, 'end')">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                <circle cx="12" cy="12" r="10"/>
                                <polyline points="12,6 12,12 16,14"/>
                            </svg>
                            <span class="time-display">오전 ${endTimeStr}</span>
                        </button>
                    </div>
                </div>
                
                <form class="event-form" id="event-creation-form">
                    <div class="form-section">
                        <div class="form-field">
                            <label>제목</label>
                            <input type="text" name="title" class="title-input" placeholder="일정 제목 입력" required>
                        </div>
                        <div class="form-field">
                            <label>설명</label>
                            <textarea name="description" placeholder="일정 설명 (선택사항)"></textarea>
                        </div>
                    </div>
                    
                    <input type="hidden" name="date" value="${this.formatDateForInput(startDate)}">
                    <input type="hidden" name="startTime" value="${startTimeStr}">
                    <input type="hidden" name="endTime" value="${endTimeStr}">
                </form>
            </div>
            
            <div class="form-actions">
                <button type="button" class="btn-secondary" onclick="this.closest('.event-creation-popup').remove()">
                    취소
                </button>
                <button type="button" class="btn-primary" onclick="window.googleCalendarGrid.saveEventFromFullScreen()">
                    저장
                </button>
            </div>
        `;
        
        // Append to body for modal overlay effect
        document.body.appendChild(popup);
        
        // Focus on title input
        setTimeout(() => {
            const titleInput = popup.querySelector('input[name="title"]');
            titleInput.focus();
        }, 100);
        
        // Store popup reference for later use
        this.currentPopup = popup;
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
                    id: savedEvent.id || Date.now(),
                    date: formData.get('date'),
                    startTime: formData.get('startTime'),
                    endTime: formData.get('endTime')
                };
                
                // Add to events array
                this.events.push(fullEventData);
                
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
                
                console.log('📅 Event created and saved:', fullEventData);
            } else {
                throw new Error('Failed to save event');
            }
        } catch (error) {
            console.error('Failed to save event:', error);
            
            // Still show the event locally for user experience
            const localEventData = {
                ...eventData,
                id: Date.now(),
                date: formData.get('date'),
                startTime: formData.get('startTime'),
                endTime: formData.get('endTime')
            };
            
            this.events.push(localEventData);
            this.renderEvent(localEventData);
            
            // Update the event list
            this.updateEventList();
            
            // Save to localStorage as backup
            this.saveToLocalStorage(localEventData);
            
            // Show warning notification
            if (window.showNotification) {
                showNotification('일정이 로컬에만 저장되었습니다', 'warning');
            }
            
            // Force re-render after a short delay
            setTimeout(() => {
                console.log('🔄 Force re-rendering event...');
                this.renderEvent(localEventData);
            }, 100);
        }
        
        // Remove popup
        popup.remove();
    }
    
    renderEvent(eventData) {
        console.log('🎯 renderEvent called with data:', eventData);
        
        // Ensure weekStart is properly initialized
        if (!this.weekStart || !(this.weekStart instanceof Date)) {
            this.weekStart = this.getWeekStart(new Date());
            console.log('⚠️ weekStart was undefined in renderEvent, recalculated:', this.weekStart);
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
        
        console.log('📅 Event date string:', eventDateStr);
        console.log('📅 Event date (parsed):', eventDate);
        console.log('📅 Week start (noon):', weekStart);
        console.log('📅 Time difference (ms):', timeDiff);
        console.log('📅 Day index:', dayIndex);
        
        if (dayIndex < -1 || dayIndex > 7) { // Allow more flexible range
            console.log('❌ Event too far from current week, skipping render. DayIndex:', dayIndex);
            return; // Not in current week
        }
        
        // Adjust dayIndex if it's negative (previous week) or > 6 (next week)
        if (dayIndex < 0) {
            console.log('⚠️ Event from previous week, adjusting...');
        } else if (dayIndex > 6) {
            console.log('⚠️ Event from next week, adjusting...');
        }
        
        const [startHour, startMin] = eventData.startTime.split(':').map(Number);
        const [endHour, endMin] = eventData.endTime.split(':').map(Number);
        
        const startPosition = startHour + startMin / 60;
        const endPosition = endHour + endMin / 60;
        const duration = endPosition - startPosition;
        
        // Ensure dayIndex is within valid range (0-6 for day columns)
        const validDayIndex = Math.max(0, Math.min(6, dayIndex));
        console.log('🔍 Original dayIndex:', dayIndex, 'Adjusted to:', validDayIndex);
        
        const dayColumn = this.container.querySelector(`.day-column[data-day="${validDayIndex}"]`);
        console.log('🔍 Looking for day column with dayIndex:', validDayIndex, 'Found:', dayColumn);
        
        if (!dayColumn) {
            console.log('❌ Day column not found! Available columns:', 
                this.container.querySelectorAll('.day-column'));
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
            <div style="font-weight: 500; margin-bottom: 2px;">${eventData.title}</div>
            ${eventData.description ? `<div style="font-size: 11px; opacity: 0.9;">${eventData.description}</div>` : ''}
        `;
        
        console.log('🎨 Event color:', eventData.color, 'Background:', eventElement.style.backgroundColor);
        
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
        console.log('✅ Event element added to DOM:', eventElement, 'Parent:', dayColumn);
        console.log('📍 Event position - top:', eventElement.style.top, 'height:', eventElement.style.height);
    }
    
    handleEventDrop(e) {
        e.preventDefault();
        
        const eventId = e.dataTransfer.getData('text/plain');
        const targetCell = e.target.closest('.time-cell');
        
        if (!targetCell || !eventId) return;
        
        const newDay = parseInt(targetCell.dataset.day);
        const newHour = parseInt(targetCell.dataset.hour);
        
        // Find the event element and data
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
        
        console.log('📅 Event time updated:', eventData);
        
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
        const form = document.getElementById('event-creation-form');
        if (!form) return;
        
        const formData = new FormData(form);
        
        // Validate required fields
        if (!formData.get('title').trim()) {
            alert('일정 제목을 입력해주세요.');
            form.querySelector('input[name="title"]').focus();
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
        
        const eventData = {
            title: formData.get('title'),
            description: formData.get('description'),
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
                console.log('✅ Event saved to server:', savedEvent);
                
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

    async loadExistingEvents() {
        console.log('📥 Loading existing events...');
        
        // Always load from localStorage first for immediate functionality
        this.loadBackupEvents();
        
        // Then try to sync with backend
        try {
            const calendarElement = document.querySelector('.calendar-workspace');
            if (!calendarElement?.dataset.calendarId) {
                console.log('⚠️ No calendar workspace or ID found, using localStorage only');
                return;
            }
            
            const calendarId = calendarElement.dataset.calendarId;
            console.log('🔍 Fetching events for calendar:', calendarId);
            
            const response = await fetch(`/api/calendars/${calendarId}/events`);
            
            if (response.ok) {
                const events = await response.json();
                console.log('📅 Loaded events from backend:', events);
                
                // Clear existing events
                this.events = [];
                
                if (events && events.length > 0) {
                    events.forEach(event => {
                        const frontendEvent = this.convertBackendEventToFrontend(event);
                        this.events.push(frontendEvent);
                        this.renderEvent(frontendEvent);
                    });
                    console.log(`✅ Successfully loaded ${events.length} events from backend`);
                } else {
                    // No backend events, try localStorage
                    console.log('📝 No backend events, loading from localStorage...');
                    this.loadBackupEvents();
                }
            } else {
                console.log(`📝 Backend API returned ${response.status} - using localStorage`);
                this.loadBackupEvents();
            }
            
        } catch (error) {
            console.log('📝 Backend connection failed - using localStorage:', error.message);
            this.loadBackupEvents();
        }
        
        // TODO: Enable backend loading once API endpoints are implemented
        /*
        try {
            const calendarElement = document.querySelector('.calendar-workspace');
            if (!calendarElement?.dataset.calendarId) {
                console.log('⚠️ No calendar workspace or ID found, using localStorage only');
                this.loadBackupEvents();
                return;
            }
            
            const calendarId = calendarElement.dataset.calendarId;
            console.log('🔍 Fetching events for calendar:', calendarId);
            
            const response = await fetch(`/api/calendars/${calendarId}/events`);
            
            if (response.ok) {
                const events = await response.json();
                console.log('📅 Loaded events from backend:', events);
                
                // Clear existing events and render loaded ones
                this.events = [];
                
                if (events && events.length > 0) {
                    events.forEach(event => {
                        const frontendEvent = this.convertBackendEventToFrontend(event);
                        this.events.push(frontendEvent);
                        this.renderEvent(frontendEvent);
                    });
                    console.log(`✅ Successfully loaded ${events.length} events from backend`);
                    // Update the event list
                    this.updateEventList();
                } else {
                    // No backend events, try localStorage
                    this.loadBackupEvents();
                }
            } else {
                console.log(`📝 Backend API not available (${response.status}) - using localStorage`);
                this.loadBackupEvents();
            }
            
        } catch (error) {
            console.log('📝 Backend connection failed - using localStorage:', error.message);
            this.loadBackupEvents();
        }
        */
    }
    
    loadBackupEvents() {
        console.log('📱 Loading events from localStorage backup...');
        const backupEvents = this.loadFromLocalStorage();
        
        if (backupEvents.length > 0) {
            backupEvents.forEach(event => {
                this.events.push(event);
                this.renderEvent(event);
            });
            console.log(`✅ Loaded ${backupEvents.length} events from localStorage backup`);
            // Update the event list
            this.updateEventList();
        } else {
            console.log('📝 No backup events found in localStorage');
        }
    }
    
    convertBackendEventToFrontend(backendEvent) {
        // Convert backend event format to match frontend expectations
        return {
            id: backendEvent.id,
            title: backendEvent.title || backendEvent.summary || 'Untitled',
            description: backendEvent.description || '',
            date: backendEvent.date || backendEvent.start?.split('T')[0],
            startTime: backendEvent.startTime || backendEvent.start_time || 
                      (backendEvent.start ? new Date(backendEvent.start).toTimeString().slice(0,5) : '09:00'),
            endTime: backendEvent.endTime || backendEvent.end_time ||
                    (backendEvent.end ? new Date(backendEvent.end).toTimeString().slice(0,5) : '10:00'),
            color: backendEvent.color || '#3b82f6'
        };
    }
    
    saveToLocalStorage(eventData) {
        try {
            const storageKey = 'calendar_events_backup';
            const existing = JSON.parse(localStorage.getItem(storageKey) || '[]');
            existing.push(eventData);
            localStorage.setItem(storageKey, JSON.stringify(existing));
            console.log('💾 Event saved to localStorage backup');
        } catch (error) {
            console.error('❌ Failed to save to localStorage:', error);
        }
    }
    
    loadFromLocalStorage() {
        try {
            const storageKey = 'calendar_events_backup';
            const events = JSON.parse(localStorage.getItem(storageKey) || '[]');
            console.log('📱 Loaded from localStorage backup:', events.length, 'events');
            return events;
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
        
        const currentHour = now.getHours() + now.getMinutes() / 60;
        const dayIndex = now.getDay();
        
        if (currentHour < this.startHour || currentHour > this.endHour + 1) {
            return; // Outside visible hours
        }
        
        // Create time indicator line
        const timeLine = document.createElement('div');
        timeLine.className = 'current-time-line';
        
        const top = (currentHour - this.startHour) * this.timeSlotHeight;
        timeLine.style.top = `${top}px`;
        
        const gridBody = this.container.querySelector('.calendar-grid-body');
        gridBody.appendChild(timeLine);
    }

    // Event Search and List Methods
    searchEvents(query) {
        console.log('🔍 Searching events for:', query);
        const results = this.events.filter(event => 
            event.title.toLowerCase().includes(query.toLowerCase()) ||
            (event.description && event.description.toLowerCase().includes(query.toLowerCase()))
        );
        
        console.log('🔍 Search results:', results);
        this.displaySearchResults(results, query);
        return results;
    }
    
    displaySearchResults(results, query) {
        console.log('📊 Displaying search results:', results.length);
        
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
        console.log('📋 Initializing event list');
        this.updateEventList();
    }
    
    updateEventList(eventsToShow = null, searchQuery = null) {
        const eventList = document.getElementById('event-list');
        if (!eventList) {
            console.warn('Event list container not found');
            return;
        }
        
        const events = eventsToShow || this.events;
        console.log('📋 Updating event list with', events.length, 'events');
        
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
                    <div style="margin-bottom: 8px;">📅</div>
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
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('google-calendar-container');
    if (container) {
        window.googleCalendarGrid = new GoogleCalendarGrid(container);
    }
});