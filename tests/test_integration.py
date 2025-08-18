"""
Integration tests for the Trading System.
Tests interactions between different components and end-to-end workflows.
"""
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import asyncio
import pandas as pd
import numpy as np

from tests.base_test import BaseTestCase
from core.market_data.market_data_manager import MarketDataManager
from execution.order_manager import OrderManager
from database.database_manager import DatabaseManager
from risk_management.risk_manager import RiskManager
from monitoring.safety_monitor import SafetyMonitor
from notifications.notification_manager import NotificationManager
from strategies.ma_crossover import MACrossoverStrategy
from web_interface.api import app

class TestSystemIntegration(BaseTestCase):
    """Integration test suite for the complete trading system."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        # Initialize all components
        self.market_data = MarketDataManager()
        self.order_manager = OrderManager()
        self.db_manager = DatabaseManager()
        self.risk_manager = RiskManager()
        self.safety_monitor = SafetyMonitor()
        self.notification_manager = NotificationManager()
        self.strategy = MACrossoverStrategy()
        
        self.test_symbol = "RELIANCE"
        self.test_date = datetime(2025, 8, 16)
        
    async def test_end_to_end_trading_workflow(self):
        """Test complete trading workflow from signal generation to execution."""
        # 1. Market Data Reception
        market_data = {
            'symbol': self.test_symbol,
            'timestamp': self.test_date,
            'price': 2500.0,
            'volume': 1000
        }
        
        with patch.object(self.market_data, 'get_last_price') as mock_price:
            mock_price.return_value = market_data['price']
            
            # 2. Strategy Signal Generation
            signal = await self.strategy.generate_signal(self.test_symbol)
            self.assertIn(signal['action'], ['BUY', 'SELL', 'HOLD'])
            
            if signal['action'] != 'HOLD':
                # 3. Risk Check
                risk_check = await self.risk_manager.validate_trade(
                    symbol=self.test_symbol,
                    quantity=100,
                    price=market_data['price']
                )
                self.assertTrue(risk_check['valid'])
                
                # 4. Order Execution
                order = {
                    'symbol': self.test_symbol,
                    'quantity': 100,
                    'side': signal['action'],
                    'order_type': 'MARKET',
                    'price': market_data['price']
                }
                
                execution_result = await self.order_manager.execute_order(order)
                self.assertTrue(execution_result['success'])
                
                # 5. Database Update
                trade_id = await self.db_manager.insert_trade({
                    'symbol': self.test_symbol,
                    'quantity': order['quantity'],
                    'price': execution_result['executed_price'],
                    'timestamp': self.test_date
                })
                self.assertIsNotNone(trade_id)
                
                # 6. Position Update
                position = await self.db_manager.get_position(self.test_symbol)
                self.assertIsNotNone(position)
                
    async def test_risk_monitoring_integration(self):
        """Test integration of risk monitoring with trading operations."""
        # 1. Set up initial position
        test_position = {
            'symbol': self.test_symbol,
            'quantity': 1000,
            'average_price': 2500.0
        }
        
        await self.db_manager.update_position(test_position)
        
        # 2. Monitor Risk Levels
        risk_metrics = await self.risk_manager.calculate_risk_metrics()
        
        # 3. Safety Monitor Check
        safety_status = await self.safety_monitor.check_risk_levels()
        
        if not safety_status['is_safe']:
            # 4. Generate Risk Alert
            alert = {
                'type': 'RISK_ALERT',
                'severity': 'HIGH',
                'message': 'Risk levels exceeded',
                'timestamp': self.test_date
            }
            
            # 5. Send Notification
            await self.notification_manager.dispatch_notification(alert)
            
            # 6. Verify Risk Management Action
            risk_action = await self.risk_manager.get_risk_mitigation_action()
            self.assertIn(risk_action['action'], ['REDUCE_POSITION', 'STOP_TRADING'])
            
    async def test_market_data_strategy_integration(self):
        """Test integration between market data and strategy components."""
        # 1. Set up historical data
        historical_data = pd.DataFrame({
            'timestamp': pd.date_range(start=self.test_date - timedelta(days=30),
                                     end=self.test_date),
            'close': np.random.randn(31).cumsum() + 2500
        })
        
        with patch.object(self.market_data, 'get_historical_data') as mock_history:
            mock_history.return_value = historical_data
            
            # 2. Strategy Initialization
            await self.strategy.initialize(self.test_symbol)
            
            # 3. Real-time Data Processing
            for i in range(10):
                tick_data = {
                    'symbol': self.test_symbol,
                    'price': 2500.0 + i,
                    'timestamp': self.test_date + timedelta(minutes=i)
                }
                
                # 4. Strategy Update
                await self.strategy.on_tick(tick_data)
                
                # 5. Signal Generation
                signal = await self.strategy.check_signals()
                
                if signal['action'] != 'HOLD':
                    # 6. Verify Signal
                    self.assertIn('confidence', signal)
                    self.assertGreater(signal['confidence'], 0)
                    
    async def test_execution_monitoring_integration(self):
        """Test integration between execution and monitoring components."""
        # 1. Create Test Order
        test_order = {
            'symbol': self.test_symbol,
            'quantity': 500,
            'side': 'BUY',
            'order_type': 'MARKET'
        }
        
        # 2. Pre-execution Monitoring
        system_status = await self.safety_monitor.check_system_health()
        self.assertTrue(system_status['is_healthy'])
        
        if system_status['is_healthy']:
            # 3. Order Execution
            execution_result = await self.order_manager.execute_order(test_order)
            
            # 4. Post-execution Monitoring
            execution_quality = await self.safety_monitor.analyze_execution_quality(
                test_order,
                execution_result
            )
            
            # 5. Performance Metrics Update
            await self.db_manager.update_execution_metrics(execution_quality)
            
            # 6. Notification if needed
            if not execution_quality['within_expected_range']:
                await self.notification_manager.send_execution_alert(execution_quality)
                
    async def test_database_monitoring_integration(self):
        """Test integration between database and monitoring components."""
        # 1. Database Health Check
        db_status = await self.safety_monitor.check_database_health()
        self.assertTrue(db_status['is_healthy'])
        
        # 2. Data Consistency Check
        trades = await self.db_manager.get_recent_trades()
        positions = await self.db_manager.get_all_positions()
        
        consistency_check = await self.safety_monitor.verify_data_consistency(
            trades,
            positions
        )
        self.assertTrue(consistency_check['is_consistent'])
        
        # 3. Performance Metrics Calculation
        metrics = await self.db_manager.calculate_performance_metrics()
        
        # 4. Monitoring Update
        await self.safety_monitor.update_system_metrics(metrics)
        
    async def test_web_interface_integration(self):
        """Test integration between web interface and other components."""
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # 1. Authentication
        login_response = client.post('/api/auth/login', json={
            'username': 'test_user',
            'password': 'test_password'
        })
        self.assertEqual(login_response.status_code, 200)
        token = login_response.json()['access_token']
        
        # 2. Dashboard Data Integration
        headers = {'Authorization': f'Bearer {token}'}
        
        # Test positions endpoint
        positions_response = client.get('/api/positions', headers=headers)
        self.assertEqual(positions_response.status_code, 200)
        
        # Test performance endpoint
        performance_response = client.get('/api/performance', headers=headers)
        self.assertEqual(performance_response.status_code, 200)
        
        # 3. Real-time Updates
        with client.websocket_connect('/ws/market-data') as websocket:
            # Send test market data
            test_data = {
                'symbol': self.test_symbol,
                'price': 2500.0,
                'timestamp': self.test_date.isoformat()
            }
            websocket.send_json(test_data)
            
            # Receive updates
            response = websocket.receive_json()
            self.assertEqual(response['symbol'], test_data['symbol'])
            
    async def test_recovery_workflow_integration(self):
        """Test system recovery workflow across components."""
        # 1. Simulate System Error
        error_condition = {
            'type': 'SYSTEM_ERROR',
            'component': 'MARKET_DATA',
            'severity': 'HIGH'
        }
        
        # 2. Error Detection
        await self.safety_monitor.handle_system_error(error_condition)
        
        # 3. Recovery Process
        recovery_steps = [
            'stop_trading',
            'reconcile_positions',
            'restart_market_data',
            'verify_system_state'
        ]
        
        for step in recovery_steps:
            status = await self.safety_monitor.execute_recovery_step(step)
            self.assertTrue(status['success'])
            
        # 4. System Verification
        system_status = await self.safety_monitor.verify_system_state()
        self.assertTrue(system_status['ready_for_trading'])
        
        # 5. Trading Resume
        if system_status['ready_for_trading']:
            await self.notification_manager.send_system_status_update('TRADING_RESUMED')
            
    async def test_risk_execution_integration(self):
        """Test integration between risk management and execution components."""
        # 1. Initial Risk Check
        risk_limits = await self.risk_manager.get_current_limits()
        
        # 2. Create Test Order
        test_order = {
            'symbol': self.test_symbol,
            'quantity': risk_limits['max_position_size'] - 100,
            'side': 'BUY',
            'order_type': 'MARKET'
        }
        
        # 3. Pre-trade Risk Check
        risk_check = await self.risk_manager.validate_order(test_order)
        
        if risk_check['valid']:
            # 4. Order Execution
            execution_result = await self.order_manager.execute_order(test_order)
            
            # 5. Post-trade Risk Update
            await self.risk_manager.update_risk_metrics(execution_result)
            
            # 6. Position Monitoring
            position = await self.db_manager.get_position(self.test_symbol)
            await self.risk_manager.monitor_position_risk(position)

if __name__ == '__main__':
    unittest.main()
