"""
Unit tests for backtesting and paper trading functionality.
"""
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from tests.base_test import BaseTestCase
from strategies.ma_crossover import MACrossoverStrategy
from execution.order_manager import OrderManager
from database.database_manager import DatabaseManager
from core.market_data.market_data_manager import MarketDataManager

class TestBacktesting(BaseTestCase):
    """Test suite for backtesting system."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.strategy = MACrossoverStrategy()
        self.order_manager = OrderManager()
        self.db_manager = DatabaseManager()
        self.market_data_manager = MarketDataManager()
        
        # Setup test data
        self.test_start_date = datetime(2025, 1, 1)
        self.test_end_date = datetime(2025, 8, 16)
        self.test_symbol = "RELIANCE"
        
    def create_test_market_data(self):
        """Create synthetic market data for testing."""
        dates = pd.date_range(self.test_start_date, self.test_end_date, freq='1D')
        np.random.seed(42)  # For reproducibility
        
        prices = 1000 + np.random.randn(len(dates)).cumsum()
        volumes = np.random.randint(1000, 10000, len(dates))
        
        return pd.DataFrame({
            'date': dates,
            'open': prices + np.random.randn(len(dates)),
            'high': prices + abs(np.random.randn(len(dates))*2),
            'low': prices - abs(np.random.randn(len(dates))*2),
            'close': prices,
            'volume': volumes
        })

    async def test_backtest_data_loading(self):
        """Test historical data loading for backtesting."""
        test_data = self.create_test_market_data()
        
        with patch.object(self.market_data_manager, 'get_historical_data') as mock_get_data:
            mock_get_data.return_value = test_data
            
            data = await self.market_data_manager.get_historical_data(
                self.test_symbol,
                self.test_start_date,
                self.test_end_date
            )
            
            self.assertIsNotNone(data)
            self.assertEqual(len(data), len(test_data))
            self.assertTrue(all(col in data.columns 
                              for col in ['open', 'high', 'low', 'close', 'volume']))

    async def test_strategy_backtesting(self):
        """Test strategy execution in backtest mode."""
        test_data = self.create_test_market_data()
        
        # Configure strategy for backtesting
        self.strategy.is_backtest = True
        self.strategy.backtest_data = test_data
        
        # Run backtest
        results = await self.strategy.run_backtest(
            self.test_symbol,
            self.test_start_date,
            self.test_end_date
        )
        
        # Verify backtest results
        self.assertIsNotNone(results)
        self.assertTrue('trades' in results)
        self.assertTrue('performance_metrics' in results)
        self.assertTrue('equity_curve' in results)

    async def test_performance_metrics(self):
        """Test calculation of backtest performance metrics."""
        test_trades = [
            {'entry_price': 100, 'exit_price': 110, 'quantity': 1, 'side': 'BUY'},
            {'entry_price': 120, 'exit_price': 115, 'quantity': 1, 'side': 'SELL'},
            {'entry_price': 105, 'exit_price': 125, 'quantity': 2, 'side': 'BUY'}
        ]
        
        metrics = await self.strategy.calculate_performance_metrics(test_trades)
        
        self.assertIsNotNone(metrics['total_return'])
        self.assertIsNotNone(metrics['sharpe_ratio'])
        self.assertIsNotNone(metrics['max_drawdown'])
        self.assertIsNotNone(metrics['win_rate'])

    async def test_paper_trading_execution(self):
        """Test paper trading order execution."""
        # Setup paper trading environment
        self.order_manager.is_paper_trading = True
        
        # Create test order
        test_order = {
            'symbol': self.test_symbol,
            'quantity': 100,
            'side': 'BUY',
            'order_type': 'MARKET',
            'price': 1000
        }
        
        # Execute paper trade
        with patch.object(self.market_data_manager, 'get_last_price') as mock_price:
            mock_price.return_value = 1000
            
            execution_result = await self.order_manager.execute_order(test_order)
            
            self.assertTrue(execution_result['success'])
            self.assertEqual(execution_result['executed_quantity'], test_order['quantity'])
            self.assertEqual(execution_result['executed_price'], 1000)

    async def test_paper_trading_position_tracking(self):
        """Test paper trading position tracking."""
        self.order_manager.is_paper_trading = True
        
        # Execute multiple paper trades
        test_orders = [
            {'symbol': self.test_symbol, 'quantity': 100, 'side': 'BUY', 'price': 1000},
            {'symbol': self.test_symbol, 'quantity': 50, 'side': 'SELL', 'price': 1100},
            {'symbol': self.test_symbol, 'quantity': 75, 'side': 'BUY', 'price': 1050}
        ]
        
        for order in test_orders:
            await self.order_manager.execute_order(order)
        
        # Verify position
        position = await self.order_manager.get_position(self.test_symbol)
        self.assertEqual(position['quantity'], 125)  # 100 - 50 + 75
        
    async def test_slippage_simulation(self):
        """Test slippage simulation in paper trading."""
        self.order_manager.is_paper_trading = True
        
        test_order = {
            'symbol': self.test_symbol,
            'quantity': 1000,  # Large order to test slippage
            'side': 'BUY',
            'order_type': 'MARKET',
            'price': 1000
        }
        
        with patch.object(self.market_data_manager, 'get_last_price') as mock_price:
            mock_price.return_value = 1000
            
            execution_result = await self.order_manager.execute_order(test_order)
            
            # Verify slippage effect
            self.assertGreater(execution_result['executed_price'], 1000)
            
    async def test_market_impact(self):
        """Test market impact simulation in paper trading."""
        self.order_manager.is_paper_trading = True
        
        # Get initial market price
        with patch.object(self.market_data_manager, 'get_last_price') as mock_price:
            mock_price.return_value = 1000
            initial_price = await self.market_data_manager.get_last_price(self.test_symbol)
        
        # Execute large order
        large_order = {
            'symbol': self.test_symbol,
            'quantity': 10000,  # Very large order
            'side': 'BUY',
            'order_type': 'MARKET',
            'price': initial_price
        }
        
        execution_result = await self.order_manager.execute_order(large_order)
        
        # Verify market impact
        self.assertGreater(
            execution_result['market_impact'],
            0,
            "Large orders should have measurable market impact"
        )

    async def test_backtest_risk_management(self):
        """Test risk management rules in backtesting."""
        test_data = self.create_test_market_data()
        self.strategy.is_backtest = True
        self.strategy.backtest_data = test_data
        
        # Set risk limits
        risk_limits = {
            'max_position_size': 1000,
            'max_daily_loss': 5000,
            'max_drawdown': 0.1
        }
        
        self.strategy.risk_limits = risk_limits
        
        # Run backtest
        results = await self.strategy.run_backtest(
            self.test_symbol,
            self.test_start_date,
            self.test_end_date
        )
        
        # Verify risk compliance
        max_position = max(trade['quantity'] for trade in results['trades'])
        self.assertLessEqual(max_position, risk_limits['max_position_size'])
        
        # Verify drawdown limit
        self.assertLessEqual(
            abs(results['performance_metrics']['max_drawdown']),
            risk_limits['max_drawdown']
        )

if __name__ == '__main__':
    unittest.main()
