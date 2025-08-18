"""
Risk Management system for QuantHybrid trading system.
"""
from typing import Dict, List, Optional
from datetime import datetime, time
import pandas as pd
import numpy as np
from config.settings import RISK_LIMITS
from config.logging_config import get_logger
from database.models import Order, Trade
from utils.trading_state import TradingState

logger = get_logger('risk_manager')

class RiskManager:
    def __init__(self):
        self.trading_state = TradingState()
        self.daily_pnl = 0.0
        self.max_position_size = RISK_LIMITS['max_position_size']
        self.max_daily_loss = RISK_LIMITS['max_daily_loss']
        self.max_drawdown = RISK_LIMITS['max_drawdown']
        self.position_limits = {}
        self.risk_metrics = {}
        
    async def validate_order(self, order: Dict, strategy_metrics: Dict) -> bool:
        """
        Validate if an order meets all risk requirements.
        Returns True if order is valid, False otherwise.
        """
        try:
            # Check if trading is allowed
            if not self.trading_state.is_trading_enabled():
                logger.warning("Trading is disabled. Order rejected.")
                return False
            
            # Check daily loss limit
            if self.daily_pnl <= -self.max_daily_loss:
                logger.warning(f"Daily loss limit of {self.max_daily_loss} reached. Order rejected.")
                return False
            
            # Check drawdown limit
            if strategy_metrics.get('max_drawdown', 0) <= -self.max_drawdown:
                logger.warning(f"Maximum drawdown limit of {self.max_drawdown} reached. Order rejected.")
                return False
            
            # Check position limits
            instrument_id = order['instrumentId']
            current_position = self.position_limits.get(instrument_id, 0)
            new_position = current_position + order['quantity']
            if abs(new_position) > self.max_position_size:
                logger.warning(f"Position size limit of {self.max_position_size} exceeded. Order rejected.")
                return False
            
            # Validate based on market regime
            if not self._validate_market_regime(order, strategy_metrics):
                return False
            
            # Validate based on volatility
            if not self._validate_volatility(order, strategy_metrics):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error in order validation: {str(e)}")
            return False
    
    def _validate_market_regime(self, order: Dict, strategy_metrics: Dict) -> bool:
        """
        Validate order based on current market regime.
        """
        try:
            # Get market regime metrics
            volatility = strategy_metrics.get('volatility', 0)
            trend_strength = strategy_metrics.get('trend_strength', 0)
            
            # High volatility regime checks
            if volatility > RISK_LIMITS['high_volatility_threshold']:
                # Reduce position size in high volatility
                order['quantity'] = int(order['quantity'] * 0.5)
                logger.info(f"Reduced position size due to high volatility: {volatility}")
            
            # Trending market checks
            if trend_strength < RISK_LIMITS['min_trend_strength']:
                logger.warning(f"Insufficient trend strength: {trend_strength}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error in market regime validation: {str(e)}")
            return False
    
    def _validate_volatility(self, order: Dict, strategy_metrics: Dict) -> bool:
        """
        Validate order based on current volatility conditions.
        """
        try:
            volatility = strategy_metrics.get('volatility', 0)
            
            # Reject orders in extreme volatility
            if volatility > RISK_LIMITS['max_volatility']:
                logger.warning(f"Extreme volatility detected: {volatility}. Order rejected.")
                return False
            
            # Adjust position size based on volatility
            volatility_factor = 1.0
            if volatility > RISK_LIMITS['high_volatility_threshold']:
                volatility_factor = 0.5
            elif volatility > RISK_LIMITS['medium_volatility_threshold']:
                volatility_factor = 0.75
            
            order['quantity'] = int(order['quantity'] * volatility_factor)
            
            return True
            
        except Exception as e:
            logger.error(f"Error in volatility validation: {str(e)}")
            return False
    
    async def update_risk_metrics(self, positions: List[Dict], trades: List[Dict]):
        """
        Update risk metrics based on current positions and trades.
        """
        try:
            # Update daily P&L
            self.daily_pnl = sum(float(pos.get('pnl', 0)) for pos in positions)
            
            # Update position limits
            self.position_limits = {
                pos['instrumentId']: pos.get('quantity', 0)
                for pos in positions
            }
            
            # Calculate risk metrics
            self.risk_metrics = {
                'daily_pnl': self.daily_pnl,
                'total_exposure': sum(abs(pos.get('quantity', 0) * float(pos.get('avgPrice', 0))) 
                                   for pos in positions),
                'largest_position': max((abs(pos.get('quantity', 0)) for pos in positions), default=0),
                'open_positions': len(positions),
                'daily_trades': len(trades)
            }
            
        except Exception as e:
            logger.error(f"Error updating risk metrics: {str(e)}")
    
    def get_position_size(self, instrument_id: str, price: float, strategy_metrics: Dict) -> int:
        """
        Calculate appropriate position size based on risk parameters.
        """
        try:
            base_size = self.max_position_size
            
            # Adjust for volatility
            volatility = strategy_metrics.get('volatility', 0)
            volatility_factor = min(1.0, RISK_LIMITS['volatility_base'] / volatility) if volatility > 0 else 1.0
            
            # Adjust for available capital
            capital_factor = min(1.0, RISK_LIMITS['max_capital_per_trade'] / (price * base_size))
            
            # Adjust for current drawdown
            drawdown = strategy_metrics.get('max_drawdown', 0)
            drawdown_factor = max(0.2, 1.0 + drawdown / self.max_drawdown)
            
            # Calculate final size
            position_size = int(base_size * volatility_factor * capital_factor * drawdown_factor)
            
            # Ensure minimum size
            return max(RISK_LIMITS['min_position_size'], position_size)
            
        except Exception as e:
            logger.error(f"Error calculating position size: {str(e)}")
            return RISK_LIMITS['min_position_size']
    
    def should_stop_trading(self) -> bool:
        """
        Check if trading should be stopped based on risk metrics.
        """
        try:
            # Check daily loss limit
            if self.daily_pnl <= -self.max_daily_loss:
                logger.warning("Daily loss limit reached. Stopping trading.")
                return True
            
            # Check max drawdown
            if any(metric.get('max_drawdown', 0) <= -self.max_drawdown 
                  for metric in self.risk_metrics.values()):
                logger.warning("Maximum drawdown limit reached. Stopping trading.")
                return True
            
            # Check other risk factors
            total_exposure = self.risk_metrics.get('total_exposure', 0)
            if total_exposure > RISK_LIMITS['max_total_exposure']:
                logger.warning("Maximum exposure limit reached. Stopping trading.")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking trading status: {str(e)}")
            return True  # Stop trading on error to be safe
