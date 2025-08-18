"""
Unit tests for strategy components.
"""
import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from tests.base_test import BaseTestCase
from strategies import MovingAverageCrossoverStrategy
from core.market_data.market_data_manager import MarketDataManager
from execution.order_manager import OrderManager
from risk_management.risk_manager import RiskManager

class TestMovingAverageCrossoverStrategy(BaseTestCase):
    """Test suite for MA Crossover strategy."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        
        # Mock dependencies
        self.market_data = MagicMock(spec=MarketDataManager)
        self.order_manager = MagicMock(spec=OrderManager)
        self.risk_manager = MagicMock(spec=RiskManager)
        
        # Create strategy instance
        self.strategy = MovingAverageCrossoverStrategy(
            name="Test MA Strategy",
            instruments=[{'instrumentId': 'TEST'}],
            market_data_manager=self.market_data,
            order_manager=self.order_manager,
            risk_manager=self.risk_manager,
            params={
                'fast_ma_period': 9,
                'slow_ma_period': 21,
                'min_volume': 100000,
                'position_size': 1
            }
        )
    
    async def test_strategy_initialization(self):
        """Test strategy initialization."""
        self.assertEqual(self.strategy.name, "Test MA Strategy")
        self.assertEqual(len(self.strategy.instruments), 1)
        self.assertEqual(self.strategy.fast_ma_period, 9)
        self.assertEqual(self.strategy.slow_ma_period, 21)
        self.assertEqual(self.strategy.min_volume, 100000)
        self.assertEqual(self.strategy.position_size, 1)
        self.assertFalse(self.strategy.is_active)
    
    async def test_generate_buy_signal(self):
        """Test buy signal generation."""
        # Create test data with bullish crossover
        data = self.create_test_data("market_data", num_bars=50)
        # Modify close prices to create crossover
        data.loc[45:, 'close'] = [101 + i * 0.5 for i in range(5)]
        
        # Mock market data response
        self.market_data.get_historical_data.return_value = data
        
        # Update market data
        await self.strategy._update_market_data()
        
        # Generate signals
        await self.strategy._generate_signals()
        
        # Check if buy signal was generated
        self.assertTrue('TEST' in self.strategy.signals)
        signal = self.strategy.signals['TEST']
        self.assertTrue(signal['active'])
        self.assertEqual(signal['transaction_type'], 'BUY')
    
    async def test_generate_sell_signal(self):
        """Test sell signal generation."""
        # Create test data with bearish crossover
        data = self.create_test_data("market_data", num_bars=50)
        # Modify close prices to create crossover
        data.loc[45:, 'close'] = [101 - i * 0.5 for i in range(5)]
        
        # Mock market data response
        self.market_data.get_historical_data.return_value = data
        
        # Update market data
        await self.strategy._update_market_data()
        
        # Generate signals
        await self.strategy._generate_signals()
        
        # Check if sell signal was generated
        self.assertTrue('TEST' in self.strategy.signals)
        signal = self.strategy.signals['TEST']
        self.assertTrue(signal['active'])
        self.assertEqual(signal['transaction_type'], 'SELL')
    
    async def test_volume_filter(self):
        """Test volume filtering."""
        # Create test data with low volume
        data = self.create_test_data("market_data", num_bars=50)
        data['volume'] = 50000  # Below min_volume threshold
        
        # Mock market data response
        self.market_data.get_historical_data.return_value = data
        
        # Update market data
        await self.strategy._update_market_data()
        
        # Generate signals
        await self.strategy._generate_signals()
        
        # Check that no signal was generated due to low volume
        self.assertTrue('TEST' not in self.strategy.signals)
    
    async def test_risk_management_integration(self):
        """Test risk management integration."""
        # Create test data
        data = self.create_test_data("market_data", num_bars=50)
        
        # Mock market data response
        self.market_data.get_historical_data.return_value = data
        
        # Mock risk manager to reject order
        self.risk_manager.validate_order.return_value = False
        
        # Update market data
        await self.strategy._update_market_data()
        
        # Generate and execute signals
        await self.strategy._generate_signals()
        await self.strategy._execute_signals()
        
        # Verify that no order was placed due to risk management rejection
        self.order_manager.place_order.assert_not_called()
    
    async def test_position_tracking(self):
        """Test position tracking."""
        # Mock current positions
        self.order_manager.client.get_positions.return_value = {
            'result': [{
                'instrumentId': 'TEST',
                'quantity': 1,
                'avgPrice': 100.0,
                'side': 'BUY',
                'pnl': 50.0
            }]
        }
        
        # Update positions
        await self.strategy._update_positions()
        
        # Verify position tracking
        self.assertTrue('TEST' in self.strategy.positions)
        position = self.strategy.positions['TEST']
        self.assertEqual(position['quantity'], 1)
        self.assertEqual(position['avgPrice'], 100.0)
        self.assertEqual(position['pnl'], 50.0)
    
    async def test_performance_metrics(self):
        """Test performance metrics calculation."""
        # Set up test trades
        self.strategy.total_trades = 10
        self.strategy.winning_trades = 6
        
        # Mock positions with PnL
        self.strategy.positions = {
            'TEST': {'pnl': 100.0}
        }
        
        # Update metrics
        await self.strategy._update_metrics()
        
        # Verify metrics
        metrics = self.strategy.get_metrics()
        self.assertEqual(metrics['total_trades'], 10)
        self.assertEqual(metrics['winning_trades'], 6)
        self.assertEqual(metrics['win_rate'], 60.0)
        self.assertEqual(metrics['total_pnl'], 100.0)
    
    async def test_trading_hours_check(self):
        """Test trading hours validation."""
        # Test during trading hours
        current_time = datetime.strptime(TRADING_HOURS['start'], '%H:%M').time()
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime.combine(datetime.today(), current_time)
            self.assertTrue(self.strategy._is_trading_time())
        
        # Test outside trading hours
        outside_time = (datetime.strptime(TRADING_HOURS['end'], '%H:%M') + 
                       timedelta(minutes=1)).time()
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime.combine(datetime.today(), outside_time)
            self.assertFalse(self.strategy._is_trading_time())

if __name__ == '__main__':
    unittest.main()
