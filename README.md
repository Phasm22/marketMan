# MarketMan Trading System

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

An AI-powered trading system combining real-time news analysis, sentiment detection, and technical analysis to generate actionable trading signals for ETFs and options.

## Quick Start

### Prerequisites
- Python 3.9+
- API key for OpenAI
- Pushover account (optional, for notifications)

### Installation
```bash
git clone <repository-url>
cd marketMan
pip install -r requirements.txt

cp .env.example .env
# Edit .env with your API keys

pre-commit install
```

### First Run
``` bash
python marketman config validate
python marketman news cycle
python marketman status
```
Key Features
	•	Multi-source news analysis
	•	AI-powered sentiment and signal generation
	•	Risk management (position sizing, stop-loss controls)
	•	Technical analysis with pattern recognition and indicators
	•	Configurable notifications via Pushover
	•	Trade performance tracking
	•	Modular, maintainable architecture

Core Commands

# News and signals
```bash
python marketman news cycle
python marketman signals run
python marketman alerts check
```
# System management
```bash
python marketman status
python marketman config validate
python marketman performance show
```
# Development
```bash
python marketman test
python marketman lint
```


License

MIT License

⸻
