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
import pytz
from src.core.utils import get_setting

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
        self.timezone = self.market_hours.get('timezone', 'America/New_York')
        
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
        self.similarity_window_size = self.duplicate_config.get('similarity_window_size', 100)  # NEW: configurable window size
        
        # Advanced filtering (patched: always use dot-paths for config lookup)
        self.min_relevance_score = get_setting('news_ingestion.advanced_filtering.min_relevance_score', 0.0)
        self.min_sentiment_strength = get_setting('news_ingestion.advanced_filtering.min_sentiment_strength', 0.0)
        self.require_multiple_tickers = get_setting('news_ingestion.advanced_filtering.require_multiple_tickers', False)
        self.min_ticker_count = get_setting('news_ingestion.advanced_filtering.min_ticker_count', 1)
        
        # Content thresholds (externalized)
        self.min_title_length = self.news_config.get('min_title_length', 10)
        self.min_content_length = self.news_config.get('min_content_length', 20)
        
        # Sentiment keywords (externalized)
        sentiment_cfg = self.news_config.get('sentiment_keywords', {})
        self.positive_words = set(sentiment_cfg.get('positive_words', [
            'surge', 'rally', 'gain', 'up', 'positive', 'bullish', 'growth', 'profit', 'earnings', 'beat', 'strong', 'record'
        ]))
        self.negative_words = set(sentiment_cfg.get('negative_words', [
            'drop', 'fall', 'decline', 'down', 'negative', 'bearish', 'loss', 'miss', 'crash', 'plunge', 'downgrade', 'fear'
        ]))
        
        # Verbosity toggle for rejection logging
        self.verbose = self.news_config.get('verbose', True)
        
        # Daily counters
        self.daily_headline_count = 0
        self.daily_reset_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self.processed_hashes = set()
        
        # Store recent items for similarity checking (scalable window)
        from collections import deque
        self.recent_items = deque(maxlen=self.similarity_window_size)  # NEW: scalable window
        
        # Compile regex patterns for efficiency
        self._compile_patterns()
        
        # Disable market hours filter for testing if set in config
        self.disable_market_hours_filter = self.news_config.get('disable_market_hours_filter', False)
        
        # Time decay parameters (externalized)
        decay_cfg = self.news_config.get('time_decay', {})
        self.half_life_hours = decay_cfg.get('half_life_hours', 36)  # default to 36 hours
        self.max_age_hours = decay_cfg.get('max_age_hours', 240)     # default to 240 hours (10 days)
        
        logger.info(f"📰 NewsFilter initialized with {len(self.tracked_tickers)} tracked tickers, {len(self.keywords)} keywords")
        logger.info(f"🔍 Multi-source validation: {'enabled' if self.enable_source_validation else 'disabled'}")
        logger.info(f"[Filter Thresholds] min_relevance_score: {self.min_relevance_score}, min_sentiment_strength: {self.min_sentiment_strength}, require_multiple_tickers: {self.require_multiple_tickers}, min_ticker_count: {self.min_ticker_count}")
    
    def _compile_patterns(self):
        """Compile regex patterns for efficient matching (robustified)"""
        # DEBUG: Allow trivial pattern for testing
        debug_trivial_pattern = getattr(self, 'debug_trivial_pattern', False)
        if debug_trivial_pattern:
            self.ticker_pattern = re.compile(r'.+', re.IGNORECASE)
            self.keyword_pattern = re.compile(r'.+', re.IGNORECASE)
            logger.info("[DEBUG] Using trivial regex pattern '.+' for both tickers and keywords!")
            return
        # Expanded ETF/index synonyms and variations
        synonyms = [
            'Nasdaq', 'NASDAQ', 'Nasdaq-100', 'Nasdaq100', 'Nasdaq 100',
            'S&P 500', 'S&P500', 'SP500', 'SP-500', 'SP 500',
            'Dow', 'Dow Jones', 'DowJones', 'DJIA', 'DIA', 'DIA ETF',
            'Russell', 'Russell 2000', 'Russell2000',
            'NYSE', 'VIX', 'VIXY', 'VXX', 'SPY', 'SPY ETF', 'QQQ', 'QQQ ETF',
            'IWM', 'IWM ETF', 'SQQQ', 'SPXS', 'PBW', 'TAN', 'LIT', 'SMH', 'SOXX', 'QCLN', 'XAR', 'REMX', 'NLR', 'PPA', 'IRBO', 'ARKQ', 'DFEN', 'URA', 'URNM', 'ROBO', 'BOTZ'
        ]
        # Add plural and dash/space variations
        expanded_synonyms = set()
        for s in synonyms:
            expanded_synonyms.add(s)
            if not s.endswith('s'):
                expanded_synonyms.add(s + 's')
            expanded_synonyms.add(s.replace(' ', ''))
            expanded_synonyms.add(s.replace('-', ''))
            expanded_synonyms.add(s.replace(' ', '-'))
            expanded_synonyms.add(s.replace('-', ' '))
        all_tickers = set(self.tracked_tickers)
        for t in list(all_tickers):
            all_tickers.add(t.upper())
            all_tickers.add(t.lower())
            all_tickers.add(t.capitalize())
            if not t.endswith('s'):
                all_tickers.add(t + 's')
            all_tickers.add(t.replace(' ', ''))
            all_tickers.add(t.replace('-', ''))
            all_tickers.add(t.replace(' ', '-'))
            all_tickers.add(t.replace('-', ' '))
        all_tickers.update(expanded_synonyms)
        # Build a robust regex: word boundaries, allow optional spaces/dashes, ignore case
        pattern = r'\b(' + '|'.join(sorted(re.escape(t) for t in all_tickers if t)) + r')\b'
        self.ticker_pattern = re.compile(pattern, re.IGNORECASE)
        # Keyword pattern: allow for plural, dash, and space variations
        expanded_keywords = set()
        for k in self.keywords:
            expanded_keywords.add(k)
            if not k.endswith('s'):
                expanded_keywords.add(k + 's')
            expanded_keywords.add(k.replace(' ', ''))
            expanded_keywords.add(k.replace('-', ''))
            expanded_keywords.add(k.replace(' ', '-'))
            expanded_keywords.add(k.replace('-', ' '))
        keyword_pattern = r'\b(' + '|'.join(sorted(re.escape(k) for k in expanded_keywords if k)) + r')\b'
        self.keyword_pattern = re.compile(keyword_pattern, re.IGNORECASE)
        logger = logging.getLogger(__name__)
        logger.info(f"[Ticker Pattern] Using pattern: {self.ticker_pattern.pattern}")
        logger.info(f"[Ticker Pattern] Tickers/synonyms: {sorted(all_tickers)}")
        logger.info(f"[Keyword Pattern] Using pattern: {self.keyword_pattern.pattern}")
        logger.info(f"[Keyword Pattern] Keywords/synonyms: {sorted(expanded_keywords)}")
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for matching: lowercase, remove extra punctuation (except $ and %), collapse whitespace"""
        import re
        text = text.lower()
        text = re.sub(r'[^\w\s\$%\-]', ' ', text)  # keep alphanum, whitespace, $, %, -
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _extract_tickers(self, text: str) -> List[str]:
        """Extract ticker symbols from text (robustified)"""
        norm_text = self._normalize_text(text)
        # DEBUG: Log normalized text and pattern
        if hasattr(self, '_debug_counter'):
            self._debug_counter += 1
        else:
            self._debug_counter = 1
        if self._debug_counter <= 3:
            logger.info(f"[DEBUG] Normalized text for ticker extraction: '{norm_text}'")
            logger.info(f"[DEBUG] Ticker regex pattern: {self.ticker_pattern.pattern}")
        matches = self.ticker_pattern.findall(norm_text)
        logger.info(f"[Ticker Extract] Text: {text[:120]}... | Found tickers: {matches}")
        return list(set(matches))  # Remove duplicates
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text using robust partial matches"""
        norm_text = self._normalize_text(text)
        # DEBUG: Log normalized text and pattern
        if hasattr(self, '_debug_counter_kw'):
            self._debug_counter_kw += 1
        else:
            self._debug_counter_kw = 1
        if self._debug_counter_kw <= 3:
            logger.info(f"[DEBUG] Normalized text for keyword extraction: '{norm_text}'")
            logger.info(f"[DEBUG] Keyword regex pattern: {self.keyword_pattern.pattern}")
        matches = self.keyword_pattern.findall(norm_text)
        logger.info(f"[Keyword Extract] Text: {text[:120]}... | Found keywords: {matches}")
        return list(set(matches))
    
    def _reset_daily_counters(self):
        """Reset daily counters if it's a new day"""
        now = datetime.now()
        if now.date() > self.daily_reset_time.date():
            self.daily_headline_count = 0
            self.daily_reset_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
            self.processed_hashes.clear()
            logger.info("🔄 Daily news counters reset")
    
    def _is_market_hours(self, timestamp: datetime) -> bool:
        """Check if timestamp is during market hours (with timezone awareness and debug logging)"""
        if self.disable_market_hours_filter:
            logger.info(f"[Market Hours] Filtering is DISABLED for testing. All news allowed.")
            return True
        if not self.market_hours:
            return True  # No restrictions if not configured
        start_time = self.market_hours.get('start', '09:30')
        end_time = self.market_hours.get('end', '16:00')
        tz_name = self.market_hours.get('timezone', 'America/New_York')
        try:
            tz = pytz.timezone(tz_name)
            if timestamp.tzinfo is None:
                timestamp = tz.localize(timestamp)
            else:
                timestamp = timestamp.astimezone(tz)
            start_hour, start_minute = map(int, start_time.split(':'))
            end_hour, end_minute = map(int, end_time.split(':'))
            market_start = timestamp.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
            market_end = timestamp.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
            in_hours = market_start <= timestamp <= market_end
            logger.info(f"[Market Hours] Timestamp: {timestamp}, Market Start: {market_start}, Market End: {market_end}, In Hours: {in_hours}")
            return in_hours
        except Exception as e:
            logger.warning(f"⚠️ Error checking market hours: {e}")
            return True  # Default to allowing if error
    
    def _is_duplicate(self, news_item: NewsItem) -> bool:
        """Check if news item is a duplicate of previously processed content"""
        if not self.duplicate_enabled:
            return False
        # Check exact hash match
        if news_item.hash_id in self.processed_hashes:
            return True
        # Check similarity with recent items (scalable window)
        import pytz
        cutoff_time = datetime.now(pytz.UTC) - timedelta(hours=self.duplicate_window_hours)
        for recent in self.recent_items:
            # Only check items within the time window
            if hasattr(recent, 'published_at'):
                # Ensure recent.published_at is UTC-aware
                if recent.published_at.tzinfo is None:
                    recent_time = recent.published_at.replace(tzinfo=pytz.UTC)
                else:
                    recent_time = recent.published_at.astimezone(pytz.UTC)
                if recent_time < cutoff_time:
                    continue
            sim = self._calculate_similarity(news_item.title, recent.title)
            if sim >= self.similarity_threshold:
                return True
        # Add to recent_items for future checks
        self.recent_items.append(news_item)
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
        
        # Inject a test news item with a known keyword and ticker for debugging
        test_item = {
            'title': 'Test News: AI ETF Surges on Quantum Chip Breakthrough',
            'content': 'The AI ETF (QQQ) rallied after a major quantum chip breakthrough was announced.',
            'source': 'DebugSource',
            'url': 'http://debug.test/news',
            'published_at': datetime.now().isoformat()
        }
        if not hasattr(self, '_test_injected'):
            raw_news_items = [test_item] + raw_news_items
            self._test_injected = True
        
        filtered_items = []
        stats = {
            "total_received": len(raw_news_items),
            "filtered_out": 0,
            "reasons": {},
            "sample_rejected_items": []  # NEW: Track sample rejected items for debugging
        }
        
        for raw_item in raw_news_items:
            try:
                news_item = self._create_news_item(raw_item)
                should_process, reason = self._apply_filters(news_item)
                # Log every item with detailed info
                logger.info(
                    f"[NEWS MICRO] Title: {news_item.title} | Source: {news_item.source} | Tickers: {news_item.tickers} | Keywords: {news_item.keywords} | Relevance: {news_item.relevance_score:.2f} | Sentiment: {news_item.sentiment_score:.2f} | Reason: {reason} | Content: {news_item.content[:200]}..."
                )
                if should_process:
                    filtered_items.append(news_item)
                    self.processed_hashes.add(news_item.hash_id)
                    self.daily_headline_count += 1
                    
                    logger.info(f"[ACCEPTED] Title: {news_item.title} | Source: {news_item.source} | Tickers: {news_item.tickers} | Keywords: {news_item.keywords} | Relevance: {news_item.relevance_score:.2f} | Sentiment: {news_item.sentiment_score:.2f}")
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
        # Ensure published_at is timezone-aware (UTC)
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=pytz.UTC)
        else:
            published_at = published_at.astimezone(pytz.UTC)
        
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
        logger = logging.getLogger(__name__)
        import pytz
        # Ensure published_at is UTC-aware before converting to local timezone
        if news_item.published_at.tzinfo is None:
            news_item.published_at = news_item.published_at.replace(tzinfo=pytz.UTC)
        else:
            news_item.published_at = news_item.published_at.astimezone(pytz.UTC)
        tz = pytz.timezone(self.timezone)
        news_item.published_at = news_item.published_at.astimezone(tz)
        # 1. Market hours filter
        if not self._is_market_hours(news_item.published_at):
            if self.verbose:
                logger.debug(f"[Filter] OUT: outside_market_hours | Title: {news_item.title} | Published: {news_item.published_at}")
            return False, "outside_market_hours"
        # 2. Duplicate filter
        if self._is_duplicate(news_item):
            if self.verbose:
                logger.debug(f"[Filter] OUT: duplicate_content | Title: {news_item.title}")
            return False, "duplicate_content"
        # 3. Relevance score filter
        if news_item.relevance_score < self.min_relevance_score:
            if self.verbose:
                logger.debug(f"[Filter] OUT: low_relevance_score_{news_item.relevance_score:.2f} | Title: {news_item.title}")
            return False, f"low_relevance_score_{news_item.relevance_score:.2f}"
        # 4. Sentiment strength filter (only if sentiment is present)
        if abs(news_item.sentiment_score) > 0:
            if abs(news_item.sentiment_score) < self.min_sentiment_strength:
                if self.verbose:
                    logger.debug(f"[Filter] OUT: weak_sentiment_{abs(news_item.sentiment_score):.2f} | Title: {news_item.title}")
                return False, f"weak_sentiment_{abs(news_item.sentiment_score):.2f}"
        # 5. Ticker count filter
        logger.info(f"[Ticker Filter] Bypassed for testing. Tickers found: {news_item.tickers}")
        # 6. Keyword relevance filter (relaxed - allow items with good ticker coverage)
        if not news_item.keywords and len(news_item.tickers) < 2:
            if self.verbose:
                logger.debug(f"[Filter] OUT: no_relevant_keywords | Title: {news_item.title}")
            return False, "no_relevant_keywords"
        # 7. Content quality filter (configurable thresholds)
        if len(news_item.title) < self.min_title_length or len(news_item.content) < self.min_content_length:
            if self.verbose:
                logger.debug(f"[Filter] OUT: insufficient_content | Title: {news_item.title}")
            return False, "insufficient_content"
        # 8. Source quality filter (optional)
        low_quality_sources = {'spam', 'clickbait', 'fake'}
        if any(source in news_item.source.lower() for source in low_quality_sources):
            if self.verbose:
                logger.debug(f"[Filter] OUT: low_quality_source | Title: {news_item.title}")
            return False, "low_quality_source"
        # 9. Source validation (if enabled)
        if self.enable_source_validation:
            if news_item.source_priority < 2:  # Restored from 1
                if self.verbose:
                    logger.debug(f"[Filter] OUT: low_priority_source_{news_item.source_priority} | Title: {news_item.title}")
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
        # Use externalized keywords if present
        positive_words = self.positive_words
        negative_words = self.negative_words
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        if positive_count == 0 and negative_count == 0:
            return 0.0
        total = positive_count + negative_count
        sentiment = (positive_count - negative_count) / total
        return sentiment


def create_news_filter(config: Dict) -> NewsFilter:
    """Factory function to create NewsFilter instance"""
    return NewsFilter(config) 