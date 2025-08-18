"""
Risk management settings and parameters based on industry best practices.
"""

# Capital Protection Parameters
RISK_LIMITS = {
    # Daily Risk Limits (% of total capital)
    'max_daily_loss_percent': 1.0,  # Maximum 1% loss per day
    'max_position_percent': 2.0,    # Maximum 2% risk per position
    'max_total_exposure': 15.0,     # Maximum 15% total portfolio exposure
    
    # Position Size Limits
    'min_position_size': 1,         # Minimum lots/quantity
    'max_position_size': 5,         # Maximum lots/quantity per trade
    'max_capital_per_trade': 0.02,  # Maximum 2% of capital per trade
    
    # Drawdown Controls
    'max_drawdown': 5.0,           # Maximum 5% drawdown before stopping
    'trailing_stop_percent': 2.0,   # 2% trailing stop loss
    
    # Volatility-based Adjustments
    'volatility_base': 15.0,       # Base annualized volatility (%)
    'high_volatility_threshold': 25.0,  # Reduce position above this volatility
    'medium_volatility_threshold': 20.0, # Start scaling down at this level
    'max_volatility': 35.0,        # Stop trading above this volatility
    
    # Market Regime Parameters
    'min_trend_strength': 20.0,    # Minimum ADX for trend following
    'max_spread_percent': 0.1,     # Maximum bid-ask spread (%)
    
    # Time-based Controls
    'min_time_between_trades': 60,  # Minimum seconds between trades
    'max_trades_per_hour': 5,      # Maximum trades per hour
    'max_trades_per_day': 20,      # Maximum trades per day
    
    # Price Movement Limits
    'max_adverse_price_movement': 1.0,  # Max adverse price movement (%)
    'price_timeout': 2.0,          # Max seconds for price staleness
    
    # Order Execution Safety
    'slippage_tolerance': 0.1,     # Maximum acceptable slippage (%)
    'min_volume_factor': 10,       # Min ratio of volume to position size
    'max_impact_factor': 0.1,      # Max market impact allowed (%)
}

# Strategy-specific Risk Adjustments
STRATEGY_RISK_ADJUSTMENTS = {
    'trending_market': {
        'position_size_multiplier': 1.0,
        'stop_loss_multiplier': 1.5,
        'profit_target_multiplier': 2.0
    },
    'ranging_market': {
        'position_size_multiplier': 0.7,
        'stop_loss_multiplier': 1.0,
        'profit_target_multiplier': 1.5
    },
    'high_volatility': {
        'position_size_multiplier': 0.5,
        'stop_loss_multiplier': 2.0,
        'profit_target_multiplier': 2.5
    }
}

# Market Hours Risk Adjustments
MARKET_HOURS_RISK = {
    'open_minutes': 15,            # First 15 minutes
    'close_minutes': 15,           # Last 15 minutes
    'position_size_factor': 0.5,   # Reduce position size by 50%
    'avoid_trading': True          # Avoid new positions during these periods
}

# Circuit Breaker Levels
CIRCUIT_BREAKERS = {
    'level_1': {
        'drawdown': 2.0,           # 2% drawdown
        'action': 'reduce_size',
        'reduction_factor': 0.5
    },
    'level_2': {
        'drawdown': 3.5,           # 3.5% drawdown
        'action': 'hedge_only',
        'reduction_factor': 0.75
    },
    'level_3': {
        'drawdown': 5.0,           # 5% drawdown
        'action': 'stop_trading',
        'cooldown_minutes': 60
    }
}

# Recovery Mode Parameters
RECOVERY_SETTINGS = {
    'activation_threshold': -3.0,   # Start recovery mode at 3% loss
    'position_size_factor': 0.3,    # Reduce to 30% of normal size
    'min_win_rate': 0.60,          # Required win rate to exit recovery
    'min_trades': 10,              # Minimum trades before normal mode
}

# Risk Monitoring Thresholds
MONITORING_THRESHOLDS = {
    'margin_warning': 50.0,        # Warning at 50% margin used
    'margin_critical': 70.0,       # Critical at 70% margin used
    'cpu_warning': 70.0,           # CPU usage warning threshold
    'memory_warning': 80.0,        # Memory usage warning threshold
    'latency_warning': 500,        # Order latency warning (ms)
    'quote_latency_warning': 1000, # Market data latency warning (ms)
}

# System Health Checks
HEALTH_CHECK_SETTINGS = {
    'check_interval': 60,          # Check every 60 seconds
    'max_order_latency': 2000,     # Maximum acceptable order latency (ms)
    'max_quote_staleness': 5000,   # Maximum quote age (ms)
    'min_tick_frequency': 10,      # Minimum ticks per second
    'heartbeat_interval': 30,      # Heartbeat check interval (seconds)
}
