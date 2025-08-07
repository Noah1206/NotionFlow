/**
 * 🎨 NotionFlow Theme Manager
 * Handles dark/light mode persistence and switching across all pages
 */

// 중복 선언 방지
if (typeof window.ThemeManager !== 'undefined') {
    // console.log('🎨 ThemeManager already exists, skipping redefinition');
} else {

class ThemeManager {
    constructor() {
        this.THEME_KEY = 'theme'; // Keep same key as original dashboard code
        this.THEMES = {
            DARK: 'dark',
            LIGHT: 'light'
        };
        
        // Initialize theme immediately to prevent flash
        this.initializeTheme();
        
        // Wait for DOM to be ready for toggle button
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupToggleButton());
        } else {
            this.setupToggleButton();
        }
    }

    /**
     * Initialize theme from localStorage or default to dark
     */
    initializeTheme() {
        const savedTheme = localStorage.getItem(this.THEME_KEY);
        const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        // Priority: saved theme > system preference > default dark
        const theme = savedTheme || (systemPrefersDark ? this.THEMES.DARK : this.THEMES.LIGHT);
        
        this.applyTheme(theme);
        
        // console.log(`🎨 Theme initialized: ${theme}`);
    }

    /**
     * Apply theme to document
     */
    applyTheme(theme) {
        const html = document.documentElement;
        const body = document.body;
        
        // Set data-theme attribute
        html.setAttribute('data-theme', theme);
        
        // Also set on body for compatibility
        if (body) {
            body.setAttribute('data-theme', theme);
        }
        
        // Save to localStorage
        localStorage.setItem(this.THEME_KEY, theme);
        
        // Update toggle button if it exists
        this.updateToggleButton(theme);
        
        // console.log(`🎨 Theme applied: ${theme}`);
    }

    /**
     * Toggle between dark and light themes
     */
    toggleTheme() {
        const currentTheme = this.getCurrentTheme();
        const newTheme = currentTheme === this.THEMES.DARK ? this.THEMES.LIGHT : this.THEMES.DARK;
        
        // Add visual feedback to the toggle button
        const toggleButton = document.getElementById('theme-toggle');
        if (toggleButton) {
            toggleButton.style.transform = 'scale(0.95)';
            setTimeout(() => {
                toggleButton.style.transform = 'scale(1)';
            }, 150);
            
            // Force update slider color immediately
            const slider = toggleButton.nextElementSibling;
            if (slider && slider.classList.contains('toggle-slider')) {
                const isChecked = toggleButton.checked;
                if (isChecked) {
                    slider.style.backgroundColor = '#00d15a';
                } else {
                    slider.style.backgroundColor = newTheme === this.THEMES.DARK ? '#8e8e93' : '#ccc';
                }
            }
        }
        
        this.applyTheme(newTheme);
        
        // Dispatch custom event for components that need to react to theme changes
        window.dispatchEvent(new CustomEvent('themeChanged', {
            detail: { theme: newTheme, previousTheme: currentTheme }
        }));
        
        // console.log(`🎨 Theme toggled: ${currentTheme} → ${newTheme}`);
    }

    /**
     * Get current theme
     */
    getCurrentTheme() {
        return document.documentElement.getAttribute('data-theme') || this.THEMES.DARK;
    }

    /**
     * Setup theme toggle button
     */
    setupToggleButton() {
        // Don't create toggle button in sidebar - only look for existing ones
        let toggleButton = document.getElementById('theme-toggle');
        
        // Don't create new button anymore
        // if (!toggleButton) {
        //     toggleButton = this.createToggleButton();
        // }
        
        if (toggleButton) {
            // Check if already has our listener to prevent duplicates
            if (!toggleButton.hasAttribute('data-theme-listener')) {
                // Remove any existing listeners first
                const newButton = toggleButton.cloneNode(true);
                toggleButton.parentNode.replaceChild(newButton, toggleButton);
                toggleButton = newButton;
                
                // Add appropriate event listener based on element type
                if (toggleButton.type === 'checkbox') {
                    // For checkbox toggle switch
                    toggleButton.addEventListener('change', (e) => {
                        e.stopPropagation();
                        this.toggleTheme();
                    });
                } else {
                    // For button style
                    toggleButton.addEventListener('click', (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        this.toggleTheme();
                    });
                }
                
                // Mark as having our listener
                toggleButton.setAttribute('data-theme-listener', 'true');
            }
            
            // Update initial state
            this.updateToggleButton(this.getCurrentTheme());
            
            // console.log('🎨 Theme toggle button initialized');
        }
    }

    /**
     * Create theme toggle button if it doesn't exist
     */
    createToggleButton() {
        // DISABLED: Don't create toggle button automatically
        // User wants theme toggle only in settings modal
        console.log('🎨 Theme toggle button creation disabled - use settings modal instead');
        return null;
    }

    /**
     * Update toggle button appearance
     */
    updateToggleButton(theme) {
        const toggleButton = document.getElementById('theme-toggle');
        if (!toggleButton) return;
        
        const isDark = theme === this.THEMES.DARK;
        
        // Check if it's a checkbox input (toggle switch style)
        if (toggleButton.type === 'checkbox') {
            // For toggle switch: checked = dark mode
            toggleButton.checked = isDark;
            
            // Force update slider color based on checked state
            const slider = toggleButton.nextElementSibling;
            if (slider && slider.classList.contains('toggle-slider')) {
                if (toggleButton.checked) {
                    // ON state - green color
                    slider.style.backgroundColor = '#00d15a';
                } else {
                    // OFF state - gray color
                    slider.style.backgroundColor = isDark ? '#8e8e93' : '#ccc';
                }
            }
            
            // Update label text if it exists
            const themeLabel = toggleButton.closest('.theme-toggle')?.querySelector('.theme-toggle-label');
            if (themeLabel) {
                themeLabel.textContent = isDark ? '다크모드' : '라이트모드';
            }
        } else {
            // For button style (fallback)
            const buttonText = isDark ? '라이트모드' : '다크모드';
            const themeTextSpan = toggleButton.querySelector('.theme-text');
            if (themeTextSpan) {
                themeTextSpan.textContent = buttonText;
            } else {
                toggleButton.innerHTML = buttonText;
            }
        }
        
        // Update title and accessibility
        const titleText = isDark ? '라이트 모드로 전환' : '다크 모드로 전환';
        toggleButton.title = titleText;
        toggleButton.setAttribute('aria-label', titleText);
    }

    /**
     * Listen for system theme changes
     */
    setupSystemThemeListener() {
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        
        mediaQuery.addListener((e) => {
            // Only auto-switch if user hasn't manually set a theme
            const savedTheme = localStorage.getItem(this.THEME_KEY);
            if (!savedTheme) {
                const systemTheme = e.matches ? this.THEMES.DARK : this.THEMES.LIGHT;
                this.applyTheme(systemTheme);
            }
        });
    }

    /**
     * Force theme (for testing or special cases)
     */
    setTheme(theme) {
        if (Object.values(this.THEMES).includes(theme)) {
            this.applyTheme(theme);
        } else {
            // console.warn(`🎨 Invalid theme: ${theme}`);
        }
    }

    /**
     * Reset theme to system preference
     */
    resetToSystemTheme() {
        localStorage.removeItem(this.THEME_KEY);
        const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        const systemTheme = systemPrefersDark ? this.THEMES.DARK : this.THEMES.LIGHT;
        
        this.applyTheme(systemTheme);
        // console.log(`🎨 Theme reset to system preference: ${systemTheme}`);
    }
}

// Global theme manager instance - prevent duplicate declarations
window.ThemeManager = ThemeManager;  // Store class reference

if (!window.themeManager) {
    window.themeManager = new ThemeManager();
}

// Global utility functions for easy access
window.toggleTheme = () => window.themeManager.toggleTheme();
window.setTheme = (theme) => window.themeManager.setTheme(theme);
window.resetTheme = () => window.themeManager.resetToSystemTheme();

// Export for module usage if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeManager;
}

// console.log('🎨 NotionFlow Theme Manager loaded');

} // End of duplicate prevention check