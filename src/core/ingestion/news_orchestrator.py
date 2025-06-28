"""
News Ingestion Orchestrator - Main coordinator for news processing pipeline
Coordinates filtering, batching, and AI processing with strict cost controls
"""
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import os

from .news_filter import NewsFilter, NewsItem, create_news_filter
from .news_batcher import NewsBatcher, NewsBatch, create_news_batcher
from .news_sources.base import NewsSourceManager, RawNewsItem
from .news_sources.finnhub import create_finnhub_source
from .news_sources.newsapi import create_newsapi_source
from .news_sources.newdata import create_newdata_source

logger = logging.getLogger(__name__)


class NewsIngestionOrchestrator:
    """Main orchestrator for news ingestion and processing"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.news_config = config.get('news_ingestion', {})
        
        # Initialize components
        self.news_filter = create_news_filter(config)
        self.news_batcher = create_news_batcher(config)
        self.news_sources = self._initialize_news_sources()
        self.source_manager = NewsSourceManager(self.news_sources)
        
        # Cost tracking
        self.daily_ai_calls = 0
        self.monthly_ai_cost = 0.0
        self.ai_cost_per_call = 0.02  # Estimated cost per GPT call
        
        logger.info("🎯 NewsIngestionOrchestrator initialized with cost controls")
    
    def _initialize_news_sources(self) -> List:
        """Initialize all configured news sources"""
        sources = []
        
        # Initialize Finnhub (highest priority)
        try:
            if os.getenv("FINNHUB_KEY"):
                finnhub_source = create_finnhub_source()
                sources.append(finnhub_source)
                logger.info("✅ Finnhub source initialized")
            else:
                logger.warning("⚠️ FINNHUB_KEY not found, skipping Finnhub")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Finnhub: {e}")
        
        # Initialize NewsAPI (medium priority)
        try:
            if os.getenv("NEWS_API"):
                newsapi_source = create_newsapi_source()
                sources.append(newsapi_source)
                logger.info("✅ NewsAPI source initialized")
            else:
                logger.warning("⚠️ NEWS_API not found, skipping NewsAPI")
        except Exception as e:
            logger.error(f"❌ Failed to initialize NewsAPI: {e}")
        
        # Initialize NewData (lowest priority)
        try:
            if os.getenv("NEWS_DATA_KEY"):
                newdata_source = create_newdata_source()
                sources.append(newdata_source)
                logger.info("✅ NewData source initialized")
            else:
                logger.warning("⚠️ NEWS_DATA_KEY not found, skipping NewData")
        except Exception as e:
            logger.error(f"❌ Failed to initialize NewData: {e}")
        
        if not sources:
            logger.error("❌ No news sources could be initialized!")
        
        return sources
    
    def process_news_cycle(self, tickers: List[str] = None, hours_back: int = 24) -> Dict:
        """
        Complete news processing cycle with cost controls
        
        Returns:
            Dict with processing results and statistics
        """
        logger.info("🔄 Starting news processing cycle")
        
        # Step 1: Fetch news from all sources
        raw_news = self._fetch_news_from_sources(tickers, hours_back)
        
        # Step 2: Filter news based on criteria
        filtered_news, filter_stats = self._filter_news(raw_news)
        
        # Step 3: Batch news for efficient AI processing
        news_batches = self._batch_news(filtered_news)
        
        # Step 4: Process batches with AI (if within budget)
        ai_results = self._process_batches_with_ai(news_batches)
        
        # Compile results
        results = {
            "timestamp": datetime.now().isoformat(),
            "raw_news_count": len(raw_news),
            "filtered_news_count": len(filtered_news),
            "batches_created": len(news_batches),
            "ai_processed_batches": len(ai_results),
            "filter_stats": filter_stats,
            "batch_stats": self.news_batcher.get_batch_stats(),
            "source_stats": self.source_manager.get_all_stats(),
            "cost_stats": self._get_cost_stats()
        }
        
        logger.info(f"✅ News cycle complete: {results['ai_processed_batches']} batches processed with AI")
        return results
    
    def _fetch_news_from_sources(self, tickers: List[str] = None, hours_back: int = 24) -> List[RawNewsItem]:
        """Fetch news from all configured sources"""
        logger.info(f"📰 Fetching news for {len(tickers) if tickers else 'all'} tickers")
        
        try:
            raw_news = self.source_manager.fetch_all_news(
                tickers=tickers,
                hours_back=hours_back
            )
            logger.info(f"📰 Fetched {len(raw_news)} raw news items")
            return raw_news
        except Exception as e:
            logger.error(f"❌ Error fetching news: {e}")
            return []
    
    def _filter_news(self, raw_news: List[RawNewsItem]) -> Tuple[List[NewsItem], Dict]:
        """Filter raw news based on configured criteria"""
        # Convert RawNewsItem to dict format for filter
        raw_news_dicts = []
        for item in raw_news:
            raw_news_dicts.append({
                'title': item.title,
                'content': item.content,
                'source': item.source,
                'url': item.url,
                'published_at': item.published_at.isoformat()
            })
        
        # Apply filtering
        filtered_items, filter_stats = self.news_filter.filter_news(raw_news_dicts)
        
        logger.info(f"📊 Filtering complete: {len(filtered_items)}/{len(raw_news)} items accepted")
        return filtered_items, filter_stats
    
    def _batch_news(self, news_items: List[NewsItem]) -> List[NewsBatch]:
        """Batch news items for efficient AI processing"""
        if not news_items:
            return []
        
        batches = self.news_batcher.add_news_items(news_items)
        
        logger.info(f"📦 Created {len(batches)} news batches")
        return batches
    
    def _process_batches_with_ai(self, batches: List[NewsBatch]) -> List[Dict]:
        """Process news batches with AI analysis (with cost controls)"""
        if not batches:
            return []
        
        # Check AI budget
        max_daily_calls = self.news_config.get('max_daily_ai_calls', 50)
        max_monthly_budget = self.news_config.get('max_monthly_ai_budget', 20.0)
        
        if self.daily_ai_calls >= max_daily_calls:
            logger.warning(f"🚫 Daily AI call limit reached ({max_daily_calls})")
            return []
        
        if self.monthly_ai_cost >= max_monthly_budget:
            logger.warning(f"🚫 Monthly AI budget reached (${max_monthly_budget})")
            return []
        
        ai_results = []
        processed_count = 0
        
        for batch in batches:
            # Check if we can afford another AI call
            if self.daily_ai_calls >= max_daily_calls:
                logger.info(f"🚫 Stopping AI processing after {processed_count} batches (daily limit)")
                break
            
            if self.monthly_ai_cost >= max_monthly_budget:
                logger.info(f"🚫 Stopping AI processing after {processed_count} batches (budget limit)")
                break
            
            try:
                # Process batch with AI
                result = self._analyze_batch_with_ai(batch)
                if result:
                    ai_results.append(result)
                    processed_count += 1
                    
                    # Update cost tracking
                    self.daily_ai_calls += 1
                    self.monthly_ai_cost += self.ai_cost_per_call
                    
                    logger.info(f"🤖 Processed batch {batch.batch_id} with AI")
                
            except Exception as e:
                logger.error(f"❌ Error processing batch {batch.batch_id} with AI: {e}")
                continue
        
        logger.info(f"🤖 AI processing complete: {processed_count}/{len(batches)} batches processed")
        return ai_results
    
    def _analyze_batch_with_ai(self, batch: NewsBatch) -> Optional[Dict]:
        """Analyze a news batch with AI (placeholder for now)"""
        # This will be implemented to call the ETF signal engine
        # For now, return a placeholder result
        
        return {
            "batch_id": batch.batch_id,
            "processed_at": datetime.now().isoformat(),
            "items_count": batch.batch_size,
            "common_tickers": batch.common_tickers,
            "common_keywords": batch.common_keywords,
            "analysis_result": {
                "signal": "Neutral",
                "confidence": 5,
                "reasoning": "Batch analysis placeholder"
            }
        }
    
    def _get_cost_stats(self) -> Dict:
        """Get current cost statistics"""
        max_daily_calls = self.news_config.get('max_daily_ai_calls', 50)
        max_monthly_budget = self.news_config.get('max_monthly_ai_budget', 20.0)
        
        return {
            "daily_ai_calls": self.daily_ai_calls,
            "max_daily_ai_calls": max_daily_calls,
            "remaining_daily_calls": max_daily_calls - self.daily_ai_calls,
            "monthly_ai_cost": round(self.monthly_ai_cost, 2),
            "max_monthly_budget": max_monthly_budget,
            "remaining_budget": round(max_monthly_budget - self.monthly_ai_cost, 2),
            "estimated_cost_per_call": self.ai_cost_per_call
        }
    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        return {
            "news_filter": self.news_filter.get_filter_stats(),
            "news_batcher": self.news_batcher.get_batch_stats(),
            "news_sources": self.source_manager.get_all_stats(),
            "cost_tracking": self._get_cost_stats(),
            "configuration": {
                "max_daily_headlines": self.news_config.get('max_daily_headlines', 20),
                "tracked_tickers_count": len(self.news_config.get('tracked_tickers', [])),
                "keywords_count": len(self.news_config.get('keywords', []))
            }
        }


def create_news_orchestrator(config: Dict) -> NewsIngestionOrchestrator:
    """Factory function to create NewsIngestionOrchestrator"""
    return NewsIngestionOrchestrator(config) 