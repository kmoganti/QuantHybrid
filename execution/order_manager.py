"""
Smart order router and execution manager.
"""
from typing import Dict, List, Optional, Any
import asyncio
from datetime import datetime
from config.logging_config import get_logger
from config.settings import CIRCUIT_BREAKER
from database.database_manager import DatabaseManager
from database.models import Order, OrderStatus, Trade
from execution.iifl_execution import IIFLExecutionClient
from utils.trading_state import TradingState

logger = get_logger('execution')

class OrderManager:
    """Manages order execution and monitoring."""
    
    def __init__(self, session_token: str = "test_session"):
        self.client = IIFLExecutionClient(session_token)
        self.trading_state = TradingState()
        self.pending_orders: Dict[str, Order] = {}
        self.order_update_task = None
        self.db_manager = DatabaseManager(test_mode=True)
    
    async def start(self):
        """Start order manager."""
        try:
            # Start order monitoring
            self.order_update_task = asyncio.create_task(self._monitor_orders())
            self.trading_state.set_component_status('order_manager', True)
            logger.info("Order manager started successfully")
        except Exception as e:
            logger.error(f"Failed to start order manager: {str(e)}")
            self.trading_state.set_component_status('order_manager', False)
            raise
    
    async def stop(self):
        """Stop order manager."""
        try:
            if self.order_update_task:
                self.order_update_task.cancel()
            self.trading_state.set_component_status('order_manager', False)
            logger.info("Order manager stopped")
        except Exception as e:
            logger.error(f"Error stopping order manager: {str(e)}")
            raise
    
    async def place_order(self, order_params: Dict[str, Any]) -> Optional[str]:
        """Place a new order with smart routing."""
        try:
            if not self.trading_state.is_trading_enabled():
                logger.warning("Trading is disabled - order rejected")
                return None
            
            # Add safety checks
            if not self._validate_order_params(order_params):
                logger.error("Invalid order parameters")
                return None
            
            # Place the order
            response = await self.client.place_order(order_params)
            broker_order_id = response['result'][0]['brokerOrderId']
            
            # Create order record
            order = Order(
                broker_order_id=broker_order_id,
                instrument_id=order_params['instrumentId'],
                transaction_type=order_params['transactionType'],
                quantity=order_params['quantity'],
                price=order_params.get('price'),
                trigger_price=order_params.get('slTriggerPrice'),
                status=OrderStatus.PLACED.value,
                strategy=order_params.get('orderTag', 'UNKNOWN'),
                portfolio_type=order_params.get('portfolio_type', 'SATELLITE')
            )
            
            # Store in database
            await self.db_manager.add_item(order)
            
            # Add to pending orders
            self.pending_orders[broker_order_id] = order
            
            logger.info(f"Order placed successfully: {broker_order_id}")
            return broker_order_id
            
        except Exception as e:
            logger.error(f"Failed to place order: {str(e)}")
            return None
    
    async def modify_order(self, broker_order_id: str, modify_params: Dict[str, Any]) -> bool:
        """Modify an existing order."""
        try:
            if not self.trading_state.is_trading_enabled():
                logger.warning("Trading is disabled - modification rejected")
                return False
            
            await self.client.modify_order(broker_order_id, modify_params)
            
            # Update order record
            order_list = await self.db_manager.get_items(Order, broker_order_id=broker_order_id)
            if order_list:
                order = order_list[0]
                order.status = OrderStatus.MODIFIED.value
                await self.db_manager.update_item(order)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to modify order: {str(e)}")
            return False
    
    async def cancel_order(self, broker_order_id: str) -> bool:
        """Cancel an order."""
        try:
            await self.client.cancel_order(broker_order_id)
            
            # Update order record
            order_list = await self.db_manager.get_items(Order, broker_order_id=broker_order_id)
            if order_list:
                order = order_list[0]
                order.status = OrderStatus.CANCELLED.value
                await self.db_manager.update_item(order)
            
            # Remove from pending orders
            self.pending_orders.pop(broker_order_id, None)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel order: {str(e)}")
            return False
    
    async def _monitor_orders(self):
        """Monitor and update order status."""
        while True:
            try:
                if not self.pending_orders:
                    await asyncio.sleep(1)
                    continue
                
                # Get order book
                order_book = await self.client.get_order_book()
                
                # Update order status
                for order_data in order_book.get('result', []):
                    broker_order_id = order_data['brokerOrderId']
                    if broker_order_id in self.pending_orders:
                        await self._update_order_status(broker_order_id, order_data)
                
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in order monitoring: {str(e)}")
                await asyncio.sleep(5)
    
    async def _update_order_status(self, broker_order_id: str, order_data: Dict):
        """Update order status and create trade if executed."""
        try:
            order = self.pending_orders[broker_order_id]
            new_status = OrderStatus(order_data['orderStatus'].lower())
            
            if new_status.value != order.status:
                order.status = new_status.value
                await self.db_manager.update_item(order)
                
                if new_status == OrderStatus.EXECUTED:
                    # Create trade record
                    trade = Trade(
                        instrument_id=order.instrument_id,
                        order_id=broker_order_id,
                        transaction_type=order.transaction_type,
                        quantity=order_data['filledQuantity'],
                        price=order_data['averageTradedPrice'],
                        strategy=order.strategy,
                        portfolio_type=order.portfolio_type
                    )
                    await self.db_manager.add_item(trade)
                    
                    # Remove from pending orders
                    self.pending_orders.pop(broker_order_id)
                    
                logger.info(f"Order {broker_order_id} status updated to {new_status.value}")
                
        except Exception as e:
            logger.error(f"Error updating order status: {str(e)}")
    
    def _validate_order_params(self, params: Dict) -> bool:
        """Validate order parameters."""
        required_fields = ['instrumentId', 'exchange', 'transactionType', 'quantity']
        return all(field in params for field in required_fields)
