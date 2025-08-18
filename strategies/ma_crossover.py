"""
Moving Average Crossover Strategy implementation.
"""
import asyncio
from typing import Dict, List
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from config.logging_config import get_logger
from .base_strategy import BaseStrategy

logger = get_logger('ma_crossover_strategy')

class MovingAverageCrossoverStrategy(BaseStrategy):
    """
    A strategy that trades based on moving average crossovers.
    When the fast MA crosses above the slow MA, it generates a buy signal.
    When the fast MA crosses below the slow MA, it generates a sell signal.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Strategy-specific parameters
        self.fast_ma_period = self.params.get('fast_ma_period', 9)
        self.slow_ma_period = self.params.get('slow_ma_period', 21)
        self.lookback_period = max(self.fast_ma_period, self.slow_ma_period) + 10
        self.min_volume = self.params.get('min_volume', 100000)
        self.position_size = self.params.get('position_size', 1)
        
        # Market regime parameters
        self.volatility_period = self.params.get('volatility_period', 20)
        self.trend_period = self.params.get('trend_period', 50)
        self.regime_threshold = self.params.get('regime_threshold', 0.02)
        
        # Strategy state
        self.historical_data = {}
        self.ma_data = {}
        self.last_crossover = {}
        self.market_regime = {}
    
    async def _update_market_data(self):
        """Update market data and calculate indicators."""
        try:
            # Get historical data for each instrument
            for instrument in self.instruments:
                instrument_id = instrument['instrumentId']
                
                # Get historical data
                end_time = datetime.now()
                start_time = end_time - timedelta(days=5)  # Adjust based on your needs
                
                candles = await self.market_data.get_historical_data(
                    instrument_id,
                    start_time,
                    end_time,
                    '5min'  # 5-minute candles
                )
                
                if not candles:
                    continue
                
                # Convert to DataFrame
                df = pd.DataFrame(candles)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
                
                # Calculate moving averages
                df['fast_ma'] = df['close'].rolling(window=self.fast_ma_period).mean()
                df['slow_ma'] = df['close'].rolling(window=self.slow_ma_period).mean()
                
                # Calculate market regime indicators
                # Volatility (using ATR)
                df['high_low'] = df['high'] - df['low']
                df['high_close'] = abs(df['high'] - df['close'].shift())
                df['low_close'] = abs(df['low'] - df['close'].shift())
                df['tr'] = pd.concat([df['high_low'], df['high_close'], df['low_close']], axis=1).max(axis=1)
                df['atr'] = df['tr'].rolling(window=self.volatility_period).mean()
                df['volatility'] = df['atr'] / df['close']
                
                # Trend strength (using ADX)
                df['+dm'] = np.where((df['high'] - df['high'].shift()) > (df['low'].shift() - df['low']),
                                   np.maximum(df['high'] - df['high'].shift(), 0), 0)
                df['-dm'] = np.where((df['low'].shift() - df['low']) > (df['high'] - df['high'].shift()),
                                   np.maximum(df['low'].shift() - df['low'], 0), 0)
                df['+di'] = 100 * (df['+dm'].rolling(window=self.trend_period).mean() / df['atr'])
                df['-di'] = 100 * (df['-dm'].rolling(window=self.trend_period).mean() / df['atr'])
                df['dx'] = 100 * abs(df['+di'] - df['-di']) / (df['+di'] + df['-di'])
                df['adx'] = df['dx'].rolling(window=self.trend_period).mean()
                
                # Determine market regime
                regime = self._determine_market_regime(df)
                
                # Store data
                self.historical_data[instrument_id] = df
                self.ma_data[instrument_id] = {
                    'fast_ma': df['fast_ma'].iloc[-1],
                    'slow_ma': df['slow_ma'].iloc[-1],
                    'prev_fast_ma': df['fast_ma'].iloc[-2],
                    'prev_slow_ma': df['slow_ma'].iloc[-2],
                    'volatility': df['volatility'].iloc[-1],
                    'trend_strength': df['adx'].iloc[-1],
                    'regime': regime
                }
                
        except Exception as e:
            logger.error(f"Error updating market data: {str(e)}")
    
    async def _generate_signals(self):
        """Generate trading signals based on moving average crossovers."""
        try:
            for instrument in self.instruments:
                instrument_id = instrument['instrumentId']
                
                if instrument_id not in self.ma_data:
                    continue
                
                ma_data = self.ma_data[instrument_id]
                df = self.historical_data[instrument_id]
                
                # Check volume
                if df['volume'].iloc[-1] < self.min_volume:
                    continue
                
                # Check for crossovers
                prev_diff = ma_data['prev_fast_ma'] - ma_data['prev_slow_ma']
                curr_diff = ma_data['fast_ma'] - ma_data['slow_ma']
                
                signal = None
                
                # Bullish crossover (fast MA crosses above slow MA)
                if prev_diff <= 0 and curr_diff > 0:
                    signal = self._create_buy_signal(instrument)
                    logger.info(f"Bullish crossover detected for {instrument_id}")
                
                # Bearish crossover (fast MA crosses below slow MA)
                elif prev_diff >= 0 and curr_diff < 0:
                    signal = self._create_sell_signal(instrument)
                    logger.info(f"Bearish crossover detected for {instrument_id}")
                
                if signal:
                    self.signals[instrument_id] = signal
                    
        except Exception as e:
            logger.error(f"Error generating signals: {str(e)}")
    
    def _create_buy_signal(self, instrument: Dict) -> Dict:
        """Create a buy signal."""
        return {
            'active': True,
            'exchange': instrument['exchange'],
            'transaction_type': 'BUY',
            'quantity': self.position_size,
            'order_type': 'MARKET',
            'product': 'INTRADAY'
        }
    
    def _create_sell_signal(self, instrument: Dict) -> Dict:
        """Create a sell signal."""
        return {
            'active': True,
            'exchange': instrument['exchange'],
            'transaction_type': 'SELL',
            'quantity': self.position_size,
            'order_type': 'MARKET',
            'product': 'INTRADAY'
        }
    
    async def _update_metrics(self):
        """Update strategy-specific metrics."""
        await super()._update_metrics()
        
        try:
            # Calculate strategy-specific metrics
            for instrument_id, df in self.historical_data.items():
                if len(df) < self.lookback_period:
                    continue
                
                # Calculate daily returns
                df['returns'] = df['close'].pct_change()
                
                # Calculate Sharpe ratio (assuming daily data)
                returns_mean = df['returns'].mean() * 252  # Annualized return
                returns_std = df['returns'].std() * np.sqrt(252)  # Annualized volatility
                sharpe_ratio = returns_mean / returns_std if returns_std != 0 else 0
                
                # Update metrics
                self.metrics = {
                    **self.get_metrics(),
                    'sharpe_ratio': sharpe_ratio,
                    'volatility': returns_std * 100  # Convert to percentage
                }
                
        except Exception as e:
            logger.error(f"Error updating strategy metrics: {str(e)}")
