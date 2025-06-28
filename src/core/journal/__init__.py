"""
Journal module for MarketMan.

This module provides trade journaling, performance tracking, and signal logging functionality.
"""

from .alert_batcher import AlertBatcher

# Phase 3 components
from .trade_journal import TradeJournal, TradeEntry, create_trade_journal, log_trade_from_dict
from .performance_tracker import PerformanceTracker, PerformanceMetrics, create_performance_tracker, generate_performance_report
from .signal_logger import SignalLogger, SignalEntry, create_signal_logger, log_news_signal, log_technical_signal, generate_signal_report

__all__ = [
    # Existing components
    "AlertBatcher",
    
    # Phase 3 components
    "TradeJournal",
    "TradeEntry",
    "create_trade_journal",
    "log_trade_from_dict",
    "PerformanceTracker",
    "PerformanceMetrics",
    "create_performance_tracker",
    "generate_performance_report",
    "SignalLogger",
    "SignalEntry",
    "create_signal_logger",
    "log_news_signal",
    "log_technical_signal",
    "generate_signal_report"
]
