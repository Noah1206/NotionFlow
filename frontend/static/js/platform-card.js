/**
 * 🔗 PlatformCard Component
 * Reusable platform card component for registration and connection management
 */

class PlatformCard {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            showRegistrationButton: true,
            showConnectionButtons: false,
            calendarId: null,
            onRegister: null,
            onConnect: null,
            onDisconnect: null,
            ...options
        };
        
        this.platforms = {};
        this.registeredPlatforms = {};
        
        this.init();
    }
    
    async init() {
        await this.loadPlatforms();
        await this.loadRegisteredPlatforms();
        this.render();
        this.attachEventListeners();
    }
    
    async loadPlatforms() {
        try {
            const response = await fetch('/api/keys/platforms');
            const data = await response.json();
            
            if (data.success) {
                this.platforms = data.platforms;
            }
        } catch (error) {
            // Console error removed
        }
    }
    
    async loadRegisteredPlatforms() {
        try {
            const response = await fetch('/api/platforms/list');
            const data = await response.json();
            
            if (data.success) {
                this.registeredPlatforms = data.platforms;
            }
        } catch (error) {
            // Console error removed
        }
    }
    
    render() {
        if (!this.container) return;
        
        const platformCards = Object.keys(this.platforms).map(platformId => {
            const platform = this.platforms[platformId];
            const registered = this.registeredPlatforms[platformId];
            
            return this.createPlatformCard(platformId, platform, registered);
        }).join('');
        
        this.container.innerHTML = `
            <div class="platform-cards-grid">
                ${platformCards}
            </div>
        `;
    }
    
    createPlatformCard(platformId, platform, registered) {
        const isRegistered = registered && registered.registered;
        const healthStatus = registered ? registered.health_status : 'not_registered';
        
        return `
            <div class="platform-registration-card ${isRegistered ? 'registered' : 'unregistered'}" 
                 data-platform="${platformId}">
                <div class="platform-card-header">
                    <div class="platform-card-info">
                        <div class="platform-card-icon ${platformId}">
                            ${this.getPlatformIcon(platformId)}
                        </div>
                        <div class="platform-card-details">
                            <h3 class="platform-card-name">${platform.name}</h3>
                            <p class="platform-card-description">${platform.description || this.getDefaultDescription(platformId)}</p>
                            <div class="platform-card-status ${healthStatus}">
                                <span class="status-indicator"></span>
                                ${this.getStatusText(healthStatus, isRegistered)}
                            </div>
                        </div>
                    </div>
                    <div class="platform-card-actions">
                        ${this.createActionButtons(platformId, isRegistered, registered)}
                    </div>
                </div>
                
                ${!isRegistered && this.options.showRegistrationButton ? this.createRegistrationForm(platformId, platform) : ''}
            </div>
        `;
    }
    
    createActionButtons(platformId, isRegistered, registered) {
        let buttons = '';
        
        if (isRegistered) {
            buttons += `
                <button class="btn-test-connection" data-platform="${platformId}">
                    <span class="btn-icon">🔍</span>
                    <span class="btn-text">테스트</span>
                </button>
                <button class="btn-unregister" data-platform="${platformId}">
                    <span class="btn-icon">🗑️</span>
                    <span class="btn-text">해제</span>
                </button>
            `;
            
            if (this.options.showConnectionButtons && this.options.calendarId) {
                buttons += `
                    <button class="btn-connect-to-calendar" data-platform="${platformId}" data-calendar="${this.options.calendarId}">
                        <span class="btn-icon">📅</span>
                        <span class="btn-text">연결</span>
                    </button>
                `;
            }
        } else if (this.options.showRegistrationButton) {
            buttons += `
                <button class="btn-register-platform" data-platform="${platformId}">
                    <span class="btn-icon">🔗</span>
                    <span class="btn-text">등록</span>
                </button>
                <button class="btn-toggle-form" data-platform="${platformId}">
                    <span class="btn-icon">⚙️</span>
                    <span class="btn-text">설정</span>
                </button>
            `;
        }
        
        return buttons;
    }
    
    createRegistrationForm(platformId, platform) {
        const fields = platform.required_fields.map(field => {
            return `
                <div class="form-group">
                    <label for="${platformId}-${field}">${this.getFieldLabel(field)}</label>
                    <input type="${this.getFieldType(field)}" 
                           id="${platformId}-${field}" 
                           name="${field}"
                           placeholder="${this.getFieldPlaceholder(platformId, field)}"
                           required>
                </div>
            `;
        }).join('');
        
        return `
            <div class="platform-registration-form" id="${platformId}-form" style="display: none;">
                <div class="form-header">
                    <h4>${platform.name} 등록</h4>
                    <p>플랫폼 연결을 위한 인증 정보를 입력하세요</p>
                </div>
                
                <form class="registration-form" data-platform="${platformId}">
                    ${fields}
                    
                    <div class="form-actions">
                        <button type="button" class="btn-cancel" data-platform="${platformId}">취소</button>
                        <button type="submit" class="btn-register-submit">
                            <span class="btn-text">등록하기</span>
                            <div class="btn-loader" style="display: none;">
                                <div class="loader-spinner"></div>
                            </div>
                        </button>
                    </div>
                </form>
                
                <div class="form-help">
                    <p><strong>도움말:</strong></p>
                    <ul>
                        ${this.getHelpText(platformId)}
                    </ul>
                </div>
            </div>
        `;
    }
    
    attachEventListeners() {
        this.container.addEventListener('click', this.handleClick.bind(this));
        this.container.addEventListener('submit', this.handleSubmit.bind(this));
    }
    
    handleClick(event) {
        const target = event.target.closest('button');
        if (!target) return;
        
        event.preventDefault();
        
        const platform = target.dataset.platform;
        const calendarId = target.dataset.calendar;
        
        if (target.classList.contains('btn-register-platform')) {
            this.handleOneClickRegister(platform);
        } else if (target.classList.contains('btn-toggle-form')) {
            this.toggleRegistrationForm(platform);
        } else if (target.classList.contains('btn-cancel')) {
            this.toggleRegistrationForm(platform, false);
        } else if (target.classList.contains('btn-test-connection')) {
            this.testConnection(platform);
        } else if (target.classList.contains('btn-unregister')) {
            this.unregisterPlatform(platform);
        } else if (target.classList.contains('btn-connect-to-calendar')) {
            this.connectToCalendar(platform, calendarId);
        }
    }
    
    async handleSubmit(event) {
        if (!event.target.classList.contains('registration-form')) return;
        
        event.preventDefault();
        
        const platform = event.target.dataset.platform;
        const formData = new FormData(event.target);
        const credentials = {};
        
        for (let [key, value] of formData.entries()) {
            credentials[key] = value.trim();
        }
        
        await this.registerPlatform(platform, credentials, event.target);
    }
    
    async handleOneClickRegister(platform) {
        try {
            // Apple의 경우 마법사로 위임 (apple-setup-wizard.js에서 오버라이드됨)
            if (platform === 'apple' && window.appleWizard) {
                window.appleWizard.start(platform);
                return;
            }
            
            // Check if platform supports OAuth
            const oauthPlatforms = ['google', 'notion', 'slack', 'outlook'];
            const supportsOAuth = oauthPlatforms.includes(platform);
            
            if (supportsOAuth) {
                // Use OAuth flow
                await this.registerWithOAuth(platform);
            } else {
                // Show form for API key registration
                this.toggleRegistrationForm(platform, true);
                this.showNotification(`${platform} 설정 양식을 확인하고 정보를 입력하세요`, 'info');
            }
        } catch (error) {
            // Console error removed
            this.showNotification('원클릭 등록에 실패했습니다', 'error');
        }
    }
    
    async registerWithOAuth(platform) {
        try {
            // Show loading state on button
            const button = document.querySelector(`[data-platform="${platform}"] .btn-one-click`);
            const originalContent = button ? button.innerHTML : '';
            
            if (button) {
                button.innerHTML = `
                    <div class="btn-loader" style="display: flex;">
                        <div class="loader-spinner"></div>
                    </div>
                    <span class="btn-text">연결 중...</span>
                `;
                button.disabled = true;
            }
            
            // Open OAuth popup
            const popup = this.openOAuthPopup(platform);
            
            // Wait for OAuth completion
            const result = await this.waitForOAuthCompletion(popup);
            
            if (result.success) {
                this.showNotification(`${platform.toUpperCase()} 연결 성공!`, 'success');

                // Notion 연동 성공 시에만 모달 표시
                if (platform === 'notion') {
                    this.showNotionSuccessModal();
                }

                if (this.options.onRegister) {
                    this.options.onRegister({
                        id: platform,
                        name: platform.toUpperCase()
                    }, {
                        platform_name: platform.toUpperCase(),
                        user_info: result.user_info,
                        connection_method: 'oauth'
                    });
                }
            } else {
                throw new Error(result.error || 'OAuth 연결에 실패했습니다');
            }
            
        } catch (error) {
            // Console error removed
            this.showNotification(error.message || 'OAuth 연결에 실패했습니다', 'error');
        } finally {
            // Restore button state
            const button = document.querySelector(`[data-platform="${platform}"] .btn-one-click`);
            if (button) {
                button.innerHTML = originalContent;
                button.disabled = false;
            }
        }
    }
    
    openOAuthPopup(platform) {
        const width = 500;
        const height = 700;
        const left = (screen.width - width) / 2;
        const top = (screen.height - height) / 2;
        
        const popup = window.open(
            `/oauth/${platform}/authorize`,
            `oauth_${platform}`,
            `width=${width},height=${height},left=${left},top=${top},scrollbars=yes,resizable=yes`
        );
        
        if (!popup) {
            throw new Error('팝업이 차단되었습니다. OAuth 인증을 위해 팝업을 허용해주세요.');
        }
        
        return popup;
    }
    
    waitForOAuthCompletion(popup) {
        return new Promise((resolve, reject) => {
            const checkInterval = 500;
            let timeoutCount = 0;
            const maxTimeout = 240; // 2분 타임아웃
            
            // 팝업으로부터 메시지 수신 대기
            const messageHandler = (event) => {
                // 보안을 위한 origin 검증
                if (event.origin !== window.location.origin) {
                    return;
                }
                
                if (event.data && event.data.type) {
                    if (event.data.type === 'oauth_success') {
                        cleanup();
                        resolve({
                            success: true,
                            platform: event.data.platform,
                            user_info: event.data.user_info
                        });
                    } else if (event.data.type === 'oauth_error') {
                        cleanup();
                        reject(new Error(event.data.error || 'OAuth 인증에 실패했습니다'));
                    }
                }
            };
            
            // 팝업이 수동으로 닫혔는지 확인
            const checkClosed = setInterval(() => {
                if (popup.closed) {
                    cleanup();
                    reject(new Error('OAuth 인증이 취소되었습니다'));
                    return;
                }
                
                timeoutCount++;
                if (timeoutCount >= maxTimeout) {
                    cleanup();
                    if (!popup.closed) {
                        popup.close();
                    }
                    reject(new Error('OAuth 인증 시간이 초과되었습니다'));
                }
            }, checkInterval);
            
            const cleanup = () => {
                window.removeEventListener('message', messageHandler);
                clearInterval(checkClosed);
                if (!popup.closed) {
                    popup.close();
                }
            };
            
            window.addEventListener('message', messageHandler);
        });
    }
    
    toggleRegistrationForm(platform, show = null) {
        const form = document.getElementById(`${platform}-form`);
        if (!form) return;
        
        const isVisible = form.style.display !== 'none';
        form.style.display = show !== null ? (show ? 'block' : 'none') : (isVisible ? 'none' : 'block');
    }
    
    async registerPlatform(platform, credentials, form) {
        const submitButton = form.querySelector('.btn-register-submit');
        const buttonText = submitButton.querySelector('.btn-text');
        const loader = submitButton.querySelector('.btn-loader');
        
        // Show loading state
        submitButton.disabled = true;
        buttonText.style.display = 'none';
        loader.style.display = 'flex';
        
        try {
            const response = await fetch('/api/platforms/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    platform: platform,
                    credentials: credentials
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification(data.message, 'success');
                this.toggleRegistrationForm(platform, false);
                
                // Refresh the display
                await this.loadRegisteredPlatforms();
                this.render();
                this.attachEventListeners();
                
                // Call callback if provided
                if (this.options.onRegister) {
                    this.options.onRegister(platform, data);
                }
            } else {
                this.showNotification(data.error || '등록에 실패했습니다', 'error');
            }
        } catch (error) {
            // Console error removed
            this.showNotification('등록 중 오류가 발생했습니다', 'error');
        } finally {
            // Restore button state
            submitButton.disabled = false;
            buttonText.style.display = 'inline';
            loader.style.display = 'none';
        }
    }
    
    async testConnection(platform) {
        const button = document.querySelector(`[data-platform="${platform}"] .btn-test-connection`);
        const originalContent = button.innerHTML;
        
        try {
            // Show loading state
            button.innerHTML = `
                <div class="btn-loader" style="display: flex;">
                    <div class="loader-spinner"></div>
                </div>
                <span class="btn-text">테스트 중...</span>
            `;
            button.disabled = true;
            
            const response = await fetch(`/api/platforms/test/${platform}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification(`${platform.toUpperCase()} 연결 테스트 성공: ${data.message}`, 'success');
                
                // Update the platform card's status immediately
                this.updatePlatformStatus(platform, data.health_status, data.last_test_at);
            } else {
                this.showNotification(`연결 테스트 실패: ${data.error}`, 'error');
                
                // Update status to error
                this.updatePlatformStatus(platform, 'error', data.last_test_at);
                
                // Show re-authentication hint if needed
                if (data.requires_reauth) {
                    this.showNotification(`${platform.toUpperCase()} 재인증이 필요합니다. 원클릭 등록을 다시 시도해주세요.`, 'info');
                }
            }
        } catch (error) {
            // Console error removed
            this.showNotification('연결 테스트 중 오류가 발생했습니다', 'error');
            this.updatePlatformStatus(platform, 'error');
        } finally {
            // Restore button state
            button.innerHTML = originalContent;
            button.disabled = false;
        }
    }
    
    async unregisterPlatform(platform) {
        if (!confirm(`${platform} 플랫폼 등록을 해제하시겠습니까? 모든 캘린더 연결도 함께 해제됩니다.`)) {
            return;
        }
        
        try {
            const response = await fetch(`/api/platforms/unregister/${platform}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification(data.message, 'success');
                
                // Refresh the display
                await this.loadRegisteredPlatforms();
                this.render();
                this.attachEventListeners();
            } else {
                this.showNotification(data.error || '등록 해제에 실패했습니다', 'error');
            }
        } catch (error) {
            // Console error removed
            this.showNotification('등록 해제 중 오류가 발생했습니다', 'error');
        }
    }
    
    async connectToCalendar(platform, calendarId) {
        if (!calendarId) return;
        
        try {
            const response = await fetch(`/api/calendars/${calendarId}/connect`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    platform: platform,
                    sync_config: {
                        sync_enabled: true,
                        sync_direction: 'both',
                        sync_frequency: 15,
                        auto_sync: true
                    }
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                let message = data.message;
                
                // Handle auto-import results for Google Calendar
                if (data.auto_import && platform === 'google') {
                    if (data.auto_import.success) {
                        const { imported_count, failed_count } = data.auto_import;
                        message += ` | 자동으로 ${imported_count}개의 일정을 가져왔습니다`;
                        if (failed_count > 0) {
                            message += ` (${failed_count}개 실패)`;
                        }
                    } else {
                        message += ' | 일정 자동 가져오기 실패: ' + data.auto_import.error;
                    }
                } else if (platform === 'google') {
                    // Check if Google was manually disconnected to prevent auto-reconnection
                    const manuallyDisconnected = localStorage.getItem('google_manually_disconnected');
                    if (manuallyDisconnected === 'true') {
                        // Console log removed
                    } else {
                        // If no auto_import data and not manually disconnected, trigger import
                        // Console log removed
                        this.triggerGoogleImport();
                    }
                }
                
                this.showNotification(message, 'success');
                
                // Call callback if provided
                if (this.options.onConnect) {
                    this.options.onConnect(platform, calendarId, data);
                }
            } else {
                this.showNotification(data.error || '캘린더 연결에 실패했습니다', 'error');
            }
        } catch (error) {
            // Console error removed
            this.showNotification('캘린더 연결 중 오류가 발생했습니다', 'error');
        }
    }
    
    // Trigger Google Calendar import
    async triggerGoogleImport() {
        try {
            // Console log removed
            
            const response = await fetch('/api/google-calendar/auto-import', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                const message = `✅ Google Calendar 이벤트를 자동으로 가져왔습니다! (${data.imported_count}개 성공${data.failed_count > 0 ? `, ${data.failed_count}개 실패` : ''})`;
                this.showNotification(message, 'success');
                // Console log removed
            } else {
                // Console error removed
                this.showNotification('Google Calendar 이벤트 가져오기 실패: ' + (data.error || '알 수 없는 오류'), 'warning');
            }
        } catch (error) {
            // Console error removed
            // Don't show error notification to avoid disturbing user experience
            // Console log removed
        }
    }
    
    // Utility methods
    getPlatformIcon(platformId) {
        const icons = {
            notion: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M4.459 4.208c.746.606 1.026.56 2.428.466l13.215-.793c.28 0 .047-.28-.046-.326L17.86 1.968c-.42-.326-.981-.7-2.055-.607L3.01 2.295c-.466.046-.56.28-.374.466zm.793 3.08v13.904c0 .747.373 1.027 1.214.98l14.523-.84c.841-.046 1.121-.56 1.121-1.167V6.354c0-.606-.233-.933-.747-.887l-15.177.887c-.56.047-.934.373-.934 1.027zm13.748.327c.093.42 0 .84-.42.888l-.7.14v10.264c-.608.327-1.168.514-1.635.514-.748 0-.935-.234-1.495-.933l-4.577-7.186v6.952L12.21 19s0 .84-1.168.84l-3.222.186c-.093-.186 0-.653.327-.746l.84-.233V9.854L7.822 9.76c-.094-.42.14-1.026.793-1.073z"/></svg>',
            google: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 3h-1V1h-2v2H8V1H6v2H5c-1.11 0-1.99.9-1.99 2L3 19c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V8h14v11zM7 10h5v5H7z"/></svg>',
            apple: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M17 3H7c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h10c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 16c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zm2.5-4H9.5V6h5v9z"/></svg>',
            outlook: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M7.88 12.04q0 .45-.11.87-.1.41-.33.74-.22.33-.58.52-.37.2-.87.2-.51 0-.87-.2-.37-.19-.59-.52-.21-.33-.32-.74-.1-.42-.1-.87 0-.44.1-.86.11-.41.32-.73.22-.33.59-.52.36-.2.87-.2.5 0 .87.2.36.19.58.52.23.32.33.73.11.42.11.86z"/></svg>',
            slack: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M5.042 15.165a2.528 2.528 0 0 1-2.52 2.523A2.528 2.528 0 0 1 0 15.165a2.527 2.527 0 0 1 2.522-2.52h2.52v2.52z"/></svg>'
        };
        return icons[platformId] || '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"/></svg>';
    }
    
    getDefaultDescription(platformId) {
        const descriptions = {
            notion: '노트와 데이터베이스를 캘린더와 동기화',
            google: 'Google 캘린더와 실시간 동기화',
            apple: 'Apple 캘린더(iCloud)와 동기화',
            outlook: 'Microsoft Outlook 캘린더와 동기화',
            slack: 'Slack 채널로 캘린더 알림 전송'
        };
        return descriptions[platformId] || '외부 플랫폼과 연동';
    }
    
    getStatusText(healthStatus, isRegistered) {
        if (!isRegistered) return '등록되지 않음';
        
        const statusTexts = {
            healthy: '정상 작동',
            error: '오류 발생',
            warning: '주의 필요',
            not_registered: '등록되지 않음'
        };
        
        return statusTexts[healthStatus] || '상태 불명';
    }
    
    getFieldLabel(field) {
        const labels = {
            api_key: 'API 키',
            client_id: '클라이언트 ID',
            client_secret: '클라이언트 시크릿',
            webhook_url: 'Webhook URL',
            server_url: '서버 URL',
            username: '사용자명',
            password: '비밀번호'
        };
        return labels[field] || field.replace('_', ' ').toUpperCase();
    }
    
    getFieldType(field) {
        const types = {
            api_key: 'password',
            client_secret: 'password',
            password: 'password',
            webhook_url: 'url',
            server_url: 'url',
            username: 'email'
        };
        return types[field] || 'text';
    }
    
    getFieldPlaceholder(platformId, field) {
        const placeholders = {
            notion: {
                api_key: 'secret_으로 시작하는 토큰을 입력하세요'
            },
            google: {
                client_id: 'Google Cloud Console에서 발급받은 클라이언트 ID',
                client_secret: 'Google Cloud Console에서 발급받은 클라이언트 시크릿'
            },
            slack: {
                webhook_url: 'https://hooks.slack.com/services/...'
            },
            apple: {
                server_url: 'https://caldav.icloud.com',
                username: 'your-apple-id@icloud.com',
                password: '앱 전용 비밀번호'
            },
            outlook: {
                client_id: 'Azure Portal에서 발급받은 클라이언트 ID',
                client_secret: 'Azure Portal에서 발급받은 클라이언트 시크릿'
            }
        };
        
        return placeholders[platformId]?.[field] || `${field}을(를) 입력하세요`;
    }
    
    getHelpText(platformId) {
        const helpTexts = {
            notion: '<li>Notion 설정에서 "내 연결"으로 이동</li><li>"새 연결" 클릭 후 Internal Integration 생성</li><li>API 키를 복사하여 입력</li>',
            google: '<li>Google Cloud Console에서 새 프로젝트 생성</li><li>Calendar API 활성화</li><li>OAuth 2.0 클라이언트 ID 생성</li>',
            slack: '<li>Slack 워크스페이스 설정으로 이동</li><li>"앱" > "수신 웹후크" 설정</li><li>채널 선택 후 웹후크 URL 복사</li>',
            apple: '<li>Apple ID 설정에서 2단계 인증 활성화</li><li>"앱 전용 암호" 생성</li><li>iCloud 캘린더 접근 권한 필요</li>',
            outlook: '<li>Azure Portal에서 새 앱 등록</li><li>Microsoft Graph API 권한 부여</li><li>클라이언트 시크릿 생성</li>'
        };
        
        return helpTexts[platformId] || '<li>플랫폼 설정 페이지에서 API 키를 발급받으세요</li>';
    }
    
    updatePlatformStatus(platform, healthStatus, lastTestAt = null) {
        const platformCard = document.querySelector(`[data-platform="${platform}"]`);
        if (!platformCard) return;
        
        const statusElement = platformCard.querySelector('.platform-card-status');
        const statusIndicator = statusElement.querySelector('.status-indicator');
        
        // Update status class
        statusElement.className = `platform-card-status ${healthStatus}`;
        
        // Update status text
        const statusTexts = {
            healthy: '정상 작동',
            error: '연결 오류',
            warning: '주의 필요',
            not_registered: '등록되지 않음'
        };
        
        statusElement.innerHTML = `
            <span class="status-indicator"></span>
            ${statusTexts[healthStatus] || '상태 불명'}
            ${lastTestAt ? `<small class="status-time">(${this.formatLastTestTime(lastTestAt)})</small>` : ''}
        `;
        
        // Update registered platforms data
        if (this.registeredPlatforms[platform]) {
            this.registeredPlatforms[platform].health_status = healthStatus;
            this.registeredPlatforms[platform].last_test_at = lastTestAt;
        }
    }
    
    formatLastTestTime(isoTime) {
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

    showNotification(message, type = 'info') {
        // Use centralized notification system
        if (window.NotificationUtils) {
            return window.NotificationUtils.show(message, type);
        }

        // Fallback for backward compatibility
        return window.showNotification ? window.showNotification(message, type) : console.log(`${type}: ${message}`);
    }

    showNotionSuccessModal() {
        // UnifiedSyncModal이 있으면 사용, 없으면 기본 알림만 표시
        if (window.UnifiedSyncModal) {
            try {
                // 모달 인스턴스가 있으면 재사용, 없으면 새로 생성
                if (!window.unifiedSyncModalInstance) {
                    window.unifiedSyncModalInstance = new window.UnifiedSyncModal();
                }

                // 모달 열기
                if (window.unifiedSyncModalInstance.openModal) {
                    window.unifiedSyncModalInstance.openModal();
                } else {
                    // Console warn removed
                }
            } catch (error) {
                // Console error removed
                this.showNotionFallbackModal();
            }
        } else {
            this.showNotionFallbackModal();
        }
    }

    showNotionFallbackModal() {
        // 간단한 확인 모달 표시
        const shouldOpenSync = confirm('Notion 연동이 완료되었습니다!\n\n캘린더와 동기화를 시작하시겠습니까?');

        if (shouldOpenSync) {
            // 캘린더 페이지가 있으면 이동
            if (window.location.pathname.includes('dashboard')) {
                window.location.href = '/calendar';
            } else {
                // 현재 페이지에서 동기화 기능이 있으면 실행
                this.showNotification('캘린더 페이지로 이동하여 동기화를 설정해주세요.', 'info');
            }
        }
    }
}

// Export for use in other files
window.PlatformCard = PlatformCard;