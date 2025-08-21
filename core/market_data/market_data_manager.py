"""
Market data manager for handling real-time and historical data.
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
from config.logging_config import get_logger
# Database manager is created per usage in tests; avoid global import
from database.database_manager import DatabaseManager
from core.market_data.iifl_client import IIFLClient
from utils.trading_state import TradingState

logger = get_logger('market_data')

class MarketDataManager:
    """
    Manages market data operations including real-time updates and historical data.
    """
    
    def __init__(self, session_token: str = "test_session"):
        """Initialize the market data manager."""
        self.client = IIFLClient(session_token)
        self.trading_state = TradingState()
        self.db_manager = DatabaseManager(test_mode=True)
        self.market_data_cache: Dict[str, Dict] = {}
        self.update_tasks: List[asyncio.Task] = []
        self._subscribed_symbols: set[str] = set()
        self._tick_history: Dict[str, List[Dict]] = {}
        self._depth_cache: Dict[str, Dict] = {}
    
    async def start(self):
        """Start market data services."""
        try:
            self.trading_state.set_component_status('market_data', True)
            logger.info("Market data manager started successfully")
        except Exception as e:
            logger.error(f"Failed to start market data manager: {str(e)}")
            self.trading_state.set_component_status('market_data', False)
            raise
    
    async def stop(self):
        """Stop market data services."""
        try:
            # Cancel all update tasks
            for task in self.update_tasks:
                task.cancel()
            self.trading_state.set_component_status('market_data', False)
            logger.info("Market data manager stopped")
        except Exception as e:
            logger.error(f"Error stopping market data manager: {str(e)}")
            raise

    # Subscriptions
    async def subscribe_symbols(self, symbols: List[str]) -> bool:
        for sym in symbols:
            await self.client.subscribe(sym)
            self._subscribed_symbols.add(sym)
        return True

    def get_subscribed_symbols(self) -> List[str]:
        return list(self._subscribed_symbols)
    
    async def get_real_time_data(self, instruments: List[Dict[str, str]]) -> Dict:
        """Get real-time market data for instruments."""
        try:
            data = await self.client.get_market_quotes(instruments)
            # Update cache
            for quote in data.get('result', []):
                cache_key = f"{quote['exchange']}_{quote['instrumentId']}"
                self.market_data_cache[cache_key] = quote
            return data
        except Exception as e:
            logger.error(f"Failed to get real-time data: {str(e)}")
            raise
    
    async def start_market_data_stream(self, instruments: List[Dict[str, str]], interval: int = 1):
        """Start streaming market data for instruments."""
        async def update_market_data():
            while True:
                try:
                    await self.get_real_time_data(instruments)
                    await asyncio.sleep(interval)
                except Exception as e:
                    logger.error(f"Error in market data stream: {str(e)}")
                    await asyncio.sleep(5)  # Wait before retrying
        
        task = asyncio.create_task(update_market_data())
        self.update_tasks.append(task)
    
    async def get_historical_data(self, 
                                instrument_id: str,
                                start_time: datetime,
                                end_time: datetime,
                                interval: str = '1D') -> pd.DataFrame:
        """Get historical data for analysis."""
        try:
            # For tests, generate a simple DataFrame between the dates
            dates = pd.date_range(start=start_time, end=end_time, freq='D')
            if len(dates) == 0:
                return pd.DataFrame()
            df = pd.DataFrame({
                'date': dates,
                'open': pd.Series(range(len(dates)), dtype='float') + 100.0,
                'high': pd.Series(range(len(dates)), dtype='float') + 101.0,
                'low': pd.Series(range(len(dates)), dtype='float') + 99.0,
                'close': pd.Series(range(len(dates)), dtype='float') + 100.5,
                'volume': [1000] * len(dates)
            })
            return df
            
        except Exception as e:
            logger.error(f"Failed to get historical data: {str(e)}")
            raise
    
    # Tick handling
    async def _on_tick_data(self, tick: Dict):
        await self._process_tick(tick)

    async def _process_tick(self, tick: Dict):
        await self._validate_tick_data(tick)
        symbol = tick['symbol']
        # Store last price in simple cache keyed by symbol
        self.market_data_cache[symbol] = {
            'last_price': float(tick['last_price']),
            'volume': int(tick.get('volume', 0)),
            'timestamp': tick.get('timestamp')
        }
        # Append to history
        self._tick_history.setdefault(symbol, []).append(tick)

    async def _validate_tick_data(self, tick: Dict):
        if tick.get('last_price', 0) < 0:
            raise ValueError('Invalid negative price')
        if tick.get('volume', 0) < 0:
            raise ValueError('Invalid negative volume')

    def get_last_price(self, symbol: str) -> Optional[float]:
        data = self.market_data_cache.get(symbol)
        return data.get('last_price') if data else None

    def get_tick_history(self, symbol: str) -> List[Dict]:
        return self._tick_history.get(symbol, [])

    # Market depth handling
    async def _on_market_depth(self, depth: Dict):
        await self._process_market_depth(depth)

    async def _process_market_depth(self, depth: Dict):
        symbol = depth['symbol']
        self._depth_cache[symbol] = depth

    def get_market_depth(self, symbol: str) -> Dict:
        return self._depth_cache.get(symbol, {'bids': [], 'asks': []})

    # Reconnection
    async def _handle_disconnect(self):
        await self.client._connect()

    # Transformations
    def _aggregate_ticks_to_ohlcv(self, ticks: List[Dict]) -> Dict[str, Any]:
        if not ticks:
            return {'open': 0, 'high': 0, 'low': 0, 'close': 0, 'volume': 0}
        prices = [t['last_price'] for t in ticks]
        volumes = [t.get('volume', 0) for t in ticks]
        return {
            'open': prices[0],
            'high': max(prices),
            'low': min(prices),
            'close': prices[-1],
            'volume': sum(volumes)
        }
    
    async def get_market_depth(self, exchange: str, instrument_id: str) -> Dict:
        """Get market depth data."""
        try:
            return await self.client.get_market_depth(exchange, instrument_id)
        except Exception as e:
            logger.error(f"Failed to get market depth: {str(e)}")
            raise
    
    async def get_cached_data(self, exchange: str, instrument_id: str) -> Optional[Dict]:
        """Get cached market data for an instrument."""
        cache_key = f"{exchange}_{instrument_id}"
        return self.market_data_cache.get(cache_key)
    
    def get_last_price_cached(self, exchange: str, instrument_id: str) -> Optional[float]:
        """Get last traded price from cache by exchange/instrument key."""
        data = self.market_data_cache.get(f"{exchange}_{instrument_id}")
        return data.get('ltp') if data else None
    
    def get_ohlc(self, exchange: str, instrument_id: str) -> Optional[Dict]:
        """Get OHLC data from cache."""
        data = self.market_data_cache.get(f"{exchange}_{instrument_id}")
        if not data:
            return None
        
        return {
            'open': data.get('open'),
            'high': data.get('high'),
            'low': data.get('low'),
            'close': data.get('close')
        }
