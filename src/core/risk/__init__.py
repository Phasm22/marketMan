"""
Risk management module for MarketMan.

This module contains all risk management logic including:
- Position sizing calculations
- Stop-loss logic
- Risk metrics and monitoring
- Portfolio risk assessment
"""

from .position_sizing import PositionSizer, PositionSizeResult

__all__ = ["PositionSizer", "PositionSizeResult"]
