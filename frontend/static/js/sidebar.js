/**
 * 🚀 NotionFlow Dashboard Sidebar Module
 * 재사용 가능한 사이드바 컴포넌트 JavaScript
 */

class SidebarManager {
    constructor() {
        this.sidebar = null;
        this.toggleBtn = null;
        this.mobileMenuToggle = null;
        this.overlay = null;
        this.isInitialized = false;
    }

    /**
     * 🎯 사이드바 초기화
     */
    init() {
        if (this.isInitialized) {
            // // Console warn removed
            return;
        }

        try {
            // DOM 요소 찾기
            this.sidebar = document.getElementById('sidebar');
            this.toggleBtn = document.getElementById('sidebar-toggle');
            this.mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
            this.overlay = document.querySelector('.sidebar-overlay');

            if (!this.sidebar) {
                // // Console warn removed
                return;
            }

            // 이벤트 리스너 설정
            this.setupEventListeners();
            this.setupMobileSupport();
            this.updateActiveNavItem();
            this.restoreSidebarState();

            // 사용자 로그인 후 사이드바 링크 업데이트
            setTimeout(() => {
                this.updateSidebarLinksWithUserID();
            }, 500);

            this.isInitialized = true;
            // // Console log removed
        } catch (error) {
            // Console error removed
        }
    }

    /**
     * 🖱️ 이벤트 리스너 설정
     */
    setupEventListeners() {
        // 데스크톱 토글 버튼
        if (this.toggleBtn) {
            this.toggleBtn.addEventListener('click', () => this.toggleSidebar());
        }

        // 모바일 메뉴 토글
        if (this.mobileMenuToggle) {
            this.mobileMenuToggle.addEventListener('click', () => this.toggleMobileSidebar());
        }

        // 오버레이 클릭으로 사이드바 닫기
        if (this.overlay) {
            this.overlay.addEventListener('click', () => this.closeMobileSidebar());
        }

        // ESC 키로 모바일 사이드바 닫기
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.sidebar?.classList.contains('mobile-open')) {
                this.closeMobileSidebar();
            }
        });

        // 윈도우 리사이즈 처리
        window.addEventListener('resize', () => this.handleResize());
    }

    /**
     * 📱 모바일 지원 설정
     */
    setupMobileSupport() {
        // 모바일 메뉴 토글 버튼이 없으면 생성
        if (!this.mobileMenuToggle && window.innerWidth <= 768) {
            this.createMobileMenuToggle();
        }

        // 오버레이가 없으면 생성
        if (!this.overlay) {
            this.createOverlay();
        }
    }

    /**
     * 🍔 모바일 메뉴 토글 버튼 생성
     */
    createMobileMenuToggle() {
        const toggleBtn = document.createElement('button');
        toggleBtn.className = 'mobile-menu-toggle';
        toggleBtn.innerHTML = '☰';
        toggleBtn.setAttribute('aria-label', '메뉴 열기');
        
        document.body.appendChild(toggleBtn);
        this.mobileMenuToggle = toggleBtn;
        
        // 이벤트 리스너 추가
        toggleBtn.addEventListener('click', () => this.toggleMobileSidebar());
    }

    /**
     * 🌫️ 오버레이 생성
     */
    createOverlay() {
        const overlay = document.createElement('div');
        overlay.className = 'sidebar-overlay';
        document.body.appendChild(overlay);
        this.overlay = overlay;
        
        // 이벤트 리스너 추가
        overlay.addEventListener('click', () => this.closeMobileSidebar());
    }

    /**
     * 🔄 사이드바 토글 (데스크톱)
     */
    toggleSidebar() {
        if (!this.sidebar) return;

        this.sidebar.classList.toggle('collapsed');
        
        // 사이드바 컨테이너 클래스 관리 - floating 버튼 표시/숨김용
        const sidebarContainer = document.querySelector('.sidebar-container');
        if (sidebarContainer) {
            if (this.sidebar.classList.contains('collapsed')) {
                sidebarContainer.classList.add('sidebar-collapsed');
            } else {
                sidebarContainer.classList.remove('sidebar-collapsed');
            }
        }
        
        // body 클래스 관리 - 모든 대시보드 페이지에서 사이드바 상태 반영
        if (this.sidebar.classList.contains('collapsed')) {
            document.body.classList.add('sidebar-collapsed');
        } else {
            document.body.classList.remove('sidebar-collapsed');
        }
        
        // 토글 아이콘 업데이트
        this.updateToggleIcon();
        
        // 상태 저장
        this.saveSidebarState();
        
        // 커스텀 이벤트 발생
        this.dispatchSidebarEvent('sidebar-toggle', {
            collapsed: this.sidebar.classList.contains('collapsed')
        });
    }

    /**
     * 📱 모바일 사이드바 토글
     */
    toggleMobileSidebar() {
        if (window.innerWidth > 768) return;

        if (this.sidebar?.classList.contains('mobile-open')) {
            this.closeMobileSidebar();
        } else {
            this.openMobileSidebar();
        }
    }

    /**
     * 📱 모바일 사이드바 열기
     */
    openMobileSidebar() {
        if (!this.sidebar) return;

        this.sidebar.classList.add('mobile-open');
        this.overlay?.classList.add('active');
        document.body.style.overflow = 'hidden'; // 배경 스크롤 방지
        
        // 포커스 관리
        this.sidebar.focus();
        
        this.dispatchSidebarEvent('mobile-sidebar-open');
    }

    /**
     * 📱 모바일 사이드바 닫기
     */
    closeMobileSidebar() {
        if (!this.sidebar) return;

        this.sidebar.classList.remove('mobile-open');
        this.overlay?.classList.remove('active');
        document.body.style.overflow = ''; // 스크롤 복원
        
        this.dispatchSidebarEvent('mobile-sidebar-close');
    }

    /**
     * 🎯 토글 아이콘 업데이트
     */
    updateToggleIcon() {
        // 실제 존재하는 토글 버튼들 사용
        const expandedHeader = document.querySelector('.expanded-header');
        const collapsedHeader = document.querySelector('.collapsed-header');
        
        if (this.sidebar?.classList.contains('collapsed')) {
            if (expandedHeader) expandedHeader.style.display = 'none';
            if (collapsedHeader) collapsedHeader.style.display = 'block';
        } else {
            if (expandedHeader) expandedHeader.style.display = 'flex';
            if (collapsedHeader) collapsedHeader.style.display = 'none';
        }
    }

    /**
     * 🎯 활성 네비게이션 아이템 업데이트
     */
    updateActiveNavItem() {
        const navItems = document.querySelectorAll('.sidebar .nav-item');
        const currentPath = window.location.pathname;
        
        navItems.forEach(item => {
            const href = item.getAttribute('href');
            if (href && this.isActivePath(currentPath, href)) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
    }

    /**
     * 🔗 사이드바 링크를 사용자 고유 URL로 업데이트
     */
    async updateSidebarLinksWithUserID() {
        try {
            // 인증 서비스가 있는지 확인
            if (typeof window.authService === 'undefined') {
                // // Console log removed
                return;
            }

            // 사용자 대시보드 정보 가져오기
            const dashboardInfo = await window.authService.getDashboardInfo();
            
            if (dashboardInfo.success && dashboardInfo.encrypted_user_id) {
                // // Console log removed
                
                // 사이드바 링크들 업데이트
                const calendarLink = document.getElementById('nav-calendar-link');
                const settingsLink = document.getElementById('nav-settings-link');
                
                if (calendarLink) {
                    // Remove href to prevent navigation, use onclick instead
                    calendarLink.removeAttribute('href');
                    calendarLink.onclick = function(e) {
                        e.preventDefault();
                        if (typeof window.navigateToSection === 'function') {
                            window.navigateToSection('calendar');
                        } else {
                            // Console warn removed
                        }
                    };
                    // // Console log removed
                }
                
                if (settingsLink) {
                    const newSettingsHref = `/dashboard/settings`;
                    settingsLink.setAttribute('href', newSettingsHref);
                    // // Console log removed
                }
                
                // 활성 아이템 다시 업데이트
                this.updateActiveNavItem();
                
                return true;
            } else {
                // // Console log removed
                return false;
            }
            
        } catch (error) {
            // Console error removed
            return false;
        }
    }

    /**
     * 🎯 경로 활성 상태 확인
     */
    isActivePath(currentPath, itemHref) {
        // 정확한 매치
        if (currentPath === itemHref) return true;
        
        // 대시보드 홈 특별 처리
        if (itemHref.endsWith('dashboard') && 
            (currentPath.endsWith('dashboard') || currentPath.endsWith('dashboard/index'))) {
            return true;
        }
        
        // 서브 경로 매치
        if (itemHref !== '/' && currentPath.startsWith(itemHref)) {
            return true;
        }
        
        return false;
    }

    /**
     * 💾 사이드바 상태 저장
     */
    saveSidebarState() {
        if (this.sidebar) {
            const isCollapsed = this.sidebar.classList.contains('collapsed');
            localStorage.setItem('sidebar-collapsed', isCollapsed.toString());
        }
    }

    /**
     * 📖 사이드바 상태 복원
     */
    restoreSidebarState() {
        const savedState = localStorage.getItem('sidebar-collapsed');
        
        // 저장된 상태가 없으면 기본적으로 접힌 상태로 시작
        if (savedState === null || savedState === 'true') {
            if (this.sidebar) {
                this.sidebar.classList.add('collapsed');
                this.updateToggleIcon();
                
                // 사이드바 컨테이너 클래스 관리 - floating 버튼 표시/숨김용
                const sidebarContainer = document.querySelector('.sidebar-container');
                if (sidebarContainer) {
                    sidebarContainer.classList.add('sidebar-collapsed');
                }
                
                // body 클래스 관리 - 모든 대시보드 페이지에서 사이드바 상태 반영
                document.body.classList.add('sidebar-collapsed');
            }
        }
    }

    /**
     * 📐 윈도우 리사이즈 처리
     */
    handleResize() {
        // 데스크톱으로 변경 시 모바일 상태 초기화
        if (window.innerWidth > 768) {
            this.closeMobileSidebar();
            
            // 모바일 메뉴 토글 숨기기
            if (this.mobileMenuToggle) {
                this.mobileMenuToggle.style.display = 'none';
            }
        } else {
            // 모바일로 변경 시 모바일 메뉴 토글 표시
            if (this.mobileMenuToggle) {
                this.mobileMenuToggle.style.display = 'block';
            }
        }
    }

    /**
     * 📡 사이드바 이벤트 발송
     */
    dispatchSidebarEvent(eventName, detail = {}) {
        const event = new CustomEvent(eventName, { 
            detail: detail,
            bubbles: true 
        });
        document.dispatchEvent(event);
    }

    /**
     * 🧹 정리
     */
    destroy() {
        // 이벤트 리스너 제거
        if (this.toggleBtn) {
            this.toggleBtn.removeEventListener('click', this.toggleSidebar);
        }
        
        if (this.mobileMenuToggle) {
            this.mobileMenuToggle.remove();
        }
        
        if (this.overlay) {
            this.overlay.remove();
        }
        
        document.body.style.overflow = '';
        this.isInitialized = false;
    }
}

// 전역 사이드바 인스턴스
let sidebarManager = null;

/**
 * 🚀 사이드바 초기화 함수
 */
function initSidebar() {
    if (!sidebarManager) {
        sidebarManager = new SidebarManager();
    }
    sidebarManager.init();
}

/**
 * 🎯 사이드바 API 노출
 */
window.sidebarAPI = {
    init: initSidebar,
    toggle: () => sidebarManager?.toggleSidebar(),
    collapse: () => {
        if (sidebarManager?.sidebar && !sidebarManager.sidebar.classList.contains('collapsed')) {
            sidebarManager.toggleSidebar();
        }
    },
    expand: () => {
        if (sidebarManager?.sidebar && sidebarManager.sidebar.classList.contains('collapsed')) {
            sidebarManager.toggleSidebar();
        }
    },
    updateActiveItem: () => sidebarManager?.updateActiveNavItem(),
    updateLinksWithUserID: () => sidebarManager?.updateSidebarLinksWithUserID()
};

// 전역 toggleSidebar 함수 - HTML onclick에서 직접 호출 가능
window.toggleSidebar = function() {
    // // Console log removed // 디버그용
    
    if (sidebarManager) {
        sidebarManager.toggleSidebar();
        
        // 토글 버튼 아이콘 업데이트
        const floatingBtn = document.getElementById('sidebar-toggle-floating');
        // 실제 존재하는 토글 버튼들 사용
        const expandedHeader = document.querySelector('.expanded-header');
        const collapsedHeader = document.querySelector('.collapsed-header');
        
        if (sidebarManager.sidebar?.classList.contains('collapsed')) {
            // 사이드바가 접혔을 때 - 햄버거 아이콘 표시
            if (expandedHeader) expandedHeader.style.display = 'none';
            if (collapsedHeader) collapsedHeader.style.display = 'block';
        } else {
            // 사이드바가 펼쳐졌을 때 - 닫기 아이콘 표시
            if (expandedHeader) expandedHeader.style.display = 'flex';
            if (collapsedHeader) collapsedHeader.style.display = 'none';
        }
    } else {
        // // Console log removed // 디버그용
    }
};

// DOM 로드 완료 시 자동 초기화
document.addEventListener('DOMContentLoaded', initSidebar);

// 브라우저 뒤로가기/앞으로가기 시 활성 아이템 업데이트
window.addEventListener('popstate', () => {
    setTimeout(() => sidebarManager?.updateActiveNavItem(), 100);
});

// 전역으로 SidebarManager 클래스 노출 (모듈 시스템 없이 사용하는 경우를 위해)
window.SidebarManager = SidebarManager;

// 캘린더 만들기 모달 제어 함수들
function openCalendarModal() {
    const modal = document.getElementById('calendar-modal');
    if (modal) {
        modal.classList.remove('hidden');
    }
}

function closeCalendarModal() {
    const modal = document.getElementById('calendar-modal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

function createPersonalCalendar() {
    if (typeof createCalendar === 'function') {
        createCalendar('personal');
    }
    closeCalendarModal();
}

function createSharedCalendar() {
    if (typeof createCalendar === 'function') {
        createCalendar('shared');
    }
    closeCalendarModal();
}