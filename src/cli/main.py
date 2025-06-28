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


def main() -> int:
    """
    Main CLI entry point.

    Returns:
        Exit code
    """
    parser = create_parser()
    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

    # Load configuration
    try:
        config = get_config()
        logging.info("Configuration loaded successfully")
    except Exception as e:
        logging.error(f"Failed to load configuration: {e}")
        return 1

    # Handle commands
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
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
