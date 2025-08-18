/**
 * API client for QuantHybrid trading system
 */
class ApiClient {
    constructor() {
        this.baseUrl = '/api';
        this.token = localStorage.getItem('token');
    }

    async request(endpoint, options = {}) {
        try {
            const url = `${this.baseUrl}${endpoint}`;
            const headers = {
                'Content-Type': 'application/json',
                ...(this.token && { 'Authorization': `Bearer ${this.token}` }),
                ...options.headers
            };

            const response = await fetch(url, {
                ...options,
                headers
            });

            if (response.status === 401) {
                // Token expired or invalid
                localStorage.removeItem('token');
                window.location.reload();
                return;
            }

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    // Authentication
    async login(username, password) {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        const response = await fetch(`${this.baseUrl}/token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData
        });

        if (!response.ok) {
            throw new Error('Login failed');
        }

        const data = await response.json();
        this.token = data.access_token;
        localStorage.setItem('token', data.access_token);
        return data;
    }

    // System Status
    async getSystemStatus() {
        return this.request('/system/status');
    }

    // Strategies
    async getStrategies() {
        return this.request('/strategies');
    }

    async createStrategy(strategy) {
        return this.request('/strategies', {
            method: 'POST',
            body: JSON.stringify(strategy)
        });
    }

    async updateStrategy(strategyId, strategy) {
        return this.request(`/strategies/${strategyId}`, {
            method: 'PUT',
            body: JSON.stringify(strategy)
        });
    }

    // Positions
    async getPositions() {
        return this.request('/positions');
    }

    // Orders
    async getOrders(status, limit = 100) {
        return this.request(`/orders?status=${status}&limit=${limit}`);
    }

    // Performance
    async getPerformance(strategyId = null, timeframe = '1d') {
        let url = '/performance?timeframe=' + timeframe;
        if (strategyId) {
            url += `&strategy_id=${strategyId}`;
        }
        return this.request(url);
    }

    // Trading Control
    async enableTrading() {
        return this.request('/trading/enable', { method: 'POST' });
    }

    async disableTrading() {
        return this.request('/trading/disable', { method: 'POST' });
    }

    // WebSocket Connections
    connectToMarketData(onMessage) {
        const ws = new WebSocket(`ws://${window.location.host}/ws/market-data`);
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            onMessage(data);
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        return ws;
    }

    connectToSystemMetrics(onMessage) {
        const ws = new WebSocket(`ws://${window.location.host}/ws/system-metrics`);
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            onMessage(data);
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        return ws;
    }
}

// Create global API client instance
const api = new ApiClient();
