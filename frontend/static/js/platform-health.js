/**
 * 🔍 Platform Health Monitor
 * Real-time health monitoring and status updates for platform connections
 */

class PlatformHealthMonitor {
    constructor(options = {}) {
        this.options = {
            autoCheckInterval: 60000, // 1 minute
            enableAutoCheck: true,
            showHealthIndicator: true,
            ...options
        };
        
        this.healthData = {};
        this.autoCheckTimer = null;
        this.isChecking = false;
        
        this.init();
    }
    
    async init() {
        // Initial health status load
        await this.loadHealthStatus();
        
        // Start auto-checking if enabled
        if (this.options.enableAutoCheck) {
            this.startAutoCheck();
        }
        
        // Add health indicator to UI if enabled
        if (this.options.showHealthIndicator) {
            this.addHealthIndicatorToUI();
        }
    }
    
    async loadHealthStatus() {
        try {
            const response = await fetch('/api/health/platforms/status');
            const data = await response.json();
            
            if (data.success) {
                this.healthData = data.platforms;
                this.updateHealthIndicators(data.summary);
                return data;
            } else {
                console.error('Failed to load health status:', data.error);
                return null;
            }
        } catch (error) {
            console.error('Health status request failed:', error);
            return null;
        }
    }
    
    async checkAllPlatforms(showNotification = true) {
        if (this.isChecking) {
            console.log('Health check already in progress');
            return;
        }
        
        this.isChecking = true;
        
        try {
            if (showNotification) {
                this.showNotification('플랫폼 연결 상태를 확인하는 중...', 'info');
            }
            
            const response = await fetch('/api/health/platforms/check', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Update health data
                data.results.forEach(result => {
                    this.healthData[result.platform] = {
                        name: result.platform_name,
                        health_status: result.health_status,
                        last_test_at: result.last_test_at,
                        last_error: result.error
                    };
                });
                
                // Update UI indicators
                this.updateHealthIndicators(data.summary);
                
                // Update platform cards if they exist
                this.updatePlatformCards(data.results);
                
                if (showNotification) {
                    const { healthy, errors, warnings } = data.summary;
                    const message = `✅ ${healthy}개 정상, ⚠️ ${warnings}개 주의, ❌ ${errors}개 오류`;
                    this.showNotification(`플랫폼 상태 확인 완료: ${message}`, 'success');
                }
                
                return data;
            } else {
                if (showNotification) {
                    this.showNotification(`건강 상태 확인 실패: ${data.error}`, 'error');
                }
                return null;
            }
        } catch (error) {
            console.error('Platform health check failed:', error);
            if (showNotification) {
                this.showNotification('플랫폼 상태 확인 중 오류가 발생했습니다', 'error');
            }
            return null;
        } finally {
            this.isChecking = false;
        }
    }
    
    async autoCheckStale() {
        try {
            const response = await fetch('/api/health/platforms/auto-check', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success && data.results.length > 0) {
                // Update health data for auto-checked platforms
                data.results.forEach(result => {
                    if (this.healthData[result.platform]) {
                        this.healthData[result.platform].health_status = result.health_status;
                        this.healthData[result.platform].last_test_at = new Date().toISOString();
                    }
                });
                
                // Update UI silently
                this.updateHealthIndicators();
                
                console.log(`Auto-checked ${data.results.length} platforms`);
            }
        } catch (error) {
            console.error('Auto health check failed:', error);
        }
    }
    
    updateHealthIndicators(summary = null) {
        // Calculate summary if not provided
        if (!summary) {
            const platforms = Object.values(this.healthData);
            summary = {
                total: platforms.length,
                healthy: platforms.filter(p => p.health_status === 'healthy').length,
                errors: platforms.filter(p => p.health_status === 'error').length,
                warnings: platforms.filter(p => p.health_status === 'warning').length
            };
            summary.health_percentage = summary.total > 0 ? 
                Math.round((summary.healthy / summary.total) * 100) : 0;
        }
        
        // Update main health indicator
        const healthIndicator = document.querySelector('.platform-health-indicator');
        if (healthIndicator) {
            const statusClass = this.getOverallHealthClass(summary);
            healthIndicator.className = `platform-health-indicator ${statusClass}`;
            healthIndicator.innerHTML = `
                <div class=\"health-icon\">${this.getHealthIcon(statusClass)}</div>
                <div class=\"health-stats\">
                    <div class=\"health-percentage\">${summary.health_percentage}%</div>
                    <div class=\"health-details\">${summary.healthy}/${summary.total} 정상</div>
                </div>
                <div class=\"health-tooltip\">
                    <div class=\"tooltip-content\">
                        <div>✅ 정상: ${summary.healthy}</div>
                        <div>⚠️ 주의: ${summary.warnings}</div>
                        <div>❌ 오류: ${summary.errors}</div>
                        <div><small>마지막 확인: ${this.formatLastCheck()}</small></div>
                    </div>
                </div>
            `;
        }
        
        // Update individual platform status indicators
        Object.keys(this.healthData).forEach(platform => {
            const platformElement = document.querySelector(`[data-platform=\"${platform}\"]`);
            if (platformElement) {
                const statusElement = platformElement.querySelector('.platform-card-status');
                if (statusElement) {
                    const healthData = this.healthData[platform];
                    statusElement.className = `platform-card-status ${healthData.health_status}`;
                    
                    const statusTexts = {
                        healthy: '정상 작동',
                        error: '연결 오류',
                        warning: '재인증 필요',
                        not_registered: '등록되지 않음'
                    };
                    
                    statusElement.innerHTML = `
                        <span class=\"status-indicator\"></span>
                        ${statusTexts[healthData.health_status] || '상태 불명'}
                        ${healthData.last_test_at ? `<small class=\"status-time\">(${this.formatRelativeTime(healthData.last_test_at)})</small>` : ''}
                    `;
                }
            }
        });
    }
    
    updatePlatformCards(results) {
        // Try to update PlatformCard instances if they exist
        if (window.PlatformCard) {
            results.forEach(result => {
                // Trigger updatePlatformStatus if the method exists
                const event = new CustomEvent('platformHealthUpdate', {
                    detail: {
                        platform: result.platform,
                        health_status: result.health_status,
                        last_test_at: result.last_test_at,
                        success: result.success,
                        message: result.message,
                        error: result.error
                    }
                });
                document.dispatchEvent(event);
            });
        }
    }
    
    getOverallHealthClass(summary) {
        const healthPercentage = summary.health_percentage;
        
        if (healthPercentage >= 90) return 'excellent';
        if (healthPercentage >= 70) return 'good';
        if (healthPercentage >= 50) return 'fair';
        if (healthPercentage > 0) return 'poor';
        return 'critical';
    }
    
    getHealthIcon(statusClass) {
        const icons = {
            excellent: '💚',
            good: '✅',
            fair: '⚠️',
            poor: '🔶',
            critical: '❌'
        };
        return icons[statusClass] || '❓';
    }
    
    formatLastCheck() {
        return new Date().toLocaleTimeString('ko-KR');
    }
    
    formatRelativeTime(isoTime) {
        try {
            const date = new Date(isoTime);
            const now = new Date();
            const diffMinutes = Math.floor((now - date) / (1000 * 60));
            
            if (diffMinutes < 1) return '방금 전';
            if (diffMinutes < 60) return `${diffMinutes}분 전`;
            if (diffMinutes < 1440) return `${Math.floor(diffMinutes / 60)}시간 전`;
            return `${Math.floor(diffMinutes / 1440)}일 전`;
        } catch (e) {
            return '';
        }
    }
    
    addHealthIndicatorToUI() {
        // Find a suitable place to add the health indicator
        const header = document.querySelector('header') || document.querySelector('.navbar') || document.querySelector('.dashboard-header');
        
        if (header) {
            const healthIndicator = document.createElement('div');
            healthIndicator.className = 'platform-health-indicator good';
            healthIndicator.innerHTML = `
                <div class=\"health-icon\">💚</div>
                <div class=\"health-stats\">
                    <div class=\"health-percentage\">--%</div>
                    <div class=\"health-details\">로딩 중...</div>
                </div>
                <div class=\"health-tooltip\">
                    <div class=\"tooltip-content\">
                        <div>플랫폼 상태를 확인하는 중...</div>
                    </div>
                </div>
            `;
            
            // Add click handler for manual refresh
            healthIndicator.addEventListener('click', () => {
                this.checkAllPlatforms(true);
            });
            
            header.appendChild(healthIndicator);
            
            // Add CSS styles
            this.addHealthIndicatorStyles();
        }
    }
    
    addHealthIndicatorStyles() {
        if (document.getElementById('platform-health-styles')) return;
        
        const styles = document.createElement('style');
        styles.id = 'platform-health-styles';
        styles.textContent = `
            .platform-health-indicator {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 8px 12px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.3s ease;
                position: relative;
                min-width: 120px;
            }
            
            .platform-health-indicator:hover {
                background: rgba(255, 255, 255, 0.2);
                transform: translateY(-1px);
            }
            
            .platform-health-indicator.excellent { border-left: 3px solid #10b981; }
            .platform-health-indicator.good { border-left: 3px solid #059669; }
            .platform-health-indicator.fair { border-left: 3px solid #f59e0b; }
            .platform-health-indicator.poor { border-left: 3px solid #ef4444; }
            .platform-health-indicator.critical { border-left: 3px solid #dc2626; }
            
            .health-icon {
                font-size: 16px;
                line-height: 1;
            }
            
            .health-stats {
                flex: 1;
                min-width: 0;
            }
            
            .health-percentage {
                font-weight: 600;
                font-size: 14px;
                color: white;
                line-height: 1;
            }
            
            .health-details {
                font-size: 11px;
                color: rgba(255, 255, 255, 0.7);
                line-height: 1;
                margin-top: 2px;
            }
            
            .health-tooltip {
                position: absolute;
                top: 100%;
                right: 0;
                margin-top: 4px;
                opacity: 0;
                visibility: hidden;
                transition: all 0.3s ease;
                z-index: 1000;
            }
            
            .platform-health-indicator:hover .health-tooltip {
                opacity: 1;
                visibility: visible;
            }
            
            .tooltip-content {
                background: #1f2937;
                color: white;
                padding: 8px 12px;
                border-radius: 6px;
                font-size: 12px;
                white-space: nowrap;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            }
            
            .tooltip-content div {
                margin: 2px 0;
            }
            
            .tooltip-content small {
                color: rgba(255, 255, 255, 0.6);
            }
            
            .status-time {
                color: rgba(255, 255, 255, 0.5);
                font-size: 10px;
                margin-left: 4px;
            }
        `;
        
        document.head.appendChild(styles);
    }
    
    startAutoCheck() {
        if (this.autoCheckTimer) {
            clearInterval(this.autoCheckTimer);
        }
        
        // Run auto-check for stale platforms periodically
        this.autoCheckTimer = setInterval(() => {
            this.autoCheckStale();
        }, this.options.autoCheckInterval);
        
        console.log(`Platform health auto-check started (${this.options.autoCheckInterval}ms interval)`);
    }
    
    stopAutoCheck() {
        if (this.autoCheckTimer) {
            clearInterval(this.autoCheckTimer);
            this.autoCheckTimer = null;
            console.log('Platform health auto-check stopped');
        }
    }
    
    showNotification(message, type = 'info') {
        // Use centralized notification system
        if (window.NotificationUtils) {
            return window.NotificationUtils.show(message, type);
        }
        
        // Fallback
        return window.showNotification ? window.showNotification(message, type) : console.log(message);
    }
    
    destroy() {
        this.stopAutoCheck();
        
        // Remove health indicator
        const healthIndicator = document.querySelector('.platform-health-indicator');
        if (healthIndicator) {
            healthIndicator.remove();
        }
        
        // Remove styles
        const styles = document.getElementById('platform-health-styles');
        if (styles) {
            styles.remove();
        }
    }
}

// Auto-initialize if not in a module environment
if (typeof window !== 'undefined') {
    window.PlatformHealthMonitor = PlatformHealthMonitor;
    
    // Auto-start health monitoring on page load
    document.addEventListener('DOMContentLoaded', () => {
        if (!window.platformHealthMonitor) {
            window.platformHealthMonitor = new PlatformHealthMonitor({
                enableAutoCheck: true,
                showHealthIndicator: true
            });
        }
    });
}