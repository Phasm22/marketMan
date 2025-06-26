# Performance Dashboard Integration

## Overview

The MarketMan system now includes performance dashboard support for tracking trade executions and portfolio performance. This feature allows you to automatically log executed trades to dedicated Notion databases for analysis and tracking.

## Setup

### 1. Environment Variables

Add the following variables to your `.env` file:

```bash
# Performance Dashboard Configuration
TRADES_DATABASE_ID=your-trades-database-id
PERFORMANCE_DATABASE_ID=your-performance-database-id
```

### 2. Notion Database Schema

Create two Notion databases with the following schemas:

#### Trades Database Schema

The `TRADES_DATABASE_ID` should point to a Notion database with these properties:

- **Ticker** (Title) - ETF ticker symbol
- **Action** (Select) - Options: "BUY", "SELL"  
- **Quantity** (Number) - Number of shares
- **Price** (Number) - Execution price per share
- **Trade Value** (Number) - Total trade value (auto-calculated)
- **Trade Date** (Date) - Date/time of trade execution
- **Signal Confidence** (Number) - Original signal confidence score (optional)
- **Signal Reference** (Relation) - Link to original signal page (optional)
- **Notes** (Rich Text) - Additional notes about the trade

#### Performance Database Schema

The `PERFORMANCE_DATABASE_ID` can be used for aggregate performance tracking (schema TBD based on requirements).

## Usage

### Automatic Trade Reporting

The `NotionReporter.report_trade()` method can be called to log trades:

```python
from src.core.notion_reporter import NotionReporter

reporter = NotionReporter()

trade = {
    'ticker': 'BOTZ',
    'action': 'BUY',
    'quantity': 100,
    'price': 25.50,
    'timestamp': datetime.now(),
    'signal_confidence': 8.5,
    'notes': 'Strong AI sector momentum'
}

success = reporter.report_trade(trade, signal_page_id="optional-notion-page-id")
```

### Integration Points

To enable automatic trade reporting when signals are acted upon:

1. **Manual Integration**: Call `report_trade()` when you execute trades based on MarketMan signals
2. **Automated Integration**: Extend the system to automatically detect "Acted On" status changes in Notion and trigger trade reporting

## Testing

Run the performance dashboard test to verify configuration:

```bash
python test_performance_dashboard.py
```

## Validation

The system includes built-in validation:

- Checks for required environment variables on initialization
- Logs warnings if performance dashboard features are not configured
- Gracefully handles missing database IDs without breaking existing functionality
- Validates trade data before attempting to log to Notion

## Future Enhancements

- Automatic portfolio performance calculations
- P&L tracking and reporting
- Integration with brokerage APIs for automatic trade detection
- Performance analytics and visualizations in Notion
