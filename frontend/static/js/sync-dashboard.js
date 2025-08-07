/**
 * 🎯 Sync Dashboard UI Controller
 * Manages the sync activity dashboard interface
 */

// Platform configuration
const PLATFORM_CONFIG = {
    notion: { icon: '📝', name: 'Notion', color: '#000000' },
    google: { icon: '📅', name: 'Google Calendar', color: '#4285F4' },
    slack: { icon: '💬', name: 'Slack', color: '#4A154B' },
    outlook: { icon: '📧', name: 'Outlook', color: '#0078D4' },
    todoist: { icon: '✅', name: 'Todoist', color: '#E44332' },
    apple: { icon: '🍎', name: 'Apple Calendar', color: '#333333' }
};

// Activity type icons
const ACTIVITY_ICONS = {
    login: '🔐',
    logout: '🚪',
    sync_triggered: '🔄',
    sync_scheduled: '⏰',
    settings_changed: '⚙️',
    platform_connected: '🔗',
    platform_disconnected: '🔌',
    api_key_added: '🔑',
    api_key_removed: '🗑️',
    subscription_changed: '💳'
};

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Set up event listeners
    setupEventListeners();
    
    // Update UI when data changes
    if (window.syncTracker) {
        window.syncTracker.on('coverage:updated', updatePlatformCoverage);
        window.syncTracker.on('events:updated', updateSyncEvents);
        window.syncTracker.on('activities:updated', updateActivityTimeline);
        window.syncTracker.on('analytics:updated', updateAnalyticsCharts);
        
        // Initial UI update
        updateSummaryCards();
    }
});

/**
 * Set up event listeners
 */
function setupEventListeners() {
    // Real-time updates
    if (window.syncTracker) {
        window.syncTracker.on('event:new', (event) => {
            // Add animation for new events
            const eventElement = createEventElement(event);
            if (eventElement) {
                eventElement.classList.add('new-event');
                document.getElementById('sync-events').prepend(eventElement);
            }
        });
        
        window.syncTracker.on('activity:new', (activity) => {
            // Add animation for new activities
            const activityElement = createActivityElement(activity);
            if (activityElement) {
                activityElement.classList.add('new-activity');
                document.getElementById('activity-timeline').prepend(activityElement);
            }
        });
    }
}

/**
 * Update summary cards
 */
function updateSummaryCards() {
    if (!window.syncTracker || !window.syncTracker.analytics.summary) return;
    
    const summary = window.syncTracker.analytics.summary;
    
    // Update connected platforms
    document.getElementById('connected-platforms').textContent = 
        summary.connected_platforms || 0;
    
    // Update total synced
    document.getElementById('total-synced').textContent = 
        formatNumber(summary.total_synced_items || 0);
    
    // Update success rate
    document.getElementById('success-rate').textContent = 
        `${summary.overall_success_rate || 0}%`;
    
    // Update last activity
    updateLastActivity();
}

/**
 * Update platform coverage section
 */
function updatePlatformCoverage(data) {
    const container = document.getElementById('platform-grid');
    container.innerHTML = '';
    
    // Create platform cards
    Object.entries(data.platforms).forEach(([platform, platformData]) => {
        const card = createPlatformCard(platform, platformData);
        container.appendChild(card);
    });
    
    // Update summary cards
    updateSummaryCards();
}

/**
 * Create platform card element
 */
function createPlatformCard(platform, data) {
    const template = document.getElementById('platform-card-template');
    const card = template.content.cloneNode(true);
    const cardElement = card.querySelector('.platform-card');
    
    // Set platform data
    cardElement.dataset.platform = platform;
    
    // Set platform info
    const config = PLATFORM_CONFIG[platform] || { icon: '❓', name: platform };
    card.querySelector('.platform-icon').textContent = config.icon;
    card.querySelector('.platform-name').textContent = config.name;
    
    // Set connection status
    const statusElement = card.querySelector('.platform-status');
    if (data.is_connected) {
        statusElement.textContent = '🟢';
        statusElement.title = 'Connected';
    } else {
        statusElement.textContent = '⚫';
        statusElement.title = 'Not Connected';
    }
    
    // Set statistics
    card.querySelector('.success-rate').textContent = `${data.sync_success_rate}%`;
    card.querySelector('.total-synced').textContent = formatNumber(data.total_synced_items);
    card.querySelector('.last-active').textContent = formatRelativeTime(data.last_active_at);
    
    // Set features
    const featuresContainer = card.querySelector('.platform-features');
    if (data.feature_coverage) {
        Object.entries(data.feature_coverage).forEach(([feature, enabled]) => {
            if (enabled) {
                const badge = document.createElement('span');
                badge.className = 'feature-badge';
                badge.textContent = formatFeatureName(feature);
                featuresContainer.appendChild(badge);
            }
        });
    }
    
    // Set health indicator
    const health = window.syncTracker.getPlatformHealth(platform);
    const healthIndicator = card.querySelector('.health-indicator');
    const healthLabel = card.querySelector('.health-label');
    
    healthIndicator.className = `health-indicator health-${health}`;
    healthLabel.textContent = health.charAt(0).toUpperCase() + health.slice(1);
    
    return cardElement;
}

/**
 * Update activity timeline
 */
function updateActivityTimeline(activities) {
    const container = document.getElementById('activity-timeline');
    container.innerHTML = '';
    
    activities.forEach(activity => {
        const element = createActivityElement(activity);
        if (element) {
            container.appendChild(element);
        }
    });
}

/**
 * Create activity element
 */
function createActivityElement(activity) {
    const template = document.getElementById('activity-item-template');
    const item = template.content.cloneNode(true);
    const itemElement = item.querySelector('.activity-item');
    
    // Set activity type
    itemElement.dataset.type = activity.activity_type;
    
    // Set icon
    const icon = ACTIVITY_ICONS[activity.activity_type] || '📌';
    item.querySelector('.activity-icon').textContent = icon;
    
    // Set content
    item.querySelector('.activity-title').textContent = formatActivityTitle(activity);
    item.querySelector('.activity-details').textContent = formatActivityDetails(activity);
    item.querySelector('.activity-time').textContent = formatRelativeTime(activity.created_at);
    
    return itemElement;
}

/**
 * Update sync events
 */
function updateSyncEvents(events) {
    const container = document.getElementById('sync-events');
    container.innerHTML = '';
    
    // Apply filters
    const platformFilter = document.getElementById('platform-filter').value;
    const statusFilter = document.getElementById('status-filter').value;
    
    const filteredEvents = events.filter(event => {
        if (platformFilter && event.platform !== platformFilter) return false;
        if (statusFilter && event.status !== statusFilter) return false;
        return true;
    });
    
    filteredEvents.forEach(event => {
        const element = createEventElement(event);
        if (element) {
            container.appendChild(element);
        }
    });
}

/**
 * Create event element
 */
function createEventElement(event) {
    const template = document.getElementById('event-item-template');
    const item = template.content.cloneNode(true);
    const itemElement = item.querySelector('.event-item');
    
    // Set status
    itemElement.dataset.status = event.status;
    
    // Set status icon
    const statusIcon = {
        success: '✅',
        failed: '❌',
        skipped: '⏭️',
        pending: '⏳'
    }[event.status] || '❓';
    item.querySelector('.event-status').textContent = statusIcon;
    
    // Set platform
    const config = PLATFORM_CONFIG[event.platform] || { icon: '❓', name: event.platform };
    item.querySelector('.event-platform').textContent = `${config.icon} ${config.name}`;
    
    // Set event type
    item.querySelector('.event-type').textContent = formatEventType(event.event_type);
    
    // Set title
    if (event.item_title) {
        item.querySelector('.event-title').textContent = event.item_title;
    } else {
        item.querySelector('.event-title').style.display = 'none';
    }
    
    // Set error message
    if (event.error_message) {
        item.querySelector('.event-error').textContent = event.error_message;
    } else {
        item.querySelector('.event-error').style.display = 'none';
    }
    
    // Set time
    item.querySelector('.event-time').textContent = formatRelativeTime(event.created_at);
    
    return itemElement;
}

/**
 * Update analytics charts
 */
function updateAnalyticsCharts(analytics) {
    // This is a placeholder - you would integrate with a charting library
    // Update analytics charts
    
    // For now, just show a summary
    const trendChart = document.getElementById('sync-trend-chart');
    const breakdownChart = document.getElementById('platform-breakdown-chart');
    
    if (analytics && analytics.length > 0) {
        // Show basic stats
        const totalSyncs = analytics.reduce((sum, a) => sum + a.total_syncs, 0);
        const successfulSyncs = analytics.reduce((sum, a) => sum + a.successful_syncs, 0);
        
        trendChart.innerHTML = `
            <div class="chart-placeholder">
                <h3>Sync Trend</h3>
                <p>Total Syncs: ${totalSyncs}</p>
                <p>Successful: ${successfulSyncs}</p>
                <p>Success Rate: ${Math.round(successfulSyncs / totalSyncs * 100)}%</p>
            </div>
        `;
    }
}

/**
 * Update last activity time
 */
function updateLastActivity() {
    const recentEvents = window.syncTracker?.analytics.recentEvents || [];
    const recentActivities = window.syncTracker?.analytics.recentActivities || [];
    
    let lastTime = null;
    
    if (recentEvents.length > 0) {
        lastTime = recentEvents[0].created_at;
    }
    
    if (recentActivities.length > 0) {
        const activityTime = recentActivities[0].created_at;
        if (!lastTime || new Date(activityTime) > new Date(lastTime)) {
            lastTime = activityTime;
        }
    }
    
    document.getElementById('last-activity').textContent = 
        lastTime ? formatRelativeTime(lastTime) : 'Never';
}

/**
 * Trigger manual sync
 */
async function triggerManualSync() {
    try {
        const button = event.target;
        button.disabled = true;
        button.textContent = '⏳ Syncing...';
        
        const response = await fetch('/api/sync/trigger', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Sync triggered successfully!', 'success');
        } else {
            showNotification(data.error || 'Sync failed', 'error');
        }
        
    } catch (error) {
        console.error('Error triggering sync:', error);
        showNotification('Failed to trigger sync', 'error');
    } finally {
        button.disabled = false;
        button.textContent = '⚡ Sync Now';
    }
}

/**
 * Filter activities
 */
function filterActivities() {
    const filter = document.getElementById('activity-filter').value;
    const items = document.querySelectorAll('.activity-item');
    
    items.forEach(item => {
        if (filter === 'all' || item.dataset.type === filter) {
            item.style.display = '';
        } else {
            item.style.display = 'none';
        }
    });
}

/**
 * Filter events
 */
function filterEvents() {
    if (window.syncTracker) {
        updateSyncEvents(window.syncTracker.analytics.recentEvents);
    }
}

/**
 * Update analytics period
 */
async function updateAnalytics() {
    const period = document.getElementById('analytics-period').value;
    if (window.syncTracker) {
        await window.syncTracker.loadAnalytics(period);
    }
}

// Utility functions

function formatNumber(num) {
    return new Intl.NumberFormat().format(num);
}

function formatRelativeTime(timestamp) {
    if (!timestamp) return 'Never';
    
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    
    return date.toLocaleDateString();
}

function formatFeatureName(feature) {
    const names = {
        sync_tasks: '📋 Tasks',
        sync_events: '📅 Events',
        sync_notes: '📝 Notes',
        bidirectional: '↔️ Two-way',
        real_time: '⚡ Real-time',
        webhooks: '🔗 Webhooks'
    };
    return names[feature] || feature;
}

function formatActivityTitle(activity) {
    const titles = {
        login: 'User logged in',
        logout: 'User logged out',
        sync_triggered: 'Manual sync triggered',
        sync_scheduled: 'Scheduled sync started',
        settings_changed: 'Settings updated',
        platform_connected: 'Platform connected',
        platform_disconnected: 'Platform disconnected',
        api_key_added: 'API key added',
        api_key_removed: 'API key removed',
        subscription_changed: 'Subscription updated'
    };
    return titles[activity.activity_type] || activity.activity_type;
}

function formatActivityDetails(activity) {
    if (activity.platform) {
        const config = PLATFORM_CONFIG[activity.platform];
        return `${config ? config.name : activity.platform}`;
    }
    if (activity.activity_details && activity.activity_details.description) {
        return activity.activity_details.description;
    }
    return '';
}

function formatEventType(eventType) {
    const types = {
        sync_started: 'Sync Started',
        sync_completed: 'Sync Completed',
        sync_failed: 'Sync Failed',
        item_created: 'Item Created',
        item_updated: 'Item Updated',
        item_deleted: 'Item Deleted',
        platform_connected: 'Connected',
        platform_disconnected: 'Disconnected'
    };
    return types[eventType] || eventType;
}

function showNotification(message, type = 'info') {
    // You can implement a toast notification system here
    
    // Simple alert for now
    if (type === 'error') {
        alert(`Error: ${message}`);
    }
}