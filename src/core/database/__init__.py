"""
Database abstraction layer for MarketMan.

This module contains all database operations including:
- Market memory management
- Data persistence
- Database connections and queries
- Data validation and integrity
"""

from .market_memory import MarketMemory

__all__ = ['MarketMemory'] 