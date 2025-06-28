"""
Base News Source Module - Abstract base class for all news sources
Defines the interface and common functionality for news API integrations
"""
import logging
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import requests
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class NewsSourceConfig:
    """Configuration for a news source"""
    api_key: str
    base_url: str
    rate_limit_per_minute: int
    rate_limit_per_day: int
    enabled: bool = True
    priority: int = 1  # Higher number = higher priority


@dataclass
class RawNewsItem:
    """Raw news item from API before processing"""
    title: str
    content: str
    source: str
    url: str
    published_at: datetime
    raw_data: Dict  # Original API response data


class NewsSource(ABC):
    """Abstract base class for all news sources"""
    
    def __init__(self, config: NewsSourceConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MarketMan/1.0 (News Aggregator)'
        })
        
        # Rate limiting
        self.last_request_time = 0
        self.daily_request_count = 0
        self.daily_reset_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        logger.info(f"📰 {self.__class__.__name__} initialized with rate limit: {config.rate_limit_per_minute}/min, {config.rate_limit_per_day}/day")
    
    def _reset_daily_counter(self):
        """Reset daily request counter if it's a new day"""
        now = datetime.now()
        if now.date() > self.daily_reset_time.date():
            self.daily_request_count = 0
            self.daily_reset_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
            logger.debug(f"🔄 Daily counter reset for {self.__class__.__name__}")
    
    def _check_rate_limits(self) -> bool:
        """Check if we can make a request based on rate limits"""
        self._reset_daily_counter()
        
        # Check daily limit
        if self.daily_request_count >= self.config.rate_limit_per_day:
            logger.warning(f"🚫 Daily rate limit reached for {self.__class__.__name__}")
            return False
        
        # Check per-minute limit
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        min_interval = 60.0 / self.config.rate_limit_per_minute
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            logger.debug(f"⏳ Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        return True
    
    def _make_request(self, url: str, params: Dict = None, headers: Dict = None) -> Optional[Dict]:
        """Make a rate-limited request to the API"""
        if not self._check_rate_limits():
            return None
        
        try:
            # Update request time
            self.last_request_time = time.time()
            self.daily_request_count += 1
            
            # Make request
            response = self.session.get(url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                logger.warning(f"⚠️ Rate limited by {self.__class__.__name__}: {response.status_code}")
                return None
            else:
                logger.warning(f"⚠️ API error from {self.__class__.__name__}: {response.status_code}")
                try:
                    error_content = response.text[:200]  # First 200 chars
                    logger.warning(f"⚠️ Error response: {error_content}")
                except:
                    pass
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Request error from {self.__class__.__name__}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error from {self.__class__.__name__}: {e}")
            return None
    
    @abstractmethod
    def fetch_news(self, query: str = None, tickers: List[str] = None, 
                   hours_back: int = 24) -> List[RawNewsItem]:
        """
        Fetch news from this source
        
        Args:
            query: Search query (optional)
            tickers: List of ticker symbols to search for
            hours_back: How many hours back to fetch news
            
        Returns:
            List of RawNewsItem objects
        """
        pass
    
    @abstractmethod
    def get_source_name(self) -> str:
        """Get the name of this news source"""
        pass
    
    def get_rate_limit_stats(self) -> Dict:
        """Get current rate limiting statistics"""
        return {
            "source": self.get_source_name(),
            "daily_requests": self.daily_request_count,
            "daily_limit": self.config.rate_limit_per_day,
            "remaining_daily": self.config.rate_limit_per_day - self.daily_request_count,
            "rate_limit_per_minute": self.config.rate_limit_per_minute,
            "enabled": self.config.enabled
        }


class NewsSourceManager:
    """Manages multiple news sources and aggregates results"""
    
    def __init__(self, sources: List[NewsSource]):
        self.sources = sources
        # Sort by priority (highest first)
        self.sources.sort(key=lambda s: s.config.priority, reverse=True)
        
        logger.info(f"📰 NewsSourceManager initialized with {len(sources)} sources")
    
    def fetch_all_news(self, query: str = None, tickers: List[str] = None, 
                      hours_back: int = 24) -> List[RawNewsItem]:
        """Fetch news from all enabled sources"""
        all_news = []
        
        for source in self.sources:
            if not source.config.enabled:
                continue
            
            try:
                logger.debug(f"📰 Fetching from {source.get_source_name()}")
                news_items = source.fetch_news(query, tickers, hours_back)
                all_news.extend(news_items)
                logger.info(f"✅ {source.get_source_name()}: {len(news_items)} items")
                
            except Exception as e:
                logger.error(f"❌ Error fetching from {source.get_source_name()}: {e}")
                continue
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_news = []
        for item in all_news:
            if item.url not in seen_urls:
                seen_urls.add(item.url)
                unique_news.append(item)
        
        logger.info(f"📊 Total unique news items: {len(unique_news)}")
        return unique_news
    
    def get_all_stats(self) -> Dict:
        """Get statistics from all sources"""
        stats = {
            "total_sources": len(self.sources),
            "enabled_sources": len([s for s in self.sources if s.config.enabled]),
            "sources": []
        }
        
        for source in self.sources:
            source_stats = source.get_rate_limit_stats()
            stats["sources"].append(source_stats)
        
        return stats


def create_news_source_manager(sources: List[NewsSource]) -> NewsSourceManager:
    """Factory function to create NewsSourceManager"""
    return NewsSourceManager(sources) 