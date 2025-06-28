"""
Data ingestion module for MarketMan.

This module contains all data ingestion and validation logic including:
- Market data collection
- Data validation and cleaning
- Real-time data feeds
- Historical data import
"""

from .market_data import MarketData

__all__ = ['MarketData'] 