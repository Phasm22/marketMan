# MarketMan User Guide

Complete guide to using MarketMan for automated trading signal generation and analysis.

## 📋 Table of Contents

- [Getting Started](#getting-started)
- [Core Concepts](#core-concepts)
- [Daily Operations](#daily-operations)
- [Configuration](#configuration)
- [Monitoring & Alerts](#monitoring--alerts)
- [Troubleshooting](#troubleshooting)

## 🚀 Getting Started

### Prerequisites

Before using MarketMan, ensure you have:

- **Python 3.9+** installed
- **API Keys** for required services:
  - OpenAI (for AI analysis)
  - Finnhub (for financial news)
  - NewsAPI (for general news)
  - NewData (for additional sources)
- **Pushover account** (optional, for notifications)

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
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Validate configuration**:
   ```bash
   python marketman config validate
   ```

### First Run

1. **Test the system**:
   ```bash
   python marketman status
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

1. **Collection** - Gathers news from multiple sources
2. **Filtering** - Removes irrelevant content using keywords
3. **Batching** - Groups related news for efficient processing
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
   python marketman status
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
- **Monitor performance** with the dashboard
- **Review daily summaries** in Notion (if configured)

### End-of-Day Review

1. **Check performance**:
   ```bash
   python marketman performance show
   ```

2. **Review trades**:
   ```bash
   python marketman journal performance
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
  min_relevance_score: 0.15     # Minimum relevance threshold
```

#### Alerts
```yaml
alerts:
  batch_strategy: smart_batch   # Alert batching strategy
  max_daily_alerts: 10          # Maximum alerts per day
  confidence_threshold: 7       # Minimum confidence for alerts
```

### Environment Variables

Required in `.env` file:
```bash
# OpenAI
OPENAI_API_KEY=your_openai_key

# News APIs
FINNHUB_KEY=your_finnhub_key
NEWS_API=your_newsapi_key
NEWS_DATA_KEY=your_newdata_key

# Notifications
PUSHOVER_TOKEN=your_pushover_token
PUSHOVER_USER=your_pushover_user

# Notion (optional)
NOTION_TOKEN=your_notion_token
NOTION_DATABASE_ID=your_database_id
```

## 📱 Monitoring & Alerts

### Pushover Notifications

MarketMan sends notifications for:
- **High-confidence signals** (7+ confidence)
- **Risk warnings** (market volatility)
- **System alerts** (errors, warnings)

#### Setup Pushover
1. Create account at [pushover.net](https://pushover.net)
2. Get API token and user key
3. Add to `.env` file
4. Test with: `python marketman pushover test`

#### Alert Types
- **Signal Alerts**: Trading opportunities
- **Risk Warnings**: Market volatility alerts
- **System Alerts**: Service status updates

### Performance Monitoring

#### Dashboard
```bash
python marketman performance show
```

Shows:
- Total trades and win rate
- P&L and drawdown
- Signal accuracy
- Sector performance

#### Performance Reports
```bash
python marketman journal performance --days 30
```

Generates detailed performance analysis.

## 🔧 Troubleshooting

### Common Issues

#### "API rate limit exceeded"
- **Solution**: Reduce API call limits in `config/settings.yaml`
- **Prevention**: Monitor usage with `python marketman status`

#### "No signals generated"
- **Check**: News sources are working
- **Check**: AI API key is valid
- **Check**: Confidence thresholds aren't too high

#### "Configuration errors"
- **Solution**: Run `python marketman config validate`
- **Check**: All required API keys in `.env`

#### "Database errors"
- **Solution**: Check database permissions
- **Reset**: Delete `*.db` files and restart

### Debug Mode

Enable debug logging:
```bash
export DEBUG=true
python marketman news cycle
```

### Log Files

Check logs in `logs/` directory:
- `marketman.log` - Main application log
- `analyzer.log` - AI analysis log

### Getting Help

1. **Check documentation**: `docs/` folder
2. **Run diagnostics**: `python marketman status`
3. **Validate config**: `python marketman config validate`
4. **Create issue**: GitHub issues page

## 📊 Best Practices

### Risk Management
- Start with paper trading
- Use conservative position sizes
- Set appropriate stop losses
- Monitor daily loss limits

### Configuration
- Validate settings regularly
- Monitor API costs
- Adjust thresholds based on performance
- Keep backups of working configurations

### Monitoring
- Check system status daily
- Review performance weekly
- Monitor API usage
- Keep logs for troubleshooting

### Signal Quality
- Focus on high-confidence signals (7+)
- Consider market conditions
- Use multiple timeframes
- Don't chase every signal

---

**Next**: [API Reference](api-reference.md) for technical details 