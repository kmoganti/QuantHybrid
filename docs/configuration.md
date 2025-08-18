# Configuration Guide

## Overview

This guide details all configuration options in the QuantHybrid system. The system uses a layered configuration approach with different files for different aspects of the system.

## Configuration Files

1. `settings.py` - Main system settings
2. `risk_settings.py` - Risk management parameters
3. `logging_config.py` - Logging configuration
4. `db_config.py` - Database settings

## Main Settings (settings.py)

### Basic Configuration
```python
# Environment Configuration
ENV = os.getenv('ENVIRONMENT', 'development')  # 'development', 'production', 'testing'
DEBUG = ENV == 'development'

# API Configuration
API_HOST = os.getenv('API_HOST', '0.0.0.0')
API_PORT = int(os.getenv('API_PORT', '8000'))
API_VERSION = 'v1'
API_PREFIX = f'/api/{API_VERSION}'

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/quantdb')
DB_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '20'))
DB_MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', '10'))

# Redis Configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
REDIS_MAX_CONNECTIONS = int(os.getenv('REDIS_MAX_CONNECTIONS', '100'))

# Market Data Configuration
MARKET_DATA_SOURCE = os.getenv('MARKET_DATA_SOURCE', 'IIFL')
MARKET_DATA_API_KEY = os.getenv('MARKET_DATA_API_KEY')
MARKET_DATA_API_SECRET = os.getenv('MARKET_DATA_API_SECRET')

# Authentication Configuration
JWT_SECRET = os.getenv('JWT_SECRET', 'your-super-secret-key')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION = int(os.getenv('JWT_EXPIRATION', '3600'))  # 1 hour

# WebSocket Configuration
WS_HEARTBEAT_INTERVAL = int(os.getenv('WS_HEARTBEAT_INTERVAL', '30'))  # seconds
WS_CONNECTION_TIMEOUT = int(os.getenv('WS_CONNECTION_TIMEOUT', '60'))  # seconds

# Cache Configuration
CACHE_TTL = int(os.getenv('CACHE_TTL', '300'))  # seconds
CACHE_MAX_SIZE = int(os.getenv('CACHE_MAX_SIZE', '10000'))
```

## Risk Settings (risk_settings.py)

### Risk Limits
```python
# Position Limits
RISK_LIMITS = {
    'max_position_size': 1000,  # Maximum position size per symbol
    'max_total_exposure': 1000000,  # Maximum total exposure
    'max_leverage': 2.0,  # Maximum leverage
    'max_concentration': 0.2,  # Maximum concentration in single symbol
    
    # Loss Limits
    'max_daily_loss': 50000,  # Maximum daily loss
    'max_drawdown': 0.1,  # Maximum drawdown (10%)
    'stop_loss_threshold': 0.02,  # Stop loss threshold (2%)
    
    # Volatility Limits
    'max_volatility': 0.3,  # Maximum allowed volatility
    'high_volatility_threshold': 0.25,  # High volatility threshold
    'volatility_adjustment_factor': 0.5,  # Position size adjustment for high volatility
    
    # Trading Limits
    'max_trades_per_day': 100,  # Maximum trades per day
    'min_trade_interval': 5,  # Minimum seconds between trades
    'max_orders_per_second': 5,  # Maximum orders per second
}

# Circuit Breakers
CIRCUIT_BREAKERS = {
    'level_1': {
        'drawdown': 0.05,  # 5% drawdown
        'action': 'REDUCE_SIZE',
        'reduction_factor': 0.5
    },
    'level_2': {
        'drawdown': 0.08,  # 8% drawdown
        'action': 'STOP_NEW_TRADES',
        'duration': 3600  # 1 hour
    },
    'level_3': {
        'drawdown': 0.1,  # 10% drawdown
        'action': 'CLOSE_ALL_POSITIONS',
        'requires_manual_reset': True
    }
}

# Recovery Settings
RECOVERY_SETTINGS = {
    'activation_threshold': -20000,  # Activate recovery mode after 20k loss
    'position_size_factor': 0.5,  # Reduce position sizes by 50%
    'min_recovery_period': 3600,  # Minimum recovery period (1 hour)
    'recovery_targets': {
        'profit_target': 10000,  # Exit recovery mode after 10k profit
        'time_target': 86400  # Maximum recovery period (24 hours)
    }
}
```

## Logging Configuration (logging_config.py)

### Logging Setup
```python
# Logging Configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'detailed': {
            'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s'
        }
    },
    
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'level': 'INFO'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/trading.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'detailed',
            'level': 'DEBUG'
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/error.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'detailed',
            'level': 'ERROR'
        }
    },
    
    'loggers': {
        '': {  # Root logger
            'handlers': ['console', 'file'],
            'level': 'INFO'
        },
        'trading_system': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'DEBUG',
            'propagate': False
        },
        'market_data': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False
        }
    }
}

# Log Rotation Settings
LOG_ROTATION = {
    'max_size': 10485760,  # 10MB
    'backup_count': 5,
    'compression': True
}

# Log Monitoring
LOG_MONITORING = {
    'error_alert_threshold': 10,  # Alert after 10 errors in 5 minutes
    'monitoring_interval': 300,  # 5 minutes
    'alert_channels': ['email', 'slack']
}
```

## Database Configuration (db_config.py)

### Database Settings
```python
# Database Configuration
DATABASE_CONFIG = {
    'main': {
        'url': os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/quantdb'),
        'pool_size': 20,
        'max_overflow': 10,
        'pool_timeout': 30,
        'pool_recycle': 1800,
        'echo': False
    },
    'readonly': {
        'url': os.getenv('READONLY_DATABASE_URL', 'postgresql://readonly:password@localhost:5432/quantdb'),
        'pool_size': 10,
        'max_overflow': 5,
        'pool_timeout': 30,
        'pool_recycle': 1800,
        'echo': False
    }
}

# Connection Pool Settings
POOL_SETTINGS = {
    'pool_size': 20,
    'max_overflow': 10,
    'pool_timeout': 30,
    'pool_recycle': 1800
}

# Query Settings
QUERY_SETTINGS = {
    'timeout': 30,  # seconds
    'statement_timeout': 29000,  # milliseconds
    'max_row_count': 100000
}

# Migration Settings
MIGRATION_CONFIG = {
    'script_location': 'database/migrations',
    'target_metadata': 'database/models.py',
    'compare_type': True
}
```

## Environment Variables (.env)

Create a `.env` file in the root directory with the following template:

```bash
# Environment
ENVIRONMENT=development

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/quantdb
READONLY_DATABASE_URL=postgresql://readonly:password@localhost:5432/quantdb

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Market Data Configuration
MARKET_DATA_SOURCE=IIFL
MARKET_DATA_API_KEY=your_api_key
MARKET_DATA_API_SECRET=your_api_secret

# Authentication
JWT_SECRET=your-super-secret-key
JWT_EXPIRATION=3600

# Logging
LOG_LEVEL=DEBUG

# Risk Management
MAX_POSITION_SIZE=1000
MAX_DAILY_LOSS=50000
MAX_DRAWDOWN=0.1
```

## Configuration Management

### Validation
All configuration values are validated on system startup:
```python
def validate_config():
    """Validate all configuration settings."""
    validate_database_config()
    validate_risk_settings()
    validate_logging_config()
    check_environment_variables()
```

### Reloading
Configuration can be reloaded without system restart:
```python
async def reload_config():
    """Reload configuration settings."""
    load_env_variables()
    load_risk_settings()
    update_logging_config()
    notify_components()
```

### Security
Sensitive configuration values are encrypted:
```python
def encrypt_sensitive_config(config: dict) -> dict:
    """Encrypt sensitive configuration values."""
    sensitive_keys = ['API_SECRET', 'JWT_SECRET', 'DATABASE_URL']
    for key in sensitive_keys:
        if key in config:
            config[key] = encrypt_value(config[key])
    return config
```
