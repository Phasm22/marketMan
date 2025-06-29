"""
News Batching Module - Groups related headlines for efficient AI processing
Reduces API costs by batching multiple headlines into single AI calls
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import time

from .news_filter import NewsItem

logger = logging.getLogger(__name__)


@dataclass
class NewsBatch:
    """A batch of related news items for AI processing with multi-source validation"""
    items: List[NewsItem]
    batch_id: str
    created_at: datetime
    common_tickers: List[str]
    common_keywords: List[str]
    batch_size: int
    # Multi-source validation metadata
    source_agreement_score: float = 0.0  # How much sources agree (0-1)
    contradiction_flag: bool = False  # True if sources contradict each other
    avg_source_weight: float = 0.0  # Average source reliability weight
    avg_relevance_score: float = 0.0  # Average relevance score
    avg_sentiment_score: float = 0.0  # Average sentiment score
    batch_quality_score: float = 0.0  # Overall batch quality (0-1)
    source_diversity: int = 0  # Number of unique sources
    sentiment_consistency: float = 0.0  # How consistent sentiment is across sources
    
    def __post_init__(self):
        self.batch_size = len(self.items)
        # Calculate multi-source validation metrics
        self._calculate_validation_metrics()
    
    def _calculate_validation_metrics(self):
        """Calculate multi-source validation metrics for the batch"""
        if not self.items:
            return
        
        # Source diversity
        unique_sources = set(item.source for item in self.items)
        self.source_diversity = len(unique_sources)
        
        # Average scores
        self.avg_source_weight = sum(item.get_source_weight() for item in self.items) / len(self.items)
        self.avg_relevance_score = sum(item.relevance_score for item in self.items) / len(self.items)
        self.avg_sentiment_score = sum(item.sentiment_score for item in self.items) / len(self.items)
        
        # Sentiment consistency
        sentiment_values = [item.sentiment_score for item in self.items if abs(item.sentiment_score) > 0.1]
        if len(sentiment_values) > 1:
            # Calculate standard deviation of sentiment (lower = more consistent)
            mean_sentiment = sum(sentiment_values) / len(sentiment_values)
            variance = sum((s - mean_sentiment) ** 2 for s in sentiment_values) / len(sentiment_values)
            std_dev = variance ** 0.5
            # Convert to consistency score (0-1, higher = more consistent)
            self.sentiment_consistency = max(0, 1 - std_dev)
        else:
            self.sentiment_consistency = 1.0  # Single sentiment or no sentiment
        
        # Source agreement (simplified - in production, use more sophisticated analysis)
        # For now, we'll use sentiment consistency as a proxy for source agreement
        self.source_agreement_score = self.sentiment_consistency
        
        # Contradiction detection
        positive_sentiments = [s for s in sentiment_values if s > 0.2]
        negative_sentiments = [s for s in sentiment_values if s < -0.2]
        self.contradiction_flag = len(positive_sentiments) > 0 and len(negative_sentiments) > 0
        
        # Overall batch quality score
        quality_factors = [
            self.avg_source_weight / 5.0,  # Normalize source weight
            self.avg_relevance_score,
            self.sentiment_consistency,
            min(self.source_diversity / 3.0, 1.0),  # Prefer diverse sources but cap at 3
            1.0 if not self.contradiction_flag else 0.5  # Penalize contradictions
        ]
        self.batch_quality_score = sum(quality_factors) / len(quality_factors)
    
    def get_combined_text(self) -> str:
        """Get combined text for AI analysis with source metadata"""
        combined = []
        for item in self.items:
            combined.append(f"Source: {item.source} (Priority: {item.source_priority}, Category: {item.source_category})")
            combined.append(f"Title: {item.title}")
            combined.append(f"Content: {item.content}")
            combined.append(f"Tickers: {', '.join(item.tickers)}")
            combined.append(f"Keywords: {', '.join(item.keywords)}")
            combined.append(f"Sentiment: {item.sentiment_score:.2f}, Relevance: {item.relevance_score:.2f}")
            combined.append("---")
        return "\n".join(combined)
    
    def get_summary(self) -> str:
        """Get a summary of the batch for logging with validation metrics"""
        tickers_str = ", ".join(self.common_tickers[:3])
        if len(self.common_tickers) > 3:
            tickers_str += f" (+{len(self.common_tickers) - 3} more)"
        
        validation_info = f"Quality: {self.batch_quality_score:.2f}, Sources: {self.source_diversity}"
        if self.contradiction_flag:
            validation_info += ", ⚠️ Contradictions"
        
        return f"Batch {self.batch_id}: {self.batch_size} items, Tickers: {tickers_str} ({validation_info})"


class NewsBatcher:
    """Groups related news items into batches for efficient AI processing"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.news_config = config.get('news_ingestion', {})
        self.batch_config = self.news_config.get('batching', {})
        
        # Batching parameters
        self.max_headlines_per_batch = self.batch_config.get('max_headlines_per_batch', 5)
        self.min_batch_size = self.batch_config.get('min_batch_size', 2)
        self.max_batch_wait_time = self.batch_config.get('max_batch_wait_time', 300)  # 5 minutes
        
        # Batch storage
        self.pending_batches: Dict[str, NewsBatch] = {}
        self.batch_timers: Dict[str, datetime] = {}
        
        logger.info(f"📦 NewsBatcher initialized: max_batch_size={self.max_headlines_per_batch}, min_batch_size={self.min_batch_size}")
    
    def add_news_items(self, news_items: List[NewsItem]) -> List[NewsBatch]:
        """
        Add news items to batching system and return ready batches
        
        Returns:
            List of NewsBatch objects ready for AI processing
        """
        if not news_items:
            return []
        
        # Group items by common characteristics
        grouped_items = self._group_news_items(news_items)
        
        # Create or update batches
        ready_batches = []
        
        for group_key, items in grouped_items.items():
            batch = self._get_or_create_batch(group_key, items)
            
            if batch and self._is_batch_ready(batch):
                ready_batches.append(batch)
                # Remove from pending
                if batch.batch_id in self.pending_batches:
                    del self.pending_batches[batch.batch_id]
                if batch.batch_id in self.batch_timers:
                    del self.batch_timers[batch.batch_id]
        
        # Check for expired batches
        expired_batches = self._get_expired_batches()
        ready_batches.extend(expired_batches)
        
        logger.info(f"📦 Created {len(ready_batches)} ready batches from {len(news_items)} news items")
        return ready_batches
    
    def _group_news_items(self, news_items: List[NewsItem]) -> Dict[str, List[NewsItem]]:
        """Group news items by common tickers and keywords"""
        groups = defaultdict(list)
        
        for item in news_items:
            # Create group key based on common tickers
            if item.tickers:
                # Use the most common ticker as primary grouping
                primary_ticker = item.tickers[0]
                group_key = f"ticker_{primary_ticker}"
                groups[group_key].append(item)
            else:
                # Group by keywords if no tickers
                if item.keywords:
                    primary_keyword = item.keywords[0]
                    group_key = f"keyword_{primary_keyword}"
                    groups[group_key].append(item)
                else:
                    # Default group for items without clear categorization
                    group_key = "general"
                    groups[group_key].append(item)
        
        return dict(groups)
    
    def _get_or_create_batch(self, group_key: str, items: List[NewsItem]) -> Optional[NewsBatch]:
        """Get existing batch or create new one for the group"""
        batch_id = f"{group_key}_{int(time.time())}"
        
        logger.debug(f"🔍 Creating batch for group '{group_key}' with {len(items)} items (min_size={self.min_batch_size})")
        
        # Check if we already have a pending batch for this group
        existing_batch = self.pending_batches.get(group_key)
        
        if existing_batch:
            logger.debug(f"📦 Adding {len(items)} items to existing batch '{group_key}'")
            # Add items to existing batch
            existing_batch.items.extend(items)
            
            # Update common characteristics
            all_tickers = set()
            all_keywords = set()
            for item in existing_batch.items:
                all_tickers.update(item.tickers)
                all_keywords.update(item.keywords)
            
            existing_batch.common_tickers = list(all_tickers)
            existing_batch.common_keywords = list(all_keywords)
            
            return existing_batch
        else:
            # Create new batch
            if len(items) >= self.min_batch_size:
                logger.debug(f"✅ Creating immediate batch for {len(items)} items (>= {self.min_batch_size})")
                # Create batch immediately if we have enough items
                batch = self._create_batch(group_key, items)
                return batch
            else:
                logger.debug(f"⏳ Storing pending batch for {len(items)} items (< {self.min_batch_size})")
                # Store as pending batch
                batch = self._create_batch(group_key, items)
                self.pending_batches[group_key] = batch
                self.batch_timers[group_key] = datetime.now()
                return None
    
    def _create_batch(self, group_key: str, items: List[NewsItem]) -> NewsBatch:
        """Create a new NewsBatch from items with multi-source validation"""
        # Find common characteristics
        all_tickers = set()
        all_keywords = set()
        
        for item in items:
            all_tickers.update(item.tickers)
            all_keywords.update(item.keywords)
        
        batch_id = f"{group_key}_{int(time.time())}"
        
        return NewsBatch(
            items=items,
            batch_id=batch_id,
            created_at=datetime.now(),
            common_tickers=list(all_tickers),
            common_keywords=list(all_keywords),
            batch_size=len(items)
            # Multi-source validation metrics will be calculated in __post_init__
        )
    
    def _is_batch_ready(self, batch: NewsBatch) -> bool:
        """Check if a batch is ready for processing"""
        logger.debug(f"🔍 Checking if batch '{batch.batch_id}' is ready: size={batch.batch_size}, max_size={self.max_headlines_per_batch}, min_size={self.min_batch_size}")
        
        # Check if batch is full
        if batch.batch_size >= self.max_headlines_per_batch:
            logger.debug(f"✅ Batch '{batch.batch_id}' ready: full size ({batch.batch_size} >= {self.max_headlines_per_batch})")
            return True
        
        # Check if batch has minimum size and has been waiting long enough
        if batch.batch_size >= self.min_batch_size:
            batch_age = datetime.now() - batch.created_at
            age_seconds = batch_age.total_seconds()
            logger.debug(f"⏰ Batch '{batch.batch_id}' age: {age_seconds:.1f}s (need {self.max_batch_wait_time}s)")
            if age_seconds >= self.max_batch_wait_time:
                logger.debug(f"✅ Batch '{batch.batch_id}' ready: waited long enough ({age_seconds:.1f}s >= {self.max_batch_wait_time}s)")
                return True
            else:
                logger.debug(f"⏳ Batch '{batch.batch_id}' not ready: waiting ({age_seconds:.1f}s < {self.max_batch_wait_time}s)")
        else:
            logger.debug(f"❌ Batch '{batch.batch_id}' not ready: too small ({batch.batch_size} < {self.min_batch_size})")
        
        return False
    
    def _get_expired_batches(self) -> List[NewsBatch]:
        """Get batches that have expired and should be processed"""
        expired_batches = []
        current_time = datetime.now()
        
        for group_key, timer in list(self.batch_timers.items()):
            if (current_time - timer).total_seconds() >= self.max_batch_wait_time:
                batch = self.pending_batches.get(group_key)
                if batch and batch.batch_size >= self.min_batch_size:
                    expired_batches.append(batch)
                    # Remove from pending
                    del self.pending_batches[group_key]
                    del self.batch_timers[group_key]
        
        return expired_batches
    
    def get_pending_batches(self) -> List[NewsBatch]:
        """Get all pending batches"""
        return list(self.pending_batches.values())
    
    def get_batch_stats(self) -> Dict:
        """Get batching statistics"""
        pending_count = len(self.pending_batches)
        total_pending_items = sum(len(batch.items) for batch in self.pending_batches.values())
        
        return {
            "pending_batches": pending_count,
            "total_pending_items": total_pending_items,
            "max_batch_size": self.max_headlines_per_batch,
            "min_batch_size": self.min_batch_size,
            "max_wait_time_seconds": self.max_batch_wait_time
        }


def create_news_batcher(config: Dict) -> NewsBatcher:
    """Factory function to create NewsBatcher instance"""
    return NewsBatcher(config) 