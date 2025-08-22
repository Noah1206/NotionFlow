// Friends Page JavaScript

// Global variables
let currentUser = null;
let friends = [];
let friendCalendars = [];
let currentPage = 1;
const itemsPerPage = 10;

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    await loadCurrentUser();
    await loadFriends();
    await loadMyCalendars();
    await loadSharedCalendars();
    await loadFriendCalendars();
    initializeEventListeners();
    checkFriendRequests();
});

// Load current user
async function loadCurrentUser() {
    try {
        const response = await fetch('/api/user/profile', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (response.ok) {
            currentUser = await response.json();
        }
    } catch (error) {
        console.error('Error loading user:', error);
    }
}

// Load friends list
async function loadFriends() {
    try {
        const response = await fetch('/api/friends', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (response.ok) {
            friends = await response.json();
            renderStoryBar();
            updateFilterOptions();
        }
    } catch (error) {
        console.error('Error loading friends:', error);
        showNotification('친구 목록을 불러오는데 실패했습니다.', 'error');
    }
}

// Load friend calendars
async function loadFriendCalendars() {
    try {
        const response = await fetch('/api/friends/calendars', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (response.ok) {
            friendCalendars = await response.json();
            renderCalendarTable();
            updateStats();
        }
    } catch (error) {
        console.error('Error loading friend calendars:', error);
        showNotification('캘린더 목록을 불러오는데 실패했습니다.', 'error');
    }
}

// Render Instagram-style story bar
function renderStoryBar() {
    const storyList = document.getElementById('story-list');
    const myStory = storyList.querySelector('.my-story');
    
    // Clear existing friend stories
    const existingStories = storyList.querySelectorAll('.story-item:not(.my-story)');
    existingStories.forEach(story => story.remove());
    
    // Add friend stories
    friends.forEach(friend => {
        const hasPublicCalendars = friend.public_calendars > 0;
        const storyItem = document.createElement('div');
        storyItem.className = `story-item ${friend.viewed ? 'viewed' : ''}`;
        storyItem.onclick = () => viewFriendCalendars(friend.id);
        
        storyItem.innerHTML = `
            <div class="story-avatar ${hasPublicCalendars ? '' : 'viewed'}">
                <img src="${friend.avatar || '/static/images/default-avatar.png'}" 
                     alt="${friend.name}"
                     onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iMTIiIGN5PSI4IiByPSI0IiBmaWxsPSIjOTk5Ii8+CjxwYXRoIGQ9Ik0yMCAyMGMwLTUuNS0zLjUtMTAtOC0xMHMtOCA0LjUtOCAxMCIgZmlsbD0iIzk5OSIvPgo8L3N2Zz4K';">
            </div>
            <span class="story-name">${friend.name}</span>
        `;
        
        storyList.appendChild(storyItem);
    });
    
    // Check if scrolling is needed
    checkStoryScroll();
}

// Check if story scrolling buttons are needed
function checkStoryScroll() {
    const storyList = document.getElementById('story-list');
    const scrollContainer = storyList.parentElement;
    const prevBtn = scrollContainer.querySelector('.prev');
    const nextBtn = scrollContainer.querySelector('.next');
    
    if (storyList.scrollWidth > scrollContainer.clientWidth) {
        nextBtn.style.display = 'flex';
        
        storyList.addEventListener('scroll', () => {
            prevBtn.style.display = storyList.scrollLeft > 0 ? 'flex' : 'none';
            nextBtn.style.display = 
                storyList.scrollLeft < storyList.scrollWidth - scrollContainer.clientWidth 
                ? 'flex' : 'none';
        });
    }
}

// Scroll stories
function scrollStories(direction) {
    const storyList = document.getElementById('story-list');
    const scrollAmount = 200;
    
    if (direction === 'prev') {
        storyList.scrollLeft -= scrollAmount;
    } else {
        storyList.scrollLeft += scrollAmount;
    }
}

// View friend's calendars
async function viewFriendCalendars(friendId) {
    // Filter calendars by friend
    const filtered = friendCalendars.filter(cal => cal.owner_id === friendId);
    renderCalendarTable(filtered);
    
    // Mark friend as viewed
    const friend = friends.find(f => f.id === friendId);
    if (friend) {
        friend.viewed = true;
        renderStoryBar();
    }
    
    // Update filter
    document.getElementById('filter-friend').value = friendId;
}

// Render calendar table
function renderCalendarTable(calendars = null) {
    const tbody = document.getElementById('calendar-table-body');
    const calendarsToRender = calendars || friendCalendars;
    
    // Apply pagination
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const paginatedCalendars = calendarsToRender.slice(startIndex, endIndex);
    
    if (paginatedCalendars.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="empty-state">
                    <div class="empty-icon">📅</div>
                    <div class="empty-title">아직 공개된 캘린더가 없습니다</div>
                    <div class="empty-description">친구들이 캘린더를 공개하면 여기에 표시됩니다.</div>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = paginatedCalendars.map(calendar => {
        const friend = friends.find(f => f.id === calendar.owner_id) || {};
        const updateTime = formatTimeAgo(calendar.updated_at);
        
        return `
            <tr class="calendar-row" data-calendar-id="${calendar.id}">
                <td>
                    <input type="checkbox" class="select-calendar">
                </td>
                <td>
                    <div class="friend-avatar-small">
                        <img src="${friend.avatar || '/static/images/default-avatar.png'}" 
                             alt="${friend.name || 'Unknown'}"
                             onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAiIGhlaWdodD0iMzAiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iMTIiIGN5PSI4IiByPSI0IiBmaWxsPSIjOTk5Ii8+CjxwYXRoIGQ9Ik0yMCAyMGMwLTUuNS0zLjUtMTAtOC0xMHMtOCA0LjUtOCAxMCIgZmlsbD0iIzk5OSIvPgo8L3N2Zz4K';">
                    </div>
                </td>
                <td>
                    <div class="calendar-name-cell">
                        <div class="calendar-color-dot" style="background: ${calendar.color || '#3B82F6'};"></div>
                        <span class="calendar-name">${calendar.name}</span>
                    </div>
                </td>
                <td>
                    <span class="calendar-type-badge ${calendar.type || 'personal'}">${getCalendarTypeName(calendar.type)}</span>
                </td>
                <td>
                    <span class="update-time">${updateTime}</span>
                </td>
                <td>
                    <span class="event-count">${calendar.event_count || 0}</span>
                </td>
                <td>
                    <span class="share-status ${calendar.is_public ? 'public' : 'private'}">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                            ${calendar.is_public ? 
                                '<path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.94-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>' :
                                '<path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z"/>'
                            }
                        </svg>
                        ${calendar.is_public ? '공개' : '비공개'}
                    </span>
                </td>
                <td>
                    <button class="btn-view-calendar" onclick="viewCalendarDetail('${calendar.id}')">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                            <circle cx="12" cy="12" r="3"/>
                        </svg>
                        보기
                    </button>
                </td>
            </tr>
        `;
    }).join('');
    
    // Update pagination info
    updatePagination(calendarsToRender.length);
}

// View calendar detail
async function viewCalendarDetail(calendarId) {
    try {
        // Navigate to calendar detail page
        window.location.href = `/calendar/${calendarId}`;
    } catch (error) {
        console.error('Error viewing calendar:', error);
        showNotification('캘린더를 불러오는데 실패했습니다.', 'error');
    }
}

// Update filter options
function updateFilterOptions() {
    const filterSelect = document.getElementById('filter-friend');
    
    // Clear existing options except "All"
    filterSelect.innerHTML = '<option value="">모든 친구</option>';
    
    // Add friend options
    friends.forEach(friend => {
        const option = document.createElement('option');
        option.value = friend.id;
        option.textContent = friend.name;
        filterSelect.appendChild(option);
    });
}

// Update statistics
function updateStats() {
    const stats = {
        friends: friends.length,
        publicCalendars: friendCalendars.filter(c => c.is_public).length,
        totalEvents: friendCalendars.reduce((sum, c) => sum + (c.event_count || 0), 0),
        sharing: friendCalendars.filter(c => c.is_shared).length
    };
    
    // Update stat cards
    document.querySelectorAll('.stat-card').forEach((card, index) => {
        const value = card.querySelector('.stat-value');
        if (value) {
            switch(index) {
                case 0: value.textContent = stats.friends; break;
                case 1: value.textContent = stats.publicCalendars; break;
                case 2: value.textContent = stats.totalEvents; break;
                case 3: value.textContent = stats.sharing; break;
            }
        }
    });
}

// Check friend requests
async function checkFriendRequests() {
    try {
        const response = await fetch('/api/friends/requests', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (response.ok) {
            const requests = await response.json();
            const badge = document.getElementById('request-count');
            
            if (requests.length > 0) {
                badge.textContent = requests.length;
                badge.style.display = 'flex';
            } else {
                badge.style.display = 'none';
            }
        }
    } catch (error) {
        console.error('Error checking friend requests:', error);
    }
}

// Initialize event listeners
function initializeEventListeners() {
    // Search input
    const searchInput = document.getElementById('calendar-search');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(filterCalendars, 300));
    }
    
    // Filter selects
    document.getElementById('filter-friend')?.addEventListener('change', filterCalendars);
    document.getElementById('filter-type')?.addEventListener('change', filterCalendars);
}

// Filter calendars
function filterCalendars() {
    const searchTerm = document.getElementById('calendar-search').value.toLowerCase();
    const friendFilter = document.getElementById('filter-friend').value;
    const typeFilter = document.getElementById('filter-type').value;
    
    let filtered = friendCalendars;
    
    // Apply search filter
    if (searchTerm) {
        filtered = filtered.filter(cal => 
            cal.name.toLowerCase().includes(searchTerm) ||
            cal.description?.toLowerCase().includes(searchTerm)
        );
    }
    
    // Apply friend filter
    if (friendFilter) {
        filtered = filtered.filter(cal => cal.owner_id === friendFilter);
    }
    
    // Apply type filter
    if (typeFilter) {
        filtered = filtered.filter(cal => cal.type === typeFilter);
    }
    
    // Reset to first page
    currentPage = 1;
    
    // Render filtered results
    renderCalendarTable(filtered);
}

// Toggle select all
function toggleSelectAll() {
    const selectAll = document.getElementById('select-all');
    const checkboxes = document.querySelectorAll('.select-calendar');
    
    checkboxes.forEach(checkbox => {
        checkbox.checked = selectAll.checked;
    });
}

// Change page
function changePage(direction) {
    const totalPages = Math.ceil(friendCalendars.length / itemsPerPage);
    
    if (direction === 'prev' && currentPage > 1) {
        currentPage--;
    } else if (direction === 'next' && currentPage < totalPages) {
        currentPage++;
    }
    
    renderCalendarTable();
}

// Update pagination display
function updatePagination(totalItems) {
    const totalPages = Math.ceil(totalItems / itemsPerPage);
    const pageInfo = document.querySelector('.page-info');
    
    if (pageInfo) {
        pageInfo.textContent = `${currentPage} / ${totalPages}`;
    }
}

// Modal functions
function openAddFriendModal() {
    document.getElementById('add-friend-modal').style.display = 'flex';
}

function closeAddFriendModal() {
    document.getElementById('add-friend-modal').style.display = 'none';
    document.getElementById('friend-email').value = '';
    document.getElementById('search-result').style.display = 'none';
}

function openFriendRequests() {
    document.getElementById('friend-requests-modal').style.display = 'flex';
    loadFriendRequests();
}

function closeFriendRequests() {
    document.getElementById('friend-requests-modal').style.display = 'none';
}

// Load friend requests
async function loadFriendRequests() {
    try {
        const response = await fetch('/api/friends/requests', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (response.ok) {
            const requests = await response.json();
            renderFriendRequests(requests);
        }
    } catch (error) {
        console.error('Error loading friend requests:', error);
    }
}

// Render friend requests
function renderFriendRequests(requests) {
    const requestsList = document.querySelector('.requests-list');
    
    if (requests.length === 0) {
        requestsList.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📮</div>
                <div class="empty-title">친구 요청이 없습니다</div>
            </div>
        `;
        return;
    }
    
    requestsList.innerHTML = requests.map(request => `
        <div class="request-item">
            <div class="request-avatar">
                <img src="${request.avatar || '/static/images/default-avatar.png'}" alt="${request.name}">
            </div>
            <div class="request-info">
                <div class="request-name">${request.name}</div>
                <div class="request-time">${formatTimeAgo(request.created_at)}</div>
            </div>
            <div class="request-actions">
                <button class="btn-accept" onclick="acceptRequest('${request.id}')">수락</button>
                <button class="btn-decline" onclick="declineRequest('${request.id}')">거절</button>
            </div>
        </div>
    `).join('');
}

// Search friend
async function searchFriend() {
    const email = document.getElementById('friend-email').value;
    
    if (!email) {
        showNotification('이메일을 입력해주세요.', 'warning');
        return;
    }
    
    try {
        const response = await fetch(`/api/users/search?email=${encodeURIComponent(email)}`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (response.ok) {
            const user = await response.json();
            showSearchResult(user);
        } else if (response.status === 404) {
            showNotification('사용자를 찾을 수 없습니다.', 'warning');
        }
    } catch (error) {
        console.error('Error searching friend:', error);
        showNotification('검색 중 오류가 발생했습니다.', 'error');
    }
}

// Show search result
function showSearchResult(user) {
    const resultDiv = document.getElementById('search-result');
    const resultCard = resultDiv.querySelector('.result-card');
    
    resultCard.querySelector('img').src = user.avatar || '/static/images/default-avatar.png';
    resultCard.querySelector('.result-name').textContent = user.name;
    resultCard.querySelector('.result-email').textContent = user.email;
    
    const addBtn = resultCard.querySelector('.btn-add');
    if (user.is_friend) {
        addBtn.textContent = '이미 친구입니다';
        addBtn.disabled = true;
    } else if (user.request_sent) {
        addBtn.textContent = '요청 전송됨';
        addBtn.disabled = true;
    } else {
        addBtn.innerHTML = `
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <line x1="12" y1="5" x2="12" y2="19"/>
                <line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            친구 요청
        `;
        addBtn.disabled = false;
        addBtn.onclick = () => sendFriendRequest(user.id);
    }
    
    resultDiv.style.display = 'block';
}

// Send friend request
async function sendFriendRequest(userId) {
    try {
        const response = await fetch('/api/friends/request', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            },
            body: JSON.stringify({ user_id: userId })
        });
        
        if (response.ok) {
            showNotification('친구 요청을 보냈습니다.', 'success');
            closeAddFriendModal();
        } else {
            const error = await response.json();
            showNotification(error.message || '요청 전송에 실패했습니다.', 'error');
        }
    } catch (error) {
        console.error('Error sending friend request:', error);
        showNotification('요청 전송 중 오류가 발생했습니다.', 'error');
    }
}

// Accept friend request
async function acceptRequest(requestId) {
    try {
        const response = await fetch(`/api/friends/request/${requestId}/accept`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (response.ok) {
            showNotification('친구 요청을 수락했습니다.', 'success');
            loadFriendRequests();
            loadFriends();
            checkFriendRequests();
        }
    } catch (error) {
        console.error('Error accepting request:', error);
        showNotification('요청 수락에 실패했습니다.', 'error');
    }
}

// Decline friend request
async function declineRequest(requestId) {
    try {
        const response = await fetch(`/api/friends/request/${requestId}/decline`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (response.ok) {
            showNotification('친구 요청을 거절했습니다.', 'info');
            loadFriendRequests();
            checkFriendRequests();
        }
    } catch (error) {
        console.error('Error declining request:', error);
        showNotification('요청 거절에 실패했습니다.', 'error');
    }
}

// Copy invite link
function copyInviteLink() {
    const input = document.getElementById('invite-link');
    input.select();
    document.execCommand('copy');
    
    const btn = event.target.closest('.btn-copy');
    const originalText = btn.innerHTML;
    btn.innerHTML = '✓ 복사됨';
    
    setTimeout(() => {
        btn.innerHTML = originalText;
    }, 2000);
}

// Open my calendar settings
function openMyCalendarSettings() {
    // Navigate to calendar settings or show modal
    window.location.href = '/dashboard/settings#calendars';
}

// Utility functions
function formatTimeAgo(date) {
    const now = new Date();
    const past = new Date(date);
    const diffMs = now - past;
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffDays > 0) {
        return `${diffDays}일 전`;
    } else if (diffHours > 0) {
        return `${diffHours}시간 전`;
    } else if (diffMins > 0) {
        return `${diffMins}분 전`;
    } else {
        return '방금 전';
    }
}

function getCalendarTypeName(type) {
    const types = {
        work: '업무',
        personal: '개인',
        hobby: '취미',
        study: '학습',
        health: '건강',
        social: '소셜'
    };
    return types[type] || '기타';
}

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

// ===== MY CALENDARS SHARING FUNCTIONS =====

// Load current user's calendars
async function loadMyCalendars() {
    const loadingEl = document.getElementById('my-calendars-loading');
    const gridEl = document.getElementById('my-calendars-grid');
    const emptyEl = document.getElementById('my-calendars-empty');
    
    // Show loading
    loadingEl.style.display = 'flex';
    gridEl.style.display = 'none';
    emptyEl.style.display = 'none';
    
    try {
        const response = await fetch('/api/calendar/my-calendars');
        const data = await response.json();
        
        if (data.success && data.calendars) {
            if (data.calendars.length > 0) {
                renderMyCalendars(data.calendars);
                gridEl.style.display = 'grid';
            } else {
                emptyEl.style.display = 'block';
            }
        } else {
            emptyEl.style.display = 'block';
        }
    } catch (error) {
        console.error('Error loading my calendars:', error);
        emptyEl.style.display = 'block';
    } finally {
        loadingEl.style.display = 'none';
    }
}

// Render my calendars
function renderMyCalendars(calendars) {
    const gridEl = document.getElementById('my-calendars-grid');
    
    gridEl.innerHTML = calendars.map(calendar => `
        <div class="calendar-card" data-calendar-id="${calendar.id}">
            <div class="calendar-header">
                <div class="calendar-color" style="background-color: ${calendar.color || '#2563eb'}"></div>
                <div class="calendar-info">
                    <h3 class="calendar-name">${escapeHtml(calendar.name)}</h3>
                    <span class="calendar-type">${getCalendarTypeName(calendar.platform)}</span>
                </div>
                <div class="calendar-status">
                    ${calendar.is_currently_shared ? 
                        '<span class="status-shared">🔗 공유중</span>' : 
                        '<span class="status-private">🔒 비공개</span>'
                    }
                </div>
            </div>
            
            <div class="calendar-body">
                <p class="calendar-description">${escapeHtml(calendar.description || '설명 없음')}</p>
                
                ${calendar.is_currently_shared ? `
                    <div class="shared-with">
                        <small>공유된 친구: ${calendar.shared_with.length}명</small>
                    </div>
                ` : ''}
            </div>
            
            <div class="calendar-actions">
                <button class="btn-share" onclick="openShareModal('${calendar.id}', '${escapeHtml(calendar.name)}')">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/>
                        <polyline points="16,6 12,2 8,6"/>
                        <line x1="12" y1="2" x2="12" y2="15"/>
                    </svg>
                    친구와 공유
                </button>
                
                ${calendar.is_currently_shared ? `
                    <button class="btn-manage-share" onclick="openManageShareModal('${calendar.id}', '${escapeHtml(calendar.name)}')">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                            <circle cx="12" cy="12" r="3"/>
                            <path d="M12 1v6m0 6v6"/>
                        </svg>
                        공유 관리
                    </button>
                ` : ''}
            </div>
        </div>
    `).join('');
}

// Open share modal
function openShareModal(calendarId, calendarName) {
    // Create modal if not exists
    let modal = document.getElementById('share-calendar-modal');
    if (!modal) {
        modal = createShareModal();
        document.body.appendChild(modal);
    }
    
    // Set calendar info
    document.getElementById('share-calendar-name').textContent = calendarName;
    document.getElementById('share-calendar-id').value = calendarId;
    
    // Load friends
    loadFriendsForSharing();
    
    // Show modal
    modal.style.display = 'flex';
}

// Create share modal
function createShareModal() {
    const modal = document.createElement('div');
    modal.id = 'share-calendar-modal';
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2 class="modal-title">캘린더 공유하기</h2>
                <button class="modal-close" onclick="closeShareModal()">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path d="M6 18L18 6M6 6l12 12"/>
                    </svg>
                </button>
            </div>
            
            <div class="modal-body">
                <div class="share-info">
                    <h3>캘린더: <span id="share-calendar-name"></span></h3>
                    <input type="hidden" id="share-calendar-id">
                </div>
                
                <div class="friends-list-container">
                    <h4>친구 목록</h4>
                    <div class="friends-search">
                        <input type="text" placeholder="친구 검색..." id="friends-search" onkeyup="filterFriends()">
                    </div>
                    <div class="friends-list" id="share-friends-list">
                        <div class="loading-spinner">
                            <div class="spinner"></div>
                            <span>친구 목록을 불러오는 중...</span>
                        </div>
                    </div>
                </div>
                
                <div class="share-actions">
                    <button class="btn-cancel" onclick="closeShareModal()">취소</button>
                    <button class="btn-share-selected" onclick="shareWithSelectedFriends()">선택한 친구에게 공유</button>
                </div>
            </div>
        </div>
    `;
    return modal;
}

// Load friends for sharing
async function loadFriendsForSharing() {
    const listEl = document.getElementById('share-friends-list');
    
    try {
        const response = await fetch('/api/friends');
        const data = await response.json();
        
        if (data.success && data.friends) {
            renderFriendsForSharing(data.friends);
        } else {
            listEl.innerHTML = '<div class="empty-state">친구가 없습니다.</div>';
        }
    } catch (error) {
        console.error('Error loading friends:', error);
        listEl.innerHTML = '<div class="error-state">친구 목록을 불러올 수 없습니다.</div>';
    }
}

// Render friends for sharing
function renderFriendsForSharing(friends) {
    const listEl = document.getElementById('share-friends-list');
    
    listEl.innerHTML = friends.map(friend => `
        <div class="friend-item">
            <div class="friend-avatar">
                <img src="${friend.avatar || '/static/images/default-avatar.png'}" alt="${escapeHtml(friend.name)}" 
                     onerror="this.src='/static/images/default-avatar.png'">
            </div>
            <div class="friend-info">
                <div class="friend-name">${escapeHtml(friend.name)}</div>
                <div class="friend-email">${escapeHtml(friend.email || '')}</div>
            </div>
            <div class="friend-action">
                <input type="checkbox" class="friend-checkbox" value="${friend.id}" id="friend-${friend.id}">
                <label for="friend-${friend.id}" class="checkbox-label">공유</label>
            </div>
        </div>
    `).join('');
}

// Filter friends
function filterFriends() {
    const searchTerm = document.getElementById('friends-search').value.toLowerCase();
    const friendItems = document.querySelectorAll('.friend-item');
    
    friendItems.forEach(item => {
        const name = item.querySelector('.friend-name').textContent.toLowerCase();
        const email = item.querySelector('.friend-email').textContent.toLowerCase();
        
        if (name.includes(searchTerm) || email.includes(searchTerm)) {
            item.style.display = 'flex';
        } else {
            item.style.display = 'none';
        }
    });
}

// Share with selected friends
async function shareWithSelectedFriends() {
    const calendarId = document.getElementById('share-calendar-id').value;
    const selectedFriends = Array.from(document.querySelectorAll('.friend-checkbox:checked')).map(cb => cb.value);
    
    if (selectedFriends.length === 0) {
        showNotification('공유할 친구를 선택해주세요.', 'warning');
        return;
    }
    
    const shareBtn = document.querySelector('.btn-share-selected');
    const originalText = shareBtn.textContent;
    shareBtn.textContent = '공유 중...';
    shareBtn.disabled = true;
    
    try {
        const promises = selectedFriends.map(friendId => 
            fetch('/api/calendar/share', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    calendar_id: calendarId,
                    friend_id: friendId
                })
            })
        );
        
        const results = await Promise.all(promises);
        const successful = results.filter(r => r.ok).length;
        
        if (successful > 0) {
            showNotification(`${successful}명의 친구에게 캘린더를 공유했습니다.`, 'success');
            closeShareModal();
            loadMyCalendars(); // Refresh the calendar list
        } else {
            showNotification('캘린더 공유에 실패했습니다.', 'error');
        }
    } catch (error) {
        console.error('Error sharing calendar:', error);
        showNotification('캘린더 공유 중 오류가 발생했습니다.', 'error');
    } finally {
        shareBtn.textContent = originalText;
        shareBtn.disabled = false;
    }
}

// Close share modal
function closeShareModal() {
    const modal = document.getElementById('share-calendar-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Open manage share modal (for future implementation)
function openManageShareModal(calendarId, calendarName) {
    showNotification('공유 관리 기능은 곧 추가될 예정입니다.', 'info');
}

// ===== SHARED CALENDARS FUNCTIONS =====

// Load calendars shared with current user
async function loadSharedCalendars() {
    const loadingEl = document.getElementById('shared-calendars-loading');
    const gridEl = document.getElementById('shared-calendars-grid');
    const emptyEl = document.getElementById('shared-calendars-empty');
    
    // Show loading
    loadingEl.style.display = 'flex';
    gridEl.style.display = 'none';
    emptyEl.style.display = 'none';
    
    try {
        const response = await fetch('/api/calendar/shared-with-me');
        const data = await response.json();
        
        if (data.success && data.calendars) {
            if (data.calendars.length > 0) {
                renderSharedCalendars(data.calendars);
                gridEl.style.display = 'grid';
            } else {
                emptyEl.style.display = 'block';
            }
        } else {
            emptyEl.style.display = 'block';
        }
    } catch (error) {
        console.error('Error loading shared calendars:', error);
        emptyEl.style.display = 'block';
    } finally {
        loadingEl.style.display = 'none';
    }
}

// Render shared calendars
function renderSharedCalendars(calendars) {
    const gridEl = document.getElementById('shared-calendars-grid');
    
    gridEl.innerHTML = calendars.map(calendar => `
        <div class="shared-calendar-card" data-calendar-id="${calendar.id}">
            <div class="calendar-header">
                <div class="calendar-color" style="background-color: ${calendar.color || '#2563eb'}"></div>
                <div class="calendar-info">
                    <h3 class="calendar-name">${escapeHtml(calendar.name)}</h3>
                    <span class="calendar-type">${getCalendarTypeName(calendar.platform)}</span>
                </div>
                <div class="calendar-status">
                    <span class="status-shared-received">📥 공유받음</span>
                </div>
            </div>
            
            <div class="calendar-body">
                <p class="calendar-description">${escapeHtml(calendar.description || '설명 없음')}</p>
                
                <div class="shared-info">
                    <small>공유자: ${escapeHtml(calendar.shared_by || 'Unknown')}</small>
                    <br>
                    <small>공유일: ${formatTimeAgo(calendar.shared_at)}</small>
                </div>
            </div>
            
            <div class="calendar-actions">
                <button class="btn-view-calendar" onclick="viewSharedCalendar('${calendar.id}', '${escapeHtml(calendar.name)}')">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                        <circle cx="12" cy="12" r="3"/>
                    </svg>
                    캘린더 보기
                </button>
                
                ${calendar.can_edit ? `
                    <button class="btn-edit-calendar" onclick="editSharedCalendar('${calendar.id}', '${escapeHtml(calendar.name)}')">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                        </svg>
                        편집
                    </button>
                ` : ''}
            </div>
        </div>
    `).join('');
}

// View shared calendar
function viewSharedCalendar(calendarId, calendarName) {
    // Navigate to calendar view (could be dashboard with specific calendar selected)
    const params = new URLSearchParams({
        calendar: calendarId,
        shared: 'true'
    });
    window.location.href = `/dashboard?${params.toString()}`;
}

// Edit shared calendar (if permission allows)
function editSharedCalendar(calendarId, calendarName) {
    showNotification('공유 캘린더 편집 기능은 곧 추가될 예정입니다.', 'info');
}

// Escape HTML
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text ? text.replace(/[&<>"']/g, m => map[m]) : '';
}

// ===== USER SEARCH FUNCTIONS =====

let searchTimeout = null;

// Search users with debouncing
function searchUsers(query) {
    // Clear previous timeout
    if (searchTimeout) {
        clearTimeout(searchTimeout);
    }
    
    const trimmedQuery = query.trim();
    
    // Reset to placeholder if query is too short
    if (trimmedQuery.length < 2) {
        showSearchState('placeholder');
        return;
    }
    
    // Show loading state
    showSearchState('loading');
    
    // Debounce the search
    searchTimeout = setTimeout(async () => {
        try {
            const response = await fetch(`/api/users/search?q=${encodeURIComponent(trimmedQuery)}`);
            const data = await response.json();
            
            if (data.success) {
                if (data.users && data.users.length > 0) {
                    renderSearchResults(data.users);
                    showSearchState('results');
                } else {
                    showSearchState('empty');
                }
            } else {
                console.error('Search failed:', data.error);
                showSearchState('empty');
            }
        } catch (error) {
            console.error('Search error:', error);
            showSearchState('empty');
        }
    }, 300); // 300ms debounce
}

// Show different search states
function showSearchState(state) {
    const placeholder = document.getElementById('search-placeholder');
    const loading = document.getElementById('search-loading');
    const results = document.getElementById('search-results');
    const empty = document.getElementById('search-empty');
    
    // Hide all states first
    [placeholder, loading, results, empty].forEach(el => {
        if (el) el.style.display = 'none';
    });
    
    // Show the requested state
    switch (state) {
        case 'placeholder':
            if (placeholder) placeholder.style.display = 'block';
            break;
        case 'loading':
            if (loading) loading.style.display = 'flex';
            break;
        case 'results':
            if (results) results.style.display = 'block';
            break;
        case 'empty':
            if (empty) empty.style.display = 'block';
            break;
    }
}

// Render search results
function renderSearchResults(users) {
    const resultsContainer = document.getElementById('search-results');
    if (!resultsContainer) return;
    
    resultsContainer.innerHTML = users.map(user => `
        <div class="user-result-card" data-user-id="${user.id}">
            <div class="user-avatar">
                <img src="${user.avatar || '/static/images/default-avatar.png'}" 
                     alt="${escapeHtml(user.name)}" 
                     onerror="this.src='/static/images/default-avatar.png'">
            </div>
            <div class="user-info">
                <div class="user-name">${escapeHtml(user.name)}</div>
                <div class="user-email">${escapeHtml(user.email)}</div>
                <div class="user-id">ID: ${escapeHtml(user.id)}</div>
            </div>
            <div class="user-actions">
                ${user.is_friend ? `
                    <span class="friend-status">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                            <path d="M20 6L9 17l-5-5"/>
                        </svg>
                        이미 친구
                    </span>
                ` : `
                    <button class="btn-send-request" onclick="sendFriendRequestToUser('${user.id}', '${escapeHtml(user.name)}', this)">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                            <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                            <circle cx="8.5" cy="7" r="4"/>
                            <line x1="20" y1="8" x2="20" y2="14"/>
                            <line x1="23" y1="11" x2="17" y2="11"/>
                        </svg>
                        친구 요청
                    </button>
                `}
            </div>
        </div>
    `).join('');
}

// Send friend request to a specific user
async function sendFriendRequestToUser(userId, userName, buttonElement) {
    const originalText = buttonElement.textContent;
    const originalHtml = buttonElement.innerHTML;
    
    // Show loading state
    buttonElement.disabled = true;
    buttonElement.innerHTML = `
        <div class="spinner small"></div>
        전송 중...
    `;
    
    try {
        const response = await fetch('/api/friends/request', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: userId
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Show success state
            buttonElement.innerHTML = `
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M20 6L9 17l-5-5"/>
                </svg>
                요청 완료
            `;
            buttonElement.classList.add('success');
            buttonElement.disabled = true;
            
            showNotification(`${userName}님에게 친구 요청을 보냈습니다.`, 'success');
        } else {
            // Show error and restore button
            showNotification(data.error || '친구 요청을 보내는데 실패했습니다.', 'error');
            buttonElement.innerHTML = originalHtml;
            buttonElement.disabled = false;
        }
    } catch (error) {
        console.error('Error sending friend request:', error);
        showNotification('친구 요청을 보내는 중 오류가 발생했습니다.', 'error');
        
        // Restore button
        buttonElement.innerHTML = originalHtml;
        buttonElement.disabled = false;
    }
}

// Clear search when modal is opened
function openAddFriendModal() {
    const modal = document.getElementById('add-friend-modal');
    const searchInput = document.getElementById('user-search-input');
    
    if (modal) {
        modal.style.display = 'flex';
    }
    
    // Clear search input and reset to placeholder
    if (searchInput) {
        searchInput.value = '';
        showSearchState('placeholder');
    }
}

// Close add friend modal
function closeAddFriendModal() {
    const modal = document.getElementById('add-friend-modal');
    if (modal) {
        modal.style.display = 'none';
    }
    
    // Clear any ongoing search
    if (searchTimeout) {
        clearTimeout(searchTimeout);
        searchTimeout = null;
    }
}

// Show notification
function showNotification(message, type = 'info') {
    // Use the notification utility if available
    if (window.NotificationUtils) {
        window.NotificationUtils.show(message, type);
    } else {
        // Fallback to console
        console.log(`[${type.toUpperCase()}] ${message}`);
    }
}