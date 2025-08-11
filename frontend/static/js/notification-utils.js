/**
 * 🔔 Notification Utilities
 * Centralized notification system to avoid code duplication
 */

window.NotificationUtils = {
    /**
     * Show a notification message
     * @param {string} message - The message to display
     * @param {string} type - Type of notification ('success', 'error', 'info', 'warning')
     * @param {number} duration - Duration in milliseconds (default: 3000)
     */
    show(message, type = 'info', duration = 3000) {
        // Remove existing notification if present
        const existing = document.querySelector('.global-notification');
        if (existing) {
            existing.remove();
        }

        const notification = document.createElement('div');
        notification.className = `global-notification notification ${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 16px 24px;
            border-radius: 12px;
            color: white;
            font-weight: 500;
            z-index: 10000;
            transform: translateX(400px);
            transition: transform 0.3s ease;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
            max-width: 350px;
            word-wrap: break-word;
            ${type === 'success' ? 'background: linear-gradient(135deg, #10b981, #059669);' : ''}
            ${type === 'error' ? 'background: linear-gradient(135deg, #ef4444, #dc2626);' : ''}
            ${type === 'info' ? 'background: linear-gradient(135deg, #3b82f6, #2563eb);' : ''}
            ${type === 'warning' ? 'background: linear-gradient(135deg, #f59e0b, #d97706);' : ''}
        `;
        
        document.body.appendChild(notification);
        
        // Animation
        setTimeout(() => notification.style.transform = 'translateX(0)', 100);
        setTimeout(() => notification.style.transform = 'translateX(400px)', duration);
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, duration + 500);
        
        return notification;
    },

    /**
     * Show success notification
     */
    success(message, duration) {
        return this.show(message, 'success', duration);
    },

    /**
     * Show error notification
     */
    error(message, duration) {
        return this.show(message, 'error', duration);
    },

    /**
     * Show info notification
     */
    info(message, duration) {
        return this.show(message, 'info', duration);
    },

    /**
     * Show warning notification
     */
    warning(message, duration) {
        return this.show(message, 'warning', duration);
    }
};

// Backward compatibility - global function
window.showNotification = (message, type, duration) => {
    return window.NotificationUtils.show(message, type, duration);
};