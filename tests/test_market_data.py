"""
Unit tests for Market Data Manager and IIFL Client.
"""
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from tests.base_test import BaseTestCase
from core.market_data.market_data_manager import MarketDataManager
from core.market_data.iifl_client import IIFLClient

class TestMarketData(BaseTestCase):
    """Test suite for market data components."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.market_data_manager = MarketDataManager()
        self.iifl_client = IIFLClient()
        
        # Setup test data
        self.test_symbol = "RELIANCE"
        self.test_date = datetime(2025, 8, 16)
        
    async def test_iifl_client_connection(self):
        """Test IIFL client connection and authentication."""
        with patch.object(self.iifl_client, '_connect') as mock_connect:
            mock_connect.return_value = True
            
            connected = await self.iifl_client.connect()
            self.assertTrue(connected)
            
            # Test reconnection logic
            self.iifl_client._connected = False
            connected = await self.iifl_client.connect()
            self.assertTrue(connected)
            
    async def test_market_data_subscription(self):
        """Test market data subscription functionality."""
        test_symbols = ["RELIANCE", "TCS", "INFY"]
        
        with patch.object(self.iifl_client, 'subscribe') as mock_subscribe:
            mock_subscribe.return_value = True
            
            # Subscribe to multiple symbols
            success = await self.market_data_manager.subscribe_symbols(test_symbols)
            self.assertTrue(success)
            
            # Verify subscription status
            subscribed = self.market_data_manager.get_subscribed_symbols()
            self.assertEqual(set(subscribed), set(test_symbols))
            
    async def test_real_time_data_handling(self):
        """Test real-time market data handling."""
        test_tick = {
            'symbol': self.test_symbol,
            'last_price': 2500.0,
            'volume': 1000,
            'timestamp': self.test_date,
            'bid': 2499.0,
            'ask': 2501.0
        }
        
        # Test tick data processing
        with patch.object(self.market_data_manager, '_process_tick') as mock_process:
            await self.market_data_manager._on_tick_data(test_tick)
            mock_process.assert_called_once()
            
        # Verify data storage
        last_price = self.market_data_manager.get_last_price(self.test_symbol)
        self.assertEqual(last_price, test_tick['last_price'])
        
    async def test_historical_data_retrieval(self):
        """Test historical data retrieval and processing."""
        start_date = self.test_date - timedelta(days=30)
        end_date = self.test_date
        
        test_data = pd.DataFrame({
            'date': pd.date_range(start_date, end_date),
            'open': np.random.rand(31) * 100 + 2400,
            'high': np.random.rand(31) * 100 + 2450,
            'low': np.random.rand(31) * 100 + 2350,
            'close': np.random.rand(31) * 100 + 2400,
            'volume': np.random.randint(1000, 10000, 31)
        })
        
        with patch.object(self.iifl_client, 'get_historical_data') as mock_historical:
            mock_historical.return_value = test_data
            
            data = await self.market_data_manager.get_historical_data(
                self.test_symbol,
                start_date,
                end_date
            )
            
            self.assertIsNotNone(data)
            self.assertEqual(len(data), 31)
            self.assertTrue(all(col in data.columns 
                              for col in ['open', 'high', 'low', 'close', 'volume']))
            
    async def test_market_depth_handling(self):
        """Test market depth data handling."""
        test_depth = {
            'symbol': self.test_symbol,
            'bids': [(2499, 100), (2498, 200), (2497, 150)],
            'asks': [(2501, 120), (2502, 180), (2503, 140)]
        }
        
        with patch.object(self.market_data_manager, '_process_market_depth') as mock_process:
            await self.market_data_manager._on_market_depth(test_depth)
            mock_process.assert_called_once()
            
        # Verify market depth data
        depth = self.market_data_manager.get_market_depth(self.test_symbol)
        self.assertEqual(len(depth['bids']), 3)
        self.assertEqual(len(depth['asks']), 3)
        
    async def test_error_handling(self):
        """Test error handling in market data components."""
        # Test connection failure
        with patch.object(self.iifl_client, '_connect') as mock_connect:
            mock_connect.side_effect = Exception("Connection failed")
            
            with self.assertRaises(Exception):
                await self.iifl_client.connect()
                
        # Test subscription failure
        with patch.object(self.iifl_client, 'subscribe') as mock_subscribe:
            mock_subscribe.side_effect = Exception("Subscription failed")
            
            with self.assertRaises(Exception):
                await self.market_data_manager.subscribe_symbols([self.test_symbol])
                
    async def test_data_validation(self):
        """Test market data validation."""
        invalid_tick = {
            'symbol': self.test_symbol,
            'last_price': -100,  # Invalid negative price
            'volume': -50,  # Invalid negative volume
            'timestamp': self.test_date
        }
        
        # Verify invalid data handling
        with self.assertRaises(ValueError):
            await self.market_data_manager._validate_tick_data(invalid_tick)
            
    async def test_data_persistence(self):
        """Test market data persistence."""
        test_ticks = [
            {
                'symbol': self.test_symbol,
                'last_price': 2500.0 + i,
                'volume': 1000 + i,
                'timestamp': self.test_date + timedelta(seconds=i)
            }
            for i in range(10)
        ]
        
        # Test tick data storage
        for tick in test_ticks:
            await self.market_data_manager._process_tick(tick)
            
        # Verify data retrieval
        stored_data = self.market_data_manager.get_tick_history(self.test_symbol)
        self.assertEqual(len(stored_data), 10)
        
    async def test_reconnection_handling(self):
        """Test reconnection handling."""
        # Simulate disconnect
        self.iifl_client._connected = False
        
        with patch.object(self.iifl_client, '_connect') as mock_connect:
            mock_connect.return_value = True
            
            # Test auto-reconnect
            await self.market_data_manager._handle_disconnect()
            
            # Verify resubscription
            self.assertTrue(self.iifl_client._connected)
            mock_connect.assert_called_once()
            
    async def test_data_transformation(self):
        """Test market data transformation functions."""
        # Test OHLCV data aggregation
        test_ticks = [
            {'last_price': 100, 'volume': 10, 'timestamp': self.test_date},
            {'last_price': 102, 'volume': 20, 'timestamp': self.test_date},
            {'last_price': 98, 'volume': 15, 'timestamp': self.test_date},
            {'last_price': 101, 'volume': 25, 'timestamp': self.test_date}
        ]
        
        ohlcv = self.market_data_manager._aggregate_ticks_to_ohlcv(test_ticks)
        
        self.assertEqual(ohlcv['open'], 100)
        self.assertEqual(ohlcv['high'], 102)
        self.assertEqual(ohlcv['low'], 98)
        self.assertEqual(ohlcv['close'], 101)
        self.assertEqual(ohlcv['volume'], 70)

if __name__ == '__main__':
    unittest.main()
