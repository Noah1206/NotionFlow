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