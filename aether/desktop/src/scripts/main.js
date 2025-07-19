// Main JavaScript for Aether Desktop Application

class AetherApp {
    constructor() {
        this.currentPage = 'dashboard';
        this.init();
    }

    async init() {
        console.log('Initializing Aether Desktop App');
        
        // Initialize components
        this.initNavigation();
        this.initQuickCapture();
        this.initSettings();
        this.initEventListeners();
        
        // Load initial data
        await this.loadDashboard();
        
        console.log('Aether Desktop App initialized');
    }

    initNavigation() {
        const navItems = document.querySelectorAll('.nav-item');
        
        navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const page = item.dataset.page;
                this.navigateToPage(page);
            });
        });

        // Listen for navigation events from Rust backend
        if (window.__TAURI__) {
            window.__TAURI__.event.listen('navigate', (event) => {
                console.log('Navigation event received:', event.payload);
                this.navigateToPage(event.payload);
            });
        }
    }

    navigateToPage(page) {
        console.log('Navigating to page:', page);
        
        // Update active nav item
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        
        const activeNavItem = document.querySelector(`[data-page="${page}"]`);
        if (activeNavItem) {
            activeNavItem.classList.add('active');
        }
        
        // Show/hide pages
        document.querySelectorAll('.page').forEach(pageEl => {
            pageEl.classList.remove('active');
        });
        
        const targetPage = document.getElementById(`${page}-page`);
        if (targetPage) {
            targetPage.classList.add('active');
            this.currentPage = page;
            
            // Load page-specific data
            this.loadPageData(page);
        }
    }

    async loadPageData(page) {
        switch (page) {
            case 'dashboard':
                await this.loadDashboard();
                break;
            case 'ideas':
                await this.loadIdeas();
                break;
            case 'tasks':
                await this.loadTasks();
                break;
            case 'conversations':
                await this.loadConversations();
                break;
            case 'integrations':
                await this.loadIntegrations();
                break;
            case 'settings':
                await this.loadSettings();
                break;
        }
    }

    async loadDashboard() {
        console.log('Loading dashboard data');
        
        try {
            // Initialize advanced dashboard if on dashboard page
            if (this.currentPage === 'dashboard') {
                if (!this.dashboardManager) {
                    this.dashboardManager = new DashboardManager();
                }
            }
            
            // Get dashboard data from backend
            const data = await this.invokeCommand('get_dashboard_data');
            console.log('Dashboard data received:', data);
            
            // Update legacy stats cards (for compatibility)
            this.updateStatsCards(data);
            
            // Update recent activity
            this.updateRecentActivity(data.recent_activity || []);
            
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
            this.showError('Failed to load dashboard data');
        }
    }

    updateStatsCards(data) {
        // Update task stats
        const tasksTotal = document.getElementById('tasks-total');
        if (tasksTotal && data.tasks) {
            tasksTotal.textContent = data.tasks.total || 0;
        }
        
        // Update ideas stats
        const ideasTotal = document.getElementById('ideas-total');
        if (ideasTotal && data.ideas) {
            ideasTotal.textContent = data.ideas.total || 0;
        }
        
        // Update notifications stats
        const notificationsUnread = document.getElementById('notifications-unread');
        if (notificationsUnread && data.notifications) {
            notificationsUnread.textContent = data.notifications.unread || 0;
        }
        
        // Update integrations stats
        const integrationsActive = document.getElementById('integrations-active');
        if (integrationsActive && data.integrations) {
            const activeCount = Object.values(data.integrations).filter(
                integration => integration.status === 'connected'
            ).length;
            integrationsActive.textContent = activeCount;
        }
    }

    updateRecentActivity(activities) {
        const activityList = document.getElementById('recent-activity');
        if (!activityList) return;
        
        if (activities.length === 0) {
            activityList.innerHTML = '<div class="no-activity">No recent activity</div>';
            return;
        }
        
        const activityHTML = activities.map(activity => `
            <div class="activity-item">
                <div class="activity-icon">${this.getActivityIcon(activity.type)}</div>
                <div class="activity-content">
                    <div class="activity-title">${activity.title}</div>
                    <div class="activity-time">${this.formatTime(activity.timestamp)}</div>
                </div>
            </div>
        `).join('');
        
        activityList.innerHTML = activityHTML;
    }

    getActivityIcon(type) {
        const icons = {
            'task_completed': '✅',
            'idea_captured': '💡',
            'reminder_sent': '🔔',
            'meeting_scheduled': '📅',
            'integration_connected': '🔗'
        };
        return icons[type] || '📝';
    }

    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);
        
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        
        return date.toLocaleDateString();
    }

    initQuickCapture() {
        const quickCaptureBtn = document.getElementById('quick-capture-btn');
        const captureIdeaBtn = document.getElementById('capture-idea-btn');
        const modal = document.getElementById('quick-capture-modal');
        const closeBtn = modal?.querySelector('.modal-close');
        const cancelBtn = document.getElementById('cancel-idea-btn');
        const saveBtn = document.getElementById('save-idea-btn');
        const ideaInput = document.getElementById('idea-input');
        
        // Show modal
        const showModal = () => {
            if (modal) {
                modal.classList.add('active');
                if (ideaInput) {
                    ideaInput.focus();
                }
            }
        };
        
        // Hide modal
        const hideModal = () => {
            if (modal) {
                modal.classList.remove('active');
                if (ideaInput) {
                    ideaInput.value = '';
                }
            }
        };
        
        // Event listeners
        quickCaptureBtn?.addEventListener('click', showModal);
        captureIdeaBtn?.addEventListener('click', showModal);
        closeBtn?.addEventListener('click', hideModal);
        cancelBtn?.addEventListener('click', hideModal);
        
        // Save idea
        saveBtn?.addEventListener('click', async () => {
            const idea = ideaInput?.value.trim();
            if (idea) {
                await this.captureIdea(idea);
                hideModal();
            }
        });
        
        // Close modal on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modal?.classList.contains('active')) {
                hideModal();
            }
        });
        
        // Save on Ctrl+Enter
        ideaInput?.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                saveBtn?.click();
            }
        });
    }

    async captureIdea(idea) {
        console.log('Capturing idea:', idea);
        
        try {
            const result = await this.invokeCommand('capture_idea', { idea });
            console.log('Idea captured:', result);
            
            this.showSuccess('Idea captured successfully!');
            
            // Refresh dashboard if we're on it
            if (this.currentPage === 'dashboard') {
                await this.loadDashboard();
            }
            
        } catch (error) {
            console.error('Failed to capture idea:', error);
            this.showError('Failed to capture idea');
        }
    }

    initSettings() {
        // Auto-start checkbox
        const autostartCheckbox = document.getElementById('autostart-checkbox');
        
        if (autostartCheckbox) {
            // Load current autostart status
            this.loadAutostartStatus();
            
            // Handle checkbox change
            autostartCheckbox.addEventListener('change', async (e) => {
                try {
                    const enabled = e.target.checked;
                    await this.invokeCommand('toggle_autostart', { enable: enabled });
                    console.log('Autostart toggled:', enabled);
                } catch (error) {
                    console.error('Failed to toggle autostart:', error);
                    // Revert checkbox state
                    e.target.checked = !e.target.checked;
                    this.showError('Failed to update autostart setting');
                }
            });
        }
    }

    async loadAutostartStatus() {
        try {
            const enabled = await this.invokeCommand('is_autostart_enabled');
            const checkbox = document.getElementById('autostart-checkbox');
            if (checkbox) {
                checkbox.checked = enabled;
            }
        } catch (error) {
            console.error('Failed to load autostart status:', error);
        }
    }

    initEventListeners() {
        // Refresh button
        const refreshBtn = document.getElementById('refresh-btn');
        refreshBtn?.addEventListener('click', () => {
            this.loadPageData(this.currentPage);
        });
        
        // Quick action buttons
        const createTaskBtn = document.getElementById('create-task-btn');
        createTaskBtn?.addEventListener('click', () => {
            this.navigateToPage('tasks');
        });
        
        const startConversationBtn = document.getElementById('start-conversation-btn');
        startConversationBtn?.addEventListener('click', () => {
            this.navigateToPage('conversations');
        });
    }

    async loadIdeas() {
        console.log('Loading ideas...');
        // TODO: Implement ideas loading
    }

    async loadTasks() {
        console.log('Loading tasks...');
        // TODO: Implement tasks loading
    }

    async loadConversations() {
        console.log('Loading conversations...');
        // TODO: Implement conversations loading
    }

    async loadIntegrations() {
        console.log('Loading integrations...');
        // TODO: Implement integrations loading
    }

    async loadSettings() {
        console.log('Loading settings...');
        await this.loadAutostartStatus();
    }

    async invokeCommand(command, args = {}) {
        if (window.__TAURI__) {
            return await window.__TAURI__.invoke(command, args);
        } else {
            console.warn('Tauri not available, using mock data');
            return this.getMockResponse(command, args);
        }
    }

    getMockResponse(command, args) {
        // Mock responses for development
        switch (command) {
            case 'get_dashboard_data':
                return {
                    tasks: { total: 12, completed: 8, overdue: 2, due_today: 3 },
                    ideas: { total: 25, processed: 18, recent: 7 },
                    notifications: { unread: 4, total: 15 },
                    integrations: {
                        monday_com: { status: 'connected', items: 8 },
                        google_calendar: { status: 'disconnected', events: 0 }
                    },
                    recent_activity: [
                        {
                            type: 'task_completed',
                            title: 'Review project proposal',
                            timestamp: new Date(Date.now() - 30 * 60 * 1000).toISOString()
                        },
                        {
                            type: 'idea_captured',
                            title: 'New feature idea for mobile app',
                            timestamp: new Date(Date.now() - 75 * 60 * 1000).toISOString()
                        },
                        {
                            type: 'reminder_sent',
                            title: 'Meeting with client in 15 minutes',
                            timestamp: new Date(Date.now() - 105 * 60 * 1000).toISOString()
                        }
                    ]
                };
            case 'capture_idea':
                return 'Idea captured successfully (mock)';
            case 'is_autostart_enabled':
                return false;
            case 'toggle_autostart':
                return args.enable;
            default:
                return null;
        }
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            notification.remove();
        }, 3000);
        
        console.log(`${type.toUpperCase()}: ${message}`);
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.aetherApp = new AetherApp();
});

// Handle window focus/blur for better UX
window.addEventListener('focus', () => {
    console.log('Window focused');
    // Refresh current page data when window gains focus
    if (window.aetherApp) {
        window.aetherApp.loadPageData(window.aetherApp.currentPage);
    }
});

window.addEventListener('blur', () => {
    console.log('Window blurred');
});