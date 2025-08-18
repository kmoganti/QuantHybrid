/**
 * Strategy management module for QuantHybrid trading system
 */
class StrategyManager {
    constructor() {
        this.strategies = [];
        this.initialize();
    }

    async initialize() {
        // Setup event listeners
        this.setupEventListeners();
        
        // Load initial data
        await this.loadStrategies();
    }

    setupEventListeners() {
        // Strategy type selection change
        const strategyTypeSelect = document.querySelector('select[name="type"]');
        if (strategyTypeSelect) {
            strategyTypeSelect.addEventListener('change', (e) => {
                this.updateStrategyParameters(e.target.value);
            });
        }

        // Save strategy button
        const saveButton = document.getElementById('saveStrategy');
        if (saveButton) {
            saveButton.addEventListener('click', () => this.saveStrategy());
        }

        // Strategy list click handlers
        document.getElementById('strategiesList').addEventListener('click', (e) => {
            if (e.target.classList.contains('btn-edit')) {
                this.editStrategy(e.target.dataset.id);
            } else if (e.target.classList.contains('btn-delete')) {
                this.deleteStrategy(e.target.dataset.id);
            } else if (e.target.classList.contains('btn-toggle')) {
                this.toggleStrategy(e.target.dataset.id);
            }
        });
    }

    async loadStrategies() {
        try {
            this.strategies = await api.getStrategies();
            this.renderStrategiesList();
        } catch (error) {
            console.error('Failed to load strategies:', error);
            this.showError('Failed to load strategies');
        }
    }

    renderStrategiesList() {
        const container = document.getElementById('strategiesList');
        if (!container) return;

        if (this.strategies.length === 0) {
            container.innerHTML = '<p class="text-muted">No strategies configured</p>';
            return;
        }

        const table = document.createElement('table');
        table.className = 'table table-hover';
        table.innerHTML = `
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Type</th>
                    <th>Status</th>
                    <th>Performance</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                ${this.strategies.map(strategy => `
                    <tr>
                        <td>${strategy.name}</td>
                        <td>${strategy.type}</td>
                        <td>
                            <span class="strategy-status status-${strategy.is_active ? 'active' : 'inactive'}"></span>
                            ${strategy.is_active ? 'Active' : 'Inactive'}
                        </td>
                        <td>
                            <span class="${strategy.performance >= 0 ? 'text-success' : 'text-danger'}">
                                ${strategy.performance ? strategy.performance.toFixed(2) + '%' : 'N/A'}
                            </span>
                        </td>
                        <td>
                            <button class="btn btn-sm btn-primary btn-edit" data-id="${strategy.id}">
                                <i class="fa fa-edit"></i>
                            </button>
                            <button class="btn btn-sm btn-${strategy.is_active ? 'warning' : 'success'} btn-toggle" 
                                    data-id="${strategy.id}">
                                <i class="fa fa-${strategy.is_active ? 'pause' : 'play'}"></i>
                            </button>
                            <button class="btn btn-sm btn-danger btn-delete" data-id="${strategy.id}">
                                <i class="fa fa-trash"></i>
                            </button>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        `;
        container.innerHTML = '';
        container.appendChild(table);
    }

    updateStrategyParameters(strategyType) {
        const container = document.getElementById('strategyParameters');
        if (!container) return;

        let parametersHtml = '';
        switch (strategyType) {
            case 'MA_CROSSOVER':
                parametersHtml = `
                    <div class="mb-3">
                        <label class="form-label">Fast MA Period</label>
                        <input type="number" class="form-control" name="fast_ma_period" 
                               value="9" min="1" max="200" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Slow MA Period</label>
                        <input type="number" class="form-control" name="slow_ma_period" 
                               value="21" min="1" max="200" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Minimum Volume</label>
                        <input type="number" class="form-control" name="min_volume" 
                               value="100000" min="0" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Position Size</label>
                        <input type="number" class="form-control" name="position_size" 
                               value="1" min="1" required>
                    </div>
                `;
                break;
            // Add more strategy types here
        }
        container.innerHTML = parametersHtml;
    }

    async saveStrategy() {
        try {
            const form = document.getElementById('newStrategyForm');
            const formData = new FormData(form);
            
            const strategy = {
                name: formData.get('name'),
                type: formData.get('type'),
                parameters: {
                    fast_ma_period: parseInt(formData.get('fast_ma_period')),
                    slow_ma_period: parseInt(formData.get('slow_ma_period')),
                    min_volume: parseInt(formData.get('min_volume')),
                    position_size: parseInt(formData.get('position_size'))
                },
                is_active: false
            };

            const strategyId = form.dataset.strategyId;
            if (strategyId) {
                await api.updateStrategy(strategyId, strategy);
            } else {
                await api.createStrategy(strategy);
            }

            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('newStrategyModal'));
            modal.hide();

            // Refresh strategies list
            await this.loadStrategies();

            this.showSuccess('Strategy saved successfully');

        } catch (error) {
            console.error('Failed to save strategy:', error);
            this.showError('Failed to save strategy');
        }
    }

    async editStrategy(strategyId) {
        try {
            const strategy = this.strategies.find(s => s.id === parseInt(strategyId));
            if (!strategy) return;

            // Populate form
            const form = document.getElementById('newStrategyForm');
            form.dataset.strategyId = strategyId;
            form.elements['name'].value = strategy.name;
            form.elements['type'].value = strategy.type;

            // Update parameter fields
            this.updateStrategyParameters(strategy.type);

            // Populate parameters
            for (const [key, value] of Object.entries(strategy.parameters)) {
                if (form.elements[key]) {
                    form.elements[key].value = value;
                }
            }

            // Show modal
            const modal = new bootstrap.Modal(document.getElementById('newStrategyModal'));
            modal.show();

        } catch (error) {
            console.error('Failed to edit strategy:', error);
            this.showError('Failed to load strategy details');
        }
    }

    async deleteStrategy(strategyId) {
        if (!confirm('Are you sure you want to delete this strategy?')) return;

        try {
            await api.deleteStrategy(strategyId);
            await this.loadStrategies();
            this.showSuccess('Strategy deleted successfully');
        } catch (error) {
            console.error('Failed to delete strategy:', error);
            this.showError('Failed to delete strategy');
        }
    }

    async toggleStrategy(strategyId) {
        try {
            const strategy = this.strategies.find(s => s.id === parseInt(strategyId));
            if (!strategy) return;

            await api.updateStrategy(strategyId, {
                ...strategy,
                is_active: !strategy.is_active
            });

            await this.loadStrategies();
            this.showSuccess(`Strategy ${strategy.is_active ? 'stopped' : 'started'} successfully`);

        } catch (error) {
            console.error('Failed to toggle strategy:', error);
            this.showError('Failed to toggle strategy');
        }
    }

    showSuccess(message) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-success alert-dismissible fade show';
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        const container = document.querySelector('.container-fluid');
        container.insertBefore(alert, container.firstChild);

        setTimeout(() => {
            alert.remove();
        }, 5000);
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

        setTimeout(() => {
            alert.remove();
        }, 5000);
    }
}

// Initialize strategy manager when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.strategyManager = new StrategyManager();
});
