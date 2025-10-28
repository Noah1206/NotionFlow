/**
 * 캘린더 내보내기 시스템
 * 변경된 일정을 선택한 플랫폼으로 배치 내보내기
 */

class CalendarExportManager {
    constructor() {
        this.modal = null;
        this.currentCalendarId = null;
        this.connectedPlatforms = [];
        this.selectedPlatforms = [];
        this.pendingChanges = 0;

        this.init();
    }

    init() {
        // DOM이 로드된 후 초기화
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupUI());
        } else {
            this.setupUI();
        }
    }

    setupUI() {
        this.modal = document.getElementById('export-modal');
        this.currentCalendarId = this.getCurrentCalendarId();

        // 모달 외부 클릭 시 닫기
        if (this.modal) {
            this.modal.addEventListener('click', (e) => {
                if (e.target === this.modal) {
                    this.closeModal();
                }
            });
        }
    }

    getCurrentCalendarId() {
        // URL에서 캘린더 ID 추출 또는 데이터 속성에서 가져오기
        const calendarWorkspace = document.querySelector('.calendar-workspace');
        if (calendarWorkspace) {
            return calendarWorkspace.getAttribute('data-calendar-id');
        }

        // URL 패턴에서 추출 (예: /calendar/calendar-id)
        const pathParts = window.location.pathname.split('/');
        const calendarIndex = pathParts.indexOf('calendar');
        if (calendarIndex >= 0 && pathParts[calendarIndex + 1]) {
            return pathParts[calendarIndex + 1];
        }

        return null;
    }

    async openModal() {
        if (!this.currentCalendarId) {
            this.showError('캘린더 ID를 찾을 수 없습니다.');
            return;
        }

        // 모달 표시
        this.modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';

        // 데이터 로드
        await this.loadData();
    }

    closeModal() {
        if (this.modal) {
            this.modal.style.display = 'none';
            document.body.style.overflow = '';
        }
    }

    async loadData() {
        try {
            // 연결된 플랫폼과 변경사항 정보를 병렬로 로드
            const [platformsData, changesData] = await Promise.all([
                this.loadConnectedPlatforms(),
                this.loadPendingChanges()
            ]);

            this.updateUI();
        } catch (error) {
            console.error('데이터 로드 실패:', error);
            this.showError('정보를 불러오는 중 오류가 발생했습니다.');
        }
    }

    async loadConnectedPlatforms() {
        try {
            const response = await fetch('/api/oauth/connected-platforms', {
                method: 'GET',
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.success) {
                this.connectedPlatforms = data.platforms || [];
                console.log('연결된 플랫폼:', this.connectedPlatforms);
                return data;
            } else {
                throw new Error(data.error || '플랫폼 정보 로드 실패');
            }
        } catch (error) {
            console.error('연결된 플랫폼 로드 실패:', error);
            this.connectedPlatforms = [];
            throw error;
        }
    }

    async loadPendingChanges() {
        try {
            const response = await fetch(`/api/calendar/${this.currentCalendarId}/pending-changes`, {
                method: 'GET',
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.success) {
                this.pendingChanges = data.changes_count || 0;
                console.log('변경사항 수:', this.pendingChanges);
                return data;
            } else {
                throw new Error(data.error || '변경사항 정보 로드 실패');
            }
        } catch (error) {
            console.error('변경사항 로드 실패:', error);
            this.pendingChanges = 0;
            throw error;
        }
    }

    updateUI() {
        this.updateChangesInfo();
        this.updatePlatformsList();
        this.updateExportButton();
    }

    updateChangesInfo() {
        const changesCountElement = document.getElementById('changes-count');
        if (changesCountElement) {
            changesCountElement.textContent = this.pendingChanges;
        }

        const pendingChangesInfo = document.getElementById('pending-changes-info');
        if (pendingChangesInfo) {
            if (this.pendingChanges === 0) {
                pendingChangesInfo.style.background = '#f3f4f6';
                pendingChangesInfo.style.borderColor = '#d1d5db';
                pendingChangesInfo.innerHTML = '<span style="color: #6b7280;">변경사항이 없습니다.</span>';
            } else {
                pendingChangesInfo.style.background = '#fef3c7';
                pendingChangesInfo.style.borderColor = '#f59e0b';
            }
        }
    }

    updatePlatformsList() {
        const platformsList = document.getElementById('connected-platforms-list');
        if (!platformsList) return;

        if (this.connectedPlatforms.length === 0) {
            platformsList.innerHTML = `
                <div class="no-platforms">
                    <p style="text-align: center; color: #6b7280; padding: 40px;">
                        연결된 플랫폼이 없습니다.<br>
                        <a href="/dashboard/api-keys" style="color: #3b82f6; text-decoration: underline;">
                            설정에서 플랫폼을 연결해보세요.
                        </a>
                    </p>
                </div>
            `;
            return;
        }

        const platformsHTML = this.connectedPlatforms.map(platform => {
            const isSelected = this.selectedPlatforms.includes(platform.platform);
            const platformInfo = this.getPlatformInfo(platform.platform);

            return `
                <div class="platform-item ${isSelected ? 'selected' : ''}"
                     data-platform="${platform.platform}">
                    <div class="platform-info">
                        <div class="platform-icon ${platform.platform}">
                            ${platformInfo.icon}
                        </div>
                        <div class="platform-details">
                            <div class="platform-name">${platformInfo.name}</div>
                            <div class="platform-status">
                                ${platform.is_connected ? '연결됨' : '연결 안됨'}
                                ${platform.last_sync ? `• 최근 동기화: ${this.formatDate(platform.last_sync)}` : ''}
                            </div>
                        </div>
                    </div>
                    <div class="platform-actions">
                        <input type="checkbox"
                               class="platform-checkbox"
                               data-platform="${platform.platform}"
                               ${platform.is_connected ? '' : 'disabled'}
                               ${isSelected && platform.is_connected ? 'checked' : ''}>
                    </div>
                </div>
            `;
        }).join('');

        platformsList.innerHTML = platformsHTML;

        // 체크박스 이벤트 리스너 추가
        this.setupPlatformSelection();
    }

    setupPlatformSelection() {
        const checkboxes = document.querySelectorAll('.platform-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const platform = e.target.getAttribute('data-platform');
                const isChecked = e.target.checked;

                if (isChecked) {
                    if (!this.selectedPlatforms.includes(platform)) {
                        this.selectedPlatforms.push(platform);
                    }
                } else {
                    this.selectedPlatforms = this.selectedPlatforms.filter(p => p !== platform);
                }

                // UI 업데이트
                this.updatePlatformItemSelection();
                this.updateExportButton();
            });
        });

        // 플랫폼 아이템 클릭 시 체크박스 토글
        const platformItems = document.querySelectorAll('.platform-item');
        platformItems.forEach(item => {
            item.addEventListener('click', (e) => {
                if (e.target.type === 'checkbox') return; // 체크박스 직접 클릭은 제외

                const checkbox = item.querySelector('.platform-checkbox');
                if (checkbox && !checkbox.disabled) {
                    checkbox.checked = !checkbox.checked;
                    checkbox.dispatchEvent(new Event('change'));
                }
            });
        });
    }

    updatePlatformItemSelection() {
        const platformItems = document.querySelectorAll('.platform-item');
        platformItems.forEach(item => {
            const platform = item.getAttribute('data-platform');
            const isSelected = this.selectedPlatforms.includes(platform);

            if (isSelected) {
                item.classList.add('selected');
            } else {
                item.classList.remove('selected');
            }
        });
    }

    updateExportButton() {
        const exportBtn = document.getElementById('export-btn');
        if (!exportBtn) return;

        const hasSelection = this.selectedPlatforms.length > 0;
        const hasChanges = this.pendingChanges > 0;

        exportBtn.disabled = !hasSelection || !hasChanges;

        const btnText = exportBtn.querySelector('.btn-text');
        if (btnText) {
            if (!hasChanges) {
                btnText.textContent = '변경사항 없음';
            } else if (!hasSelection) {
                btnText.textContent = '플랫폼 선택';
            } else {
                btnText.textContent = `${this.selectedPlatforms.length}개 플랫폼으로 내보내기`;
            }
        }
    }

    async startExport() {
        if (this.selectedPlatforms.length === 0 || this.pendingChanges === 0) {
            return;
        }

        const exportBtn = document.getElementById('export-btn');
        const btnText = exportBtn.querySelector('.btn-text');
        const btnSpinner = exportBtn.querySelector('.btn-spinner');

        try {
            // 로딩 상태 설정
            exportBtn.disabled = true;
            btnText.textContent = '내보내는 중...';
            btnSpinner.style.display = 'block';

            // 내보내기 옵션 수집
            const exportAllEvents = document.getElementById('export-all-events').checked;
            const keepSync = document.getElementById('keep-sync').checked;

            // 내보내기 요청
            const response = await fetch(`/api/calendar/${this.currentCalendarId}/export`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({
                    platforms: this.selectedPlatforms,
                    export_all: exportAllEvents,
                    keep_sync: keepSync
                })
            });

            const data = await response.json();

            if (data.success) {
                this.showSuccess('내보내기가 완료되었습니다!');

                // 변경사항 수 업데이트
                this.pendingChanges = data.remaining_changes || 0;
                this.updateChangesInfo();
                this.updateExportButton();

                // 3초 후 모달 닫기
                setTimeout(() => {
                    this.closeModal();
                }, 3000);

            } else {
                throw new Error(data.error || '내보내기 실패');
            }

        } catch (error) {
            console.error('내보내기 실패:', error);
            this.showError('내보내기 중 오류가 발생했습니다: ' + error.message);

        } finally {
            // 로딩 상태 해제
            exportBtn.disabled = false;
            btnSpinner.style.display = 'none';
            this.updateExportButton();
        }
    }

    getPlatformInfo(platform) {
        const platformMap = {
            google: { name: 'Google Calendar', icon: 'G' },
            notion: { name: 'Notion', icon: 'N' },
            outlook: { name: 'Microsoft Outlook', icon: 'O' },
            apple: { name: 'Apple Calendar', icon: 'A' },
            slack: { name: 'Slack', icon: 'S' }
        };

        return platformMap[platform] || { name: platform, icon: '?' };
    }

    formatDate(dateString) {
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('ko-KR', {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (error) {
            return '알 수 없음';
        }
    }

    showSuccess(message) {
        this.showMessage(message, 'success');
    }

    showError(message) {
        this.showMessage(message, 'error');
    }

    showMessage(message, type) {
        // 기존 메시지 제거
        const existingResult = document.querySelector('.export-result');
        if (existingResult) {
            existingResult.remove();
        }

        // 새 메시지 생성
        const resultDiv = document.createElement('div');
        resultDiv.className = `export-result ${type}`;
        resultDiv.textContent = message;
        resultDiv.style.display = 'block';

        const modalFooter = document.querySelector('.export-modal .modal-footer');
        if (modalFooter) {
            modalFooter.insertBefore(resultDiv, modalFooter.firstChild);
        }

        // 5초 후 자동 제거
        setTimeout(() => {
            if (resultDiv.parentNode) {
                resultDiv.remove();
            }
        }, 5000);
    }
}

// 전역 함수들 (HTML에서 호출)
let exportManager = null;

// DOM 로드 후 매니저 초기화
document.addEventListener('DOMContentLoaded', function() {
    exportManager = new CalendarExportManager();
});

function openShareModal() {
    if (exportManager) {
        exportManager.openModal();
    } else {
        console.error('Export manager not initialized');
    }
}

function closeExportModal() {
    if (exportManager) {
        exportManager.closeModal();
    }
}

function startExport() {
    if (exportManager) {
        exportManager.startExport();
    }
}

// ESC 키로 모달 닫기
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && exportManager) {
        exportManager.closeModal();
    }
});