# Notion Integration

Complete guide to integrating MarketMan with Notion databases for signal tracking, trade journaling, and performance analytics.

## 📋 Table of Contents

- [Overview](#overview)
- [Setup](#setup)
- [Database Structure](#database-structure)
- [Configuration](#configuration)
- [Usage](#usage)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

MarketMan integrates with Notion to automatically sync:
- **Trading Signals** - AI-generated signals with analysis
- **Trade Journal** - Entry/exit data and P&L tracking
- **Performance Analytics** - Metrics and performance reports
- **News Items** - Relevant news with sentiment analysis

### Benefits
- **Centralized Tracking** - All trading data in one place
- **Rich Formatting** - Notion's rich text and database features
- **Collaboration** - Share insights with team members
- **Customization** - Flexible database structure
- **Mobile Access** - Access data from anywhere

## 🚀 Setup

### Prerequisites

1. **Notion Account** - Free or paid account
2. **Integration Token** - Create a Notion integration
3. **Database IDs** - Create or identify target databases

### Step 1: Create Notion Integration

1. Go to [Notion Integrations](https://www.notion.so/my-integrations)
2. Click "New integration"
3. Fill in details:
   - **Name**: MarketMan Trading Bot
   - **Description**: Automated trading signal and performance tracking
   - **Workspace**: Select your workspace
4. Click "Submit"
5. Copy the **Internal Integration Token**

### Step 2: Create Databases

#### Signals Database

1. Create a new page in Notion
2. Add a database with these properties:

| Property Name | Type | Description |
|---------------|------|-------------|
| Signal Type | Select | Bullish, Bearish, Neutral |
| Confidence | Number | 1-10 confidence score |
| Title | Title | Signal title |
| Reasoning | Text | Signal reasoning |
| ETFs | Multi-select | Affected ETFs |
| Sector | Select | Market sector |
| Source | Text | News source |
| Timestamp | Date | Signal timestamp |
| Status | Select | Active, Closed, Expired |

#### Trades Database

1. Create another database with these properties:

| Property Name | Type | Description |
|---------------|------|-------------|
| Symbol | Title | Trading symbol |
| Signal ID | Text | Associated signal |
| Entry Price | Number | Entry price |
| Exit Price | Number | Exit price |
| Quantity | Number | Number of shares |
| Entry Date | Date | Entry timestamp |
| Exit Date | Date | Exit timestamp |
| P&L | Number | Realized P&L |
| Status | Select | Open, Closed |
| Notes | Text | Trade notes |

#### Performance Database

1. Create a performance tracking database:

| Property Name | Type | Description |
|---------------|------|-------------|
| Date | Date | Performance date |
| Total Trades | Number | Number of trades |
| Win Rate | Number | Win rate percentage |
| Total P&L | Number | Total P&L |
| Max Drawdown | Number | Maximum drawdown |
| Sharpe Ratio | Number | Sharpe ratio |
| Notes | Text | Performance notes |

### Step 3: Get Database IDs

1. Open each database in Notion
2. Copy the URL
3. Extract the database ID (32-character string after the last `/`)

Example URL: `https://notion.so/workspace/1234567890abcdef1234567890abcdef`
Database ID: `1234567890abcdef1234567890abcdef`

### Step 4: Configure MarketMan

Add to your `.env` file:

```bash
# Notion Integration
NOTION_TOKEN=secret_your_integration_token_here
NOTION_DATABASE_ID=your_signals_database_id
TRADES_DATABASE_ID=your_trades_database_id
SIGNALS_DATABASE_ID=your_signals_database_id
PERFORMANCE_DATABASE_ID=your_performance_database_id
```

## 🗄️ Database Structure

### Signals Database Schema

```json
{
  "parent": {
    "database_id": "your_signals_database_id"
  },
  "properties": {
    "Signal Type": {
      "select": {
        "name": "Bullish"
      }
    },
    "Confidence": {
      "number": 8
    },
    "Title": {
      "title": [
        {
          "text": {
            "content": "Tesla Reports Strong Q4 Earnings"
          }
        }
      ]
    },
    "Reasoning": {
      "rich_text": [
        {
          "text": {
            "content": "Tesla exceeded analyst expectations with strong revenue growth..."
          }
        }
      ]
    },
    "ETFs": {
      "multi_select": [
        {"name": "TSLA"},
        {"name": "LIT"},
        {"name": "DRIV"}
      ]
    },
    "Sector": {
      "select": {
        "name": "Electric Vehicles"
      }
    },
    "Source": {
      "rich_text": [
        {
          "text": {
            "content": "Reuters"
          }
        }
      ]
    },
    "Timestamp": {
      "date": {
        "start": "2024-01-01T10:00:00.000Z"
      }
    },
    "Status": {
      "select": {
        "name": "Active"
      }
    }
  }
}
```

### Trades Database Schema

```json
{
  "parent": {
    "database_id": "your_trades_database_id"
  },
  "properties": {
    "Symbol": {
      "title": [
        {
          "text": {
            "content": "TSLA"
          }
        }
      ]
    },
    "Signal ID": {
      "rich_text": [
        {
          "text": {
            "content": "signal_123"
          }
        }
      ]
    },
    "Entry Price": {
      "number": 250.50
    },
    "Exit Price": {
      "number": 255.75
    },
    "Quantity": {
      "number": 100
    },
    "Entry Date": {
      "date": {
        "start": "2024-01-01T10:30:00.000Z"
      }
    },
    "Exit Date": {
      "date": {
        "start": "2024-01-01T15:45:00.000Z"
      }
    },
    "P&L": {
      "number": 525.00
    },
    "Status": {
      "select": {
        "name": "Closed"
      }
    },
    "Notes": {
      "rich_text": [
        {
          "text": {
            "content": "Strong earnings beat drove price higher"
          }
        }
      ]
    }
  }
}
```

## ⚙️ Configuration

### Environment Variables

```bash
# Required
NOTION_TOKEN=secret_your_integration_token_here
NOTION_DATABASE_ID=your_main_database_id

# Optional (for separate databases)
TRADES_DATABASE_ID=your_trades_database_id
SIGNALS_DATABASE_ID=your_signals_database_id
PERFORMANCE_DATABASE_ID=your_performance_database_id
```

### Configuration File

Add to `config/settings.yaml`:

```yaml
integrations:
  notion:
    enabled: true
    token: ${NOTION_TOKEN}
    databases:
      signals: ${SIGNALS_DATABASE_ID}
      trades: ${TRADES_DATABASE_ID}
      performance: ${PERFORMANCE_DATABASE_ID}
    
    # Sync settings
    sync_signals: true
    sync_trades: true
    sync_performance: true
    
    # Formatting options
    include_rich_text: true
    include_links: true
    include_emoji: true
    
    # Rate limiting
    max_requests_per_minute: 3
    retry_attempts: 3
    retry_delay: 5
```

## 🚀 Usage

### Manual Sync

```bash
# Sync all data
python marketman notion sync

# Sync specific data types
python marketman notion sync --signals
python marketman notion sync --trades
python marketman notion sync --performance

# Force sync (ignore timestamps)
python marketman notion sync --force
```

### Automatic Sync

MarketMan automatically syncs data when:

- New signals are generated
- Trades are opened/closed
- Performance metrics are updated

### CLI Commands

```bash
# Test connection
python marketman notion test

# Show sync status
python marketman notion status

# View recent entries
python marketman notion recent --limit 10

# Search entries
python marketman notion search --query "TSLA"

# Export data
python marketman notion export --format csv
```

### Programmatic Usage

```python
from src.integrations.notion import NotionReporter

# Initialize reporter
reporter = NotionReporter(
    token="your_token",
    database_id="your_database_id"
)

# Add signal
signal_id = reporter.add_signal({
    "signal_type": "bullish",
    "confidence": 8,
    "title": "Tesla Reports Strong Earnings",
    "reasoning": "Exceeded analyst expectations...",
    "etfs": ["TSLA", "LIT", "DRIV"],
    "sector": "Electric Vehicles"
})

# Add trade
trade_id = reporter.add_trade({
    "symbol": "TSLA",
    "signal_id": signal_id,
    "entry_price": 250.50,
    "quantity": 100,
    "entry_timestamp": "2024-01-01T10:30:00Z"
})

# Update performance
reporter.update_performance({
    "date": "2024-01-01",
    "total_trades": 15,
    "win_rate": 0.73,
    "total_pnl": 1250.00
})
```

## 📊 Data Formatting

### Rich Text Formatting

MarketMan supports Notion's rich text formatting:

```python
# Bold text
{"text": {"content": "Important signal"}, "annotations": {"bold": True}}

# Colored text
{"text": {"content": "High confidence"}, "annotations": {"color": "green"}}

# Links
{"text": {"content": "Source article", "link": {"url": "https://example.com"}}}
```

### Emoji Support

```python
# Signal types with emojis
signal_emojis = {
    "bullish": "📈",
    "bearish": "📉", 
    "neutral": "➡️"
}

# Confidence levels
confidence_emojis = {
    10: "🔥",
    9: "⚡",
    8: "💪",
    7: "👍",
    6: "👌",
    5: "🤔",
    4: "😐",
    3: "😕",
    2: "😟",
    1: "😱"
}
```

### Database Views

Create different views in Notion for better organization:

1. **Signals by Confidence** - Group by confidence level
2. **Signals by Sector** - Group by market sector
3. **Recent Trades** - Sort by entry date
4. **Performance Timeline** - Calendar view
5. **P&L Summary** - Gallery view with charts

## 🔧 Troubleshooting

### Common Issues

#### "Invalid token"

**Solution**:
```bash
# Check token format
echo $NOTION_TOKEN | head -c 20

# Should start with: secret_

# Regenerate token at:
# https://notion.so/my-integrations
```

#### "Database not found"

**Solution**:
```bash
# Verify database ID
python marketman notion test

# Check database permissions
# Ensure integration has access to database
```

#### "Rate limit exceeded"

**Solution**:
```yaml
# Reduce sync frequency in config/settings.yaml:
integrations:
  notion:
    max_requests_per_minute: 1  # Reduce from 3
    retry_delay: 10  # Increase from 5
```

#### "Sync failed"

**Solution**:
```bash
# Check logs
tail -f logs/marketman.log

# Test connection
python marketman notion test

# Manual sync with debug
DEBUG=true python marketman notion sync --debug
```

### Debug Mode

```bash
# Enable debug logging
export DEBUG=true

# Run with debug output
python marketman notion sync --debug

# Check Notion API logs
grep -i notion logs/marketman.log
```

### Testing Integration

```bash
# Test connection
python marketman notion test

# Test database access
python marketman notion test --database signals

# Test data creation
python marketman notion test --create-sample
```

## 📈 Advanced Features

### Custom Properties

Add custom properties to your databases:

```python
# Custom signal properties
custom_properties = {
    "Market Cap": {"number": 1000000000},
    "Volume": {"number": 5000000},
    "Analyst Rating": {"select": {"name": "Buy"}},
    "Risk Level": {"select": {"name": "Medium"}}
}
```

### Filtering and Sorting

```python
# Filter signals by confidence
filter_params = {
    "filter": {
        "property": "Confidence",
        "number": {
            "greater_than_or_equal_to": 7
        }
    }
}

# Sort by timestamp
sort_params = {
    "sorts": [
        {
            "property": "Timestamp",
            "direction": "descending"
        }
    ]
}
```

### Batch Operations

```python
# Batch create multiple entries
entries = [
    {"title": "Signal 1", "confidence": 8},
    {"title": "Signal 2", "confidence": 7},
    {"title": "Signal 3", "confidence": 9}
]

reporter.batch_create(entries)
```

### Webhooks (Future Feature)

```python
# Subscribe to database changes
webhook_url = "https://your-server.com/notion-webhook"
reporter.create_webhook(webhook_url)
```

## 🔗 Related Documentation

- **[User Guide](../user-guide.md)** - Complete usage instructions
- **[Configuration Guide](../configuration.md)** - Setup and configuration
- **[API Reference](../api-reference.md)** - Technical API documentation
- **[Troubleshooting](../troubleshooting.md)** - Common issues and solutions

---

**Need help?** Check the [Troubleshooting Guide](../troubleshooting.md) or create an issue on GitHub. 