/**
 * Performance analytics module for QuantHybrid trading system
 */
class PerformanceAnalytics {
    constructor() {
        this.performanceData = null;
        this.charts = {};
        this.initialize();
    }

    async initialize() {
        // Initialize charts
        this.initializeCharts();
        
        // Load initial data
        await this.loadPerformanceData();
        
        // Setup event listeners
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Timeframe selector
        const timeframeSelect = document.getElementById('timeframeSelect');
        if (timeframeSelect) {
            timeframeSelect.addEventListener('change', () => this.loadPerformanceData());
        }

        // Strategy selector
        const strategySelect = document.getElementById('strategySelect');
        if (strategySelect) {
            strategySelect.addEventListener('change', () => this.loadPerformanceData());
        }

        // Handle authentication events
        window.addEventListener('auth:logout', () => this.clearCharts());
    }

    initializeCharts() {
        // Equity curve chart
        this.charts.equity = this.createEquityChart();
        
        // Drawdown chart
        this.charts.drawdown = this.createDrawdownChart();
        
        // Daily returns chart
        this.charts.returns = this.createReturnsChart();
        
        // Win/Loss ratio chart
        this.charts.winLoss = this.createWinLossChart();
    }

    createEquityChart() {
        const ctx = document.getElementById('equityChart').getContext('2d');
        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Equity Curve',
                    data: [],
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1,
                    fill: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Equity Curve'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false
                    }
                }
            }
        });
    }

    createDrawdownChart() {
        const ctx = document.getElementById('drawdownChart').getContext('2d');
        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Drawdown',
                    data: [],
                    borderColor: 'rgb(255, 99, 132)',
                    fill: true,
                    backgroundColor: 'rgba(255, 99, 132, 0.2)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Drawdown'
                    }
                },
                scales: {
                    y: {
                        reverse: true,
                        beginAtZero: true
                    }
                }
            }
        });
    }

    createReturnsChart() {
        const ctx = document.getElementById('returnsChart').getContext('2d');
        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Daily Returns',
                    data: [],
                    backgroundColor: []
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Daily Returns'
                    }
                }
            }
        });
    }

    createWinLossChart() {
        const ctx = document.getElementById('winLossChart').getContext('2d');
        return new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Winning Trades', 'Losing Trades'],
                datasets: [{
                    data: [0, 0],
                    backgroundColor: [
                        'rgb(75, 192, 192)',
                        'rgb(255, 99, 132)'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Win/Loss Ratio'
                    }
                }
            }
        });
    }

    async loadPerformanceData() {
        try {
            const timeframeSelect = document.getElementById('timeframeSelect');
            const strategySelect = document.getElementById('strategySelect');
            
            const timeframe = timeframeSelect ? timeframeSelect.value : '1d';
            const strategyId = strategySelect ? strategySelect.value : null;
            
            this.performanceData = await api.getPerformance(strategyId, timeframe);
            this.updateCharts();
            this.updateMetrics();
            
        } catch (error) {
            console.error('Failed to load performance data:', error);
            this.showError('Failed to load performance data');
        }
    }

    updateCharts() {
        if (!this.performanceData) return;

        // Update equity curve
        this.charts.equity.data.labels = this.performanceData.timestamps;
        this.charts.equity.data.datasets[0].data = this.performanceData.equity;
        this.charts.equity.update();

        // Update drawdown
        this.charts.drawdown.data.labels = this.performanceData.timestamps;
        this.charts.drawdown.data.datasets[0].data = this.performanceData.drawdown;
        this.charts.drawdown.update();

        // Update daily returns
        this.charts.returns.data.labels = this.performanceData.timestamps;
        this.charts.returns.data.datasets[0].data = this.performanceData.returns;
        this.charts.returns.data.datasets[0].backgroundColor = this.performanceData.returns.map(
            value => value >= 0 ? 'rgb(75, 192, 192)' : 'rgb(255, 99, 132)'
        );
        this.charts.returns.update();

        // Update win/loss ratio
        this.charts.winLoss.data.datasets[0].data = [
            this.performanceData.winning_trades,
            this.performanceData.losing_trades
        ];
        this.charts.winLoss.update();
    }

    updateMetrics() {
        if (!this.performanceData) return;

        const metricsContainer = document.getElementById('performanceMetrics');
        if (!metricsContainer) return;

        metricsContainer.innerHTML = `
            <div class="row">
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">Total Return</h5>
                            <p class="card-text ${this.performanceData.total_return >= 0 ? 'text-success' : 'text-danger'}">
                                ${this.performanceData.total_return.toFixed(2)}%
                            </p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">Sharpe Ratio</h5>
                            <p class="card-text">
                                ${this.performanceData.sharpe_ratio.toFixed(2)}
                            </p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">Max Drawdown</h5>
                            <p class="card-text text-danger">
                                ${this.performanceData.max_drawdown.toFixed(2)}%
                            </p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">Win Rate</h5>
                            <p class="card-text">
                                ${this.performanceData.win_rate.toFixed(2)}%
                            </p>
                        </div>
                    </div>
                </div>
            </div>
            <div class="row mt-3">
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">Profit Factor</h5>
                            <p class="card-text">
                                ${this.performanceData.profit_factor.toFixed(2)}
                            </p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">Average Trade</h5>
                            <p class="card-text ${this.performanceData.average_trade >= 0 ? 'text-success' : 'text-danger'}">
                                ${this.performanceData.average_trade.toFixed(2)}
                            </p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">Total Trades</h5>
                            <p class="card-text">
                                ${this.performanceData.total_trades}
                            </p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">Recovery Factor</h5>
                            <p class="card-text">
                                ${this.performanceData.recovery_factor.toFixed(2)}
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    clearCharts() {
        Object.values(this.charts).forEach(chart => {
            chart.data.labels = [];
            chart.data.datasets.forEach(dataset => {
                dataset.data = [];
            });
            chart.update();
        });
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
        setTimeout(() => alert.remove(), 5000);
    }
}

// Initialize performance analytics when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.performanceAnalytics = new PerformanceAnalytics();
});
