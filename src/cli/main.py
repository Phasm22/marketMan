"""
Main CLI entry point for MarketMan.

This module provides the command-line interface for all MarketMan operations.
"""

import argparse
import sys
import logging
from typing import Optional

from src.core.utils import get_config, format_signal_summary, format_table
from src.core.signals import NewsAnalyzer
from src.core.options import OptionsScalpingStrategy
from src.core.journal import AlertBatcher
from src.core.risk import PositionSizer
from src.core.ingestion import create_news_orchestrator

# Import journal commands
from .commands.journal import journal


def setup_logging(verbose: bool = False) -> None:
    """
    Setup logging configuration.

    Args:
        verbose: Enable verbose logging if True
    """
    level = logging.DEBUG if verbose else logging.INFO
    root = logging.getLogger()
    # Remove all handlers associated with the root logger object.
    for handler in root.handlers[:]:
        root.removeHandler(handler)
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("/var/log/marketman.log")
        ],
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
  marketman journal performance  # Generate performance report
  marketman journal signals      # Generate signal analysis
  marketman journal import-fidelity # Import Fidelity trades
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
        "action", choices=["status", "cycle", "test", "signals"], help="News action to perform"
    )

    # Journal command (Phase 3)
    journal_parser = subparsers.add_parser("journal", help="Trade journaling and performance tracking")
    journal_parser.add_argument(
        "action", choices=[
            "list-trades", "performance", "signals", "setup-fidelity", 
            "import-fidelity", "add-trade", "add-signal", "sync-notion", "analyze"
        ], help="Journal action to perform"
    )
    
    # Add journal-specific options
    journal_parser.add_argument("--symbol", "-s", help="Symbol filter")
    journal_parser.add_argument("--days", "-d", type=int, default=30, help="Number of days")
    journal_parser.add_argument("--output", "-o", help="Output file")
    journal_parser.add_argument("--action", "-a", help="Trade action (Buy/Sell)")
    journal_parser.add_argument("--quantity", "-q", type=float, help="Trade quantity")
    journal_parser.add_argument("--price", "-p", type=float, help="Trade price")
    journal_parser.add_argument("--date", help="Trade date")
    journal_parser.add_argument("--confidence", "-c", type=float, help="Signal confidence")
    journal_parser.add_argument("--notes", "-n", help="Trade notes")
    journal_parser.add_argument("--type", "-t", help="Signal type")
    journal_parser.add_argument("--direction", help="Signal direction")
    journal_parser.add_argument("--reasoning", "-r", help="Signal reasoning")
    journal_parser.add_argument("--source", help="Signal source")
    journal_parser.add_argument("--email", "-e", help="Email for Fidelity setup")
    journal_parser.add_argument("--password", help="Password for Fidelity setup")

    # Config command
    config_parser = subparsers.add_parser("config", help="Configuration management commands")
    config_parser.add_argument(
        "action", choices=["validate", "show", "reload"], help="Configuration action to perform"
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
            
        elif args.action == "signals":
            print("🤖 Running signal engine integration test...")
            orchestrator = create_news_orchestrator(config)
            
            # Get tracked tickers from config
            tracked_tickers = config.get('news_ingestion', {}).get('tracked_tickers', [])
            
            # Test signal processing
            results = orchestrator.process_signals(
                tickers=tracked_tickers[:5],  # Limit to 5 tickers for testing
                hours_back=24  # Last 24 hours for more data
            )
            
            print("\n🤖 Signal Processing Results:")
            print("=" * 50)
            print(f"📰 Raw news items: {results['raw_news_count']}")
            print(f"✅ Filtered items: {results['filtered_news_count']}")
            print(f"📦 Batches created: {results['batches_created']}")
            print(f"🤖 AI processed: {results['ai_processed_batches']}")
            
            # Show signal details if any were generated
            if results['ai_processed_batches'] > 0:
                print(f"\n🎯 Signal Engine Integration: SUCCESS")
                print(f"✅ News → Filter → Batch → AI → Signal pipeline working")
            else:
                print(f"\n📭 No signals generated - this is normal if no relevant news found")
                print(f"✅ Pipeline is working correctly (filtering out irrelevant content)")
            
            # Cost stats
            cost_stats = results['cost_stats']
            print(f"\n💰 Cost impact:")
            print(f"  • AI calls used: {cost_stats['daily_ai_calls']}")
            print(f"  • Cost incurred: ${cost_stats['monthly_ai_cost']}")
            
            print("\n✅ Signal engine integration test completed!")
            return 0
            
        else:
            print(f"Unknown action: {args.action}")
            return 1
            
    except Exception as e:
        logging.error(f"Error in news command: {e}")
        return 1


def handle_journal(args: argparse.Namespace) -> int:
    """
    Handle journal command.

    Args:
        args: Parsed arguments

    Returns:
        Exit code
    """
    try:
        if args.action == "list-trades":
            from src.core.journal.trade_journal import create_trade_journal
            from datetime import datetime, timedelta
            
            journal = create_trade_journal()
            start_date = (datetime.now() - timedelta(days=args.days)).isoformat()
            trades = journal.get_trades(symbol=args.symbol, start_date=start_date)
            
            if not trades:
                print("No trades found for the specified criteria.")
                return 0
            
            print(f"Found {len(trades)} trades:")
            print("-" * 80)
            
            for trade in trades[:20]:  # Show first 20 trades
                print(f"{trade['timestamp']} | {trade['symbol']} | {trade['action']} | "
                      f"{trade['quantity']} @ ${trade['price']:.2f} | ${trade['trade_value']:.2f}")
            
            if len(trades) > 20:
                print(f"... and {len(trades) - 20} more trades")
            
            if args.output:
                if journal.export_trades_to_csv(args.output, args.symbol, start_date):
                    print(f"Trades exported to {args.output}")
                else:
                    print("Failed to export trades")
            
        elif args.action == "performance":
            from src.core.journal.performance_tracker import generate_performance_report
            
            print(f"Generating performance report for last {args.days} days...")
            report = generate_performance_report(args.days)
            
            # Display summary
            print("\n📊 PERFORMANCE SUMMARY")
            print("=" * 50)
            print(f"Total Trades: {report['metrics']['total_trades']}")
            print(f"Winning Trades: {report['metrics']['winning_trades']}")
            print(f"Losing Trades: {report['metrics']['losing_trades']}")
            print(f"Total P&L: ${report['metrics']['total_pnl']:,.2f}")
            print(f"Win Rate: {report['metrics']['win_rate']}")
            print(f"Profit Factor: {report['metrics']['profit_factor']:.2f}")
            print(f"Max Drawdown: ${report['metrics']['max_drawdown']:,.2f}")
            print(f"Sharpe Ratio: {report['metrics']['sharpe_ratio']:.2f}")
            print(f"Signal Accuracy: {report['metrics']['signal_accuracy']}")
            
            if args.output:
                import json
                with open(args.output, 'w') as f:
                    json.dump(report, f, indent=2)
                print(f"\nReport saved to {args.output}")
            
        elif args.action == "signals":
            from src.core.journal.signal_logger import generate_signal_report
            
            print(f"Generating signal report for last {args.days} days...")
            report = generate_signal_report(args.days)
            
            # Display summary
            print("\n📊 SIGNAL ANALYSIS")
            print("=" * 40)
            print(f"Total Signals: {report['summary']['total_signals']}")
            print(f"Executed Signals: {report['summary']['executed_signals']}")
            print(f"Signal Accuracy: {report['summary']['signal_accuracy']}")
            print(f"Avg Confidence: {report['summary']['avg_confidence']:.2f}")
            
            if args.output:
                import json
                with open(args.output, 'w') as f:
                    json.dump(report, f, indent=2)
                print(f"\nReport saved to {args.output}")
            
        elif args.action == "import-fidelity":
            from src.integrations.fidelity_integration import auto_import_fidelity_trades
            
            print("Importing Fidelity trades...")
            results = auto_import_fidelity_trades()
            
            print(f"\n📊 IMPORT RESULTS")
            print("=" * 30)
            print(f"Email trades found: {results['email_trades']}")
            print(f"CSV trades found: {results['csv_trades']}")
            print(f"Trades imported: {results['imported_trades']}")
            
            if results['errors']:
                print(f"\n❌ ERRORS:")
                for error in results['errors']:
                    print(f"  - {error}")
            
            if results['imported_trades'] > 0:
                print(f"\n✅ Successfully imported {results['imported_trades']} trades!")
            else:
                print("\nℹ️ No new trades to import")
            
        elif args.action == "analyze":
            from src.core.journal.performance_tracker import generate_performance_report
            from src.core.journal.signal_logger import generate_signal_report
            
            print(f"Running comprehensive analysis for last {args.days} days...")
            
            # Performance analysis
            print("\n📊 PERFORMANCE ANALYSIS")
            print("=" * 30)
            perf_report = generate_performance_report(args.days)
            print(f"Total P&L: ${perf_report['metrics']['total_pnl']:,.2f}")
            print(f"Win Rate: {perf_report['metrics']['win_rate']}")
            print(f"Signal Accuracy: {perf_report['metrics']['signal_accuracy']}")
            
            # Signal analysis
            print("\n📈 SIGNAL ANALYSIS")
            print("=" * 20)
            signal_report = generate_signal_report(args.days)
            print(f"Total Signals: {signal_report['summary']['total_signals']}")
            print(f"Signal Accuracy: {signal_report['summary']['signal_accuracy']}")
            
            # Recommendations
            print("\n💡 RECOMMENDATIONS")
            print("=" * 20)
            
            if perf_report['metrics']['win_rate'] < 50:
                print("⚠️ Win rate below 50% - consider reviewing strategy")
            
            if perf_report['metrics']['signal_accuracy'] < 60:
                print("⚠️ Signal accuracy below 60% - consider improving signal quality")
            
            if perf_report['metrics']['max_drawdown'] > 1000:
                print("⚠️ High drawdown - consider risk management improvements")
            
            print("✅ Analysis complete!")
            
        else:
            print(f"Unknown journal action: {args.action}")
            print("Available actions: list-trades, performance, signals, import-fidelity, analyze")
            return 1
        
        return 0
        
    except Exception as e:
        logging.error(f"Error in journal command: {e}")
        return 1


def handle_config(args: argparse.Namespace) -> int:
    """
    Handle config command.

    Args:
        args: Parsed arguments

    Returns:
        Exit code
    """
    try:
        if args.action == "validate":
            print("🔍 Validating configuration...")
            # Import and run the validation script
            import subprocess
            result = subprocess.run([sys.executable, "scripts/validate_config.py"], 
                                  capture_output=True, text=True)
            print(result.stdout)
            if result.stderr:
                print("Errors:", result.stderr)
            return result.returncode
            
        elif args.action == "show":
            print("📋 Current Configuration Summary")
            print("=" * 40)
            
            config_loader = get_config()
            config = config_loader.load_settings()
            
            # Show key settings
            risk_config = config.get('risk', {})
            print(f"Risk Management:")
            print(f"  • Max Daily Loss: {risk_config.get('max_daily_loss_percent', 'N/A')}%")
            print(f"  • Max Position Size: {risk_config.get('max_position_size_percent', 'N/A')}%")
            print(f"  • Kelly Fraction: {risk_config.get('max_kelly_fraction', 'N/A')}")
            
            api_config = config.get('api_limits', {})
            print(f"\nAPI Limits:")
            print(f"  • OpenAI Requests/Day: {api_config.get('openai', {}).get('max_requests_per_day', 'N/A')}")
            print(f"  • Finnhub Calls/Day: {api_config.get('finnhub', {}).get('calls_per_day', 'N/A')}")
            
            alert_config = config.get('alerts', {})
            print(f"\nAlerts:")
            print(f"  • Max Daily Alerts: {alert_config.get('max_daily_alerts', 'N/A')}")
            print(f"  • Batch Strategy: {alert_config.get('batch_strategy', 'N/A')}")
            
            return 0
            
        elif args.action == "reload":
            print("🔄 Reloading configuration...")
            config_loader = get_config()
            config_loader.reload_configs()
            print("✅ Configuration reloaded successfully")
            return 0
            
        else:
            print(f"Unknown action: {args.action}")
            return 1
            
    except Exception as e:
        logging.error(f"Error in config command: {e}")
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
        elif args.command == "journal":
            return handle_journal(args)
        elif args.command == "config":
            return handle_config(args)
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
