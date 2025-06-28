"""
Signal processing module for MarketMan.

This module contains all signal processing logic including:
- ETF signal engines
- News signal orchestrators
- Technical analysis signals
- Signal validation and filtering
"""

from .etf_signal_engine import (
    analyze_thematic_etf_news,
    generate_tactical_explanation,
    categorize_etfs_by_sector,
)
from .news_signal_orchestrator import NewsAnalyzer

__all__ = [
    "analyze_thematic_etf_news",
    "generate_tactical_explanation",
    "categorize_etfs_by_sector",
    "NewsAnalyzer",
]
