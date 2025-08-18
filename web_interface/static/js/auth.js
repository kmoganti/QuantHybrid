/**
 * Authentication module for QuantHybrid trading system
 */
class Auth {
    constructor() {
        this.loginForm = document.getElementById('loginForm');
        this.mainContent = document.getElementById('mainContent');
        this.logoutBtn = document.getElementById('logoutBtn');
        
        this.setupEventListeners();
        this.checkAuth();
    }

    setupEventListeners() {
        // Login form submission
        document.getElementById('login').addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.handleLogin();
        });

        // Logout button
        this.logoutBtn.addEventListener('click', () => this.handleLogout());
    }

    async checkAuth() {
        const token = localStorage.getItem('token');
        if (!token) {
            this.showLoginForm();
            return false;
        }

        try {
            // Verify token by making a test API call
            await api.getSystemStatus();
            this.showMainContent();
            return true;
        } catch (error) {
            console.error('Auth check failed:', error);
            this.showLoginForm();
            return false;
        }
    }

    async handleLogin() {
        try {
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;

            // Show loading state
            this.setLoadingState(true);

            // Attempt login
            await api.login(username, password);

            // Clear form
            document.getElementById('login').reset();

            // Show main content
            this.showMainContent();

            // Initialize dashboard
            window.dispatchEvent(new Event('auth:login'));

        } catch (error) {
            console.error('Login failed:', error);
            this.showError('Login failed. Please check your credentials.');
        } finally {
            this.setLoadingState(false);
        }
    }

    handleLogout() {
        // Clear token
        localStorage.removeItem('token');

        // Reset API client
        api.token = null;

        // Show login form
        this.showLoginForm();

        // Notify other components
        window.dispatchEvent(new Event('auth:logout'));
    }

    showLoginForm() {
        this.loginForm.classList.remove('d-none');
        this.mainContent.classList.add('d-none');
    }

    showMainContent() {
        this.loginForm.classList.add('d-none');
        this.mainContent.classList.remove('d-none');
    }

    setLoadingState(isLoading) {
        const submitBtn = document.querySelector('#login button[type="submit"]');
        if (isLoading) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Logging in...';
        } else {
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Login';
        }
    }

    showError(message) {
        // Remove any existing error messages
        const existingError = document.querySelector('.alert-danger');
        if (existingError) {
            existingError.remove();
        }

        // Create and show new error message
        const alert = document.createElement('div');
        alert.className = 'alert alert-danger';
        alert.role = 'alert';
        alert.textContent = message;

        const form = document.getElementById('login');
        form.insertBefore(alert, form.firstChild);

        // Auto-hide after 5 seconds
        setTimeout(() => {
            alert.remove();
        }, 5000);
    }
}

// Initialize authentication when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.auth = new Auth();
});
