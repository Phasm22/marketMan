"""
Signal processing module for MarketMan.

This module contains all signal processing logic including:
- ETF signal engines
- News signal orchestrators
- Technical analysis signals
- Signal validation and filtering
"""

from .etf_signal_engine import ETFSignalEngine
from .news_signal_orchestrator import NewsSignalOrchestrator

__all__ = ['ETFSignalEngine', 'NewsSignalOrchestrator'] 