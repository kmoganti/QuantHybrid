"""
Base test case for QuantHybrid testing framework.
"""
import unittest
import asyncio
from typing import Dict, Any
import pandas as pd
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from config.settings import TRADING_HOURS
from database.database_manager import DatabaseManager
from utils.trading_state import TradingState

class BaseTestCase(unittest.TestCase):
    """Base test case with common utilities."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        # Create event loop for async tests
        cls.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(cls.loop)
        
        # Initialize common test components
        cls.trading_state = TradingState()
        cls.db_manager = DatabaseManager(test_mode=True)
        
        # Initialize test database
        cls.loop.run_until_complete(cls.db_manager.init_db())
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment."""
        cls.loop.close()
    
    def setUp(self):
        """Set up before each test."""
        # Reset trading state
        self.trading_state.reset()
        
        # Create clean database for tests
        self.loop.run_until_complete(self.db_manager.initialize(test_mode=True))
    
    def tearDown(self):
        """Clean up after each test."""
        # Clean up database
        self.loop.run_until_complete(self.db_manager.cleanup())
    
    def async_test(self, coro):
        """Wrapper for running async tests."""
        return self.loop.run_until_complete(coro)
    
    def create_test_data(self, data_type: str, **kwargs) -> Dict[str, Any]:
        """Create test data for different scenarios."""
        if data_type == "market_data":
            return self._create_market_data(**kwargs)
        elif data_type == "order":
            return self._create_order_data(**kwargs)
        elif data_type == "strategy":
            return self._create_strategy_data(**kwargs)
        else:
            raise ValueError(f"Unknown data type: {data_type}")
    
    def _create_market_data(self, num_bars: int = 100, **kwargs) -> pd.DataFrame:
        """Create sample market data for testing."""
        dates = pd.date_range(
            start=datetime.now() - timedelta(days=num_bars),
            end=datetime.now(),
            periods=num_bars
        )
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': [100 + i * 0.1 for i in range(num_bars)],
            'high': [101 + i * 0.1 for i in range(num_bars)],
            'low': [99 + i * 0.1 for i in range(num_bars)],
            'close': [100.5 + i * 0.1 for i in range(num_bars)],
            'volume': [1000000 for _ in range(num_bars)]
        })
        
        return data
    
    def _create_order_data(self, **kwargs) -> Dict:
        """Create sample order data for testing."""
        return {
            'instrument_id': kwargs.get('instrument_id', 'TEST'),
            'order_type': kwargs.get('order_type', 'MARKET'),
            'side': kwargs.get('side', 'BUY'),
            'quantity': kwargs.get('quantity', 1),
            'price': kwargs.get('price'),
            'strategy_id': kwargs.get('strategy_id', 1)
        }
    
    def _create_strategy_data(self, **kwargs) -> Dict:
        """Create sample strategy configuration for testing."""
        return {
            'name': kwargs.get('name', 'Test Strategy'),
            'type': kwargs.get('type', 'MA_CROSSOVER'),
            'parameters': kwargs.get('parameters', {
                'fast_ma_period': 9,
                'slow_ma_period': 21,
                'min_volume': 100000,
                'position_size': 1
            }),
            'is_active': kwargs.get('is_active', False)
        }
    
    def assert_order_equals(self, order1: Dict, order2: Dict):
        """Assert that two orders are equal."""
        self.assertEqual(order1['instrument_id'], order2['instrument_id'])
        self.assertEqual(order1['order_type'], order2['order_type'])
        self.assertEqual(order1['side'], order2['side'])
        self.assertEqual(order1['quantity'], order2['quantity'])
        if order1.get('price') is not None:
            self.assertEqual(order1['price'], order2['price'])
    
    def assert_position_equals(self, pos1: Dict, pos2: Dict):
        """Assert that two positions are equal."""
        self.assertEqual(pos1['instrument_id'], pos2['instrument_id'])
        self.assertEqual(pos1['quantity'], pos2['quantity'])
        self.assertEqual(pos1['side'], pos2['side'])
        self.assertAlmostEqual(pos1['entry_price'], pos2['entry_price'], places=2)
    
    def mock_market_data_feed(self, data: pd.DataFrame):
        """Create a mock market data feed."""
        mock_feed = MagicMock()
        mock_feed.get_historical_data.return_value = data
        return mock_feed
