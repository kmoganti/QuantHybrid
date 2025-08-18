"""
Unit tests for Web Interface components.
"""
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import json
from fastapi.testclient import TestClient
import jwt

from tests.base_test import BaseTestCase
from web_interface.api import app
from database.models import Trade, Position, Strategy, Account

class TestWebInterface(BaseTestCase):
    """Test suite for web interface components."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.client = TestClient(app)
        self.test_date = datetime(2025, 8, 16)
        
        # Setup test auth token
        self.test_token = jwt.encode(
            {'sub': 'test_user', 'exp': datetime.utcnow() + timedelta(days=1)},
            'test_secret_key'
        )
        self.headers = {'Authorization': f'Bearer {self.test_token}'}
        
    async def test_authentication(self):
        """Test authentication endpoints."""
        # Test login
        login_data = {
            'username': 'test_user',
            'password': 'test_password'
        }
        
        response = self.client.post('/api/auth/login', json=login_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('access_token', response.json())
        
        # Test invalid credentials
        invalid_login = {
            'username': 'test_user',
            'password': 'wrong_password'
        }
        response = self.client.post('/api/auth/login', json=invalid_login)
        self.assertEqual(response.status_code, 401)
        
    async def test_dashboard_data(self):
        """Test dashboard data endpoints."""
        # Mock account data
        test_account = Account(
            balance=10000000.0,
            equity=10500000.0,
            margin_used=2000000.0,
            free_margin=8000000.0
        )
        
        with patch('web_interface.api.get_account_summary') as mock_account:
            mock_account.return_value = test_account
            
            response = self.client.get('/api/dashboard/summary', headers=self.headers)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            self.assertEqual(data['balance'], test_account.balance)
            self.assertEqual(data['equity'], test_account.equity)
            
    async def test_strategy_management(self):
        """Test strategy management endpoints."""
        # Test strategy creation
        new_strategy = {
            'name': 'MA_Crossover',
            'parameters': {
                'short_window': 10,
                'long_window': 30
            },
            'symbols': ['RELIANCE', 'TCS']
        }
        
        response = self.client.post('/api/strategies', 
                                  json=new_strategy, 
                                  headers=self.headers)
        self.assertEqual(response.status_code, 201)
        strategy_id = response.json()['id']
        
        # Test strategy retrieval
        response = self.client.get(f'/api/strategies/{strategy_id}',
                                 headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['name'], new_strategy['name'])
        
    async def test_position_monitoring(self):
        """Test position monitoring endpoints."""
        # Mock position data
        test_positions = [
            {
                'symbol': 'RELIANCE',
                'quantity': 100,
                'average_price': 2500.0,
                'current_price': 2550.0,
                'unrealized_pnl': 5000.0
            },
            {
                'symbol': 'TCS',
                'quantity': 50,
                'average_price': 3500.0,
                'current_price': 3450.0,
                'unrealized_pnl': -2500.0
            }
        ]
        
        with patch('web_interface.api.get_open_positions') as mock_positions:
            mock_positions.return_value = test_positions
            
            response = self.client.get('/api/positions', headers=self.headers)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.json()), len(test_positions))
            
    async def test_trade_history(self):
        """Test trade history endpoints."""
        # Mock trade data
        test_trades = [
            {
                'symbol': 'RELIANCE',
                'entry_price': 2500.0,
                'exit_price': 2550.0,
                'quantity': 100,
                'pnl': 5000.0,
                'entry_time': self.test_date.isoformat(),
                'exit_time': (self.test_date + timedelta(hours=1)).isoformat()
            }
        ]
        
        with patch('web_interface.api.get_trade_history') as mock_trades:
            mock_trades.return_value = test_trades
            
            response = self.client.get('/api/trades', headers=self.headers)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.json()), len(test_trades))
            
    async def test_performance_analytics(self):
        """Test performance analytics endpoints."""
        # Mock performance data
        test_performance = {
            'total_pnl': 250000.0,
            'win_rate': 0.65,
            'sharpe_ratio': 1.8,
            'max_drawdown': -0.15,
            'daily_returns': [0.02, -0.01, 0.03]
        }
        
        with patch('web_interface.api.get_performance_metrics') as mock_perf:
            mock_perf.return_value = test_performance
            
            response = self.client.get('/api/analytics/performance',
                                     headers=self.headers)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['total_pnl'],
                           test_performance['total_pnl'])
            
    async def test_websocket_streaming(self):
        """Test WebSocket data streaming."""
        with self.client.websocket_connect('/ws/market-data') as websocket:
            # Mock market data
            test_tick = {
                'symbol': 'RELIANCE',
                'price': 2500.0,
                'volume': 1000,
                'timestamp': self.test_date.isoformat()
            }
            
            # Send test data
            websocket.send_json(test_tick)
            
            # Receive data
            data = websocket.receive_json()
            self.assertEqual(data['symbol'], test_tick['symbol'])
            self.assertEqual(data['price'], test_tick['price'])
            
    async def test_order_management(self):
        """Test order management endpoints."""
        # Test order placement
        new_order = {
            'symbol': 'RELIANCE',
            'quantity': 100,
            'side': 'BUY',
            'order_type': 'MARKET'
        }
        
        response = self.client.post('/api/orders', 
                                  json=new_order,
                                  headers=self.headers)
        self.assertEqual(response.status_code, 201)
        order_id = response.json()['id']
        
        # Test order status
        response = self.client.get(f'/api/orders/{order_id}',
                                 headers=self.headers)
        self.assertEqual(response.status_code, 200)
        
    async def test_risk_monitoring(self):
        """Test risk monitoring endpoints."""
        # Mock risk metrics
        test_risk_metrics = {
            'total_exposure': 5000000.0,
            'margin_utilization': 0.4,
            'risk_level': 'MEDIUM',
            'position_limits': {
                'RELIANCE': {'current': 500, 'max': 1000},
                'TCS': {'current': 300, 'max': 800}
            }
        }
        
        with patch('web_interface.api.get_risk_metrics') as mock_risk:
            mock_risk.return_value = test_risk_metrics
            
            response = self.client.get('/api/risk/metrics',
                                     headers=self.headers)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['risk_level'],
                           test_risk_metrics['risk_level'])
            
    async def test_api_rate_limiting(self):
        """Test API rate limiting."""
        # Make multiple rapid requests
        for _ in range(10):
            response = self.client.get('/api/dashboard/summary',
                                     headers=self.headers)
            
        # Next request should be rate limited
        response = self.client.get('/api/dashboard/summary',
                                 headers=self.headers)
        self.assertEqual(response.status_code, 429)
        
    async def test_error_handling(self):
        """Test API error handling."""
        # Test invalid order
        invalid_order = {
            'symbol': 'RELIANCE',
            'quantity': -100,  # Invalid negative quantity
            'side': 'BUY',
            'order_type': 'MARKET'
        }
        
        response = self.client.post('/api/orders',
                                  json=invalid_order,
                                  headers=self.headers)
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
        
    async def test_websocket_authentication(self):
        """Test WebSocket authentication."""
        # Test without authentication
        with self.assertRaises(Exception):
            with self.client.websocket_connect('/ws/market-data') as websocket:
                pass
                
        # Test with valid authentication
        with self.client.websocket_connect(
            '/ws/market-data',
            headers=self.headers
        ) as websocket:
            self.assertTrue(websocket.connected)

if __name__ == '__main__':
    unittest.main()
