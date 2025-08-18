"""
Unit tests for Order Manager and Slippage Analyzer components.
"""
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from tests.base_test import BaseTestCase
from execution.order_manager import OrderManager
from execution.slippage_analyzer import SlippageAnalyzer
from core.market_data.market_data_manager import MarketDataManager

class TestExecution(BaseTestCase):
    """Test suite for execution components."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.order_manager = OrderManager()
        self.slippage_analyzer = SlippageAnalyzer()
        self.market_data_manager = MarketDataManager()
        
        # Setup test data
        self.test_symbol = "RELIANCE"
        self.test_date = datetime(2025, 8, 16)
        
    async def test_market_order_execution(self):
        """Test market order execution."""
        # Create test market order
        market_order = {
            'symbol': self.test_symbol,
            'quantity': 100,
            'side': 'BUY',
            'order_type': 'MARKET',
            'strategy_id': 1
        }
        
        # Mock market data
        with patch.object(self.market_data_manager, 'get_last_price') as mock_price:
            mock_price.return_value = 2500.0
            
            # Execute order
            result = await self.order_manager.execute_order(market_order)
            
            self.assertTrue(result['success'])
            self.assertEqual(result['executed_quantity'], market_order['quantity'])
            self.assertIsNotNone(result['execution_time'])
            
    async def test_limit_order_execution(self):
        """Test limit order execution."""
        # Create test limit order
        limit_order = {
            'symbol': self.test_symbol,
            'quantity': 100,
            'side': 'BUY',
            'order_type': 'LIMIT',
            'limit_price': 2500.0,
            'strategy_id': 1
        }
        
        # Mock market data
        with patch.object(self.market_data_manager, 'get_last_price') as mock_price:
            # Price above limit - should not execute
            mock_price.return_value = 2550.0
            result = await self.order_manager.execute_order(limit_order)
            self.assertFalse(result['success'])
            
            # Price at limit - should execute
            mock_price.return_value = 2500.0
            result = await self.order_manager.execute_order(limit_order)
            self.assertTrue(result['success'])
            
    async def test_stop_order_execution(self):
        """Test stop order execution."""
        # Create test stop order
        stop_order = {
            'symbol': self.test_symbol,
            'quantity': 100,
            'side': 'SELL',
            'order_type': 'STOP',
            'stop_price': 2450.0,
            'strategy_id': 1
        }
        
        # Mock market data
        with patch.object(self.market_data_manager, 'get_last_price') as mock_price:
            # Price above stop - should not execute
            mock_price.return_value = 2500.0
            result = await self.order_manager.execute_order(stop_order)
            self.assertFalse(result['success'])
            
            # Price at stop - should execute
            mock_price.return_value = 2450.0
            result = await self.order_manager.execute_order(stop_order)
            self.assertTrue(result['success'])
            
    async def test_order_slippage_calculation(self):
        """Test order slippage calculation."""
        test_order = {
            'symbol': self.test_symbol,
            'quantity': 1000,  # Large order to test slippage
            'side': 'BUY',
            'order_type': 'MARKET'
        }
        
        market_depth = {
            'bids': [(2499, 100), (2498, 200), (2497, 300)],
            'asks': [(2501, 150), (2502, 250), (2503, 350)]
        }
        
        with patch.object(self.market_data_manager, 'get_market_depth') as mock_depth:
            mock_depth.return_value = market_depth
            
            slippage = await self.slippage_analyzer.calculate_slippage(test_order)
            
            self.assertGreater(slippage, 0)
            self.assertLess(slippage, 10)  # Reasonable slippage range
            
    async def test_order_sizing(self):
        """Test order sizing based on market liquidity."""
        volume_profile = pd.DataFrame({
            'timestamp': pd.date_range(self.test_date - timedelta(days=30), self.test_date),
            'volume': np.random.randint(10000, 100000, 31)
        })
        
        with patch.object(self.market_data_manager, 'get_volume_profile') as mock_volume:
            mock_volume.return_value = volume_profile
            
            max_size = await self.order_manager.calculate_max_order_size(
                self.test_symbol,
                'BUY'
            )
            
            self.assertGreater(max_size, 0)
            self.assertLess(max_size, volume_profile['volume'].mean() * 0.1)
            
    async def test_order_splitting(self):
        """Test large order splitting into smaller chunks."""
        large_order = {
            'symbol': self.test_symbol,
            'quantity': 10000,
            'side': 'BUY',
            'order_type': 'MARKET'
        }
        
        child_orders = await self.order_manager.split_large_order(large_order)
        
        self.assertGreater(len(child_orders), 1)
        self.assertEqual(sum(order['quantity'] for order in child_orders),
                        large_order['quantity'])
        
    async def test_execution_strategy(self):
        """Test different execution strategies."""
        test_order = {
            'symbol': self.test_symbol,
            'quantity': 5000,
            'side': 'BUY',
            'order_type': 'MARKET',
            'execution_strategy': 'TWAP'
        }
        
        # Test TWAP execution
        execution_plan = await self.order_manager.create_execution_plan(test_order)
        
        self.assertEqual(len(execution_plan), 5)  # Default 5 chunks for TWAP
        self.assertEqual(sum(order['quantity'] for order in execution_plan),
                        test_order['quantity'])
        
    async def test_market_impact(self):
        """Test market impact calculation."""
        test_order = {
            'symbol': self.test_symbol,
            'quantity': 5000,
            'side': 'BUY',
            'order_type': 'MARKET'
        }
        
        volume_profile = pd.DataFrame({
            'timestamp': pd.date_range(self.test_date - timedelta(days=30), self.test_date),
            'volume': np.random.randint(10000, 100000, 31)
        })
        
        with patch.object(self.market_data_manager, 'get_volume_profile') as mock_volume:
            mock_volume.return_value = volume_profile
            
            impact = await self.slippage_analyzer.calculate_market_impact(test_order)
            
            self.assertGreater(impact, 0)
            self.assertLess(impact, 1.0)  # Impact should be less than 100%
            
    async def test_execution_cost_analysis(self):
        """Test execution cost analysis."""
        executed_order = {
            'symbol': self.test_symbol,
            'quantity': 1000,
            'side': 'BUY',
            'order_type': 'MARKET',
            'intended_price': 2500.0,
            'executed_price': 2502.5
        }
        
        costs = await self.slippage_analyzer.analyze_execution_costs(executed_order)
        
        self.assertIsNotNone(costs['slippage_cost'])
        self.assertIsNotNone(costs['impact_cost'])
        self.assertIsNotNone(costs['timing_cost'])
        
    async def test_smart_order_routing(self):
        """Test smart order routing logic."""
        test_order = {
            'symbol': self.test_symbol,
            'quantity': 1000,
            'side': 'BUY',
            'order_type': 'MARKET'
        }
        
        # Mock multiple venue data
        venue_data = {
            'venue1': {'price': 2500.0, 'liquidity': 5000},
            'venue2': {'price': 2501.0, 'liquidity': 8000},
            'venue3': {'price': 2499.5, 'liquidity': 3000}
        }
        
        with patch.object(self.order_manager, '_get_venue_data') as mock_venues:
            mock_venues.return_value = venue_data
            
            routing = await self.order_manager.route_order(test_order)
            
            self.assertEqual(routing['primary_venue'], 'venue3')  # Best price
            self.assertGreater(len(routing['backup_venues']), 0)
            
    async def test_execution_reporting(self):
        """Test execution reporting functionality."""
        # Create test execution data
        executions = [
            {
                'symbol': self.test_symbol,
                'quantity': 100,
                'price': 2500.0,
                'time': self.test_date,
                'side': 'BUY'
            },
            {
                'symbol': self.test_symbol,
                'quantity': 50,
                'price': 2502.0,
                'time': self.test_date + timedelta(minutes=5),
                'side': 'BUY'
            }
        ]
        
        report = await self.order_manager.generate_execution_report(executions)
        
        self.assertIsNotNone(report['vwap'])
        self.assertIsNotNone(report['implementation_shortfall'])
        self.assertIsNotNone(report['timing_analysis'])

if __name__ == '__main__':
    unittest.main()
