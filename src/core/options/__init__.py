"""
Options trading module for MarketMan.

This module contains all options trading logic including:
- Scalping strategies for QQQ/SPY
- Options analytics and metrics
- Options backtesting
- Broker API integration for options
"""

from .scalping_strategy import OptionsScalpingStrategy, ScalpingSignal, ScalpingPosition

__all__ = ["OptionsScalpingStrategy", "ScalpingSignal", "ScalpingPosition"]
