"""
Market data manager for handling real-time and historical data.
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
from config.logging_config import get_logger
from database.database_manager import db_manager
from core.market_data.iifl_client import IIFLMarketDataClient
from utils.trading_state import TradingState

logger = get_logger('market_data')

class MarketDataManager:
    """
    Manages market data operations including real-time updates and historical data.
    """
    
    def __init__(self, session_token: str):
        """Initialize the market data manager."""
        self.client = IIFLMarketDataClient(session_token)
        self.trading_state = TradingState()
        self.market_data_cache: Dict[str, Dict] = {}
        self.update_tasks: List[asyncio.Task] = []
    
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
                                exchange: str,
                                instrument_id: str,
                                interval: str = "1 day",
                                days: int = 30) -> pd.DataFrame:
        """Get historical data for analysis."""
        try:
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days)
            
            data = await self.client.get_historical_data(
                exchange=exchange,
                instrument_id=instrument_id,
                interval=interval,
                from_date=from_date.strftime("%d-%b-%Y"),
                to_date=to_date.strftime("%d-%b-%Y")
            )
            
            # Convert to DataFrame
            df = pd.DataFrame(data['result'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            return df
            
        except Exception as e:
            logger.error(f"Failed to get historical data: {str(e)}")
            raise
    
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
    
    def get_last_price(self, exchange: str, instrument_id: str) -> Optional[float]:
        """Get last traded price from cache."""
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
