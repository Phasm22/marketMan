"""
NewsAPI News Source - General news API integration
Provides general news with 100 requests/day limit
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os

from .base import NewsSource, NewsSourceConfig, RawNewsItem

logger = logging.getLogger(__name__)


class NewsAPISource(NewsSource):
    """NewsAPI general news source"""
    
    def __init__(self, api_key: str = "", config: dict = None):
        if not api_key:
            api_key = os.getenv("NEWS_API", "")
        
        if not api_key:
            raise ValueError("NewsAPI key is required")
        
        self.config_dict = config or {}
        self.per_source_limit = self.config_dict.get('news_ingestion', {}).get('per_source_limit', 100)
        
        config_obj = NewsSourceConfig(
            api_key=api_key,
            base_url="https://newsapi.org/v2",
            rate_limit_per_minute=5,  # Conservative rate limiting
            rate_limit_per_day=100,
            enabled=True,
            priority=2  # Medium priority
        )
        
        super().__init__(config_obj)
    
    def fetch_news(self, query: str = "", tickers: Optional[List[str]] = None, 
                   hours_back: int = 24) -> List[RawNewsItem]:
        """Fetch news from NewsAPI"""
        news_items = []
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=hours_back)
        
        # Build query
        search_query = self._build_search_query(query, tickers or [])
        
        # Build parameters
        params = {
            'q': search_query,
            'from': start_date.strftime('%Y-%m-%d'),
            'to': end_date.strftime('%Y-%m-%d'),
            'language': 'en',
            'sortBy': 'publishedAt',
            'apiKey': self.config.api_key,
            'pageSize': self.per_source_limit  # Use config value
        }
        
        logger.debug(f"📰 NewsAPI query: {search_query}")
        
        # Make request
        url = f"{self.config.base_url}/everything"
        response_data = self._make_request(url, params=params)
        
        if not response_data:
            logger.warning("⚠️ NewsAPI returned no data")
            return []
        
        # Parse response
        articles = response_data.get('articles', [])
        
        if not articles:
            logger.info("📰 NewsAPI: No articles found for query")
            return []
        
        for article in articles:
            try:
                # Parse published date
                published_str = article.get('publishedAt', '')
                if published_str:
                    published_at = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
                else:
                    published_at = datetime.now()
                
                # Extract content
                title = article.get('title', '')
                content = article.get('description', '') or article.get('content', '')
                source = article.get('source', {}).get('name', 'NewsAPI')
                url = article.get('url', '')
                
                # Skip articles with no content
                if not title or not content:
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
                logger.warning(f"⚠️ Error parsing NewsAPI article: {e}")
                continue
        
        logger.info(f"📰 NewsAPI: fetched {len(news_items)} news items")
        return news_items
    
    def _build_search_query(self, query: str = "", tickers: Optional[List[str]] = None) -> str:
        """Build search query for NewsAPI"""
        search_terms = []
        
        # Add base query
        if query:
            search_terms.append(query)
        
        # Add tickers
        if tickers:
            ticker_terms = [f'"{ticker}"' for ticker in tickers[:5]]  # Limit to 5 tickers
            search_terms.extend(ticker_terms)
        
        # Add ETF-focused keywords if no specific query
        if not search_terms:
            search_terms = [
                'ETF',
                'ETF flows',
                'ETF allocation',
                'sector ETF',
                'thematic ETF',
                'index fund',
                'exchange traded fund',
                'fund rebalancing',
                'sector rotation',
                'stock market'
            ]
        
        # Combine with OR operator
        return ' OR '.join(search_terms)
    
    def get_source_name(self) -> str:
        return "NewsAPI"
    
    def fetch_business_news(self, hours_back: int = 24) -> List[RawNewsItem]:
        """Fetch business news specifically"""
        params = {
            'category': 'business',
            'language': 'en',
            'sortBy': 'publishedAt',
            'apiKey': self.config.api_key,
            'pageSize': self.per_source_limit  # Use config value
        }
        url = f"{self.config.base_url}/top-headlines"
        response_data = self._make_request(url, params=params)
        if not response_data:
            logger.warning("⚠️ NewsAPI business returned no data")
            return []
        # Check for error/status field for consistency
        if ("status" in response_data and response_data["status"] != "ok") or response_data.get("code"):
            logger.warning(f"⚠️ NewsAPI business API error: {response_data}")
            return []
        news_items = []
        articles = response_data.get('articles', [])
        for article in articles:
            try:
                published_str = article.get('publishedAt', '')
                if published_str:
                    try:
                        published_at = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
                    except Exception as e:
                        logger.warning(f"⚠️ NewsAPI: publishedAt parse failed for '{published_str}': {e}")
                        published_at = datetime.now()
                else:
                    published_at = datetime.now()
                # Fallback to content if description is empty
                content = article.get('description', '') or article.get('content', '')
                news_item = RawNewsItem(
                    title=article.get('title', ''),
                    content=content,
                    source=article.get('source', {}).get('name', 'NewsAPI'),
                    url=article.get('url', ''),
                    published_at=published_at,
                    raw_data=article
                )
                news_items.append(news_item)
            except Exception as e:
                logger.warning(f"⚠️ Error parsing NewsAPI business article: {e}")
                continue
        return news_items


def create_newsapi_source(api_key: str = "") -> NewsAPISource:
    """Factory function to create NewsAPI source"""
    return NewsAPISource(api_key) 