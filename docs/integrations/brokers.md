# Broker Integration

Complete guide to integrating MarketMan with various broker platforms for automated trading.

## 📋 Table of Contents

- [Overview](#overview)
- [Supported Brokers](#supported-brokers)
- [Setup](#setup)
- [Configuration](#configuration)
- [Usage](#usage)
- [Risk Management](#risk-management)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

MarketMan supports integration with multiple broker platforms to execute trades based on AI-generated signals. The system includes:

- **Paper Trading** - Risk-free testing environment
- **Real Trading** - Live market execution
- **Risk Management** - Position sizing and stop losses
- **Order Management** - Market, limit, and stop orders
- **Portfolio Tracking** - Real-time position monitoring

### Features
- **Multi-Broker Support** - Alpaca, Interactive Brokers, TD Ameritrade
- **Order Types** - Market, limit, stop-loss, trailing stops
- **Risk Controls** - Position limits, daily loss limits
- **Real-time Data** - Live price feeds and market data
- **Backtesting** - Historical strategy testing

## 🏦 Supported Brokers

### Paper Trading (Default)
- **Risk-free testing** environment
- **Real market data** with simulated execution
- **No capital required** for testing
- **Perfect for strategy validation**

### Alpaca
- **Commission-free** trading
- **REST API** and WebSocket support
- **Paper and live** trading
- **Fractional shares** support
- **Extended hours** trading

### Interactive Brokers (IBKR)
- **Professional platform** with advanced features
- **Global markets** access
- **Options and futures** trading
- **Advanced order types**
- **Competitive commissions**

### TD Ameritrade
- **ThinkOrSwim** platform integration
- **Commission-free** stock and ETF trading
- **Options trading** support
- **Research tools** integration
- **Mobile app** support

## 🚀 Setup

### Prerequisites

1. **Broker Account** - Active trading account
2. **API Access** - API keys and permissions
3. **Market Data** - Real-time data subscription
4. **Risk Capital** - Funds for trading (real accounts)

### Step 1: Choose Your Broker

#### For Beginners
- **Start with Paper Trading** - No risk, learn the system
- **Move to Alpaca** - Simple API, commission-free
- **Graduate to IBKR** - Advanced features when ready

#### For Experienced Traders
- **Interactive Brokers** - Professional features
- **TD Ameritrade** - Research integration
- **Custom Integration** - Build your own connector

### Step 2: Account Setup

#### Paper Trading
```bash
# No setup required - enabled by default
# Configure in config/brokers.yaml:
paper_trading:
  enabled: true
  initial_balance: 25000
```

#### Alpaca Setup
1. Create account at [alpaca.markets](https://alpaca.markets)
2. Get API keys from dashboard
3. Add to `.env`:
```bash
ALPACA_API_KEY=your_api_key
ALPACA_SECRET_KEY=your_secret_key
ALPACA_PAPER=true  # Set to false for live trading
```

#### Interactive Brokers Setup
1. Open IBKR account
2. Enable API access in TWS/IB Gateway
3. Configure connection settings
4. Add to `.env`:
```bash
IB_HOST=127.0.0.1
IB_PORT=7497  # 7496 for paper trading
IB_CLIENT_ID=1
```

#### TD Ameritrade Setup
1. Create TD Ameritrade account
2. Register app at [developer.tdameritrade.com](https://developer.tdameritrade.com)
3. Get API keys and refresh token
4. Add to `.env`:
```bash
TD_CLIENT_ID=your_client_id
TD_REFRESH_TOKEN=your_refresh_token
TD_ACCOUNT_ID=your_account_id
```

### Step 3: Configure MarketMan

Update `config/brokers.yaml`:

```yaml
# Broker Configuration
brokers:
  # Paper Trading (Default)
  paper_trading:
    enabled: true
    name: "Paper Trading"
    account_type: "paper"
    initial_balance: 25000
    commission_per_trade: 0.0
    margin_enabled: false

  # Alpaca
  alpaca:
    enabled: false  # Set to true when ready
    name: "Alpaca"
    account_type: "live"  # or "paper"
    api_key: ${ALPACA_API_KEY}
    secret_key: ${ALPACA_SECRET_KEY}
    paper_trading: true
    base_url: "https://paper-api.alpaca.markets"  # or live URL

  # Interactive Brokers
  interactive_brokers:
    enabled: false
    name: "Interactive Brokers"
    account_type: "live"
    host: ${IB_HOST}
    port: ${IB_PORT}
    client_id: ${IB_CLIENT_ID}
    paper_trading: false

  # TD Ameritrade
  td_ameritrade:
    enabled: false
    name: "TD Ameritrade"
    account_type: "live"
    client_id: ${TD_CLIENT_ID}
    refresh_token: ${TD_REFRESH_TOKEN}
    account_id: ${TD_ACCOUNT_ID}

# Global Settings
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

## ⚙️ Configuration

### Risk Management Settings

```yaml
risk_management:
  # Position Sizing
  max_position_size: 2500  # Maximum position size in dollars
  max_portfolio_risk: 0.02  # 2% maximum portfolio risk per trade
  
  # Daily Limits
  max_daily_trades: 20
  max_daily_loss: 500  # Maximum daily loss in dollars
  max_daily_loss_percent: 0.03  # 3% maximum daily loss
  
  # Stop Losses
  default_stop_loss: 0.02  # 2% default stop loss
  trailing_stop: true
  trailing_stop_percent: 0.01  # 1% trailing stop
  
  # Kelly Criterion
  kelly_enabled: true
  max_kelly_fraction: 0.25  # 25% maximum Kelly fraction
```

### Order Management

```yaml
order_management:
  # Order Types
  default_order_type: "market"  # market, limit, stop
  limit_order_buffer: 0.001  # 0.1% buffer for limit orders
  
  # Order Timing
  order_timeout: 30  # seconds
  retry_attempts: 3
  retry_delay: 5  # seconds
  
  # Order Validation
  validate_orders: true
  check_market_hours: true
  check_position_limits: true
```

### Market Data

```yaml
market_data:
  # Data Sources
  primary_source: "alpaca"  # alpaca, ib, td
  backup_source: "yahoo"
  
  # Data Types
  real_time_prices: true
  historical_data: true
  options_data: false
  
  # Update Frequency
  price_update_interval: 1  # seconds
  volume_update_interval: 5  # seconds
```

## 🚀 Usage

### Paper Trading

```bash
# Start paper trading session
python marketman broker paper start

# Check paper trading status
python marketman broker paper status

# View paper trading positions
python marketman broker paper positions

# Reset paper trading account
python marketman broker paper reset
```

### Live Trading

```bash
# Connect to live broker
python marketman broker connect --broker alpaca

# Check account status
python marketman broker status

# View positions
python marketman broker positions

# Place test order
python marketman broker order --symbol TSLA --quantity 10 --side buy
```

### Signal Execution

```bash
# Enable signal execution
python marketman signals execute --enable

# Check execution status
python marketman signals status

# View pending signals
python marketman signals pending

# Execute specific signal
python marketman signals execute --signal-id signal_123
```

### Portfolio Management

```bash
# View portfolio summary
python marketman portfolio summary

# Check risk metrics
python marketman portfolio risk

# View performance
python marketman portfolio performance

# Rebalance portfolio
python marketman portfolio rebalance
```

## 🛡️ Risk Management

### Position Sizing

```python
from src.core.risk.position_sizer import PositionSizer

# Initialize position sizer
sizer = PositionSizer()

# Calculate position size using Kelly Criterion
position_size = sizer.calculate_kelly_size(
    win_rate=0.65,
    avg_win=500,
    avg_loss=300,
    confidence=0.8
)

# Calculate fixed percentage position
position_size = sizer.calculate_fixed_percentage(
    percentage=0.02,  # 2% of account
    price=250.50,
    confidence=0.8
)
```

### Stop Loss Management

```python
from src.core.risk.stop_loss import StopLossManager

# Initialize stop loss manager
stop_manager = StopLossManager()

# Set hard stop loss
stop_manager.set_hard_stop(
    symbol="TSLA",
    stop_price=245.00,
    quantity=100
)

# Set trailing stop
stop_manager.set_trailing_stop(
    symbol="TSLA",
    trail_percent=0.01,  # 1%
    quantity=100
)
```

### Portfolio Limits

```python
from src.core.risk.portfolio_manager import PortfolioManager

# Initialize portfolio manager
portfolio = PortfolioManager()

# Check position limits
if portfolio.check_position_limit("TSLA", 1000):
    # Place order
    pass

# Check daily loss limit
if portfolio.check_daily_loss_limit():
    # Stop trading
    pass

# Check sector exposure
if portfolio.check_sector_exposure("Technology", 0.3):
    # Limit tech exposure
    pass
```

## 📊 Order Types

### Market Orders

```python
# Simple market order
order = broker.place_market_order(
    symbol="TSLA",
    quantity=100,
    side="buy"
)
```

### Limit Orders

```python
# Limit order with buffer
order = broker.place_limit_order(
    symbol="TSLA",
    quantity=100,
    side="buy",
    limit_price=250.00,
    time_in_force="day"
)
```

### Stop Orders

```python
# Stop loss order
order = broker.place_stop_order(
    symbol="TSLA",
    quantity=100,
    side="sell",
    stop_price=245.00,
    time_in_force="gtc"
)
```

### Trailing Stops

```python
# Trailing stop order
order = broker.place_trailing_stop(
    symbol="TSLA",
    quantity=100,
    side="sell",
    trail_percent=0.01,  # 1%
    time_in_force="gtc"
)
```

## 🔧 Troubleshooting

### Common Issues

#### "Broker connection failed"

**Solution**:
```bash
# Check broker status
python marketman broker status

# Test connection
python marketman broker test

# Check API keys
echo $ALPACA_API_KEY | head -c 10

# Verify network connectivity
ping api.alpaca.markets
```

#### "Order rejected"

**Solution**:
```bash
# Check order validation
python marketman broker validate --symbol TSLA --quantity 100

# Check account balance
python marketman broker balance

# Check market hours
python marketman broker hours

# Check position limits
python marketman broker limits
```

#### "Position not found"

**Solution**:
```bash
# Refresh positions
python marketman broker refresh

# Check order status
python marketman broker orders

# Verify order execution
python marketman broker history
```

### Debug Mode

```bash
# Enable debug logging
export DEBUG=true

# Run with debug output
python marketman broker connect --debug

# Check broker logs
tail -f logs/broker.log
```

### Testing

```bash
# Test paper trading
python marketman broker test --paper

# Test live connection
python marketman broker test --live

# Test order placement
python marketman broker test --order

# Test market data
python marketman broker test --data
```

## 📈 Advanced Features

### Algorithmic Trading

```python
# Custom trading algorithm
class MyTradingAlgorithm:
    def __init__(self, broker):
        self.broker = broker
    
    def execute_signal(self, signal):
        # Custom execution logic
        if signal.confidence >= 8:
            position_size = self.calculate_position_size(signal)
            order = self.broker.place_market_order(
                symbol=signal.symbol,
                quantity=position_size,
                side=signal.side
            )
            return order
```

### Multi-Broker Support

```python
# Trade across multiple brokers
brokers = {
    "alpaca": AlpacaBroker(),
    "ib": InteractiveBrokers(),
    "td": TDAmeritrade()
}

# Distribute orders across brokers
for broker_name, broker in brokers.items():
    if broker.is_available():
        order = broker.place_order(order_data)
```

### Real-time Monitoring

```python
# Monitor positions in real-time
def monitor_positions():
    while True:
        positions = broker.get_positions()
        for position in positions:
            if position.unrealized_pnl < -500:
                # Close losing position
                broker.close_position(position.symbol)
        time.sleep(30)
```

## 🔗 Related Documentation

- **[User Guide](../user-guide.md)** - Complete usage instructions
- **[Configuration Guide](../configuration.md)** - Setup and configuration
- **[Risk Management](../risk-management.md)** - Risk management guide
- **[Troubleshooting](../troubleshooting.md)** - Common issues and solutions

---

**Need help?** Check the [Troubleshooting Guide](../troubleshooting.md) or create an issue on GitHub. 