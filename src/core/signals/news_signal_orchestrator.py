"""
MarketMan News Analyzer - Refactored main orchestrator
Analyzes Google Alerts for thematic ETF opportunities and creates consolidated reports
"""
import os
import sys
import logging
from datetime import datetime
import pprint

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from integrations.pushover_utils import send_energy_alert, send_system_alert
from core.database.market_memory import MarketMemory
from core.journal.alert_batcher import queue_alert, process_alert_queue, BatchStrategy

# Import refactored modules
from core.signals.etf_signal_engine import (
    analyze_thematic_etf_news,
    generate_tactical_explanation,
    categorize_etfs_by_sector,
)
from src.core.ingestion.market_data import get_market_snapshot, get_etf_prices, adjust_price_anchors_for_splits
from integrations.gmail_poller import GmailPoller
from integrations.notion_reporter import NotionReporter
from core.journal.report_consolidator import create_consolidated_signal_report
from src.core.utils.config_loader import get_config
from core.ingestion.technicals import get_batch_technicals
from core.signals.pattern_recognizer import create_pattern_recognizer
# from src.core.ingestion.news_orchestrator import create_news_orchestrator

# Set up logging with debug control
DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"
log_level = logging.DEBUG if DEBUG_MODE else logging.INFO
logger = logging.getLogger(__name__)

# Alert batching configuration
ALERT_STRATEGY = os.getenv("ALERT_STRATEGY", "smart_batch").lower()
BATCH_STRATEGY_MAP = {
    "immediate": BatchStrategy.IMMEDIATE,
    "time_window": BatchStrategy.TIME_WINDOW,
    "daily_digest": BatchStrategy.DAILY_DIGEST,
    "smart_batch": BatchStrategy.SMART_BATCH,
}
CURRENT_BATCH_STRATEGY = BATCH_STRATEGY_MAP.get(ALERT_STRATEGY, BatchStrategy.SMART_BATCH)

# Initialize MarketMemory for contextual tracking
memory = MarketMemory()


def filter_high_conviction_etfs(session_analyses, min_mentions=2):
    """Filter ETFs that appear in multiple analyses and rank by cumulative confidence"""
    etf_scores = {}

    # Calculate cumulative scores for each ETF
    for analysis in session_analyses:
        confidence = analysis.get("confidence", 0)
        for etf in analysis.get("affected_etfs", []):
            if etf not in etf_scores:
                etf_scores[etf] = {
                    "mentions": 0,
                    "cumulative_confidence": 0,
                    "analyses": [],
                    "avg_confidence": 0,
                }

            etf_scores[etf]["mentions"] += 1
            etf_scores[etf]["cumulative_confidence"] += confidence
            etf_scores[etf]["analyses"].append(analysis)

    # Calculate average confidence for each ETF
    for etf, data in etf_scores.items():
        data["avg_confidence"] = data["cumulative_confidence"] / data["mentions"]

    # Filter ETFs with minimum mentions and exclude broad-tech unless no alternatives
    qualified_etfs = {}
    broad_tech_etfs = {"XLK", "QQQ", "VGT", "FTEC", "IYW", "VTI", "SPY"}

    # First pass: Include specialized ETFs with sufficient mentions
    for etf, data in etf_scores.items():
        if data["mentions"] >= min_mentions and etf not in broad_tech_etfs:
            qualified_etfs[etf] = data

    # Second pass: Include broad-tech only if no specialized alternatives qualify
    if not qualified_etfs:
        logger.info("⚠️ No specialized ETFs qualify, falling back to broad-market funds")
        for etf, data in etf_scores.items():
            if data["mentions"] >= min_mentions and etf in broad_tech_etfs:
                qualified_etfs[etf] = data

    # Sort by cumulative confidence (highest first)
    sorted_etfs = sorted(
        qualified_etfs.items(), key=lambda x: x[1]["cumulative_confidence"], reverse=True
    )

    logger.info(
        f"🎯 Filtered to {len(sorted_etfs)} high-conviction ETFs from {len(etf_scores)} total"
    )
    return sorted_etfs[:3]  # Return top 3 only


def check_technical_support(etf, market_data, support_threshold=0.03):
    """Check if ETF has acceptable technical support (not overextended)"""
    if not market_data or etf not in market_data:
        logger.warning(f"⚠️ No market data for {etf}, skipping technical filter")
        return True, 0.0  # Allow through if no data available

    etf_data = market_data[etf]
    current_price = etf_data.get("price", 0)
    daily_change = etf_data.get("change_pct", 0) / 100  # Convert percentage to decimal

    if current_price <= 0:
        logger.warning(f"⚠️ Invalid price for {etf}, skipping technical filter")
        return True, 0.0  # Allow through if invalid price

    # Estimate support as recent low (conservative approach)
    # Using 2x daily volatility as support distance proxy
    estimated_support = current_price * (1 - abs(daily_change) * 2)

    support_gap = (
        (current_price - estimated_support) / estimated_support if estimated_support > 0 else 0
    )

    is_acceptable = support_gap < support_threshold

    logger.debug(
        f"📊 {etf}: Price ${current_price:.2f}, Support gap {support_gap:.1%}, Acceptable: {is_acceptable}"
    )

    return is_acceptable, support_gap


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

        # Before batch analysis
        logger.info(f"[DEBUG] Fetching ETF prices for batch analysis...")
        etf_prices, used_fallback, fallback_reason = get_etf_prices()
        logger.info(f"[DEBUG] ETF prices fetched: {pprint.pformat(etf_prices)}")
        self.market_data_fallback = used_fallback
        self.market_data_fallback_reason = fallback_reason

        # Fetch technicals and pattern results for all ETFs in the snapshot
        config = get_config().load_settings()
        risk_config = config.get('risk', {})
        etf_symbols = list(etf_prices.keys())
        technicals = get_batch_technicals(etf_symbols)
        pattern_recognizer = create_pattern_recognizer()
        pattern_results = pattern_recognizer.detect_patterns(etf_symbols, technicals)

        for alert in alerts:
            logger.info(f"Processing alert for: {alert['search_term']}")

            for article in alert["articles"]:
                try:
                    # Get contextual insights from memory
                    contextual_insight = memory.get_contextual_insight(
                        {"signal": "Neutral", "affected_etfs": []}, []
                    )

                    # Analyze the article
                    analysis = analyze_thematic_etf_news(
                        headline=article["title"],
                        summary=article["snippet"],
                        snippet=article["snippet"],
                        etf_prices=etf_prices,
                        contextual_insight=contextual_insight,
                        memory=memory,
                        technicals=technicals,
                        pattern_results=pattern_results,
                        risk_config=risk_config,
                    )

                    if not analysis:
                        continue

                    # Add market snapshot to analysis
                    analysis["market_snapshot"] = etf_prices

                    # Apply split adjustments to price anchors if needed
                    if etf_prices and any(etf_data.get('split_factor', 1.0) != 1.0 for etf_data in etf_prices.values()):
                        split_adjustments = {
                            symbol: data.get('split_factor', 1.0) 
                            for symbol, data in etf_prices.items() 
                            if data.get('split_factor', 1.0) != 1.0
                        }
                        if split_adjustments:
                            analysis["price_anchors"] = adjust_price_anchors_for_splits(
                                analysis.get("price_anchors", {}), 
                                split_adjustments
                            )
                            logger.info(f"🔄 Applied split adjustments to price anchors: {split_adjustments}")

                    # Add metadata for consolidated reporting
                    analysis["source_article"] = {
                        "title": article["title"],
                        "link": article["link"],
                        "search_term": alert["search_term"],
                        "timestamp": alert["timestamp"],
                    }

                    # Focus ETFs using sector intelligence
                    focused_etfs, primary_sector = categorize_etfs_by_sector(
                        analysis.get("affected_etfs", [])
                    )
                    analysis["focused_etfs"] = focused_etfs
                    analysis["primary_sector"] = primary_sector

                    # Track for pattern analysis
                    all_mentioned_etfs.update(focused_etfs)

                    # Add to session collection
                    session_analyses.append(analysis)

                    signal = analysis.get("signal", "Neutral")
                    confidence = analysis.get("confidence", 0)

                    logger.info(
                        f"📊 {signal} signal ({confidence}/10) - {primary_sector or 'Mixed'} - {article['title'][:60]}..."
                    )

                except Exception as e:
                    logger.error(f"Error processing article '{article['title']}': {e}")
                    continue

        # Create consolidated signal report if we have analyses
        if session_analyses:
            logger.info(f"📊 Creating consolidated report from {len(session_analyses)} analyses...")

            # Filter for high-conviction ETFs before creating consolidated report
            high_conviction_etfs = filter_high_conviction_etfs(session_analyses, min_mentions=2)

            if high_conviction_etfs:
                logger.info(f"🎯 High-conviction ETFs identified:")
                for etf, data in high_conviction_etfs:
                    logger.info(
                        f"   • {etf}: {data['mentions']} mentions, {data['cumulative_confidence']:.1f} total confidence, {data['avg_confidence']:.1f} avg"
                    )

                # Update session analyses to focus only on high-conviction ETFs
                filtered_etf_set = {etf for etf, _ in high_conviction_etfs}
                for analysis in session_analyses:
                    # Filter affected_etfs to only include high-conviction ones
                    original_etfs = analysis.get("affected_etfs", [])
                    filtered_etfs = [etf for etf in original_etfs if etf in filtered_etf_set]
                    analysis["affected_etfs"] = filtered_etfs
                    analysis["high_conviction_etfs"] = filtered_etfs
            else:
                logger.info("⚠️ No ETFs meet high-conviction criteria (≥2 mentions)")

            consolidated_report = create_consolidated_signal_report(
                session_analyses, session_timestamp
            )

            notion_url = None  # Initialize outside the if block
            if consolidated_report:
                # Log consolidated report to Notion
                notion_url = self.notion_reporter.log_consolidated_report_to_notion(
                    consolidated_report
                )

            # Apply technical filter to high-conviction signals before queuing
            high_conviction_signals = [
                a for a in session_analyses if a.get("confidence", 0) >= 8
            ]

            if high_conviction_signals:
                logger.info(
                    f"📋 Filtering {len(high_conviction_signals)} high-conviction signals for technical criteria..."
                )

                technically_sound_signals = []

                for analysis in high_conviction_signals:
                    analysis_etfs = analysis.get(
                        "high_conviction_etfs", analysis.get("affected_etfs", [])
                    )
                    qualified_etfs = []

                    for etf in analysis_etfs:
                        is_acceptable, support_gap = check_technical_support(
                            etf, etf_prices
                        )
                        if is_acceptable:
                            qualified_etfs.append(etf)
                            logger.info(
                                f"✅ {etf}: Passes technical filter (support gap: {support_gap:.1%})"
                            )
                        else:
                            logger.info(
                                f"❌ {etf}: Rejected - overextended (support gap: {support_gap:.1%})"
                            )

                    if qualified_etfs:
                        # Update analysis with only technically sound ETFs
                        analysis["filtered_etfs"] = qualified_etfs
                        technically_sound_signals.append(analysis)

                if technically_sound_signals:
                    logger.info(
                        f"🎯 Queueing {len(technically_sound_signals)} technically sound signals..."
                    )

                    for analysis in technically_sound_signals:
                        logger.info(f"[DEBUG] Price anchors for alert: {pprint.pformat(analysis.get('price_anchors', {}))}")
                        alert_id = queue_alert(
                            signal=analysis.get("signal", "Neutral"),
                            confidence=analysis.get("confidence", 0),
                            title=f"High Conviction: {analysis.get('primary_sector', 'Mixed')} Signal",
                            reasoning=analysis.get("reasoning", ""),
                            etfs=analysis.get("filtered_etfs", []),
                            sector=analysis.get("primary_sector", "Mixed"),
                            article_url=notion_url,
                            search_term="filtered_high_conviction",
                            strategy=CURRENT_BATCH_STRATEGY,
                            if_then_scenario=analysis.get("if_then_scenario", ""),
                            contradictory_signals=analysis.get("contradictory_signals", ""),
                            uncertainty_metric=analysis.get("uncertainty_metric", ""),
                            price_anchors=analysis.get("price_anchors", {}),
                            position_risk_bracket=analysis.get("position_risk_bracket", ""),
                        )
                        logger.info(f"✅ Alert queued: {alert_id[:8]}")
                else:
                    logger.info("📉 No signals pass technical filtering criteria")
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
                if (
                    pattern.get("consecutive_days", 0) >= 3
                    or pattern.get("average_confidence", 0) >= 7
                ):
                    significant_patterns.append(pattern)

        if significant_patterns:
            logger.info(f"📊 Found {len(significant_patterns)} significant patterns")
            # TODO: Log significant patterns to Notion (requires separate patterns database)

    def _process_alert_batches(self):
        """Process any pending alert batches, passing fallback warning if present"""
        logger.info("📱 Processing alert queue...")
        fallback_warning = self.market_data_fallback_reason if getattr(self, 'market_data_fallback', False) else None
        batch_results = process_alert_queue(fallback_warning=fallback_warning)

        if batch_results:
            for strategy, success in batch_results.items():
                status = "✅" if success else "❌"
                logger.info(f"{status} Batch sent via {strategy} strategy")
        else:
            logger.info("📭 No batches ready to send")


def test_tactical_explanation():
    """Test the tactical explanation generation"""
    test_analysis = {
        "signal": "Bullish",
        "confidence": 8,
        "affected_etfs": ["QQQ", "TQQQ", "VTI"],
        "reasoning": "Strong earnings beats from tech giants driving sector momentum",
        "sector": "Technology",
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
            "signal": "Bullish",
            "confidence": 9,
            "affected_etfs": ["BOTZ", "ROBO", "ARKQ"],
            "reasoning": "Strong AI sector momentum with institutional inflows",
            "sector": "AI",
            "market_snapshot": {
                "BOTZ": {"price": 31.42, "volume": 359773},
                "ROBO": {"price": 57.93, "volume": 32891},
                "ARKQ": {"price": 85.74, "volume": 103217},
            },
            "source_article": {"title": "AI ETFs See Record Inflows", "search_term": "AI ETF"},
        },
        {
            "signal": "Bullish",
            "confidence": 8,
            "affected_etfs": ["ITA", "XAR", "DFEN"],
            "reasoning": "Defense spending increases drive sector optimism",
            "sector": "Defense",
            "market_snapshot": {
                "ITA": {"price": 181.76, "volume": 726277},
                "XAR": {"price": 200.79, "volume": 111597},
                "DFEN": {"price": 46.63, "volume": 528594},
            },
            "source_article": {"title": "Defense Budget Increases", "search_term": "defense ETF"},
        },
    ]

    # Test consolidated report creation
    consolidated_report = create_consolidated_signal_report(
        mock_analyses, datetime.now().isoformat()
    )

    if consolidated_report:
        print("✅ Successfully created consolidated report!")
        print("\\n" + "=" * 60)
        print("📊 CONSOLIDATED SIGNAL REPORT:")
        print("=" * 60)

        print(f"📋 Executive Summary:")
        print(f"   {consolidated_report['executive_summary']}")

        print(f"\\n💼 Market Sentiment: {consolidated_report['market_sentiment']}")
        print(f"⚡ Conviction Level: {consolidated_report['conviction_level']}")
        print("=" * 60)
        return True
    else:
        print("❌ Failed to create consolidated report")
        return False


def test_etf_filtering():
    """Test the new ETF filtering and ranking system"""
    print("\\n🧪 Testing enhanced ETF filtering system...")

    # Mock analyses that demonstrate the filtering logic
    mock_analyses = [
        {
            "confidence": 8,
            "signal": "Bullish",
            "affected_etfs": ["BOTZ", "XLK"],  # BOTZ is specialized, XLK is broad
            "sector": "AI",
        },
        {
            "confidence": 7,
            "signal": "Bullish",
            "affected_etfs": ["BOTZ", "ROBO"],  # BOTZ mentioned again (frequency)
            "sector": "AI",
        },
        {
            "confidence": 6,
            "signal": "Bullish",
            "affected_etfs": ["BOTZ"],  # BOTZ mentioned third time
            "sector": "AI",
        },
        {
            "confidence": 8,
            "signal": "Bullish",
            "affected_etfs": ["XLK"],  # XLK mentioned second time but still broad
            "sector": "Technology",
        },
    ]

    # Test filtering
    filtered_etfs = filter_high_conviction_etfs(mock_analyses, min_mentions=2)

    print(f"\\n📊 ETF Filtering Results:")
    print(f"   Input: 4 analyses mentioning BOTZ(3x), XLK(2x), ROBO(1x)")
    print(f"   Filtered: {len(filtered_etfs)} ETFs")

    for etf, data in filtered_etfs:
        print(
            f"   • {etf}: {data['mentions']} mentions, {data['cumulative_confidence']:.1f} total confidence"
        )

    # Should prioritize BOTZ (specialized, 3 mentions, 21 total confidence) over XLK (broad, 2 mentions, 14 total confidence)
    if filtered_etfs and filtered_etfs[0][0] == "BOTZ":
        print("   ✅ Correctly prioritized specialized ETF (BOTZ) over broad ETF (XLK)")
        return True
    else:
        print("   ❌ Failed to prioritize specialized ETF")
        return False


def test_technical_filtering():
    """Test technical support filtering"""
    print("\\n🧪 Testing technical support filtering...")

    # Mock market data with different support scenarios
    mock_market_data = {
        "GOOD_ETF": {"price": 100.0, "change_percent": 1.0},  # 2% support gap - acceptable
        "BAD_ETF": {"price": 100.0, "change_percent": 5.0},  # 10% support gap - overextended
        "NO_DATA": {},  # No price data
    }

    test_results = []
    for etf, data in mock_market_data.items():
        acceptable, gap = check_technical_support(etf, {etf: data})
        test_results.append((etf, acceptable, gap))
        print(f"   • {etf}: Support gap {gap:.1%}, Acceptable: {acceptable}")

    # Should accept GOOD_ETF, reject BAD_ETF and NO_DATA
    expected = [("GOOD_ETF", True), ("BAD_ETF", False), ("NO_DATA", False)]
    actual = [(etf, acceptable) for etf, acceptable, _ in test_results]

    if all(exp in actual for exp in expected):
        print("   ✅ Technical filtering working correctly")
        return True
    else:
        print("   ❌ Technical filtering failed")
        return False


# MAIN EXECUTION
if __name__ == "__main__":
    import sys
    import logging
    from src.core.utils.config_loader import get_config

    # Setup logging
    logger = logging.getLogger(__name__)

    logger.info("🚀 Starting MarketMan News Analysis System...")

    try:
        # Load configuration
        config_loader = get_config()
        config = config_loader.load_settings()
        
        # Create the proper news orchestrator with multiple sources
        orchestrator = create_news_orchestrator(config)
        
        # Get tracked tickers from config
        tracked_tickers = config.get('news_ingestion', {}).get('tracked_tickers', [])
        
        logger.info(f"📰 Using multiple news sources: Finnhub, NewsAPI, NewData")
        logger.info(f"🎯 Tracking {len(tracked_tickers)} ETFs: {', '.join(tracked_tickers[:5])}{'...' if len(tracked_tickers) > 5 else ''}")
        
        # Run the proper news processing cycle with signal generation
        results = orchestrator.process_signals(
            tickers=tracked_tickers,
            hours_back=24  # Last 24 hours for comprehensive coverage
        )
        
        logger.info(f"📊 News Processing Results:")
        logger.info(f"  📰 Raw news items: {results['raw_news_count']}")
        logger.info(f"  ✅ Filtered items: {results['filtered_news_count']}")
        logger.info(f"  📦 Batches created: {results['batches_created']}")
        logger.info(f"  🤖 AI processed: {results['ai_processed_batches']}")
        
        # Show source statistics
        source_stats = results.get('source_stats', {})
        if source_stats:
            logger.info(f"📰 News Sources Used:")
            for source in source_stats.get('sources', []):
                logger.info(f"  • {source['source']}: {source['daily_requests']}/{source['daily_limit']} calls")
        
        # Show cost impact
        cost_stats = results.get('cost_stats', {})
        if cost_stats:
            logger.info(f"💰 Cost Impact:")
            logger.info(f"  • AI calls used: {cost_stats.get('daily_ai_calls', 0)}")
            logger.info(f"  • Cost incurred: ${cost_stats.get('monthly_ai_cost', 0.0):.2f}")
        
        if results['ai_processed_batches'] > 0:
            logger.info("🎯 Signals generated successfully!")
        else:
            logger.info("📭 No signals generated - this is normal if no relevant news found")
            logger.info("✅ Pipeline is working correctly (filtering out irrelevant content)")
        
        logger.info("✅ MarketMan analysis cycle complete")
        
    except Exception as e:
        logger.error(f"❌ Error in news analysis cycle: {e}")
        sys.exit(1)
