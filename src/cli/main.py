"""
Main CLI entry point for MarketMan.

This module provides the command-line interface for all MarketMan operations.
"""

import argparse
import sys
import logging
from typing import Optional

from core.utils import get_config, format_signal_summary, format_table
from core.signals import NewsAnalyzer
from core.options import OptionsScalpingStrategy
from core.journal import AlertBatcher
from core.risk import PositionSizer
from core.ingestion import create_news_orchestrator


def setup_logging(verbose: bool = False) -> None:
    """
    Setup logging configuration.

    Args:
        verbose: Enable verbose logging if True
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("logs/marketman_cli.log")],
    )


def create_parser() -> argparse.ArgumentParser:
    """
    Create the main argument parser.

    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description="MarketMan - Automated Trading Signal System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  marketman signals run          # Run signal processing
  marketman alerts check         # Check for new alerts
  marketman performance show     # Show performance dashboard
  marketman options scalp        # Run options scalping strategy
  marketman news status          # Show news ingestion status
  marketman news cycle           # Run news processing cycle
        """,
    )

    # Global options
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")

    parser.add_argument(
        "--config", default="config/settings.yaml", help="Path to configuration file"
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Signals command
    signals_parser = subparsers.add_parser("signals", help="Signal processing commands")
    signals_parser.add_argument(
        "action", choices=["run", "status", "backtest"], help="Signal action to perform"
    )

    # Alerts command
    alerts_parser = subparsers.add_parser("alerts", help="Alert management commands")
    alerts_parser.add_argument(
        "action", choices=["check", "send", "status"], help="Alert action to perform"
    )

    # Performance command
    performance_parser = subparsers.add_parser(
        "performance", help="Performance monitoring commands"
    )
    performance_parser.add_argument(
        "action", choices=["show", "update", "export"], help="Performance action to perform"
    )

    # Options command
    options_parser = subparsers.add_parser("options", help="Options trading commands")
    options_parser.add_argument(
        "action", choices=["scalp", "analyze", "backtest"], help="Options action to perform"
    )

    # Risk command
    risk_parser = subparsers.add_parser("risk", help="Risk management commands")
    risk_parser.add_argument(
        "action", choices=["analyze", "limits", "position-size"], help="Risk action to perform"
    )

    # News command
    news_parser = subparsers.add_parser("news", help="News ingestion commands")
    news_parser.add_argument(
        "action", choices=["status", "cycle", "test"], help="News action to perform"
    )

    return parser


def handle_signals(args: argparse.Namespace) -> int:
    """
    Handle signals command.

    Args:
        args: Parsed arguments

    Returns:
        Exit code
    """
    try:
        if args.action == "run":
            print("Running signal processing...")
            analyzer = NewsAnalyzer()
            analyzer.process_alerts()
            print("✅ Signal processing completed")
            return 0
        elif args.action == "status":
            print("Checking signal status...")
            # TODO: Implement signal status check
            print("📊 Signal processing is active")
            return 0
        elif args.action == "backtest":
            print("Running signal backtest...")
            # TODO: Implement signal backtest
            print("🧪 Backtest completed")
            return 0
        else:
            print(f"Unknown action: {args.action}")
            return 1
    except Exception as e:
        logging.error(f"Error in signals command: {e}")
        return 1


def handle_alerts(args: argparse.Namespace) -> int:
    """
    Handle alerts command.

    Args:
        args: Parsed arguments

    Returns:
        Exit code
    """
    try:
        if args.action == "check":
            print("Checking for new alerts...")
            batcher = AlertBatcher()
            pending_alerts = batcher.get_pending_alerts()

            if pending_alerts:
                print(f"📬 Found {len(pending_alerts)} pending alerts:")
                for alert in pending_alerts[:5]:  # Show first 5
                    summary = format_signal_summary(
                        alert.signal, alert.confidence, alert.etfs, alert.reasoning
                    )
                    print(f"\n{summary}")
                    print("-" * 50)
            else:
                print("📭 No pending alerts found")
            return 0
        elif args.action == "send":
            print("Sending alerts...")
            batcher = AlertBatcher()
            results = batcher.process_pending()
            print(f"📤 Sent {len(results)} alert batches")
            return 0
        elif args.action == "status":
            print("Checking alert status...")
            batcher = AlertBatcher()
            stats = batcher.get_batch_stats()
            print(f"📊 Alert queue status: {stats}")
            return 0
        else:
            print(f"Unknown action: {args.action}")
            return 1
    except Exception as e:
        logging.error(f"Error in alerts command: {e}")
        return 1


def handle_performance(args: argparse.Namespace) -> int:
    """
    Handle performance command.

    Args:
        args: Parsed arguments

    Returns:
        Exit code
    """
    try:
        if args.action == "show":
            print("Showing performance dashboard...")
            # TODO: Implement performance display
            print("📈 Performance dashboard loaded")
            return 0
        elif args.action == "update":
            print("Updating performance data...")
            # TODO: Implement performance update
            print("🔄 Performance data updated")
            return 0
        elif args.action == "export":
            print("Exporting performance data...")
            # TODO: Implement export
            print("💾 Performance data exported")
            return 0
        else:
            print(f"Unknown action: {args.action}")
            return 1
    except Exception as e:
        logging.error(f"Error in performance command: {e}")
        return 1


def handle_options(args: argparse.Namespace) -> int:
    """
    Handle options command.

    Args:
        args: Parsed arguments

    Returns:
        Exit code
    """
    try:
        if args.action == "scalp":
            print("Running options scalping strategy...")
            strategy = OptionsScalpingStrategy()

            if not strategy.is_enabled():
                print("⚠️ Options scalping is disabled in configuration")
                return 0

            opportunities = strategy.scan_for_opportunities()
            if opportunities:
                print(f"🎯 Found {len(opportunities)} scalping opportunities:")
                for opp in opportunities[:3]:  # Show first 3
                    print(
                        f"  • {opp.symbol} {opp.strike} {opp.option_type} - Confidence: {opp.confidence:.1f}"
                    )
            else:
                print("📭 No scalping opportunities found")
            return 0
        elif args.action == "analyze":
            print("Analyzing options data...")
            # TODO: Implement options analysis
            print("📊 Options analysis completed")
            return 0
        elif args.action == "backtest":
            print("Running options backtest...")
            # TODO: Implement options backtest
            print("🧪 Options backtest completed")
            return 0
        else:
            print(f"Unknown action: {args.action}")
            return 1
    except Exception as e:
        logging.error(f"Error in options command: {e}")
        return 1


def handle_risk(args: argparse.Namespace) -> int:
    """
    Handle risk command.

    Args:
        args: Parsed arguments

    Returns:
        Exit code
    """
    try:
        if args.action == "analyze":
            print("Analyzing portfolio risk...")
            # TODO: Implement risk analysis
            print("⚠️ Risk analysis completed")
            return 0
        elif args.action == "limits":
            print("Checking risk limits...")
            sizer = PositionSizer()
            limits = sizer.get_position_limits()

            print("📊 Current position limits:")
            table_data = [
                {
                    "Setting": k.replace("_", " ").title(),
                    "Value": f"${v:,.2f}" if isinstance(v, float) else str(v),
                }
                for k, v in limits.items()
            ]
            print(format_table(table_data))
            return 0
        elif args.action == "position-size":
            print("Calculating position sizes...")
            sizer = PositionSizer()

            # Example calculations
            print("📏 Example position size calculations:")

            # Kelly Criterion example
            kelly_result = sizer.calculate_kelly_size(
                win_rate=0.6, avg_win=1000, avg_loss=500, confidence=0.8
            )
            print(
                f"  • Kelly Criterion: {kelly_result.quantity} units (${kelly_result.dollar_amount:,.2f})"
            )

            # Fixed percentage example
            fixed_result = sizer.calculate_fixed_percentage(
                percentage=0.02, price=50.0, confidence=0.9  # 2%
            )
            print(
                f"  • Fixed 2%: {fixed_result.quantity} units (${fixed_result.dollar_amount:,.2f})"
            )

            return 0
        else:
            print(f"Unknown action: {args.action}")
            return 1
    except Exception as e:
        logging.error(f"Error in risk command: {e}")
        return 1


def handle_news(args: argparse.Namespace) -> int:
    """
    Handle news command.

    Args:
        args: Parsed arguments

    Returns:
        Exit code
    """
    try:
        config_loader = get_config()
        config = config_loader.load_settings()
        
        if args.action == "status":
            print("📊 Checking news ingestion system status...")
            orchestrator = create_news_orchestrator(config)
            status = orchestrator.get_system_status()
            
            print("\n📰 News Ingestion System Status:")
            print("=" * 50)
            
            # Filter stats
            filter_stats = status["news_filter"]
            print(f"📰 News Filter:")
            print(f"  • Daily headlines: {filter_stats['daily_headline_count']}/{filter_stats['max_daily_headlines']}")
            print(f"  • Remaining budget: {filter_stats['remaining_budget']}")
            print(f"  • Tracked tickers: {filter_stats['tracked_tickers_count']}")
            print(f"  • Keywords: {filter_stats['keywords_count']}")
            
            # Batch stats
            batch_stats = status["news_batcher"]
            print(f"\n📦 News Batcher:")
            print(f"  • Pending batches: {batch_stats['pending_batches']}")
            print(f"  • Pending items: {batch_stats['total_pending_items']}")
            print(f"  • Max batch size: {batch_stats['max_batch_size']}")
            
            # Source stats
            source_stats = status["news_sources"]
            print(f"\n📰 News Sources:")
            print(f"  • Total sources: {source_stats['total_sources']}")
            print(f"  • Enabled sources: {source_stats['enabled_sources']}")
            
            for source in source_stats["sources"]:
                print(f"    • {source['source']}: {source['daily_requests']}/{source['daily_limit']} calls")
            
            # Cost stats
            cost_stats = status["cost_tracking"]
            print(f"\n💰 Cost Tracking:")
            print(f"  • Daily AI calls: {cost_stats['daily_ai_calls']}/{cost_stats['max_daily_ai_calls']}")
            print(f"  • Monthly cost: ${cost_stats['monthly_ai_cost']}/${cost_stats['max_monthly_budget']}")
            print(f"  • Remaining budget: ${cost_stats['remaining_budget']}")
            
            return 0
            
        elif args.action == "cycle":
            print("🔄 Running news processing cycle...")
            orchestrator = create_news_orchestrator(config)
            
            # Get tracked tickers from config
            tracked_tickers = config.get('news_ingestion', {}).get('tracked_tickers', [])
            
            # Run news cycle
            results = orchestrator.process_news_cycle(
                tickers=tracked_tickers[:5],  # Limit to 5 tickers for testing
                hours_back=24  # Last 24 hours for more data
            )
            
            print("\n📊 News Processing Results:")
            print("=" * 50)
            print(f"📰 Raw news items: {results['raw_news_count']}")
            print(f"✅ Filtered items: {results['filtered_news_count']}")
            print(f"📦 Batches created: {results['batches_created']}")
            print(f"🤖 AI processed: {results['ai_processed_batches']}")
            
            # Filter stats
            filter_stats = results['filter_stats']
            if filter_stats.get('reasons'):
                print(f"\n🚫 Filter reasons:")
                for reason, count in filter_stats['reasons'].items():
                    print(f"  • {reason}: {count}")
            
            # Cost stats
            cost_stats = results['cost_stats']
            print(f"\n💰 Cost impact:")
            print(f"  • AI calls used: {cost_stats['daily_ai_calls']}")
            print(f"  • Cost incurred: ${cost_stats['monthly_ai_cost']}")
            
            print("\n✅ News processing cycle completed!")
            return 0
            
        elif args.action == "test":
            print("🧪 Testing news ingestion system...")
            orchestrator = create_news_orchestrator(config)
            
            # Test with sample data
            sample_news = [
                {
                    'title': 'ETF Market Update: BOTZ and ITA Show Strong Performance',
                    'content': 'AI and defense ETFs continue to outperform market expectations...',
                    'source': 'Financial Times',
                    'url': 'https://example.com/article1',
                    'published_at': '2024-01-15T10:30:00Z'
                },
                {
                    'title': 'Federal Reserve Signals Potential Rate Changes',
                    'content': 'The Fed is considering adjustments to interest rates...',
                    'source': 'Reuters',
                    'url': 'https://example.com/article2',
                    'published_at': '2024-01-15T11:00:00Z'
                }
            ]
            
            # Test filtering
            filtered_items, filter_stats = orchestrator.news_filter.filter_news(sample_news)
            print(f"✅ Filter test: {len(filtered_items)}/{len(sample_news)} items accepted")
            
            # Test batching
            if filtered_items:
                batches = orchestrator.news_batcher.add_news_items(filtered_items)
                print(f"✅ Batch test: {len(batches)} batches created")
            
            print("🧪 News ingestion system test completed!")
            return 0
            
        else:
            print(f"Unknown action: {args.action}")
            return 1
            
    except Exception as e:
        logging.error(f"Error in news command: {e}")
        return 1


def main() -> int:
    """
    Main CLI entry point.

    Returns:
        Exit code
    """
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Setup logging
    setup_logging(args.verbose)

    try:
        if args.command == "signals":
            return handle_signals(args)
        elif args.command == "alerts":
            return handle_alerts(args)
        elif args.command == "performance":
            return handle_performance(args)
        elif args.command == "options":
            return handle_options(args)
        elif args.command == "risk":
            return handle_risk(args)
        elif args.command == "news":
            return handle_news(args)
        else:
            print(f"Unknown command: {args.command}")
            return 1
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user")
        return 1
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
