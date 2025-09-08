// 主题切换系统

class ThemeManager {
    constructor() {
        this.themes = {
            light: 'light',
            dark: 'dark',
            auto: 'auto'
        };
        
        this.currentTheme = this.themes.auto;
        this.selector = null;
        
        this.init();
    }
    
    init() {
        // 从localStorage读取保存的主题设置
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme && Object.values(this.themes).includes(savedTheme)) {
            this.currentTheme = savedTheme;
            console.log(`从localStorage恢复主题设置: ${savedTheme}`);
        } else {
            console.log('使用默认主题: auto');
        }
        
        // 设置选择器监听器
        this.setupSelectorListener();
        
        // 应用主题
        this.applyTheme();
        
        // 监听系统主题变化
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            mediaQuery.addEventListener('change', () => {
                if (this.currentTheme === this.themes.auto) {
                    console.log('系统主题发生变化，重新应用auto模式');
                    this.applyTheme();
                }
            });
        }
    }
    
    // 设置选择器监听器
    setupSelectorListener() {
        const selector = document.getElementById('theme-selector');
        if (selector) {
            this.selector = selector;
            
            // 设置当前选中值
            this.selector.value = this.currentTheme;
            
            // 移除旧的监听器
            if (this.handleThemeChange) {
                selector.removeEventListener('change', this.handleThemeChange);
            }
            
            // 创建新的监听器
            this.handleThemeChange = (e) => {
                const selectedTheme = e.target.value;
                console.log(`主题选择器变化: ${selectedTheme}`);
                this.setTheme(selectedTheme);
            };
            
            // 绑定监听器
            selector.addEventListener('change', this.handleThemeChange);
            console.log(`主题选择器监听器已设置，当前主题: ${this.currentTheme}`);
        } else {
            console.warn('未找到主题选择器元素，稍后重试');
            // 如果元素还没有准备好，稍后再试
            setTimeout(() => {
                this.setupSelectorListener();
            }, 100);
        }
    }
    
    // 获取系统主题偏好
    getSystemTheme() {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return this.themes.dark;
        }
        return this.themes.light;
    }
    
    // 获取实际应用的主题（处理auto模式）
    getEffectiveTheme() {
        if (this.currentTheme === this.themes.auto) {
            return this.getSystemTheme();
        }
        return this.currentTheme;
    }
    
    // 应用主题
    applyTheme() {
        const effectiveTheme = this.getEffectiveTheme();
        const root = document.documentElement;
        
        console.log(`正在应用主题: ${this.currentTheme} (实际应用: ${effectiveTheme})`);
        
        // 移除所有主题属性
        root.removeAttribute('data-theme');
        
        // 强制浏览器重新计算样式
        void root.offsetHeight;
        
        // 应用新主题
        if (effectiveTheme === this.themes.dark) {
            root.setAttribute('data-theme', 'dark');
            console.log('已设置暗色主题');
        } else {
            // 明确设置为light主题
            root.setAttribute('data-theme', 'light');
            console.log('已设置亮色主题');
        }
        
        // 立即强制重新渲染
        void root.offsetHeight;
        
        // 更新选择器状态
        this.updateSelectorState();
        
        // 保存当前设置
        localStorage.setItem('theme', this.currentTheme);
        
        // 触发CSS重新计算和过渡动画
        document.body.classList.add('theme-transitioning');
        
        // 确保所有元素都获得了新的主题样式
        this.forceStyleRecalculation();
        
        // 触发自定义事件通知其他组件
        const themeChangeEvent = new CustomEvent('themeChanged', {
            detail: { theme: this.currentTheme, effectiveTheme: effectiveTheme }
        });
        document.dispatchEvent(themeChangeEvent);
        
        setTimeout(() => {
            document.body.classList.remove('theme-transitioning');
        }, 300);
        
        console.log(`主题切换完成: ${this.currentTheme} (实际应用: ${effectiveTheme})`);
    }
    
    // 强制样式重新计算
    forceStyleRecalculation() {
        // 强制重新计算所有可能受影响的元素
        const elementsToRefresh = [
            '.navbar', '.modal', '.card', '.form-control', '.form-select', 
            '.table', '.btn', '.list-group-item', '.log-execution-item'
        ];
        
        elementsToRefresh.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(element => {
                void element.offsetHeight;
            });
        });
    }
    
    // 更新选择器状态
    updateSelectorState() {
        if (this.selector) {
            this.selector.value = this.currentTheme;
            console.log(`选择器状态已更新: ${this.currentTheme}`);
        }
    }
    
    // 循环切换主题 (保留此方法用于键盘快捷键等场景)
    toggleTheme() {
        console.log(`切换主题前: 当前主题=${this.currentTheme}`);
        
        // 按照 light -> dark -> auto -> light 的循环顺序
        switch (this.currentTheme) {
            case this.themes.light:
                this.currentTheme = this.themes.dark;
                console.log('切换到暗色主题');
                break;
            case this.themes.dark:
                this.currentTheme = this.themes.auto;
                console.log('切换到自动主题');
                break;
            case this.themes.auto:
            default:
                this.currentTheme = this.themes.light;
                console.log('切换到亮色主题');
                break;
        }
        
        this.applyTheme();
    }
    
    // 设置主题
    setTheme(theme) {
        if (Object.values(this.themes).includes(theme)) {
            console.log(`设置主题: ${theme}`);
            this.currentTheme = theme;
            this.applyTheme();
            
            // 强制触发页面重新渲染
            this.triggerPageRefresh();
        }
    }
    
    // 触发页面内容重新渲染
    triggerPageRefresh() {
        // 如果有当前tab内容，重新加载
        if (window.loadCurrentTab && typeof window.loadCurrentTab === 'function') {
            setTimeout(() => {
                try {
                    window.loadCurrentTab();
                } catch (e) {
                    console.log('无法重新加载当前tab内容:', e);
                }
            }, 100);
        }
        
        // 触发自定义主题变更事件
        const themeChangeEvent = new CustomEvent('themeChanged', {
            detail: {
                theme: this.currentTheme,
                effectiveTheme: this.getEffectiveTheme()
            }
        });
        document.dispatchEvent(themeChangeEvent);
    }
    
    // 获取当前主题
    getCurrentTheme() {
        return this.currentTheme;
    }
    
    // 获取实际主题（用于UI显示）
    getDisplayTheme() {
        return this.getEffectiveTheme();
    }
    
    // 重新初始化主题系统（用于动态内容加载后）
    reinitialize() {
        console.log('重新初始化主题系统');
        this.setupSelectorListener();
        this.applyTheme();
    }
}

// 全局主题管理器实例
let themeManager;

// 确保主题系统尽早初始化
function initThemeManager() {
    if (!themeManager) {
        themeManager = new ThemeManager();
        window.themeManager = themeManager;
        console.log('主题管理器已初始化');
    }
    return themeManager;
}

// 多种方式确保主题管理器初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initThemeManager);
} else {
    // 如果DOM已经加载完成，立即初始化
    initThemeManager();
}

// 添加额外的初始化检查
setTimeout(() => {
    if (!themeManager) {
        console.warn('主题管理器延迟初始化');
        initThemeManager();
    }
}, 100);

// 提供便捷的全局函数
function toggleTheme() {
    if (themeManager) {
        themeManager.toggleTheme();
    }
}

function setTheme(theme) {
    if (themeManager) {
        themeManager.setTheme(theme);
    }
}

function getCurrentTheme() {
    return themeManager ? themeManager.getCurrentTheme() : 'auto';
}

// 导出供模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ThemeManager, toggleTheme, setTheme, getCurrentTheme };
}