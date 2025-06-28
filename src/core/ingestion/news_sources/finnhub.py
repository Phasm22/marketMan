"""
Finnhub News Source - Financial news API integration
Provides real-time financial news with 60 calls/minute limit
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os

from .base import NewsSource, NewsSourceConfig, RawNewsItem

logger = logging.getLogger(__name__)


class FinnhubNewsSource(NewsSource):
    """Finnhub financial news source"""
    
    def __init__(self, api_key: str = None):
        if not api_key:
            api_key = os.getenv("FINNHUB_KEY")
        
        if not api_key:
            raise ValueError("Finnhub API key is required")
        
        config = NewsSourceConfig(
            api_key=api_key,
            base_url="https://finnhub.io/api/v1",
            rate_limit_per_minute=60,
            rate_limit_per_day=1000,
            enabled=True,
            priority=3  # High priority for financial news
        )
        
        super().__init__(config)
        
        # Add API key to session headers
        self.session.headers.update({
            'X-Finnhub-Token': api_key
        })
    
    def fetch_news(self, query: str = None, tickers: List[str] = None, 
                   hours_back: int = 24) -> List[RawNewsItem]:
        """Fetch news from Finnhub"""
        news_items = []
        
        # Calculate time range
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        
        # Convert to Unix timestamps
        start_timestamp = int(start_time.timestamp())
        end_timestamp = int(end_time.timestamp())
        
        # Build query parameters
        params = {
            'from': start_timestamp,
            'to': end_timestamp,
            'token': self.config.api_key
        }
        
        # Add tickers if provided
        if tickers:
            # Finnhub supports multiple tickers separated by comma
            params['symbol'] = ','.join(tickers[:10])  # Limit to 10 tickers per request
        
        # Add query if provided
        if query:
            params['q'] = query
        
        # Make request
        url = f"{self.config.base_url}/news"
        response_data = self._make_request(url, params=params)
        
        if not response_data:
            return []
        
        # Parse response
        articles = []
        if isinstance(response_data, dict):
            articles = response_data.get('result', [])
        elif isinstance(response_data, list):
            articles = response_data
        else:
            logger.warning(f"⚠️ Unexpected Finnhub response format: {type(response_data)}")
            return []
        
        for article in articles:
            try:
                # Parse timestamp
                published_at = datetime.fromtimestamp(article.get('datetime', 0))
                
                # Extract content
                title = article.get('headline', '')
                content = article.get('summary', '')
                source = article.get('source', 'Finnhub')
                url = article.get('url', '')
                
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
                logger.warning(f"⚠️ Error parsing Finnhub article: {e}")
                continue
        
        logger.info(f"📰 Finnhub: fetched {len(news_items)} news items")
        return news_items
    
    def get_source_name(self) -> str:
        return "Finnhub"
    
    def fetch_company_news(self, ticker: str, hours_back: int = 24) -> List[RawNewsItem]:
        """Fetch company-specific news"""
        return self.fetch_news(tickers=[ticker], hours_back=hours_back)
    
    def fetch_market_news(self, hours_back: int = 24) -> List[RawNewsItem]:
        """Fetch general market news"""
        return self.fetch_news(hours_back=hours_back)


def create_finnhub_source(api_key: str = None) -> FinnhubNewsSource:
    """Factory function to create Finnhub news source"""
    return FinnhubNewsSource(api_key) 