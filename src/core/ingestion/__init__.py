"""
MarketMan Ingestion Module - Data collection and processing
Handles market data, news ingestion, and real-time data streams
"""

# Core ingestion components
from .news_orchestrator import NewsIngestionOrchestrator, create_news_orchestrator

# News filtering and batching
from .news_filter import NewsFilter, NewsItem, create_news_filter
from .news_batcher import NewsBatcher, NewsBatch, create_news_batcher

# News sources
from .news_sources.base import NewsSource, NewsSourceManager, RawNewsItem
from .news_sources.finnhub import FinnhubNewsSource, create_finnhub_source
from .news_sources.newsapi import NewsAPISource, create_newsapi_source
from .news_sources.newdata import NewDataSource, create_newdata_source

__all__ = [
    # Core components
    'NewsIngestionOrchestrator',
    'create_news_orchestrator',
    
    # News filtering and batching
    'NewsFilter',
    'NewsItem',
    'create_news_filter',
    'NewsBatcher',
    'NewsBatch',
    'create_news_batcher',
    
    # News sources
    'NewsSource',
    'NewsSourceManager',
    'RawNewsItem',
    'FinnhubNewsSource',
    'create_finnhub_source',
    'NewsAPISource',
    'create_newsapi_source',
    'NewDataSource',
    'create_newdata_source',
]
