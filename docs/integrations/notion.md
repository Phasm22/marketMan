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
- **Trading Signals** - AI-generated signals with actionable analysis
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

#### Signals Database (v3 Schema)

1. Create a new page in Notion
2. Add a database with these properties:

| Property Name | Type | Description |
|---------------|------|-------------|
| Title | Title | Signal title |
| Signal | Select | Bullish, Bearish, Neutral |
| Confidence | Number | 1-10 confidence score |
| ETFs | Multi-select | Affected ETF tickers |
| Sector | Select | Market sector |
| Timestamp | Date | Signal timestamp |
| Reasoning | Text | Signal reasoning (bullet-pointed) |
| Status | Select | New, Reviewed, Acted On, Archived |
| Journal Notes | Text | Optional manual notes |
| If-Then Scenario | Text | Validation logic for signal |
| Contradictory Signals | Text | Opposing signals/risks |
| Uncertainty Metric | Text | Confidence with context |
| Position Risk Bracket | Text | Position sizing guidance |
| Price Anchors | Text | ETF price context |

#### Trades Database

1. Create another database with these properties:

| Property Name | Type | Description |
|---------------|------|-------------|
| Ticker | Title | Trading symbol |
| Action | Select | BUY, SELL |
| Quantity | Number | Number of shares |
| Price | Number | Trade price |
| Trade Date | Date | Trade timestamp |
| Trade Value | Number | Total trade value |
| Notes | Text | Trade notes |
| Status | Select | Open, Closed, Review |

#### Performance Database

1. Create a performance tracking database:

| Property Name | Type | Description |
|---------------|------|-------------|
| Period | Title | Performance period |
| Total Trades | Number | Number of trades |
| Win Rate | Number | Win rate percentage |
| Total P&L | Number | Total P&L |
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
SIGNALS_DATABASE_ID=your_signals_database_id
TRADES_DATABASE_ID=your_trades_database_id
PERFORMANCE_DATABASE_ID=your_performance_database_id
```

## 🗄️ Database Structure

### Signals Database Schema (v3)

```json
{
  "parent": {
    "database_id": "your_signals_database_id"
  },
  "properties": {
    "Title": {
      "title": [
        {
          "text": {
            "content": "Tesla Reports Strong Q4 Earnings"
          }
        }
      ]
    },
    "Signal": {
      "select": {
        "name": "Bullish"
      }
    },
    "Confidence": {
      "number": 8
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
    "Timestamp": {
      "date": {
        "start": "2024-01-01T10:00:00.000Z"
      }
    },
    "Reasoning": {
      "rich_text": [
        {
          "text": {
            "content": "• Tesla exceeded analyst expectations with strong revenue growth\n• Institutional volume in TSLA > 2x average\n• Reuters, Bloomberg coverage aligns"
          }
        }
      ]
    },
    "Status": {
      "select": {
        "name": "New"
      }
    },
    "If-Then Scenario": {
      "rich_text": [
        {
          "text": {
            "content": "If TSLA volume > 2x 5-day average this week, confirm bullish thesis; if negative headlines increase, reduce exposure."
          }
        }
      ]
    },
    "Contradictory Signals": {
      "rich_text": [
        {
          "text": {
            "content": "Supply chain issues or regulatory changes could reverse momentum."
          }
        }
      ]
    },
    "Uncertainty Metric": {
      "rich_text": [
        {
          "text": {
            "content": "Confidence 8, but headline-driven and source agreement only moderate."
          }
        }
      ]
    },
    "Position Risk Bracket": {
      "rich_text": [
        {
          "text": {
            "content": "Position sizing: conservative (high volatility, sector headline risk)"
          }
        }
      ]
    },
    "Price Anchors": {
      "rich_text": [
        {
          "text": {
            "content": "TSLA: $250.50 → $255.75 (+2.1%) | 2.1M (1.8x avg)\nLIT: $95.30 → $95.80 (+1.7%) | 1.2M (1.5x avg)"
          }
        }
      ]
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
    "Ticker": {
      "title": [
        {
          "text": {
            "content": "TSLA"
          }
        }
      ]
    },
    "Action": {
      "select": {
        "name": "BUY"
      }
    },
    "Quantity": {
      "number": 100
    },
    "Price": {
      "number": 250.50
    },
    "Trade Date": {
      "date": {
        "start": "2024-01-01T10:30:00.000Z"
      }
    },
    "Trade Value": {
      "number": 25050.00
    },
    "Status": {
      "select": {
        "name": "Open"
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
SIGNALS_DATABASE_ID=your_signals_database_id

# Optional (for separate databases)
TRADES_DATABASE_ID=your_trades_database_id
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
python marketman notion sync --signals-only
python marketman notion sync --trades-only
python marketman notion sync --performance-only
```

### Signal Fields

The v3 signal schema includes these actionable fields:

- **If-Then Scenario**: Validation logic for confirming or refuting signals
- **Contradictory Signals**: Risks and opposing factors to monitor
- **Uncertainty Metric**: Confidence level with context and caveats
- **Position Risk Bracket**: Position sizing guidance based on volatility
- **Price Anchors**: Real-time ETF price context and trends

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
properties["Custom Field"] = {"rich_text": [{"text": {"content": "value"}}]}
```

### Signal Filtering

Filter signals by various criteria:

```python
# Filter by confidence
high_confidence_signals = [s for s in signals if s["confidence"] >= 8]

# Filter by sector
defense_signals = [s for s in signals if s["sector"] == "Defense"]

# Filter by status
new_signals = [s for s in signals if s["status"] == "New"]
```

### Performance Tracking

Track signal performance over time:

```python
# Calculate signal accuracy
def calculate_accuracy(signals):
    correct = sum(1 for s in signals if s["outcome"] == "correct")
    return correct / len(signals) if signals else 0

# Track by signal type
bullish_accuracy = calculate_accuracy([s for s in signals if s["signal"] == "Bullish"])
bearish_accuracy = calculate_accuracy([s for s in signals if s["signal"] == "Bearish"])
```

## 🔗 Related Documentation

- **[User Guide](../user-guide.md)** - Complete usage instructions
- **[Configuration Guide](../configuration.md)** - Setup and configuration
- **[API Reference](../api-reference.md)** - Technical API documentation
- **[Troubleshooting](../troubleshooting.md)** - Common issues and solutions

---

**Need help?** Check the [Troubleshooting Guide](../troubleshooting.md) or create an issue on GitHub. 