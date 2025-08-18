"""
Order execution client for IIFL API.
"""
from typing import Dict, List, Optional, Any
import aiohttp
from config.settings import IIFL_BASE_URL
from config.logging_config import get_logger
from utils.trading_state import TradingState
from database.models import OrderStatus

logger = get_logger('execution')

class IIFLExecutionClient:
    """Client for order execution through IIFL API."""
    
    def __init__(self, session_token: str):
        self.session_token = session_token
        self.base_url = IIFL_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {session_token}",
            "Content-Type": "application/json"
        }
        self.trading_state = TradingState()
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make HTTP request to IIFL API."""
        url = f"{self.base_url}/{endpoint}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, headers=self.headers, json=data) as response:
                    if response.status == 401:
                        logger.error("Authentication failed - session may have expired")
                        self.trading_state.disable_trading()
                        raise Exception("Authentication failed")
                    
                    response_data = await response.json()
                    if response.status != 200:
                        logger.error(f"API request failed: {response_data}")
                        raise Exception(f"API request failed: {response_data}")
                    
                    return response_data
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            raise
    
    async def place_order(self, order_params: Dict[str, Any]) -> Dict:
        """Place a new order."""
        try:
            response = await self._make_request("POST", "orders", data=order_params)
            logger.info(f"Order placed successfully: {response}")
            return response
        except Exception as e:
            logger.error(f"Failed to place order: {str(e)}")
            raise
    
    async def modify_order(self, broker_order_id: str, modify_params: Dict[str, Any]) -> Dict:
        """Modify an existing order."""
        try:
            response = await self._make_request(
                "PUT",
                f"orders/{broker_order_id}",
                data=modify_params
            )
            logger.info(f"Order modified successfully: {response}")
            return response
        except Exception as e:
            logger.error(f"Failed to modify order: {str(e)}")
            raise
    
    async def cancel_order(self, broker_order_id: str) -> Dict:
        """Cancel an order."""
        try:
            response = await self._make_request("DELETE", f"orders/{broker_order_id}")
            logger.info(f"Order cancelled successfully: {response}")
            return response
        except Exception as e:
            logger.error(f"Failed to cancel order: {str(e)}")
            raise
    
    async def get_order_book(self) -> Dict:
        """Get all orders for the day."""
        try:
            response = await self._make_request("GET", "orders")
            return response
        except Exception as e:
            logger.error(f"Failed to get order book: {str(e)}")
            raise
    
    async def get_trade_book(self) -> Dict:
        """Get all trades for the day."""
        try:
            response = await self._make_request("GET", "trades")
            return response
        except Exception as e:
            logger.error(f"Failed to get trade book: {str(e)}")
            raise
    
    async def get_positions(self) -> Dict:
        """Get current positions."""
        try:
            response = await self._make_request("GET", "positions")
            return response
        except Exception as e:
            logger.error(f"Failed to get positions: {str(e)}")
            raise
    
    async def get_holdings(self) -> Dict:
        """Get holdings."""
        try:
            response = await self._make_request("GET", "holdings")
            return response
        except Exception as e:
            logger.error(f"Failed to get holdings: {str(e)}")
            raise
