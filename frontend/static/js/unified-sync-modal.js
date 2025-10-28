/**
 * 통합 동기화 모달 - 기존 코드 100% 재활용
 * 기존 CalendarSyncService와 Platform Manager 재사용
 */

class UnifiedSyncModal {
    constructor() {
        this.selectedPlatforms = new Set();
        this.selectedEvents = new Set();
        this.calendarEvents = [];
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

        // 전역 참조 설정 (HTML 이벤트 핸들러에서 사용)
        window.unifiedSync = this;

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
            // .topbar-right가 없는 페이지에서는 버튼을 생성하지 않음 (정상 동작)
            return;
        }
        
        const syncButton = document.createElement('button');
        syncButton.id = 'unified-sync-button';
        syncButton.className = 'sync-icon-button'; // 새로운 아이콘 버튼 스타일
        syncButton.title = '캘린더 연동하기'; // 툴팁
        syncButton.innerHTML = `
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sync-icon">
                <path d="M23 4v6h-6M1 20v-6h6"/>
                <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"/>
            </svg>
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
        
        // 클릭 이벤트 - event delegation으로 안전하게 처리
        syncButton.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.openModal();
        });
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
                <button class="close-form-btn" onclick="this.closest('#unified-sync-modal').parentElement.style.display='none'" title="닫기">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            <div class="event-form-content">
                <!-- Step 1: 이벤트 선택 -->
                <div class="sync-step" id="step-events" style="display: block;">
                    <h3>1단계: 내보낼 이벤트 선택</h3>

                    <!-- 선택 헬퍼 버튼들 -->
                    <div class="event-selection-controls" style="margin-bottom: 15px; display: flex; gap: 10px;">
                        <button class="btn-secondary" onclick="window.unifiedSync.selectAllEvents()" style="padding: 6px 12px; font-size: 14px;">전체 선택</button>
                        <button class="btn-secondary" onclick="window.unifiedSync.deselectAllEvents()" style="padding: 6px 12px; font-size: 14px;">전체 해제</button>
                        <span style="margin-left: auto; color: #666; font-size: 14px;">
                            <span id="selected-count">0</span>개 선택됨
                        </span>
                    </div>

                    <!-- 이벤트 목록 컨테이너 -->
                    <div class="event-list-container" style="
                        max-height: 400px;
                        overflow-y: auto;
                        border: 1px solid #e5e7eb;
                        border-radius: 8px;
                        padding: 10px;
                        background: #f9fafb;
                    ">
                        <div id="event-list-content">
                            <div style="text-align: center; padding: 20px; color: #666;">
                                이벤트를 불러오는 중...
                            </div>
                        </div>
                    </div>

                    <div style="margin-top: 15px;">
                        <button class="btn-primary" onclick="window.unifiedSync.nextStep()" style="width: 100%;">다음</button>
                    </div>
                </div>

                <!-- Step 2: 플랫폼 선택 -->
                <div class="sync-step" id="step-platforms" style="display: none;">
                    <h3>2단계: 연동 플랫폼 선택</h3>
                    <div class="platform-selection">
                        ${this.getPlatformCheckboxes()}
                    </div>
                    <div class="step-buttons">
                        <button class="btn-secondary" onclick="window.unifiedSync.prevStep()">이전</button>
                        <button class="btn-primary" onclick="window.unifiedSync.nextStep()">다음</button>
                    </div>
                </div>

                <!-- Step 3: 옵션 설정 -->
                <div class="sync-step" id="step-options" style="display: none;">
                    <h3>3단계: 동기화 옵션</h3>
                    ${this.getOptionsHTML()}
                    <div class="step-buttons">
                        <button class="btn-secondary" onclick="window.unifiedSync.prevStep()">이전</button>
                        <button class="btn-primary" onclick="window.unifiedSync.nextStep()">다음</button>
                    </div>
                </div>

                <!-- Step 4: 검토 및 실행 -->
                <div class="sync-step" id="step-review" style="display: none;">
                    <h3>4단계: 검토 및 실행</h3>
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
            // Console error removed
            
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
        // Console log removed

        const overlay = document.getElementById('sync-modal-overlay');
        if (overlay) {
            // Console log removed
            overlay.style.display = 'block';
            this.currentStep = 1;
            this.showStep(1);

            // 이벤트 목록 로드
            // Console log removed
            await this.loadCalendarEvents();
            await this.checkPlatformStatus();
            // Console log removed
        } else {
            // Console error removed

            // 모달이 없으면 다시 생성 시도
            // Console log removed
            this.createModal();
            const newOverlay = document.getElementById('sync-modal-overlay');
            if (newOverlay) {
                newOverlay.style.display = 'block';
                this.currentStep = 1;
                this.showStep(1);
                await this.loadCalendarEvents();
                await this.checkPlatformStatus();
            }
        }
    }

    // 캘린더 이벤트 로드
    async loadCalendarEvents() {
        try {
            // 캘린더 ID 가져오기
            const calendarId = window.calendarId || document.querySelector('.calendar-workspace')?.dataset.calendarId;
            if (!calendarId) {
                // Console warn removed

                // 캘린더 ID가 없으면 사용자 캘린더 목록을 가져와서 첫 번째 것 사용
                try {
                    const response = await fetch('/api/calendars/list');
                    const data = await response.json();

                    if (data.success && data.calendars && data.calendars.length > 0) {
                        const firstCalendar = data.calendars[0];
                        // Console log removed
                        await this.loadEventsForCalendar(firstCalendar.id);
                        return;
                    }
                } catch (error) {
                    // Console error removed
                }

                // 캘린더가 없으면 빈 상태 표시
                this.showEmptyEventState();
                return;
            }

            await this.loadEventsForCalendar(calendarId);
        } catch (error) {
            // Console error removed
            document.getElementById('event-list-content').innerHTML = `
                <div style="text-align: center; padding: 20px; color: #dc3545;">
                    이벤트를 불러오는 중 오류가 발생했습니다.
                </div>
            `;
        }
    }

    // 이벤트 목록 렌더링
    renderEventList(events) {
        const container = document.getElementById('event-list-content');
        if (!container) return;

        // 데이터 타입 검증 및 안전한 처리
        if (!events || !Array.isArray(events) || events.length === 0) {
            container.innerHTML = `
                <div style="text-align: center; padding: 20px; color: #666;">
                    이벤트가 없습니다.
                </div>
            `;
            return;
        }

        // 날짜별로 이벤트 그룹화
        const eventsByDate = {};
        events.forEach(event => {
            const date = new Date(event.start_datetime || event.date).toLocaleDateString('ko-KR');
            if (!eventsByDate[date]) {
                eventsByDate[date] = [];
            }
            eventsByDate[date].push(event);
        });

        // HTML 생성
        let html = '';
        Object.keys(eventsByDate).sort().forEach(date => {
            html += `
                <div class="event-date-group" style="margin-bottom: 15px;">
                    <div style="font-weight: 600; color: #374151; margin-bottom: 8px; padding: 5px 0; border-bottom: 1px solid #e5e7eb;">
                        ${date}
                    </div>
                    <div class="event-items">
            `;

            eventsByDate[date].forEach(event => {
                const eventId = event.id || event.event_id;
                const time = event.start_datetime ?
                    new Date(event.start_datetime).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' }) :
                    '종일';

                html += `
                    <label class="event-item" style="
                        display: flex;
                        align-items: center;
                        padding: 8px;
                        margin-bottom: 4px;
                        background: white;
                        border-radius: 6px;
                        cursor: pointer;
                        transition: background 0.2s;
                    " onmouseover="this.style.background='#f3f4f6'" onmouseout="this.style.background='white'">
                        <input type="checkbox"
                               value="${eventId}"
                               onchange="window.unifiedSync.toggleEventSelection('${eventId}')"
                               style="margin-right: 10px;">
                        <div style="flex: 1;">
                            <div style="font-weight: 500; color: #111827;">
                                ${event.title || '제목 없음'}
                            </div>
                            <div style="font-size: 12px; color: #6b7280; margin-top: 2px;">
                                ${time}
                                ${event.location ? ` • ${event.location}` : ''}
                                ${event.source_platform ? ` • ${event.source_platform}` : ''}
                            </div>
                        </div>
                    </label>
                `;
            });

            html += `
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;
        this.updateSelectedCount();
    }

    // 이벤트 선택 토글
    toggleEventSelection(eventId) {
        if (this.selectedEvents.has(eventId)) {
            this.selectedEvents.delete(eventId);
        } else {
            this.selectedEvents.add(eventId);
        }
        this.updateSelectedCount();
    }

    // 전체 선택
    selectAllEvents() {
        const checkboxes = document.querySelectorAll('#event-list-content input[type="checkbox"]');
        checkboxes.forEach(checkbox => {
            checkbox.checked = true;
            this.selectedEvents.add(checkbox.value);
        });
        this.updateSelectedCount();
    }

    // 전체 해제
    deselectAllEvents() {
        const checkboxes = document.querySelectorAll('#event-list-content input[type="checkbox"]');
        checkboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
        this.selectedEvents.clear();
        this.updateSelectedCount();
    }

    // 선택 개수 업데이트
    updateSelectedCount() {
        const countElement = document.getElementById('selected-count');
        if (countElement) {
            countElement.textContent = this.selectedEvents.size;
        }
    }

    // 특정 캘린더의 이벤트 로드
    async loadEventsForCalendar(calendarId) {
        try {
            const response = await fetch(`/api/calendars/${calendarId}/events`);
            if (!response.ok) {
                throw new Error('Failed to load events');
            }

            const events = await response.json();

            // API는 직접 배열을 반환함
            this.calendarEvents = Array.isArray(events) ? events : [];
            this.selectedEvents = new Set();

            // 이벤트 목록 렌더링
            this.renderEventList(this.calendarEvents);
        } catch (error) {
            // Console error removed
            this.showEmptyEventState();
        }
    }

    // 빈 이벤트 상태 표시
    showEmptyEventState() {
        const container = document.getElementById('event-list-content');
        if (container) {
            container.innerHTML = `
                <div style="text-align: center; padding: 40px; color: #666;">
                    <div style="font-size: 48px; margin-bottom: 16px;">📅</div>
                    <h3 style="margin: 0 0 8px 0; color: #333;">이벤트가 없습니다</h3>
                    <p style="margin: 0; font-size: 14px;">캘린더에 이벤트를 추가한 후 다시 시도해주세요.</p>
                </div>
            `;
        }
        this.calendarEvents = [];
        this.selectedEvents = new Set();
        this.updateSelectedCount();
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
        const names = ['', 'events', 'platforms', 'options', 'review', 'results'];
        return names[step] || 'events';
    }

    nextStep() {
        // Step 1: 이벤트 선택 확인
        if (this.currentStep === 1 && this.selectedEvents.size === 0) {
            alert('내보낼 이벤트를 하나 이상 선택해주세요.');
            return;
        }

        // Step 2: 플랫폼 선택 확인
        if (this.currentStep === 2 && this.selectedPlatforms.size === 0) {
            alert('연동할 플랫폼을 하나 이상 선택해주세요.');
            return;
        }

        if (this.currentStep < 5) {
            this.currentStep++;
            this.showStep(this.currentStep);

            if (this.currentStep === 4) {
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
    
    async generatePreview() {
        const previewElement = document.getElementById('sync-preview');
        if (!previewElement) return;

        const platformList = Array.from(this.selectedPlatforms).join(', ');
        const direction = this.syncOptions.direction;
        const scope = this.syncOptions.scope;

        previewElement.innerHTML = `
            <div class="preview-summary">
                <h4>🛡️ 동기화 검증 및 검토</h4>
                <div style="margin-bottom: 20px;">
                    <p><strong>선택된 이벤트:</strong> ${this.selectedEvents.size}개</p>
                    <p><strong>대상 플랫폼:</strong> ${platformList}</p>
                    <p><strong>동기화 방향:</strong> ${this.getDirectionText(direction)}</p>
                    <p><strong>동기화 범위:</strong> ${this.getScopeText(scope)}</p>
                </div>

                <div id="validation-results" style="margin-top: 20px;">
                    <div style="text-align: center; padding: 20px; color: #666;">
                        <div class="validation-loading">🔍 이벤트 검증 중...</div>
                        <div style="margin-top: 10px; font-size: 14px;">
                            3단계 검증을 진행하고 있습니다...
                        </div>
                    </div>
                </div>
            </div>
        `;

        // 3단계 검증 실행
        await this.performValidation();
    }

    async performValidation() {
        try {
            const validationResults = document.getElementById('validation-results');
            if (!validationResults) return;

            // 선택된 플랫폼들에 대해 검증 수행
            const allValidationResults = new Map();

            for (const platform of this.selectedPlatforms) {
                // Console log removed

                // localStorage에서 휴지통 이벤트 가져오기
                const trashedEvents = JSON.parse(localStorage.getItem('trashedEvents') || '[]');

                // 검증 API 호출
                const response = await fetch('/api/unified-sync/validate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        event_ids: Array.from(this.selectedEvents),
                        target_platform: platform,
                        trashed_events: trashedEvents
                    })
                });

                if (response.ok) {
                    const result = await response.json();
                    allValidationResults.set(platform, result);
                    // Console log removed
                } else {
                    const error = await response.json();
                    allValidationResults.set(platform, {
                        success: false,
                        error: error.message || 'Validation failed'
                    });
                    // Console error removed
                }
            }

            // 검증 결과 표시
            this.displayValidationResults(allValidationResults);

        } catch (error) {
            // Console error removed

            const validationResults = document.getElementById('validation-results');
            if (validationResults) {
                validationResults.innerHTML = `
                    <div style="text-align: center; padding: 20px; color: #dc3545;">
                        검증 중 오류가 발생했습니다: ${error.message}
                    </div>
                `;
            }
        }
    }

    displayValidationResults(allValidationResults) {
        const validationResults = document.getElementById('validation-results');
        if (!validationResults) return;

        let totalApproved = 0;
        let totalEvents = 0;
        let html = '';

        // 플랫폼별 검증 결과 표시
        for (const [platform, result] of allValidationResults) {
            if (result.success) {
                const summary = result.summary;
                totalApproved += summary.approved_count;
                totalEvents += summary.total_events;

                html += `
                    <div class="validation-platform-result" style="
                        margin-bottom: 15px;
                        padding: 15px;
                        border: 1px solid #e5e7eb;
                        border-radius: 8px;
                        background: ${summary.approval_rate === 100 ? '#ecfdf5' : '#fef3c7'};
                    ">
                        <h5 style="margin: 0 0 10px 0; color: #374151;">
                            ${this.getPlatformName(platform)} 검증 결과
                        </h5>

                        <div style="display: flex; gap: 20px; margin-bottom: 10px;">
                            <div style="color: #059669;">
                                ✅ 승인: ${summary.approved_count}개
                            </div>
                            <div style="color: #dc2626;">
                                ❌ 거부: ${summary.rejected_count}개
                            </div>
                            <div style="color: #374151;">
                                📊 승인률: ${summary.approval_rate.toFixed(1)}%
                            </div>
                        </div>

                        ${summary.rejected_count > 0 ? `
                            <div style="font-size: 14px; color: #6b7280;">
                                <strong>거부 사유:</strong>
                                ${Object.entries(summary.rejection_reasons).map(([reason, count]) =>
                                    `${reason} (${count}개)`
                                ).join(', ')}
                            </div>
                        ` : ''}
                    </div>
                `;
            } else {
                html += `
                    <div class="validation-platform-result" style="
                        margin-bottom: 15px;
                        padding: 15px;
                        border: 1px solid #dc2626;
                        border-radius: 8px;
                        background: #fee2e2;
                    ">
                        <h5 style="margin: 0 0 10px 0; color: #dc2626;">
                            ${this.getPlatformName(platform)} 검증 실패
                        </h5>
                        <div style="color: #dc2626; font-size: 14px;">
                            ${result.error}
                        </div>
                    </div>
                `;
            }
        }

        // 전체 요약
        const overallApprovalRate = totalEvents > 0 ? (totalApproved / totalEvents * 100) : 0;

        html = `
            <div class="validation-overall-summary" style="
                margin-bottom: 20px;
                padding: 15px;
                background: ${overallApprovalRate === 100 ? '#dcfce7' : overallApprovalRate > 50 ? '#fef3c7' : '#fee2e2'};
                border-radius: 8px;
                text-align: center;
            ">
                <h4 style="margin: 0 0 10px 0; color: #374151;">전체 검증 요약</h4>
                <div style="font-size: 18px; font-weight: 600; margin-bottom: 5px;">
                    ${totalApproved}/${totalEvents} 이벤트 승인됨 (${overallApprovalRate.toFixed(1)}%)
                </div>
                <div style="font-size: 14px; color: #6b7280;">
                    ${totalApproved > 0 ? `${totalApproved}개 이벤트가 동기화 준비 완료` : '동기화 가능한 이벤트가 없습니다'}
                </div>
            </div>
        ` + html;

        validationResults.innerHTML = html;

        // 검증된 이벤트 저장 (실행 단계에서 사용)
        this.validationResults = allValidationResults;
        this.totalApprovedEvents = totalApproved;
    }

    getPlatformName(platform) {
        const names = {
            'google': 'Google Calendar',
            'notion': 'Notion',
            'apple': 'Apple Calendar'
        };
        return names[platform] || platform;
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
            // 검증 결과 확인
            if (!this.validationResults || this.validationResults.length === 0) {
                throw new Error('검증이 완료되지 않았습니다. 다시 시도해주세요.');
            }

            // 승인된 이벤트만 필터링 (approved 상태인 것들)
            const approvedEvents = this.validationResults.filter(result =>
                result.validation_status === 'approved'
            );

            if (approvedEvents.length === 0) {
                this.showResults({
                    error: '동기화 가능한 이벤트가 없습니다. 모든 이벤트가 검증에서 거부되었습니다.'
                });
                return;
            }

            // 검증된 이벤트로 동기화 실행
            const result = await this.callValidatedSyncAPI(approvedEvents, this.selectedPlatforms, this.syncOptions);

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
            // Console error removed
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
            // Console error removed
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
            // Console error removed
            return { success: false, error: error.message };
        }
    }

    // 검증된 이벤트로 동기화 실행 API
    async callValidatedSyncAPI(approvedEvents, platforms, options) {
        try {
            const response = await fetch('/api/unified-sync/sync-validated', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    validated_events: approvedEvents,
                    platforms: Array.from(platforms),
                    options: options
                })
            });

            return await response.json();
        } catch (error) {
            // Console error removed
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
                // Console error removed
                return {};
            }
        } catch (error) {
            // Console error removed
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

// 클래스를 전역 스코프에 노출
window.UnifiedSyncModal = UnifiedSyncModal;

// 전역 인스턴스 생성 (기존 패턴 재활용)
window.addEventListener('DOMContentLoaded', () => {
    window.unifiedSync = new UnifiedSyncModal();
});