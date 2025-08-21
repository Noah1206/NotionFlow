// Calendar Day Page - Modern Notion Style

// Global variables
let calendarId = '';
let selectedDate = '';

// Initialize the calendar day page
document.addEventListener('DOMContentLoaded', function() {
    console.log('🗓️ Calendar Day page initialized');
    
    // Get calendar ID and selected date from data attributes
    const workspace = document.querySelector('.calendar-day-workspace');
    if (workspace) {
        calendarId = workspace.dataset.calendarId;
        selectedDate = workspace.dataset.selectedDate;
        console.log(`📅 Calendar ID: ${calendarId}, Selected Date: ${selectedDate}`);
    }
    
    // Load saved data from localStorage
    loadSavedData();
    
    // Generate weekly calendar
    generateWeeklyCalendar();
    
    // Load weather data for the week
    loadWeatherData();
    
    // Set default datetime values for event modal
    initializeEventModal();
    
    // Load events and tasks for the selected date
    loadDayEvents();
    loadDayTasks();
    
    // Setup event listeners
    setupEventListeners();
    
    // Initialize real-time features
    initializeRealtimeFeatures();
    
    // Setup auto-save on input changes
    setupAutoSave();
    
    // Setup time click handlers for highlighting
    setupTimeClickHandlers();
});

// Initialize real-time features
function initializeRealtimeFeatures() {
    // Update current time display
    updateCurrentTime();
    setInterval(updateCurrentTime, 60000); // Update every minute
    
    // Highlight current time slot in routine
    highlightCurrentTimeSlot();
    setInterval(highlightCurrentTimeSlot, 60000); // Update every minute
    
    // Update progress stats
    updateProgressStats();
}

// Update current time display
function updateCurrentTime() {
    const currentTimeElement = document.getElementById('current-time');
    if (currentTimeElement) {
        const now = new Date();
        const hours = now.getHours().toString().padStart(2, '0');
        const minutes = now.getMinutes().toString().padStart(2, '0');
        currentTimeElement.textContent = `${hours}:${minutes}`;
    }
}

// Highlight current time slot in routine
function highlightCurrentTimeSlot() {
    const now = new Date();
    const currentHour = now.getHours();
    const currentMinute = now.getMinutes();
    const currentTimeMinutes = currentHour * 60 + currentMinute;
    
    // Remove previous highlights
    document.querySelectorAll('.routine-row.current-time').forEach(row => {
        row.classList.remove('current-time');
    });
    
    // Find and highlight current time slot
    const routineRows = document.querySelectorAll('.routine-row');
    routineRows.forEach(row => {
        const timeCell = row.querySelector('.time-cell');
        if (timeCell) {
            const timeText = timeCell.textContent.trim();
            const [hours, minutes] = timeText.split(':').map(Number);
            const slotTimeMinutes = hours * 60 + minutes;
            
            // Highlight if current time is within 30 minutes of this slot
            if (Math.abs(currentTimeMinutes - slotTimeMinutes) <= 30) {
                row.classList.add('current-time');
            }
        }
    });
}

// Update progress stats dynamically
function updateProgressStats() {
    // Count completed routines
    const routineCheckboxes = document.querySelectorAll('.routine-checkbox');
    const completedRoutines = document.querySelectorAll('.routine-checkbox:checked').length;
    const totalRoutines = routineCheckboxes.length;
    
    // Count completed tasks
    const taskCheckboxes = document.querySelectorAll('.task-checkbox');
    const completedTasks = document.querySelectorAll('.task-checkbox:checked').length;
    const totalTasks = taskCheckboxes.length;
    
    // Update stats display
    const statsGrid = document.querySelector('.stats-grid');
    if (statsGrid) {
        // Update routine stats
        const routineStatValue = statsGrid.querySelector('.stat-item:nth-child(1) .stat-value');
        const routineStatBar = statsGrid.querySelector('.stat-item:nth-child(1) .stat-progress');
        if (routineStatValue) {
            routineStatValue.textContent = `${completedRoutines}/${totalRoutines}`;
        }
        if (routineStatBar) {
            const routinePercent = totalRoutines > 0 ? (completedRoutines / totalRoutines * 100) : 0;
            routineStatBar.style.width = `${routinePercent}%`;
        }
        
        // Update task stats
        const taskStatValue = statsGrid.querySelector('.stat-item:nth-child(2) .stat-value');
        const taskStatBar = statsGrid.querySelector('.stat-item:nth-child(2) .stat-progress');
        if (taskStatValue) {
            taskStatValue.textContent = `${completedTasks}/${totalTasks}`;
        }
        if (taskStatBar) {
            const taskPercent = totalTasks > 0 ? (completedTasks / totalTasks * 100) : 0;
            taskStatBar.style.width = `${taskPercent}%`;
        }
    }
}

// Initialize event modal with selected date
function initializeEventModal() {
    if (selectedDate) {
        const startInput = document.getElementById('event-start');
        const endInput = document.getElementById('event-end');
        
        if (startInput && endInput) {
            // Set start time to 9:00 AM of selected date
            const startDateTime = `${selectedDate}T09:00`;
            startInput.value = startDateTime;
            
            // Set end time to 10:00 AM of selected date
            const endDateTime = `${selectedDate}T10:00`;
            endInput.value = endDateTime;
        }
    }
}

// Load events for the selected date
function loadDayEvents() {
    const eventsContainer = document.getElementById('day-events');
    if (!eventsContainer) return;
    
    // Mock events data - replace with actual API call
    const events = [
        // Add mock events here if needed
    ];
    
    if (events.length === 0) {
        eventsContainer.innerHTML = `
            <div class="no-events">
                <p>이 날짜에 일정이 없습니다.</p>
                <button class="btn-add-event-inline" onclick="openEventModal()">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <line x1="12" y1="5" x2="12" y2="19"/>
                        <line x1="5" y1="12" x2="19" y2="12"/>
                    </svg>
                    이벤트 추가
                </button>
            </div>
        `;
    } else {
        // Render events
        eventsContainer.innerHTML = events.map(event => `
            <div class="event-item" data-event-id="${event.id}">
                <div class="event-time">${event.time}</div>
                <div class="event-content">
                    <div class="event-title">${event.title}</div>
                    <div class="event-description">${event.description || ''}</div>
                </div>
                <div class="event-color" style="background: ${event.color}"></div>
            </div>
        `).join('');
    }
}

// Load tasks for the selected date
function loadDayTasks() {
    console.log('📋 Loading tasks for selected date');
    // Tasks are already rendered in HTML template
    // This function can be expanded to load dynamic tasks from API
}

// Setup event listeners
function setupEventListeners() {
    // Color picker for event modal
    const colorOptions = document.querySelectorAll('.color-option');
    colorOptions.forEach(option => {
        option.addEventListener('click', function() {
            colorOptions.forEach(opt => opt.classList.remove('active'));
            this.classList.add('active');
        });
    });
    
    // Setup Excel-style interactions
    initializeExcelInteractions();
    
    // Setup drag and drop for routine and task tables
    initializeDragAndDrop();
    
    // Setup auto-expanding textarea
    initializeAutoExpandingTextarea();
    
    // Setup table row interactions
    initializeTableInteractions();
}

// Initialize Excel-style table interactions
function initializeExcelInteractions() {
    // Routine checkboxes with enhanced Excel-style feedback
    const routineCheckboxes = document.querySelectorAll('.routine-checkbox');
    routineCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const routineRow = this.closest('.table-row');
            const activityTitle = routineRow.querySelector('.activity-title');
            const activityDescription = routineRow.querySelector('.activity-description');
            
            if (this.checked) {
                // Add completed styling with Excel-like effects
                routineRow.classList.add('completed');
                routineRow.style.opacity = '0.6';
                routineRow.style.background = '#f9fafb';
                
                // Strike through text
                if (activityTitle) {
                    activityTitle.style.textDecoration = 'line-through';
                    activityTitle.style.color = '#9ca3af';
                }
                if (activityDescription) {
                    activityDescription.style.textDecoration = 'line-through';
                    activityDescription.style.color = '#d1d5db';
                }
                
                // Animate checkbox
                this.style.transform = 'scale(1.1)';
                setTimeout(() => {
                    this.style.transform = 'scale(1)';
                }, 200);
                
                console.log('✅ Routine completed');
                updateProgressStats(); // Update stats when checkbox changes
            } else {
                // Remove completed styling
                routineRow.classList.remove('completed');
                routineRow.style.opacity = '1';
                routineRow.style.background = '#ffffff';
                
                // Remove strike through
                if (activityTitle) {
                    activityTitle.style.textDecoration = 'none';
                    activityTitle.style.color = '#1f2937';
                }
                if (activityDescription) {
                    activityDescription.style.textDecoration = 'none';
                    activityDescription.style.color = '#6b7280';
                }
                
                console.log('🔄 Routine uncompleted');
            }
        });
    });
    
    // Task checkboxes with enhanced Excel-style feedback
    const taskCheckboxes = document.querySelectorAll('.task-checkbox');
    taskCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const taskRow = this.closest('.table-row');
            
            if (this.checked) {
                // Add completed class (CSS handles the styling)
                taskRow.classList.add('completed');
                
                // Animate checkbox
                this.style.transform = 'scale(1.1)';
                setTimeout(() => {
                    this.style.transform = 'scale(1)';
                }, 200);
                
                // Add completion animation
                taskRow.style.transform = 'scale(0.98)';
                setTimeout(() => {
                    taskRow.style.transform = 'scale(1)';
                }, 150);
                
                console.log('✅ Task completed');
            } else {
                // Remove completed class
                taskRow.classList.remove('completed');
                console.log('🔄 Task uncompleted');
            }
        });
    });
}

// Initialize drag and drop functionality for Excel-style tables
function initializeDragAndDrop() {
    let draggedElement = null;
    let placeholder = null;
    
    // Setup drag and drop for routine rows
    const routineRows = document.querySelectorAll('.routine-row');
    routineRows.forEach(row => {
        setupRowDragAndDrop(row, 'routine');
    });
    
    // Setup drag and drop for task rows
    const taskRows = document.querySelectorAll('.task-row');
    taskRows.forEach(row => {
        setupRowDragAndDrop(row, 'task');
    });
}

function setupRowDragAndDrop(row, type) {
    row.addEventListener('dragstart', function(e) {
        draggedElement = this;
        this.classList.add('dragging');
        this.style.opacity = '0.5';
        
        // Create placeholder
        placeholder = document.createElement('div');
        placeholder.className = 'drag-placeholder';
        placeholder.style.height = this.offsetHeight + 'px';
        placeholder.style.background = '#eff6ff';
        placeholder.style.border = '2px dashed #3b82f6';
        placeholder.style.borderRadius = '8px';
        placeholder.style.margin = '4px 0';
        
        console.log(`🔀 Started dragging ${type} row`);
    });
    
    row.addEventListener('dragend', function(e) {
        this.classList.remove('dragging');
        this.style.opacity = '1';
        
        if (placeholder && placeholder.parentNode) {
            placeholder.parentNode.removeChild(placeholder);
        }
        
        draggedElement = null;
        placeholder = null;
        
        console.log(`✅ Finished dragging ${type} row`);
    });
    
    row.addEventListener('dragover', function(e) {
        e.preventDefault();
        
        if (draggedElement && draggedElement !== this) {
            const tableBody = this.parentNode;
            const afterElement = getDragAfterElement(tableBody, e.clientY);
            
            if (afterElement == null) {
                if (placeholder) {
                    tableBody.appendChild(placeholder);
                }
            } else {
                if (placeholder) {
                    tableBody.insertBefore(placeholder, afterElement);
                }
            }
        }
    });
    
    row.addEventListener('drop', function(e) {
        e.preventDefault();
        
        if (draggedElement && placeholder && placeholder.parentNode) {
            placeholder.parentNode.insertBefore(draggedElement, placeholder);
            placeholder.parentNode.removeChild(placeholder);
            
            // Save new order (implement as needed)
            saveRowOrder(type);
        }
    });
}

function getDragAfterElement(container, y) {
    const draggableElements = [...container.querySelectorAll('.table-row:not(.dragging)')];
    
    return draggableElements.reduce((closest, child) => {
        const box = child.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;
        
        if (offset < 0 && offset > closest.offset) {
            return { offset: offset, element: child };
        } else {
            return closest;
        }
    }, { offset: Number.NEGATIVE_INFINITY }).element;
}

function saveRowOrder(type) {
    console.log(`💾 Saving ${type} row order`);
    // Implement order persistence here
    // You could send the new order to your backend API
}

// Initialize auto-expanding textarea for notes
function initializeAutoExpandingTextarea() {
    const textarea = document.querySelector('.notes-textarea');
    if (textarea) {
        // Auto-expand on input
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.max(this.scrollHeight, 160) + 'px';
        });
        
        // Set initial height
        textarea.style.height = Math.max(textarea.scrollHeight, 160) + 'px';
    }
    
    // Also handle notes title input
    const notesTitle = document.querySelector('.notes-title');
    if (notesTitle) {
        notesTitle.addEventListener('focus', function() {
            this.style.borderBottom = '2px solid #3b82f6';
        });
        
        notesTitle.addEventListener('blur', function() {
            this.style.borderBottom = '1px solid #e5e7eb';
        });
    }
}

// Initialize enhanced table row interactions
function initializeTableInteractions() {
    const tableRows = document.querySelectorAll('.table-row');
    
    tableRows.forEach(row => {
        // Enhanced hover effects
        row.addEventListener('mouseenter', function() {
            if (!this.classList.contains('dragging')) {
                this.style.transform = 'translateX(2px)';
                this.style.boxShadow = 'inset 3px 0 0 #3b82f6, 0 2px 4px rgba(0,0,0,0.05)';
            }
        });
        
        row.addEventListener('mouseleave', function() {
            if (!this.classList.contains('dragging')) {
                this.style.transform = 'translateX(0)';
                this.style.boxShadow = 'none';
            }
        });
        
        // Keyboard navigation support
        row.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                const checkbox = this.querySelector('input[type="checkbox"]');
                if (checkbox) {
                    checkbox.checked = !checkbox.checked;
                    checkbox.dispatchEvent(new Event('change'));
                }
            }
        });
    });
    
    // Add click-to-focus for table rows
    tableRows.forEach(row => {
        row.addEventListener('click', function(e) {
            // Don't interfere with checkbox or button clicks
            if (e.target.type !== 'checkbox' && !e.target.closest('button')) {
                const checkbox = this.querySelector('input[type="checkbox"]');
                if (checkbox) {
                    checkbox.focus();
                }
            }
        });
    });
    
    // Initialize inline text editing
    initializeInlineTextEditing();
}

// Initialize inline text editing functionality
function initializeInlineTextEditing() {
    // Setup double-click editing for routine items
    const routineRows = document.querySelectorAll('.routine-row');
    routineRows.forEach(row => {
        setupInlineEditing(row, 'routine');
    });
    
    // Setup double-click editing for task items
    const taskRows = document.querySelectorAll('.task-row');
    taskRows.forEach(row => {
        setupInlineEditing(row, 'task');
    });
}

function setupInlineEditing(row, type) {
    const titleElement = row.querySelector(type === 'routine' ? '.activity-title' : '.task-title');
    const descriptionElement = row.querySelector(type === 'routine' ? '.activity-description' : '.task-description');
    const timeElement = row.querySelector('.time-cell');
    
    // Make elements editable on double-click
    [titleElement, descriptionElement, timeElement].forEach(element => {
        if (element) {
            setupElementEditing(element, type);
        }
    });
}

function setupElementEditing(element, type) {
    let isEditing = false;
    let originalValue = '';
    
    // Double-click to edit
    element.addEventListener('dblclick', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        if (isEditing) return;
        
        startInlineEdit(this);
    });
    
    // Click to edit (single click alternative)
    element.addEventListener('click', function(e) {
        if (e.detail === 1) { // Single click
            setTimeout(() => {
                if (e.detail === 1 && !isEditing) {
                    // Add visual hint for editing
                    this.style.cursor = 'text';
                    this.title = '더블클릭하여 편집';
                }
            }, 200);
        }
    });
    
    function startInlineEdit(element) {
        if (isEditing) return;
        
        isEditing = true;
        originalValue = element.textContent;
        
        // Create input field
        const input = document.createElement('input');
        const isTimeCell = element.classList.contains('time-cell') || element.closest('.time-cell');
        
        if (isTimeCell) {
            input.type = 'time';
            // Convert display format to time input format
            const timeMatch = originalValue.match(/(\d{1,2}):(\d{2})/);
            if (timeMatch) {
                const hours = timeMatch[1].padStart(2, '0');
                const minutes = timeMatch[2];
                input.value = `${hours}:${minutes}`;
            }
        } else {
            input.type = 'text';
            input.value = originalValue;
        }
        
        input.className = 'inline-editor';
        
        // Style the input to match the original element
        const computedStyle = window.getComputedStyle(element);
        input.style.font = computedStyle.font;
        input.style.color = computedStyle.color;
        input.style.background = '#ffffff';
        input.style.border = '2px solid #3b82f6';
        input.style.borderRadius = '4px';
        input.style.padding = isTimeCell ? '2px 6px' : '4px 8px';
        input.style.width = isTimeCell ? '80px' : Math.max(element.offsetWidth + 20, 120) + 'px';
        input.style.fontSize = computedStyle.fontSize;
        input.style.fontWeight = computedStyle.fontWeight;
        input.style.outline = 'none';
        input.style.boxShadow = '0 2px 4px rgba(59, 130, 246, 0.1)';
        input.style.textAlign = isTimeCell ? 'center' : 'left';
        
        // Replace element with input
        element.style.display = 'none';
        element.parentNode.insertBefore(input, element);
        
        // Focus and select all text
        input.focus();
        input.select();
        
        // Save on Enter, cancel on Escape
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                saveEdit();
            } else if (e.key === 'Escape') {
                cancelEdit();
            }
            e.stopPropagation();
        });
        
        // Save when clicking outside
        input.addEventListener('blur', function() {
            setTimeout(saveEdit, 100);
        });
        
        function saveEdit() {
            if (!isEditing) return;
            
            let newValue = input.value.trim();
            
            // Special handling for time input
            if (isTimeCell && newValue) {
                // Convert from 24-hour format to display format if needed
                const timeMatch = newValue.match(/(\d{1,2}):(\d{2})/);
                if (timeMatch) {
                    const hours = parseInt(timeMatch[1]);
                    const minutes = timeMatch[2];
                    newValue = `${hours.toString().padStart(2, '0')}:${minutes}`;
                }
            }
            
            if (newValue && newValue !== originalValue) {
                // Update the text
                element.textContent = newValue;
                
                // Add save animation with different colors for different types
                const saveColor = isTimeCell ? '#eff6ff' : '#f0fdf4';
                element.style.background = saveColor;
                element.style.transform = 'scale(1.02)';
                element.style.borderRadius = '4px';
                element.style.transition = 'all 0.3s ease';
                
                setTimeout(() => {
                    element.style.background = '';
                    element.style.transform = 'scale(1)';
                    element.style.borderRadius = '';
                    element.style.transition = '';
                }, 300);
                
                console.log(`💾 Updated ${type} ${isTimeCell ? 'time' : 'text'}: "${originalValue}" → "${newValue}"`);
                
                // Here you could save to server
                saveTextChange(element, type, newValue);
            } else if (!newValue) {
                // Don't allow empty values
                input.style.borderColor = '#dc2626';
                input.style.background = '#fef2f2';
                input.placeholder = isTimeCell ? '시간 입력' : '내용을 입력하세요';
                input.focus();
                return;
            }
            
            finishEdit();
        }
        
        function cancelEdit() {
            if (!isEditing) return;
            
            // Add cancel animation
            input.style.background = '#fef2f2';
            setTimeout(finishEdit, 150);
        }
        
        function finishEdit() {
            if (!isEditing) return;
            
            isEditing = false;
            element.style.display = '';
            element.style.cursor = '';
            element.title = '';
            
            if (input.parentNode) {
                input.parentNode.removeChild(input);
            }
        }
    }
}

// Save text changes (implement server sync here)
function saveTextChange(element, type, newValue) {
    // Mock save - implement actual server API call here
    const saveData = {
        type: type,
        element: element.className,
        newValue: newValue,
        timestamp: new Date().toISOString()
    };
    
    // You could send this to your backend API
    // fetch('/api/save-text-change', {
    //     method: 'POST',
    //     headers: { 'Content-Type': 'application/json' },
    //     body: JSON.stringify(saveData)
    // });
    
    console.log('📝 Text change saved:', saveData);
}

// Modal functions
function openEventModal() {
    const modal = document.getElementById('event-modal');
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
        
        // Focus on title input
        const titleInput = document.getElementById('event-title');
        if (titleInput) {
            setTimeout(() => titleInput.focus(), 100);
        }
    }
}

function closeEventModal() {
    const modal = document.getElementById('event-modal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
        
        // Clear form
        clearEventForm();
    }
}

function clearEventForm() {
    const titleInput = document.getElementById('event-title');
    const descriptionInput = document.getElementById('event-description');
    const alldayCheckbox = document.getElementById('event-allday');
    
    if (titleInput) titleInput.value = '';
    if (descriptionInput) descriptionInput.value = '';
    if (alldayCheckbox) alldayCheckbox.checked = false;
    
    // Reset color selection
    const colorOptions = document.querySelectorAll('.color-option');
    colorOptions.forEach(opt => opt.classList.remove('active'));
    if (colorOptions.length > 0) {
        colorOptions[0].classList.add('active');
    }
    
    // Reset datetime values
    initializeEventModal();
}

// Save event
function saveEvent() {
    const title = document.getElementById('event-title')?.value;
    const startTime = document.getElementById('event-start')?.value;
    const endTime = document.getElementById('event-end')?.value;
    const description = document.getElementById('event-description')?.value;
    const isAllDay = document.getElementById('event-allday')?.checked;
    const selectedColor = document.querySelector('.color-option.active')?.dataset.color || '#3B82F6';
    
    if (!title) {
        alert('이벤트 제목을 입력해주세요.');
        return;
    }
    
    if (!startTime || !endTime) {
        alert('시작일과 종료일을 설정해주세요.');
        return;
    }
    
    const eventData = {
        title,
        start_time: startTime,
        end_time: endTime,
        description,
        is_all_day: isAllDay,
        color: selectedColor,
        calendar_id: calendarId,
        date: selectedDate
    };
    
    console.log('💾 Saving event:', eventData);
    
    // Here you would make an API call to save the event
    // For now, just show success message
    alert('이벤트가 저장되었습니다.');
    closeEventModal();
    
    // Reload events
    loadDayEvents();
}

// Add routine item
function addRoutineItem() {
    const time = prompt('시간을 입력하세요 (예: 14:30):') || '09:00';
    const task = prompt('할 일을 입력하세요:') || '새 루틴';
    const description = prompt('설명을 입력하세요 (선택사항):') || '';
    
    if (time && task) {
        const routineTableBody = document.querySelector('.routine-table .table-body');
        if (routineTableBody) {
            const newRoutineRow = document.createElement('div');
            newRoutineRow.className = 'table-row routine-row';
            newRoutineRow.draggable = true;
            newRoutineRow.innerHTML = `
                <div class="cell time-cell">${time}</div>
                <div class="cell activity-cell">
                    <div class="activity-title">${task}</div>
                    <div class="activity-description">${description}</div>
                </div>
                <div class="cell status-cell">
                    <input type="checkbox" class="routine-checkbox">
                </div>
            `;
            
            routineTableBody.appendChild(newRoutineRow);
            
            // Setup all interactions for the new row
            setupRowDragAndDrop(newRoutineRow, 'routine');
            setupInlineEditing(newRoutineRow, 'routine');
            
            // Add enhanced hover effects
            newRoutineRow.addEventListener('mouseenter', function() {
                if (!this.classList.contains('dragging')) {
                    this.style.transform = 'translateX(2px)';
                    this.style.boxShadow = 'inset 3px 0 0 #3b82f6, 0 2px 4px rgba(0,0,0,0.05)';
                }
            });
            
            newRoutineRow.addEventListener('mouseleave', function() {
                if (!this.classList.contains('dragging')) {
                    this.style.transform = 'translateX(0)';
                    this.style.boxShadow = 'none';
                }
            });
            
            // Add checkbox event listener with Excel-style feedback
            const newCheckbox = newRoutineRow.querySelector('.routine-checkbox');
            newCheckbox.addEventListener('change', function() {
                const routineRow = this.closest('.table-row');
                const activityTitle = routineRow.querySelector('.activity-title');
                const activityDescription = routineRow.querySelector('.activity-description');
                
                if (this.checked) {
                    routineRow.classList.add('completed');
                    routineRow.style.opacity = '0.6';
                    routineRow.style.background = '#f9fafb';
                    
                    if (activityTitle) {
                        activityTitle.style.textDecoration = 'line-through';
                        activityTitle.style.color = '#9ca3af';
                    }
                    if (activityDescription) {
                        activityDescription.style.textDecoration = 'line-through';
                        activityDescription.style.color = '#d1d5db';
                    }
                    
                    this.style.transform = 'scale(1.1)';
                    setTimeout(() => { this.style.transform = 'scale(1)'; }, 200);
                } else {
                    routineRow.classList.remove('completed');
                    routineRow.style.opacity = '1';
                    routineRow.style.background = '#ffffff';
                    
                    if (activityTitle) {
                        activityTitle.style.textDecoration = 'none';
                        activityTitle.style.color = '#1f2937';
                    }
                    if (activityDescription) {
                        activityDescription.style.textDecoration = 'none';
                        activityDescription.style.color = '#6b7280';
                    }
                }
            });
            
            console.log('✅ New routine item added with inline editing enabled');
        }
    }
}

// Add task item
function addTaskItem() {
    const title = prompt('할 일 제목을 입력하세요:') || '새 작업';
    const description = prompt('설명을 입력하세요 (선택사항):') || '';
    const priority = prompt('우선순위를 입력하세요 (high/medium/low):', 'medium') || 'medium';
    
    if (title) {
        const taskTableBody = document.querySelector('.tasks-table .table-body');
        if (taskTableBody) {
            const newTaskRow = document.createElement('div');
            newTaskRow.className = 'table-row task-row';
            newTaskRow.draggable = true;
            
            const priorityText = priority === 'high' ? '중요' : priority === 'low' ? '낮음' : '보통';
            
            newTaskRow.innerHTML = `
                <div class="cell status-cell">
                    <input type="checkbox" class="task-checkbox">
                </div>
                <div class="cell task-cell">
                    <div class="task-title">${title}</div>
                    <div class="task-description">${description}</div>
                </div>
                <div class="cell priority-cell">
                    <span class="priority-chip ${priority}">${priorityText}</span>
                </div>
            `;
            
            taskTableBody.appendChild(newTaskRow);
            
            // Setup all interactions for the new row
            setupRowDragAndDrop(newTaskRow, 'task');
            setupInlineEditing(newTaskRow, 'task');
            
            // Add enhanced hover effects
            newTaskRow.addEventListener('mouseenter', function() {
                if (!this.classList.contains('dragging')) {
                    this.style.transform = 'translateX(2px)';
                    this.style.boxShadow = 'inset 3px 0 0 #3b82f6, 0 2px 4px rgba(0,0,0,0.05)';
                }
            });
            
            newTaskRow.addEventListener('mouseleave', function() {
                if (!this.classList.contains('dragging')) {
                    this.style.transform = 'translateX(0)';
                    this.style.boxShadow = 'none';
                }
            });
            
            // Add checkbox event listener with Excel-style feedback
            const newCheckbox = newTaskRow.querySelector('.task-checkbox');
            newCheckbox.addEventListener('change', function() {
                const taskRow = this.closest('.table-row');
                
                if (this.checked) {
                    taskRow.classList.add('completed');
                    
                    // Animate checkbox
                    this.style.transform = 'scale(1.1)';
                    setTimeout(() => {
                        this.style.transform = 'scale(1)';
                    }, 200);
                    
                    // Add completion animation
                    taskRow.style.transform = 'scale(0.98)';
                    setTimeout(() => {
                        taskRow.style.transform = 'scale(1)';
                    }, 150);
                } else {
                    taskRow.classList.remove('completed');
                }
            });
            
            console.log('✅ New task item added with inline editing enabled');
        }
    }
}

// Save notes
function saveNotes() {
    const notesTextarea = document.querySelector('.notes-textarea');
    if (notesTextarea) {
        const notesContent = notesTextarea.value;
        
        // Here you would save to API
        console.log('💾 Saving notes:', notesContent);
        
        // Show success feedback
        const saveBtn = document.querySelector('.save-notes-btn');
        if (saveBtn) {
            const originalText = saveBtn.textContent;
            saveBtn.textContent = '저장됨!';
            saveBtn.style.background = '#10b981';
            
            setTimeout(() => {
                saveBtn.textContent = originalText;
                saveBtn.style.background = '';
            }, 2000);
        }
    }
}

// Go to today
function goToToday() {
    const today = new Date();
    const todayString = today.toISOString().split('T')[0];
    window.location.href = `/dashboard/calendar/${calendarId}/day/${todayString}`;
}

// Close modal when clicking outside
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal-overlay')) {
        closeEventModal();
    }
});

// Close modal with Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeEventModal();
    }
});

/* ============================================================================
   NEW CRUD FUNCTIONS FOR ENHANCED EXCEL-STYLE SECTIONS
   ============================================================================ */

// Global counters for unique IDs
let noteIdCounter = 4;
let progressIdCounter = 4;
let timeIdCounter = 4;
let routineIdCounter = 6;

// ===== QUICK NOTES SECTION =====

function addNoteItem() {
    const noteTableBody = document.getElementById('notes-table-body');
    const notesEmpty = document.getElementById('notes-empty');
    
    if (noteTableBody) {
        // Hide empty state if visible
        if (notesEmpty) {
            notesEmpty.style.display = 'none';
        }
        
        const newNoteRow = document.createElement('div');
        newNoteRow.className = 'table-row note-row';
        newNoteRow.setAttribute('data-note-id', noteIdCounter);
        
        newNoteRow.innerHTML = `
            <div class="cell priority-cell">
                <select class="priority-select">
                    <option value="high">🔥 높음</option>
                    <option value="medium" selected>📋 보통</option>
                    <option value="low">📝 낮음</option>
                </select>
            </div>
            <div class="cell note-cell">
                <input type="text" class="note-input" placeholder="새 메모 입력..." autofocus>
            </div>
            <div class="cell action-cell">
                <button class="action-btn delete-note" onclick="deleteNote(${noteIdCounter})" title="삭제">🗑</button>
            </div>
        `;
        
        noteTableBody.appendChild(newNoteRow);
        
        // Focus on the new input
        const newInput = newNoteRow.querySelector('.note-input');
        if (newInput) {
            newInput.focus();
        }
        
        noteIdCounter++;
        console.log('✅ New note added');
    }
}

function deleteNote(noteId) {
    const noteRow = document.querySelector(`[data-note-id="${noteId}"]`);
    const noteTableBody = document.getElementById('notes-table-body');
    const notesEmpty = document.getElementById('notes-empty');
    
    if (noteRow && confirm('이 메모를 삭제하시겠습니까?')) {
        // Add deletion animation
        noteRow.style.transform = 'scale(0.9)';
        noteRow.style.opacity = '0.5';
        
        setTimeout(() => {
            noteRow.remove();
            
            // Show empty state if no notes remain
            const remainingNotes = noteTableBody.querySelectorAll('.note-row');
            if (remainingNotes.length === 0 && notesEmpty) {
                notesEmpty.style.display = 'flex';
            }
            
            console.log(`🗑 Note ${noteId} deleted`);
        }, 200);
    }
}

function clearAllNotes() {
    const noteTableBody = document.getElementById('notes-table-body');
    const notesEmpty = document.getElementById('notes-empty');
    
    if (noteTableBody && confirm('모든 메모를 삭제하시겠습니까?')) {
        // Add clearing animation
        const noteRows = noteTableBody.querySelectorAll('.note-row');
        noteRows.forEach((row, index) => {
            setTimeout(() => {
                row.style.transform = 'translateX(-100%)';
                row.style.opacity = '0';
            }, index * 50);
        });
        
        setTimeout(() => {
            noteTableBody.innerHTML = '';
            if (notesEmpty) {
                notesEmpty.style.display = 'flex';
            }
            console.log('🗑 All notes cleared');
        }, noteRows.length * 50 + 200);
    }
}

// ===== TODAY'S PROGRESS SECTION =====

function addProgressItem() {
    const progressTableBody = document.getElementById('progress-table-body');
    const progressEmpty = document.getElementById('progress-empty');
    
    if (progressTableBody) {
        // Hide empty state if visible
        if (progressEmpty) {
            progressEmpty.style.display = 'none';
        }
        
        const newProgressRow = document.createElement('div');
        newProgressRow.className = 'table-row progress-row';
        newProgressRow.setAttribute('data-progress-id', progressIdCounter);
        
        newProgressRow.innerHTML = `
            <div class="cell metric-cell">
                <input type="text" class="metric-input" placeholder="지표명 입력..." autofocus>
            </div>
            <div class="cell value-cell">
                <div class="progress-input-group">
                    <input type="number" class="progress-current" value="0" min="0" max="99">
                    <span class="progress-separator">/</span>
                    <input type="number" class="progress-total" value="1" min="1" max="99">
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: 0%"></div>
                </div>
            </div>
            <div class="cell action-cell">
                <button class="action-btn delete-progress" onclick="deleteProgress(${progressIdCounter})" title="삭제">🗑</button>
            </div>
        `;
        
        progressTableBody.appendChild(newProgressRow);
        
        // Setup progress calculation for new row
        setupProgressCalculation(newProgressRow);
        
        // Focus on the new input
        const newInput = newProgressRow.querySelector('.metric-input');
        if (newInput) {
            newInput.focus();
        }
        
        progressIdCounter++;
        console.log('✅ New progress metric added');
    }
}

function setupProgressCalculation(progressRow) {
    const currentInput = progressRow.querySelector('.progress-current');
    const totalInput = progressRow.querySelector('.progress-total');
    const progressBar = progressRow.querySelector('.progress-fill');
    
    function updateProgress() {
        const current = parseInt(currentInput.value) || 0;
        const total = parseInt(totalInput.value) || 1;
        const percentage = total > 0 ? (current / total * 100) : 0;
        
        progressBar.style.width = `${Math.min(100, Math.max(0, percentage))}%`;
    }
    
    currentInput.addEventListener('input', updateProgress);
    totalInput.addEventListener('input', updateProgress);
    
    // Initial calculation
    updateProgress();
}

function deleteProgress(progressId) {
    const progressRow = document.querySelector(`[data-progress-id="${progressId}"]`);
    const progressTableBody = document.getElementById('progress-table-body');
    const progressEmpty = document.getElementById('progress-empty');
    
    if (progressRow && confirm('이 지표를 삭제하시겠습니까?')) {
        // Add deletion animation
        progressRow.style.transform = 'scale(0.9)';
        progressRow.style.opacity = '0.5';
        
        setTimeout(() => {
            progressRow.remove();
            
            // Show empty state if no progress items remain
            const remainingProgress = progressTableBody.querySelectorAll('.progress-row');
            if (remainingProgress.length === 0 && progressEmpty) {
                progressEmpty.style.display = 'flex';
            }
            
            console.log(`🗑 Progress ${progressId} deleted`);
        }, 200);
    }
}

function refreshProgress() {
    // Recalculate all progress bars
    const progressRows = document.querySelectorAll('.progress-row');
    progressRows.forEach(row => {
        setupProgressCalculation(row);
        
        // Add refresh animation
        const progressBar = row.querySelector('.progress-fill');
        if (progressBar) {
            progressBar.style.animation = 'none';
            progressBar.offsetHeight; // Trigger reflow
            progressBar.style.animation = 'pulse 0.5s ease-in-out';
        }
    });
    
    console.log('🔄 Progress refreshed');
}

// ===== TIME OVERVIEW SECTION =====

function addTimeItem() {
    const timeTableBody = document.getElementById('time-table-body');
    const timeEmpty = document.getElementById('time-empty');
    
    if (timeTableBody) {
        // Hide empty state if visible
        if (timeEmpty) {
            timeEmpty.style.display = 'none';
        }
        
        const newTimeRow = document.createElement('div');
        newTimeRow.className = 'table-row time-row';
        newTimeRow.setAttribute('data-time-id', timeIdCounter);
        
        newTimeRow.innerHTML = `
            <div class="cell label-cell">
                <select class="time-type-select">
                    <option value="current">⏰ 현재 시간</option>
                    <option value="next" selected>📅 다음 일정</option>
                    <option value="deadline">⏳ 마감 시간</option>
                    <option value="reminder">🔔 알림</option>
                </select>
            </div>
            <div class="cell time-content-cell">
                <input type="text" class="time-content-input" placeholder="시간과 내용 입력..." autofocus>
            </div>
            <div class="cell action-cell">
                <button class="action-btn delete-time" onclick="deleteTime(${timeIdCounter})" title="삭제">🗑</button>
            </div>
        `;
        
        timeTableBody.appendChild(newTimeRow);
        
        // Focus on the new input
        const newInput = newTimeRow.querySelector('.time-content-input');
        if (newInput) {
            newInput.focus();
        }
        
        timeIdCounter++;
        console.log('✅ New time item added');
    }
}

function deleteTime(timeId) {
    const timeRow = document.querySelector(`[data-time-id="${timeId}"]`);
    const timeTableBody = document.getElementById('time-table-body');
    const timeEmpty = document.getElementById('time-empty');
    
    if (timeRow && confirm('이 시간 정보를 삭제하시겠습니까?')) {
        // Add deletion animation
        timeRow.style.transform = 'scale(0.9)';
        timeRow.style.opacity = '0.5';
        
        setTimeout(() => {
            timeRow.remove();
            
            // Show empty state if no time items remain
            const remainingTimes = timeTableBody.querySelectorAll('.time-row');
            if (remainingTimes.length === 0 && timeEmpty) {
                timeEmpty.style.display = 'flex';
            }
            
            console.log(`🗑 Time ${timeId} deleted`);
        }, 200);
    }
}

function syncCurrentTime() {
    // Update all current time displays
    const currentTimeDisplays = document.querySelectorAll('.time-display-live');
    const now = new Date();
    const hours = now.getHours().toString().padStart(2, '0');
    const minutes = now.getMinutes().toString().padStart(2, '0');
    const currentTimeString = `${hours}:${minutes}`;
    
    currentTimeDisplays.forEach(display => {
        display.textContent = currentTimeString;
        
        // Add sync animation
        display.style.color = '#10b981';
        display.style.transform = 'scale(1.1)';
        
        setTimeout(() => {
            display.style.color = '#3b82f6';
            display.style.transform = 'scale(1)';
        }, 500);
    });
    
    console.log('🕐 Current time synced');
}

// ===== DAILY ROUTINE SECTION =====

function deleteRoutine(routineId) {
    const routineRow = document.querySelector(`[data-routine-id="${routineId}"]`);
    const routineTableBody = document.getElementById('routine-table-body');
    const routineEmpty = document.getElementById('routine-empty');
    
    if (routineRow && confirm('이 루틴을 삭제하시겠습니까?')) {
        // Add deletion animation
        routineRow.style.transform = 'scale(0.9)';
        routineRow.style.opacity = '0.5';
        
        setTimeout(() => {
            routineRow.remove();
            
            // Show empty state if no routine items remain
            const remainingRoutines = routineTableBody.querySelectorAll('.routine-row');
            if (remainingRoutines.length === 0 && routineEmpty) {
                routineEmpty.style.display = 'flex';
            }
            
            // Update progress stats
            updateProgressStats();
            
            // Save to localStorage
            saveToLocalStorage();
            
            console.log(`🗑 Routine ${routineId} deleted`);
        }, 200);
    }
}

function clearAllRoutines() {
    const routineTableBody = document.getElementById('routine-table-body');
    const routineEmpty = document.getElementById('routine-empty');
    
    if (routineTableBody && confirm('모든 루틴을 삭제하시겠습니까?')) {
        // Add clearing animation
        const routineRows = routineTableBody.querySelectorAll('.routine-row');
        routineRows.forEach((row, index) => {
            setTimeout(() => {
                row.style.transform = 'translateX(-100%)';
                row.style.opacity = '0';
            }, index * 30);
        });
        
        setTimeout(() => {
            routineTableBody.innerHTML = '';
            if (routineEmpty) {
                routineEmpty.style.display = 'flex';
            }
            
            // Update progress stats
            updateProgressStats();
            
            // Save to localStorage
            saveToLocalStorage();
            
            console.log('🗑 All routines cleared');
        }, routineRows.length * 30 + 200);
    }
}

function sortRoutinesByTime() {
    const routineTableBody = document.getElementById('routine-table-body');
    
    if (routineTableBody) {
        const routineRows = Array.from(routineTableBody.querySelectorAll('.routine-row'));
        
        // Sort by time
        routineRows.sort((a, b) => {
            const timeA = a.querySelector('.time-input').value || '00:00';
            const timeB = b.querySelector('.time-input').value || '00:00';
            return timeA.localeCompare(timeB);
        });
        
        // Add sorting animation
        routineRows.forEach((row, index) => {
            setTimeout(() => {
                row.style.transform = 'translateY(-5px)';
                row.style.boxShadow = '0 4px 8px rgba(59, 130, 246, 0.2)';
                
                setTimeout(() => {
                    row.style.transform = 'translateY(0)';
                    row.style.boxShadow = '';
                }, 200);
                
                routineTableBody.appendChild(row);
            }, index * 50);
        });
        
        console.log('↕ Routines sorted by time');
    }
}

// Enhanced addRoutineItem function to work with new structure
function addRoutineItem() {
    const routineTableBody = document.getElementById('routine-table-body');
    const routineEmpty = document.getElementById('routine-empty');
    
    if (routineTableBody) {
        // Hide empty state if visible
        if (routineEmpty) {
            routineEmpty.style.display = 'none';
        }
        
        const newRoutineRow = document.createElement('div');
        newRoutineRow.className = 'table-row routine-row';
        newRoutineRow.draggable = true;
        newRoutineRow.setAttribute('data-routine-id', routineIdCounter);
        
        const now = new Date();
        const hours = now.getHours().toString().padStart(2, '0');
        const minutes = now.getMinutes().toString().padStart(2, '0');
        const defaultTime = `${hours}:${minutes}`;
        
        newRoutineRow.innerHTML = `
            <div class="cell time-cell">
                <input type="time" class="time-input" value="${defaultTime}">
            </div>
            <div class="cell activity-cell">
                <input type="text" class="activity-title-input" placeholder="활동명..." autofocus>
                <input type="text" class="activity-desc-input" placeholder="상세 설명...">
            </div>
            <div class="cell status-cell">
                <input type="checkbox" class="routine-checkbox">
            </div>
            <div class="cell action-cell">
                <button class="action-btn delete-routine" onclick="deleteRoutine(${routineIdCounter})" title="삭제">🗑</button>
            </div>
        `;
        
        routineTableBody.appendChild(newRoutineRow);
        
        // Setup interactions for new row
        setupRowDragAndDrop(newRoutineRow, 'routine');
        
        // Setup checkbox event listener
        const checkbox = newRoutineRow.querySelector('.routine-checkbox');
        checkbox.addEventListener('change', function() {
            updateProgressStats();
            saveToLocalStorage();
        });
        
        // Setup input change listeners for auto-save
        const inputs = newRoutineRow.querySelectorAll('input');
        inputs.forEach(input => {
            input.addEventListener('change', saveToLocalStorage);
            input.addEventListener('input', debounce(saveToLocalStorage, 500));
        });
        
        // Focus on the title input
        const titleInput = newRoutineRow.querySelector('.activity-title-input');
        if (titleInput) {
            titleInput.focus();
        }
        
        routineIdCounter++;
        
        // Save to localStorage
        saveToLocalStorage();
        console.log('✅ New routine added');
    }
}

// Initialize existing progress calculation for loaded items
document.addEventListener('DOMContentLoaded', function() {
    // Setup progress calculations for existing items
    document.querySelectorAll('.progress-row').forEach(row => {
        setupProgressCalculation(row);
    });
    
    // Show empty states if needed
    checkEmptyStates();
});

function checkEmptyStates() {
    // Check routine
    const routineTableBody = document.getElementById('routine-table-body');
    const routineEmpty = document.getElementById('routine-empty');
    if (routineTableBody && routineEmpty) {
        const routineRows = routineTableBody.querySelectorAll('.routine-row');
        if (routineRows.length === 0) {
            routineEmpty.style.display = 'flex';
        }
    }
    
    // Check tasks
    const tasksTableBody = document.getElementById('tasks-table-body');
    const tasksEmpty = document.getElementById('tasks-empty');
    if (tasksTableBody && tasksEmpty) {
        const taskRows = tasksTableBody.querySelectorAll('.task-row');
        if (taskRows.length === 0) {
            tasksEmpty.style.display = 'flex';
        }
    }
}

// ===== NEW FUNCTIONS FOR SIMPLIFIED LAYOUT =====

// Global counter for tasks
let taskIdCounter = 5;

// Daily Commitment functions
function saveCommitment() {
    const textarea = document.querySelector('.commitment-textarea');
    const saveBtn = document.querySelector('.btn-save-commitment');
    
    if (textarea && saveBtn) {
        // Save to localStorage
        saveToLocalStorage();
        console.log('💾 Saving commitment:', textarea.value);
        
        // Visual feedback
        const originalText = saveBtn.textContent;
        saveBtn.textContent = '✅ 저장 완료!';
        saveBtn.style.background = '#059669';
        
        setTimeout(() => {
            saveBtn.textContent = originalText;
            saveBtn.style.background = '';
        }, 2000);
    }
}

function clearCommitment() {
    const textarea = document.querySelector('.commitment-textarea');
    
    if (textarea && confirm('오늘의 다짐을 지우시겠습니까?')) {
        textarea.value = '';
        textarea.focus();
        
        // Save to localStorage
        saveToLocalStorage();
        console.log('🗑 Commitment cleared');
    }
}

// Enhanced addTaskItem function for new structure
function addTaskItem() {
    const tasksTableBody = document.getElementById('tasks-table-body');
    const tasksEmpty = document.getElementById('tasks-empty');
    
    if (tasksTableBody) {
        // Hide empty state if visible
        if (tasksEmpty) {
            tasksEmpty.style.display = 'none';
        }
        
        const newTaskRow = document.createElement('div');
        newTaskRow.className = 'table-row task-row';
        newTaskRow.draggable = true;
        newTaskRow.setAttribute('data-task-id', taskIdCounter);
        
        newTaskRow.innerHTML = `
            <div class="cell status-cell">
                <input type="checkbox" class="task-checkbox">
            </div>
            <div class="cell task-cell">
                <input type="text" class="task-title-input" placeholder="작업명..." autofocus>
                <input type="text" class="task-desc-input" placeholder="상세 설명...">
            </div>
            <div class="cell priority-cell">
                <select class="priority-select">
                    <option value="high">🔥 중요</option>
                    <option value="medium" selected>📋 보통</option>
                    <option value="low">📝 낮음</option>
                </select>
            </div>
            <div class="cell action-cell">
                <button class="action-btn delete-task" onclick="deleteTask(${taskIdCounter})" title="삭제">🗑</button>
            </div>
        `;
        
        tasksTableBody.appendChild(newTaskRow);
        
        // Setup interactions for new row
        setupRowDragAndDrop(newTaskRow, 'task');
        
        // Setup checkbox event listener
        const checkbox = newTaskRow.querySelector('.task-checkbox');
        checkbox.addEventListener('change', function() {
            const taskRow = this.closest('.table-row');
            
            if (this.checked) {
                taskRow.classList.add('completed');
                
                // Animate checkbox
                this.style.transform = 'scale(1.1)';
                setTimeout(() => {
                    this.style.transform = 'scale(1)';
                }, 200);
            } else {
                taskRow.classList.remove('completed');
            }
            
            // Save to localStorage
            saveToLocalStorage();
        });
        
        // Setup input change listeners for auto-save
        const inputs = newTaskRow.querySelectorAll('input, select');
        inputs.forEach(input => {
            input.addEventListener('change', saveToLocalStorage);
            input.addEventListener('input', debounce(saveToLocalStorage, 500));
        });
        
        // Focus on the title input
        const titleInput = newTaskRow.querySelector('.task-title-input');
        if (titleInput) {
            titleInput.focus();
        }
        
        taskIdCounter++;
        
        // Save to localStorage
        saveToLocalStorage();
        console.log('✅ New task added');
    }
}

function deleteTask(taskId) {
    const taskRow = document.querySelector(`[data-task-id="${taskId}"]`);
    const tasksTableBody = document.getElementById('tasks-table-body');
    const tasksEmpty = document.getElementById('tasks-empty');
    
    if (taskRow && confirm('이 작업을 삭제하시겠습니까?')) {
        // Add deletion animation
        taskRow.style.transform = 'scale(0.9)';
        taskRow.style.opacity = '0.5';
        
        setTimeout(() => {
            taskRow.remove();
            
            // Show empty state if no task items remain
            const remainingTasks = tasksTableBody.querySelectorAll('.task-row');
            if (remainingTasks.length === 0 && tasksEmpty) {
                tasksEmpty.style.display = 'flex';
            }
            
            // Save to localStorage
            saveToLocalStorage();
            console.log(`🗑 Task ${taskId} deleted`);
        }, 200);
    }
}

function clearAllTasks() {
    const tasksTableBody = document.getElementById('tasks-table-body');
    const tasksEmpty = document.getElementById('tasks-empty');
    
    if (tasksTableBody && confirm('모든 작업을 삭제하시겠습니까?')) {
        // Add clearing animation
        const taskRows = tasksTableBody.querySelectorAll('.task-row');
        taskRows.forEach((row, index) => {
            setTimeout(() => {
                row.style.transform = 'translateX(-100%)';
                row.style.opacity = '0';
            }, index * 30);
        });
        
        setTimeout(() => {
            tasksTableBody.innerHTML = '';
            if (tasksEmpty) {
                tasksEmpty.style.display = 'flex';
            }
            
            // Save to localStorage
            saveToLocalStorage();
            console.log('🗑 All tasks cleared');
        }, taskRows.length * 30 + 200);
    }
}

// Update header current time
function updateHeaderCurrentTime() {
    const headerTimeDisplay = document.getElementById('header-current-time');
    if (headerTimeDisplay) {
        const now = new Date();
        const hours = now.getHours().toString().padStart(2, '0');
        const minutes = now.getMinutes().toString().padStart(2, '0');
        headerTimeDisplay.textContent = `${hours}:${minutes}`;
    }
}

// Initialize header time updates
document.addEventListener('DOMContentLoaded', function() {
    updateHeaderCurrentTime();
    setInterval(updateHeaderCurrentTime, 60000); // Update every minute
});

/* ============================================================================
   LOCALSTORAGE FUNCTIONS FOR DATA PERSISTENCE
   ============================================================================ */

// Get storage key based on calendar and date
function getStorageKey() {
    return `calendar-day-${calendarId}-${selectedDate}`;
}

// Save all data to localStorage
function saveToLocalStorage() {
    const data = {
        commitment: document.querySelector('.commitment-textarea')?.value || '',
        routines: [],
        tasks: []
    };
    
    // Save routines
    const routineRows = document.querySelectorAll('.routine-row');
    routineRows.forEach((row) => {
        const routineId = row.getAttribute('data-routine-id');
        const timeInput = row.querySelector('.time-input');
        const titleInput = row.querySelector('.activity-title-input');
        const descInput = row.querySelector('.activity-desc-input');
        const checkbox = row.querySelector('.routine-checkbox');
        
        if (timeInput && titleInput && descInput && checkbox) {
            data.routines.push({
                id: routineId,
                time: timeInput.value,
                title: titleInput.value,
                description: descInput.value,
                completed: checkbox.checked
            });
        }
    });
    
    // Save tasks
    const taskRows = document.querySelectorAll('.task-row');
    taskRows.forEach((row) => {
        const taskId = row.getAttribute('data-task-id');
        const titleInput = row.querySelector('.task-title-input');
        const descInput = row.querySelector('.task-desc-input');
        const prioritySelect = row.querySelector('.priority-select');
        const checkbox = row.querySelector('.task-checkbox');
        
        if (titleInput && descInput && prioritySelect && checkbox) {
            data.tasks.push({
                id: taskId,
                title: titleInput.value,
                description: descInput.value,
                priority: prioritySelect.value,
                completed: checkbox.checked
            });
        }
    });
    
    localStorage.setItem(getStorageKey(), JSON.stringify(data));
    
    // Update weekly calendar with new commitment
    updateCurrentDayCommitment(data.commitment);
    
    console.log('💾 Data saved to localStorage');
}

// Update current day's commitment in weekly calendar
function updateCurrentDayCommitment(commitment) {
    if (commitment && commitment.trim()) {
        // Today gets the default yellow sticky note
        updateDayCommitment(selectedDate, commitment, '');
    } else {
        // Clear the commitment
        const dayContent = document.getElementById(`day-content-${selectedDate}`);
        if (dayContent) {
            dayContent.innerHTML = `<div class="empty-day-message">다짐을 적어보세요</div>`;
        }
    }
}

// Load saved data from localStorage
function loadSavedData() {
    const storageKey = getStorageKey();
    const savedData = localStorage.getItem(storageKey);
    
    if (savedData) {
        try {
            const data = JSON.parse(savedData);
            console.log('📂 Loading saved data:', data);
            
            // Load commitment
            if (data.commitment) {
                const commitmentTextarea = document.querySelector('.commitment-textarea');
                if (commitmentTextarea) {
                    commitmentTextarea.value = data.commitment;
                }
            }
            
            // Load routines
            if (data.routines && data.routines.length > 0) {
                const routineTableBody = document.getElementById('routine-table-body');
                const routineEmpty = document.getElementById('routine-empty');
                
                if (routineTableBody) {
                    routineTableBody.innerHTML = '';
                    
                    data.routines.forEach((routine) => {
                        createRoutineRow(routine);
                    });
                    
                    if (routineEmpty) {
                        routineEmpty.style.display = 'none';
                    }
                }
            }
            
            // Load tasks
            if (data.tasks && data.tasks.length > 0) {
                const tasksTableBody = document.getElementById('tasks-table-body');
                const tasksEmpty = document.getElementById('tasks-empty');
                
                if (tasksTableBody) {
                    tasksTableBody.innerHTML = '';
                    
                    data.tasks.forEach((task) => {
                        createTaskRow(task);
                    });
                    
                    if (tasksEmpty) {
                        tasksEmpty.style.display = 'none';
                    }
                }
            }
            
            // Update ID counters
            if (data.routines.length > 0) {
                const maxRoutineId = Math.max(...data.routines.map(r => parseInt(r.id))) + 1;
                routineIdCounter = maxRoutineId;
            }
            
            if (data.tasks.length > 0) {
                const maxTaskId = Math.max(...data.tasks.map(t => parseInt(t.id))) + 1;
                taskIdCounter = maxTaskId;
            }
            
        } catch (e) {
            console.error('Error loading saved data:', e);
        }
    }
    
    // Always check empty states after loading
    checkEmptyStates();
}

// Create routine row from data
function createRoutineRow(routine) {
    const routineTableBody = document.getElementById('routine-table-body');
    if (!routineTableBody) return;
    
    const newRoutineRow = document.createElement('div');
    newRoutineRow.className = 'table-row routine-row';
    newRoutineRow.draggable = true;
    newRoutineRow.setAttribute('data-routine-id', routine.id);
    
    newRoutineRow.innerHTML = `
        <div class="cell time-cell">
            <input type="time" class="time-input" value="${routine.time}">
        </div>
        <div class="cell activity-cell">
            <input type="text" class="activity-title-input" value="${routine.title}" placeholder="활동명...">
            <input type="text" class="activity-desc-input" value="${routine.description}" placeholder="상세 설명...">
        </div>
        <div class="cell status-cell">
            <input type="checkbox" class="routine-checkbox" ${routine.completed ? 'checked' : ''}>
        </div>
        <div class="cell action-cell">
            <button class="action-btn delete-routine" onclick="deleteRoutine(${routine.id})" title="삭제">🗑</button>
        </div>
    `;
    
    routineTableBody.appendChild(newRoutineRow);
    
    // Setup interactions for loaded row
    setupRowDragAndDrop(newRoutineRow, 'routine');
    
    // Setup checkbox event listener
    const checkbox = newRoutineRow.querySelector('.routine-checkbox');
    checkbox.addEventListener('change', function() {
        saveToLocalStorage();
    });
    
    // Setup input change listeners
    const inputs = newRoutineRow.querySelectorAll('input');
    inputs.forEach(input => {
        input.addEventListener('change', saveToLocalStorage);
        input.addEventListener('input', debounce(saveToLocalStorage, 500));
    });
}

// Create task row from data
function createTaskRow(task) {
    const tasksTableBody = document.getElementById('tasks-table-body');
    if (!tasksTableBody) return;
    
    const newTaskRow = document.createElement('div');
    newTaskRow.className = `table-row task-row ${task.completed ? 'completed' : ''}`;
    newTaskRow.draggable = true;
    newTaskRow.setAttribute('data-task-id', task.id);
    
    newTaskRow.innerHTML = `
        <div class="cell status-cell">
            <input type="checkbox" class="task-checkbox" ${task.completed ? 'checked' : ''}>
        </div>
        <div class="cell task-cell">
            <input type="text" class="task-title-input" value="${task.title}" placeholder="작업명...">
            <input type="text" class="task-desc-input" value="${task.description}" placeholder="상세 설명...">
        </div>
        <div class="cell priority-cell">
            <select class="priority-select">
                <option value="high" ${task.priority === 'high' ? 'selected' : ''}>🔥 중요</option>
                <option value="medium" ${task.priority === 'medium' ? 'selected' : ''}>📋 보통</option>
                <option value="low" ${task.priority === 'low' ? 'selected' : ''}>📝 낮음</option>
            </select>
        </div>
        <div class="cell action-cell">
            <button class="action-btn delete-task" onclick="deleteTask(${task.id})" title="삭제">🗑</button>
        </div>
    `;
    
    tasksTableBody.appendChild(newTaskRow);
    
    // Setup interactions for loaded row
    setupRowDragAndDrop(newTaskRow, 'task');
    
    // Setup checkbox event listener
    const checkbox = newTaskRow.querySelector('.task-checkbox');
    checkbox.addEventListener('change', function() {
        const taskRow = this.closest('.table-row');
        
        if (this.checked) {
            taskRow.classList.add('completed');
            
            // Animate checkbox
            this.style.transform = 'scale(1.1)';
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 200);
        } else {
            taskRow.classList.remove('completed');
        }
        
        saveToLocalStorage();
    });
    
    // Setup input change listeners
    const inputs = newTaskRow.querySelectorAll('input, select');
    inputs.forEach(input => {
        input.addEventListener('change', saveToLocalStorage);
        input.addEventListener('input', debounce(saveToLocalStorage, 500));
    });
}

// Setup auto-save on input changes
function setupAutoSave() {
    // Auto-save commitment
    const commitmentTextarea = document.querySelector('.commitment-textarea');
    if (commitmentTextarea) {
        commitmentTextarea.addEventListener('input', debounce(saveToLocalStorage, 1000));
    }
}

// Debounce function to limit save frequency
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/* ============================================================================
   WEEKLY CALENDAR FUNCTIONS
   ============================================================================ */

// Generate weekly calendar view
function generateWeeklyCalendar() {
    const weekGrid = document.getElementById('week-grid');
    if (!weekGrid) return;
    
    const currentDate = new Date(selectedDate);
    const startOfWeek = getStartOfWeek(currentDate);
    
    const dayNames = ['일', '월', '화', '수', '목', '금', '토'];
    const variants = ['', 'variant-blue', 'variant-green', 'variant-pink'];
    
    weekGrid.innerHTML = '';
    
    for (let i = 0; i < 7; i++) {
        const dayDate = new Date(startOfWeek);
        dayDate.setDate(startOfWeek.getDate() + i);
        
        const dateString = formatDateForStorage(dayDate);
        const isToday = dateString === selectedDate;
        
        const dayCell = document.createElement('div');
        dayCell.className = `day-cell ${isToday ? 'today' : ''}`;
        dayCell.setAttribute('data-date', dateString);
        
        dayCell.innerHTML = `
            <div class="day-header">
                <div class="day-name">${dayNames[i]}</div>
                <div class="day-date">${dayDate.getDate()}</div>
            </div>
            <div class="day-content" id="day-content-${dateString}">
                <div class="empty-day-message">다짐을 적어보세요</div>
            </div>
        `;
        
        // Add click handler to navigate to that day
        dayCell.addEventListener('click', () => {
            if (!isToday) {
                window.location.href = `/dashboard/calendar/${calendarId}/day/${dateString}`;
            }
        });
        
        weekGrid.appendChild(dayCell);
    }
    
    // Load commitments for all days in the week
    loadWeeklyCommitments(startOfWeek);
}

// Get start of week (Sunday)
function getStartOfWeek(date) {
    const d = new Date(date);
    const day = d.getDay();
    const diff = d.getDate() - day;
    return new Date(d.setDate(diff));
}

// Format date for storage key
function formatDateForStorage(date) {
    return date.toISOString().split('T')[0];
}

// Load commitments for the entire week
function loadWeeklyCommitments(startOfWeek) {
    const variants = ['', 'variant-blue', 'variant-green', 'variant-pink'];
    
    for (let i = 0; i < 7; i++) {
        const dayDate = new Date(startOfWeek);
        dayDate.setDate(startOfWeek.getDate() + i);
        const dateString = formatDateForStorage(dayDate);
        
        // Get commitment for this date
        const storageKey = `calendar-day-${calendarId}-${dateString}`;
        const savedData = localStorage.getItem(storageKey);
        
        if (savedData) {
            try {
                const data = JSON.parse(savedData);
                if (data.commitment && data.commitment.trim()) {
                    updateDayCommitment(dateString, data.commitment, variants[i % variants.length]);
                }
            } catch (e) {
                console.error('Error loading commitment for date:', dateString, e);
            }
        }
    }
}

// Update commitment display for a specific day
function updateDayCommitment(dateString, commitment, variant = '') {
    const dayContent = document.getElementById(`day-content-${dateString}`);
    if (!dayContent) return;
    
    // Truncate long commitments for display
    const displayText = commitment.length > 50 ? commitment.substring(0, 47) + '...' : commitment;
    
    dayContent.innerHTML = `
        <div class="commitment-sticky ${variant}">
            ${displayText}
        </div>
    `;
}

// Update weekly calendar when commitment changes
function updateWeeklyCalendar() {
    const currentDate = new Date(selectedDate);
    const startOfWeek = getStartOfWeek(currentDate);
    loadWeeklyCommitments(startOfWeek);
}

// ==================== 날씨 시스템 ====================

// 날씨 데이터 로드 함수
async function loadWeatherData() {
    try {
        console.log('🌤️ Loading weather data...');
        
        // 서울 날씨 정보 가져오기 (기본값)
        const response = await fetch('/api/weather/Seoul');
        const data = await response.json();
        
        if (data.success) {
            console.log('✅ Weather data loaded:', data.weather);
            displayWeatherInCalendar(data.weather);
            
            // 날씨 데이터를 전역 변수에 저장
            window.weeklyWeatherData = data.weather;
        } else {
            console.warn('⚠️ Failed to load weather data, using fallback');
            displayFallbackWeather();
        }
    } catch (error) {
        console.error('❌ Error loading weather data:', error);
        displayFallbackWeather();
    }
}

// 주간 캘린더에 날씨 정보 표시
function displayWeatherInCalendar(weatherData) {
    const weekGrid = document.getElementById('week-grid');
    if (!weekGrid) return;
    
    const dayCells = weekGrid.querySelectorAll('.day-cell');
    
    dayCells.forEach((cell, index) => {
        const dateStr = cell.dataset.date;
        
        // 해당 날짜의 날씨 정보 찾기
        const weatherInfo = weatherData.find(w => w.date === dateStr);
        
        if (weatherInfo) {
            // 기존 날씨 위젯 제거
            const existingWeather = cell.querySelector('.day-weather');
            if (existingWeather) {
                existingWeather.remove();
            }
            
            // 새로운 날씨 위젯 생성
            const weatherWidget = createWeatherWidget(weatherInfo);
            
            // 날짜 정보 뒤에 삽입
            const dayDate = cell.querySelector('.day-date');
            if (dayDate) {
                dayDate.insertAdjacentElement('afterend', weatherWidget);
            }
        }
    });
}

// 날씨 위젯 생성
function createWeatherWidget(weatherInfo) {
    const weatherDiv = document.createElement('div');
    weatherDiv.className = 'day-weather';
    
    // 날씨 상태에 따른 데이터 속성 추가 (CSS 스타일링용)
    if (weatherInfo.weather) {
        weatherDiv.setAttribute('data-weather', weatherInfo.weather);
    }
    
    // 날씨 정보에 따른 툴팁 추가
    const weatherName = getWeatherNameInKorean(weatherInfo.weather || 'Clear');
    weatherDiv.title = `${weatherName} ${weatherInfo.temp}°C`;
    
    weatherDiv.innerHTML = `
        <div class="weather-emoji">${weatherInfo.emoji}</div>
        <div class="weather-temp">${weatherInfo.temp}°</div>
    `;
    
    return weatherDiv;
}

// 날씨 상태를 한국어로 변환
function getWeatherNameInKorean(weatherMain) {
    const weatherNames = {
        'Clear': '맑음',
        'Clouds': '흐림',
        'Rain': '비',
        'Drizzle': '이슬비',
        'Thunderstorm': '뇌우',
        'Snow': '눈',
        'Mist': '안개',
        'Fog': '짙은 안개',
        'Haze': '실안개',
        'Dust': '황사',
        'Sand': '모래바람',
        'Ash': '재',
        'Squall': '돌풍',
        'Tornado': '토네이도'
    };
    
    return weatherNames[weatherMain] || '알 수 없음';
}

// 폴백 날씨 표시 (API 실패 시)
function displayFallbackWeather() {
    const fallbackWeather = [
        { emoji: '☀️', temp: 15 },
        { emoji: '☁️', temp: 12 },
        { emoji: '🌧️', temp: 8 },
        { emoji: '☀️', temp: 18 },
        { emoji: '☁️', temp: 14 },
        { emoji: '☀️', temp: 16 },
        { emoji: '🌦️', temp: 10 }
    ];
    
    const weekGrid = document.getElementById('week-grid');
    if (!weekGrid) return;
    
    const dayCells = weekGrid.querySelectorAll('.day-cell');
    
    dayCells.forEach((cell, index) => {
        if (index < fallbackWeather.length) {
            const weather = fallbackWeather[index];
            
            // 기존 날씨 위젯 제거
            const existingWeather = cell.querySelector('.day-weather');
            if (existingWeather) {
                existingWeather.remove();
            }
            
            // 새로운 날씨 위젯 생성
            const weatherWidget = createWeatherWidget(weather);
            
            // 날짜 정보 뒤에 삽입
            const dayDate = cell.querySelector('.day-date');
            if (dayDate) {
                dayDate.insertAdjacentElement('afterend', weatherWidget);
            }
        }
    });
}

// 날씨 데이터 새로고침
function refreshWeatherData() {
    loadWeatherData();
}

// ==================== 시간 하이라이트 시스템 ====================

// 시간 하이라이트 전역 변수
let currentHighlightedTime = null;

// 시간 클릭 이벤트 설정
function setupTimeClickHandlers() {
    // 모든 루틴 행에 시간 클릭 이벤트 추가
    const routineTableBody = document.getElementById('routine-table-body');
    if (routineTableBody) {
        routineTableBody.addEventListener('click', function(e) {
            const timeElement = e.target.closest('.routine-time');
            if (timeElement) {
                const routineRow = timeElement.closest('.routine-row');
                if (routineRow) {
                    const timeText = timeElement.textContent.trim();
                    highlightTimeSlot(timeText, routineRow);
                }
            }
        });
    }
}

// 시간대 하이라이트 함수
function highlightTimeSlot(timeText, routineRow) {
    console.log(`🕐 시간 선택: ${timeText}`);
    
    // 이전 하이라이트 제거
    clearTimeHighlight();
    
    // 새로운 하이라이트 적용
    routineRow.classList.add('time-highlighted');
    currentHighlightedTime = {
        time: timeText,
        element: routineRow
    };
    
    // 5초 후 자동으로 하이라이트 제거
    setTimeout(() => {
        if (currentHighlightedTime && currentHighlightedTime.element === routineRow) {
            clearTimeHighlight();
        }
    }, 5000);
    
    // 시간 선택 피드백 표시
    showTimeSelectedFeedback(timeText);
}

// 시간 하이라이트 제거
function clearTimeHighlight() {
    if (currentHighlightedTime) {
        currentHighlightedTime.element.classList.remove('time-highlighted');
        currentHighlightedTime = null;
    }
    
    // 모든 하이라이트 제거 (안전장치)
    document.querySelectorAll('.routine-row.time-highlighted').forEach(row => {
        row.classList.remove('time-highlighted');
    });
}

// 시간 선택 피드백 표시
function showTimeSelectedFeedback(timeText) {
    // 기존 피드백 제거
    const existingFeedback = document.querySelector('.time-feedback');
    if (existingFeedback) {
        existingFeedback.remove();
    }
    
    // 새 피드백 생성
    const feedback = document.createElement('div');
    feedback.className = 'time-feedback';
    feedback.innerHTML = `
        <div class="feedback-content">
            <div class="feedback-icon">🕐</div>
            <div class="feedback-text">${timeText} 선택됨</div>
        </div>
    `;
    
    // 페이지에 추가
    document.body.appendChild(feedback);
    
    // 애니메이션 후 제거
    setTimeout(() => {
        feedback.style.opacity = '0';
        feedback.style.transform = 'translateY(-20px)';
        setTimeout(() => {
            if (feedback.parentNode) {
                feedback.parentNode.removeChild(feedback);
            }
        }, 300);
    }, 2000);
}

// 동적으로 추가된 루틴에도 시간 클릭 핸들러 적용
function refreshTimeClickHandlers() {
    setupTimeClickHandlers();
}