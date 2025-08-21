"""
IIFL API client for market data operations.
"""
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from config.settings import IIFL_BASE_URL
from config.logging_config import get_logger
from utils.trading_state import TradingState

logger = get_logger('api')

class IIFLClient:
    """
    Client for interacting with IIFL market data APIs.
    """
    
    def __init__(self, session_token: str = "test_session"):
        """Initialize the client with session token."""
        self.session_token = session_token
        self.base_url = IIFL_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {session_token}",
            "Content-Type": "application/json"
        }
        self.trading_state = TradingState()
        self._connected: bool = False
        self._subscriptions: set[str] = set()
    
    async def connect(self) -> bool:
        """Public connect method that uses internal _connect implementation."""
        try:
            result = await self._connect()
            self._connected = bool(result)
            return self._connected
        except Exception as exc:
            self._connected = False
            raise
    
    async def _connect(self) -> bool:
        """Low-level connect implementation (stubbed for tests)."""
        # In real-world, perform handshake/auth validation here
        await asyncio.sleep(0)
        return True

    async def subscribe(self, symbol: str) -> bool:
        """Subscribe to real-time updates for a symbol (stub for tests)."""
        if not self._connected:
            await self.connect()
        self._subscriptions.add(symbol)
        return True

    async def unsubscribe(self, symbol: str) -> bool:
        self._subscriptions.discard(symbol)
        return True
    
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
    
    async def get_market_quotes(self, instruments: List[Dict[str, str]]) -> Dict:
        """
        Get real-time market quotes for instruments.
        
        Args:
            instruments: List of dicts with exchange and instrumentId
        """
        try:
            response = await self._make_request(
                "POST",
                "marketdata/marketquotes",
                data=instruments
            )
            return response
        except Exception as e:
            logger.error(f"Failed to get market quotes: {str(e)}")
            raise
    
    async def get_historical_data(self, 
                                exchange: str,
                                instrument_id: str,
                                interval: str,
                                from_date: str,
                                to_date: str) -> Dict:
        """Get historical candlestick data."""
        try:
            response = await self._make_request(
                "POST",
                "marketdata/historicaldata",
                data={
                    "exchange": exchange,
                    "instrumentId": instrument_id,
                    "interval": interval,
                    "fromDate": from_date,
                    "toDate": to_date
                }
            )
            return response
        except Exception as e:
            logger.error(f"Failed to get historical data: {str(e)}")
            raise
    
    async def get_market_depth(self, exchange: str, instrument_id: str) -> Dict:
        """Get market depth for an instrument."""
        try:
            response = await self._make_request(
                "POST",
                "marketdata/marketdepth",
                data={
                    "exchange": exchange,
                    "instrumentId": instrument_id
                }
            )
            return response
        except Exception as e:
            logger.error(f"Failed to get market depth: {str(e)}")
            raise
    
    async def get_option_chain(self, underlying: str) -> Dict:
        """Get option chain for an underlying."""
        try:
            response = await self._make_request(
                "GET",
                f"marketdata/optionchain/{underlying}"
            )
            return response
        except Exception as e:
            logger.error(f"Failed to get option chain: {str(e)}")
            raise
    
    async def get_indices_data(self) -> Dict:
        """Get major market indices data."""
        try:
            instruments = [
                {"exchange": "NSEEQ", "instrumentId": "NIFTY50"},
                {"exchange": "NSEEQ", "instrumentId": "BANKNIFTY"},
                {"exchange": "BSEEQ", "instrumentId": "SENSEX"}
            ]
            response = await self.get_market_quotes(instruments)
            return response
        except Exception as e:
            logger.error(f"Failed to get indices data: {str(e)}")
            raise
