"""
News Filter Module - Cost-effective pre-filtering before AI analysis
Implements intelligent filtering to reduce AI API costs while maintaining signal quality
"""
import re
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
import hashlib
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


@dataclass
class NewsItem:
    """Standardized news item structure"""
    title: str
    content: str
    source: str
    url: str
    published_at: datetime
    tickers: List[str]
    keywords: List[str]
    hash_id: str
    
    def __post_init__(self):
        if not self.hash_id:
            # Create hash from title + content for duplicate detection
            content_str = f"{self.title}{self.content}"
            self.hash_id = hashlib.md5(content_str.encode()).hexdigest()


class NewsFilter:
    """Intelligent news filtering to reduce AI API costs"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.news_config = config.get('news_ingestion', {})
        
        # Extract configuration
        self.max_daily_headlines = self.news_config.get('max_daily_headlines', 20)
        self.tracked_tickers = set(self.news_config.get('tracked_tickers', []))
        self.keywords = set(self.news_config.get('keywords', []))
        self.market_hours = self.news_config.get('market_hours', {})
        
        # Duplicate detection
        self.duplicate_config = self.news_config.get('duplicate_detection', {})
        self.duplicate_enabled = self.duplicate_config.get('enabled', True)
        self.duplicate_window_hours = self.duplicate_config.get('time_window_hours', 24)
        self.similarity_threshold = self.duplicate_config.get('similarity_threshold', 0.8)
        
        # Daily counters
        self.daily_headline_count = 0
        self.daily_reset_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self.processed_hashes = set()
        
        # Compile regex patterns for efficiency
        self._compile_patterns()
        
        logger.info(f"📰 NewsFilter initialized with {len(self.tracked_tickers)} tracked tickers, {len(self.keywords)} keywords")
    
    def _compile_patterns(self):
        """Compile regex patterns for efficient matching"""
        # Create case-insensitive patterns
        self.ticker_pattern = re.compile(r'\b(' + '|'.join(self.tracked_tickers) + r')\b', re.IGNORECASE)
        self.keyword_pattern = re.compile(r'\b(' + '|'.join(self.keywords) + r')\b', re.IGNORECASE)
    
    def _reset_daily_counters(self):
        """Reset daily counters if it's a new day"""
        now = datetime.now()
        if now.date() > self.daily_reset_time.date():
            self.daily_headline_count = 0
            self.daily_reset_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
            self.processed_hashes.clear()
            logger.info("🔄 Daily news counters reset")
    
    def _is_market_hours(self, timestamp: datetime) -> bool:
        """Check if timestamp is during market hours"""
        if not self.market_hours:
            return True  # No restrictions if not configured
        
        start_time = self.market_hours.get('start', '09:30')
        end_time = self.market_hours.get('end', '16:00')
        
        try:
            start_hour, start_minute = map(int, start_time.split(':'))
            end_hour, end_minute = map(int, end_time.split(':'))
            
            current_time = timestamp.time()
            market_start = timestamp.replace(hour=start_hour, minute=start_minute).time()
            market_end = timestamp.replace(hour=end_hour, minute=end_minute).time()
            
            return market_start <= current_time <= market_end
        except Exception as e:
            logger.warning(f"⚠️ Error checking market hours: {e}")
            return True  # Default to allowing if error
    
    def _extract_tickers(self, text: str) -> List[str]:
        """Extract ticker symbols from text"""
        matches = self.ticker_pattern.findall(text)
        return list(set(matches))  # Remove duplicates
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        matches = self.keyword_pattern.findall(text)
        return list(set(matches))  # Remove duplicates
    
    def _is_duplicate(self, news_item: NewsItem) -> bool:
        """Check if news item is a duplicate of previously processed content"""
        if not self.duplicate_enabled:
            return False
        
        # Check exact hash match
        if news_item.hash_id in self.processed_hashes:
            return True
        
        # Check similarity with recent items
        cutoff_time = datetime.now() - timedelta(hours=self.duplicate_window_hours)
        
        # For now, we'll use a simple approach. In production, you'd store recent items in a database
        # and check similarity against them
        return False
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts using SequenceMatcher"""
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    def filter_news(self, raw_news_items: List[Dict]) -> Tuple[List[NewsItem], Dict]:
        """
        Filter news items based on configured rules
        
        Returns:
            Tuple of (filtered_news_items, filter_stats)
        """
        self._reset_daily_counters()
        
        if self.daily_headline_count >= self.max_daily_headlines:
            logger.info(f"🚫 Daily headline limit reached ({self.max_daily_headlines}), skipping processing")
            return [], {"reason": "daily_limit_reached", "processed": 0}
        
        filtered_items = []
        stats = {
            "total_received": len(raw_news_items),
            "filtered_out": 0,
            "reasons": {}
        }
        
        for raw_item in raw_news_items:
            try:
                # Convert to NewsItem
                news_item = self._create_news_item(raw_item)
                
                # Apply filters
                should_process, reason = self._apply_filters(news_item)
                
                if should_process:
                    filtered_items.append(news_item)
                    self.processed_hashes.add(news_item.hash_id)
                    self.daily_headline_count += 1
                    
                    logger.debug(f"✅ Accepted: {news_item.title[:60]}... (Tickers: {news_item.tickers})")
                else:
                    stats["filtered_out"] += 1
                    stats["reasons"][reason] = stats["reasons"].get(reason, 0) + 1
                    logger.debug(f"❌ Filtered: {news_item.title[:60]}... (Reason: {reason})")
                
                # Check daily limit
                if self.daily_headline_count >= self.max_daily_headlines:
                    logger.info(f"🚫 Daily limit reached after processing {len(filtered_items)} items")
                    break
                    
            except Exception as e:
                logger.warning(f"⚠️ Error processing news item: {e}")
                stats["filtered_out"] += 1
                continue
        
        stats["processed"] = len(filtered_items)
        stats["remaining_daily_budget"] = self.max_daily_headlines - self.daily_headline_count
        
        logger.info(f"📊 News filtering complete: {stats['processed']}/{stats['total_received']} items accepted")
        return filtered_items, stats
    
    def _create_news_item(self, raw_item: Dict) -> NewsItem:
        """Convert raw news item to standardized NewsItem"""
        # Handle different date formats
        published_at = raw_item.get('published_at')
        if isinstance(published_at, str):
            try:
                published_at = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            except:
                published_at = datetime.now()
        elif not isinstance(published_at, datetime):
            published_at = datetime.now()
        
        # Extract text content
        title = raw_item.get('title', '')
        content = raw_item.get('content', '') or raw_item.get('description', '') or raw_item.get('summary', '')
        
        # Combine title and content for analysis
        full_text = f"{title} {content}"
        
        # Extract tickers and keywords
        tickers = self._extract_tickers(full_text)
        keywords = self._extract_keywords(full_text)
        
        return NewsItem(
            title=title,
            content=content,
            source=raw_item.get('source', 'unknown'),
            url=raw_item.get('url', ''),
            published_at=published_at,
            tickers=tickers,
            keywords=keywords,
            hash_id=''  # Will be set in __post_init__
        )
    
    def _apply_filters(self, news_item: NewsItem) -> Tuple[bool, str]:
        """Apply all filters to a news item"""
        
        # 1. Market hours filter
        if not self._is_market_hours(news_item.published_at):
            return False, "outside_market_hours"
        
        # 2. Duplicate filter
        if self._is_duplicate(news_item):
            return False, "duplicate_content"
        
        # 3. Ticker relevance filter
        if not news_item.tickers:
            return False, "no_relevant_tickers"
        
        # 4. Keyword relevance filter
        if not news_item.keywords:
            return False, "no_relevant_keywords"
        
        # 5. Content quality filter
        if len(news_item.title) < 10 or len(news_item.content) < 20:
            return False, "insufficient_content"
        
        # 6. Source quality filter (optional)
        low_quality_sources = {'spam', 'clickbait', 'fake'}
        if any(source in news_item.source.lower() for source in low_quality_sources):
            return False, "low_quality_source"
        
        return True, "accepted"
    
    def get_filter_stats(self) -> Dict:
        """Get current filtering statistics"""
        return {
            "daily_headline_count": self.daily_headline_count,
            "max_daily_headlines": self.max_daily_headlines,
            "remaining_budget": self.max_daily_headlines - self.daily_headline_count,
            "tracked_tickers_count": len(self.tracked_tickers),
            "keywords_count": len(self.keywords),
            "processed_hashes_count": len(self.processed_hashes)
        }


def create_news_filter(config: Dict) -> NewsFilter:
    """Factory function to create NewsFilter instance"""
    return NewsFilter(config) 