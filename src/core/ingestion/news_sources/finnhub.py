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
    
    def __init__(self, api_key: Optional[str] = None, config: dict = None):
        if not api_key:
            api_key = os.getenv("FINNHUB_KEY")
        
        if not api_key:
            raise ValueError("Finnhub API key is required")
        
        self.config_dict = config or {}
        self.per_source_limit = self.config_dict.get('news_ingestion', {}).get('per_source_limit', 100)
        
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
    
    def fetch_news(self, query: Optional[str] = None, tickers: Optional[List[str]] = None, 
                   hours_back: int = 24) -> List[RawNewsItem]:
        """Fetch news from Finnhub
        - If tickers are provided, use /company-news for each ticker (more precise, less noise)
        - If no tickers, use /news (general market news, more noise)
        - 'q' param is ignored by Finnhub and not sent
        """
        news_items = []
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        start_date = start_time.strftime('%Y-%m-%d')
        end_date = end_time.strftime('%Y-%m-%d')
        # If tickers are provided, use /company-news for each ticker
        if tickers:
            for ticker in tickers[:10]:  # Limit to 10 tickers per cycle
                params = {
                    'symbol': ticker,
                    'from': start_date,
                    'to': end_date,
                    'token': self.config.api_key
                }
                url = f"{self.config.base_url}/company-news"
                response_data = self._make_request(url, params=params)
                news_items_for_ticker = self._parse_response(response_data, ticker=ticker)
                news_items.extend(news_items_for_ticker[:self.per_source_limit])
        else:
            # General market news
            params = {
                'category': 'general',
                'token': self.config.api_key
            }
            url = f"{self.config.base_url}/news"
            response_data = self._make_request(url, params=params)
            news_items.extend(self._parse_response(response_data)[:self.per_source_limit])
        logger.info(f"📰 Finnhub: fetched {len(news_items)} news items")
        return news_items

    def _parse_response(self, response_data, ticker=None):
        """Parse Finnhub API response, log warnings for missing datetime, testable for edge cases."""
        news_items = []
        if not response_data:
            return news_items
        articles = []
        if isinstance(response_data, dict):
            articles = response_data.get('result', [])
        elif isinstance(response_data, list):
            articles = response_data
        else:
            logger.warning(f"⚠️ Unexpected Finnhub response format: {type(response_data)}")
            return news_items
        for article in articles:
            try:
                dt = article.get('datetime')
                if not dt:
                    logger.warning(f"Finnhub article missing datetime: {article}")
                    published_at = datetime.fromtimestamp(0)
                else:
                    try:
                        published_at = datetime.fromtimestamp(dt)
                    except Exception:
                        logger.warning(f"Finnhub article has malformed datetime: {dt} | {article}")
                        published_at = datetime.fromtimestamp(0)
                title = article.get('headline', '')
                content = article.get('summary', '')
                source = article.get('source', 'Finnhub')
                url = article.get('url', '')
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
        return news_items
    
    def get_source_name(self) -> str:
        return "Finnhub"
    
    def fetch_company_news(self, ticker: str, hours_back: int = 24) -> List[RawNewsItem]:
        """Fetch company-specific news"""
        return self.fetch_news(tickers=[ticker], hours_back=hours_back)
    
    def fetch_market_news(self, hours_back: int = 24) -> List[RawNewsItem]:
        """Fetch general market news"""
        return self.fetch_news(hours_back=hours_back)


def create_finnhub_source(api_key: Optional[str] = None) -> FinnhubNewsSource:
    """Factory function to create Finnhub news source"""
    return FinnhubNewsSource(api_key) 