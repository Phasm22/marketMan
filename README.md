# 🚀 MarketMan

**Professional ETF Market Intelligence & Alert System**

MarketMan transforms Google Alerts into actionable ETF trading signals using AI analysis, contextual memory, and intelligent batching. Built for serious thematic ETF investors who need precise, timely market intelligence without notification fatigue.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Architecture](https://img.shields.io/badge/Architecture-Modular-brightgreen.svg)

## 📑 Table of Contents

- [🏗️ Architecture Overview](#️-architecture-overview)
- [🎯 What It Does](#-what-it-does)
- [⚡ Quick Start](#-quick-start)
- [🔧 Configuration](#-configuration)
- [🧠 Alert Batching Strategies](#-alert-batching-strategies)
- [📧 Gmail Management](#-gmail-management)
- [📝 Notion Status Tracking](#-notion-status-tracking)
- [📊 Core Components](#-core-components)
- [🔧 Developer Guide](#-developer-guide)
- [🛠️ Command Line Tools](#️-command-line-tools)
- [📈 Typical Workflows](#-typical-workflows)
- [🎯 Alert Examples](#-alert-examples)
- [🗂️ Project Structure](#️-project-structure)
- [🎉 Recent Updates](#-recent-updates)
- [🚀 Migration Guide](#-migration-guide)
- [🎯 Summary](#-summary)

---

## 🎯 What It Does

- **📰 Analyzes Google Alerts** → AI-powered ETF signal extraction
- **🧠 Contextual Memory** → Pattern detection and historical insights  
- **📊 Real-time Data** → Live ETF prices and market snapshots
- **🎯 Smart Batching** → Intelligent notification grouping
- **📝 Notion Integration** → Comprehensive analysis logging
- **📱 Pushover Alerts** → Professional mobile notifications

## ⚡ Quick Start

### 1. Installation
```bash
git clone <repository>
cd marketMan
pip install -r requirements.txt
chmod +x marketman marketman-alerts
```

### 2. Configuration
```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Setup Notion Database
```bash
python setup/notion_setup_enhanced.py
```

### 4. Test System
```bash
# Test refactored system
python -m src.core.news_analyzer_refactored test

# Test with debug mode
python -m src.core.news_analyzer_refactored --debug test

# Legacy test (still works)
python src/core/news_gpt_analyzer.py test

# Test all components
./bin/marketman test --all
```

### 5. Run Analysis
```bash
# Use refactored system (recommended)
python -m src.core.news_analyzer_refactored

# Continuous monitoring with refactored system
./bin/marketman monitor --loop 30

# Legacy single run (still works)
python src/core/news_gpt_analyzer.py

# Check alert queue
./bin/marketman-alerts stats
```

## 🔧 Configuration

### Environment Variables (`.env`)
```bash
# Required
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password
OPENAI_API_KEY=sk-your-openai-key

# Optional  
PUSHOVER_TOKEN=your-pushover-token
PUSHOVER_USER=your-pushover-user
NOTION_TOKEN=your-notion-token
NOTION_DATABASE_ID=your-database-id

# Alert Strategy (smart_batch recommended)
ALERT_STRATEGY=smart_batch
```

### Google Alerts Setup
1. Create Google Alerts for your target keywords
2. Set delivery to your Gmail account
3. MarketMan automatically processes new alerts

## 🧠 Alert Batching Strategies

| Strategy | Description | Best For |
|----------|-------------|-----------|
| `smart_batch` | High confidence immediate, others batched | **Recommended default** |
| `immediate` | Send every alert right away | Low-volume setups |
| `time_window` | Batch alerts every 30 minutes | High-volume monitoring |
| `daily_digest` | One summary per day | Long-term investors |

```bash
# Change strategy
echo "ALERT_STRATEGY=daily_digest" >> .env

# Check configuration
./marketman-alerts config
```

## 📧 Gmail Management

MarketMan can automatically organize your MarketMan alerts in Gmail:

```bash
# Set up Gmail integration (one-time)
./bin/gmail-organizer setup

# Move read MarketMan alerts to folder
./bin/gmail-organizer organize

# See what would be moved (dry run)
./bin/gmail-organizer dry-run

# Auto-organize if 5+ emails found
./bin/gmail-organizer auto
```

## 📝 Notion Status Tracking

New Notion cards include a **Status** field to track your review progress:

- **New** - Freshly analyzed signals (default)
- **Reviewed** - You've read and considered the signal
- **Acted On** - You've taken action based on the signal
- **Archived** - Historical reference

Simply update the Status dropdown in Notion to keep track of what you've reviewed!

## 📊 Core Components

### 🤖 AI Analysis Engine (Refactored)
**Primary Module:** `etf_analyzer.py` (254 lines)
- **GPT-4 powered** thematic ETF analysis
- **Sector categorization** (AI, Defense, Clean Energy, etc.)
- **Confidence scoring** (1-10 scale)
- **Tactical explanations** with specific entry/exit strategies
- **ETF categorization** by sector and theme

**Market Data Module:** `market_data.py` (112 lines)
- **Real-time ETF pricing** via yfinance with rate limiting
- **28 ETFs tracked** across AI, Defense, CleanTech, Nuclear, Volatility
- **Price change tracking** and volume analysis
- **Automatic retry logic** for failed price fetches

### 📧 Gmail Integration (Refactored)
**Primary Module:** `gmail_poller.py` (192 lines)
- **IMAP integration** for Google Alerts processing
- **Robust HTML parsing** with fallback mechanisms  
- **URL cleaning** and article extraction
- **Error handling** for malformed emails

### 📝 Notion Integration (Refactored)
**Primary Module:** `notion_reporter.py` (424 lines)
- **Comprehensive logging** with rich formatting
- **Cover image fetching** via Microlink API
- **Financial terminology** and risk assessments
- **Consolidated report formatting** with position recommendations

### 📊 Report Consolidation (New)
**Primary Module:** `report_consolidator.py` (124 lines)
- **Multi-analysis aggregation** from session articles
- **Conviction scoring** based on signal strength
- **Strong buy/sell recommendations** with entry prices
- **Watchlist generation** for medium-conviction signals

### 🎯 Main Orchestrator (Refactored)
**Primary Module:** `news_analyzer_refactored.py` (315 lines)
- **Clean module coordination** with dependency injection
- **Session-based analysis** for consolidated reporting
- **Alert batching integration** with smart notifications
- **Pattern detection** and memory integration

### 🧠 Contextual Memory (`market_memory.py`)
- **SQLite-backed** signal storage
- **Pattern detection** (streaks, reversals, volatility)
- **Contextual insights** based on historical signals
- **CLI management** via `marketman` command

### 📱 Smart Notifications (`alert_batcher.py`)
- **Intelligent batching** prevents alert fatigue
- **Sector-focused** ETF grouping
- **Rate limit protection** (Pushover: 7,500/month)
- **Queue management** with retry logic

## 🔧 Developer Guide

### Using Individual Modules

#### ETF Analysis
```python
from src.core.etf_analyzer import analyze_thematic_etf_news, generate_tactical_explanation
from src.core.etf_analyzer import categorize_etfs_by_sector

# Analyze a news article
result = analyze_thematic_etf_news(headline, summary, snippet)

# Generate tactical explanation for high-confidence signals
explanation = generate_tactical_explanation(result, headline)

# Categorize ETFs by sector
focused_etfs, primary_sector = categorize_etfs_by_sector(['BOTZ', 'ROBO', 'ICLN'])
```

#### Market Data
```python
from src.core.market_data import get_etf_prices

# Get current prices for specific ETFs
prices = get_etf_prices(['BOTZ', 'ROBO', 'ICLN'])

# Get all major ETFs (28 tracked)
all_prices = get_etf_prices()
```

#### Gmail Integration
```python
from src.core.gmail_poller import GmailPoller

# Poll for new Google Alerts
poller = GmailPoller()
alerts = poller.get_google_alerts()
```

#### Consolidated Reporting
```python
from src.core.report_consolidator import create_consolidated_signal_report

# Create consolidated report from multiple analyses
report = create_consolidated_signal_report(analyses, timestamp)
```

#### Notion Integration
```python
from src.core.notion_reporter import NotionReporter

# Log analysis to Notion
reporter = NotionReporter()
success = reporter.log_consolidated_report_to_notion(report_data)
```

### Running Different Versions

#### Refactored System (Recommended)
```bash
# Normal operation
python -m src.core.news_analyzer_refactored

# Test mode
python -m src.core.news_analyzer_refactored test

# Debug mode
python -m src.core.news_analyzer_refactored --debug test
```

#### Legacy System (Still Functional)
```bash
# Normal operation
python src/core/news_gpt_analyzer.py

# Test mode
python src/core/news_gpt_analyzer.py test

# Debug mode
python src/core/news_gpt_analyzer.py --debug test
```

### Module Testing

Individual modules can be tested independently:

```bash
# Test ETF analysis
python -c "from src.core.etf_analyzer import analyze_thematic_etf_news; print('✅ ETF Analyzer ready')"

# Test market data
python -c "from src.core.market_data import get_etf_prices; print('✅ Market Data ready')"

# Test Gmail integration  
python -c "from src.core.gmail_poller import GmailPoller; print('✅ Gmail Poller ready')"

# Test Notion integration
python -c "from src.core.notion_reporter import NotionReporter; print('✅ Notion Reporter ready')"

# Test report consolidation
python -c "from src.core.report_consolidator import create_consolidated_signal_report; print('✅ Report Consolidator ready')"
```

## �️ Command Line Tools

### Main CLI (`./bin/marketman`)
```bash
# Test components
./bin/marketman test --pushover
./bin/marketman test --all

# System monitoring
./bin/marketman monitor --system --loop 60
./bin/marketman monitor --news --loop 30

# Memory management  
./bin/marketman memory --stats
./bin/marketman memory --cleanup --days 30
./bin/marketman memory --patterns ITA

# Manual notifications
./bin/marketman send "Market update" --priority 1
```

### Alert Management (`./bin/marketman-alerts`)
```bash
# Queue status
./bin/marketman-alerts stats
./bin/marketman-alerts pending

# Process batches
./bin/marketman-alerts process

# Test batching
./bin/marketman-alerts test

# Configuration
./bin/marketman-alerts config
```

### System Monitor (`src/monitoring/marketman_monitor.py`)
```bash
# Combined system + market monitoring
python src/monitoring/marketman_monitor.py --loop 30

# Individual components
python src/monitoring/marketman_monitor.py --system-only
python src/monitoring/marketman_monitor.py --news-only
```

## 📈 Typical Workflows

### Day Trader Setup
```bash
# Smart batching with 15-minute processing
ALERT_STRATEGY=smart_batch
echo "*/15 * * * * cd /root/marketMan && ./bin/marketman-alerts process" | crontab -
```

### Multiple Keywords Monitoring
```bash
# Time-based batching for high volume
ALERT_STRATEGY=time_window  
echo "*/15 * * * * cd /root/marketMan && ./bin/marketman-alerts process" | crontab -
```

### Long-term Investor
```bash
# Daily market digest
ALERT_STRATEGY=daily_digest
echo "0 8 * * * cd /root/marketMan && ./bin/marketman-alerts process" | crontab -
```

## 🎯 Alert Examples

### Single Alert (High Confidence)
```
↗ BULLISH Signal (9/10)

Clean Energy Bill Passes Senate Committee...

Reason: Bipartisan legislation unlocks $50B investment
ETFs: ICLN, TAN, QCLN
```

### Batched Alerts
```
🎯 Market Batch Update (4 signals)

Signals: ↗ 3 Bullish | ↘ 1 Bearish

🔥 High Confidence Alerts:
• Bullish Clean Energy: Infrastructure spending approved...
• Bullish Electric Vehicles: Tesla earnings beat...

📈 Sectors Active:
• Clean Energy: ICLN, TAN, QCLN
• Electric Vehicles: LIT, DRIV, ARKQ
```

## 🏗️ Architecture Overview

**Recently Refactored!** MarketMan has been transformed from a monolithic system into a clean, modular architecture for enhanced maintainability and extensibility.


## 🗂️ Project Structure

```
marketMan/
├── 🤖 Core Analysis (src/core/) - REFACTORED ARCHITECTURE
│   ├── news_analyzer_refactored.py  # Main orchestrator (315 lines)
│   ├── etf_analyzer.py             # AI analysis engine (254 lines)
│   ├── market_data.py              # ETF price fetching (112 lines)
│   ├── gmail_poller.py             # Gmail integration (192 lines)
│   ├── notion_reporter.py          # Notion API integration (424 lines)
│   ├── report_consolidator.py      # Consolidated reporting (124 lines)
│   ├── news_gpt_analyzer.py        # Legacy monolithic file (1,630 lines)
│   ├── market_memory.py            # Contextual memory system
│   └── alert_batcher.py            # Smart batching system
│
├── 🔗 Integrations (src/integrations/)
│   ├── pushover_utils.py           # Notification utilities
│   ├── notion_setup_enhanced.py   # Notion database setup
│   └── deepseek_integration.py    # AI model integration
│
├── 📊 Monitoring (src/monitoring/)
│   └── marketman_monitor.py        # Combined system monitoring
│
├── 🛠️ Command Line Tools (bin/)
│   ├── marketman                   # Main CLI tool
│   ├── marketman-alerts            # Queue management CLI
│   └── run_analyzer.sh             # Analysis runner script
│
├── ⚙️ Setup & Configuration (setup/)
│   ├── notion_setup.py             # Basic Notion setup
│   ├── setup.sh                   # System setup script
│   └── requirements.txt            # Python dependencies
│
├── 🧪 Tests (tests/)
│   ├── test_contextual.py          # Memory system tests
│   ├── test_fixes.py              # Bug fix tests
│   ├── test_real_context.py       # Integration tests
│   └── test_setup.py              # Setup validation tests
│
├── 📚 Documentation
│   ├── README.md                   # This comprehensive guide
│   ├── REFACTORING_SUMMARY.md      # Architecture refactoring details
│   ├── ALERT_BATCHING_GUIDE.md
│   ├── BATCHING_IMPLEMENTATION_SUMMARY.md
│   └── CONTEXTUAL_MEMORY_COMPLETE.md
│
├── 💾 Data Storage (data/)
│   ├── marketman_memory.db         # Memory patterns (SQLite)
│   ├── alert_batch.db              # Alert queue (SQLite)
│   └── debug_email.html            # Debug files
│
├── 📋 Examples (examples/)
│   ├── create_digest_dashboard.py
│   └── create_digest_dashboard_simple.py
│
├── 🔧 Configuration (config/)
│   ├── .env.example               # Environment template
│   └── marketman.service          # Systemd service
│
├── .env                           # Environment variables
├── requirements.txt               # Python dependencies
└── README.md                     # This file
```

##  Recent Updates

### ✅ Conviction System Overhaul (June 2025)
- **Fixed Misleading Labels**: No more "HIGH CONVICTION BUYS" with 1.5/10 scores
- **Tiered System**: TACTICAL (< 1.5) → MEDIUM (1.5-2.5) → HIGH CONVICTION (2.5+)
- **Dynamic Position Sizing**: 1-2% tactical → 2-3% medium → 3-5% high conviction
- **Enhanced Narratives**: Macro context and specific inverse tickers for tactical sells
- **Trader Dashboard Style**: Quick signals with execution timeframes and urgency levels
- **Inverse Ticker Mapping**: Specific hedge recommendations (FAZ for XLF, SQQQ for QQQ, etc.)

### ✅ Architecture Refactoring (June 2025)
- **Modular Design**: Broke down 1,630-line monolithic file into 6 focused modules
- **Enhanced Maintainability**: 87% reduction in individual file complexity
- **Better Testing**: Individual modules can be tested independently
- **Cleaner Dependencies**: Clear separation of concerns
- **Preserved Functionality**: 100% backward compatibility maintained

### ✅ Key Features
- **Consolidated Reporting**: Multiple Google Alerts aggregated into single actionable reports
- **Financial Rigor**: Professional terminology, entry prices, stop-losses, profit targets
- **Hero Images**: Automatic cover image fetching for visually appealing Notion cards
- **Risk Assessment**: Comprehensive risk warnings and position sizing guidance
- **Pattern Memory**: Contextual insights based on historical market patterns

## 🚀 Migration Guide

### From Legacy to Refactored System

**Option 1: Use Refactored System (Recommended)**
```bash
# Replace this
python src/core/news_gpt_analyzer.py

# With this
python -m src.core.news_analyzer_refactored
```

**Option 2: Gradual Migration**
```bash
# Both systems work in parallel
python src/core/news_gpt_analyzer.py          # Legacy
python -m src.core.news_analyzer_refactored   # Refactored
```

**Option 3: Individual Module Usage**
```python
# Import specific functionality
from src.core.etf_analyzer import analyze_thematic_etf_news
from src.core.market_data import get_etf_prices
from src.core.report_consolidator import create_consolidated_signal_report
```

### Benefits of Migration
- **Better Performance**: Modular architecture reduces memory footprint
- **Easier Debugging**: Issues isolated to specific modules
- **Enhanced Features**: New consolidated reporting and improved formatting
- **Future-Proof**: Easier to add new features and integrations

## 🎯 Summary

MarketMan is a production-ready, professional ETF market intelligence system that has evolved from a simple alert processor into a sophisticated, modular trading platform. With its recent architectural refactoring, the system now offers:

### ✅ Core Capabilities
- **AI-Powered Analysis**: GPT-4 driven ETF signal extraction from Google Alerts
- **Smart Notifications**: Intelligent batching prevents alert fatigue
- **Contextual Memory**: Pattern detection and historical market insights
- **Professional Reporting**: Notion integration with tactical recommendations
- **Real-Time Data**: Live ETF prices and market snapshots
- **Modular Architecture**: Clean, maintainable, and extensible codebase

### 🎯 Target Users
- **Active ETF Traders**: High-frequency thematic ETF opportunities
- **Portfolio Managers**: Institutional-grade analysis and reporting
- **Quantitative Analysts**: Pattern detection and systematic signals
- **Financial Advisors**: Client-ready market intelligence reports

### 🚀 Getting Started
1. **Clone and Install**: `git clone` → `pip install -r requirements.txt`
2. **Configure APIs**: Set up `.env` with Gmail, OpenAI, Pushover, Notion
3. **Test System**: `python -m src.core.news_analyzer_refactored test`
4. **Start Monitoring**: `python -m src.core.news_analyzer_refactored`