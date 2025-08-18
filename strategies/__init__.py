"""
Strategy package initialization.
"""
from .base_strategy import BaseStrategy
from .ma_crossover import MovingAverageCrossoverStrategy

__all__ = ['BaseStrategy', 'MovingAverageCrossoverStrategy']
