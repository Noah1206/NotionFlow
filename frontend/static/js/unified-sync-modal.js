/**
 * 통합 동기화 모달 - 기존 코드 100% 재활용
 * 기존 CalendarSyncService와 Platform Manager 재사용
 */

class UnifiedSyncModal {
    constructor() {
        this.selectedPlatforms = new Set();
        this.syncOptions = {
            direction: 'bidirectional', // push, pull, bidirectional
            scope: 'current_screen', // single, current_screen, selected
            target: 'auto', // auto-detect based on platform
            advanced: {
                duplicateDetection: true,
                reminder10Min: true,
                inviteAttendees: false
            }
        };
        
        // 기존 서비스 재활용 (클래스 존재 여부 확인)
        this.platformManagers = {};
        
        // Platform manager 클래스들이 존재하면 사용, 없으면 fallback
        if (typeof window.GooglePlatformManager !== 'undefined') {
            this.platformManagers.google = new window.GooglePlatformManager('google');
        }
        if (typeof window.NotionPlatformManager !== 'undefined') {
            this.platformManagers.notion = new window.NotionPlatformManager('notion');
        }
        if (typeof window.ApplePlatformManager !== 'undefined') {
            this.platformManagers.apple = new window.ApplePlatformManager('apple');
        }
        
        this.init();
    }
    
    init() {
        this.createSyncButton();
        this.createModal();
        this.bindEvents();
    }
    
    // 기존 .topbar-right 영역에 "연동하기" 버튼 추가
    createSyncButton() {
        const topbarRight = document.querySelector('.topbar-right');
        if (!topbarRight) {
            console.error('Header topbar-right not found');
            return;
        }
        
        const syncButton = document.createElement('button');
        syncButton.id = 'unified-sync-button';
        syncButton.className = 'view-option sync-trigger'; // 기존 스타일 재활용
        syncButton.innerHTML = `
            <span class="sync-text">연동하기</span>
            <div class="sync-loader" style="display: none;">
                <div class="loader-spinner"></div>
            </div>
        `;
        
        // 기존 view-toggle 옆에 추가
        const viewToggle = topbarRight.querySelector('.view-toggle');
        if (viewToggle) {
            topbarRight.insertBefore(syncButton, viewToggle.nextSibling);
        } else {
            topbarRight.appendChild(syncButton);
        }
        
        syncButton.addEventListener('click', () => this.openModal());
    }
    
    // 기존 event-form-widget 스타일 재활용한 모달 생성
    createModal() {
        const modal = document.createElement('div');
        modal.id = 'unified-sync-modal';
        modal.className = 'sidebar-widget event-form-widget'; // 기존 모달 스타일 재활용
        modal.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            z-index: 1000;
            width: 600px;
            max-width: 90vw;
            max-height: 80vh;
            overflow-y: auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
            display: none;
        `;
        
        modal.innerHTML = this.getModalHTML();
        
        // Overlay 생성 (기존 calendar-overlay-form 패턴 재활용)
        const overlay = document.createElement('div');
        overlay.id = 'sync-modal-overlay';
        overlay.className = 'calendar-overlay-form'; // 기존 오버레이 스타일 재활용
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            z-index: 999;
            display: none;
        `;
        
        overlay.appendChild(modal);
        document.body.appendChild(overlay);
        
        // 오버레이 클릭으로 닫기
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                this.closeModal();
            }
        });
    }
    
    getModalHTML() {
        return `
            <div class="widget-header">
                <div class="widget-icon">🔗</div>
                <h4>캘린더 연동하기</h4>
                <button class="close-form-btn" onclick="window.unifiedSync.closeModal()" title="닫기">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>
            
            <div class="event-form-content">
                <!-- Step 1: 플랫폼 선택 -->
                <div class="sync-step" id="step-platforms" style="display: block;">
                    <h3>1단계: 연동 플랫폼 선택</h3>
                    <div class="platform-selection">
                        ${this.getPlatformCheckboxes()}
                    </div>
                    <button class="btn-primary" onclick="window.unifiedSync.nextStep()">다음</button>
                </div>
                
                <!-- Step 2: 옵션 설정 -->
                <div class="sync-step" id="step-options" style="display: none;">
                    <h3>2단계: 동기화 옵션</h3>
                    ${this.getOptionsHTML()}
                    <div class="step-buttons">
                        <button class="btn-secondary" onclick="window.unifiedSync.prevStep()">이전</button>
                        <button class="btn-primary" onclick="window.unifiedSync.nextStep()">다음</button>
                    </div>
                </div>
                
                <!-- Step 3: 검토 및 실행 -->
                <div class="sync-step" id="step-review" style="display: none;">
                    <h3>3단계: 검토 및 실행</h3>
                    <div id="sync-preview"></div>
                    <div class="step-buttons">
                        <button class="btn-secondary" onclick="window.unifiedSync.prevStep()">이전</button>
                        <button class="btn-primary" onclick="window.unifiedSync.executSync()">동기화 실행</button>
                    </div>
                </div>
                
                <!-- Results -->
                <div class="sync-step" id="step-results" style="display: none;">
                    <h3>동기화 완료</h3>
                    <div id="sync-results"></div>
                    <button class="btn-primary" onclick="window.unifiedSync.closeModal()">완료</button>
                </div>
            </div>
        `;
    }
    
    getPlatformCheckboxes() {
        return `
            <div class="platform-checkbox-group">
                <label class="platform-checkbox">
                    <input type="checkbox" value="google" onchange="window.unifiedSync.togglePlatform('google')">
                    <div class="platform-info">
                        <span class="platform-name">Google Calendar</span>
                        <span class="platform-status" id="google-status">연결 확인 중...</span>
                    </div>
                </label>
                
                <label class="platform-checkbox">
                    <input type="checkbox" value="notion" onchange="window.unifiedSync.togglePlatform('notion')">
                    <div class="platform-info">
                        <span class="platform-name">Notion</span>
                        <span class="platform-status" id="notion-status">연결 확인 중...</span>
                    </div>
                </label>
                
                <label class="platform-checkbox">
                    <input type="checkbox" value="apple" onchange="window.unifiedSync.togglePlatform('apple')">
                    <div class="platform-info">
                        <span class="platform-name">Apple Calendar</span>
                        <span class="platform-status" id="apple-status">구현 예정</span>
                    </div>
                </label>
            </div>
        `;
    }
    
    getOptionsHTML() {
        return `
            <div class="sync-options">
                <div class="option-group">
                    <h4>동기화 방향</h4>
                    <select id="sync-direction" onchange="window.unifiedSync.updateOption('direction', this.value)">
                        <option value="bidirectional">양방향 (↔️)</option>
                        <option value="push">푸시 (내보내기 →)</option>
                        <option value="pull">풀 (가져오기 ←)</option>
                    </select>
                </div>
                
                <div class="option-group">
                    <h4>동기화 범위</h4>
                    <select id="sync-scope" onchange="window.unifiedSync.updateOption('scope', this.value)">
                        <option value="current_screen">현재 화면 전체</option>
                        <option value="single">단일 이벤트</option>
                        <option value="selected">선택한 이벤트들</option>
                    </select>
                </div>
                
                <div class="option-group">
                    <h4>고급 옵션</h4>
                    <label class="checkbox-option">
                        <input type="checkbox" id="duplicate-detection" checked onchange="window.unifiedSync.updateAdvancedOption('duplicateDetection', this.checked)">
                        중복 감지 및 방지
                    </label>
                    <label class="checkbox-option">
                        <input type="checkbox" id="reminder-10min" checked onchange="window.unifiedSync.updateAdvancedOption('reminder10Min', this.checked)">
                        10분 전 알림 추가
                    </label>
                    <label class="checkbox-option">
                        <input type="checkbox" id="invite-attendees" onchange="window.unifiedSync.updateAdvancedOption('inviteAttendees', this.checked)">
                        참석자 초대
                    </label>
                </div>
            </div>
        `;
    }
    
    // 통합 API로 플랫폼 상태 확인
    async checkPlatformStatus() {
        const platforms = ['google', 'notion', 'apple'];
        
        try {
            // 새로운 통합 상태 API 사용
            const allStatus = await this.checkAllPlatformStatus();
            
            for (const platform of platforms) {
                const statusElement = document.getElementById(`${platform}-status`);
                if (!statusElement) continue;
                
                const status = allStatus[platform];
                if (status) {
                    if (status.connected) {
                        statusElement.textContent = '연결됨';
                        statusElement.className = 'platform-status connected';
                    } else {
                        statusElement.textContent = status.message || '연결 안됨';
                        statusElement.className = 'platform-status disconnected';
                    }
                } else {
                    statusElement.textContent = '상태 확인 실패';
                    statusElement.className = 'platform-status disconnected';
                }
            }
        } catch (error) {
            console.error('Platform status check failed:', error);
            
            // 에러 발생시 개별 플랫폼 상태 표시
            for (const platform of platforms) {
                const statusElement = document.getElementById(`${platform}-status`);
                if (statusElement) {
                    statusElement.textContent = platform === 'apple' ? '구현 예정' : '상태 확인 실패';
                    statusElement.className = 'platform-status disconnected';
                }
            }
        }
    }
    
    togglePlatform(platform) {
        if (this.selectedPlatforms.has(platform)) {
            this.selectedPlatforms.delete(platform);
        } else {
            this.selectedPlatforms.add(platform);
        }
    }
    
    updateOption(key, value) {
        this.syncOptions[key] = value;
    }
    
    updateAdvancedOption(key, value) {
        this.syncOptions.advanced[key] = value;
    }
    
    async openModal() {
        const overlay = document.getElementById('sync-modal-overlay');
        if (overlay) {
            overlay.style.display = 'block';
            this.currentStep = 1;
            this.showStep(1);
            await this.checkPlatformStatus();
        }
    }
    
    closeModal() {
        const overlay = document.getElementById('sync-modal-overlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
        this.selectedPlatforms.clear();
        this.currentStep = 1;
    }
    
    showStep(step) {
        // 모든 단계 숨기기
        document.querySelectorAll('.sync-step').forEach(el => el.style.display = 'none');
        
        // 해당 단계 보이기
        const stepElement = document.getElementById(`step-${this.getStepName(step)}`);
        if (stepElement) {
            stepElement.style.display = 'block';
        }
    }
    
    getStepName(step) {
        const names = ['', 'platforms', 'options', 'review', 'results'];
        return names[step] || 'platforms';
    }
    
    nextStep() {
        if (this.currentStep === 1 && this.selectedPlatforms.size === 0) {
            alert('연동할 플랫폼을 하나 이상 선택해주세요.');
            return;
        }
        
        if (this.currentStep < 4) {
            this.currentStep++;
            this.showStep(this.currentStep);
            
            if (this.currentStep === 3) {
                this.generatePreview();
            }
        }
    }
    
    prevStep() {
        if (this.currentStep > 1) {
            this.currentStep--;
            this.showStep(this.currentStep);
        }
    }
    
    generatePreview() {
        const previewElement = document.getElementById('sync-preview');
        if (!previewElement) return;
        
        const platformList = Array.from(this.selectedPlatforms).join(', ');
        const direction = this.syncOptions.direction;
        const scope = this.syncOptions.scope;
        
        previewElement.innerHTML = `
            <div class="preview-summary">
                <h4>동기화 요약</h4>
                <p><strong>플랫폼:</strong> ${platformList}</p>
                <p><strong>방향:</strong> ${this.getDirectionText(direction)}</p>
                <p><strong>범위:</strong> ${this.getScopeText(scope)}</p>
                <p><strong>예상 영향:</strong> 계산 중...</p>
            </div>
        `;
        
        // 기존 캘린더 이벤트 수 계산 (재활용)
        this.calculateImpact();
    }
    
    async calculateImpact() {
        // 기존 GoogleCalendarGrid의 events 배열 재활용
        const currentEvents = window.googleCalendarGrid?.events || [];
        const eventCount = currentEvents.length;
        
        const previewElement = document.getElementById('sync-preview');
        if (previewElement) {
            const impactText = previewElement.querySelector('p:last-child');
            if (impactText) {
                impactText.innerHTML = `<strong>예상 영향:</strong> ${eventCount}개 이벤트 동기화`;
            }
        }
    }
    
    getDirectionText(direction) {
        const texts = {
            'bidirectional': '양방향 동기화',
            'push': '내보내기 (로컬 → 외부)',
            'pull': '가져오기 (외부 → 로컬)'
        };
        return texts[direction] || direction;
    }
    
    getScopeText(scope) {
        const texts = {
            'current_screen': '현재 화면의 모든 이벤트',
            'single': '단일 선택 이벤트',
            'selected': '선택된 여러 이벤트'
        };
        return texts[scope] || scope;
    }
    
    // 새로운 통합 API로 동기화 실행
    async executSync() {
        const syncButton = document.querySelector('#step-review .btn-primary');
        if (syncButton) {
            syncButton.disabled = true;
            syncButton.textContent = '동기화 중...';
        }
        
        try {
            // 새로운 통합 sync API 호출
            const result = await this.callUnifiedSyncAPI(this.selectedPlatforms, this.syncOptions);
            
            if (result.success) {
                // 성공적인 결과를 기존 형식으로 변환
                const formattedResults = {};
                for (const [platform, platformResult] of Object.entries(result.results)) {
                    formattedResults[platform] = platformResult;
                }
                this.showResults(formattedResults);
            } else {
                // 에러 처리
                this.showResults({ error: result.error || '동기화에 실패했습니다' });
            }
            
        } catch (error) {
            console.error('Sync execution failed:', error);
            this.showResults({ error: error.message });
        } finally {
            // 버튼 상태 복원
            if (syncButton) {
                syncButton.disabled = false;
                syncButton.textContent = '동기화 실행';
            }
        }
    }
    
    // 기존 API 호출 함수 재활용 + 새로운 통합 API
    async callExistingSyncAPI(endpoint, options) {
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(options)
            });
            
            return await response.json();
        } catch (error) {
            console.error(`API call to ${endpoint} failed:`, error);
            return { success: false, error: error.message };
        }
    }
    
    // 새로운 통합 sync API 호출
    async callUnifiedSyncAPI(platforms, options) {
        try {
            const response = await fetch('/api/unified-sync/sync', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    platforms: Array.from(platforms),
                    options: options
                })
            });
            
            return await response.json();
        } catch (error) {
            console.error('Unified sync API call failed:', error);
            return { success: false, error: error.message };
        }
    }
    
    // 플랫폼 상태 확인 API
    async checkAllPlatformStatus() {
        try {
            const response = await fetch('/api/unified-sync/status');
            const data = await response.json();
            
            if (data.success) {
                return data.status;
            } else {
                console.error('Platform status check failed:', data.error);
                return {};
            }
        } catch (error) {
            console.error('Platform status API call failed:', error);
            return {};
        }
    }
    
    showResults(results) {
        this.currentStep = 4;
        this.showStep(4);
        
        const resultsElement = document.getElementById('sync-results');
        if (resultsElement) {
            let html = '<div class="sync-results">';
            
            for (const [platform, result] of Object.entries(results)) {
                const status = result.success ? '성공' : '실패';
                const icon = result.success ? '✅' : '❌';
                html += `
                    <div class="result-item">
                        ${icon} <strong>${platform}</strong>: ${status}
                        ${result.message ? `<br><small>${result.message}</small>` : ''}
                    </div>
                `;
            }
            
            html += '</div>';
            resultsElement.innerHTML = html;
        }
        
        // 기존 notification 시스템 재활용
        if (window.showNotification) {
            const successCount = Object.values(results).filter(r => r.success).length;
            const message = `${successCount}개 플랫폼 동기화 완료`;
            showNotification(message, 'success');
        }
        
        // 기존 캘린더 새로고침 로직 재활용
        if (window.googleCalendarGrid && typeof window.googleCalendarGrid.loadEvents === 'function') {
            setTimeout(() => {
                window.location.reload(); // 간단한 새로고침으로 결과 반영
            }, 2000);
        }
    }
    
    bindEvents() {
        // ESC 키로 모달 닫기
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
        });
    }
}

// 전역 인스턴스 생성 (기존 패턴 재활용)
window.addEventListener('DOMContentLoaded', () => {
    window.unifiedSync = new UnifiedSyncModal();
});