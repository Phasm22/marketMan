# Configuration Guide

Complete guide to configuring MarketMan for your trading needs.

## 📋 Table of Contents

- [Overview](#overview)
- [Configuration Files](#configuration-files)
- [Risk Management](#risk-management)
- [News Processing](#news-processing)
- [Alerts & Notifications](#alerts--notifications)
- [Performance Tuning](#performance-tuning)
- [Validation](#validation)

## 🎯 Overview

MarketMan uses a YAML-based configuration system:
- **settings.yaml** - Main system configuration and API keys
- **strategies.yaml** - Trading strategy configurations
- **brokers.yaml** - Broker and trading settings
- **Runtime validation** - Ensures settings are valid

## 📁 Configuration Files

### settings.yaml

Main system configuration file (create this file in `config/` directory):

```yaml
# OpenAI Configuration
openai:
  api_key: sk-proj-your-openai-key-here

# News APIs
finnhub:
  api_key: your-finnhub-key
newsapi:
  api_key: your-newsapi-key
newdata:
  api_key: your-newdata-key

# Pushover (notifications)
pushover:
  token: your-pushover-token
  user_key: your-pushover-user-key

# Notion (optional)
notion:
  token: your-notion-token
  database_id: your-database-id
  trades_database_id: your-trades-db-id
  signals_database_id: your-signals-db-id
  performance_database_id: your-performance-db-id

# Gmail (optional)
gmail:
  client_id: your-gmail-client-id
  client_secret: your-gmail-client-secret
  refresh_token: your-gmail-refresh-token

# Fidelity (optional)
fidelity:
  email: your-fidelity-email
  password: your-fidelity-password

# Application Settings
app:
  name: MarketMan
  version: 1.0.0
  debug: false
  log_level: INFO

# Risk Management
risk:
  max_daily_loss: 0.05          # 5% maximum daily loss
  max_position_size: 0.02       # 2% maximum position size
  stop_loss_percent: 2.0        # 2% stop loss
  max_kelly_fraction: 0.25      # 25% Kelly criterion limit
  position_sizing_enabled: true

# News Processing
news_ingestion:
  max_daily_headlines: 50       # Maximum headlines per day
  max_daily_ai_calls: 75        # Maximum AI API calls
  min_relevance_score: 0.15     # Minimum relevance threshold
  batch_size: 10                # News batching size

# Alerts
alerts:
  batch_strategy: smart_batch   # immediate, smart_batch, time_window, daily_digest
  max_daily_alerts: 10          # Maximum alerts per day
  confidence_threshold: 7       # Minimum confidence for alerts
  pushover_enabled: true
  notion_enabled: false

# Database
database:
  type: sqlite
  path: data/marketman.db
  backup_enabled: true
  backup_interval_hours: 24

# Logging
logging:
  level: INFO
  file: logs/marketman.log
  max_size_mb: 100
  backup_count: 5
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

# News Analysis Strategy
news_analysis:
  name: "News Sentiment Strategy"
  enabled: true
  
  keywords:
    positive: ["bullish", "rally", "surge", "gain", "positive", "growth"]
    negative: ["bearish", "decline", "drop", "loss", "negative", "recession"]
    neutral: ["stable", "steady", "unchanged", "flat"]
  
  sentiment_weights:
    positive: 1.0
    negative: -1.0
    neutral: 0.0
  
  time_decay:
    half_life_hours: 24
    max_age_hours: 168  # 1 week

# Options Scalping Strategy
options_scalping:
  name: "QQQ/SPY Options Scalping"
  enabled: false  # Toggle to activate
  
  symbols:
    - "QQQ"
    - "SPY"
  
  entry_conditions:
    min_iv_percentile: 30
    max_iv_percentile: 80
    min_dte: 1
    max_dte: 7
    min_bid_ask_spread: 0.05
  
  exit_conditions:
    profit_target_percent: 1.5
    stop_loss_percent: 1.0
    max_hold_time_minutes: 30
    theta_decay_threshold: 0.1
  
  position_sizing:
    max_capital_per_trade: 1000
    max_portfolio_risk: 0.02  # 2%
    max_correlation: 0.7

# Risk Management Strategy
risk_management:
  name: "Dynamic Risk Management"
  enabled: true
  
  position_sizing:
    kelly_criterion_enabled: true
    max_kelly_fraction: 0.25
    min_position_size: 100
    max_position_size: 2500  # Reduced from 10000 to align with 25k account
  
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

Broker and trading configurations:

```yaml
# Paper Trading (Default)
paper_trading:
  enabled: true
  name: "Paper Trading"
  account_type: "paper"
  initial_balance: 25000
  commission_per_trade: 0.0
  margin_enabled: false

# Interactive Brokers (Future)
interactive_brokers:
  enabled: false
  name: "Interactive Brokers"
  account_type: "live"
  host: "127.0.0.1"
  port: 7497
  client_id: 1
  paper_trading: false
  
  # API Settings
  api_settings:
    timeout: 30
    retry_attempts: 3
    retry_delay: 1
  
  # Order Settings
  order_settings:
    default_order_type: "MKT"
    default_time_in_force: "DAY"
    max_slippage: 0.01

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

## 🔐 Getting API Keys

### OpenAI
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Create account and add billing
3. Generate API key in API Keys section

### Finnhub
1. Visit [Finnhub.io](https://finnhub.io/)
2. Sign up for free account
3. Get API key from dashboard

### NewsAPI
1. Go to [NewsAPI.org](https://newsapi.org/)
2. Register for free account
3. Copy API key from account page

### NewData
1. Visit [NewData.io](https://newsdata.io/)
2. Create free account
3. Get API key from dashboard

### Pushover
1. Go to [Pushover.net](https://pushover.net/)
2. Create account
3. Get User Key from main page
4. Create app to get API Token

### Notion (Optional)
1. Go to [Notion Developers](https://developers.notion.com/)
2. Create integration
3. Get internal integration token
4. Share database with integration

## 🛡️ Risk Management

### Position Sizing

Configure position sizing parameters:

```yaml
risk:
  max_daily_loss: 0.05          # 5% maximum daily loss
  max_position_size: 0.02       # 2% maximum position size
  stop_loss_percent: 2.0        # 2% stop loss
  max_kelly_fraction: 0.25      # 25% Kelly criterion limit
```

### Portfolio Limits

Set portfolio-level risk limits:

```yaml
risk_management:
  portfolio_limits:
    max_sector_exposure: 0.3    # 30% max per sector
    max_single_position: 0.1    # 10% max per position
    max_correlation: 0.8        # Max correlation between positions
    min_diversification: 5      # Minimum number of positions
```

## 📰 News Processing

### Source Configuration

Configure news sources and limits:

```yaml
news_ingestion:
  max_daily_headlines: 50       # Maximum headlines per day
  max_daily_ai_calls: 75        # Maximum AI API calls
  min_relevance_score: 0.15     # Minimum relevance threshold
  batch_size: 10                # News batching size
```

### Filtering Settings

Advanced news filtering options:

```yaml
news_analysis:
  keywords:
    positive: ["bullish", "rally", "surge", "gain", "positive", "growth"]
    negative: ["bearish", "decline", "drop", "loss", "negative", "recession"]
    neutral: ["stable", "steady", "unchanged", "flat"]
  
  sentiment_weights:
    positive: 1.0
    negative: -1.0
    neutral: 0.0
```

## 📱 Alerts & Notifications

### Alert Configuration

Configure alert behavior:

```yaml
alerts:
  batch_strategy: smart_batch   # Batching strategy
  max_daily_alerts: 10          # Maximum alerts per day
  confidence_threshold: 7       # Minimum confidence for alerts
  pushover_enabled: true        # Enable Pushover notifications
  notion_enabled: false         # Enable Notion integration
```

### Batching Strategies

The news ingestion system uses a hybrid batching approach:
- Batches are finalized and processed immediately if they reach the maximum batch size.
- Batches are also finalized if they have at least the minimum batch size and have been waiting longer than the configured max wait time.
- At the end of each news cycle, any remaining pending batches that meet the minimum batch size are finalized and processed, ensuring no news is left unprocessed. This is handled by the `finalize_all_pending_batches` method in the batcher and called by the orchestrator.

## ⚡ Performance Tuning

### Database Settings

Optimize database performance:

```yaml
database:
  type: sqlite
  path: data/marketman.db
  backup_enabled: true
  backup_interval_hours: 24
```

### Logging Configuration

Configure logging behavior:

```yaml
logging:
  level: INFO                   # DEBUG, INFO, WARNING, ERROR
  file: logs/marketman.log
  max_size_mb: 100
  backup_count: 5
```

### API Rate Limits

Monitor and adjust API usage:

```yaml
# Built-in rate limiting
news_ingestion:
  max_daily_headlines: 50       # Adjust based on API limits
  max_daily_ai_calls: 75        # Monitor OpenAI usage
```

## ✅ Validation

### Configuration Validation

Validate your configuration:

```bash
# Validate all configuration files
python marketman config validate

# Show current configuration
python marketman config show

# Test specific components
python marketman news test
```

### Common Validation Errors

#### Missing API Keys
```
Error: Missing required API key: openai.api_key
Solution: Add your OpenAI API key to config/settings.yaml
```

#### Invalid File Paths
```
Error: Database path not accessible: data/marketman.db
Solution: Ensure data/ directory exists and is writable
```

#### Invalid Values
```
Error: Invalid confidence_threshold: 15 (must be 1-10)
Solution: Set confidence_threshold to a value between 1 and 10
```

### Configuration Testing

Test individual components:

```bash
# Test news sources
python marketman news test

# Test Pushover notifications
python src/monitoring/marketman_monitor.py --test

# Test database connection
python -c "from src.core.database.db_manager import DatabaseManager; print('Database OK')"
```

## 🔧 Advanced Configuration

### Custom Strategies

Add custom trading strategies:

```yaml
# Custom Strategy Example
custom_strategy:
  name: "Custom Momentum Strategy"
  enabled: true
  
  # Define your strategy parameters
  parameters:
    lookback_period: 20
    momentum_threshold: 0.05
    volume_multiplier: 1.5
  
  # Define entry/exit conditions
  conditions:
    entry:
      - "price > sma_20"
      - "volume > avg_volume * 1.5"
    exit:
      - "price < sma_20"
      - "stop_loss_hit"
```

### Environment-Specific Settings

Use different configurations for different environments:

```bash
# Development
cp config/settings.yaml config/settings.dev.yaml

# Production
cp config/settings.yaml config/settings.prod.yaml

# Use specific config
python marketman --config config/settings.prod.yaml news cycle
```

### Configuration Inheritance

Override default settings:

```yaml
# Override specific settings
risk:
  max_daily_loss: 0.03          # More conservative for production
  
news_ingestion:
  max_daily_ai_calls: 50        # Reduce costs in production
```

## 🚫 Not Implemented

The following configuration features are **NOT YET IMPLEMENTED**:

1. **Environment Variables** - No .env file support
2. **Configuration Encryption** - No encrypted configuration
3. **Dynamic Configuration** - No runtime configuration changes
4. **Configuration Templates** - No template system
5. **Configuration Validation Schema** - Basic validation only
6. **Configuration Migration** - No automatic migration system

---

**Next**: [API Reference](api-reference.md) for technical details 