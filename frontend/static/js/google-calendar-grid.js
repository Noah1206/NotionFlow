// Google Calendar Style Grid Implementation

class GoogleCalendarGrid {
    constructor(container) {
        this.container = container;
        this.currentDate = new Date();
        this.weekStart = this.getWeekStart(this.currentDate);
        this.events = [];
        
        // Selection state
        this.isSelecting = false;
        this.selectionStart = null;
        this.selectionEnd = null;
        this.selectedCells = new Set();
        
        // Time configuration
        this.startHour = 0; // 12 AM
        this.endHour = 23;  // 11 PM
        this.timeSlotHeight = 120; // pixels - Slightly smaller for better balance
        
        this.init();
    }
    
    init() {
        this.render();
        this.attachEventListeners();
        this.updateCurrentTimeIndicator();
        
        // Update time indicator every minute
        setInterval(() => {
            this.updateCurrentTimeIndicator();
        }, 60000);
        
        console.log('🎯 Google Calendar Grid initialized');
    }
    
    getWeekStart(date) {
        const d = new Date(date);
        const day = d.getDay();
        const diff = d.getDate() - day;
        return new Date(d.setDate(diff));
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
        const startDate = new Date(this.weekStart);
        startDate.setDate(startDate.getDate() + startDay);
        startDate.setHours(startHour, 0, 0, 0);
        
        const endDate = new Date(this.weekStart);
        endDate.setDate(endDate.getDate() + endDay);
        endDate.setHours(endHour + 1, 0, 0, 0); // +1 for end time
        
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
            
            // Show warning notification
            if (window.showNotification) {
                showNotification('일정이 로컬에만 저장되었습니다', 'warning');
            }
        }
        
        // Remove popup
        popup.remove();
    }
    
    renderEvent(eventData) {
        const eventDate = new Date(eventData.date);
        const dayIndex = Math.floor((eventDate - this.weekStart) / (24 * 60 * 60 * 1000));
        
        if (dayIndex < 0 || dayIndex > 6) return; // Not in current week
        
        const [startHour, startMin] = eventData.startTime.split(':').map(Number);
        const [endHour, endMin] = eventData.endTime.split(':').map(Number);
        
        const startPosition = startHour + startMin / 60;
        const endPosition = endHour + endMin / 60;
        const duration = endPosition - startPosition;
        
        const dayColumn = this.container.querySelector(`.day-column[data-day="${dayIndex}"]`);
        if (!dayColumn) return;
        
        const eventElement = document.createElement('div');
        eventElement.className = `calendar-event ${eventData.color}`;
        eventElement.innerHTML = `
            <div style="font-weight: 500; margin-bottom: 2px;">${eventData.title}</div>
            ${eventData.description ? `<div style="font-size: 11px; opacity: 0.9;">${eventData.description}</div>` : ''}
        `;
        
        // Position the event
        const top = (startPosition - this.startHour) * this.timeSlotHeight;
        const height = duration * this.timeSlotHeight - 2; // -2 for spacing
        
        eventElement.style.position = 'absolute';
        eventElement.style.top = `${top}px`;
        eventElement.style.left = '2px';
        eventElement.style.right = '2px';
        eventElement.style.height = `${height}px`;
        eventElement.style.zIndex = '10';
        
        dayColumn.appendChild(eventElement);
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