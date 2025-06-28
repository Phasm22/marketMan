"""
Main CLI entry point for MarketMan.

This module provides the command-line interface for all MarketMan operations.
"""

import argparse
import sys
import logging
from typing import Optional

from src.core.utils import get_config


def setup_logging(verbose: bool = False) -> None:
    """
    Setup logging configuration.
    
    Args:
        verbose: Enable verbose logging if True
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/marketman_cli.log')
        ]
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
        """
    )
    
    # Global options
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--config',
        default='config/settings.yaml',
        help='Path to configuration file'
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(
        dest='command',
        help='Available commands'
    )
    
    # Signals command
    signals_parser = subparsers.add_parser(
        'signals',
        help='Signal processing commands'
    )
    signals_parser.add_argument(
        'action',
        choices=['run', 'status', 'backtest'],
        help='Signal action to perform'
    )
    
    # Alerts command
    alerts_parser = subparsers.add_parser(
        'alerts',
        help='Alert management commands'
    )
    alerts_parser.add_argument(
        'action',
        choices=['check', 'send', 'status'],
        help='Alert action to perform'
    )
    
    # Performance command
    performance_parser = subparsers.add_parser(
        'performance',
        help='Performance monitoring commands'
    )
    performance_parser.add_argument(
        'action',
        choices=['show', 'update', 'export'],
        help='Performance action to perform'
    )
    
    # Options command
    options_parser = subparsers.add_parser(
        'options',
        help='Options trading commands'
    )
    options_parser.add_argument(
        'action',
        choices=['scalp', 'analyze', 'backtest'],
        help='Options action to perform'
    )
    
    # Risk command
    risk_parser = subparsers.add_parser(
        'risk',
        help='Risk management commands'
    )
    risk_parser.add_argument(
        'action',
        choices=['analyze', 'limits', 'position-size'],
        help='Risk action to perform'
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
        if args.action == 'run':
            print("Running signal processing...")
            # TODO: Implement signal processing
            return 0
        elif args.action == 'status':
            print("Checking signal status...")
            # TODO: Implement status check
            return 0
        elif args.action == 'backtest':
            print("Running signal backtest...")
            # TODO: Implement backtest
            return 0
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
        if args.action == 'check':
            print("Checking for new alerts...")
            # TODO: Implement alert checking
            return 0
        elif args.action == 'send':
            print("Sending alerts...")
            # TODO: Implement alert sending
            return 0
        elif args.action == 'status':
            print("Checking alert status...")
            # TODO: Implement status check
            return 0
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
        if args.action == 'show':
            print("Showing performance dashboard...")
            # TODO: Implement performance display
            return 0
        elif args.action == 'update':
            print("Updating performance data...")
            # TODO: Implement performance update
            return 0
        elif args.action == 'export':
            print("Exporting performance data...")
            # TODO: Implement export
            return 0
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
        if args.action == 'scalp':
            print("Running options scalping strategy...")
            # TODO: Implement options scalping
            return 0
        elif args.action == 'analyze':
            print("Analyzing options data...")
            # TODO: Implement options analysis
            return 0
        elif args.action == 'backtest':
            print("Running options backtest...")
            # TODO: Implement options backtest
            return 0
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
        if args.action == 'analyze':
            print("Analyzing portfolio risk...")
            # TODO: Implement risk analysis
            return 0
        elif args.action == 'limits':
            print("Checking risk limits...")
            # TODO: Implement limits check
            return 0
        elif args.action == 'position-size':
            print("Calculating position sizes...")
            # TODO: Implement position sizing
            return 0
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
    if args.command == 'signals':
        return handle_signals(args)
    elif args.command == 'alerts':
        return handle_alerts(args)
    elif args.command == 'performance':
        return handle_performance(args)
    elif args.command == 'options':
        return handle_options(args)
    elif args.command == 'risk':
        return handle_risk(args)
    else:
        parser.print_help()
        return 0


if __name__ == '__main__':
    sys.exit(main()) 