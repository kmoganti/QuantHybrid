"""
Performance tests for the Trading System.
Tests system behavior under various load conditions and performance scenarios.
"""
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import asyncio
import time
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import psutil
import logging

from tests.base_test import BaseTestCase
from core.market_data.market_data_manager import MarketDataManager
from execution.order_manager import OrderManager
from database.database_manager import DatabaseManager
from risk_management.risk_manager import RiskManager
from monitoring.safety_monitor import SafetyMonitor
from strategies.ma_crossover import MACrossoverStrategy
from web_interface.api import app
from fastapi.testclient import TestClient

class TestSystemPerformance(BaseTestCase):
    """Performance test suite for the trading system."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.market_data = MarketDataManager()
        self.order_manager = OrderManager()
        self.db_manager = DatabaseManager()
        self.risk_manager = RiskManager()
        self.strategy = MACrossoverStrategy()
        self.client = TestClient(app)
        
        # Setup performance monitoring
        self.logger = logging.getLogger('performance_tests')
        self.test_start_time = datetime.now()
        
    def measure_execution_time(self, func):
        """Decorator to measure function execution time."""
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            result = await func(*args, **kwargs)
            end_time = time.time()
            execution_time = end_time - start_time
            self.logger.info(f"{func.__name__} execution time: {execution_time:.4f} seconds")
            return result, execution_time
        return wrapper
        
    async def test_market_data_throughput(self):
        """Test market data processing throughput."""
        num_ticks = 10000
        symbols = ['RELIANCE', 'TCS', 'INFY', 'HDFC', 'ICICI']
        
        @self.measure_execution_time
        async def process_market_data(ticks):
            for tick in ticks:
                await self.market_data._process_tick(tick)
                
        # Generate test ticks
        test_ticks = [
            {
                'symbol': symbols[i % len(symbols)],
                'price': 1000 + (i % 100),
                'volume': 100 + i,
                'timestamp': datetime.now() + timedelta(microseconds=i)
            }
            for i in range(num_ticks)
        ]
        
        # Measure processing time
        result, execution_time = await process_market_data(test_ticks)
        
        # Calculate throughput
        throughput = num_ticks / execution_time
        self.logger.info(f"Market data throughput: {throughput:.2f} ticks/second")
        
        # Verify processing under load
        self.assertGreater(throughput, 1000)  # Minimum expected throughput
        
    async def test_order_execution_latency(self):
        """Test order execution latency under load."""
        num_orders = 1000
        
        @self.measure_execution_time
        async def execute_orders(orders):
            tasks = [self.order_manager.execute_order(order) for order in orders]
            return await asyncio.gather(*tasks)
            
        # Generate test orders
        test_orders = [
            {
                'symbol': 'RELIANCE',
                'quantity': 100,
                'side': 'BUY' if i % 2 == 0 else 'SELL',
                'order_type': 'MARKET',
                'price': 1000 + i
            }
            for i in range(num_orders)
        ]
        
        # Measure execution time
        results, execution_time = await execute_orders(test_orders)
        
        # Calculate average latency
        avg_latency = execution_time / num_orders * 1000  # in milliseconds
        self.logger.info(f"Average order execution latency: {avg_latency:.2f} ms")
        
        # Verify latency requirements
        self.assertLess(avg_latency, 50)  # Maximum acceptable latency
        
    async def test_database_performance(self):
        """Test database performance under load."""
        num_operations = 5000
        
        @self.measure_execution_time
        async def perform_db_operations(operations):
            for op in operations:
                if op['type'] == 'insert':
                    await self.db_manager.insert_trade(op['data'])
                else:
                    await self.db_manager.get_trade(op['id'])
                    
        # Generate test operations
        test_operations = []
        for i in range(num_operations):
            if i % 2 == 0:
                # Insert operation
                test_operations.append({
                    'type': 'insert',
                    'data': {
                        'symbol': 'RELIANCE',
                        'quantity': 100,
                        'price': 1000 + i,
                        'timestamp': datetime.now()
                    }
                })
            else:
                # Read operation
                test_operations.append({
                    'type': 'read',
                    'id': i // 2
                })
                
        # Measure database performance
        result, execution_time = await perform_db_operations(test_operations)
        
        # Calculate operations per second
        ops_per_second = num_operations / execution_time
        self.logger.info(f"Database operations per second: {ops_per_second:.2f}")
        
        # Verify database performance
        self.assertGreater(ops_per_second, 1000)  # Minimum expected throughput
        
    async def test_strategy_calculation_performance(self):
        """Test strategy calculation performance with large datasets."""
        num_candles = 10000
        
        @self.measure_execution_time
        async def run_strategy_calculations(data):
            return await self.strategy.calculate_signals(data)
            
        # Generate test data
        test_data = pd.DataFrame({
            'timestamp': pd.date_range(start=datetime.now(), periods=num_candles, freq='1min'),
            'close': np.random.randn(num_candles).cumsum() + 1000,
            'volume': np.random.randint(100, 1000, num_candles)
        })
        
        # Measure calculation time
        results, execution_time = await run_strategy_calculations(test_data)
        
        # Calculate processing rate
        candles_per_second = num_candles / execution_time
        self.logger.info(f"Strategy calculation rate: {candles_per_second:.2f} candles/second")
        
        # Verify calculation performance
        self.assertGreater(candles_per_second, 5000)  # Minimum expected rate
        
    async def test_system_memory_usage(self):
        """Test system memory usage under load."""
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # Generate load
        large_data = pd.DataFrame({
            'timestamp': pd.date_range(start=datetime.now(), periods=100000, freq='1min'),
            'close': np.random.randn(100000).cumsum(),
            'volume': np.random.randint(100, 1000, 100000)
        })
        
        await self.strategy.initialize(large_data)
        
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        self.logger.info(f"Memory usage increase: {memory_increase:.2f} MB")
        self.assertLess(memory_increase, 1000)  # Maximum acceptable memory increase
        
    async def test_concurrent_user_load(self):
        """Test system performance under concurrent user load."""
        num_users = 100
        requests_per_user = 50
        
        @self.measure_execution_time
        async def simulate_user_requests():
            async def user_session():
                for _ in range(requests_per_user):
                    response = self.client.get('/api/dashboard/summary')
                    self.assertEqual(response.status_code, 200)
                    
            tasks = [user_session() for _ in range(num_users)]
            await asyncio.gather(*tasks)
            
        # Measure concurrent user performance
        result, execution_time = await simulate_user_requests()
        
        # Calculate requests per second
        total_requests = num_users * requests_per_user
        requests_per_second = total_requests / execution_time
        
        self.logger.info(f"API requests per second: {requests_per_second:.2f}")
        self.assertGreater(requests_per_second, 1000)  # Minimum expected throughput
        
    async def test_real_time_processing_pipeline(self):
        """Test end-to-end real-time processing pipeline performance."""
        num_events = 5000
        
        @self.measure_execution_time
        async def process_event_pipeline(event):
            # 1. Market data processing
            await self.market_data._process_tick(event)
            
            # 2. Strategy calculation
            signal = await self.strategy.generate_signal(event['symbol'])
            
            # 3. Risk check
            if signal['action'] != 'HOLD':
                risk_check = await self.risk_manager.validate_trade(
                    symbol=event['symbol'],
                    quantity=100,
                    price=event['price']
                )
                
                # 4. Order execution if approved
                if risk_check['valid']:
                    order = {
                        'symbol': event['symbol'],
                        'quantity': 100,
                        'side': signal['action'],
                        'order_type': 'MARKET',
                        'price': event['price']
                    }
                    await self.order_manager.execute_order(order)
                    
        # Generate test events
        test_events = [
            {
                'symbol': 'RELIANCE',
                'price': 1000 + (i % 100),
                'volume': 100 + i,
                'timestamp': datetime.now() + timedelta(microseconds=i)
            }
            for i in range(num_events)
        ]
        
        # Measure pipeline performance
        total_execution_time = 0
        for event in test_events:
            result, execution_time = await process_event_pipeline(event)
            total_execution_time += execution_time
            
        # Calculate average processing time
        avg_processing_time = total_execution_time / num_events * 1000  # in milliseconds
        self.logger.info(f"Average event processing time: {avg_processing_time:.2f} ms")
        
        # Verify processing time requirements
        self.assertLess(avg_processing_time, 10)  # Maximum acceptable processing time
        
    async def test_system_recovery_performance(self):
        """Test system recovery performance after simulated failure."""
        @self.measure_execution_time
        async def perform_recovery():
            # 1. Stop all operations
            await self.order_manager.stop_all_operations()
            
            # 2. Verify database consistency
            await self.db_manager.verify_consistency()
            
            # 3. Reconcile positions
            await self.risk_manager.reconcile_positions()
            
            # 4. Restart market data
            await self.market_data.reconnect()
            
            # 5. Resume operations
            await self.order_manager.resume_operations()
            
        # Measure recovery time
        result, recovery_time = await perform_recovery()
        
        self.logger.info(f"System recovery time: {recovery_time:.2f} seconds")
        self.assertLess(recovery_time, 30)  # Maximum acceptable recovery time

if __name__ == '__main__':
    unittest.main()
