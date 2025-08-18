"""
Unit tests for Database Manager and Database Models.
"""
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import sqlite3
import pandas as pd

from tests.base_test import BaseTestCase
from database.database_manager import DatabaseManager
from database.models import Trade, Position, Order, Strategy, Account

class TestDatabase(BaseTestCase):
    """Test suite for database components."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.db_manager = DatabaseManager()
        self.test_date = datetime(2025, 8, 16)
        
        # Create test database in memory
        self.db_manager.connection_string = ":memory:"
        self.db_manager.initialize_database()
        
    def tearDown(self):
        """Clean up test environment."""
        self.db_manager.close_connection()
        super().tearDown()
        
    async def test_database_initialization(self):
        """Test database initialization and schema creation."""
        # Verify all tables are created
        tables = await self.db_manager.get_all_tables()
        expected_tables = ['trades', 'positions', 'orders', 'strategies', 'accounts']
        
        for table in expected_tables:
            self.assertIn(table, tables)
            
        # Verify table schemas
        schema = await self.db_manager.get_table_schema('trades')
        required_columns = ['id', 'symbol', 'entry_price', 'exit_price', 'quantity']
        for column in required_columns:
            self.assertIn(column, schema)
            
    async def test_trade_operations(self):
        """Test trade-related database operations."""
        # Create test trade
        test_trade = Trade(
            symbol='RELIANCE',
            entry_price=2500.0,
            exit_price=2550.0,
            quantity=100,
            entry_time=self.test_date,
            exit_time=self.test_date + timedelta(hours=1),
            strategy_id=1,
            pnl=5000.0
        )
        
        # Test insert
        trade_id = await self.db_manager.insert_trade(test_trade)
        self.assertIsNotNone(trade_id)
        
        # Test retrieve
        stored_trade = await self.db_manager.get_trade(trade_id)
        self.assertEqual(stored_trade.symbol, test_trade.symbol)
        self.assertEqual(stored_trade.quantity, test_trade.quantity)
        
        # Test update
        stored_trade.exit_price = 2560.0
        await self.db_manager.update_trade(stored_trade)
        updated_trade = await self.db_manager.get_trade(trade_id)
        self.assertEqual(updated_trade.exit_price, 2560.0)
        
    async def test_position_tracking(self):
        """Test position tracking in database."""
        # Create test position
        test_position = Position(
            symbol='TCS',
            quantity=500,
            average_price=3500.0,
            current_price=3550.0,
            unrealized_pnl=25000.0,
            strategy_id=1
        )
        
        # Test position insert
        position_id = await self.db_manager.insert_position(test_position)
        self.assertIsNotNone(position_id)
        
        # Test position update
        test_position.quantity += 100
        test_position.average_price = 3520.0
        await self.db_manager.update_position(test_position)
        
        # Verify position
        stored_position = await self.db_manager.get_position('TCS')
        self.assertEqual(stored_position.quantity, 600)
        self.assertEqual(stored_position.average_price, 3520.0)
        
    async def test_order_management(self):
        """Test order management in database."""
        # Create test order
        test_order = Order(
            symbol='INFY',
            quantity=200,
            price=1500.0,
            order_type='MARKET',
            side='BUY',
            status='PENDING',
            strategy_id=1
        )
        
        # Test order insert
        order_id = await self.db_manager.insert_order(test_order)
        self.assertIsNotNone(order_id)
        
        # Test order status update
        await self.db_manager.update_order_status(order_id, 'EXECUTED')
        stored_order = await self.db_manager.get_order(order_id)
        self.assertEqual(stored_order.status, 'EXECUTED')
        
    async def test_strategy_persistence(self):
        """Test strategy persistence in database."""
        # Create test strategy
        test_strategy = Strategy(
            name='MA_Crossover',
            parameters={'short_window': 10, 'long_window': 30},
            status='ACTIVE',
            capital_allocated=1000000.0
        )
        
        # Test strategy insert
        strategy_id = await self.db_manager.insert_strategy(test_strategy)
        self.assertIsNotNone(strategy_id)
        
        # Test strategy retrieval
        stored_strategy = await self.db_manager.get_strategy(strategy_id)
        self.assertEqual(stored_strategy.name, test_strategy.name)
        self.assertEqual(stored_strategy.parameters, test_strategy.parameters)
        
    async def test_account_management(self):
        """Test account management in database."""
        # Create test account
        test_account = Account(
            balance=10000000.0,
            equity=10500000.0,
            margin_used=2000000.0,
            free_margin=8000000.0
        )
        
        # Test account insert
        account_id = await self.db_manager.insert_account(test_account)
        self.assertIsNotNone(account_id)
        
        # Test account update
        test_account.equity += 50000.0
        await self.db_manager.update_account(test_account)
        
        # Verify account
        stored_account = await self.db_manager.get_account(account_id)
        self.assertEqual(stored_account.equity, 10550000.0)
        
    async def test_performance_metrics(self):
        """Test performance metrics calculation and storage."""
        # Insert test trades
        test_trades = [
            Trade(symbol='RELIANCE', entry_price=2500, exit_price=2550, quantity=100,
                  entry_time=self.test_date, exit_time=self.test_date + timedelta(hours=1),
                  strategy_id=1, pnl=5000.0),
            Trade(symbol='TCS', entry_price=3500, exit_price=3450, quantity=50,
                  entry_time=self.test_date, exit_time=self.test_date + timedelta(hours=2),
                  strategy_id=1, pnl=-2500.0)
        ]
        
        for trade in test_trades:
            await self.db_manager.insert_trade(trade)
            
        # Calculate metrics
        metrics = await self.db_manager.calculate_performance_metrics(strategy_id=1)
        
        self.assertIsNotNone(metrics['total_pnl'])
        self.assertIsNotNone(metrics['win_rate'])
        self.assertIsNotNone(metrics['average_win'])
        self.assertIsNotNone(metrics['average_loss'])
        
    async def test_data_integrity(self):
        """Test database data integrity constraints."""
        # Test duplicate prevention
        test_strategy = Strategy(
            name='MA_Crossover',
            parameters={'short_window': 10, 'long_window': 30},
            status='ACTIVE'
        )
        
        strategy_id = await self.db_manager.insert_strategy(test_strategy)
        
        # Attempt to insert duplicate strategy
        with self.assertRaises(sqlite3.IntegrityError):
            await self.db_manager.insert_strategy(test_strategy)
            
    async def test_transaction_management(self):
        """Test transaction management."""
        # Start transaction
        async with self.db_manager.transaction():
            # Create test position and order
            position = Position(symbol='WIPRO', quantity=300, average_price=400.0)
            order = Order(symbol='WIPRO', quantity=100, price=410.0, side='BUY')
            
            position_id = await self.db_manager.insert_position(position)
            order_id = await self.db_manager.insert_order(order)
            
            # Verify both inserts succeeded
            self.assertIsNotNone(position_id)
            self.assertIsNotNone(order_id)
            
        # Test transaction rollback
        try:
            async with self.db_manager.transaction():
                # This should succeed
                await self.db_manager.insert_position(position)
                # This should fail and trigger rollback
                raise Exception("Simulated error")
        except:
            # Verify position was not inserted due to rollback
            stored_position = await self.db_manager.get_position('WIPRO')
            self.assertEqual(stored_position.quantity, 300)  # Original quantity

    async def test_query_optimization(self):
        """Test query optimization and indexing."""
        # Insert bulk test data
        test_trades = [
            Trade(
                symbol=f'STOCK{i}',
                entry_price=1000 + i,
                exit_price=1050 + i,
                quantity=100,
                entry_time=self.test_date + timedelta(hours=i),
                strategy_id=1
            )
            for i in range(1000)
        ]
        
        for trade in test_trades:
            await self.db_manager.insert_trade(trade)
            
        # Test indexed query performance
        start_time = datetime.now()
        trades = await self.db_manager.get_trades_by_symbol('STOCK500')
        query_time = datetime.now() - start_time
        
        self.assertLess(query_time.total_seconds(), 0.1)  # Should be fast with index
        self.assertEqual(len(trades), 1)

if __name__ == '__main__':
    unittest.main()
