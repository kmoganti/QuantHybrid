/**
 * Dashboard module for QuantHybrid trading system
 */
class Dashboard {
    constructor() {
        this.systemMetricsWs = null;
        this.marketDataWs = null;
        this.performanceChart = null;
        this.updateInterval = null;
        
        this.initialize();
    }

    async initialize() {
        // Initialize charts
        this.initializePerformanceChart();
        
        // Start real-time updates
        this.startRealtimeUpdates();
        
        // Initial data load
        await this.loadDashboardData();
        
        // Setup event listeners
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Trading toggle button
        const tradingToggle = document.getElementById('tradingToggle');
        tradingToggle.addEventListener('click', async () => {
            try {
                if (tradingToggle.classList.contains('trading-disabled')) {
                    await api.enableTrading();
                    this.updateTradingStatus(true);
                } else {
                    await api.disableTrading();
                    this.updateTradingStatus(false);
                }
            } catch (error) {
                console.error('Failed to toggle trading:', error);
                this.showError('Failed to toggle trading status');
            }
        });

        // Handle authentication events
        window.addEventListener('auth:login', () => this.onLogin());
        window.addEventListener('auth:logout', () => this.onLogout());
    }

    async loadDashboardData() {
        try {
            // Get system status
            const status = await api.getSystemStatus();
            this.updateSystemStatus(status);

            // Get performance data
            const performance = await api.getPerformance();
            this.updatePerformanceChart(performance);

            // Get active strategies
            const strategies = await api.getStrategies();
            this.updateActiveStrategies(strategies);

        } catch (error) {
            console.error('Failed to load dashboard data:', error);
            this.showError('Failed to load dashboard data');
        }
    }

    startRealtimeUpdates() {
        // Connect to system metrics WebSocket
        this.systemMetricsWs = api.connectToSystemMetrics((data) => {
            this.updateSystemStatus(data);
        });

        // Connect to market data WebSocket
        this.marketDataWs = api.connectToMarketData((data) => {
            this.updateMarketData(data);
        });

        // Start periodic updates
        this.updateInterval = setInterval(() => {
            this.loadDashboardData();
        }, 60000); // Refresh every minute
    }

    stopRealtimeUpdates() {
        if (this.systemMetricsWs) {
            this.systemMetricsWs.close();
        }
        if (this.marketDataWs) {
            this.marketDataWs.close();
        }
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
    }

    initializePerformanceChart() {
        const ctx = document.getElementById('performanceChart').getContext('2d');
        this.performanceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'P&L',
                    data: [],
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: true,
                        text: 'Daily Performance'
                    }
                }
            }
        });
    }

    updateSystemStatus(status) {
        // Update system metrics
        document.getElementById('cpuUsage').textContent = status.cpu_usage.toFixed(1);
        document.getElementById('memoryUsage').textContent = status.memory_usage.toFixed(1);
        document.getElementById('networkLatency').textContent = status.network_latency.toFixed(0);
        document.getElementById('activeStrategies').textContent = status.active_strategies;
        document.getElementById('openPositions').textContent = status.total_positions;
        
        // Update P&L with color coding
        const pnlElement = document.getElementById('dailyPnL');
        const pnl = status.daily_pnl;
        pnlElement.textContent = pnl.toFixed(2);
        pnlElement.className = pnl >= 0 ? 'text-success' : 'text-danger';

        // Update trading status
        this.updateTradingStatus(status.trading_enabled);
    }

    updateMarketData(data) {
        // Update market data cards
        const container = document.getElementById('marketDataContainer');
        if (!container) return;

        // Clear existing content
        container.innerHTML = '';

        // Add market data cards
        for (const [symbol, quote] of Object.entries(data)) {
            const card = this.createMarketDataCard(symbol, quote);
            container.appendChild(card);
        }
    }

    createMarketDataCard(symbol, quote) {
        const card = document.createElement('div');
        card.className = 'col-md-3 mb-3';
        card.innerHTML = `
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">${symbol}</h5>
                    <p class="mb-1">Bid: ${quote.bid}</p>
                    <p class="mb-1">Ask: ${quote.ask}</p>
                    <p class="mb-1">Last: ${quote.last}</p>
                    <p class="mb-0">Volume: ${quote.volume}</p>
                </div>
            </div>
        `;
        return card;
    }

    updatePerformanceChart(data) {
        if (!this.performanceChart) return;

        this.performanceChart.data.labels = data.timestamps;
        this.performanceChart.data.datasets[0].data = data.pnl;
        this.performanceChart.update();
    }

    updateActiveStrategies(strategies) {
        const container = document.getElementById('activeStrategiesList');
        if (!container) return;

        container.innerHTML = ''; // Clear existing content

        if (strategies.length === 0) {
            container.innerHTML = '<p class="text-muted">No active strategies</p>';
            return;
        }

        const table = document.createElement('table');
        table.className = 'table table-hover';
        table.innerHTML = `
            <thead>
                <tr>
                    <th>Strategy</th>
                    <th>Type</th>
                    <th>P&L</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                ${strategies.map(strategy => `
                    <tr>
                        <td>${strategy.name}</td>
                        <td>${strategy.type}</td>
                        <td class="${strategy.pnl >= 0 ? 'text-success' : 'text-danger'}">
                            ${strategy.pnl.toFixed(2)}
                        </td>
                        <td>
                            <span class="strategy-status status-${strategy.is_active ? 'active' : 'inactive'}"></span>
                            ${strategy.is_active ? 'Active' : 'Inactive'}
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        `;
        container.appendChild(table);
    }

    updateTradingStatus(isEnabled) {
        const button = document.getElementById('tradingToggle');
        if (isEnabled) {
            button.classList.remove('trading-disabled');
            button.classList.add('trading-enabled');
            button.textContent = 'Trading Enabled';
        } else {
            button.classList.remove('trading-enabled');
            button.classList.add('trading-disabled');
            button.textContent = 'Trading Disabled';
        }
    }

    showError(message) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-danger alert-dismissible fade show';
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        const container = document.querySelector('.container-fluid');
        container.insertBefore(alert, container.firstChild);

        // Auto-hide after 5 seconds
        setTimeout(() => {
            alert.remove();
        }, 5000);
    }

    onLogin() {
        this.initialize();
    }

    onLogout() {
        this.stopRealtimeUpdates();
    }
}

// Initialize dashboard when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new Dashboard();
});
