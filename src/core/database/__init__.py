"""
Database abstraction layer for MarketMan.

This module contains all database operations including:
- Market memory management
- Data persistence
- Database connections and queries
- Data validation and integrity
"""

from .market_memory import MarketMemory
from .db_manager import (
    DatabaseManager,
    MarketMemoryDB,
    AlertBatchDB,
    market_memory_db,
    alert_batch_db,
)

__all__ = [
    "MarketMemory",
    "DatabaseManager",
    "MarketMemoryDB",
    "AlertBatchDB",
    "market_memory_db",
    "alert_batch_db",
]
