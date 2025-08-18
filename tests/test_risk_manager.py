"""
Unit tests for risk management system.
"""
import unittest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import datetime

from tests.base_test import BaseTestCase
from risk_management.risk_manager import RiskManager
from config.risk_settings import RISK_LIMITS

class TestRiskManager(BaseTestCase):
    """Test suite for Risk Management system."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.risk_manager = RiskManager()
        self.risk_manager.trading_state = self.trading_state
    
    async def test_position_size_limits(self):
        """Test position size limits."""
        # Create test order
        order = self.create_test_data("order", quantity=RISK_LIMITS['max_position_size'] + 1)
        strategy_metrics = {'volatility': 15.0, 'max_drawdown': -2.0}
        
        # Validate order
        result = await self.risk_manager.validate_order(order, strategy_metrics)
        
        # Order should be rejected due to size
        self.assertFalse(result)
    
    async def test_daily_loss_limit(self):
        """Test daily loss limit."""
        # Set daily loss near limit
        self.risk_manager.daily_pnl = -RISK_LIMITS['max_daily_loss'] * 0.99
        
        # Create test order
        order = self.create_test_data("order")
        strategy_metrics = {'volatility': 15.0, 'max_drawdown': -2.0}
        
        # Validate order
        result = await self.risk_manager.validate_order(order, strategy_metrics)
        
        # Order should be rejected due to approaching daily loss limit
        self.assertFalse(result)
    
    async def test_drawdown_limit(self):
        """Test drawdown limit."""
        # Create test order with high drawdown
        order = self.create_test_data("order")
        strategy_metrics = {'volatility': 15.0, 'max_drawdown': -RISK_LIMITS['max_drawdown'] - 1}
        
        # Validate order
        result = await self.risk_manager.validate_order(order, strategy_metrics)
        
        # Order should be rejected due to exceeding drawdown limit
        self.assertFalse(result)
    
    async def test_volatility_adjustment(self):
        """Test volatility-based position sizing."""
        base_quantity = 5
        order = self.create_test_data("order", quantity=base_quantity)
        
        # Test high volatility scenario
        high_vol_metrics = {'volatility': RISK_LIMITS['high_volatility_threshold'] * 1.5}
        size = self.risk_manager.get_position_size(
            order['instrument_id'],
            100.0,  # price
            high_vol_metrics
        )
        self.assertLess(size, base_quantity)
        
        # Test low volatility scenario
        low_vol_metrics = {'volatility': RISK_LIMITS['high_volatility_threshold'] * 0.5}
        size = self.risk_manager.get_position_size(
            order['instrument_id'],
            100.0,  # price
            low_vol_metrics
        )
        self.assertGreaterEqual(size, base_quantity)
    
    async def test_market_regime_validation(self):
        """Test market regime based validation."""
        order = self.create_test_data("order")
        
        # Test weak trend scenario
        weak_trend_metrics = {
            'volatility': 15.0,
            'trend_strength': RISK_LIMITS['min_trend_strength'] - 1
        }
        result = await self.risk_manager._validate_market_regime(order, weak_trend_metrics)
        self.assertFalse(result)
        
        # Test strong trend scenario
        strong_trend_metrics = {
            'volatility': 15.0,
            'trend_strength': RISK_LIMITS['min_trend_strength'] + 1
        }
        result = await self.risk_manager._validate_market_regime(order, strong_trend_metrics)
        self.assertTrue(result)
    
    async def test_risk_metrics_update(self):
        """Test risk metrics updating."""
        # Create test positions and trades
        positions = [
            {'instrumentId': 'TEST1', 'quantity': 1, 'avgPrice': 100, 'pnl': 50},
            {'instrumentId': 'TEST2', 'quantity': 2, 'avgPrice': 200, 'pnl': -30}
        ]
        trades = [
            {'id': 1, 'pnl': 100},
            {'id': 2, 'pnl': -50}
        ]
        
        # Update metrics
        await self.risk_manager.update_risk_metrics(positions, trades)
        
        # Verify metrics
        self.assertEqual(self.risk_manager.daily_pnl, 20)  # 50 - 30
        self.assertEqual(len(self.risk_manager.position_limits), 2)
        self.assertEqual(
            self.risk_manager.risk_metrics['total_exposure'],
            1 * 100 + 2 * 200
        )
    
    async def test_circuit_breakers(self):
        """Test circuit breaker levels."""
        # Test Level 1 circuit breaker
        self.risk_manager.daily_pnl = -CIRCUIT_BREAKERS['level_1']['drawdown'] * 1.1
        should_stop = self.risk_manager.should_stop_trading()
        self.assertFalse(should_stop)  # Level 1 reduces size but doesn't stop
        
        # Test Level 3 circuit breaker
        self.risk_manager.daily_pnl = -CIRCUIT_BREAKERS['level_3']['drawdown'] * 1.1
        should_stop = self.risk_manager.should_stop_trading()
        self.assertTrue(should_stop)  # Level 3 stops trading
    
    async def test_recovery_mode(self):
        """Test recovery mode logic."""
        # Trigger recovery mode
        self.risk_manager.daily_pnl = RECOVERY_SETTINGS['activation_threshold'] - 1
        
        # Test position sizing in recovery mode
        order = self.create_test_data("order")
        strategy_metrics = {'volatility': 15.0, 'max_drawdown': -2.0}
        
        # Get position size
        size = self.risk_manager.get_position_size(
            order['instrument_id'],
            100.0,  # price
            strategy_metrics
        )
        
        # Verify reduced position size
        self.assertLessEqual(
            size,
            RISK_LIMITS['max_position_size'] * RECOVERY_SETTINGS['position_size_factor']
        )
    
    async def test_exposure_limits(self):
        """Test exposure limits."""
        # Set high total exposure
        self.risk_manager.risk_metrics = {
            'total_exposure': RISK_LIMITS['max_total_exposure'] * 1.1
        }
        
        # Create test order
        order = self.create_test_data("order")
        strategy_metrics = {'volatility': 15.0, 'max_drawdown': -2.0}
        
        # Validate order
        result = await self.risk_manager.validate_order(order, strategy_metrics)
        
        # Order should be rejected due to high exposure
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
