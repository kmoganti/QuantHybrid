"""
Base strategy class for QuantHybrid trading system.
"""
from typing import Dict, List, Optional, Any
import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
import pandas as pd
import numpy as np
from config.settings import TRADING_HOURS, ML_SETTINGS
from config.logging_config import get_logger
from database.models import MarketRegime, Order
from core.market_data.market_data_manager import MarketDataManager
from execution.order_manager import OrderManager
from utils.trading_state import TradingState

logger = get_logger('strategy')

class BaseStrategy(ABC):
    """Abstract base class for all trading strategies."""
    
    def __init__(
        self,
        name: str,
        instruments: List[Dict[str, str]],
        market_data_manager: MarketDataManager,
        order_manager: OrderManager,
        risk_manager: RiskManager,
        params: Dict[str, Any] = None
    ):
        self.name = name
        self.instruments = instruments
        self.market_data = market_data_manager
        self.order_manager = order_manager
        self.risk_manager = risk_manager
        self.params = params or {}
        self.trading_state = TradingState()
        self.positions: Dict[str, Dict] = {}
        self.signals: Dict[str, Dict] = {}
        self.is_active = False
        self.update_task = None
        
        # Performance metrics
        self.total_trades = 0
        self.winning_trades = 0
        self.total_pnl = 0.0
        self.max_drawdown = 0.0
    
    async def start(self):
        """Start the strategy."""
        try:
            self.is_active = True
            self.update_task = asyncio.create_task(self._strategy_loop())
            self.trading_state.set_strategy_status(self.name, True)
            logger.info(f"Strategy {self.name} started")
        except Exception as e:
            logger.error(f"Failed to start strategy {self.name}: {str(e)}")
            self.trading_state.set_strategy_status(self.name, False)
            raise
    
    async def stop(self):
        """Stop the strategy."""
        try:
            self.is_active = False
            if self.update_task:
                self.update_task.cancel()
            self.trading_state.set_strategy_status(self.name, False)
            logger.info(f"Strategy {self.name} stopped")
        except Exception as e:
            logger.error(f"Error stopping strategy {self.name}: {str(e)}")
            raise
    
    async def _strategy_loop(self):
        """Main strategy loop."""
        while self.is_active:
            try:
                # Check trading hours
                if not self._is_trading_time():
                    await asyncio.sleep(60)
                    continue
                
                # Check if trading is enabled
                if not self.trading_state.is_trading_enabled():
                    await asyncio.sleep(1)
                    continue
                
                # Update market data
                await self._update_market_data()
                
                # Generate signals
                await self._generate_signals()
                
                # Execute signals
                await self._execute_signals()
                
                # Update positions
                await self._update_positions()
                
                # Update performance metrics
                await self._update_metrics()
                
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in strategy loop: {str(e)}")
                await asyncio.sleep(5)
    
    @abstractmethod
    async def _generate_signals(self):
        """Generate trading signals. To be implemented by specific strategies."""
        pass
    
    async def _execute_signals(self):
        """Execute generated trading signals with risk management."""
        try:
            for instrument_id, signal in self.signals.items():
                if not signal.get('active', False):
                    continue
                
                # Create order parameters
                order_params = self._create_order_params(instrument_id, signal)
                if not order_params:
                    continue
                
                # Get strategy metrics for risk assessment
                metrics = self.get_metrics()
                
                # Validate order with risk manager
                if not await self.risk_manager.validate_order(order_params, metrics):
                    logger.warning(f"Order rejected by risk manager for {instrument_id}")
                    continue
                
                # Adjust position size based on risk
                price = float(signal.get('price', 0)) or self.market_data.get_last_price(instrument_id)
                risk_adjusted_size = self.risk_manager.get_position_size(instrument_id, price, metrics)
                order_params['quantity'] = risk_adjusted_size
                
                # Place order if it passes all checks
                await self.order_manager.place_order(order_params)
                signal['active'] = False  # Mark signal as executed
                
                # Update risk metrics after order execution
                await self.risk_manager.update_risk_metrics(
                    list(self.positions.values()),
                    self.order_manager.get_todays_trades()
                )
                
        except Exception as e:
            logger.error(f"Error executing signals: {str(e)}")
    
    async def _update_market_data(self):
        """Update market data for strategy instruments."""
        try:
            await self.market_data.get_real_time_data(self.instruments)
        except Exception as e:
            logger.error(f"Error updating market data: {str(e)}")
    
    async def _update_positions(self):
        """Update current positions."""
        try:
            positions = await self.order_manager.client.get_positions()
            self.positions = {
                pos['instrumentId']: pos
                for pos in positions.get('result', [])
            }
        except Exception as e:
            logger.error(f"Error updating positions: {str(e)}")
    
    async def _update_metrics(self):
        """Update strategy performance metrics."""
        try:
            # Calculate PnL
            current_pnl = sum(
                float(pos.get('pnl', 0))
                for pos in self.positions.values()
            )
            
            # Update maximum drawdown
            self.max_drawdown = min(self.max_drawdown, current_pnl)
            
            # Update total PnL
            self.total_pnl = current_pnl
            
        except Exception as e:
            logger.error(f"Error updating metrics: {str(e)}")
    
    def _is_trading_time(self) -> bool:
        """Check if current time is within trading hours."""
        now = datetime.now().time()
        start_time = datetime.strptime(TRADING_HOURS['start'], '%H:%M').time()
        end_time = datetime.strptime(TRADING_HOURS['end'], '%H:%M').time()
        return start_time <= now <= end_time
    
    def _create_order_params(self, instrument_id: str, signal: Dict) -> Optional[Dict]:
        """Create order parameters from signal."""
        try:
            return {
                'instrumentId': instrument_id,
                'exchange': signal['exchange'],
                'transactionType': signal['transaction_type'],
                'quantity': signal['quantity'],
                'orderType': signal.get('order_type', 'MARKET'),
                'price': signal.get('price'),
                'triggerPrice': signal.get('trigger_price'),
                'product': signal.get('product', 'INTRADAY'),
                'validity': signal.get('validity', 'DAY'),
                'disclosedQuantity': signal.get('disclosed_quantity'),
                'orderComplexity': signal.get('order_complexity', 'REGULAR'),
                'orderTag': self.name
            }
        except KeyError as e:
            logger.error(f"Missing required signal parameter: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error creating order parameters: {str(e)}")
            return None
    
    def get_metrics(self) -> Dict:
        """Get strategy performance metrics."""
        return {
            'name': self.name,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'win_rate': (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0,
            'total_pnl': self.total_pnl,
            'max_drawdown': self.max_drawdown,
            'active_positions': len(self.positions)
        }
