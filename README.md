# 🚀 MarketMan

**Enterprise ETF Market Intelligence & Alert System**

MarketMan transforms Google Alerts into actionable ETF trading signals using AI, contextual memory, and intelligent batching. Built for professional and enterprise-level thematic ETF investors who demand precision, reliability, and extensibility.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Architecture](https://img.shields.io/badge/Architecture-Modular-brightgreen.svg)

---

## 📚 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Command Line Interface](#command-line-interface)
- [Alert Batching & Notification](#alert-batching--notification)
- [Performance Dashboard](#performance-dashboard)
- [Notion Integration](#notion-integration)
- [Pipeline & Conviction Calculation](#pipeline--conviction-calculation)
- [Cron & Automation](#cron--automation)
- [Testing & Validation](#testing--validation)
- [Project Structure](#project-structure)
- [Enterprise Benefits](#enterprise-benefits)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

MarketMan is a modular, extensible platform for transforming unstructured market news into actionable ETF trading signals. It leverages AI, robust data pipelines, and enterprise-grade integrations to deliver timely, high-confidence alerts and performance tracking.

---

## Architecture

- **Modular Python 3.8+ codebase**
- **Core pipeline**: News ingestion → AI analysis → ETF filtering → Conviction scoring → Alert batching → Notion/Push delivery
- **Extensible integrations**: Gmail, Notion, Pushover, custom dashboards
- **CLI-first**: All operations are accessible via robust command-line tools

---

## Features

- **AI-powered ETF signal extraction** from Google Alerts
- **Contextual memory** for pattern detection and historical insights
- **Real-time ETF data** and technical checks
- **Smart batching** to prevent notification fatigue
- **Enterprise Notion integration** for logging, tracking, and workflow automation
- **Performance dashboard** for trade execution and P&L monitoring
- **Professional mobile notifications** via Pushover

---

## Quick Start

```bash
git clone <repository>
cd marketMan
pip install -r requirements.txt
cp .env.example .env  # Edit with your API keys
chmod +x bin/marketman bin/marketman-alerts bin/gmail-organizer
```

### Notion Database Setup

```bash
python setup/notion_setup_enhanced.py
```

### Run Tests

```bash
./bin/marketman test
```

### Run Analysis

```bash
./bin/marketman run
```

---

## Configuration

Edit `.env` with your credentials:

```env
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password
OPENAI_API_KEY=sk-...
NOTION_TOKEN=ntn_...
NOTION_DATABASE_ID=...
TRADES_DATABASE_ID=...
PERFORMANCE_DATABASE_ID=...
PUSHOVER_TOKEN=...
PUSHOVER_USER=...
ALERT_STRATEGY=smart_batch
```

---

## Command Line Interface

All major operations are available via `bin/marketman`:

- `./bin/marketman run` — Run main analysis
- `./bin/marketman test` — Run all tests
- `./bin/marketman monitor` — Run monitoring
- `./bin/marketman setup --notion` — Setup Notion
- `./bin/marketman memory` — Memory operations
- `./bin/marketman send "Message"` — Send manual alert

Other scripts:
- `./bin/marketman-alerts` — Alert batching and queue management
- `./bin/gmail-organizer` — Gmail integration and cleanup

---

## Alert Batching & Notification

- **Batching strategies**: `immediate`, `smart_batch`, `time_window`, `daily_digest`
- **Pushover integration**: High-confidence alerts delivered to mobile devices
- **Alert queue management**: View, process, and audit alert batches

---

## Performance Dashboard

- **Automatic trade logging** to Notion databases
- **Customizable schemas** for trades and performance
- **Validation and error handling** for robust operation

---

## Notion Integration

- **Rich, trader-friendly reports** with average confidence, liquidity context, and actionable next steps
- **Clean sector classification** using AI, not raw search terms
- **Automated and manual logging** of signals, trades, and performance

---

## Pipeline & Conviction Calculation

- **Frequency-based ETF filtering**: Only ETFs with multiple high-confidence mentions are recommended
- **Specialized ETF prioritization**: Focus on pure-play thematic opportunities
- **Technical overextension filter**: Avoids FOMO entries
- **Per-ETF conviction calculation**: Accurate, defensible metrics for each ETF
- **Defensive validation and logging**: Ensures reliability and transparency

---

## Cron & Automation

- **Helper scripts** for installing and managing cron jobs
- **Recommended schedules** for high-frequency and conservative trading
- **Automated memory cleanup** and system health checks

---

## Testing & Validation

- **Comprehensive test suite**: Run with `./bin/marketman test`
- **Unit, integration, and formatting tests** for all major features
- **Continuous validation** of Notion and performance dashboard integrations

---

## Project Structure

```
bin/                # CLI entry points
config/             # Environment and service configs
data/               # Databases and persistent data
docs/               # Documentation (see this README)
setup/              # Setup scripts
src/                # Core source code (modular)
tests/              # Test suite
logs/               # Log files
```

---

## Enterprise Benefits

- **Scalable, modular architecture** for easy extension and integration
- **Robust error handling** and defensive coding practices
- **Professional documentation and CLI tools**
- **Ready for deployment in production and enterprise environments**

---

## Contributing

Contributions are welcome! Please open issues or pull requests for improvements, bug fixes, or new features.

---

## License

MIT License

---

This README replaces the need for all other markdown documentation files.  
For further details, see the code and CLI help.