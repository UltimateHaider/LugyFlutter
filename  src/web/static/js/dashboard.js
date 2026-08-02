/**
 * LugyFlutter - Dashboard JavaScript
 * ملف JavaScript الخاص بلوحة التحكم Streamlit
 * يحتوي على وظائف تفاعلية وتحسينات للواجهة
 */

// ============================================================
// الإعدادات العامة
// ============================================================

const LUGY_CONFIG = {
    // إعدادات التحديث التلقائي
    AUTO_REFRESH: true,
    REFRESH_INTERVAL: 5000, // 5 ثواني
    
    // إعدادات الإشعارات
    NOTIFICATIONS: true,
    NOTIFICATION_DURATION: 3000, // 3 ثواني
    
    // إعدادات الرسوم البيانية
    CHART_ANIMATION: true,
    CHART_DURATION: 500, // 0.5 ثانية
    
    // إعدادات السجلات
    LOG_AUTO_SCROLL: true,
    LOG_MAX_LINES: 1000
};


// ============================================================
// إدارة الحالة (State Management)
// ============================================================

const LugyState = {
    _data: {},
    _listeners: [],
    
    // تحديث الحالة
    set(key, value) {
        this._data[key] = value;
        this._notifyListeners(key, value);
    },
    
    // الحصول على قيمة
    get(key, defaultValue = null) {
        return this._data.hasOwnProperty(key) ? this._data[key] : defaultValue;
    },
    
    // إضافة مستمع
    addListener(callback) {
        this._listeners.push(callback);
    },
    
    // إزالة مستمع
    removeListener(callback) {
        const index = this._listeners.indexOf(callback);
        if (index > -1) {
            this._listeners.splice(index, 1);
        }
    },
    
    // إعلام المستمعين
    _notifyListeners(key, value) {
        this._listeners.forEach(callback => {
            try {
                callback(key, value);
            } catch (e) {
                console.error('خطأ في مستمع الحالة:', e);
            }
        });
    },
    
    // مسح الحالة
    clear() {
        this._data = {};
        this._listeners = [];
    }
};


// ============================================================
// إدارة الإشعارات (Notification System)
// ============================================================

class NotificationManager {
    constructor() {
        this.container = null;
        this.notifications = [];
        this._initContainer();
    }
    
    _initContainer() {
        // إنشاء حاوية الإشعارات
        this.container = document.createElement('div');
        this.container.id = 'lugy-notifications';
        this.container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-width: 400px;
            width: 100%;
            pointer-events: none;
        `;
        document.body.appendChild(this.container);
    }
    
    show(message, type = 'info', duration = LUGY_CONFIG.NOTIFICATION_DURATION) {
        if (!LUGY_CONFIG.NOTIFICATIONS) return;
        
        const notification = this._createNotification(message, type);
        this.container.appendChild(notification);
        this.notifications.push(notification);
        
        // إزالة الإشعار بعد المدة المحددة
        setTimeout(() => {
            this._removeNotification(notification);
        }, duration);
        
        // إزالة الإشعارات القديمة (حد أقصى 5)
        if (this.notifications.length > 5) {
            const oldest = this.notifications.shift();
            if (oldest && oldest.parentNode) {
                oldest.parentNode.removeChild(oldest);
            }
        }
    }
    
    _createNotification(message, type) {
        const colors = {
            success: '#4CAF50',
            error: '#F44336',
            warning: '#FFC107',
            info: '#6200EE'
        };
        
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        
        const div = document.createElement('div');
        div.style.cssText = `
            background: #1E1E2E;
            border-left: 4px solid ${colors[type] || colors.info};
            border-radius: 8px;
            padding: 12px 16px;
            color: #FFFFFF;
            font-size: 14px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            display: flex;
            align-items: center;
            gap: 12px;
            animation: slideInRight 0.3s ease;
            pointer-events: auto;
            cursor: pointer;
        `;
        
        const icon = document.createElement('span');
        icon.textContent = icons[type] || icons.info;
        icon.style.fontSize = '20px';
        
        const text = document.createElement('span');
        text.textContent = message;
        text.style.flex = '1';
        
        const closeBtn = document.createElement('span');
        closeBtn.textContent = '✕';
        closeBtn.style.cssText = `
            cursor: pointer;
            opacity: 0.6;
            font-size: 16px;
            padding: 0 4px;
            transition: opacity 0.2s;
        `;
        closeBtn.onmouseover = () => closeBtn.style.opacity = '1';
        closeBtn.onmouseout = () => closeBtn.style.opacity = '0.6';
        closeBtn.onclick = () => this._removeNotification(div);
        
        div.appendChild(icon);
        div.appendChild(text);
        div.appendChild(closeBtn);
        
        // إضافة حدث النقر لإغلاق الإشعار
        div.onclick = (e) => {
            if (e.target !== closeBtn) {
                this._removeNotification(div);
            }
        };
        
        return div;
    }
    
    _removeNotification(notification) {
        if (notification && notification.parentNode) {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }
        
        const index = this.notifications.indexOf(notification);
        if (index > -1) {
            this.notifications.splice(index, 1);
        }
    }
    
    success(message, duration) {
        this.show(message, 'success', duration);
    }
    
    error(message, duration) {
        this.show(message, 'error', duration);
    }
    
    warning(message, duration) {
        this.show(message, 'warning', duration);
    }
    
    info(message, duration) {
        this.show(message, 'info', duration);
    }
}


// ============================================================
// إدارة السجلات (Log Viewer)
// ============================================================

class LogViewer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.lines = [];
        this.maxLines = LUGY_CONFIG.LOG_MAX_LINES;
        this.autoScroll = LUGY_CONFIG.LOG_AUTO_SCROLL;
        this._initViewer();
    }
    
    _initViewer() {
        if (!this.container) return;
        
        // إضافة أنماط CSS
        this.container.style.cssText = `
            background: #0D0D1A;
            border-radius: 8px;
            padding: 12px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            color: #C8C8D4;
            max-height: 400px;
            overflow-y: auto;
            overflow-x: auto;
            white-space: pre-wrap;
            word-break: break-all;
        `;
        
        // إضافة عنصر فارغ
        this.container.textContent = '📝 انتظار السجلات...';
        
        // إضافة مستمع للتمرير التلقائي
        this.container.addEventListener('scroll', () => {
            const isAtBottom = this.container.scrollHeight - this.container.scrollTop <= this.container.clientHeight + 10;
            this.autoScroll = isAtBottom;
        });
    }
    
    addLine(message, level = 'INFO') {
        if (!this.container) return;
        
        // إزالة رسالة "انتظار السجلات"
        if (this.lines.length === 0 && this.container.textContent.includes('انتظار السجلات')) {
            this.container.textContent = '';
        }
        
        // تنسيق الوقت
        const timestamp = new Date().toLocaleTimeString();
        
        // تحديد اللون حسب المستوى
        const colors = {
            DEBUG: '#6C6C8A',
            INFO: '#4CAF50',
            WARNING: '#FFC107',
            ERROR: '#F44336',
            CRITICAL: '#FF1744'
        };
        
        const color = colors[level] || colors.INFO;
        
        // إنشاء السطر
        const line = document.createElement('div');
        line.style.cssText = `
            padding: 1px 0;
            display: flex;
            gap: 8px;
            font-size: 12px;
        `;
        
        const timeSpan = document.createElement('span');
        timeSpan.textContent = `[${timestamp}]`;
        timeSpan.style.color = '#6C6C8A';
        
        const levelSpan = document.createElement('span');
        levelSpan.textContent = level;
        levelSpan.style.color = color;
        levelSpan.style.fontWeight = 'bold';
        
        const msgSpan = document.createElement('span');
        msgSpan.textContent = message;
        msgSpan.style.color = '#E8E8F0';
        
        line.appendChild(timeSpan);
        line.appendChild(levelSpan);
        line.appendChild(msgSpan);
        
        this.container.appendChild(line);
        this.lines.push(line);
        
        // التحقق من الحد الأقصى
        if (this.lines.length > this.maxLines) {
            const removed = this.lines.shift();
            if (removed && removed.parentNode) {
                removed.parentNode.removeChild(removed);
            }
        }
        
        // التمرير التلقائي
        if (this.autoScroll) {
            this.container.scrollTop = this.container.scrollHeight;
        }
    }
    
    clear() {
        if (this.container) {
            this.container.textContent = '';
            this.lines = [];
        }
    }
    
    setAutoScroll(enabled) {
        this.autoScroll = enabled;
    }
}


// ============================================================
// إدارة الرسوم البيانية (Chart Manager)
// ============================================================

class ChartManager {
    constructor() {
        this.charts = {};
    }
    
    createChart(elementId, config) {
        const element = document.getElementById(elementId);
        if (!element) return null;
        
        // استخدام Plotly إذا كان متاحاً
        if (typeof Plotly !== 'undefined') {
            const layout = {
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: { color: '#C8C8D4' },
                ...config.layout
            };
            
            const chart = {
                element: element,
                data: config.data || [],
                layout: layout,
                config: {
                    responsive: true,
                    displayModeBar: false,
                    ...config.config
                }
            };
            
            Plotly.newPlot(element, chart.data, chart.layout, chart.config);
            this.charts[elementId] = chart;
            return chart;
        }
        
        return null;
    }
    
    updateChart(elementId, data) {
        const chart = this.charts[elementId];
        if (!chart || typeof Plotly === 'undefined') return;
        
        Plotly.react(chart.element, data, chart.layout, chart.config);
    }
    
    updateLayout(elementId, layout) {
        const chart = this.charts[elementId];
        if (!chart || typeof Plotly === 'undefined') return;
        
        chart.layout = { ...chart.layout, ...layout };
        Plotly.react(chart.element, chart.data, chart.layout, chart.config);
    }
    
    destroy(elementId) {
        const chart = this.charts[elementId];
        if (!chart || typeof Plotly === 'undefined') return;
        
        Plotly.purge(chart.element);
        delete this.charts[elementId];
    }
}


// ============================================================
# إدارة API (API Client)
// ============================================================

class ApiClient {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl || window.location.origin;
        this.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        };
    }
    
    setAuthToken(token) {
        if (token) {
            this.headers['Authorization'] = `Bearer ${token}`;
        } else {
            delete this.headers['Authorization'];
        }
    }
    
    async request(endpoint, method = 'GET', data = null) {
        const url = `${this.baseUrl}${endpoint}`;
        const options = {
            method: method,
            headers: this.headers
        };
        
        if (data) {
            options.body = JSON.stringify(data);
        }
        
        try {
            const response = await fetch(url, options);
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.message || `HTTP ${response.status}`);
            }
            
            return result;
        } catch (error) {
            console.error('خطأ في طلب API:', error);
            throw error;
        }
    }
    
    // طرق GET
    async get(endpoint) {
        return this.request(endpoint, 'GET');
    }
    
    // طرق POST
    async post(endpoint, data) {
        return this.request(endpoint, 'POST', data);
    }
    
    // طرق PUT
    async put(endpoint, data) {
        return this.request(endpoint, 'PUT', data);
    }
    
    // طرق DELETE
    async delete(endpoint) {
        return this.request(endpoint, 'DELETE');
    }
    
    // طرق خاصة بالوكيل
    async executeTask(userInput, mode = 'full_interactive') {
        return this.post('/task/execute', { user_input: userInput, mode });
    }
    
    async getTaskStatus(taskId) {
        return this.get(`/task/${taskId}`);
    }
    
    async getStatus() {
        return this.get('/status');
    }
    
    async getCheckpoints() {
        return this.get('/checkpoints');
    }
    
    async createCheckpoint(description) {
        return this.post('/checkpoints', { description });
    }
    
    async undoCheckpoint() {
        return this.post('/checkpoints/undo');
    }
    
    async redoCheckpoint() {
        return this.post('/checkpoints/redo');
    }
    
    async getScreenshot() {
        return this.get('/screenshot');
    }
    
    async exportLogs() {
        return this.post('/export/logs');
    }
}


// ============================================================
# دوال مساعدة للواجهة (UI Helpers)
# ============================================================

const UIHelpers = {
    // تحميل مؤشر
    showLoading(elementId, message = 'جاري التحميل...') {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        element.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: center; gap: 12px; padding: 20px;">
                <div class="spinner"></div>
                <span>${message}</span>
            </div>
        `;
    },
    
    hideLoading(elementId) {
        const element = document.getElementById(elementId);
        if (!element) return;
        element.innerHTML = '';
    },
    
    // عرض رسالة خطأ
    showError(elementId, message) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        element.innerHTML = `
            <div style="background: #2D0A0A; border: 1px solid #F44336; border-radius: 8px; padding: 16px; color: #F44336;">
                <strong>❌ خطأ:</strong> ${message}
            </div>
        `;
    },
    
    // تنسيق الوقت
    formatTime(timestamp) {
        try {
            const date = new Date(timestamp);
            return date.toLocaleString('ar-SA', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        } catch {
            return timestamp || 'غير محدد';
        }
    },
    
    // تنسيق الحجم
    formatSize(bytes) {
        if (!bytes) return '0 B';
        
        const units = ['B', 'KB', 'MB', 'GB', 'TB'];
        let size = bytes;
        let unitIndex = 0;
        
        while (size >= 1024 && unitIndex < units.length - 1) {
            size /= 1024;
            unitIndex++;
        }
        
        return `${size.toFixed(1)} ${units[unitIndex]}`;
    },
    
    // تنسيق المدة
    formatDuration(seconds) {
        if (!seconds) return '0 ثانية';
        
        if (seconds < 60) {
            return `${Math.round(seconds)} ثانية`;
        } else if (seconds < 3600) {
            const minutes = Math.floor(seconds / 60);
            const secs = Math.round(seconds % 60);
            return `${minutes} دقيقة ${secs} ثانية`;
        } else {
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            return `${hours} ساعة ${minutes} دقيقة`;
        }
    },
    
    // الحصول على لون الحالة
    getStatusColor(status) {
        const colors = {
            'success': '#4CAF50',
            'completed': '#4CAF50',
            'running': '#6200EE',
            'in_progress': '#6200EE',
            'pending': '#FFC107',
            'warning': '#FFC107',
            'error': '#F44336',
            'failed': '#F44336',
            'active': '#4CAF50',
            'archived': '#6C6C8A',
            'deleted': '#F44336',
            'draft': '#FFC107'
        };
        return colors[status] || '#6C6C8A';
    },
    
    // الحصول على رمز الحالة
    getStatusIcon(status) {
        const icons = {
            'success': '✅',
            'completed': '✅',
            'running': '🔄',
            'in_progress': '⏳',
            'pending': '⏳',
            'warning': '⚠️',
            'error': '❌',
            'failed': '❌',
            'active': '✅',
            'archived': '📦',
            'deleted': '🗑️',
            'draft': '📝'
        };
        return icons[status] || '❓';
    }
};


// ============================================================
# تهيئة التطبيق (App Initialization)
# ============================================================

class LugyDashboardApp {
    constructor() {
        this.api = new ApiClient();
        this.notifications = new NotificationManager();
        this.logViewer = null;
        this.chartManager = new ChartManager();
        this.refreshTimer = null;
        this.isInitialized = false;
    }
    
    init() {
        if (this.isInitialized) return;
        
        console.log('🚀 تهيئة لوحة تحكم LugyFlutter...');
        
        // تهيئة عارض السجلات
        const logContainer = document.getElementById('lugy-logs');
        if (logContainer) {
            this.logViewer = new LogViewer('lugy-logs');
        }
        
        // بدء التحديث التلقائي
        if (LUGY_CONFIG.AUTO_REFRESH) {
            this._startAutoRefresh();
        }
        
        // إضافة الأنماط الديناميكية
        this._injectStyles();
        
        // تهيئة الأحداث
        this._initEvents();
        
        this.isInitialized = true;
        console.log('✅ تم تهيئة لوحة التحكم بنجاح');
        this.notifications.info('مرحباً بك في لوحة تحكم LugyFlutter');
    }
    
    _injectStyles() {
        const styles = document.createElement('style');
        styles.textContent = `
            @keyframes slideInRight {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            
            @keyframes slideOutRight {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
            }
            
            @keyframes spin {
                from { transform: rotate(0deg); }
                to { transform: rotate(360deg); }
            }
            
            .spinner {
                display: inline-block;
                width: 24px;
                height: 24px;
                border: 3px solid #2D2D44;
                border-top: 3px solid #6200EE;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }
            
            .lugy-card {
                background: #1E1E2E;
                border-radius: 10px;
                padding: 16px;
                border: 1px solid #2D2D44;
                transition: all 0.3s ease;
            }
            
            .lugy-card:hover {
                border-color: #6200EE;
                transform: translateY(-2px);
                box-shadow: 0 4px 20px rgba(98, 0, 238, 0.1);
            }
            
            .lugy-progress-bar {
                width: 100%;
                height: 6px;
                background: #2D2D44;
                border-radius: 3px;
                overflow: hidden;
            }
            
            .lugy-progress-bar .fill {
                height: 100%;
                background: linear-gradient(90deg, #6200EE, #BB86FC);
                border-radius: 3px;
                transition: width 0.5s ease;
            }
            
            ::-webkit-scrollbar {
                width: 8px;
                height: 8px;
            }
            
            ::-webkit-scrollbar-track {
                background: #1A1A2E;
                border-radius: 4px;
            }
            
            ::-webkit-scrollbar-thumb {
                background: #2D2D44;
                border-radius: 4px;
            }
            
            ::-webkit-scrollbar-thumb:hover {
                background: #6200EE;
            }
        `;
        document.head.appendChild(styles);
    }
    
    _initEvents() {
        // زر التحديث اليدوي
        const refreshBtn = document.getElementById('btn-refresh');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refresh();
                this.notifications.info('تم تحديث البيانات');
            });
        }
        
        // زر مسح السجلات
        const clearLogsBtn = document.getElementById('btn-clear-logs');
        if (clearLogsBtn && this.logViewer) {
            clearLogsBtn.addEventListener('click', () => {
                this.logViewer.clear();
                this.notifications.success('تم مسح السجلات');
            });
        }
        
        // زر تصدير السجلات
        const exportLogsBtn = document.getElementById('btn-export-logs');
        if (exportLogsBtn) {
            exportLogsBtn.addEventListener('click', async () => {
                try {
                    const result = await this.api.exportLogs();
                    this.notifications.success(`تم التصدير بنجاح: ${result.file_path}`);
                } catch (e) {
                    this.notifications.error(`فشل التصدير: ${e.message}`);
                }
            });
        }
    }
    
    _startAutoRefresh() {
        this.refreshTimer = setInterval(() => {
            this.refresh();
        }, LUGY_CONFIG.REFRESH_INTERVAL);
    }
    
    async refresh() {
        try {
            const status = await this.api.getStatus();
            LugyState.set('status', status);
            
            // تحديث المقاييس
            this._updateMetrics(status);
            
            // تحديث نقاط التفتيش
            if (status.checkpoints) {
                this._updateCheckpoints(status.checkpoints);
            }
            
            // إضافة سجل
            if (this.logViewer) {
                this.logViewer.addLine('تم تحديث البيانات', 'INFO');
            }
            
        } catch (error) {
            console.error('فشل تحديث البيانات:', error);
            if (this.logViewer) {
                this.logViewer.addLine(`فشل التحديث: ${error.message}`, 'ERROR');
            }
        }
    }
    
    _updateMetrics(status) {
        // تحديث المقاييس في الواجهة
        const metrics = {
            'metric-tasks': status.stats?.tasks_executed || 0,
            'metric-success': status.stats?.successful_tasks || 0,
            'metric-failed': status.stats?.failed_tasks || 0,
            'metric-checkpoints': status.checkpoints || 0,
            'metric-projects': status.projects || 0
        };
        
        Object.entries(metrics).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });
    }
    
    _updateCheckpoints(count) {
        const element = document.getElementById('checkpoint-count');
        if (element) {
            element.textContent = count;
        }
    }
    
    destroy() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
        }
        this.isInitialized = false;
        console.log('🛑 تم إيقاف لوحة التحكم');
    }
}


// ============================================================
# تهيئة التطبيق عند تحميل الصفحة
# ============================================================

let app = null;

document.addEventListener('DOMContentLoaded', () => {
    app = new LugyDashboardApp();
    app.init();
});

// إيقاف التطبيق عند إغلاق الصفحة
window.addEventListener('beforeunload', () => {
    if (app) {
        app.destroy();
        app = null;
    }
});


// ============================================================
# تصدير للاستخدام في وحدات أخرى
# ============================================================

if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        LugyState,
        NotificationManager,
        LogViewer,
        ChartManager,
        ApiClient,
        UIHelpers,
        LugyDashboardApp
    };
}


// ============================================================
# دوال إضافية للاستخدام مع Streamlit
# ============================================================

// تسجيل الدوال في النافذة العامة للاستخدام من Streamlit
window.Lugy = {
    // تهيئة
    init: () => {
        if (!app) {
            app = new LugyDashboardApp();
            app.init();
        }
        return app;
    },
    
    // إشعارات
    notify: (message, type) => {
        if (!app) {
            app = new LugyDashboardApp();
            app.init();
        }
        app.notifications.show(message, type);
    },
    
    // تسجيل
    log: (message, level) => {
        if (!app || !app.logViewer) return;
        app.logViewer.addLine(message, level || 'INFO');
    },
    
    // تحديث
    refresh: () => {
        if (app) {
            app.refresh();
        }
    },
    
    // API
    api: new ApiClient(),
    
    // حالة
    state: LugyState
};

console.log('📦 LugyFlutter Dashboard JS تم تحميله بنجاح');