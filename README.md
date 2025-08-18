# QuantHybrid Trading System

A high-performance algorithmic trading system designed for the Indian markets with support for multiple strategies, real-time data processing, and comprehensive risk management.

## Features

- **Market Data Integration**: Real-time data handling with IIFL API integration
- **Strategy Framework**: Extensible strategy framework with built-in MA Crossover strategy
- **Risk Management**: Comprehensive risk monitoring and position management
- **Order Execution**: Smart order routing with slippage analysis
- **Web Interface**: Real-time monitoring dashboard and control panel
- **Database Management**: Efficient trade and position tracking
- **Monitoring System**: Advanced system health and performance monitoring
- **Notification System**: Real-time alerts and notifications

## System Requirements

- Python 3.9+
- PostgreSQL 13+
- Redis 6+
- 16GB RAM (minimum)
- Multi-core CPU recommended
- Fast internet connection for real-time data

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/yourusername/QuantHybrid.git
cd QuantHybrid
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up configuration:
```bash
cp config/settings.example.py config/settings.py
# Edit settings.py with your configuration
```

4. Initialize database:
```bash
python scripts/init_db.py
```

5. Start the system:
```bash
python main.py
```

## Documentation

- [User Guide](docs/user_guide.md) - Getting started and system usage
- [Technical Documentation](docs/technical/README.md) - System architecture and components
- [API Documentation](docs/api/README.md) - REST API and WebSocket endpoints
- [Strategy Guide](docs/strategies/README.md) - Creating and implementing strategies
- [Configuration Guide](docs/configuration.md) - System configuration options
- [Deployment Guide](docs/deployment.md) - Production deployment instructions

## Project Structure

```
QuantHybrid/
├── config/                 # Configuration files
├── core/                   # Core system components
│   └── market_data/       # Market data handling
├── database/              # Database management
├── execution/             # Order execution
├── monitoring/            # System monitoring
├── notifications/         # Alert system
├── risk_management/       # Risk management
├── strategies/            # Trading strategies
├── tests/                # Test suites
├── utils/                # Utility functions
└── web_interface/        # Web dashboard
```

## Testing

Run the test suite:
```bash
python -m pytest tests/
```

Performance tests:
```bash
python -m pytest tests/test_performance.py
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Run tests and ensure they pass
4. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions, please:
- Check the [FAQ](docs/faq.md)
- Open an issue
- Contact support@quantsystem.com

## Acknowledgments

- IIFL API for market data
- Contributors and maintainers
