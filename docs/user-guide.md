# MarketMan User Guide

## Table of Contents

- [Getting Started](#getting-started)
- [Core Concepts](#core-concepts)
- [Daily Operations](#daily-operations)
- [Configuration](#configuration)
- [Monitoring & Alerts](#monitoring--alerts)
- [Troubleshooting](#troubleshooting)

## Getting Started

### Prerequisites

Before using MarketMan, ensure you have:

- Python 3.9+ installed
- API Keys for required services:
   - OpenAI (for AI analysis)
   - Finnhub (for financial news)
   - NewsAPI (for general news)
   - NewData (for additional sources)
- Pushover account (optional, for notifications)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd marketMan
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment**:
   ```bash
   # Create settings.yaml file with your API keys
   cp config/settings.yaml.example config/settings.yaml
   # Edit config/settings.yaml with your API keys
   ```

4. **Validate configuration**:
   ```bash
   python marketman config validate
   ```

### First Run

1. **Test the system**:
   ```bash
   python marketman news status
   ```

2. **Run a news cycle**:
   ```bash
   python marketman news cycle
   ```

3. **Check for signals**:
   ```bash
   python marketman signals run
   ```

## 🧠 Core Concepts

### News Processing Pipeline

MarketMan processes news through several stages:

1. **Collection** - Gathers news from multiple sources (Finnhub, NewsAPI, NewData)
2. **Filtering** - Removes irrelevant content using keywords and relevance scoring
3. **Batching** - Groups related news for efficient processing

   The system uses a hybrid batching approach:
   - Batches are finalized and processed immediately if they reach the maximum batch size.
   - Batches are also finalized if they have at least the minimum batch size and have been waiting longer than the configured max wait time.
   - At the end of each news cycle, any remaining pending batches that meet the minimum batch size are finalized and processed, ensuring no news is left unprocessed. This guarantees all accepted news is processed promptly.
4. **AI Analysis** - Uses GPT-4 to analyze sentiment and generate signals
5. **Validation** - Cross-references signals across sources
6. **Output** - Generates actionable trading signals

### Signal Types

- **Bullish** - Positive sentiment, expected price increase
- **Bearish** - Negative sentiment, expected price decrease
- **Neutral** - Mixed or unclear sentiment

### Confidence Scoring

Signals are scored 1-10 based on:
- **Source reliability** (Reuters = 5, unknown = 1)
- **Sentiment strength** (how strongly positive/negative)
- **Market impact** (potential effect on prices)
- **Technical confirmation** (supporting technical indicators)

## 📅 Daily Operations

### Morning Routine

1. **Check system status**:
   ```bash
   python marketman news status
   ```

2. **Process overnight news**:
   ```bash
   python marketman news cycle
   ```

3. **Review generated signals**:
   ```bash
   python marketman signals run
   ```

4. **Check alerts**:
   ```bash
   python marketman alerts check
   ```

### Continuous Monitoring

- **Set up automated alerts** via Pushover
- **Monitor performance** with the journal commands
- **Review daily summaries** in Notion (if configured)

### End-of-Day Review

1. **Check performance**:
   ```bash
   python marketman journal performance
   ```

2. **Review trades**:
   ```bash
   python marketman journal list-trades
   ```

3. **Update configuration** if needed:
   ```bash
   python marketman config show
   ```

## ⚙️ Configuration

### Key Settings

#### Risk Management
```yaml
risk:
  max_daily_loss: 0.05          # 5% maximum daily loss
  max_position_size: 0.02       # 2% maximum position size
  stop_loss_percent: 2.0        # 2% stop loss
  max_kelly_fraction: 0.25      # 25% Kelly criterion limit
```

#### News Processing
```yaml
news_ingestion:
  max_daily_headlines: 50       # Maximum headlines per day
  max_daily_ai_calls: 75        # Maximum AI API calls
  min_relevance_score: 0.05     # Minimum relevance threshold
```

#### Alerts
```yaml
alerts:
  batch_strategy: smart_batch   # Alert batching strategy
  max_daily_alerts: 10          # Maximum alerts per day
  confidence_threshold: 7       # Minimum confidence for alerts
```

### Environment Variables

Required in `config/settings.yaml`:
```yaml
# OpenAI
openai:
  api_key: your_openai_key

# News APIs
finnhub:
  api_key: your_finnhub_key
newsapi:
  api_key: your_newsapi_key
newdata:
  api_key: your_newdata_key

# Notifications
pushover:
  token: your_pushover_token
  user_key: your_pushover_user

# Notion (optional)
notion:
  token: your_notion_token
  database_id: your_database_id
```

## 📱 Monitoring & Alerts

### Pushover Notifications

MarketMan sends notifications for:
- **High-confidence signals** (7+ confidence)
- **Risk warnings** (market volatility)
- **System alerts** (errors, warnings)

### System Monitoring

Monitor system health:
```bash
# Check system status
python marketman news status

# Run system monitoring
python src/monitoring/marketman_monitor.py

# Continuous monitoring
python src/monitoring/marketman_monitor.py --loop 30
```

## 🔧 Available Commands

### News Commands

```bash
# Check news system status
python marketman news status

# Run news processing cycle
python marketman news cycle

# Test news sources
python marketman news test

# Generate signals from news
python marketman news signals
```

### Signal Commands

```bash
# Run signal processing
python marketman signals run

# Check signal status
python marketman signals status

# Run signal backtest (not implemented)
python marketman signals backtest
```

### Alert Commands

```bash
# Check for new alerts
python marketman alerts check

# Send pending alerts
python marketman alerts send

# Check alert status
python marketman alerts status
```

### Performance Commands

```bash
# Show performance dashboard
python marketman performance show

# Update performance data
python marketman performance update

# Export performance data
python marketman performance export
```

### Options Commands

```bash
# Run options scalping
python marketman options scalp

# Analyze options
python marketman options analyze

# Run options backtest (not implemented)
python marketman options backtest
```

### Risk Commands

```bash
# Analyze portfolio risk
python marketman risk analyze

# Check risk limits
python marketman risk limits

# Calculate position size
python marketman risk position-size
```

### Journal Commands

```bash
# List trades
python marketman journal list-trades

# Show performance
python marketman journal performance

# Show signal analysis
python marketman journal signals

# Setup Fidelity integration
python marketman journal setup-fidelity

# Import Fidelity trades
python marketman journal import-fidelity

# Add manual trade
python marketman journal add-trade

# Add manual signal
python marketman journal add-signal

# Sync with Notion
python marketman journal sync-notion

# Analyze performance
python marketman journal analyze
```

### Configuration Commands

```bash
# Validate configuration
python marketman config validate

# Show configuration
python marketman config show

# Reload configuration
python marketman config reload
```

## 🗄️ Database Management

### Database Location

MarketMan uses SQLite databases stored in the `data/` directory:
- `data/marketman.db` - Main database
- `data/marketman_memory.db` - Market memory cache
- `data/alert_batch.db` - Alert batching data

### Backup and Recovery

```bash
# Manual backup
cp data/marketman.db data/marketman_backup_$(date +%Y%m%d).db

# Restore from backup
cp data/marketman_backup_20240101.db data/marketman.db
```

## 🔍 Troubleshooting

### Common Issues

#### API Rate Limits
- **Problem**: "API rate limit exceeded" errors
- **Solution**: Reduce API call limits in `config/settings.yaml`

#### Database Errors
- **Problem**: Database connection issues
- **Solution**: Check database file permissions and disk space

#### Configuration Errors
- **Problem**: "Configuration validation failed"
- **Solution**: Run `python marketman config validate` to identify issues

#### Signal Generation Issues
- **Problem**: No signals being generated
- **Solution**: Check news sources and AI API key configuration

### Debug Mode

Enable verbose logging for troubleshooting:
```bash
python marketman --verbose news cycle
```

### Log Files

Check log files for detailed error information:
- `logs/marketman.log` - Main application logs
- `logs/marketman_cli.log` - CLI command logs

## 📊 Performance Tracking

### Trade Journal

Track your trading performance:
```bash
# Add a trade
python marketman journal add-trade --symbol AAPL --action Buy --quantity 100 --price 150.00

# View trade history
python marketman journal list-trades --days 30

# Performance analysis
python marketman journal performance --days 90
```

### Signal Analysis

Analyze signal performance:
```bash
# View signal history
python marketman journal signals --days 30

# Add manual signal
python marketman journal add-signal --type bullish --confidence 8 --symbol TSLA
```

### Fidelity Integration

Import trades from Fidelity:
```bash
# Setup Fidelity integration
python marketman journal setup-fidelity --email your@email.com

# Import recent trades
python marketman journal import-fidelity --days 30
```

## 🔗 Integrations

### Notion Integration

Sync data with Notion:
```bash
# Sync signals to Notion
python marketman journal sync-notion

# Add signal to Notion
python marketman journal add-signal --sync-notion
```

### Gmail Organization

Organize MarketMan emails:
```bash
# Run Gmail cleanup
python src/monitoring/marketman_monitor.py --gmail-only
```

## 🚫 Not Implemented

The following features are **NOT YET IMPLEMENTED**:

1. **Web Dashboard** - CLI-only interface
2. **RESTful API** - No web API endpoints
3. **Backtesting Engine** - Empty module, no implementation
4. **Real-time Trading** - Paper trading only
5. **Advanced Risk Models** - Basic Kelly Criterion only
6. **Advanced Authentication** - No user authentication system
7. **Load Balancing** - Single instance only
8. **Advanced Database Features** - No partitioning or sharding

---

**Next**: [Configuration](configuration.md) for detailed configuration options 