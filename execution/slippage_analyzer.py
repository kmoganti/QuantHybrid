"""
Slippage analyzer for order execution.
"""
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from config.logging_config import get_logger
from database.database_manager import DatabaseManager
from database.models import Trade, Order

logger = get_logger('execution')

class SlippageAnalyzer:
    """Analyzes and predicts execution slippage."""
    
    def __init__(self):
        self.slippage_stats = {}
        self.historical_slippage = pd.DataFrame()
    
    async def calculate_slippage(self, trade: Trade, intended_price: float) -> float:
        """Calculate slippage for a trade."""
        try:
            slippage = (trade.price - intended_price) / intended_price * 100
            
            # Update statistics
            instrument_id = trade.instrument_id
            if instrument_id not in self.slippage_stats:
                self.slippage_stats[instrument_id] = []
            
            self.slippage_stats[instrument_id].append(slippage)
            
            logger.info(f"Slippage for trade {trade.id}: {slippage:.4f}%")
            return slippage
            
        except Exception as e:
            logger.error(f"Error calculating slippage: {str(e)}")
            return 0.0
    
    async def analyze_slippage_patterns(self, instrument_id: str, lookback_days: int = 30) -> Dict:
        """Analyze slippage patterns for an instrument."""
        try:
            # Get historical trades
            db_manager = DatabaseManager(test_mode=True)
            trades = await db_manager.get_items(
                Trade,
                instrument_id=instrument_id
            )
            
            if not trades:
                return {}
            
            # Calculate statistics
            slippages = self.slippage_stats.get(instrument_id, [])
            if not slippages:
                return {}
            
            stats = {
                'mean_slippage': np.mean(slippages),
                'median_slippage': np.median(slippages),
                'std_slippage': np.std(slippages),
                'max_slippage': np.max(slippages),
                'min_slippage': np.min(slippages)
            }
            
            logger.info(f"Slippage analysis for {instrument_id}: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error analyzing slippage patterns: {str(e)}")
            return {}
    
    def predict_slippage(self, instrument_id: str, order_size: int) -> float:
        """Predict potential slippage for an order."""
        try:
            stats = self.slippage_stats.get(instrument_id, [])
            if not stats:
                return 0.0
            
            # Simple prediction based on historical statistics
            mean_slippage = np.mean(stats)
            std_slippage = np.std(stats)
            
            # Adjust prediction based on order size
            size_factor = 1.0  # TODO: Implement size-based adjustment
            
            predicted_slippage = mean_slippage + std_slippage * size_factor
            
            logger.info(f"Predicted slippage for {instrument_id}: {predicted_slippage:.4f}%")
            return predicted_slippage
            
        except Exception as e:
            logger.error(f"Error predicting slippage: {str(e)}")
            return 0.0
    
    async def get_slippage_report(self) -> Dict:
        """Generate slippage report."""
        try:
            report = {
                'overall_stats': {},
                'instrument_stats': {}
            }
            
            all_slippages = []
            for instrument_id, slippages in self.slippage_stats.items():
                all_slippages.extend(slippages)
                report['instrument_stats'][instrument_id] = {
                    'mean_slippage': np.mean(slippages),
                    'median_slippage': np.median(slippages),
                    'std_slippage': np.std(slippages),
                    'sample_size': len(slippages)
                }
            
            if all_slippages:
                report['overall_stats'] = {
                    'mean_slippage': np.mean(all_slippages),
                    'median_slippage': np.median(all_slippages),
                    'std_slippage': np.std(all_slippages),
                    'total_trades': len(all_slippages)
                }
            
            logger.info("Generated slippage report")
            return report
            
        except Exception as e:
            logger.error(f"Error generating slippage report: {str(e)}")
            return {}
