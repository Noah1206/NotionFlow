// Friends Page JavaScript

// Global variables
let currentUser = null;
let friends = [];
let friendCalendars = [];
let currentPage = 1;
const itemsPerPage = 10;

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    // For testing: set a test access token if none exists
    if (!localStorage.getItem('access_token')) {
        localStorage.setItem('access_token', 'test_token_12345678901234567890');
        console.log('✅ Set test access token for development');
    }
    
    // Immediately update avatar from localStorage for instant loading
    updateMyStoryAvatar();
    
    // Then load all data
    await loadCurrentUser();
    await loadFriends();
    await loadMyCalendars();
    await loadSharedCalendars();
    await loadFriendCalendars();
    initializeEventListeners();
    checkFriendRequests();
    updateNotificationBadge();
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
            // Update the "My Story" avatar with current user's profile picture
            updateMyStoryAvatar();
        }
    } catch (error) {
        console.error('Error loading user:', error);
    }
}

// Update my story avatar with user profile picture
function updateMyStoryAvatar() {
    const myStoryAvatar = document.querySelector('.my-story .story-avatar img');
    if (!myStoryAvatar) return;
    
    // First check localStorage for quick loading
    const cachedAvatar = localStorage.getItem('user_avatar');
    if (cachedAvatar && cachedAvatar !== '/static/images/default-avatar.png') {
        myStoryAvatar.src = cachedAvatar;
    }
    
    // Then update from currentUser data if available
    if (currentUser && currentUser.avatar) {
        myStoryAvatar.src = currentUser.avatar;
        myStoryAvatar.alt = currentUser.name || '내 스토리';
        
        // Update localStorage
        localStorage.setItem('user_avatar', currentUser.avatar);
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
            const data = await response.json();
            friends = Array.isArray(data) ? data : (data.friends || []);
            renderStoryBar();
            updateFilterOptions();
        }
    } catch (error) {
        console.error('Error loading friends:', error);
        friends = []; // Ensure friends is always an array
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
            const data = await response.json();
            friendCalendars = Array.isArray(data) ? data : (data.calendars || []);
            renderCalendarTable();
            updateStats();
        }
    } catch (error) {
        console.error('Error loading friend calendars:', error);
        friendCalendars = []; // Ensure friendCalendars is always an array
        showNotification('캘린더 목록을 불러오는데 실패했습니다.', 'error');
    }
}

// Render Instagram-style story bar
function renderStoryBar() {
    const storyList = document.getElementById('story-list');
    if (!storyList) return;
    
    const myStory = storyList.querySelector('.my-story');
    
    // Clear existing friend stories
    const existingStories = storyList.querySelectorAll('.story-item:not(.my-story)');
    existingStories.forEach(story => story.remove());
    
    // Ensure friends is an array before using forEach
    if (!Array.isArray(friends)) {
        console.warn('friends is not an array:', friends);
        return;
    }
    
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
    if (!tbody) return;
    
    // Ensure we have an array to work with
    let calendarsToRender = calendars || friendCalendars;
    if (!Array.isArray(calendarsToRender)) {
        console.warn('calendarsToRender is not an array:', calendarsToRender);
        calendarsToRender = [];
    }
    
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
    if (!filterSelect) return;
    
    // Clear existing options except "All"
    filterSelect.innerHTML = '<option value="">모든 친구</option>';
    
    // Ensure friends is an array before using forEach
    if (!Array.isArray(friends)) {
        console.warn('friends is not an array:', friends);
        return;
    }
    
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
    // Ensure arrays are valid before using array methods
    const validFriends = Array.isArray(friends) ? friends : [];
    const validCalendars = Array.isArray(friendCalendars) ? friendCalendars : [];
    
    const stats = {
        friends: validFriends.length,
        publicCalendars: validCalendars.filter(c => c.is_public).length,
        totalEvents: validCalendars.reduce((sum, c) => sum + (c.event_count || 0), 0),
        sharing: validCalendars.filter(c => c.is_shared).length
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

// ===== HEADER SEARCH FUNCTIONS =====

let headerSearchTimeout = null;

// Header search function with debouncing
async function headerSearchFriends(query) {
    // Clear previous timeout
    if (headerSearchTimeout) {
        clearTimeout(headerSearchTimeout);
    }
    
    const searchInput = document.getElementById('header-friend-search');
    const clearBtn = document.getElementById('search-clear');
    const dropdown = document.getElementById('header-search-dropdown');
    const resultsContainer = document.getElementById('header-search-results');
    
    // Show/hide clear button
    if (query.trim().length > 0) {
        clearBtn.style.display = 'flex';
    } else {
        clearBtn.style.display = 'none';
        dropdown.style.display = 'none';
        return;
    }
    
    // Show loading state
    dropdown.style.display = 'block';
    resultsContainer.innerHTML = `
        <div class="search-loading">
            <div class="spinner"></div>
            <span>검색 중...</span>
        </div>
    `;
    
    // Debounce the search
    headerSearchTimeout = setTimeout(async () => {
        try {
            const response = await fetch(`/api/users/search?q=${encodeURIComponent(query)}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                const users = Array.isArray(data) ? data : (data.users || []);
                
                if (users.length > 0) {
                    renderHeaderSearchResults(users);
                } else {
                    resultsContainer.innerHTML = `
                        <div class="search-empty-state">
                            검색 결과가 없습니다.
                        </div>
                    `;
                }
            } else if (response.status === 404) {
                resultsContainer.innerHTML = `
                    <div class="search-empty-state">
                        해당하는 사용자를 찾을 수 없습니다.
                    </div>
                `;
            } else {
                resultsContainer.innerHTML = `
                    <div class="search-empty-state">
                        검색 중 오류가 발생했습니다.
                    </div>
                `;
            }
        } catch (error) {
            console.error('Search error:', error);
            resultsContainer.innerHTML = `
                <div class="search-empty-state">
                    서버에 연결할 수 없습니다.
                </div>
            `;
        }
    }, 300);
}

// Mock user data for testing
function searchMockUsers(query) {
    const mockUsers = [
        {
            id: 'user1',
            name: '김민수',
            email: 'minsu@example.com',
            avatar: null
        },
        {
            id: 'user2', 
            name: '이영희',
            email: 'younghee@gmail.com',
            avatar: null
        },
        {
            id: 'user3',
            name: '박철수',
            email: 'chulsoo@naver.com', 
            avatar: null
        },
        {
            id: 'user4',
            name: '최지은',
            email: 'jieun@daum.net',
            avatar: null
        },
        {
            id: 'user5',
            name: 'John Smith',
            email: 'john@company.com',
            avatar: null
        }
    ];
    
    const queryLower = query.toLowerCase();
    return mockUsers.filter(user => 
        user.name.toLowerCase().includes(queryLower) ||
        user.email.toLowerCase().includes(queryLower)
    );
}

// Render header search results
function renderHeaderSearchResults(users) {
    const resultsContainer = document.getElementById('header-search-results');
    
    resultsContainer.innerHTML = users.map(user => {
        // Check if already friends
        const isFriend = friends.some(f => f.id === user.id);
        
        const avatarDisplay = user.avatar 
            ? `<img src="${user.avatar}" alt="${escapeHtml(user.name)}" onerror="this.src='${generateUserAvatar(user.name)}'">` 
            : `<div class="generated-avatar" style="background: ${generateAvatarColor(user.name)}">${user.name ? user.name.charAt(0).toUpperCase() : '?'}</div>`;
        
        return `
            <div class="search-result-item" data-user-id="${user.id}" onclick="showFriendRequestPopup('${user.id}', '${escapeHtml(user.name)}', '${escapeHtml(user.email)}', '${user.avatar || 'generated'}', ${isFriend})">
                <div class="search-result-avatar">
                    ${avatarDisplay}
                </div>
                <div class="search-result-info">
                    <div class="search-result-name">${escapeHtml(user.name)}</div>
                    <div class="search-result-email">${escapeHtml(user.email || '')}</div>
                </div>
                <div class="search-result-action">
                    ${isFriend ? `
                        <button class="btn-send-request-small" disabled onclick="event.stopPropagation()">
                            이미 친구
                        </button>
                    ` : `
                        <button class="btn-send-request-small" 
                                onclick="event.stopPropagation(); sendQuickFriendRequest('${user.id}', '${escapeHtml(user.name)}', this)">
                            친구 추가
                        </button>
                    `}
                </div>
            </div>
        `;
    }).join('');
}

// Show friend request popup
function showFriendRequestPopup(userId, userName, userEmail, userAvatar, isFriend) {
    const popup = document.createElement('div');
    popup.className = 'friend-request-popup-overlay';
    popup.innerHTML = `
        <div class="friend-request-popup">
            <div class="popup-header">
                <h3>친구 추가</h3>
                <button class="popup-close" onclick="closeFriendRequestPopup()">&times;</button>
            </div>
            <div class="popup-content">
                <div class="user-profile">
                    <img src="${userAvatar}" alt="${userName}" class="user-avatar" 
                         onerror="this.src='/static/images/default-avatar.png'">
                    <div class="user-info">
                        <h4>${userName}</h4>
                        <p>${userEmail}</p>
                    </div>
                </div>
                
                ${isFriend ? `
                    <div class="already-friends">
                        <p>이미 친구입니다!</p>
                        <button class="btn-secondary" onclick="closeFriendRequestPopup()">확인</button>
                    </div>
                ` : `
                    <div class="friend-request-form">
                        <label for="request-message">메시지 (선택사항):</label>
                        <textarea id="request-message" placeholder="안녕하세요! 친구가 되어요." maxlength="200"></textarea>
                        <div class="popup-actions">
                            <button class="btn-secondary" onclick="closeFriendRequestPopup()">취소</button>
                            <button class="btn-primary" onclick="sendFriendRequestFromPopup('${userId}', '${userName}')">친구 요청 보내기</button>
                        </div>
                    </div>
                `}
            </div>
        </div>
    `;
    
    document.body.appendChild(popup);
    popup.style.display = 'flex';
}

// Close friend request popup
function closeFriendRequestPopup() {
    const popup = document.querySelector('.friend-request-popup-overlay');
    if (popup) {
        popup.remove();
    }
}

// Send friend request from popup
async function sendFriendRequestFromPopup(userId, userName) {
    const messageInput = document.getElementById('request-message');
    const message = messageInput ? messageInput.value.trim() : '';
    
    const submitBtn = document.querySelector('.friend-request-popup .btn-primary');
    const originalText = submitBtn.textContent;
    
    // Show loading state
    submitBtn.disabled = true;
    submitBtn.textContent = '전송 중...';
    
    try {
        const response = await fetch('/api/friends/request', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            },
            body: JSON.stringify({
                user_id: userId,
                message: message
            })
        });
        
        if (response.ok) {
            showNotification(`${userName}님에게 친구 요청을 보냈습니다!`, 'success');
            closeFriendRequestPopup();
            
            // Hide search dropdown
            const dropdown = document.getElementById('header-search-dropdown');
            if (dropdown) dropdown.style.display = 'none';
            
            // Clear search
            const searchInput = document.getElementById('header-friend-search');
            if (searchInput) searchInput.value = '';
        } else {
            const error = await response.json();
            showNotification(error.error || '친구 요청 전송에 실패했습니다.', 'error');
        }
    } catch (error) {
        console.error('Friend request error:', error);
        showNotification('서버 연결에 실패했습니다.', 'error');
    }
    
    // Restore button state
    submitBtn.disabled = false;
    submitBtn.textContent = originalText;
}

// Send quick friend request from header search
async function sendQuickFriendRequest(userId, userName, buttonElement) {
    const originalText = buttonElement.textContent;
    
    // Show loading state
    buttonElement.disabled = true;
    buttonElement.textContent = '전송 중...';
    
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
            buttonElement.textContent = '요청 완료';
            showNotification(`${userName}님에게 친구 요청을 보냈습니다.`, 'success');
            
            // Reload friends list after a moment
            setTimeout(() => {
                loadFriends();
            }, 1000);
        } else {
            const error = await response.json();
            showNotification(error.message || '요청 전송에 실패했습니다.', 'error');
            buttonElement.textContent = originalText;
            buttonElement.disabled = false;
        }
    } catch (error) {
        console.error('Error sending friend request:', error);
        showNotification('요청 전송 중 오류가 발생했습니다.', 'error');
        buttonElement.textContent = originalText;
        buttonElement.disabled = false;
    }
}

// Clear header search
function clearHeaderSearch() {
    const searchInput = document.getElementById('header-friend-search');
    const clearBtn = document.getElementById('search-clear');
    const dropdown = document.getElementById('header-search-dropdown');
    
    searchInput.value = '';
    clearBtn.style.display = 'none';
    dropdown.style.display = 'none';
    
    if (headerSearchTimeout) {
        clearTimeout(headerSearchTimeout);
    }
}

// Close dropdown when clicking outside
document.addEventListener('click', function(event) {
    const searchContainer = document.querySelector('.header-search');
    const dropdown = document.getElementById('header-search-dropdown');
    
    if (searchContainer && !searchContainer.contains(event.target)) {
        dropdown.style.display = 'none';
    }
});

// Update user profile avatar URL (for testing)
async function updateUserAvatar(avatarUrl) {
    try {
        const response = await fetch('/api/user/profile', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            },
            body: JSON.stringify({ avatar_url: avatarUrl })
        });
        
        if (response.ok) {
            showNotification('프로필 사진이 업데이트되었습니다.', 'success');
            // Reload current user to update the avatar
            await loadCurrentUser();
        } else {
            showNotification('프로필 사진 업데이트에 실패했습니다.', 'error');
        }
    } catch (error) {
        console.error('Error updating avatar:', error);
        showNotification('프로필 사진 업데이트 중 오류가 발생했습니다.', 'error');
    }
}

// ===== NOTIFICATIONS PANEL FUNCTIONS =====

// Toggle notifications panel
function toggleNotificationsPanel() {
    const panel = document.getElementById('notifications-panel');
    
    if (panel.style.display === 'none' || panel.style.display === '') {
        openNotificationsPanel();
    } else {
        closeNotificationsPanel();
    }
}

// Open notifications panel
function openNotificationsPanel() {
    const panel = document.getElementById('notifications-panel');
    panel.style.display = 'block';
    loadFriendRequestsForNotifications();
    
    // Close when clicking outside
    setTimeout(() => {
        document.addEventListener('click', closeNotificationsOnOutsideClick);
    }, 100);
}

// Close notifications panel
function closeNotificationsPanel() {
    const panel = document.getElementById('notifications-panel');
    panel.style.display = 'none';
    document.removeEventListener('click', closeNotificationsOnOutsideClick);
}

// Close notifications when clicking outside
function closeNotificationsOnOutsideClick(event) {
    const panel = document.getElementById('notifications-panel');
    const button = document.querySelector('.btn-requests');
    
    if (!panel.contains(event.target) && !button.contains(event.target)) {
        closeNotificationsPanel();
    }
}

// Load friend requests for notifications
async function loadFriendRequestsForNotifications() {
    const contentContainer = document.getElementById('notifications-content');
    
    try {
        const response = await fetch('/api/friends/requests', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            const requests = Array.isArray(data) ? data : (data.requests || []);
            
            if (requests.length > 0) {
                renderFriendRequestsInNotifications(requests);
                updateRequestBadge(requests.length);
            } else {
                showEmptyNotifications();
                updateRequestBadge(0);
            }
        } else {
            showNotificationError();
        }
    } catch (error) {
        console.error('Failed to load friend requests:', error);
        showNotificationError();
    }
}

// Render friend requests in notifications
function renderFriendRequestsInNotifications(requests) {
    const contentContainer = document.getElementById('notifications-content');
    
    contentContainer.innerHTML = requests.map(request => {
        const senderInfo = request.sender || {};
        const timeAgo = formatTimeAgo(new Date(request.created_at));
        
        return `
            <div class="notification-item" data-request-id="${request.id}">
                <img src="${senderInfo.avatar_url || '/static/images/default-avatar.png'}" 
                     alt="${escapeHtml(senderInfo.username || 'Unknown User')}" 
                     class="notification-avatar"
                     onerror="this.src='/static/images/default-avatar.png'">
                <div class="notification-info">
                    <div class="notification-name">${escapeHtml(senderInfo.username || 'Unknown User')}</div>
                    <div class="notification-message">
                        ${request.message ? escapeHtml(request.message) : '친구 요청을 보냈습니다.'}
                    </div>
                    <div class="notification-time">${timeAgo}</div>
                </div>
                <div class="notification-actions">
                    <button class="btn-accept" onclick="acceptFriendRequestFromNotification('${request.id}', this)">
                        수락
                    </button>
                    <button class="btn-decline" onclick="declineFriendRequestFromNotification('${request.id}', this)">
                        거절
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

// Show empty notifications state
function showEmptyNotifications() {
    const contentContainer = document.getElementById('notifications-content');
    contentContainer.innerHTML = `
        <div class="notification-empty">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
                <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
            </svg>
            <p>새로운 친구 요청이 없습니다.</p>
        </div>
    `;
}

// Show notification error state
function showNotificationError() {
    const contentContainer = document.getElementById('notifications-content');
    contentContainer.innerHTML = `
        <div class="notification-empty">
            <p>알림을 불러오는데 실패했습니다.</p>
            <button class="btn-secondary" onclick="loadFriendRequestsForNotifications()" style="margin-top: 12px;">
                다시 시도
            </button>
        </div>
    `;
}

// Accept friend request from notification
async function acceptFriendRequestFromNotification(requestId, buttonElement) {
    const originalText = buttonElement.textContent;
    buttonElement.disabled = true;
    buttonElement.textContent = '처리 중...';
    
    try {
        const response = await fetch(`/api/friends/request/${requestId}/accept`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (response.ok) {
            showNotification('친구 요청을 수락했습니다!', 'success');
            
            // Remove the notification item with animation
            const notificationItem = buttonElement.closest('.notification-item');
            notificationItem.style.animation = 'fadeOut 0.3s ease-out forwards';
            
            setTimeout(() => {
                notificationItem.remove();
                
                // Check if there are any remaining requests
                const remainingRequests = document.querySelectorAll('.notification-item').length;
                updateRequestBadge(remainingRequests);
                
                if (remainingRequests === 0) {
                    showEmptyNotifications();
                }
                
                // Refresh friends list
                loadFriends();
            }, 300);
        } else {
            const error = await response.json();
            showNotification(error.error || '친구 요청 수락에 실패했습니다.', 'error');
            buttonElement.disabled = false;
            buttonElement.textContent = originalText;
        }
    } catch (error) {
        console.error('Accept friend request error:', error);
        showNotification('서버 연결에 실패했습니다.', 'error');
        buttonElement.disabled = false;
        buttonElement.textContent = originalText;
    }
}

// Decline friend request from notification
async function declineFriendRequestFromNotification(requestId, buttonElement) {
    const originalText = buttonElement.textContent;
    buttonElement.disabled = true;
    buttonElement.textContent = '처리 중...';
    
    try {
        const response = await fetch(`/api/friends/request/${requestId}/decline`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (response.ok) {
            showNotification('친구 요청을 거절했습니다.', 'info');
            
            // Remove the notification item with animation
            const notificationItem = buttonElement.closest('.notification-item');
            notificationItem.style.animation = 'fadeOut 0.3s ease-out forwards';
            
            setTimeout(() => {
                notificationItem.remove();
                
                // Check if there are any remaining requests
                const remainingRequests = document.querySelectorAll('.notification-item').length;
                updateRequestBadge(remainingRequests);
                
                if (remainingRequests === 0) {
                    showEmptyNotifications();
                }
            }, 300);
        } else {
            const error = await response.json();
            showNotification(error.error || '친구 요청 거절에 실패했습니다.', 'error');
            buttonElement.disabled = false;
            buttonElement.textContent = originalText;
        }
    } catch (error) {
        console.error('Decline friend request error:', error);
        showNotification('서버 연결에 실패했습니다.', 'error');
        buttonElement.disabled = false;
        buttonElement.textContent = originalText;
    }
}

// Update request badge count
function updateRequestBadge(count) {
    const badge = document.getElementById('request-count');
    
    if (count > 0) {
        badge.textContent = count > 99 ? '99+' : count.toString();
        badge.style.display = 'flex';
    } else {
        badge.style.display = 'none';
    }
}

// Format time ago
function formatTimeAgo(date) {
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (diffInSeconds < 60) {
        return '방금 전';
    } else if (diffInSeconds < 3600) {
        const minutes = Math.floor(diffInSeconds / 60);
        return `${minutes}분 전`;
    } else if (diffInSeconds < 86400) {
        const hours = Math.floor(diffInSeconds / 3600);
        return `${hours}시간 전`;
    } else {
        const days = Math.floor(diffInSeconds / 86400);
        return `${days}일 전`;
    }
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Update notification badge on page load
async function updateNotificationBadge() {
    try {
        const response = await fetch('/api/friends/requests', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            const requests = Array.isArray(data) ? data : (data.requests || []);
            updateRequestBadge(requests.length);
        }
    } catch (error) {
        console.error('Failed to load notification badge:', error);
    }
}

// Avatar generation helper functions
function generateAvatarColor(name) {
    if (!name) return '#6b7280';
    
    // Generate consistent color based on name
    const colors = [
        '#ef4444', '#f97316', '#f59e0b', '#eab308', '#84cc16',
        '#22c55e', '#10b981', '#14b8a6', '#06b6d4', '#0ea5e9',
        '#3b82f6', '#6366f1', '#8b5cf6', '#a855f7', '#d946ef',
        '#ec4899', '#f43f5e'
    ];
    
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
        const char = name.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // Convert to 32bit integer
    }
    
    return colors[Math.abs(hash) % colors.length];
}

function generateUserAvatar(name) {
    if (!name) name = '?';
    const initial = name.charAt(0).toUpperCase();
    const color = generateAvatarColor(name);
    
    // Create SVG avatar and convert to URL-encoded format
    const svg = `<svg width="40" height="40" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
        <rect width="40" height="40" fill="${color}" rx="20"/>
        <text x="50%" y="50%" text-anchor="middle" dy="0.35em" fill="white" font-family="system-ui, -apple-system, sans-serif" font-size="16" font-weight="600">${initial}</text>
    </svg>`;
    
    // Return URL-encoded SVG instead of base64 to support Korean characters
    return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
}

// Add fade out animation CSS
const notificationStyle = document.createElement('style');
notificationStyle.textContent = `
    @keyframes fadeOut {
        from { opacity: 1; height: auto; }
        to { opacity: 0; height: 0; padding-top: 0; padding-bottom: 0; margin-top: 0; margin-bottom: 0; }
    }
`;
document.head.appendChild(notificationStyle);