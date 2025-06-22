# 🚀 MarketMan

**Professional ETF Market Intelligence & Alert System**

MarketMan transforms Google Alerts into actionable ETF trading signals using AI analysis, contextual memory, and intelligent batching. Built for serious thematic ETF investors who need precise, timely market intelligence without notification fatigue.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

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
./bin/marketman test --all
python src/core/news_gpt_analyzer.py test
```

### 5. Run Analysis
```bash
# Single run
python src/core/news_gpt_analyzer.py

# Continuous monitoring  
./bin/marketman monitor --loop 30

# Check alert queue
./bin/marketman-alerts stats
./marketman-alerts stats
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

### 🤖 AI Analysis Engine (`news_gpt_analyzer.py`)
- **GPT-4 powered** thematic ETF analysis
- **Sector categorization** (AI, Defense, Clean Energy, etc.)
- **Confidence scoring** (1-10 scale)
- **Real-time ETF pricing** via yfinance
- **Memory integration** for contextual insights

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

### � Notion Integration (`notion_setup_enhanced.py`)
- **Comprehensive logging** with analysis details
- **Memory insights** as toggle blocks
- **Action recommendations** (BUY/SELL/HOLD)
- **Cover images** from article previews

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

## 🗂️ Project Structure

```
marketMan/
├── 🤖 Core Analysis (src/core/)
│   ├── news_gpt_analyzer.py    # Main AI analysis engine
│   ├── market_memory.py        # Contextual memory system
│   └── alert_batcher.py        # Smart batching system
│
├── 🔗 Integrations (src/integrations/)
│   ├── pushover_utils.py       # Notification utilities
│   ├── notion_setup_enhanced.py # Notion database setup
│   └── deepseek_integration.py # AI model integration
│
├── 📊 Monitoring (src/monitoring/)
│   └── marketman_monitor.py    # Combined system monitoring
│
├── 🛠️ Command Line Tools (bin/)
│   ├── marketman               # Main CLI tool
│   ├── marketman-alerts        # Queue management CLI
│   └── run_analyzer.sh         # Analysis runner script
│
├── ⚙️ Setup & Configuration (setup/)
│   ├── notion_setup.py         # Basic Notion setup
│   ├── setup.sh               # System setup script
│   └── requirements.txt        # Python dependencies
│
├── 🧪 Tests (tests/)
│   ├── test_contextual.py      # Memory system tests
│   ├── test_fixes.py          # Bug fix tests
│   ├── test_real_context.py   # Integration tests
│   └── test_setup.py          # Setup validation tests
│
├── 📚 Documentation (docs/)
│   ├── ALERT_BATCHING_GUIDE.md
│   ├── BATCHING_IMPLEMENTATION_SUMMARY.md
│   └── CONTEXTUAL_MEMORY_COMPLETE.md
│
├── 💾 Data Storage (data/)
│   ├── marketman_memory.db     # Memory patterns (SQLite)
│   ├── alert_batch.db          # Alert queue (SQLite)
│   └── debug_email.html        # Debug files
│
├── 📋 Examples (examples/)
│   ├── create_digest_dashboard.py
│   └── create_digest_dashboard_simple.py
│
├── 🔧 Configuration (config/)
│   ├── .env.example           # Environment template
│   └── marketman.service      # Systemd service
│
├── .env                       # Environment variables
├── requirements.txt           # Python dependencies
└── README.md                 # This file
```
