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
                
                // 플랫폼 카드 업데이트
                if (window.platformCard) {
                    window.platformCard.loadRegisteredPlatforms();
                    window.platformCard.render();
                }
                
                // 성공 알림
                this.showNotification('Apple 캘린더가 성공적으로 연결되었습니다!', 'success');
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
}

// 전역 인스턴스 생성
window.appleWizard = new AppleSetupWizard();

// PlatformCard와 통합 (중복 방지를 위해 간소화)
document.addEventListener('DOMContentLoaded', () => {
    console.log('🍎 Apple Setup Wizard loaded and ready');
});