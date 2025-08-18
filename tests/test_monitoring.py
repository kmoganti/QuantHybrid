"""
Unit tests for Monitoring System and Notification components.
"""
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import asyncio

from tests.base_test import BaseTestCase
from monitoring.safety_monitor import SafetyMonitor
from notifications.notification_manager import NotificationManager
from database.models import Trade, Position, Account

class TestMonitoring(BaseTestCase):
    """Test suite for monitoring and notification components."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.safety_monitor = SafetyMonitor()
        self.notification_manager = NotificationManager()
        self.test_date = datetime(2025, 8, 16)
        
    async def test_system_health_check(self):
        """Test system health monitoring."""
        # Mock system metrics
        system_metrics = {
            'cpu_usage': 45.0,
            'memory_usage': 60.0,
            'disk_usage': 55.0,
            'network_latency': 15.0
        }
        
        with patch.object(self.safety_monitor, '_get_system_metrics') as mock_metrics:
            mock_metrics.return_value = system_metrics
            
            health_status = await self.safety_monitor.check_system_health()
            
            self.assertTrue(health_status['is_healthy'])
            self.assertIsNotNone(health_status['metrics'])
            
        # Test unhealthy system
        system_metrics['cpu_usage'] = 95.0  # High CPU usage
        with patch.object(self.safety_monitor, '_get_system_metrics') as mock_metrics:
            mock_metrics.return_value = system_metrics
            
            health_status = await self.safety_monitor.check_system_health()
            
            self.assertFalse(health_status['is_healthy'])
            self.assertEqual(health_status['alerts'][0]['type'], 'HIGH_CPU_USAGE')
            
    async def test_market_data_quality(self):
        """Test market data quality monitoring."""
        # Mock market data metrics
        market_data = {
            'timestamp': self.test_date,
            'symbol': 'RELIANCE',
            'price': 2500.0,
            'bid': 2499.0,
            'ask': 2501.0,
            'volume': 1000
        }
        
        # Test normal data
        quality_check = await self.safety_monitor.check_market_data_quality(market_data)
        self.assertTrue(quality_check['is_valid'])
        
        # Test stale data
        stale_data = market_data.copy()
        stale_data['timestamp'] = self.test_date - timedelta(minutes=10)
        quality_check = await self.safety_monitor.check_market_data_quality(stale_data)
        self.assertFalse(quality_check['is_valid'])
        self.assertEqual(quality_check['issues'][0], 'STALE_DATA')
        
    async def test_position_monitoring(self):
        """Test position monitoring."""
        # Mock position data
        test_positions = [
            Position(symbol='RELIANCE', quantity=1000, average_price=2500.0),
            Position(symbol='TCS', quantity=500, average_price=3500.0)
        ]
        
        with patch.object(self.safety_monitor, '_get_current_positions') as mock_positions:
            mock_positions.return_value = test_positions
            
            # Test position limits
            position_check = await self.safety_monitor.check_position_limits()
            self.assertTrue(position_check['within_limits'])
            
            # Test large position
            test_positions.append(
                Position(symbol='INFY', quantity=10000, average_price=1500.0)
            )
            position_check = await self.safety_monitor.check_position_limits()
            self.assertFalse(position_check['within_limits'])
            
    async def test_drawdown_monitoring(self):
        """Test drawdown monitoring."""
        # Mock account data
        account_history = [
            {'equity': 10000000.0, 'timestamp': self.test_date - timedelta(days=i)}
            for i in range(10)
        ]
        
        # Simulate drawdown
        account_history[0]['equity'] = 9000000.0  # 10% drawdown
        
        with patch.object(self.safety_monitor, '_get_account_history') as mock_history:
            mock_history.return_value = account_history
            
            drawdown = await self.safety_monitor.calculate_drawdown()
            self.assertEqual(drawdown, -0.10)
            
            # Test drawdown alert
            alert = await self.safety_monitor.check_drawdown_limits()
            self.assertTrue(alert['alert_triggered'])
            
    async def test_trading_activity_monitoring(self):
        """Test trading activity monitoring."""
        # Mock trade data
        test_trades = [
            Trade(
                symbol='RELIANCE',
                quantity=100,
                price=2500.0,
                timestamp=self.test_date - timedelta(seconds=i*30)
            )
            for i in range(20)  # 20 trades in 10 minutes
        ]
        
        with patch.object(self.safety_monitor, '_get_recent_trades') as mock_trades:
            mock_trades.return_value = test_trades
            
            # Test trading frequency
            activity = await self.safety_monitor.check_trading_activity()
            self.assertTrue(activity['high_frequency'])
            self.assertGreater(activity['trades_per_minute'], 1)
            
    async def test_risk_metrics_monitoring(self):
        """Test risk metrics monitoring."""
        # Mock risk metrics
        risk_metrics = {
            'var': 0.02,
            'leverage': 2.0,
            'concentration': 0.25,
            'correlation': 0.7
        }
        
        with patch.object(self.safety_monitor, '_calculate_risk_metrics') as mock_risk:
            mock_risk.return_value = risk_metrics
            
            # Test risk levels
            risk_status = await self.safety_monitor.check_risk_levels()
            self.assertEqual(risk_status['risk_level'], 'MEDIUM')
            self.assertFalse(risk_status['risk_exceeded'])
            
            # Test high risk scenario
            risk_metrics['leverage'] = 5.0
            risk_status = await self.safety_monitor.check_risk_levels()
            self.assertEqual(risk_status['risk_level'], 'HIGH')
            self.assertTrue(risk_status['risk_exceeded'])
            
    async def test_notification_dispatch(self):
        """Test notification dispatch system."""
        # Test different notification types
        notifications = [
            {
                'type': 'RISK_ALERT',
                'severity': 'HIGH',
                'message': 'High leverage detected',
                'timestamp': self.test_date
            },
            {
                'type': 'SYSTEM_ALERT',
                'severity': 'MEDIUM',
                'message': 'High CPU usage',
                'timestamp': self.test_date
            }
        ]
        
        for notification in notifications:
            with patch.object(self.notification_manager, '_send_notification') as mock_send:
                await self.notification_manager.dispatch_notification(notification)
                mock_send.assert_called_once()
                
    async def test_notification_channels(self):
        """Test different notification channels."""
        test_alert = {
            'type': 'RISK_ALERT',
            'severity': 'HIGH',
            'message': 'Position limit exceeded',
            'timestamp': self.test_date
        }
        
        # Test email notifications
        with patch.object(self.notification_manager, '_send_email') as mock_email:
            await self.notification_manager.send_email_alert(test_alert)
            mock_email.assert_called_once()
            
        # Test SMS notifications
        with patch.object(self.notification_manager, '_send_sms') as mock_sms:
            await self.notification_manager.send_sms_alert(test_alert)
            mock_sms.assert_called_once()
            
    async def test_alert_aggregation(self):
        """Test alert aggregation logic."""
        # Generate multiple similar alerts
        alerts = [
            {
                'type': 'SYSTEM_ALERT',
                'severity': 'MEDIUM',
                'message': 'High CPU usage',
                'timestamp': self.test_date + timedelta(seconds=i*30)
            }
            for i in range(5)
        ]
        
        # Test aggregation
        aggregated = await self.notification_manager.aggregate_alerts(alerts)
        self.assertLess(len(aggregated), len(alerts))
        self.assertTrue(any('multiple occurrences' in alert['message'] 
                          for alert in aggregated))
        
    async def test_notification_throttling(self):
        """Test notification throttling."""
        test_alert = {
            'type': 'MARKET_ALERT',
            'severity': 'LOW',
            'message': 'Price spike detected',
            'timestamp': self.test_date
        }
        
        # Send multiple alerts rapidly
        for _ in range(10):
            await self.notification_manager.dispatch_notification(test_alert)
            
        # Verify throttling
        throttle_status = self.notification_manager.check_throttle_status('MARKET_ALERT')
        self.assertTrue(throttle_status['is_throttled'])
        
    async def test_system_shutdown_monitoring(self):
        """Test system shutdown monitoring."""
        # Mock critical error
        critical_error = {
            'type': 'CRITICAL_ERROR',
            'message': 'Database connection lost',
            'timestamp': self.test_date
        }
        
        with patch.object(self.safety_monitor, '_initiate_shutdown') as mock_shutdown:
            await self.safety_monitor.handle_critical_error(critical_error)
            mock_shutdown.assert_called_once()
            
            # Verify shutdown notification
            self.assertTrue(self.safety_monitor.is_shutdown_initiated())
            
    async def test_recovery_monitoring(self):
        """Test system recovery monitoring."""
        # Mock recovery process
        recovery_steps = [
            'database_reconnect',
            'position_reconciliation',
            'strategy_restart'
        ]
        
        with patch.object(self.safety_monitor, '_execute_recovery') as mock_recovery:
            recovery_status = await self.safety_monitor.initiate_recovery(recovery_steps)
            self.assertTrue(recovery_status['success'])
            self.assertEqual(len(recovery_status['completed_steps']), 
                           len(recovery_steps))

if __name__ == '__main__':
    unittest.main()
