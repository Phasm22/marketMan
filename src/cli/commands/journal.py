#!/usr/bin/env python3
"""
Journal and Performance CLI Commands
CLI commands for trade journaling, performance tracking, and signal logging.
"""
import click
import json
from datetime import datetime, timedelta
from typing import Optional

from ...core.journal.trade_journal import create_trade_journal, TradeEntry
from ...core.journal.performance_tracker import create_performance_tracker, generate_performance_report
from ...core.journal.signal_logger import create_signal_logger, generate_signal_report
from ...integrations.fidelity_integration import create_fidelity_integration, auto_import_fidelity_trades


@click.group()
def journal():
    """Trade journaling and performance tracking commands"""
    pass


@journal.command()
@click.option('--symbol', '-s', help='Symbol to filter trades')
@click.option('--days', '-d', default=30, help='Number of days to look back')
@click.option('--output', '-o', help='Output file for CSV export')
def list_trades(symbol: Optional[str], days: int, output: Optional[str]):
    """List trades from the journal"""
    journal = create_trade_journal()
    
    start_date = (datetime.now() - timedelta(days=days)).isoformat()
    trades = journal.get_trades(symbol=symbol, start_date=start_date)
    
    if not trades:
        click.echo("No trades found for the specified criteria.")
        return
    
    click.echo(f"Found {len(trades)} trades:")
    click.echo("-" * 80)
    
    for trade in trades[:20]:  # Show first 20 trades
        click.echo(f"{trade['timestamp']} | {trade['symbol']} | {trade['action']} | "
                  f"{trade['quantity']} @ ${trade['price']:.2f} | ${trade['trade_value']:.2f}")
    
    if len(trades) > 20:
        click.echo(f"... and {len(trades) - 20} more trades")
    
    if output:
        if journal.export_trades_to_csv(output, symbol, start_date):
            click.echo(f"Trades exported to {output}")
        else:
            click.echo("Failed to export trades")


@journal.command()
@click.option('--days', '-d', default=30, help='Number of days for performance calculation')
@click.option('--output', '-o', help='Output file for JSON report')
def performance(days: int, output: Optional[str]):
    """Generate performance report"""
    click.echo(f"Generating performance report for last {days} days...")
    
    report = generate_performance_report(days)
    
    # Display summary
    click.echo("\n📊 PERFORMANCE SUMMARY")
    click.echo("=" * 50)
    click.echo(f"Total Trades: {report['metrics']['total_trades']}")
    click.echo(f"Winning Trades: {report['metrics']['winning_trades']}")
    click.echo(f"Losing Trades: {report['metrics']['losing_trades']}")
    click.echo(f"Total P&L: ${report['metrics']['total_pnl']:,.2f}")
    click.echo(f"Win Rate: {report['metrics']['win_rate']}")
    click.echo(f"Profit Factor: {report['metrics']['profit_factor']:.2f}")
    click.echo(f"Max Drawdown: ${report['metrics']['max_drawdown']:,.2f}")
    click.echo(f"Sharpe Ratio: {report['metrics']['sharpe_ratio']:.2f}")
    click.echo(f"Signal Accuracy: {report['metrics']['signal_accuracy']}")
    
    # Display sector performance
    if report['sector_performance']:
        click.echo("\n📈 SECTOR PERFORMANCE")
        click.echo("-" * 30)
        for sector, pnl in report['sector_performance'].items():
            click.echo(f"{sector}: ${pnl:,.2f}")
    
    # Display risk metrics
    click.echo("\n⚠️ RISK METRICS")
    click.echo("-" * 20)
    click.echo(f"Max Consecutive Wins: {report['risk_metrics']['max_consecutive_wins']}")
    click.echo(f"Max Consecutive Losses: {report['risk_metrics']['max_consecutive_losses']}")
    click.echo(f"Avg Holding Period: {report['risk_metrics']['avg_holding_period']}")
    
    if output:
        with open(output, 'w') as f:
            json.dump(report, f, indent=2)
        click.echo(f"\nReport saved to {output}")


@journal.command()
@click.option('--days', '-d', default=30, help='Number of days for signal analysis')
@click.option('--output', '-o', help='Output file for JSON report')
def signals(days: int, output: Optional[str]):
    """Generate signal analysis report"""
    click.echo(f"Generating signal report for last {days} days...")
    
    report = generate_signal_report(days)
    
    # Display summary
    click.echo("\n📊 SIGNAL ANALYSIS")
    click.echo("=" * 40)
    click.echo(f"Total Signals: {report['summary']['total_signals']}")
    click.echo(f"Executed Signals: {report['summary']['executed_signals']}")
    click.echo(f"Signal Accuracy: {report['summary']['signal_accuracy']}")
    click.echo(f"Avg Confidence: {report['summary']['avg_confidence']:.2f}")
    
    # Display performance by type
    if report['performance_by_type']:
        click.echo("\n📈 PERFORMANCE BY SIGNAL TYPE")
        click.echo("-" * 35)
        for signal_type, perf in report['performance_by_type'].items():
            click.echo(f"{signal_type}: {perf['accuracy']}% accuracy "
                      f"({perf['executed']}/{perf['total']} executed)")
    
    # Display performance by direction
    if report['performance_by_direction']:
        click.echo("\n📊 PERFORMANCE BY DIRECTION")
        click.echo("-" * 30)
        for direction, perf in report['performance_by_direction'].items():
            click.echo(f"{direction}: {perf['accuracy']}% accuracy "
                      f"({perf['executed']}/{perf['total']} executed)")
    
    # Display recent signals
    if report['recent_signals']:
        click.echo("\n🕒 RECENT SIGNALS")
        click.echo("-" * 20)
        for signal in report['recent_signals'][:5]:
            click.echo(f"{signal['timestamp'][:10]} | {signal['symbol']} | "
                      f"{signal['signal_type']} | {signal['direction']} | "
                      f"Confidence: {signal['confidence']}")
    
    if output:
        with open(output, 'w') as f:
            json.dump(report, f, indent=2)
        click.echo(f"\nReport saved to {output}")


@journal.command()
@click.option('--email', '-e', help='Email address for Fidelity monitoring')
@click.option('--password', '-p', help='Email password (use environment variable FIDELITY_EMAIL_PASSWORD)')
def setup_fidelity(email: Optional[str], password: Optional[str]):
    """Setup Fidelity email monitoring"""
    if not email:
        email = click.prompt("Enter Fidelity email address")
    
    if not password:
        password = click.prompt("Enter email password", hide_input=True)
    
    integration = create_fidelity_integration()
    
    if integration.setup_email_monitoring(email, password):
        click.echo("✅ Fidelity email monitoring configured successfully!")
        click.echo(f"📧 Monitoring: {email}")
        click.echo("📁 Email folder: data/fidelity_emails")
        click.echo("📁 CSV folder: data/fidelity_csv")
        click.echo("📁 Processed folder: data/processed")
    else:
        click.echo("❌ Failed to setup Fidelity email monitoring")


@journal.command()
def import_fidelity():
    """Import Fidelity trades from emails and CSV files"""
    click.echo("Importing Fidelity trades...")
    
    results = auto_import_fidelity_trades()
    
    click.echo(f"\n📊 IMPORT RESULTS")
    click.echo("=" * 30)
    click.echo(f"Email trades found: {results['email_trades']}")
    click.echo(f"CSV trades found: {results['csv_trades']}")
    click.echo(f"Trades imported: {results['imported_trades']}")
    
    if results['errors']:
        click.echo(f"\n❌ ERRORS:")
        for error in results['errors']:
            click.echo(f"  - {error}")
    
    if results['imported_trades'] > 0:
        click.echo(f"\n✅ Successfully imported {results['imported_trades']} trades!")
    else:
        click.echo("\nℹ️ No new trades to import")


@journal.command()
@click.option('--symbol', '-s', required=True, help='Symbol to add trade for')
@click.option('--action', '-a', required=True, type=click.Choice(['Buy', 'Sell']), help='Trade action')
@click.option('--quantity', '-q', required=True, type=float, help='Quantity')
@click.option('--price', '-p', required=True, type=float, help='Price per share')
@click.option('--date', '-d', help='Trade date (YYYY-MM-DD, defaults to today)')
@click.option('--confidence', '-c', type=float, help='Signal confidence (1-10)')
@click.option('--notes', '-n', help='Trade notes')
def add_trade(symbol: str, action: str, quantity: float, price: float, 
              date: Optional[str], confidence: Optional[float], notes: Optional[str]):
    """Add a manual trade entry"""
    if not date:
        date = datetime.now().date().isoformat()
    
    trade_value = quantity * price
    
    trade = TradeEntry(
        timestamp=date,
        symbol=symbol.upper(),
        action=action,
        quantity=quantity,
        price=price,
        trade_value=trade_value,
        signal_confidence=confidence,
        notes=notes,
        broker="Manual Entry"
    )
    
    journal = create_trade_journal()
    if journal.log_trade(trade):
        click.echo(f"✅ Trade added: {symbol} {action} {quantity} @ ${price:.2f}")
    else:
        click.echo("❌ Failed to add trade")


@journal.command()
@click.option('--symbol', '-s', required=True, help='Symbol for signal')
@click.option('--type', '-t', required=True, type=click.Choice(['news', 'technical', 'pattern']), help='Signal type')
@click.option('--direction', '-d', required=True, type=click.Choice(['bullish', 'bearish', 'neutral']), help='Signal direction')
@click.option('--confidence', '-c', required=True, type=click.FloatRange(1, 10), help='Confidence (1-10)')
@click.option('--reasoning', '-r', required=True, help='Signal reasoning')
@click.option('--source', help='Signal source')
def add_signal(symbol: str, type: str, direction: str, confidence: float, reasoning: str, source: Optional[str]):
    """Add a manual signal entry"""
    signal_logger = create_signal_logger()
    
    if type == 'news':
        success = signal_logger.log_news_signal(symbol, direction, confidence, reasoning, source or 'manual')
    elif type == 'technical':
        success = signal_logger.log_technical_signal(symbol, direction, confidence, reasoning, {})
    elif type == 'pattern':
        success = signal_logger.log_pattern_signal(symbol, direction, confidence, reasoning, 'manual')
    else:
        click.echo("❌ Invalid signal type")
        return
    
    if success:
        click.echo(f"✅ Signal added: {symbol} {direction} {confidence}/10")
    else:
        click.echo("❌ Failed to add signal")


@journal.command()
@click.option('--days', '-d', default=30, help='Number of days to sync')
def sync_notion(days: int):
    """Sync trades from Notion to local journal"""
    click.echo(f"Syncing trades from Notion for last {days} days...")
    
    tracker = create_performance_tracker()
    
    if tracker.sync_trades_from_notion():
        click.echo("✅ Successfully synced trades from Notion")
    else:
        click.echo("❌ Failed to sync trades from Notion")


@journal.command()
@click.option('--days', '-d', default=30, help='Number of days for analysis')
def analyze(days: int):
    """Run comprehensive analysis (performance + signals)"""
    click.echo(f"Running comprehensive analysis for last {days} days...")
    
    # Performance analysis
    click.echo("\n📊 PERFORMANCE ANALYSIS")
    click.echo("=" * 30)
    perf_report = generate_performance_report(days)
    click.echo(f"Total P&L: ${perf_report['metrics']['total_pnl']:,.2f}")
    click.echo(f"Win Rate: {perf_report['metrics']['win_rate']}")
    click.echo(f"Signal Accuracy: {perf_report['metrics']['signal_accuracy']}")
    
    # Signal analysis
    click.echo("\n📈 SIGNAL ANALYSIS")
    click.echo("=" * 20)
    signal_report = generate_signal_report(days)
    click.echo(f"Total Signals: {signal_report['summary']['total_signals']}")
    click.echo(f"Signal Accuracy: {signal_report['summary']['signal_accuracy']}")
    
    # Recommendations
    click.echo("\n💡 RECOMMENDATIONS")
    click.echo("=" * 20)
    
    if perf_report['metrics']['win_rate'] < 50:
        click.echo("⚠️ Win rate below 50% - consider reviewing strategy")
    
    if perf_report['metrics']['signal_accuracy'] < 60:
        click.echo("⚠️ Signal accuracy below 60% - consider improving signal quality")
    
    if perf_report['metrics']['max_drawdown'] > 1000:
        click.echo("⚠️ High drawdown - consider risk management improvements")
    
    click.echo("✅ Analysis complete!")


if __name__ == '__main__':
    journal() 