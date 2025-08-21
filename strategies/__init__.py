"""
Strategy package initialization.
"""
from .base_strategy import BaseStrategy
from .ma_crossover import MACrossoverStrategy, MACrossoverStrategy as MovingAverageCrossoverStrategy

__all__ = ['BaseStrategy', 'MovingAverageCrossoverStrategy', 'MACrossoverStrategy']
