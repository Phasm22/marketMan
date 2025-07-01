"""
NewData News Source - Alternative financial news API
Provides financial news with 200 requests/day limit
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os

from .base import NewsSource, NewsSourceConfig, RawNewsItem

logger = logging.getLogger(__name__)


class NewDataSource(NewsSource):
    """NewData financial news source"""
    
    def __init__(self, api_key: str = None, config: dict = None):
        if not api_key:
            api_key = os.getenv("NEWS_DATA_KEY")
        
        if not api_key:
            raise ValueError("NewData API key is required")
        
        self.config_dict = config or {}
        self.per_source_limit = self.config_dict.get('news_ingestion', {}).get('per_source_limit', 100)
        
        config = NewsSourceConfig(
            api_key=api_key,
            base_url="https://newsdata.io/api/1",  # Correct endpoint
            rate_limit_per_minute=10,  # Conservative rate limiting
            rate_limit_per_day=200,
            enabled=True,
            priority=1  # Lower priority, use as backup
        )
        
        super().__init__(config)
        
        # Add API key to session headers
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}'
        })
    
    def _parse_article(self, article: dict, is_market: bool = False) -> Optional[RawNewsItem]:
        """Helper to parse a single article dict into RawNewsItem, with robust date handling."""
        try:
            if is_market:
                published_str = article.get('published_at', '')
                published_at = None
                if published_str:
                    try:
                        published_at = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
                    except Exception as e:
                        logger.warning(f"⚠️ NewData: ISO date parse failed for '{published_str}': {e}")
                        published_at = datetime.now()
                else:
                    published_at = datetime.now()
                title = article.get('title', '')
                content = article.get('summary', '')
                source = article.get('source', 'NewData')
                url = article.get('url', '')
            else:
                published_str = article.get('pubDate', '')
                if published_str:
                    try:
                        published_at = datetime.strptime(published_str, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        logger.warning(f"⚠️ NewData: pubDate parse failed for '{published_str}', using now().")
                        published_at = datetime.now()
                else:
                    published_at = datetime.now()
                title = article.get('title', '')
                content = article.get('description', '') or article.get('content', '')
                source = article.get('source_name', 'NewData')
                url = article.get('link', '')
            # Skip articles with no content or if content is restricted
            if not title or not content or content == "ONLY AVAILABLE IN PAID PLANS":
                return None
            return RawNewsItem(
                title=title,
                content=content,
                source=source,
                url=url,
                published_at=published_at,
                raw_data=article
            )
        except Exception as e:
            logger.warning(f"⚠️ Error parsing NewData article: {e}")
            return None
    
    def fetch_news(self, query: str = None, tickers: List[str] = None, 
                   hours_back: int = 24) -> List[RawNewsItem]:
        """Fetch news from NewData"""
        news_items = []
        
        # Calculate time range
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        
        # Build query parameters
        params = {
            'apikey': self.config.api_key,  # Use 'apikey' parameter
            'language': 'en'
        }
        
        # Add tickers if provided
        if tickers:
            params['q'] = ' OR '.join(tickers[:5])  # Use 'q' for query
        
        # Add query if provided
        if query:
            if 'q' in params:
                params['q'] = f"{params['q']} AND {query}"
            else:
                params['q'] = query
        
        # Make request
        url = f"{self.config.base_url}/news"
        logger.debug(f"📰 NewData requesting: {url} with params: {params}")
        response_data = self._make_request(url, params=params)
        
        if not response_data:
            return []
        
        # Parse response
        if not response_data or response_data.get('status') != 'success':
            logger.warning(f"⚠️ NewData API error: {response_data}")
            return []
        
        articles = response_data.get('results', [])
        
        for article in articles:
            news_item = self._parse_article(article, is_market=False)
            if news_item:
                news_items.append(news_item)
            if len(news_items) >= self.per_source_limit:
                break
        
        logger.info(f"📰 NewData: fetched {len(news_items)} news items")
        return news_items
    
    def get_source_name(self) -> str:
        return "NewData"
    
    def fetch_market_news(self, hours_back: int = 24) -> List[RawNewsItem]:
        """Fetch general market news"""
        params = {
            'category': 'market',
            'limit': 20,
            'apikey': self.config.api_key  # Ensure API key is always included
        }
        
        url = f"{self.config.base_url}/news"
        response_data = self._make_request(url, params=params)
        
        if not response_data:
            return []
        
        # Check for status field for consistency
        if response_data.get('status') and response_data.get('status') != 'success':
            logger.warning(f"⚠️ NewData market API error: {response_data}")
            return []
        
        news_items = []
        articles = response_data.get('data', [])
        
        for article in articles:
            news_item = self._parse_article(article, is_market=True)
            if news_item:
                news_items.append(news_item)
        
        logger.info(f"📰 NewData: fetched {len(news_items)} market news items")
        return news_items


def create_newdata_source(api_key: str = None) -> NewDataSource:
    """Factory function to create NewData source"""
    return NewDataSource(api_key) 