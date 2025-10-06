/**
 * 🍎 Apple Calendar Smart Setup Wizard
 * 반자동 설정 마법사 - 3클릭으로 Apple 캘린더 연결
 */

class AppleSetupWizard {
    constructor() {
        this.currentStep = 0;
        this.userEmail = null;
        this.appPasswordWindow = null;
        this.clipboardInterval = null;
        this.wizardModal = null;
    }
    
    /**
     * 설정 마법사 시작
     */
    async start(platform = 'apple') {
        try {
            // Step 1: Apple Sign In 시도
            const hasOAuth = await this.checkAppleOAuth();
            
            if (hasOAuth) {
                // OAuth가 설정되어 있으면 OAuth 플로우 사용
                await this.startOAuthFlow();
            } else {
                // OAuth가 없으면 스마트 가이드 모드
                this.showSmartGuide();
            }
        } catch (error) {
            console.error('Apple setup failed:', error);
            this.showManualSetup();
        }
    }
    
    /**
     * Apple OAuth 설정 확인
     * 개발자 계정이 없으므로 항상 false 반환하여 3-클릭 마법사 사용
     */
    async checkAppleOAuth() {
        // Apple 개발자 계정이 없으므로 OAuth는 사용하지 않음
        // 항상 3-클릭 설정 마법사를 사용
        return false;
    }
    
    /**
     * OAuth 플로우 시작
     */
    async startOAuthFlow() {
        const width = 500;
        const height = 700;
        const left = (screen.width - width) / 2;
        const top = (screen.height - height) / 2;
        
        const popup = window.open(
            '/oauth/apple/authorize',
            'apple_oauth',
            `width=${width},height=${height},left=${left},top=${top}`
        );
        
        // OAuth 완료 대기
        return new Promise((resolve, reject) => {
            const checkInterval = setInterval(() => {
                if (popup.closed) {
                    clearInterval(checkInterval);
                    resolve();
                }
            }, 500);
            
            // 메시지 수신 대기
            window.addEventListener('message', (event) => {
                if (event.data.type === 'oauth_success' && event.data.platform === 'apple') {
                    clearInterval(checkInterval);
                    popup.close();
                    
                    // Apple Sign In 성공 후 CalDAV 설정 필요
                    this.userEmail = event.data.user_info?.email;
                    this.showCalDAVSetup();
                    resolve();
                }
            });
        });
    }
    
    /**
     * 스마트 가이드 모달 표시
     */
    showSmartGuide() {
        // 모달 HTML 생성
        const modalHTML = `
            <div id="apple-setup-wizard" class="wizard-modal">
                <div class="wizard-content">
                    <div class="wizard-header">
                        <h2>🍎 Apple 캘린더 간편 연결</h2>
                        <button class="wizard-close" onclick="appleWizard.close()">×</button>
                    </div>
                    
                    <div class="wizard-steps">
                        <div class="step active" data-step="1">
                            <span class="step-number">1</span>
                            <span class="step-title">Apple ID 입력</span>
                        </div>
                        <div class="step" data-step="2">
                            <span class="step-number">2</span>
                            <span class="step-title">앱 암호 생성</span>
                        </div>
                        <div class="step" data-step="3">
                            <span class="step-number">3</span>
                            <span class="step-title">연결 완료</span>
                        </div>
                    </div>
                    
                    <div class="wizard-body">
                        <!-- Step 1: Email Input -->
                        <div class="wizard-step-content" id="step1">
                            <div class="step-icon">📧</div>
                            <h3>Apple ID 입력</h3>
                            <p>iCloud 캘린더에 사용하는 Apple ID를 입력해주세요.</p>
                            <input type="email" 
                                   id="apple-email-input" 
                                   placeholder="your-email@icloud.com"
                                   class="wizard-input">
                            <button class="wizard-btn primary" onclick="appleWizard.validateEmail()">
                                다음 단계 →
                            </button>
                        </div>
                        
                        <!-- Step 2: App Password Generation -->
                        <div class="wizard-step-content hidden" id="step2">
                            <div class="step-icon">🔐</div>
                            <h3>앱 전용 암호 생성</h3>
                            <p>Apple ID 설정 페이지가 열립니다. 다음 단계를 따라주세요:</p>
                            
                            <div class="instruction-box">
                                <ol>
                                    <li>Apple ID로 로그인</li>
                                    <li><strong>"앱 암호"</strong> 섹션 찾기</li>
                                    <li><strong>"암호 생성"</strong> 클릭</li>
                                    <li>레이블: <code>NotionFlow</code> 입력</li>
                                    <li>생성된 암호 <strong>복사</strong> (xxxx-xxxx-xxxx-xxxx)</li>
                                </ol>
                            </div>
                            
                            <button class="wizard-btn primary" onclick="appleWizard.openAppPasswordPage()">
                                🌐 Apple ID 설정 페이지 열기
                            </button>
                            
                            <div class="password-input-section">
                                <p>생성한 앱 암호를 여기에 붙여넣기:</p>
                                <input type="text" 
                                       id="app-password-input" 
                                       placeholder="xxxx-xxxx-xxxx-xxxx"
                                       class="wizard-input"
                                       maxlength="19">
                                <button class="wizard-btn secondary" onclick="appleWizard.pasteFromClipboard()">
                                    📋 붙여넣기
                                </button>
                            </div>
                            
                            <button class="wizard-btn primary" 
                                    onclick="appleWizard.connectCalDAV()"
                                    id="connect-btn"
                                    disabled>
                                연결하기
                            </button>
                        </div>
                        
                        <!-- Step 3: Success -->
                        <div class="wizard-step-content hidden" id="step3">
                            <div class="step-icon success">✅</div>
                            <h3>연결 완료!</h3>
                            <p>Apple 캘린더가 성공적으로 연결되었습니다.</p>
                            
                            <div class="success-info">
                                <div class="info-item">
                                    <span class="label">연결된 계정:</span>
                                    <span class="value" id="connected-email"></span>
                                </div>
                                <div class="info-item">
                                    <span class="label">서버:</span>
                                    <span class="value">caldav.icloud.com</span>
                                </div>
                                <div class="info-item">
                                    <span class="label">상태:</span>
                                    <span class="value status-healthy">정상 작동</span>
                                </div>
                            </div>
                            
                            <button class="wizard-btn primary" onclick="appleWizard.close()">
                                완료
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // 스타일 추가
        if (!document.getElementById('apple-wizard-styles')) {
            const styles = document.createElement('style');
            styles.id = 'apple-wizard-styles';
            styles.textContent = this.getWizardStyles();
            document.head.appendChild(styles);
        }
        
        // 모달 추가
        const modalContainer = document.createElement('div');
        modalContainer.innerHTML = modalHTML;
        document.body.appendChild(modalContainer);
        
        this.wizardModal = document.getElementById('apple-setup-wizard');
        
        // 클립보드 감지 시작
        this.startClipboardDetection();
    }
    
    /**
     * 이메일 유효성 검증
     */
    validateEmail() {
        const emailInput = document.getElementById('apple-email-input');
        const email = emailInput.value.trim();
        
        if (!email || !email.includes('@')) {
            this.showError('올바른 이메일 주소를 입력해주세요.');
            return;
        }
        
        this.userEmail = email;
        this.moveToStep(2);
    }
    
    /**
     * 앱 암호 생성 페이지 열기
     */
    openAppPasswordPage() {
        // Apple ID 설정 페이지 열기
        this.appPasswordWindow = window.open(
            'https://appleid.apple.com/account/manage',
            'apple_id_settings',
            'width=1200,height=800'
        );
        
        // 버튼 상태 변경
        const openBtn = event.target;
        openBtn.textContent = '⏳ 페이지가 열렸습니다...';
        openBtn.disabled = true;
        
        // 암호 입력 섹션 활성화
        setTimeout(() => {
            document.querySelector('.password-input-section').classList.add('active');
        }, 2000);
        
        // 창 닫힘 감지
        const checkClosed = setInterval(() => {
            if (this.appPasswordWindow && this.appPasswordWindow.closed) {
                clearInterval(checkClosed);
                openBtn.textContent = '🌐 Apple ID 설정 페이지 다시 열기';
                openBtn.disabled = false;
            }
        }, 1000);
    }
    
    /**
     * 클립보드에서 붙여넣기
     */
    async pasteFromClipboard() {
        try {
            const text = await navigator.clipboard.readText();
            const passwordInput = document.getElementById('app-password-input');
            
            // Apple 앱 암호 형식 검증 (xxxx-xxxx-xxxx-xxxx)
            const cleanPassword = text.replace(/\s/g, '');
            if (cleanPassword.match(/^[a-z]{4}-[a-z]{4}-[a-z]{4}-[a-z]{4}$/)) {
                passwordInput.value = cleanPassword;
                this.validatePassword();
                this.showSuccess('암호가 자동으로 입력되었습니다!');
            } else {
                this.showError('올바른 앱 암호 형식이 아닙니다.');
            }
        } catch (error) {
            // 클립보드 접근 권한이 없는 경우
            this.showError('클립보드 접근 권한이 필요합니다. 수동으로 붙여넣기 해주세요.');
        }
    }
    
    /**
     * 클립보드 자동 감지
     */
    startClipboardDetection() {
        // 암호 입력 필드 변경 감지
        const passwordInput = document.getElementById('app-password-input');
        if (passwordInput) {
            passwordInput.addEventListener('input', () => {
                this.validatePassword();
            });
            
            // 붙여넣기 이벤트 감지
            passwordInput.addEventListener('paste', (e) => {
                setTimeout(() => this.validatePassword(), 100);
            });
        }
    }
    
    /**
     * 암호 유효성 검증
     */
    validatePassword() {
        const passwordInput = document.getElementById('app-password-input');
        const connectBtn = document.getElementById('connect-btn');
        const password = passwordInput.value.trim();
        
        // Apple 앱 암호 형식 확인
        if (password.match(/^[a-z]{4}-[a-z]{4}-[a-z]{4}-[a-z]{4}$/)) {
            connectBtn.disabled = false;
            connectBtn.classList.add('ready');
            passwordInput.classList.add('valid');
        } else {
            connectBtn.disabled = true;
            connectBtn.classList.remove('ready');
            passwordInput.classList.remove('valid');
        }
    }
    
    /**
     * CalDAV 연결
     */
    async connectCalDAV() {
        const password = document.getElementById('app-password-input').value.trim();
        const connectBtn = document.getElementById('connect-btn');
        
        if (!this.userEmail || !password) {
            this.showError('이메일과 암호를 모두 입력해주세요.');
            return;
        }
        
        // 로딩 상태
        connectBtn.disabled = true;
        connectBtn.innerHTML = '<span class="spinner"></span> 연결 중...';
        
        try {
            // API 호출
            const response = await fetch('/api/platforms/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    platform: 'apple',
                    credentials: {
                        server_url: 'https://caldav.icloud.com',
                        username: this.userEmail,
                        password: password
                    }
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // 성공
                document.getElementById('connected-email').textContent = this.userEmail;
                this.moveToStep(3);

                // 플랫폼 카드를 연결된 상태로 표시 (연결해제 버튼과 캘린더 변경 버튼 표시)
                if (window.markPlatformConnected) {
                    window.markPlatformConnected('apple');
                    console.log('✅ [APPLE WIZARD] Platform marked as connected with change calendar button');
                }

                // 플랫폼 카드 업데이트 (API 키 페이지의 함수 사용)
                if (window.updatePlatformStatus) {
                    window.updatePlatformStatus('apple', 'connected');
                    console.log('✅ [APPLE WIZARD] Platform status updated to connected');
                }

                // 플랫폼 상태 새로고침 (모든 플랫폼 상태 업데이트)
                if (window.loadAllPlatformStatus) {
                    window.loadAllPlatformStatus();
                    console.log('✅ [APPLE WIZARD] All platform statuses refreshed');
                }

                // ✅ 모든 플랫폼 상태 재검사 (크로스 플랫폼 버튼 상태 격리 보장)
                if (window.updateAllPlatformStatus) {
                    window.updateAllPlatformStatus();
                    console.log('✅ [APPLE WIZARD] Cross-platform button states updated');
                }

                // 연동된 캘린더 정보 새로고침
                if (window.loadSyncedCalendars) {
                    window.loadSyncedCalendars();
                    console.log('✅ [APPLE WIZARD] Synced calendars refreshed');
                }

                // Apple Calendar 연결 성공 후 NotionFlow 캘린더 선택 팝업 표시
                // 마법사를 닫고 캘린더 선택 모달을 표시하기 위해 타이머 설정
                setTimeout(() => {
                    // 마법사가 표시되어 있으면 먼저 닫기
                    if (this.wizardModal) {
                        this.wizardModal.style.display = 'none';
                    }

                    // 캘린더 선택 모달 표시
                    this.showCalendarSelectionModal();
                }, 1000);
            } else {
                throw new Error(data.error || '연결 실패');
            }
        } catch (error) {
            console.error('CalDAV connection failed:', error);
            this.showError(`연결 실패: ${error.message}`);
            
            // 버튼 복구
            connectBtn.disabled = false;
            connectBtn.innerHTML = '연결하기';
        }
    }
    
    /**
     * 단계 이동
     */
    moveToStep(stepNumber) {
        // 모든 단계 숨기기
        document.querySelectorAll('.wizard-step-content').forEach(content => {
            content.classList.add('hidden');
        });
        
        // 현재 단계 표시
        document.getElementById(`step${stepNumber}`).classList.remove('hidden');
        
        // 단계 인디케이터 업데이트
        document.querySelectorAll('.wizard-steps .step').forEach(step => {
            const num = parseInt(step.dataset.step);
            if (num < stepNumber) {
                step.classList.add('completed');
                step.classList.remove('active');
            } else if (num === stepNumber) {
                step.classList.add('active');
                step.classList.remove('completed');
            } else {
                step.classList.remove('active', 'completed');
            }
        });
        
        this.currentStep = stepNumber;
    }
    
    /**
     * 수동 설정 폼 표시 (폴백)
     */
    showManualSetup() {
        // 기존 수동 설정 폼 표시
        const platformCard = document.querySelector('[data-platform="apple"]');
        if (platformCard) {
            const form = platformCard.querySelector('.platform-registration-form');
            if (form) {
                form.style.display = 'block';
            }
        }
    }
    
    /**
     * 마법사 닫기
     */
    close() {
        if (this.wizardModal) {
            this.wizardModal.remove();
        }
        
        if (this.clipboardInterval) {
            clearInterval(this.clipboardInterval);
        }
        
        if (this.appPasswordWindow && !this.appPasswordWindow.closed) {
            this.appPasswordWindow.close();
        }
    }
    
    /**
     * 에러 메시지 표시
     */
    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'wizard-error';
        errorDiv.textContent = message;
        
        const currentStep = document.querySelector('.wizard-step-content:not(.hidden)');
        if (currentStep) {
            // 기존 에러 제거
            const existingError = currentStep.querySelector('.wizard-error');
            if (existingError) existingError.remove();
            
            // 새 에러 추가
            currentStep.appendChild(errorDiv);
            
            // 3초 후 제거
            setTimeout(() => errorDiv.remove(), 3000);
        }
    }
    
    /**
     * 성공 메시지 표시
     */
    showSuccess(message) {
        const successDiv = document.createElement('div');
        successDiv.className = 'wizard-success';
        successDiv.textContent = message;
        
        const currentStep = document.querySelector('.wizard-step-content:not(.hidden)');
        if (currentStep) {
            currentStep.appendChild(successDiv);
            setTimeout(() => successDiv.remove(), 3000);
        }
    }
    
    /**
     * 알림 표시
     */
    showNotification(message, type = 'info') {
        // Use centralized notification system
        if (window.NotificationUtils) {
            return window.NotificationUtils.show(message, type);
        }
        
        // Fallback
        return window.showNotification ? window.showNotification(message, type) : console.log(message);
    }
    
    /**
     * 마법사 스타일
     */
    getWizardStyles() {
        return `
            .wizard-modal {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.7);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 10000;
                animation: fadeIn 0.3s ease;
            }
            
            .wizard-content {
                background: white;
                border-radius: 16px;
                width: 90%;
                max-width: 600px;
                max-height: 90vh;
                overflow: auto;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                animation: slideUp 0.3s ease;
            }
            
            .wizard-header {
                padding: 24px;
                border-bottom: 1px solid #e5e7eb;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .wizard-header h2 {
                margin: 0;
                font-size: 24px;
                color: #1f2937;
            }
            
            .wizard-close {
                background: none;
                border: none;
                font-size: 28px;
                color: #9ca3af;
                cursor: pointer;
                padding: 0;
                width: 32px;
                height: 32px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 8px;
                transition: all 0.2s;
            }
            
            .wizard-close:hover {
                background: #f3f4f6;
                color: #1f2937;
            }
            
            .wizard-steps {
                display: flex;
                padding: 24px;
                gap: 24px;
                border-bottom: 1px solid #e5e7eb;
            }
            
            .step {
                flex: 1;
                display: flex;
                align-items: center;
                gap: 8px;
                opacity: 0.4;
                transition: all 0.3s;
            }
            
            .step.active {
                opacity: 1;
            }
            
            .step.completed {
                opacity: 1;
            }
            
            .step.completed .step-number {
                background: #10b981;
                color: white;
            }
            
            .step.active .step-number {
                background: #3b82f6;
                color: white;
            }
            
            .step-number {
                width: 28px;
                height: 28px;
                border-radius: 50%;
                background: #e5e7eb;
                color: #9ca3af;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 600;
                font-size: 14px;
            }
            
            .step-title {
                font-size: 14px;
                color: #6b7280;
                font-weight: 500;
            }
            
            .step.active .step-title {
                color: #1f2937;
                font-weight: 600;
            }
            
            .wizard-body {
                padding: 32px;
            }
            
            .wizard-step-content {
                text-align: center;
            }
            
            .wizard-step-content.hidden {
                display: none;
            }
            
            .step-icon {
                font-size: 64px;
                margin-bottom: 24px;
            }
            
            .step-icon.success {
                color: #10b981;
                animation: bounce 0.5s ease;
            }
            
            .wizard-step-content h3 {
                margin: 0 0 12px 0;
                font-size: 20px;
                color: #1f2937;
            }
            
            .wizard-step-content p {
                color: #6b7280;
                margin-bottom: 24px;
                line-height: 1.6;
            }
            
            .wizard-input {
                width: 100%;
                padding: 12px 16px;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                font-size: 16px;
                margin-bottom: 16px;
                transition: all 0.2s;
            }
            
            .wizard-input:focus {
                outline: none;
                border-color: #3b82f6;
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            }
            
            .wizard-input.valid {
                border-color: #10b981;
            }
            
            .wizard-btn {
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                border: none;
                cursor: pointer;
                transition: all 0.2s;
                margin: 8px;
            }
            
            .wizard-btn.primary {
                background: linear-gradient(135deg, #3b82f6, #2563eb);
                color: white;
            }
            
            .wizard-btn.primary:hover:not(:disabled) {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
            }
            
            .wizard-btn.secondary {
                background: #f3f4f6;
                color: #1f2937;
            }
            
            .wizard-btn.secondary:hover {
                background: #e5e7eb;
            }
            
            .wizard-btn:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }
            
            .wizard-btn.ready {
                background: linear-gradient(135deg, #10b981, #059669);
                animation: pulse 2s infinite;
            }
            
            .instruction-box {
                background: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 16px;
                margin: 24px 0;
                text-align: left;
            }
            
            .instruction-box ol {
                margin: 0;
                padding-left: 24px;
                color: #4b5563;
            }
            
            .instruction-box li {
                margin: 8px 0;
                line-height: 1.6;
            }
            
            .instruction-box code {
                background: #fff;
                padding: 2px 6px;
                border-radius: 4px;
                font-weight: 600;
                color: #1f2937;
            }
            
            .password-input-section {
                margin-top: 24px;
                padding-top: 24px;
                border-top: 1px solid #e5e7eb;
                opacity: 0.5;
                transition: all 0.3s;
            }
            
            .password-input-section.active {
                opacity: 1;
            }
            
            .success-info {
                background: #f0fdf4;
                border: 1px solid #bbf7d0;
                border-radius: 8px;
                padding: 20px;
                margin: 24px 0;
                text-align: left;
            }
            
            .info-item {
                display: flex;
                justify-content: space-between;
                margin: 12px 0;
                color: #1f2937;
            }
            
            .info-item .label {
                font-weight: 600;
                color: #6b7280;
            }
            
            .info-item .value {
                font-weight: 500;
            }
            
            .status-healthy {
                color: #10b981;
            }
            
            .wizard-error {
                background: #fef2f2;
                color: #dc2626;
                padding: 12px;
                border-radius: 8px;
                margin-top: 16px;
                animation: shake 0.3s ease;
            }
            
            .wizard-success {
                background: #f0fdf4;
                color: #059669;
                padding: 12px;
                border-radius: 8px;
                margin-top: 16px;
                animation: slideDown 0.3s ease;
            }
            
            .spinner {
                display: inline-block;
                width: 16px;
                height: 16px;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-top-color: white;
                border-radius: 50%;
                animation: spin 0.8s linear infinite;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            
            @keyframes slideUp {
                from { transform: translateY(20px); opacity: 0; }
                to { transform: translateY(0); opacity: 1; }
            }
            
            @keyframes slideDown {
                from { transform: translateY(-10px); opacity: 0; }
                to { transform: translateY(0); opacity: 1; }
            }
            
            @keyframes bounce {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.1); }
            }
            
            @keyframes shake {
                0%, 100% { transform: translateX(0); }
                25% { transform: translateX(-5px); }
                75% { transform: translateX(5px); }
            }
            
            @keyframes pulse {
                0% { box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3); }
                50% { box-shadow: 0 4px 20px rgba(16, 185, 129, 0.5); }
                100% { box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3); }
            }
            
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
        `;
    }
    /**
     * NotionFlow 캘린더 선택 모달 표시
     */
    async showCalendarSelectionModal() {
        try {
            // 기존 모달 닫기
            if (this.wizardModal) {
                this.wizardModal.remove();
            }

            // NotionFlow 캘린더 목록 가져오기
            const response = await fetch('/api/user/calendars');
            if (!response.ok) {
                throw new Error('캘린더 목록을 가져올 수 없습니다.');
            }

            const data = await response.json();
            // Notion과 동일한 API 응답 구조 처리
            const calendars = data.personal_calendars || data.calendars || data.data || [];

            if (!data.success && !calendars.length) {
                console.error('❌ [APPLE] No calendars found in response:', data);
                this.showNotification('연동할 캘린더가 없습니다. 먼저 캘린더를 만들어주세요.', 'warning');
                return;
            }

            if (calendars.length === 0) {
                this.showNotification('연동할 캘린더가 없습니다. 먼저 캘린더를 만들어주세요.', 'warning');
                return;
            }

            // 캘린더 선택 모달 HTML 생성
            const modalHTML = `
                <div class="calendar-selection-modal" id="apple-calendar-selection">
                    <div class="modal-content">
                        <div class="modal-header">
                            <div class="header-content">
                                <div class="header-icon">🍎</div>
                                <div class="header-text">
                                    <h2>Apple Calendar 연동</h2>
                                    <p class="subtitle">연동할 NotionFlow 캘린더를 선택하세요</p>
                                </div>
                            </div>
                            <button class="close-btn" onclick="document.getElementById('apple-calendar-selection').remove()">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <line x1="18" y1="6" x2="6" y2="18"></line>
                                    <line x1="6" y1="6" x2="18" y2="18"></line>
                                </svg>
                            </button>
                        </div>
                        <div class="modal-body">
                            <div class="calendar-grid">
                                ${calendars.map(cal => `
                                    <div class="calendar-card" data-calendar-id="${cal.id}" onclick="window.appleWizard.selectCalendarForSync('${cal.id}')">
                                        <div class="calendar-card-header">
                                            <div class="calendar-color-indicator" style="background: ${cal.color}"></div>
                                            <div class="calendar-badge">
                                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                                                    <line x1="16" y1="2" x2="16" y2="6"></line>
                                                    <line x1="8" y1="2" x2="8" y2="6"></line>
                                                    <line x1="3" y1="10" x2="21" y2="10"></line>
                                                </svg>
                                            </div>
                                        </div>
                                        <div class="calendar-card-content">
                                            <h3 class="calendar-name">${cal.name}</h3>
                                            <p class="calendar-stats">
                                                <span class="event-count">${cal.event_count || 0}개 일정</span>
                                                <span class="calendar-type">Personal</span>
                                            </p>
                                        </div>
                                        <div class="calendar-card-footer">
                                            <div class="select-indicator">
                                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                                    <polyline points="20,6 9,17 4,12"></polyline>
                                                </svg>
                                            </div>
                                            <span class="select-text">선택하기</span>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                            ${calendars.length === 0 ? `
                                <div class="empty-state">
                                    <div class="empty-icon">📅</div>
                                    <h3>생성된 캘린더가 없습니다</h3>
                                    <p>먼저 NotionFlow에서 캘린더를 생성한 후 연동해주세요.</p>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `;

            // 스타일 추가
            const styles = `
                <style>
                    .calendar-selection-modal {
                        position: fixed;
                        top: 0;
                        left: 0;
                        width: 100%;
                        height: 100%;
                        background: rgba(0, 0, 0, 0.6);
                        backdrop-filter: blur(4px);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        z-index: 10000;
                        animation: fadeIn 0.2s ease-out;
                    }

                    .calendar-selection-modal .modal-content {
                        background: white;
                        border-radius: 20px;
                        width: 90%;
                        max-width: 600px;
                        max-height: 85vh;
                        overflow: hidden;
                        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
                        animation: slideUp 0.3s ease-out;
                    }

                    .calendar-selection-modal .modal-header {
                        padding: 24px 28px;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        display: flex;
                        justify-content: space-between;
                        align-items: flex-start;
                    }

                    .calendar-selection-modal .header-content {
                        display: flex;
                        align-items: center;
                        gap: 16px;
                    }

                    .calendar-selection-modal .header-icon {
                        font-size: 32px;
                        filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
                    }

                    .calendar-selection-modal .header-text h2 {
                        margin: 0 0 4px 0;
                        font-size: 24px;
                        font-weight: 600;
                        color: white;
                    }

                    .calendar-selection-modal .subtitle {
                        margin: 0;
                        font-size: 14px;
                        color: rgba(255, 255, 255, 0.9);
                        font-weight: 400;
                    }

                    .calendar-selection-modal .close-btn {
                        background: rgba(255, 255, 255, 0.1);
                        border: none;
                        border-radius: 10px;
                        width: 40px;
                        height: 40px;
                        cursor: pointer;
                        color: white;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        transition: all 0.2s ease;
                    }

                    .calendar-selection-modal .close-btn:hover {
                        background: rgba(255, 255, 255, 0.2);
                        transform: scale(1.05);
                    }

                    .calendar-selection-modal .modal-body {
                        padding: 28px;
                        max-height: calc(85vh - 120px);
                        overflow-y: auto;
                    }

                    .calendar-selection-modal .calendar-grid {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                        gap: 16px;
                    }

                    .calendar-selection-modal .calendar-card {
                        background: white;
                        border: 2px solid #f1f3f4;
                        border-radius: 16px;
                        padding: 20px;
                        cursor: pointer;
                        transition: all 0.3s ease;
                        position: relative;
                        overflow: hidden;
                    }

                    .calendar-selection-modal .calendar-card:hover {
                        border-color: #667eea;
                        transform: translateY(-2px);
                        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.15);
                    }

                    .calendar-selection-modal .calendar-card:active {
                        transform: translateY(0);
                        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2);
                    }

                    .calendar-selection-modal .calendar-card-header {
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-bottom: 16px;
                    }

                    .calendar-selection-modal .calendar-color-indicator {
                        width: 12px;
                        height: 12px;
                        border-radius: 50%;
                        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
                    }

                    .calendar-selection-modal .calendar-badge {
                        background: #f8f9fa;
                        border-radius: 8px;
                        padding: 6px;
                        color: #6c757d;
                    }

                    .calendar-selection-modal .calendar-card-content {
                        margin-bottom: 16px;
                    }

                    .calendar-selection-modal .calendar-name {
                        margin: 0 0 8px 0;
                        font-size: 18px;
                        font-weight: 600;
                        color: #2d3748;
                        line-height: 1.3;
                    }

                    .calendar-selection-modal .calendar-stats {
                        margin: 0;
                        display: flex;
                        gap: 12px;
                        align-items: center;
                    }

                    .calendar-selection-modal .event-count {
                        font-size: 13px;
                        color: #718096;
                        background: #f7fafc;
                        padding: 4px 8px;
                        border-radius: 6px;
                        font-weight: 500;
                    }

                    .calendar-selection-modal .calendar-type {
                        font-size: 12px;
                        color: #a0aec0;
                        text-transform: uppercase;
                        font-weight: 600;
                        letter-spacing: 0.5px;
                    }

                    .calendar-selection-modal .calendar-card-footer {
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        gap: 8px;
                        padding: 12px 0 0 0;
                        border-top: 1px solid #f1f3f4;
                        opacity: 0.7;
                        transition: all 0.2s ease;
                    }

                    .calendar-selection-modal .calendar-card:hover .calendar-card-footer {
                        opacity: 1;
                    }

                    .calendar-selection-modal .select-indicator {
                        color: #667eea;
                        opacity: 0;
                        transform: scale(0.8);
                        transition: all 0.2s ease;
                    }

                    .calendar-selection-modal .calendar-card:hover .select-indicator {
                        opacity: 1;
                        transform: scale(1);
                    }

                    .calendar-selection-modal .select-text {
                        font-size: 14px;
                        font-weight: 500;
                        color: #667eea;
                    }

                    .calendar-selection-modal .empty-state {
                        text-align: center;
                        padding: 60px 20px;
                        color: #718096;
                    }

                    .calendar-selection-modal .empty-icon {
                        font-size: 64px;
                        margin-bottom: 20px;
                        opacity: 0.7;
                    }

                    .calendar-selection-modal .empty-state h3 {
                        margin: 0 0 12px 0;
                        font-size: 20px;
                        font-weight: 600;
                        color: #4a5568;
                    }

                    .calendar-selection-modal .empty-state p {
                        margin: 0;
                        font-size: 14px;
                        line-height: 1.5;
                        max-width: 300px;
                        margin-left: auto;
                        margin-right: auto;
                    }

                    @keyframes fadeIn {
                        from { opacity: 0; }
                        to { opacity: 1; }
                    }

                    @keyframes slideUp {
                        from {
                            opacity: 0;
                            transform: translateY(20px) scale(0.95);
                        }
                        to {
                            opacity: 1;
                            transform: translateY(0) scale(1);
                        }
                    }

                    /* 모바일 반응형 */
                    @media (max-width: 768px) {
                        .calendar-selection-modal .modal-content {
                            width: 95%;
                            max-height: 90vh;
                            border-radius: 16px;
                        }

                        .calendar-selection-modal .modal-header {
                            padding: 20px 24px;
                        }

                        .calendar-selection-modal .header-icon {
                            font-size: 28px;
                        }

                        .calendar-selection-modal .header-text h2 {
                            font-size: 20px;
                        }

                        .calendar-selection-modal .modal-body {
                            padding: 20px;
                        }

                        .calendar-selection-modal .calendar-grid {
                            grid-template-columns: 1fr;
                            gap: 12px;
                        }

                        .calendar-selection-modal .calendar-card {
                            padding: 16px;
                        }
                    }
                </style>
            `;

            // 스타일과 모달을 DOM에 추가
            if (!document.getElementById('apple-calendar-selection-styles')) {
                const styleElement = document.createElement('style');
                styleElement.id = 'apple-calendar-selection-styles';
                styleElement.innerHTML = styles;
                document.head.appendChild(styleElement);
            }

            const modalContainer = document.createElement('div');
            modalContainer.innerHTML = modalHTML;
            document.body.appendChild(modalContainer.firstElementChild);

        } catch (error) {
            console.error('Failed to show calendar selection:', error);
            this.showNotification('캘린더 목록을 불러오는데 실패했습니다.', 'error');
        }
    }

    /**
     * 캘린더 선택 후 날짜 범위 설정
     */
    async selectCalendarForSync(calendarId) {
        try {
            // 기존 캘린더 선택 모달 닫기
            const modal = document.getElementById('apple-calendar-selection');
            if (modal) modal.remove();

            // 날짜 범위 선택 모달 표시
            this.showDateRangeModal(calendarId);

        } catch (error) {
            console.error('Calendar selection failed:', error);
            this.showNotification('캘린더 선택에 실패했습니다.', 'error');
        }
    }

    /**
     * 날짜 범위 선택 모달 표시
     */
    showDateRangeModal(calendarId) {
        const today = new Date();
        const defaultStart = new Date(today.getFullYear() - 1, today.getMonth(), today.getDate());
        const defaultEnd = new Date(today.getFullYear() + 1, today.getMonth(), today.getDate());

        const modalHTML = `
            <div class="apple-date-range-modal" id="apple-date-range-modal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>🍎 Apple Calendar 동기화 설정</h3>
                        <button class="close-btn" onclick="document.getElementById('apple-date-range-modal').remove()">×</button>
                    </div>
                    <div class="modal-body">
                        <div class="step-description">
                            <h4>동기화할 기간을 선택하세요</h4>
                            <p>Apple Calendar에서 가져올 일정의 기간을 설정해주세요.</p>
                        </div>

                        <div class="date-range-picker">
                            <div class="date-range-row">
                                <div class="date-input-group">
                                    <label class="date-label">시작 날짜</label>
                                    <input type="date" id="apple-sync-start-date" class="date-input" value="${defaultStart.toISOString().split('T')[0]}">
                                </div>
                                <div class="date-range-separator">~</div>
                                <div class="date-input-group">
                                    <label class="date-label">종료 날짜</label>
                                    <input type="date" id="apple-sync-end-date" class="date-input" value="${defaultEnd.toISOString().split('T')[0]}">
                                </div>
                            </div>

                            <div class="date-range-presets">
                                <button type="button" class="preset-btn" onclick="window.appleWizard.setAppleDateRange('last3months')">최근 3개월</button>
                                <button type="button" class="preset-btn" onclick="window.appleWizard.setAppleDateRange('last6months')">최근 6개월</button>
                                <button type="button" class="preset-btn active" onclick="window.appleWizard.setAppleDateRange('last1year')">최근 1년</button>
                                <button type="button" class="preset-btn" onclick="window.appleWizard.setAppleDateRange('all')">전체 기간</button>
                            </div>

                            <div class="date-range-preview">
                                <span class="preview-text" id="apple-date-range-preview">최근 1년간의 일정을 가져옵니다</span>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn-secondary" onclick="document.getElementById('apple-date-range-modal').remove()">취소</button>
                        <button class="btn-primary" onclick="window.appleWizard.proceedWithSync('${calendarId}')">동기화 시작</button>
                    </div>
                </div>
            </div>
        `;

        // 기존 스타일에 날짜 범위 모달 스타일 추가
        const additionalStyles = `
            <style>
                .apple-date-range-modal {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.5);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 10001;
                }
                .apple-date-range-modal .modal-content {
                    background: white;
                    border-radius: 12px;
                    width: 90%;
                    max-width: 500px;
                    max-height: 80vh;
                    overflow: auto;
                }
                .apple-date-range-modal .modal-header {
                    padding: 20px;
                    border-bottom: 1px solid #e0e0e0;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .apple-date-range-modal .modal-body {
                    padding: 20px;
                }
                .apple-date-range-modal .modal-footer {
                    padding: 20px;
                    border-top: 1px solid #e0e0e0;
                    display: flex;
                    gap: 10px;
                    justify-content: flex-end;
                }
                .apple-date-range-modal .step-description h4 {
                    margin-bottom: 8px;
                    color: #333;
                }
                .apple-date-range-modal .step-description p {
                    color: #666;
                    margin-bottom: 20px;
                }
                .apple-date-range-modal .date-range-picker {
                    background: #f9fafb;
                    border: 1px solid #e5e7eb;
                    border-radius: 8px;
                    padding: 16px;
                }
                .apple-date-range-modal .date-range-row {
                    display: flex;
                    align-items: end;
                    gap: 16px;
                    margin-bottom: 16px;
                }
                .apple-date-range-modal .date-input-group {
                    flex: 1;
                }
                .apple-date-range-modal .date-label {
                    display: block;
                    font-size: 12px;
                    font-weight: 500;
                    color: #6b7280;
                    margin-bottom: 6px;
                }
                .apple-date-range-modal .date-input {
                    width: 100%;
                    padding: 8px 12px;
                    border: 1px solid #d1d5db;
                    border-radius: 6px;
                    font-size: 14px;
                    color: #374151;
                    background: white;
                }
                .apple-date-range-modal .date-range-separator {
                    color: #6b7280;
                    font-weight: 500;
                    margin-bottom: 8px;
                }
                .apple-date-range-modal .date-range-presets {
                    display: flex;
                    gap: 8px;
                    margin-bottom: 12px;
                    flex-wrap: wrap;
                }
                .apple-date-range-modal .preset-btn {
                    padding: 6px 12px;
                    border: 1px solid #d1d5db;
                    border-radius: 6px;
                    background: white;
                    color: #6b7280;
                    font-size: 12px;
                    cursor: pointer;
                }
                .apple-date-range-modal .preset-btn.active {
                    background: #007AFF;
                    border-color: #007AFF;
                    color: white;
                }
                .apple-date-range-modal .date-range-preview {
                    background: #eff6ff;
                    border: 1px solid #bfdbfe;
                    border-radius: 6px;
                    padding: 8px 12px;
                }
                .apple-date-range-modal .preview-text {
                    font-size: 12px;
                    color: #1e40af;
                    font-weight: 500;
                }
                .apple-date-range-modal .btn-secondary,
                .apple-date-range-modal .btn-primary {
                    padding: 10px 20px;
                    border-radius: 6px;
                    border: none;
                    cursor: pointer;
                    font-weight: 500;
                }
                .apple-date-range-modal .btn-secondary {
                    background: #f3f4f6;
                    color: #374151;
                }
                .apple-date-range-modal .btn-primary {
                    background: #007AFF;
                    color: white;
                }
            </style>
        `;

        // 스타일 추가
        if (!document.getElementById('apple-date-range-styles')) {
            const styleElement = document.createElement('style');
            styleElement.id = 'apple-date-range-styles';
            styleElement.innerHTML = additionalStyles;
            document.head.appendChild(styleElement);
        }

        // 모달 추가
        const modalContainer = document.createElement('div');
        modalContainer.innerHTML = modalHTML;
        document.body.appendChild(modalContainer.firstElementChild);

        // 이벤트 리스너 추가
        setTimeout(() => {
            const startInput = document.getElementById('apple-sync-start-date');
            const endInput = document.getElementById('apple-sync-end-date');
            if (startInput && endInput) {
                startInput.addEventListener('change', () => this.updateAppleDateRangePreview());
                endInput.addEventListener('change', () => this.updateAppleDateRangePreview());
            }
        }, 100);
    }

    /**
     * Apple Calendar 날짜 범위 프리셋 설정
     */
    setAppleDateRange(preset) {
        const startDateInput = document.getElementById('apple-sync-start-date');
        const endDateInput = document.getElementById('apple-sync-end-date');
        const today = new Date();
        let startDate, endDate;

        // 기존 active 제거
        document.querySelectorAll('.apple-date-range-modal .preset-btn').forEach(btn => btn.classList.remove('active'));

        switch (preset) {
            case 'last3months':
                startDate = new Date(today.getFullYear(), today.getMonth() - 3, today.getDate());
                endDate = new Date(today.getFullYear(), today.getMonth() + 3, today.getDate());
                document.querySelector('[onclick="window.appleWizard.setAppleDateRange(\'last3months\')"]').classList.add('active');
                break;
            case 'last6months':
                startDate = new Date(today.getFullYear(), today.getMonth() - 6, today.getDate());
                endDate = new Date(today.getFullYear(), today.getMonth() + 6, today.getDate());
                document.querySelector('[onclick="window.appleWizard.setAppleDateRange(\'last6months\')"]').classList.add('active');
                break;
            case 'last1year':
                startDate = new Date(today.getFullYear() - 1, today.getMonth(), today.getDate());
                endDate = new Date(today.getFullYear() + 1, today.getMonth(), today.getDate());
                document.querySelector('[onclick="window.appleWizard.setAppleDateRange(\'last1year\')"]').classList.add('active');
                break;
            case 'all':
                startDate = new Date(2020, 0, 1);
                endDate = new Date(today.getFullYear() + 2, 11, 31);
                document.querySelector('[onclick="window.appleWizard.setAppleDateRange(\'all\')"]').classList.add('active');
                break;
        }

        if (startDateInput && endDateInput) {
            startDateInput.value = startDate.toISOString().split('T')[0];
            endDateInput.value = endDate.toISOString().split('T')[0];
        }

        this.updateAppleDateRangePreview();
    }

    /**
     * Apple Calendar 날짜 범위 프리뷰 업데이트
     */
    updateAppleDateRangePreview() {
        const startDate = document.getElementById('apple-sync-start-date').value;
        const endDate = document.getElementById('apple-sync-end-date').value;
        const previewElement = document.getElementById('apple-date-range-preview');

        if (startDate && endDate) {
            const start = new Date(startDate);
            const end = new Date(endDate);
            const startString = start.toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' });
            const endString = end.toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' });

            previewElement.textContent = `${startString} ~ ${endString} 기간의 일정을 가져옵니다`;
        } else {
            previewElement.textContent = '날짜 범위를 선택해주세요';
        }
    }

    /**
     * 날짜 범위와 함께 실제 동기화 수행
     */
    async proceedWithSync(calendarId) {
        try {
            const startDate = document.getElementById('apple-sync-start-date').value;
            const endDate = document.getElementById('apple-sync-end-date').value;

            if (!startDate || !endDate) {
                this.showNotification('날짜 범위를 선택해주세요.', 'error');
                return;
            }

            // 로딩 상태
            const syncBtn = document.querySelector('.apple-date-range-modal .btn-primary');
            const originalText = syncBtn.textContent;
            syncBtn.disabled = true;
            syncBtn.textContent = '연동 중...';

            // Apple Calendar과 NotionFlow 캘린더 연결
            // Google과 동일한 방식으로 처리
            const response = await fetch('/api/calendars/sync', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    platform: 'apple',
                    calendar_id: calendarId,
                    sync_settings: {
                        date_range: {
                            start_date: startDate,
                            end_date: endDate
                        }
                    }
                })
            });

            if (!response.ok) {
                throw new Error('동기화 실패');
            }

            const data = await response.json();

            // 모달 닫기
            const modal = document.getElementById('apple-date-range-modal');
            if (modal) modal.remove();

            // 성공 알림
            this.showNotification(`Apple Calendar가 성공적으로 연결되었습니다! ${data.synced_events || 0}개의 일정이 동기화되었습니다.`, 'success');

            // 페이지 새로고침 또는 캘린더 목록 업데이트
            if (window.loadSyncedCalendars) {
                window.loadSyncedCalendars();
            }

        } catch (error) {
            console.error('Apple Calendar sync failed:', error);
            this.showNotification('Apple Calendar 동기화에 실패했습니다.', 'error');

            // 버튼 복원
            const syncBtn = document.querySelector('.apple-date-range-modal .btn-primary');
            if (syncBtn) {
                syncBtn.disabled = false;
                syncBtn.textContent = '동기화 시작';
            }
        }
    }
}

// 전역 인스턴스 생성
window.appleWizard = new AppleSetupWizard();

// PlatformCard와 통합 (중복 방지를 위해 간소화)
document.addEventListener('DOMContentLoaded', () => {
    console.log('🍎 Apple Setup Wizard loaded and ready');
});