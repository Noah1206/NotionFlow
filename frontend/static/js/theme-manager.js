/**
 * 🎨 NotionFlow Theme Manager - Light Mode Only
 * 다크 모드를 완전히 비활성화하고 라이트 모드만 강제 사용
 */

// 중복 선언 방지
if (typeof window.ThemeManager !== 'undefined') {
    // console.log('🎨 ThemeManager already exists, skipping redefinition');
} else {

class ThemeManager {
    constructor() {
        this.THEME_KEY = 'theme';
        this.THEMES = {
            LIGHT: 'light'  // 다크 모드 제거
        };
        
        // 항상 라이트 모드로 초기화
        this.forceLightMode();
        
        // 다크 모드 토글 버튼들 숨기기
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.hideDarkModeToggles());
        } else {
            this.hideDarkModeToggles();
        }
    }

    /**
     * 라이트 모드로 강제 설정
     */
    forceLightMode() {
        this.applyTheme('light');
        
        // 다크 모드 관련 localStorage 제거
        localStorage.removeItem(this.THEME_KEY);
        localStorage.setItem(this.THEME_KEY, 'light');
        
        console.log('🎨 Forced light mode only');
    }

    /**
     * Apply theme to document (라이트 모드만)
     */
    applyTheme(theme) {
        const html = document.documentElement;
        const body = document.body;
        
        // 항상 라이트 모드로 강제 설정
        html.setAttribute('data-theme', 'light');
        html.removeAttribute('data-bs-theme'); // Bootstrap 다크 모드 제거
        
        if (body) {
            body.setAttribute('data-theme', 'light');
            body.className = body.className.replace(/\b(dark|dark-theme|dark-mode)\b/g, '').trim();
            body.classList.add('light-theme');
            body.style.background = '#ffffff';
            body.style.color = '#000000';
        }
        
        // 다크 모드 관련 클래스 모두 제거
        document.querySelectorAll('.dark, .dark-theme, .dark-mode, [data-theme="dark"]').forEach(el => {
            el.classList.remove('dark', 'dark-theme', 'dark-mode');
            el.setAttribute('data-theme', 'light');
            el.style.background = '#ffffff';
            el.style.color = '#000000';
        });
        
        localStorage.setItem(this.THEME_KEY, 'light');
        console.log('🎨 Light theme applied (forced)');
    }

    /**
     * 다크 모드 토글 비활성화
     */
    toggleTheme() {
        // 다크 모드 토글 비활성화 - 항상 라이트 모드 유지
        this.forceLightMode();
        console.log('🎨 Dark mode toggle disabled - staying in light mode');
    }

    /**
     * Get current theme (항상 라이트 모드)
     */
    getCurrentTheme() {
        return 'light';
    }

    /**
     * 다크 모드 토글 버튼들 숨기기
     */
    hideDarkModeToggles() {
        const toggleSelectors = [
            '#theme-toggle',
            '.theme-toggle',
            '.dark-mode-toggle',
            '[data-theme-toggle]',
            '.theme-switch'
        ];
        
        toggleSelectors.forEach(selector => {
            document.querySelectorAll(selector).forEach(element => {
                element.style.display = 'none';
                element.disabled = true;
            });
        });
        
        // 다크 모드 관련 아이콘들도 숨기기
        document.querySelectorAll('.fa-moon, .theme-icon, .dark-mode-icon').forEach(icon => {
            icon.style.display = 'none';
        });
        
        console.log('🎨 Dark mode toggles hidden');
    }

    /**
     * Force theme (라이트 모드만)
     */
    setTheme(theme) {
        // 무엇을 요청하든 항상 라이트 모드만
        this.forceLightMode();
    }

    /**
     * Reset theme (라이트 모드로)
     */
    resetToSystemTheme() {
        this.forceLightMode();
    }
}

// Global theme manager instance - prevent duplicate declarations
window.ThemeManager = ThemeManager;  // Store class reference

if (!window.themeManager) {
    window.themeManager = new ThemeManager();
}

// Global utility functions - 모든 함수는 라이트 모드만 지원
window.toggleTheme = () => {
    console.log('🎨 Theme toggle disabled - light mode only');
    window.themeManager.forceLightMode();
};
window.setTheme = (theme) => window.themeManager.forceLightMode();
window.resetTheme = () => window.themeManager.forceLightMode();

// 주기적으로 다크 모드 감지 및 제거
setInterval(() => {
    if (window.themeManager) {
        // 다크 모드로 설정된 요소들을 감지하고 라이트 모드로 변경
        if (document.documentElement.getAttribute('data-theme') === 'dark') {
            window.themeManager.forceLightMode();
        }
        
        // 다크 모드 관련 클래스가 있는 요소들 정리
        document.querySelectorAll('.dark, .dark-theme, .dark-mode').forEach(el => {
            el.classList.remove('dark', 'dark-theme', 'dark-mode');
            el.classList.add('light-theme');
            el.style.background = '#ffffff';
            el.style.color = '#000000';
        });
    }
}, 500);

// Export for module usage if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeManager;
}

console.log('🎨 NotionFlow Theme Manager loaded - Light mode only');

} // End of duplicate prevention check