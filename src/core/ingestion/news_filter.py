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
    """Standardized news item structure with enhanced source tracking"""
    title: str
    content: str
    source: str
    url: str
    published_at: datetime
    tickers: List[str]
    keywords: List[str]
    hash_id: str
    source_priority: int = 1  # Higher number = higher priority/reliability
    source_category: str = "general"  # financial, tech, general, etc.
    sentiment_score: float = 0.0  # Pre-calculated sentiment (-1 to 1)
    relevance_score: float = 0.0  # Relevance to tracked tickers/keywords (0 to 1)
    
    def __post_init__(self):
        if not self.hash_id:
            # Create hash from title + content for duplicate detection
            content_str = f"{self.title}{self.content}"
            self.hash_id = hashlib.md5(content_str.encode()).hexdigest()
    
    def get_source_weight(self) -> float:
        """Get source weight based on priority and category"""
        base_weight = self.source_priority
        
        # Adjust weight based on source category
        category_weights = {
            "financial": 1.2,
            "tech": 1.1,
            "general": 1.0,
            "blog": 0.8,
            "social": 0.6
        }
        
        category_multiplier = category_weights.get(self.source_category, 1.0)
        return base_weight * category_multiplier


class NewsFilter:
    """Intelligent news filtering to reduce AI API costs with multi-source validation"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.news_config = config.get('news_ingestion', {})
        
        # Extract configuration
        self.max_daily_headlines = self.news_config.get('max_daily_headlines', 20)
        self.tracked_tickers = set(self.news_config.get('tracked_tickers', []))
        self.keywords = set(self.news_config.get('keywords', []))
        self.market_hours = self.news_config.get('market_hours', {})
        
        # Multi-source validation config
        self.validation_config = self.news_config.get('multi_source_validation', {})
        self.enable_source_validation = self.validation_config.get('enabled', True)
        self.source_weights = self.validation_config.get('source_weights', {
            "Reuters": 5,
            "Bloomberg": 5,
            "Financial Times": 5,
            "CNBC": 4,
            "MarketWatch": 4,
            "Yahoo Finance": 3,
            "Seeking Alpha": 3,
            "TechCrunch": 3,
            "Ars Technica": 2,
            "unknown": 1
        })
        self.source_categories = self.validation_config.get('source_categories', {
            "Reuters": "financial",
            "Bloomberg": "financial", 
            "Financial Times": "financial",
            "CNBC": "financial",
            "MarketWatch": "financial",
            "Yahoo Finance": "financial",
            "Seeking Alpha": "financial",
            "TechCrunch": "tech",
            "Ars Technica": "tech",
            "unknown": "general"
        })
        
        # Duplicate detection
        self.duplicate_config = self.news_config.get('duplicate_detection', {})
        self.duplicate_enabled = self.duplicate_config.get('enabled', True)
        self.duplicate_window_hours = self.duplicate_config.get('time_window_hours', 24)
        self.similarity_threshold = self.duplicate_config.get('similarity_threshold', 0.8)
        
        # Advanced filtering
        self.advanced_config = self.news_config.get('advanced_filtering', {})
        self.min_relevance_score = self.advanced_config.get('min_relevance_score', 0.3)
        self.min_sentiment_strength = self.advanced_config.get('min_sentiment_strength', 0.2)
        self.require_multiple_tickers = self.advanced_config.get('require_multiple_tickers', False)
        self.min_ticker_count = self.advanced_config.get('min_ticker_count', 1)
        
        # Daily counters
        self.daily_headline_count = 0
        self.daily_reset_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self.processed_hashes = set()
        
        # Store recent items for similarity checking
        self.recent_items = []  # Store last N items for similarity detection
        
        # Compile regex patterns for efficiency
        self._compile_patterns()
        
        logger.info(f"📰 NewsFilter initialized with {len(self.tracked_tickers)} tracked tickers, {len(self.keywords)} keywords")
        logger.info(f"🔍 Multi-source validation: {'enabled' if self.enable_source_validation else 'disabled'}")
    
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
            "reasons": {},
            "sample_rejected_items": []  # NEW: Track sample rejected items for debugging
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
                    
                    logger.debug(f"✅ Accepted: {news_item.title[:60]}... (Tickers: {news_item.tickers}, Score: {news_item.relevance_score:.2f})")
                else:
                    stats["filtered_out"] += 1
                    stats["reasons"][reason] = stats["reasons"].get(reason, 0) + 1
                    
                    # NEW: Track sample rejected items for debugging
                    if len(stats["sample_rejected_items"]) < 5:
                        stats["sample_rejected_items"].append({
                            "title": news_item.title[:80],
                            "source": news_item.source,
                            "tickers": news_item.tickers,
                            "keywords": news_item.keywords,
                            "relevance_score": news_item.relevance_score,
                            "sentiment_score": news_item.sentiment_score,
                            "reason": reason
                        })
                    
                    logger.debug(f"❌ Filtered: {news_item.title[:60]}... (Reason: {reason}, Score: {news_item.relevance_score:.2f}, Tickers: {news_item.tickers})")
                
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
        
        # NEW: Log detailed filtering statistics
        logger.info(f"📊 News filtering complete: {stats['processed']}/{stats['total_received']} items accepted")
        if stats["reasons"]:
            logger.info(f"🚫 Filter reasons:")
            for reason, count in stats["reasons"].items():
                percentage = (count / stats["total_received"]) * 100
                logger.info(f"  • {reason}: {count} items ({percentage:.1f}%)")
        
        # NEW: Log sample rejected items for debugging
        if stats["sample_rejected_items"]:
            logger.info(f"🔍 Sample rejected items:")
            for i, item in enumerate(stats["sample_rejected_items"], 1):
                logger.info(f"  {i}. '{item['title']}' (Source: {item['source']}, Score: {item['relevance_score']:.2f}, Reason: {item['reason']})")
        
        return filtered_items, stats
    
    def _create_news_item(self, raw_item: Dict) -> NewsItem:
        """Convert raw news item to standardized NewsItem with enhanced metadata"""
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
        
        # Get source metadata
        source_name = raw_item.get('source', 'unknown')
        source_priority, source_category = self._get_source_metadata(source_name)
        
        # Calculate scores
        relevance_score = self._calculate_relevance_score(tickers, keywords)
        sentiment_score = self._calculate_sentiment_score(full_text)
        
        return NewsItem(
            title=title,
            content=content,
            source=source_name,
            url=raw_item.get('url', ''),
            published_at=published_at,
            tickers=tickers,
            keywords=keywords,
            hash_id='',  # Will be set in __post_init__
            source_priority=source_priority,
            source_category=source_category,
            sentiment_score=sentiment_score,
            relevance_score=relevance_score
        )
    
    def _apply_filters(self, news_item: NewsItem) -> Tuple[bool, str]:
        """Apply all filters to a news item with enhanced validation"""
        
        # 1. Market hours filter
        if not self._is_market_hours(news_item.published_at):
            return False, "outside_market_hours"
        
        # 2. Duplicate filter
        if self._is_duplicate(news_item):
            return False, "duplicate_content"
        
        # 3. Relevance score filter
        if news_item.relevance_score < self.min_relevance_score:
            return False, f"low_relevance_score_{news_item.relevance_score:.2f}"
        
        # 4. Sentiment strength filter (only if sentiment is present)
        if abs(news_item.sentiment_score) > 0:
            if abs(news_item.sentiment_score) < self.min_sentiment_strength:
                return False, f"weak_sentiment_{abs(news_item.sentiment_score):.2f}"
        
        # 5. Ticker count filter
        if self.require_multiple_tickers and len(news_item.tickers) < self.min_ticker_count:
            return False, f"insufficient_tickers_{len(news_item.tickers)}"
        elif len(news_item.tickers) < self.min_ticker_count:
            return False, f"no_relevant_tickers"
        
        # 6. Keyword relevance filter (relaxed - allow items with good ticker coverage)
        if not news_item.keywords and len(news_item.tickers) < 2:
            return False, "no_relevant_keywords"
        
        # 7. Content quality filter
        if len(news_item.title) < 10 or len(news_item.content) < 20:
            return False, "insufficient_content"
        
        # 8. Source quality filter (optional)
        low_quality_sources = {'spam', 'clickbait', 'fake'}
        if any(source in news_item.source.lower() for source in low_quality_sources):
            return False, "low_quality_source"
        
        # 9. Source validation (if enabled)
        if self.enable_source_validation:
            if news_item.source_priority < 2:  # Restored from 1
                return False, f"low_priority_source_{news_item.source_priority}"
        
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

    def _get_source_metadata(self, source_name: str) -> Tuple[int, str]:
        """Get source priority and category"""
        priority = self.source_weights.get(source_name, self.source_weights.get("unknown", 1))
        category = self.source_categories.get(source_name, self.source_categories.get("unknown", "general"))
        return priority, category
    
    def _calculate_relevance_score(self, tickers: List[str], keywords: List[str]) -> float:
        """Calculate relevance score based on tickers and keywords"""
        if not tickers and not keywords:
            return 0.0
        
        # Weight tickers more heavily than keywords
        ticker_score = len(tickers) * 0.6
        keyword_score = len(keywords) * 0.4
        
        total_score = ticker_score + keyword_score
        
        # Normalize to 0-1 range (max score would be ~10 for very relevant items)
        return min(total_score / 10.0, 1.0)
    
    def _calculate_sentiment_score(self, text: str) -> float:
        """Calculate basic sentiment score using simple heuristics"""
        # Simple sentiment calculation - in production, use VADER or similar
        positive_words = {'surge', 'rally', 'gain', 'up', 'positive', 'bullish', 'growth', 'profit', 'earnings', 'beat'}
        negative_words = {'drop', 'fall', 'decline', 'down', 'negative', 'bearish', 'loss', 'miss', 'crash', 'plunge'}
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count == 0 and negative_count == 0:
            return 0.0
        
        # Normalize to -1 to 1 range
        total = positive_count + negative_count
        sentiment = (positive_count - negative_count) / total
        
        return sentiment


def create_news_filter(config: Dict) -> NewsFilter:
    """Factory function to create NewsFilter instance"""
    return NewsFilter(config) 