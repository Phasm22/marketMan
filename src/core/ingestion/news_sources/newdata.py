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
    
    def __init__(self, api_key: str = None):
        if not api_key:
            api_key = os.getenv("NEWS_DATA_KEY")
        
        if not api_key:
            raise ValueError("NewData API key is required")
        
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
            try:
                # Parse published date
                published_str = article.get('pubDate', '')
                if published_str:
                    # Handle format: "2025-06-28 07:32:00"
                    try:
                        published_at = datetime.strptime(published_str, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        published_at = datetime.now()
                else:
                    published_at = datetime.now()
                
                # Extract content
                title = article.get('title', '')
                content = article.get('description', '') or article.get('content', '')
                source = article.get('source_name', 'NewData')
                url = article.get('link', '')
                
                # Skip articles with no content or if content is restricted
                if not title or not content or content == "ONLY AVAILABLE IN PAID PLANS":
                    continue
                
                # Create RawNewsItem
                news_item = RawNewsItem(
                    title=title,
                    content=content,
                    source=source,
                    url=url,
                    published_at=published_at,
                    raw_data=article
                )
                
                news_items.append(news_item)
                
            except Exception as e:
                logger.warning(f"⚠️ Error parsing NewData article: {e}")
                continue
        
        logger.info(f"📰 NewData: fetched {len(news_items)} news items")
        return news_items
    
    def get_source_name(self) -> str:
        return "NewData"
    
    def fetch_market_news(self, hours_back: int = 24) -> List[RawNewsItem]:
        """Fetch general market news"""
        params = {
            'category': 'market',
            'limit': 20
        }
        
        url = f"{self.config.base_url}/news"
        response_data = self._make_request(url, params=params)
        
        if not response_data:
            return []
        
        news_items = []
        articles = response_data.get('data', [])
        
        for article in articles:
            try:
                published_str = article.get('published_at', '')
                if published_str:
                    published_at = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
                else:
                    published_at = datetime.now()
                
                news_item = RawNewsItem(
                    title=article.get('title', ''),
                    content=article.get('summary', ''),
                    source=article.get('source', 'NewData'),
                    url=article.get('url', ''),
                    published_at=published_at,
                    raw_data=article
                )
                
                news_items.append(news_item)
                
            except Exception as e:
                logger.warning(f"⚠️ Error parsing NewData market article: {e}")
                continue
        
        return news_items


def create_newdata_source(api_key: str = None) -> NewDataSource:
    """Factory function to create NewData source"""
    return NewDataSource(api_key) 