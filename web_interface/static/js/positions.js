/**
 * Position monitoring module for QuantHybrid trading system
 */
class PositionManager {
    constructor() {
        this.positions = [];
        this.updateInterval = null;
        this.initialize();
    }

    async initialize() {
        await this.loadPositions();
        this.startRealtimeUpdates();
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Refresh button
        const refreshBtn = document.getElementById('refreshPositions');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadPositions());
        }

        // Position actions
        document.getElementById('positionsList').addEventListener('click', (e) => {
            if (e.target.classList.contains('btn-close-position')) {
                this.closePosition(e.target.dataset.id);
            }
        });

        // Handle authentication events
        window.addEventListener('auth:logout', () => this.stopRealtimeUpdates());
    }

    startRealtimeUpdates() {
        this.updateInterval = setInterval(() => {
            this.loadPositions();
        }, 5000); // Update every 5 seconds
    }

    stopRealtimeUpdates() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
    }

    async loadPositions() {
        try {
            this.positions = await api.getPositions();
            this.renderPositions();
        } catch (error) {
            console.error('Failed to load positions:', error);
            this.showError('Failed to load positions');
        }
    }

    renderPositions() {
        const container = document.getElementById('positionsList');
        if (!container) return;

        if (this.positions.length === 0) {
            container.innerHTML = '<p class="text-muted">No open positions</p>';
            return;
        }

        const table = document.createElement('table');
        table.className = 'table table-hover';
        table.innerHTML = `
            <thead>
                <tr>
                    <th>Instrument</th>
                    <th>Strategy</th>
                    <th>Side</th>
                    <th>Quantity</th>
                    <th>Entry Price</th>
                    <th>Current Price</th>
                    <th>P&L</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                ${this.positions.map(position => `
                    <tr class="position-${position.side.toLowerCase()}">
                        <td>${position.instrument_id}</td>
                        <td>${position.strategy_name}</td>
                        <td>${position.side}</td>
                        <td>${position.quantity}</td>
                        <td>${position.entry_price.toFixed(2)}</td>
                        <td>${position.current_price.toFixed(2)}</td>
                        <td class="${position.unrealized_pnl >= 0 ? 'text-success' : 'text-danger'}">
                            ${position.unrealized_pnl.toFixed(2)}
                        </td>
                        <td>
                            <button class="btn btn-sm btn-warning btn-close-position" 
                                    data-id="${position.id}">
                                Close
                            </button>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
            <tfoot>
                <tr class="table-dark">
                    <td colspan="6"><strong>Total</strong></td>
                    <td colspan="2" class="${this.getTotalPnL() >= 0 ? 'text-success' : 'text-danger'}">
                        <strong>${this.getTotalPnL().toFixed(2)}</strong>
                    </td>
                </tr>
            </tfoot>
        `;
        container.innerHTML = '';
        container.appendChild(table);
    }

    getTotalPnL() {
        return this.positions.reduce((total, position) => total + position.unrealized_pnl, 0);
    }

    async closePosition(positionId) {
        if (!confirm('Are you sure you want to close this position?')) return;

        try {
            await api.closePosition(positionId);
            await this.loadPositions();
            this.showSuccess('Position closed successfully');
        } catch (error) {
            console.error('Failed to close position:', error);
            this.showError('Failed to close position');
        }
    }

    showSuccess(message) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-success alert-dismissible fade show';
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        this.showAlert(alert);
    }

    showError(message) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-danger alert-dismissible fade show';
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        this.showAlert(alert);
    }

    showAlert(alert) {
        const container = document.querySelector('.container-fluid');
        container.insertBefore(alert, container.firstChild);
        setTimeout(() => alert.remove(), 5000);
    }
}

/**
 * Order monitoring module for QuantHybrid trading system
 */
class OrderManager {
    constructor() {
        this.orders = [];
        this.updateInterval = null;
        this.initialize();
    }

    async initialize() {
        await this.loadOrders();
        this.startRealtimeUpdates();
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Refresh button
        const refreshBtn = document.getElementById('refreshOrders');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadOrders());
        }

        // Order actions
        document.getElementById('ordersList').addEventListener('click', (e) => {
            if (e.target.classList.contains('btn-cancel-order')) {
                this.cancelOrder(e.target.dataset.id);
            }
        });

        // Status filter
        const statusFilter = document.getElementById('orderStatusFilter');
        if (statusFilter) {
            statusFilter.addEventListener('change', () => this.loadOrders());
        }

        // Handle authentication events
        window.addEventListener('auth:logout', () => this.stopRealtimeUpdates());
    }

    startRealtimeUpdates() {
        this.updateInterval = setInterval(() => {
            this.loadOrders();
        }, 5000); // Update every 5 seconds
    }

    stopRealtimeUpdates() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
    }

    async loadOrders() {
        try {
            const statusFilter = document.getElementById('orderStatusFilter');
            const status = statusFilter ? statusFilter.value : null;
            
            this.orders = await api.getOrders(status);
            this.renderOrders();
        } catch (error) {
            console.error('Failed to load orders:', error);
            this.showError('Failed to load orders');
        }
    }

    renderOrders() {
        const container = document.getElementById('ordersList');
        if (!container) return;

        if (this.orders.length === 0) {
            container.innerHTML = '<p class="text-muted">No orders found</p>';
            return;
        }

        const table = document.createElement('table');
        table.className = 'table table-hover';
        table.innerHTML = `
            <thead>
                <tr>
                    <th>Time</th>
                    <th>Instrument</th>
                    <th>Strategy</th>
                    <th>Type</th>
                    <th>Side</th>
                    <th>Quantity</th>
                    <th>Price</th>
                    <th>Status</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                ${this.orders.map(order => `
                    <tr>
                        <td>${new Date(order.submission_time).toLocaleString()}</td>
                        <td>${order.instrument_id}</td>
                        <td>${order.strategy_name}</td>
                        <td>${order.order_type}</td>
                        <td>${order.side}</td>
                        <td>${order.quantity}</td>
                        <td>${order.price ? order.price.toFixed(2) : 'MKT'}</td>
                        <td>
                            <span class="order-status status-${order.status.toLowerCase()}">
                                ${order.status}
                            </span>
                        </td>
                        <td>
                            ${order.status === 'PENDING' || order.status === 'SUBMITTED' ? `
                                <button class="btn btn-sm btn-danger btn-cancel-order" 
                                        data-id="${order.id}">
                                    Cancel
                                </button>
                            ` : ''}
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        `;
        container.innerHTML = '';
        container.appendChild(table);
    }

    async cancelOrder(orderId) {
        if (!confirm('Are you sure you want to cancel this order?')) return;

        try {
            await api.cancelOrder(orderId);
            await this.loadOrders();
            this.showSuccess('Order cancelled successfully');
        } catch (error) {
            console.error('Failed to cancel order:', error);
            this.showError('Failed to cancel order');
        }
    }

    showSuccess(message) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-success alert-dismissible fade show';
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        this.showAlert(alert);
    }

    showError(message) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-danger alert-dismissible fade show';
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        this.showAlert(alert);
    }

    showAlert(alert) {
        const container = document.querySelector('.container-fluid');
        container.insertBefore(alert, container.firstChild);
        setTimeout(() => alert.remove(), 5000);
    }
}

// Initialize position and order managers when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.positionManager = new PositionManager();
    window.orderManager = new OrderManager();
});
