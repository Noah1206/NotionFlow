/**
 * 🔄 Sync Activity Tracker
 * Real-time sync monitoring and analytics
 */

class SyncTracker {
    constructor() {
        this.subscriptions = new Map();
        this.eventHandlers = new Map();
        this.analytics = {
            platforms: {},
            recentEvents: [],
            recentActivities: []
        };
    }

    /**
     * Initialize sync tracker
     */
    async initialize() {
        
        // Load initial data
        await this.loadPlatformCoverage();
        await this.loadRecentEvents();
        await this.loadRecentActivities();
        
        // Set up real-time subscriptions
        this.setupRealtimeSubscriptions();
        
        // Set up periodic refresh
        this.startPeriodicRefresh();
        
    }

    /**
     * Load platform coverage data
     */
    async loadPlatformCoverage() {
        try {
            const response = await fetch('/api/sync/coverage');
            const data = await response.json();
            
            if (data.success) {
                this.analytics.platforms = data.platforms;
                this.analytics.summary = data.summary;
                this.emit('coverage:updated', data);
            }
        } catch (error) {
            console.error('Error loading platform coverage:', error);
        }
    }

    /**
     * Load recent sync events
     */
    async loadRecentEvents(limit = 20) {
        try {
            const response = await fetch(`/api/sync/events/recent?limit=${limit}`);
            const data = await response.json();
            
            if (data.success) {
                this.analytics.recentEvents = data.events;
                this.emit('events:updated', data.events);
            }
        } catch (error) {
            console.error('Error loading recent events:', error);
        }
    }

    /**
     * Load recent user activities
     */
    async loadRecentActivities(limit = 20) {
        try {
            const response = await fetch(`/api/sync/activity/recent?limit=${limit}`);
            const data = await response.json();
            
            if (data.success) {
                this.analytics.recentActivities = data.activities;
                this.emit('activities:updated', data.activities);
            }
        } catch (error) {
            console.error('Error loading recent activities:', error);
        }
    }

    /**
     * Load sync analytics
     */
    async loadAnalytics(period = 'daily', limit = 7) {
        try {
            const response = await fetch(`/api/sync/analytics?period=${period}&limit=${limit}`);
            const data = await response.json();
            
            if (data.success) {
                this.analytics.analytics = data.analytics;
                this.emit('analytics:updated', data.analytics);
            }
        } catch (error) {
            console.error('Error loading analytics:', error);
        }
    }

    /**
     * Set up real-time subscriptions
     */
    setupRealtimeSubscriptions() {
        // Check if Supabase client is available
        if (typeof window.supabase === 'undefined') {
            // console.warn('Supabase client not available, skipping real-time subscriptions');
            return;
        }

        const userId = this.getCurrentUserId();
        if (!userId) {
            // console.warn('No user ID found, skipping real-time subscriptions');
            return;
        }

        // Subscribe to sync events
        const syncEventsChannel = window.supabase
            .channel('sync-events-' + userId)
            .on('postgres_changes', 
                { 
                    event: 'INSERT', 
                    schema: 'public', 
                    table: 'sync_events',
                    filter: `user_id=eq.${userId}`
                }, 
                (payload) => {
                    this.handleNewSyncEvent(payload.new);
                }
            )
            .subscribe();

        this.subscriptions.set('sync-events', syncEventsChannel);

        // Subscribe to user activities
        const userActivitiesChannel = window.supabase
            .channel('user-activities-' + userId)
            .on('postgres_changes',
                {
                    event: 'INSERT',
                    schema: 'public',
                    table: 'user_activity',
                    filter: `user_id=eq.${userId}`
                },
                (payload) => {
                    this.handleNewActivity(payload.new);
                }
            )
            .subscribe();

        this.subscriptions.set('user-activities', userActivitiesChannel);

    }

    /**
     * Handle new sync event
     */
    handleNewSyncEvent(event) {
        
        // Add to recent events
        this.analytics.recentEvents.unshift(event);
        if (this.analytics.recentEvents.length > 50) {
            this.analytics.recentEvents.pop();
        }
        
        // Update platform coverage
        if (event.platform && this.analytics.platforms[event.platform]) {
            const platform = this.analytics.platforms[event.platform];
            platform.last_active_at = event.created_at;
            
            if (event.status === 'success') {
                platform.total_synced_items++;
            } else if (event.status === 'failed') {
                platform.total_failed_items++;
            }
            
            // Recalculate success rate
            const total = platform.total_synced_items + platform.total_failed_items;
            if (total > 0) {
                platform.sync_success_rate = (platform.total_synced_items / total * 100).toFixed(2);
            }
        }
        
        // Emit event
        this.emit('event:new', event);
        this.emit('events:updated', this.analytics.recentEvents);
        
        // Show notification for important events
        if (event.event_type === 'sync_failed' || event.status === 'failed') {
            this.showNotification(`${event.platform} 동기화 실패`, 'error');
        }
    }

    /**
     * Handle new user activity
     */
    handleNewActivity(activity) {
        
        // Add to recent activities
        this.analytics.recentActivities.unshift(activity);
        if (this.analytics.recentActivities.length > 50) {
            this.analytics.recentActivities.pop();
        }
        
        // Emit event
        this.emit('activity:new', activity);
        this.emit('activities:updated', this.analytics.recentActivities);
    }

    /**
     * Start periodic refresh
     */
    startPeriodicRefresh() {
        // Refresh coverage every 5 minutes
        setInterval(() => {
            this.loadPlatformCoverage();
        }, 5 * 60 * 1000);
        
        // Refresh analytics every 15 minutes
        setInterval(() => {
            this.loadAnalytics();
        }, 15 * 60 * 1000);
    }

    /**
     * Get current user ID
     */
    getCurrentUserId() {
        // Try to get from session storage or global state
        return window.currentUserId || 
               sessionStorage.getItem('userId') || 
               document.querySelector('[data-user-id]')?.dataset.userId;
    }

    /**
     * Show notification
     */
    showNotification(message, type = 'info') {
        // Check if notification system exists
        if (window.showNotification) {
            window.showNotification(message, type);
        } else {
        }
    }

    /**
     * Event emitter functionality
     */
    on(event, handler) {
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, new Set());
        }
        this.eventHandlers.get(event).add(handler);
    }

    off(event, handler) {
        if (this.eventHandlers.has(event)) {
            this.eventHandlers.get(event).delete(handler);
        }
    }

    emit(event, data) {
        if (this.eventHandlers.has(event)) {
            this.eventHandlers.get(event).forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`Error in event handler for ${event}:`, error);
                }
            });
        }
    }

    /**
     * Clean up subscriptions
     */
    cleanup() {
        this.subscriptions.forEach((channel, name) => {
            channel.unsubscribe();
        });
        this.subscriptions.clear();
        this.eventHandlers.clear();
    }

    /**
     * Get platform health status
     */
    getPlatformHealth(platform) {
        const platformData = this.analytics.platforms[platform];
        if (!platformData) return 'unknown';
        
        const successRate = parseFloat(platformData.sync_success_rate);
        if (successRate >= 95) return 'excellent';
        if (successRate >= 85) return 'good';
        if (successRate >= 70) return 'fair';
        return 'poor';
    }

    /**
     * Get recent errors for a platform
     */
    getRecentErrors(platform, limit = 5) {
        return this.analytics.recentEvents
            .filter(event => 
                event.platform === platform && 
                (event.status === 'failed' || event.event_type === 'sync_failed')
            )
            .slice(0, limit);
    }

    /**
     * Calculate sync trends
     */
    calculateTrends(period = 'daily') {
        const trends = {
            totalSyncs: 0,
            successRate: 0,
            platformBreakdown: {},
            peakHours: []
        };
        
        // Calculate from analytics data
        if (this.analytics.analytics) {
            this.analytics.analytics.forEach(data => {
                trends.totalSyncs += data.total_syncs;
                // Additional calculations...
            });
        }
        
        return trends;
    }
}

// Initialize sync tracker when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.syncTracker = new SyncTracker();
    
    // Initialize if user is authenticated
    if (document.querySelector('[data-user-id]')) {
        window.syncTracker.initialize();
    }
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SyncTracker;
}