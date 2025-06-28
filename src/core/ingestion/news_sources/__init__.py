"""
News Sources Module - Multiple news API integrations
Provides unified interface for various financial news sources
"""

from .base import NewsSource, NewsSourceManager, RawNewsItem, NewsSourceConfig
from .finnhub import FinnhubNewsSource, create_finnhub_source
from .newsapi import NewsAPISource, create_newsapi_source
from .newdata import NewDataSource, create_newdata_source

__all__ = [
    'NewsSource',
    'NewsSourceManager',
    'RawNewsItem',
    'NewsSourceConfig',
    'FinnhubNewsSource',
    'create_finnhub_source',
    'NewsAPISource',
    'create_newsapi_source',
    'NewDataSource',
    'create_newdata_source',
] 