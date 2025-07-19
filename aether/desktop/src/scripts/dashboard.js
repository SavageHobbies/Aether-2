// Advanced Dashboard Interface for Aether Desktop Application

class DashboardManager {
    constructor() {
        this.widgets = new Map();
        this.widgetOrder = [];
        this.isDragging = false;
        this.draggedWidget = null;
        this.customizationMode = false;
        this.realTimeUpdates = true;
        this.updateInterval = null;
        
        this.init();
    }

    async init() {
        console.log('Initializing Advanced Dashboard');
        
        this.setupEventListeners();
        this.loadWidgetConfiguration();
        await this.initializeWidgets();
        this.startRealTimeUpdates();
        
        console.log('Advanced Dashboard initialized');
    }

    setupEventListeners() {
        // Customization toggle
        const customizeBtn = document.getElementById('customize-dashboard-btn');
        if (customizeBtn) {
            customizeBtn.addEventListener('click', () => this.toggleCustomization());
        }

        // Refresh dashboard
        const refreshBtn = document.getElementById('refresh-dashboard-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshAllWidgets());
        }

        // Real-time toggle
        const realtimeToggle = document.getElementById('realtime-toggle');
        if (realtimeToggle) {
            realtimeToggle.addEventListener('change', (e) => {
                this.toggleRealTimeUpdates(e.target.checked);
            });
        }
    }

    async initializeWidgets() {
        const widgetConfigs = [
            { id: 'stats-overview', type: 'stats', title: 'Overview', icon: '📊' },
            { id: 'recent-tasks', type: 'list', title: 'Recent Tasks', icon: '✅' },
            { id: 'ideas-stream', type: 'list', title: 'Ideas Stream', icon: '💡' },
            { id: 'notifications', type: 'list', title: 'Notifications', icon: '🔔' },
            { id: 'quick-actions', type: 'actions', title: 'Quick Actions', icon: '⚡' },
            { id: 'activity-feed', type: 'list', title: 'Recent Activity', icon: '📈' }
        ];

        for (const config of widgetConfigs) {
            await this.createWidget(config);
        }
    } 
   async createWidget(config) {
        const widget = new DashboardWidget(config);
        this.widgets.set(config.id, widget);
        this.widgetOrder.push(config.id);
        
        await widget.render();
        this.setupWidgetDragAndDrop(widget);
        
        return widget;
    }

    setupWidgetDragAndDrop(widget) {
        const element = widget.element;
        const dragHandle = element.querySelector('.drag-handle');
        
        if (!dragHandle) return;

        dragHandle.addEventListener('mousedown', (e) => {
            if (!this.customizationMode) return;
            
            this.startDrag(widget, e);
        });

        element.addEventListener('dragover', (e) => {
            if (this.isDragging && this.draggedWidget !== widget) {
                e.preventDefault();
                element.classList.add('drop-target');
            }
        });

        element.addEventListener('dragleave', () => {
            element.classList.remove('drop-target');
        });

        element.addEventListener('drop', (e) => {
            if (this.isDragging && this.draggedWidget !== widget) {
                e.preventDefault();
                this.handleDrop(widget);
            }
        });
    }

    startDrag(widget, event) {
        this.isDragging = true;
        this.draggedWidget = widget;
        
        widget.element.classList.add('dragging');
        document.body.style.cursor = 'grabbing';
        
        const moveHandler = (e) => this.handleDragMove(e);
        const upHandler = () => this.endDrag(moveHandler, upHandler);
        
        document.addEventListener('mousemove', moveHandler);
        document.addEventListener('mouseup', upHandler);
    }

    handleDragMove(event) {
        if (!this.isDragging) return;
        
        // Visual feedback during drag
        const element = this.draggedWidget.element;
        element.style.transform = `translate(${event.clientX - element.offsetLeft}px, ${event.clientY - element.offsetTop}px) rotate(5deg)`;
    }

    endDrag(moveHandler, upHandler) {
        if (!this.isDragging) return;
        
        this.isDragging = false;
        document.body.style.cursor = '';
        
        if (this.draggedWidget) {
            this.draggedWidget.element.classList.remove('dragging');
            this.draggedWidget.element.style.transform = '';
        }
        
        document.removeEventListener('mousemove', moveHandler);
        document.removeEventListener('mouseup', upHandler);
        
        // Clear drop targets
        document.querySelectorAll('.drop-target').forEach(el => {
            el.classList.remove('drop-target');
        });
        
        this.draggedWidget = null;
    }    ha
ndleDrop(targetWidget) {
        if (!this.draggedWidget || !targetWidget) return;
        
        const draggedId = this.draggedWidget.config.id;
        const targetId = targetWidget.config.id;
        
        // Swap positions in the order array
        const draggedIndex = this.widgetOrder.indexOf(draggedId);
        const targetIndex = this.widgetOrder.indexOf(targetId);
        
        this.widgetOrder[draggedIndex] = targetId;
        this.widgetOrder[targetIndex] = draggedId;
        
        // Re-render dashboard with new order
        this.renderDashboard();
        this.saveWidgetConfiguration();
        
        console.log(`Moved widget ${draggedId} to position of ${targetId}`);
    }

    toggleCustomization() {
        this.customizationMode = !this.customizationMode;
        
        const dashboardGrid = document.querySelector('.dashboard-grid');
        const customizeBtn = document.getElementById('customize-dashboard-btn');
        
        if (this.customizationMode) {
            dashboardGrid?.classList.add('customizing');
            customizeBtn?.classList.add('active');
            this.showCustomizationPanel();
        } else {
            dashboardGrid?.classList.remove('customizing');
            customizeBtn?.classList.remove('active');
            this.hideCustomizationPanel();
        }
    }

    showCustomizationPanel() {
        const panel = document.getElementById('customization-panel');
        if (panel) {
            panel.classList.add('open');
        }
    }

    hideCustomizationPanel() {
        const panel = document.getElementById('customization-panel');
        if (panel) {
            panel.classList.remove('open');
        }
    }

    async refreshAllWidgets() {
        console.log('Refreshing all dashboard widgets');
        
        const refreshPromises = Array.from(this.widgets.values()).map(widget => 
            widget.refresh().catch(error => {
                console.error(`Failed to refresh widget ${widget.config.id}:`, error);
            })
        );
        
        await Promise.all(refreshPromises);
        console.log('All widgets refreshed');
    }

    startRealTimeUpdates() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        
        if (this.realTimeUpdates) {
            this.updateInterval = setInterval(() => {
                this.refreshAllWidgets();
            }, 30000); // Update every 30 seconds
        }
    }

    toggleRealTimeUpdates(enabled) {
        this.realTimeUpdates = enabled;
        
        if (enabled) {
            this.startRealTimeUpdates();
        } else {
            if (this.updateInterval) {
                clearInterval(this.updateInterval);
                this.updateInterval = null;
            }
        }
        
        // Update UI indicators
        document.querySelectorAll('.real-time-indicator').forEach(indicator => {
            indicator.classList.toggle('offline', !enabled);
        });
    }    
renderDashboard() {
        const container = document.querySelector('.dashboard-grid');
        if (!container) return;
        
        // Clear existing widgets
        container.innerHTML = '';
        
        // Render widgets in order
        for (const widgetId of this.widgetOrder) {
            const widget = this.widgets.get(widgetId);
            if (widget && widget.element) {
                container.appendChild(widget.element);
            }
        }
    }

    loadWidgetConfiguration() {
        try {
            const saved = localStorage.getItem('aether-dashboard-config');
            if (saved) {
                const config = JSON.parse(saved);
                this.widgetOrder = config.widgetOrder || this.widgetOrder;
                this.realTimeUpdates = config.realTimeUpdates !== false;
            }
        } catch (error) {
            console.error('Failed to load dashboard configuration:', error);
        }
    }

    saveWidgetConfiguration() {
        try {
            const config = {
                widgetOrder: this.widgetOrder,
                realTimeUpdates: this.realTimeUpdates,
                lastSaved: new Date().toISOString()
            };
            localStorage.setItem('aether-dashboard-config', JSON.stringify(config));
        } catch (error) {
            console.error('Failed to save dashboard configuration:', error);
        }
    }
}

// Individual Widget Class
class DashboardWidget {
    constructor(config) {
        this.config = config;
        this.element = null;
        this.data = null;
        this.isLoading = false;
    }

    async render() {
        this.element = this.createElement();
        await this.loadData();
        this.updateContent();
        return this.element;
    }

    createElement() {
        const widget = document.createElement('div');
        widget.className = 'dashboard-widget';
        widget.setAttribute('data-widget-id', this.config.id);
        
        widget.innerHTML = `
            <div class="widget-header">
                <h3 class="widget-title">
                    <span class="widget-icon">${this.config.icon}</span>
                    ${this.config.title}
                </h3>
                <div class="widget-actions">
                    <button class="widget-action-btn drag-handle" title="Drag to reorder">
                        <span>⋮⋮</span>
                    </button>
                    <button class="widget-action-btn refresh-btn" title="Refresh">
                        <span>🔄</span>
                    </button>
                </div>
                <div class="real-time-indicator" title="Real-time updates"></div>
            </div>
            <div class="widget-content">
                <div class="loading">Loading...</div>
            </div>
        `;
        
        // Setup refresh button
        const refreshBtn = widget.querySelector('.refresh-btn');
        refreshBtn?.addEventListener('click', () => this.refresh());
        
        return widget;
    }    asyn
c loadData() {
        this.isLoading = true;
        this.showLoading();
        
        try {
            switch (this.config.type) {
                case 'stats':
                    this.data = await this.loadStatsData();
                    break;
                case 'list':
                    this.data = await this.loadListData();
                    break;
                case 'actions':
                    this.data = await this.loadActionsData();
                    break;
                default:
                    this.data = { error: 'Unknown widget type' };
            }
        } catch (error) {
            console.error(`Failed to load data for widget ${this.config.id}:`, error);
            this.data = { error: error.message };
        } finally {
            this.isLoading = false;
        }
    }

    async loadStatsData() {
        // Load dashboard statistics
        if (window.aetherApp) {
            return await window.aetherApp.invokeCommand('get_dashboard_data');
        }
        
        // Mock data for development
        return {
            tasks: { total: 12, completed: 8, overdue: 2, due_today: 3 },
            ideas: { total: 25, processed: 18, recent: 7 },
            notifications: { unread: 4, total: 15 },
            integrations: { active: 2, total: 3 }
        };
    }

    async loadListData() {
        const endpoint = this.getListEndpoint();
        
        if (window.aetherApp) {
            return await window.aetherApp.invokeCommand(endpoint);
        }
        
        // Mock data based on widget type
        return this.getMockListData();
    }

    async loadActionsData() {
        return {
            actions: [
                { id: 'capture-idea', label: 'Capture Idea', icon: '💡', action: 'quick-capture' },
                { id: 'create-task', label: 'Create Task', icon: '✅', action: 'create-task' },
                { id: 'start-chat', label: 'Start Chat', icon: '💬', action: 'new-conversation' },
                { id: 'search-memory', label: 'Search Memory', icon: '🧠', action: 'search-memory' }
            ]
        };
    }

    getListEndpoint() {
        const endpoints = {
            'recent-tasks': 'get_recent_tasks',
            'ideas-stream': 'get_recent_ideas',
            'notifications': 'get_notifications',
            'activity-feed': 'get_recent_activity'
        };
        return endpoints[this.config.id] || 'get_dashboard_data';
    }

    getMockListData() {
        const mockData = {
            'recent-tasks': {
                items: [
                    { id: 1, title: 'Review project proposal', status: 'in-progress', priority: 'high', due: '2 hours' },
                    { id: 2, title: 'Update documentation', status: 'pending', priority: 'medium', due: '1 day' },
                    { id: 3, title: 'Team meeting prep', status: 'completed', priority: 'low', due: 'completed' }
                ]
            },
            'ideas-stream': {
                items: [
                    { id: 1, content: 'Mobile app feature for voice notes', timestamp: '5 min ago', tags: ['mobile', 'voice'] },
                    { id: 2, content: 'Integration with Slack for notifications', timestamp: '15 min ago', tags: ['integration'] },
                    { id: 3, content: 'AI-powered task prioritization', timestamp: '1 hour ago', tags: ['ai', 'tasks'] }
                ]
            },
            'notifications': {
                items: [
                    { id: 1, title: 'Meeting reminder', message: 'Client call in 15 minutes', type: 'reminder', time: '2 min ago' },
                    { id: 2, title: 'Task overdue', message: 'Project proposal is overdue', type: 'warning', time: '1 hour ago' },
                    { id: 3, title: 'Idea processed', message: 'Your idea has been converted to a task', type: 'success', time: '2 hours ago' }
                ]
            },
            'activity-feed': {
                items: [
                    { id: 1, action: 'Task completed', details: 'Review project proposal', timestamp: '30 min ago', icon: '✅' },
                    { id: 2, action: 'Idea captured', details: 'Mobile app feature for voice notes', timestamp: '45 min ago', icon: '💡' },
                    { id: 3, action: 'Meeting scheduled', details: 'Client presentation meeting', timestamp: '1 hour ago', icon: '📅' }
                ]
            }
        };
        
        return mockData[this.config.id] || { items: [] };
    }   
 updateContent() {
        const content = this.element.querySelector('.widget-content');
        if (!content) return;
        
        if (this.data?.error) {
            content.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">⚠️</div>
                    <div class="empty-state-title">Error Loading Data</div>
                    <div class="empty-state-description">${this.data.error}</div>
                </div>
            `;
            this.element.classList.add('widget-error');
            return;
        }
        
        switch (this.config.type) {
            case 'stats':
                this.renderStatsContent(content);
                break;
            case 'list':
                this.renderListContent(content);
                break;
            case 'actions':
                this.renderActionsContent(content);
                break;
        }
        
        this.element.classList.remove('widget-error');
    }

    renderStatsContent(container) {
        const stats = this.data;
        
        container.innerHTML = `
            <div class="stats-grid">
                <div class="stat-item">
                    <span class="stat-number">${stats.tasks?.total || 0}</span>
                    <span class="stat-label">Tasks</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">${stats.ideas?.total || 0}</span>
                    <span class="stat-label">Ideas</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">${stats.notifications?.unread || 0}</span>
                    <span class="stat-label">Alerts</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">${stats.integrations?.active || 0}</span>
                    <span class="stat-label">Connected</span>
                </div>
            </div>
        `;
        
        this.element.classList.add('stats-widget');
    }

    renderListContent(container) {
        const items = this.data?.items || [];
        
        if (items.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">${this.config.icon}</div>
                    <div class="empty-state-title">No ${this.config.title}</div>
                    <div class="empty-state-description">Nothing to show right now</div>
                </div>
            `;
            return;
        }
        
        const listHTML = items.map(item => this.renderListItem(item)).join('');
        
        container.innerHTML = `
            <div class="widget-list">
                ${listHTML}
            </div>
        `;
    }

    renderListItem(item) {
        switch (this.config.id) {
            case 'recent-tasks':
                return `
                    <div class="widget-list-item">
                        <div class="list-item-icon">${this.getTaskIcon(item.status)}</div>
                        <div class="list-item-content">
                            <div class="list-item-title">${item.title}</div>
                            <div class="list-item-subtitle">Priority: ${item.priority}</div>
                        </div>
                        <div class="list-item-meta">${item.due}</div>
                    </div>
                `;
            case 'ideas-stream':
                return `
                    <div class="widget-list-item">
                        <div class="list-item-icon">💡</div>
                        <div class="list-item-content">
                            <div class="list-item-title">${item.content}</div>
                            <div class="list-item-subtitle">${item.tags?.join(', ') || ''}</div>
                        </div>
                        <div class="list-item-meta">${item.timestamp}</div>
                    </div>
                `;
            case 'notifications':
                return `
                    <div class="widget-list-item">
                        <div class="list-item-icon">${this.getNotificationIcon(item.type)}</div>
                        <div class="list-item-content">
                            <div class="list-item-title">${item.title}</div>
                            <div class="list-item-subtitle">${item.message}</div>
                        </div>
                        <div class="list-item-meta">${item.time}</div>
                    </div>
                `;
            case 'activity-feed':
                return `
                    <div class="widget-list-item">
                        <div class="list-item-icon">${item.icon}</div>
                        <div class="list-item-content">
                            <div class="list-item-title">${item.action}</div>
                            <div class="list-item-subtitle">${item.details}</div>
                        </div>
                        <div class="list-item-meta">${item.timestamp}</div>
                    </div>
                `;
            default:
                return `
                    <div class="widget-list-item">
                        <div class="list-item-content">
                            <div class="list-item-title">${item.title || item.name || 'Unknown Item'}</div>
                        </div>
                    </div>
                `;
        }
    }    rend
erActionsContent(container) {
        const actions = this.data?.actions || [];
        
        const actionsHTML = actions.map(action => `
            <button class="quick-action-btn" data-action="${action.action}">
                <div class="quick-action-icon">${action.icon}</div>
                <div class="quick-action-label">${action.label}</div>
            </button>
        `).join('');
        
        container.innerHTML = `
            <div class="quick-actions-grid">
                ${actionsHTML}
            </div>
        `;
        
        // Setup action handlers
        container.querySelectorAll('.quick-action-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const action = btn.dataset.action;
                this.handleQuickAction(action);
            });
        });
    }

    handleQuickAction(action) {
        console.log(`Quick action triggered: ${action}`);
        
        switch (action) {
            case 'quick-capture':
                document.getElementById('quick-capture-btn')?.click();
                break;
            case 'create-task':
                if (window.aetherApp) {
                    window.aetherApp.navigateToPage('tasks');
                }
                break;
            case 'new-conversation':
                if (window.aetherApp) {
                    window.aetherApp.navigateToPage('conversations');
                }
                break;
            case 'search-memory':
                if (window.aetherApp) {
                    window.aetherApp.navigateToPage('memory');
                }
                break;
        }
    }

    getTaskIcon(status) {
        const icons = {
            'completed': '✅',
            'in-progress': '🔄',
            'pending': '⏳',
            'overdue': '🚨'
        };
        return icons[status] || '📋';
    }

    getNotificationIcon(type) {
        const icons = {
            'reminder': '⏰',
            'warning': '⚠️',
            'success': '✅',
            'info': 'ℹ️',
            'error': '❌'
        };
        return icons[type] || '🔔';
    }

    showLoading() {
        const content = this.element?.querySelector('.widget-content');
        if (content) {
            content.innerHTML = `
                <div class="loading">
                    <div class="widget-skeleton">
                        <div class="skeleton-line short"></div>
                        <div class="skeleton-line medium"></div>
                        <div class="skeleton-line long"></div>
                    </div>
                </div>
            `;
        }
    }

    async refresh() {
        console.log(`Refreshing widget: ${this.config.id}`);
        await this.loadData();
        this.updateContent();
    }
}

// Export for use in main application
window.DashboardManager = DashboardManager;
window.DashboardWidget = DashboardWidget;