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
    
    // Set default datetime values for event modal
    initializeEventModal();
    
    // Load events and tasks for the selected date
    loadDayEvents();
    loadDayTasks();
    
    // Setup event listeners
    setupEventListeners();
});

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
    
    // Routine checkboxes
    const routineCheckboxes = document.querySelectorAll('.routine-checkbox');
    routineCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const routineItem = this.closest('.routine-item');
            if (this.checked) {
                routineItem.style.opacity = '0.7';
                console.log('✅ Routine item completed');
            } else {
                routineItem.style.opacity = '1';
            }
        });
    });
    
    // Task checkboxes
    const taskCheckboxes = document.querySelectorAll('.task-checkbox');
    taskCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const taskItem = this.closest('.task-item');
            if (this.checked) {
                taskItem.classList.add('completed');
                console.log('✅ Task completed');
            } else {
                taskItem.classList.remove('completed');
            }
        });
    });
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
    const time = prompt('시간을 입력하세요 (예: 14:30):');
    const task = prompt('할 일을 입력하세요:');
    const description = prompt('설명을 입력하세요 (선택사항):');
    
    if (time && task) {
        const routineTimeline = document.querySelector('.routine-timeline');
        if (routineTimeline) {
            const newRoutineItem = document.createElement('div');
            newRoutineItem.className = 'routine-item';
            newRoutineItem.innerHTML = `
                <div class="routine-time">${time}</div>
                <div class="routine-content">
                    <div class="routine-task">${task}</div>
                    <div class="routine-description">${description || ''}</div>
                </div>
                <div class="routine-status">
                    <input type="checkbox" class="routine-checkbox">
                </div>
            `;
            
            routineTimeline.appendChild(newRoutineItem);
            
            // Add event listener to new checkbox
            const newCheckbox = newRoutineItem.querySelector('.routine-checkbox');
            newCheckbox.addEventListener('change', function() {
                if (this.checked) {
                    newRoutineItem.style.opacity = '0.7';
                } else {
                    newRoutineItem.style.opacity = '1';
                }
            });
            
            console.log('➕ Added new routine item');
        }
    }
}

// Add task item
function addTaskItem() {
    const title = prompt('할 일 제목을 입력하세요:');
    const description = prompt('설명을 입력하세요 (선택사항):');
    const priority = prompt('우선순위를 입력하세요 (high/medium/low):', 'medium');
    
    if (title) {
        const taskList = document.getElementById('task-list');
        if (taskList) {
            const newTaskItem = document.createElement('div');
            newTaskItem.className = 'task-item';
            
            const priorityText = priority === 'high' ? '중요' : priority === 'low' ? '낮음' : '보통';
            
            newTaskItem.innerHTML = `
                <input type="checkbox" class="task-checkbox">
                <div class="task-content">
                    <div class="task-title">${title}</div>
                    <div class="task-description">${description || ''}</div>
                </div>
                <div class="task-priority ${priority}">${priorityText}</div>
            `;
            
            taskList.appendChild(newTaskItem);
            
            // Add event listener to new checkbox
            const newCheckbox = newTaskItem.querySelector('.task-checkbox');
            newCheckbox.addEventListener('change', function() {
                if (this.checked) {
                    newTaskItem.classList.add('completed');
                } else {
                    newTaskItem.classList.remove('completed');
                }
            });
            
            console.log('➕ Added new task item');
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