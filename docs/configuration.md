# Configuration Guide

Complete guide to configuring MarketMan for your trading needs.

## 📋 Table of Contents

- [Overview](#overview)
- [Environment Setup](#environment-setup)
- [Configuration Files](#configuration-files)
- [Risk Management](#risk-management)
- [News Processing](#news-processing)
- [Alerts & Notifications](#alerts--notifications)
- [Performance Tuning](#performance-tuning)
- [Validation](#validation)

## 🎯 Overview

MarketMan uses a hierarchical configuration system:
- **Environment variables** (`.env`) - API keys and secrets
- **YAML files** (`config/`) - System settings and strategies
- **Runtime validation** - Ensures settings are valid

## 🔐 Environment Setup

### Required API Keys

Create a `.env` file in the project root:

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-proj-your-openai-key-here

# News APIs
FINNHUB_KEY=your-finnhub-key
NEWS_API=your-newsapi-key
NEWS_DATA_KEY=your-newdata-key

# Gmail (for Google Alerts)
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password

# Pushover (notifications)
PUSHOVER_TOKEN=your-pushover-token
PUSHOVER_USER=your-pushover-user-key

# Notion (optional)
NOTION_TOKEN=your-notion-token
NOTION_DATABASE_ID=your-database-id
TRADES_DATABASE_ID=your-trades-db-id
SIGNALS_DATABASE_ID=your-signals-db-id
PERFORMANCE_DATABASE_ID=your-performance-db-id

# Alert Strategy
ALERT_STRATEGY=smart_batch
```

### Getting API Keys

#### OpenAI
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Create account and add billing
3. Generate API key in API Keys section

#### Finnhub
1. Visit [Finnhub.io](https://finnhub.io/)
2. Sign up for free account
3. Get API key from dashboard

#### NewsAPI
1. Go to [NewsAPI.org](https://newsapi.org/)
2. Register for free account
3. Copy API key from account page

#### NewData
1. Visit [NewData.io](https://newsdata.io/)
2. Create free account
3. Get API key from dashboard

#### Pushover
1. Go to [Pushover.net](https://pushover.net/)
2. Create account
3. Get User Key from main page
4. Create app to get API Token

## 📁 Configuration Files

### settings.yaml

Main system configuration file:

```yaml
# Application Settings
app:
  name: MarketMan
  version: 1.0.0
  debug: false
  log_level: INFO

# Risk Management
risk:
  max_daily_loss: 0.05          # 5% maximum daily loss
  max_daily_loss_percent: 3.0   # 3% daily loss limit
  max_position_size: 0.02       # 2% maximum position size
  max_position_size_percent: 5.0 # 5% position size limit
  max_kelly_fraction: 0.25      # 25% Kelly criterion limit
  stop_loss_percent: 2.0        # 2% stop loss
  position_sizing_enabled: true

# News Processing
news_ingestion:
  max_daily_headlines: 50       # Maximum headlines per day
  max_daily_ai_calls: 75        # Maximum AI API calls
  max_monthly_ai_budget: 30.0   # Monthly AI budget in USD
  
  # Advanced Filtering
  advanced_filtering:
    min_relevance_score: 0.15   # Minimum relevance threshold
    min_sentiment_strength: 0.1 # Minimum sentiment strength
    min_ticker_count: 1         # Minimum tickers mentioned
    require_multiple_tickers: false
    max_title_length: 200
    min_content_length: 50
    exclude_clickbait: true
    require_financial_context: false

  # Market Hours (Mountain Time)
  market_hours:
    start: '08:00'
    end: '18:00'
    timezone: America/Denver

# Alerts
alerts:
  batch_strategy: smart_batch   # immediate, smart_batch, time_window, daily_digest
  max_daily_alerts: 10          # Maximum alerts per day
  notification_channels:
    - pushover
    - notion

# API Limits
api_limits:
  finnhub:
    calls_per_day: 1000
    calls_per_minute: 60
  newdata:
    calls_per_day: 200
  newsapi:
    articles_per_credit: 10
    calls_per_day: 100
  openai:
    max_requests_per_day: 50
    max_tokens_per_request: 1000

# Minimum thresholds
min_confidence_threshold: 7     # Minimum confidence for signals
min_mentions_for_etf: 2         # Minimum mentions for ETF inclusion
```

### strategies.yaml

Trading strategy configurations:

```yaml
# ETF Signal Strategy
etf_signals:
  name: "ETF Momentum Strategy"
  enabled: true
  symbols:
    - "QQQ"
    - "SPY"
    - "IWM"
    - "XLF"
    - "XLE"
  
  technical_indicators:
    rsi_period: 14
    rsi_oversold: 30
    rsi_overbought: 70
    macd_fast: 12
    macd_slow: 26
    macd_signal: 9
    sma_short: 20
    sma_long: 50
  
  signal_filters:
    min_volume: 1000000
    min_price: 10.0
    max_volatility: 0.05

# Risk Management Strategy
risk_management:
  name: "Dynamic Risk Management"
  enabled: true
  
  position_sizing:
    kelly_criterion_enabled: true
    max_kelly_fraction: 0.25
    min_position_size: 100
    max_position_size: 2500
  
  stop_loss:
    trailing_stop_enabled: true
    trailing_stop_percent: 1.0
    hard_stop_percent: 3.0
  
  portfolio_limits:
    max_sector_exposure: 0.3
    max_single_position: 0.1
    max_correlation: 0.8
    min_diversification: 5
```

### brokers.yaml

Broker and trading configuration:

```yaml
# Paper Trading (Default)
paper_trading:
  enabled: true
  name: "Paper Trading"
  account_type: "paper"
  initial_balance: 25000
  commission_per_trade: 0.0
  margin_enabled: false

# Global Broker Settings
global_settings:
  # Risk Management
  max_position_size: 2500
  max_daily_trades: 20
  max_daily_loss: 500
  
  # Order Management
  default_quantity: 100
  min_order_size: 1
  max_order_size: 2500
  
  # Market Hours (EST)
  market_open: "09:30"
  market_close: "16:00"
  pre_market_open: "04:00"
  after_hours_close: "20:00"
```

## 🛡️ Risk Management

### Position Sizing

Configure how much capital to risk per trade:

```yaml
risk:
  max_position_size: 0.02       # 2% of account per trade
  max_kelly_fraction: 0.25      # 25% Kelly criterion limit
  position_sizing_enabled: true
```

### Stop Losses

Set automatic stop losses:

```yaml
risk:
  stop_loss_percent: 2.0        # 2% stop loss
  trailing_stop_enabled: true   # Enable trailing stops
  trailing_stop_percent: 1.0    # 1% trailing stop
```

### Daily Limits

Prevent excessive losses:

```yaml
risk:
  max_daily_loss: 0.05          # 5% maximum daily loss
  max_daily_loss_percent: 3.0   # 3% daily loss limit
```

## 📰 News Processing

### Filtering Settings

Control news quality and relevance:

```yaml
news_ingestion:
  advanced_filtering:
    min_relevance_score: 0.15   # Higher = more selective
    min_sentiment_strength: 0.1 # Higher = stronger sentiment required
    exclude_clickbait: true     # Remove clickbait headlines
    require_financial_context: false # Allow tech news
```

### Cost Control

Manage API costs:

```yaml
news_ingestion:
  max_daily_ai_calls: 75        # Limit AI API calls
  max_monthly_ai_budget: 30.0   # Monthly budget limit
```

### Market Hours

Define active trading hours:

```yaml
news_ingestion:
  market_hours:
    start: '08:00'              # Start time
    end: '18:00'                # End time
    timezone: America/Denver    # Timezone
```

## 📱 Alerts & Notifications

### Pushover Configuration

```yaml
integrations:
  pushover:
    enabled: true
    api_token: your-api-token
    user_token: your-user-key
    confidence_threshold: 7     # Minimum confidence for alerts
    rate_limit_per_hour: 10     # Maximum alerts per hour
    risk_warnings_enabled: true
    priority_settings:
      high_confidence: 0        # Normal priority
      medium_confidence: 0      # Normal priority
      low_confidence: -1        # Quiet priority
      system_alerts: 1          # High priority
      risk_warnings: 1          # High priority
```

### Alert Batching

Choose alert strategy:

```yaml
alerts:
  batch_strategy: smart_batch   # Options:
                                # - immediate: Send immediately
                                # - smart_batch: Intelligent batching
                                # - time_window: 30-minute windows
                                # - daily_digest: Daily summary
  max_daily_alerts: 10          # Maximum alerts per day
```

## ⚡ Performance Tuning

### API Rate Limits

Optimize for your API tiers:

```yaml
api_limits:
  finnhub:
    calls_per_day: 1000         # Free tier limit
    calls_per_minute: 60
  openai:
    max_requests_per_day: 50    # Cost control
    max_tokens_per_request: 1000
```

### Processing Limits

Balance speed vs. cost:

```yaml
news_ingestion:
  max_daily_headlines: 50       # Process 50 headlines/day
  max_daily_ai_calls: 75        # Use 75 AI calls/day
  batching:
    max_batch_wait_time: 180    # 3-minute batch wait
    max_headlines_per_batch: 8  # 8 headlines per batch
```

### Memory Optimization

For large datasets:

```yaml
database:
  path: data/marketman.db
  type: sqlite
  cleanup_old_records: true
  max_records_per_table: 10000
```

## ✅ Validation

### Validate Configuration

Check your settings:

```bash
python marketman config validate
```

This checks:
- ✅ API keys are configured
- ✅ Risk limits are reasonable
- ✅ API limits are within bounds
- ✅ File permissions are correct
- ✅ Database connectivity

### Show Current Settings

View current configuration:

```bash
python marketman config show
```

### Reload Configuration

After making changes:

```bash
python marketman config reload
```

## 🔧 Advanced Configuration

### Custom Keywords

Add your own keywords:

```yaml
news_ingestion:
  keywords:
    - "ETF"
    - "SPY"
    - "QQQ"
    - "interest rate"
    - "Fed"
    - "earnings"
    # Add your custom keywords here
```

### Source Weights

Prioritize news sources:

```yaml
news_ingestion:
  multi_source_validation:
    source_weights:
      Reuters: 5
      Bloomberg: 5
      Financial Times: 5
      CNBC: 4
      MarketWatch: 4
      Yahoo Finance: 3
      TechCrunch: 3
      unknown: 1
```

### Tracked ETFs

Specify which ETFs to monitor:

```yaml
news_ingestion:
  tracked_tickers:
    - BOTZ    # Robotics & Automation
    - ROBO    # Robotics
    - ICLN    # Clean Energy
    - TAN     # Solar Energy
    - LIT     # Lithium & Battery Tech
    - SMH     # Semiconductor
    # Add your preferred ETFs
```

## 🚨 Troubleshooting

### Common Issues

#### "Configuration validation failed"
- Check all required API keys in `.env`
- Ensure YAML syntax is correct
- Run `python marketman config validate` for details

#### "API rate limit exceeded"
- Reduce `calls_per_day` limits
- Increase `calls_per_minute` delays
- Check your API tier limits

#### "No signals generated"
- Lower `min_relevance_score` threshold
- Reduce `min_confidence_threshold`
- Check news sources are working

#### "High API costs"
- Reduce `max_daily_ai_calls`
- Lower `max_tokens_per_request`
- Use more aggressive filtering

### Configuration Best Practices

1. **Start Conservative**: Begin with low limits and increase gradually
2. **Monitor Costs**: Track API usage and adjust limits
3. **Test Changes**: Validate configuration after changes
4. **Backup Settings**: Keep copies of working configurations
5. **Document Changes**: Note what works and what doesn't

---

**Next**: [Development Guide](development.md) for contributors 