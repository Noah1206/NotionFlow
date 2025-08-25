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
        console.log('🗓️ Current weekStart:', this.weekStart);
        
        // Create dates more carefully to avoid timezone issues
        const startDate = new Date(this.weekStart.getTime());
        startDate.setDate(startDate.getDate() + startDay);
        startDate.setHours(startHour, 0, 0, 0);
        
        const endDate = new Date(this.weekStart.getTime());
        endDate.setDate(endDate.getDate() + endDay);
        endDate.setHours(endHour + 1, 0, 0, 0); // +1 for end time
        
        console.log('📅 Created dates - Start:', startDate, 'End:', endDate);
        console.log('📍 Expected day column:', startDay, 'Actual date:', startDate.toDateString());
        
        this.showEventCreationPopup(startDate, endDate, startDay, startHour);
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
                <button class="close-btn" onclick="this.closest('.event-creation-popup').remove()">&times;</button>
            </div>
            <form class="event-form">
                <div class="form-field">
                    <label>제목</label>
                    <input type="text" name="title" placeholder="일정 제목 입력" required>
                </div>
                <div class="form-field">
                    <label>날짜</label>
                    <input type="date" name="date" value="${startDate.toISOString().split('T')[0]}">
                </div>
                <div class="form-field">
                    <label>시간</label>
                    <div style="display: flex; gap: 8px; align-items: center;">
                        <input type="time" name="startTime" value="${startTimeStr}" required>
                        <span>-</span>
                        <input type="time" name="endTime" value="${endTimeStr}" required>
                    </div>
                </div>
                <div class="form-field">
                    <label>설명</label>
                    <textarea name="description" placeholder="일정 설명 (선택사항)" rows="2"></textarea>
                </div>
                <div class="form-actions">
                    <button type="button" class="btn-secondary" onclick="this.closest('.event-creation-popup').remove()">
                        취소
                    </button>
                    <button type="submit" class="btn-primary">
                        저장
                    </button>
                </div>
            </form>
        `;
        
        // Position popup
        const targetCell = this.container.querySelector(`[data-day="${day}"][data-hour="${hour}"]`);
        if (targetCell) {
            const rect = targetCell.getBoundingClientRect();
            const containerRect = this.container.getBoundingClientRect();
            
            popup.style.left = `${Math.min(rect.left - containerRect.left, containerRect.width - 350)}px`;
            popup.style.top = `${rect.top - containerRect.top + 50}px`;
        }
        
        this.container.appendChild(popup);
        
        // Focus on title input
        const titleInput = popup.querySelector('input[name="title"]');
        titleInput.focus();
        
        // Handle form submission
        const form = popup.querySelector('.event-form');
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveEvent(form, popup);
        });
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
                
                // Render the event on the grid
                this.renderEvent(fullEventData);
                
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
        
        const eventDate = new Date(eventData.date);
        // Fix timezone issues by setting to noon
        eventDate.setHours(12, 0, 0, 0);
        
        const weekStart = new Date(this.weekStart);
        weekStart.setHours(12, 0, 0, 0);
        
        const dayIndex = Math.floor((eventDate - weekStart) / (24 * 60 * 60 * 1000));
        
        console.log('📅 Event date (noon):', eventDate, 'Week start (noon):', weekStart, 'Day index:', dayIndex);
        
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

    async loadExistingEvents() {
        console.log('📥 Loading existing events...');
        
        // Try backend first, fallback to localStorage
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
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('google-calendar-container');
    if (container) {
        window.googleCalendarGrid = new GoogleCalendarGrid(container);
    }
});