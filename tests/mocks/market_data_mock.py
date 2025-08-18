"""
Mock IIFL client for testing purposes.
"""
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

class MockIIFLMarketDataClient:
    """Mock IIFL client that provides simulated market data."""
    
    def __init__(self, session_token: str = "test_token"):
        """Initialize mock client."""
        self.session_token = session_token
        self.connected = True
        
    async def get_market_quotes(self, instruments):
        """Get mock market quotes."""
        result = []
        for instrument in instruments:
            result.append({
                'exchange': instrument['exchange'],
                'instrumentId': instrument['instrumentId'],
                'ltp': 100.0 + np.random.normal(0, 1),
                'open': 100.0,
                'high': 101.0,
                'low': 99.0,
                'close': 100.5,
                'volume': 1000000
            })
        return {'status': 'success', 'result': result}
        
    async def get_historical_data(self, exchange, instrument_id, interval, from_date, to_date):
        """Get mock historical data."""
        from_dt = datetime.strptime(from_date, "%d-%b-%Y")
        to_dt = datetime.strptime(to_date, "%d-%b-%Y")
        dates = pd.date_range(start=from_dt, end=to_dt, freq='D')
        
        data = []
        base_price = 100.0
        for date in dates:
            data.append({
                'timestamp': date.strftime("%Y-%m-%d %H:%M:%S"),
                'open': base_price + np.random.normal(0, 0.5),
                'high': base_price + 1 + np.random.normal(0, 0.5),
                'low': base_price - 1 + np.random.normal(0, 0.5),
                'close': base_price + np.random.normal(0, 0.5),
                'volume': int(1000000 + np.random.normal(0, 100000))
            })
            base_price += np.random.normal(0, 0.1)
            
        return {'status': 'success', 'result': data}
        
    async def get_market_depth(self, exchange, instrument_id):
        """Get mock market depth."""
        return {
            'status': 'success',
            'result': {
                'bids': [
                    {'price': 99.9, 'quantity': 100},
                    {'price': 99.8, 'quantity': 200},
                    {'price': 99.7, 'quantity': 300}
                ],
                'asks': [
                    {'price': 100.1, 'quantity': 150},
                    {'price': 100.2, 'quantity': 250},
                    {'price': 100.3, 'quantity': 350}
                ]
            }
        }
