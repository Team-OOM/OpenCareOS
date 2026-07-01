// OpenCareOS - Main JavaScript
// Apache License 2.0

(function() {
    'use strict';

    // ===========================================
    // Global App State
    // ===========================================
    window.App = {
        user: null,
        csrfToken: null,
        config: {
            apiBase: '/api',
            refreshInterval: 30000,
        },
    };

    // ===========================================
    // Utility Functions
    // ===========================================
    const utils = {
        // Format date
        formatDate(dateString, options = {}) {
            const defaultOptions = {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                ...options,
            };
            return new Date(dateString).toLocaleDateString('en-US', defaultOptions);
        },

        formatDateTime(dateString) {
            return this.formatDate(dateString, {
                hour: '2-digit',
                minute: '2-digit',
            });
        },

        formatRelativeTime(dateString) {
            const date = new Date(dateString);
            const now = new Date();
            const diffMs = now - date;
            const diffMins = Math.floor(diffMs / 60000);
            const diffHours = Math.floor(diffMs / 3600000);
            const diffDays = Math.floor(diffMs / 86400000);

            if (diffMins < 1) return 'Just now';
            if (diffMins < 60) return `${diffMins}m ago`;
            if (diffHours < 24) return `${diffHours}h ago`;
            if (diffDays < 7) return `${diffDays}d ago`;
            return this.formatDate(dateString);
        },

        // Debounce
        debounce(fn, delay) {
            let timeoutId;
            return (...args) => {
                clearTimeout(timeoutId);
                timeoutId = setTimeout(() => fn(...args), delay);
            };
        },

        // Throttle
        throttle(fn, limit) {
            let inThrottle;
            return (...args) => {
                if (!inThrottle) {
                    fn(...args);
                    inThrottle = true;
                    setTimeout(() => (inThrottle = false), limit);
                }
            };
        },

        // Generate ID
        generateId(prefix = 'id') {
            return `${prefix}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        },

        // Get initials from name
        getInitials(name) {
            return name
                .split(' ')
                .map(n => n[0])
                .join('')
                .toUpperCase()
                .slice(0, 2);
        },

        // Format file size
        formatFileSize(bytes) {
            if (bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
        },

        // Get file icon
        getFileIcon(mimeType) {
            if (mimeType.startsWith('image/')) return 'fas fa-image text-blue-500';
            if (mimeType === 'application/pdf') return 'fas fa-file-pdf text-red-500';
            if (mimeType === 'text/csv') return 'fas fa-file-csv text-green-500';
            if (mimeType.includes('wordprocessingml')) return 'fas fa-file-word text-blue-500';
            if (mimeType.includes('spreadsheetml')) return 'fas fa-file-excel text-green-500';
            return 'fas fa-file text-gray-500';
        },

        // Truncate text
        truncate(text, length = 50) {
            if (text.length <= length) return text;
            return text.slice(0, length).trim() + '...';
        },

        // Parse query string
        parseQueryString(queryString) {
            const params = new URLSearchParams(queryString);
            const result = {};
            for (const [key, value] of params) {
                result[key] = value;
            }
            return result;
        },

        // Build query string
        buildQueryString(params) {
            const searchParams = new URLSearchParams();
            Object.entries(params).forEach(([key, value]) => {
                if (value !== undefined && value !== null && value !== '') {
                    searchParams.append(key, value);
                }
            });
            return searchParams.toString();
        },
    };

    // ===========================================
    // API Client
    // ===========================================
    const api = {
        async request(endpoint, options = {}) {
            const url = `${App.config.apiBase}${endpoint}`;
            const config = {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers,
                },
                credentials: 'include',
                ...options,
            };

            if (config.body && typeof config.body === 'object') {
                config.body = JSON.stringify(config.body);
            }

            try {
                const response = await fetch(url, config);

                if (response.status === 401) {
                    // Token expired, try to refresh
                    const refreshed = await this.refreshToken();
                    if (refreshed) {
                        // Retry original request
                        return this.request(endpoint, options);
                    } else {
                        // Redirect to login
                        window.location.href = '/login';
                        return;
                    }
                }

                if (!response.ok) {
                    const error = await response.json().catch(() => ({
                        message: `HTTP ${response.status}`,
                    }));
                    throw new Error(error.message || `Request failed: ${response.status}`);
                }

                // Handle empty responses
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    return await response.json();
                }
                return await response.text();
            } catch (error) {
                console.error(`API Error (${endpoint}):`, error);
                throw error;
            }
        },

        get(endpoint, params = {}) {
            const queryString = utils.buildQueryString(params);
            const url = queryString ? `${endpoint}?${queryString}` : endpoint;
            return this.request(url, { method: 'GET' });
        },

        post(endpoint, data = {}) {
            return this.request(endpoint, {
                method: 'POST',
                body: data,
            });
        },

        patch(endpoint, data = {}) {
            return this.request(endpoint, {
                method: 'PATCH',
                body: data,
            });
        },

        put(endpoint, data = {}) {
            return this.request(endpoint, {
                method: 'PUT',
                body: data,
            });
        },

        delete(endpoint) {
            return this.request(endpoint, { method: 'DELETE' });
        },

        async refreshToken() {
            try {
                const response = await fetch(`${App.config.apiBase}/auth/refresh`, {
                    method: 'POST',
                    credentials: 'include',
                });
                return response.ok;
            } catch {
                return false;
            }
        },

        // Upload file
        async uploadFile(endpoint, file, additionalData = {}) {
            const formData = new FormData();
            formData.append('file', file);
            Object.entries(additionalData).forEach(([key, value]) => {
                formData.append(key, value);
            });

            return this.request(endpoint, {
                method: 'POST',
                headers: {}, // Let browser set Content-Type with boundary
                body: formData,
            });
        },
    };

    // ===========================================
    // Toast Notifications
    // ===========================================
    const toast = {
        container: null,

        init() {
            this.container = document.getElementById('toast-container');
            if (!this.container) {
                this.container = document.createElement('div');
                this.container.id = 'toast-container';
                this.container.className = 'fixed bottom-4 right-4 z-50 space-y-2';
                this.container.setAttribute('aria-live', 'polite');
                document.body.appendChild(this.container);
            }
        },

        show(message, type = 'info', duration = 5000) {
            if (!this.container) this.init();

            const icons = {
                success: 'fa-check-circle',
                error: 'fa-times-circle',
                warning: 'fa-exclamation-triangle',
                info: 'fa-info-circle',
            };
            const colors = {
                success: 'bg-green-500',
                error: 'bg-red-500',
                warning: 'bg-yellow-500',
                info: 'bg-blue-500',
            };

            const toast = document.createElement('div');
            toast.className = `flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg ${colors[type]} text-white transform transition-all duration-300 translate-x-full`;
            toast.innerHTML = `
                <i class="fas ${icons[type]}"></i>
                <span>${message}</span>
                <button onclick="this.parentElement.remove()" class="ml-4 text-white hover:text-gray-200" aria-label="Dismiss">
                    <i class="fas fa-times"></i>
                </button>
            `;

            this.container.appendChild(toast);

            // Animate in
            requestAnimationFrame(() => {
                toast.classList.remove('translate-x-full');
            });

            // Auto dismiss
            setTimeout(() => {
                toast.classList.add('translate-x-full');
                setTimeout(() => toast.remove(), 300);
            }, duration);
        },

        success(message, duration) {
            this.show(message, 'success', duration);
        },

        error(message, duration) {
            this.show(message, 'error', duration);
        },

        warning(message, duration) {
            this.show(message, 'warning', duration);
        },

        info(message, duration) {
            this.show(message, 'info', duration);
        },
    };

    // ===========================================
    // Modal Manager
    // ===========================================
    const modal = {
        container: null,

        init() {
            this.container = document.getElementById('modal-container');
            if (!this.container) {
                this.container = document.createElement('div');
                this.container.id = 'modal-container';
                this.container.className = 'fixed inset-0 z-50 hidden';
                this.container.setAttribute('aria-modal', 'true');
                this.container.setAttribute('role', 'dialog');
                document.body.appendChild(this.container);
            }
        },

        show(html, options = {}) {
            if (!this.container) this.init();

            this.container.innerHTML = `
                <div class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4" tabindex="-1">
                    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-lg w-full max-h-[90vh] overflow-hidden ${options.className || ''}">
                        ${html}
                    </div>
                </div>
            `;
            this.container.classList.remove('hidden');
            document.body.style.overflow = 'hidden';

            // Focus first focusable element
            const focusable = this.container.querySelector('button, input, select, textarea, a[href]');
            if (focusable) focusable.focus();

            // Close on backdrop click
            const backdrop = this.container.querySelector('.fixed.inset-0');
            backdrop.addEventListener('click', (e) => {
                if (e.target === backdrop) this.close();
            });

            // Close on Escape
            const handleEscape = (e) => {
                if (e.key === 'Escape') {
                    this.close();
                    document.removeEventListener('keydown', handleEscape);
                }
            };
            document.addEventListener('keydown', handleEscape);

            return {
                close: () => this.close(),
                container: this.container.querySelector('.bg-white'),
            };
        },

        close() {
            if (this.container) {
                this.container.classList.add('hidden');
                this.container.innerHTML = '';
                document.body.style.overflow = '';
            }
        },

        confirm(message, title = 'Confirm') {
            return new Promise((resolve) => {
                this.show(`
                    <div class="p-6">
                        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">${title}</h3>
                        <p class="text-gray-600 dark:text-gray-400 mb-6">${message}</p>
                        <div class="flex justify-end gap-3">
                            <button class="btn btn-secondary" onclick="App.modal.resolveConfirm(false)">Cancel</button>
                            <button class="btn btn-danger" onclick="App.modal.resolveConfirm(true)">Confirm</button>
                        </div>
                    </div>
                `);
                this.resolveConfirm = resolve;
            });
        },

        resolveConfirm: null,
    };

    // ===========================================
    // Loading State Manager
    // ===========================================
    const loading = {
        overlay: null,

        show(message = 'Loading...') {
            if (!this.overlay) {
                this.overlay = document.createElement('div');
                this.overlay.className = 'fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50';
                this.overlay.innerHTML = `
                    <div class="bg-white dark:bg-gray-800 rounded-xl p-6 flex flex-col items-center gap-4 shadow-xl">
                        <div class="spinner text-primary-600"></div>
                        <p class="text-gray-700 dark:text-gray-300" id="loading-message">${message}</p>
                    </div>
                `;
                document.body.appendChild(this.overlay);
                document.body.style.overflow = 'hidden';
            } else {
                this.overlay.querySelector('#loading-message').textContent = message;
                this.overlay.classList.remove('hidden');
            }
        },

        hide() {
            if (this.overlay) {
                this.overlay.classList.add('hidden');
            }
        },

        setMessage(message) {
            if (this.overlay) {
                this.overlay.querySelector('#loading-message').textContent = message;
            }
        },
    };

    // ===========================================
    // Form Helpers
    // ===========================================
    const forms = {
        // Serialize form to object
        serialize(form) {
            const formData = new FormData(form);
            const result = {};
            for (const [key, value] of formData) {
                if (result[key]) {
                    if (!Array.isArray(result[key])) {
                        result[key] = [result[key]];
                    }
                    result[key].push(value);
                } else {
                    result[key] = value;
                }
            }
            return result;
        },

        // Populate form from object
        populate(form, data) {
            Object.entries(data).forEach(([key, value]) => {
                const input = form.querySelector(`[name="${key}"]`);
                if (input) {
                    if (input.type === 'checkbox') {
                        input.checked = Boolean(value);
                    } else if (input.type === 'radio') {
                        const radio = form.querySelector(`[name="${key}"][value="${value}"]`);
                        if (radio) radio.checked = true;
                    } else {
                        input.value = value;
                    }
                }
            });
        },

        // Reset form
        reset(form) {
            form.reset();
            // Clear validation states
            form.querySelectorAll('.error, .valid').forEach(el => {
                el.classList.remove('error', 'valid');
            });
        },

        // Validate form
        validate(form) {
            let isValid = true;
            const requiredFields = form.querySelectorAll('[required]');

            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    field.classList.add('error');
                    field.classList.remove('valid');
                    isValid = false;
                } else {
                    field.classList.remove('error');
                    field.classList.add('valid');
                }
            });

            return isValid;
        },

        // Show field error
        showError(field, message) {
            field.classList.add('error');
            field.classList.remove('valid');
            let errorEl = field.parentNode.querySelector('.field-error');
            if (!errorEl) {
                errorEl = document.createElement('p');
                errorEl.className = 'field-error text-red-500 text-xs mt-1';
                field.parentNode.appendChild(errorEl);
            }
            errorEl.textContent = message;
        },

        // Clear field error
        clearError(field) {
            field.classList.remove('error');
            const errorEl = field.parentNode.querySelector('.field-error');
            if (errorEl) errorEl.remove();
        },
    };

    // ===========================================
    // Theme Manager
    // ===========================================
    const theme = {
        init() {
            const savedTheme = localStorage.getItem('theme') || 'light';
            this.apply(savedTheme);

            // Listen for system theme changes
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
                if (!localStorage.getItem('theme')) {
                    this.apply(e.matches ? 'dark' : 'light');
                }
            });
        },

        apply(themeName) {
            const html = document.documentElement;
            if (themeName === 'dark') {
                html.classList.add('dark');
                html.setAttribute('data-theme', 'dark');
            } else {
                html.classList.remove('dark');
                html.setAttribute('data-theme', 'light');
            }
            localStorage.setItem('theme', themeName);
        },

        toggle() {
            const current = localStorage.getItem('theme') || 'light';
            this.apply(current === 'dark' ? 'light' : 'dark');
        },

        get() {
            return localStorage.getItem('theme') || 'light';
        },
    };

    // ===========================================
    // Initialize on DOM Ready
    // ===========================================
    document.addEventListener('DOMContentLoaded', () => {
        theme.init();
        toast.init();
        modal.init();

        // Add global utilities
        window.App.utils = utils;
        window.App.api = api;
        window.App.toast = toast;
        window.App.modal = modal;
        window.App.loading = loading;
        window.App.forms = forms;
        window.App.theme = theme;

        // Toggle theme button
        window.toggleTheme = () => theme.toggle();

        // Auto-hide flash messages
        document.querySelectorAll('[data-auto-hide]').forEach(el => {
            setTimeout(() => {
                el.style.opacity = '0';
                el.style.transform = 'translateX(100%)';
                setTimeout(() => el.remove(), 300);
            }, parseInt(el.dataset.autoHide) || 5000);
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + K for search
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                const searchInput = document.querySelector('input[type="search"], input[placeholder*="search" i]');
                if (searchInput) {
                    searchInput.focus();
                    searchInput.select();
                }
            }

            // Escape to close modals
            if (e.key === 'Escape') {
                modal.close();
            }
        });

        // Add ripple effect to buttons
        document.addEventListener('click', (e) => {
            const button = e.target.closest('button, .btn, a.btn');
            if (button && !button.classList.contains('no-ripple')) {
                const ripple = document.createElement('span');
                ripple.className = 'absolute rounded-full bg-white/30 animate-ripple pointer-events-none';
                const rect = button.getBoundingClientRect();
                const size = Math.max(rect.width, rect.height);
                ripple.style.width = ripple.style.height = `${size}px`;
                ripple.style.left = `${e.clientX - rect.left - size / 2}px`;
                ripple.style.top = `${e.clientY - rect.top - size / 2}px`;
                button.style.position = 'relative';
                button.style.overflow = 'hidden';
                button.appendChild(ripple);
                setTimeout(() => ripple.remove(), 600);
            }
        });

        // Lazy load images
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        if (img.dataset.src) {
                            img.src = img.dataset.src;
                            img.removeAttribute('data-src');
                        }
                        imageObserver.unobserve(img);
                    }
                });
            });
            document.querySelectorAll('img[data-src]').forEach(img => imageObserver.observe(img));
        }

        console.log('OpenCareOS initialized');
    });

    // Add ripple animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes ripple {
            to {
                transform: scale(2);
                opacity: 0;
            }
        }
        .animate-ripple {
            animation: ripple 0.6s ease-out;
        }
    `;
    document.head.appendChild(style);
})();