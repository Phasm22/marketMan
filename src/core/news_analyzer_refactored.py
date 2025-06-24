"""
MarketMan News Analyzer - Refactored main orchestrator
Analyzes Google Alerts for thematic ETF opportunities and creates consolidated reports
"""
import os
import sys
import logging
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.integrations.pushover_utils import send_energy_alert, send_system_alert
from src.core.market_memory import MarketMemory
from src.core.alert_batcher import queue_alert, process_alert_queue, BatchStrategy

# Import refactored modules
from src.core.etf_analyzer import analyze_thematic_etf_news, generate_tactical_explanation, categorize_etfs_by_sector
from src.core.market_data import get_market_snapshot
from src.core.gmail_poller import GmailPoller
from src.core.notion_reporter import NotionReporter
from src.core.report_consolidator import create_consolidated_signal_report

# Set up logging with debug control
DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"
log_level = logging.DEBUG if DEBUG_MODE else logging.INFO
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)

# Alert batching configuration
ALERT_STRATEGY = os.getenv("ALERT_STRATEGY", "smart_batch").lower()
BATCH_STRATEGY_MAP = {
    "immediate": BatchStrategy.IMMEDIATE,
    "time_window": BatchStrategy.TIME_WINDOW,
    "daily_digest": BatchStrategy.DAILY_DIGEST,
    "smart_batch": BatchStrategy.SMART_BATCH
}
CURRENT_BATCH_STRATEGY = BATCH_STRATEGY_MAP.get(ALERT_STRATEGY, BatchStrategy.SMART_BATCH)

# Initialize MarketMemory for contextual tracking
memory = MarketMemory()

class NewsAnalyzer:
    def __init__(self):
        self.gmail_poller = GmailPoller()
        self.notion_reporter = NotionReporter()
    
    def process_alerts(self):
        """Main function to process Google Alerts - creates consolidated reports"""
        logger.info("Starting to process Google Alerts...")

        # Fetch alerts from Gmail
        alerts = self.gmail_poller.get_google_alerts()

        if not alerts:
            logger.info("No new alerts found")
            return

        # Collect all analyses for consolidated reporting
        session_analyses = []
        session_timestamp = datetime.now().isoformat()
        all_mentioned_etfs = set()
        
        # Get market snapshot once for all analyses
        market_snapshot = get_market_snapshot()
        
        for alert in alerts:
            logger.info(f"Processing alert for: {alert['search_term']}")

            for article in alert['articles']:
                try:
                    # Get contextual insights from memory
                    contextual_insight = memory.get_contextual_insight({"signal": "Neutral", "affected_etfs": []}, [])
                    
                    # Analyze the article
                    analysis = analyze_thematic_etf_news(
                        headline=article['title'],
                        summary=article['snippet'],
                        snippet=article['snippet'],
                        etf_prices=market_snapshot,
                        contextual_insight=contextual_insight,
                        memory=memory
                    )

                    if not analysis:
                        continue

                    # Add market snapshot to analysis
                    analysis['market_snapshot'] = market_snapshot

                    # Add metadata for consolidated reporting
                    analysis['source_article'] = {
                        'title': article['title'],
                        'link': article['link'],
                        'search_term': alert['search_term'],
                        'timestamp': alert['timestamp']
                    }

                    # Focus ETFs using sector intelligence
                    focused_etfs, primary_sector = categorize_etfs_by_sector(analysis.get('affected_etfs', []))
                    analysis['focused_etfs'] = focused_etfs
                    analysis['primary_sector'] = primary_sector
                    
                    # Track for pattern analysis
                    all_mentioned_etfs.update(focused_etfs)
                    
                    # Add to session collection
                    session_analyses.append(analysis)
                    
                    signal = analysis.get('signal', 'Neutral')
                    confidence = analysis.get('confidence', 0)
                    
                    logger.info(f"📊 {signal} signal ({confidence}/10) - {primary_sector or 'Mixed'} - {article['title'][:60]}...")

                except Exception as e:
                    logger.error(f"Error processing article '{article['title']}': {e}")
                    continue
        
        # Create consolidated signal report if we have analyses
        if session_analyses:
            logger.info(f"📊 Creating consolidated report from {len(session_analyses)} analyses...")
            
            consolidated_report = create_consolidated_signal_report(session_analyses, session_timestamp)
            
            if consolidated_report:
                # Log consolidated report to Notion
                notion_url = self.notion_reporter.log_consolidated_report_to_notion(consolidated_report)
                
                # Queue high-conviction signals for alerts
                high_conviction_signals = [a for a in session_analyses if a.get('confidence', 0) >= 8]
                
                if high_conviction_signals:
                    logger.info(f"📋 Queueing {len(high_conviction_signals)} high-conviction signals...")
                    
                    for analysis in high_conviction_signals:
                        alert_id = queue_alert(
                            signal=analysis.get('signal', 'Neutral'),
                            confidence=analysis.get('confidence', 0),
                            title=f"High Conviction: {analysis.get('primary_sector', 'Mixed')} Signal",
                            reasoning=analysis.get('reasoning', ''),
                            etfs=analysis.get('focused_etfs', []),
                            sector=analysis.get('primary_sector', 'Mixed'),
                            article_url=notion_url,
                            search_term="consolidated_report",
                            strategy=CURRENT_BATCH_STRATEGY
                        )
                        logger.info(f"✅ Alert queued: {alert_id[:8]}")
                else:
                    logger.info("⏭️ No high-conviction signals to queue")
        
        # After processing all alerts, check for significant new patterns
        if all_mentioned_etfs:
            self._analyze_memory_patterns(all_mentioned_etfs)
        
        # Process any pending alert batches at the end of the cycle
        self._process_alert_batches()

    def _analyze_memory_patterns(self, all_mentioned_etfs):
        """Analyze patterns for mentioned ETFs"""
        logger.info("🧠 Analyzing patterns for mentioned ETFs...")
        significant_patterns = []
        
        for etf in all_mentioned_etfs:
            patterns = memory.detect_patterns(etf_symbol=etf)
            # Only include patterns with high confidence or long streaks
            for pattern in patterns:
                if (pattern.get('consecutive_days', 0) >= 3 or 
                    pattern.get('average_confidence', 0) >= 7):
                    significant_patterns.append(pattern)
        
        if significant_patterns:
            logger.info(f"📊 Found {len(significant_patterns)} significant patterns")
            # TODO: Log significant patterns to Notion (requires separate patterns database)
    
    def _process_alert_batches(self):
        """Process any pending alert batches"""
        logger.info("📱 Processing alert queue...")
        batch_results = process_alert_queue()
        
        if batch_results:
            for strategy, success in batch_results.items():
                status = "✅" if success else "❌"
                logger.info(f"{status} Batch sent via {strategy} strategy")
        else:
            logger.info("📭 No batches ready to send")

def test_tactical_explanation():
    """Test the tactical explanation generation"""
    test_analysis = {
        'signal': 'Bullish',
        'confidence': 8,
        'affected_etfs': ['QQQ', 'TQQQ', 'VTI'],
        'reasoning': 'Strong earnings beats from tech giants driving sector momentum',
        'sector': 'Technology'
    }
    
    test_title = "Tech Giants Report Blowout Earnings, AI Revenue Surges"
    
    print("\\n🧪 Testing tactical explanation generation...")
    explanation = generate_tactical_explanation(test_analysis, test_title)
    
    if explanation:
        print(f"✅ Generated tactical explanation ({len(explanation)} characters):")
        print("=" * 60)
        print(explanation)
        print("=" * 60)
    else:
        print("❌ Failed to generate tactical explanation")
    
    return explanation is not None

def test_consolidated_reporting():
    """Test the consolidated reporting with multiple mock analyses"""
    print("\\n🧪 Testing consolidated signal reporting...")
    
    # Mock multiple analyses
    mock_analyses = [
        {
            'signal': 'Bullish',
            'confidence': 9,
            'affected_etfs': ['BOTZ', 'ROBO', 'ARKQ'],
            'reasoning': 'Strong AI sector momentum with institutional inflows',
            'sector': 'AI',
            'market_snapshot': {
                'BOTZ': {'price': 31.42, 'volume': 359773},
                'ROBO': {'price': 57.93, 'volume': 32891},
                'ARKQ': {'price': 85.74, 'volume': 103217}
            },
            'source_article': {'title': 'AI ETFs See Record Inflows', 'search_term': 'AI ETF'}
        },
        {
            'signal': 'Bullish',
            'confidence': 8,
            'affected_etfs': ['ITA', 'XAR', 'DFEN'],
            'reasoning': 'Defense spending increases drive sector optimism',
            'sector': 'Defense',
            'market_snapshot': {
                'ITA': {'price': 181.76, 'volume': 726277},
                'XAR': {'price': 200.79, 'volume': 111597},
                'DFEN': {'price': 46.63, 'volume': 528594}
            },
            'source_article': {'title': 'Defense Budget Increases', 'search_term': 'defense ETF'}
        }
    ]
    
    # Test consolidated report creation
    consolidated_report = create_consolidated_signal_report(mock_analyses, datetime.now().isoformat())
    
    if consolidated_report:
        print("✅ Successfully created consolidated report!")
        print("\\n" + "="*60)
        print("📊 CONSOLIDATED SIGNAL REPORT:")
        print("="*60)
        
        print(f"📋 Executive Summary:")
        print(f"   {consolidated_report['executive_summary']}")
        
        print(f"\\n💼 Market Sentiment: {consolidated_report['market_sentiment']}")
        print(f"⚡ Conviction Level: {consolidated_report['conviction_level']}")
        print("="*60)
        return True
    else:
        print("❌ Failed to create consolidated report")
        return False

# MAIN EXECUTION
if __name__ == "__main__":
    import json
    
    # Check for debug flag
    if "--debug" in sys.argv:
        os.environ["DEBUG"] = "true"
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("🐛 Debug mode enabled")
    
    # Check for test mode
    if "test" in sys.argv:
        logger.info("🧪 Running MarketMan test analysis...")
        
        # Run test with sample data
        headline = "AI ETF BOTZ Sees Record Inflows as Robotics Automation Accelerates"
        summary = "Robotics and AI ETFs are experiencing unprecedented investor interest as companies accelerate automation adoption."
        
        market_snapshot = get_market_snapshot()
        analysis_result = analyze_thematic_etf_news(headline, summary, etf_prices=market_snapshot, memory=memory)
        
        if analysis_result:
            logger.info("✅ MarketMan analysis successful!")
            print("\\n" + "="*60)
            print("🎯 MarketMan ANALYSIS RESULT:")
            print("="*60)
            print(json.dumps(analysis_result, indent=2))
            print("="*60)
        else:
            logger.error("❌ Test analysis failed")
    
    elif "--test-tactical" in sys.argv:
        success = test_tactical_explanation()
        sys.exit(0 if success else 1)
    
    elif "--test-consolidated" in sys.argv:
        success = test_consolidated_reporting()
        sys.exit(0 if success else 1)
    
    else:
        # Normal operation
        logger.info("🚀 Starting MarketMan News Analysis System...")
        
        # Initialize the news analyzer
        analyzer = NewsAnalyzer()
        
        # Process new Google Alerts
        analyzer.process_alerts()
        
        logger.info("✅ MarketMan analysis cycle complete")
