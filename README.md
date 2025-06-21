# 📧 MarketMan v2.0: Automated News & System Monitor

An AI-powered system that monitors energy sector news and your infrastructure, delivering unified Pushover alerts with professional coaching insights and real-time market data.

## 🚀 Features

- **📧 Gmail Integration**: Automated Google Alerts via IMAP
- **🤖 Coach Alex Analysis**: AI-powered energy sector signal detection with professional coaching tone
- **💰 Real-Time Prices**: Live ETF price integration via yfinance
- **🖥️ System Monitoring**: Server ping monitoring (like yang.prox)
- **📱 Enhanced Alerts**: Rich Pushover notifications with images and strategic insights
- **📊 Smart Filtering**: Energy companies, renewables, oil & gas focus with confidence scoring
- **🗃️ Visual Notion Logging**: Analysis results with article images and clickable links
- **🎯 ETF Focus**: XLE, ICLN, TAN, QCLN, PBW recommendations with live pricing
- **⚡ CLI Interface**: Easy testing, monitoring, and deployment

## 🚀 What's New in v2.0

### ✅ **Professional Coaching Analysis**
- **Coach Alex**: 15+ years energy markets strategist persona
- **Strategic Framework**: Market impact, price action, strategic advice, risk factors
- **Real-Time Context**: Live ETF prices integrated into analysis
- **Professional Tone**: Actionable guidance with confident, strategic perspective

### ✅ **Rich Visual Experience**
- **Microlink Integration**: Auto-fetches article preview images and screenshots
- **Notion Cover Images**: Each analysis gets a visual preview in the database
- **Pushover Image Attachments**: Notifications include article images (when available)
- **Enhanced Notifications**: Professional coaching insights with live market data

### ✅ **Unified Pushover System**
- Reusable `pushover_utils.py` matching proven server monitor patterns
- Smart energy alerts with auto-formatting and priorities
- System alerts compatible with existing yang.prox workflow
- Clean notification links to Notion analysis pages

### ✅ **Enhanced Architecture** 
- Modular design with clear separation of concerns
- Production-ready error handling and recovery
- Clean, professional logging with debug mode
- Systemd service support for automated deployment

## 🛠️ Technical Implementation

### **Key Functions & Features**
1. **`get_microlink_image(url)`** - Fetches article preview images and screenshots
2. **`get_etf_prices(symbols)`** - Real-time ETF price fetching with yfinance
3. **Enhanced `log_to_notion()`** - Adds cover images to Notion pages
4. **Enhanced `send_pushover_notification()`** - Image attachments and rich formatting
5. **`analyze_energy_news()`** - Coach Alex strategic analysis with market context

### **Smart Features**
- ⏱️ **Timeout Protection**: 10-second limits prevent hanging
- 📏 **Size Limits**: Respects Pushover 2.5MB image limit  
- 🔄 **Fallback Logic**: Multiple image sources (screenshot/image/logo)
- 🛡️ **Error Handling**: Graceful degradation if images or prices fail
- 🔍 **Smart Filtering**: AI filters out non-energy content automatically
- 💰 **Rate Limiting**: Prevents Yahoo Finance API overuse

### **Professional Output Example**
```
🎯 MARKETMAN - HIGH ALERT

📈 Bullish Signal (8/10)

📰 SITUATION:
Solar Industry Sees Record Q3 Growth as Federal Tax Credits Extended

💡 STRATEGIC ANALYSIS:
The extension of federal tax credits and falling panel costs are driving significant growth in solar installations, indicating strong future demand.

📊 LIVE MARKET DATA:
• XLE: $88.98 (+1.02%) 📈
• ICLN: $12.63 (-0.55%) 📉
• TAN: $32.05 (-1.35%) 📉

🧠 COACH'S PERSPECTIVE:
Stay focused on the long-term growth trajectory of the solar sector, leveraging policy support and technological advancements.

🎯 STRATEGIC GUIDANCE:
Consider increasing exposure to solar and clean energy ETFs like TAN and ICLN as they are poised to benefit from favorable policy conditions.

🎯 FOCUS ETFs: TAN, ICLN, QCLN, PBW
```

## 🛠️ Quick Setup

### 1. Install Dependencies
```bash
chmod +x setup.sh
./setup.sh
```

### 2. Configure Environment
Copy `.env.example` to `.env` and add your credentials:
```env
# Required
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=your-gmail-app-password
OPENAI_API_KEY=sk-your-openai-key

# Optional (for mobile alerts)
PUSHOVER_TOKEN=your-pushover-app-token
PUSHOVER_USER=your-pushover-user-key

# Optional (for data logging)
NOTION_TOKEN=secret_your-notion-integration-token
NOTION_DATABASE_ID=your-database-id
```

### 3. Test Your Setup
```bash
# Test everything
./marketman test --all

# Test specific components
./marketman test --pushover
./marketman test --notion
./marketman test --gmail
```

### 4. Set Up Google Alerts
Create alerts for energy keywords:
- "energy stocks", "solar energy", "renewable energy"
- "oil prices", "clean energy", "XLE ETF", "ICLN ETF"

## 📱 Pushover Integration (Production-Ready)

The unified `pushover_utils.py` follows proven server monitor patterns:

```python
from pushover_utils import send_energy_alert, send_system_alert

# Energy alerts (auto-formatted with emojis and priorities)
send_energy_alert(
    signal="Bearish", confidence=8,
    title="Solar Stocks Plummet",
    reasoning="Budget cuts affect sector",
    etfs=["TAN", "ICLN"],
    article_url="https://notion.so/page-url"  # Links to Notion analysis
)

# System alerts (matches your existing yang.prox style)
send_system_alert("yang.prox", "DOWN", "Host unreachable")
```

## 🏃‍♂️ Usage

### CLI Commands (Recommended)
```bash
# Quick testing
./marketman test --pushover            # Test notifications
./marketman test --all                 # Test everything

# Monitoring runs
./marketman monitor                    # Combined news + system monitoring
./marketman monitor --news             # News analysis only
./marketman monitor --system           # System monitoring only
./marketman monitor --loop 15          # Continuous every 15 minutes

# Manual actions
./marketman send "Custom alert" --priority 1  # Send manual alert
./marketman service install            # Install systemd service
./marketman service start              # Start background service
```

### Direct Python (Alternative)
```bash
python news_gpt_analyzer.py           # News analysis only
python marketman_monitor.py --loop 15 # Combined monitoring
```

### Production Deployment
```bash
# Install as systemd service
./marketman service install
./marketman service start
./marketman service status

# Monitor logs
journalctl -f -u marketman
```

## ⚙️ Detailed Setup Guide

### Gmail Configuration
1. **Enable 2FA** on your Gmail account
2. **Generate App Password**:
   - Google Account settings → Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
3. **Add to .env**: `GMAIL_APP_PASSWORD=your-16-char-password`

### Pushover Setup (Optional)
1. Create account at [pushover.net](https://pushover.net)
2. Create new application, get API token
3. Add to .env: `PUSHOVER_TOKEN` and `PUSHOVER_USER`

### Notion Setup (Optional)
```bash
# Automated setup with image support
python notion_setup.py --test              # Test existing
python notion_setup.py --create            # Create new database with Image property
python notion_setup.py --create --page-id "your-page-id" --auto  # Automated
```

**Database includes:**
- Title, Signal, Confidence, ETFs, Reasoning, Timestamp, Link
- **NEW**: Cover images and Image URL property for visual previews
- **NEW**: Enhanced database structure for better organization

## 📊 How It Works

### News Analysis Flow
1. **Fetch**: Polls Gmail for Google Alert emails
2. **Extract**: Parses article titles, summaries, and links
3. **🖼️ Image Fetch**: Uses Microlink API to get article preview images
4. **Analyze**: GPT-4 evaluates energy sector relevance and signals
5. **Filter**: Only processes confidence ≥7 signals
6. **📱 Rich Alert**: Sends Pushover notification with image and Notion link
7. **📊 Visual Log**: Stores analysis in Notion with cover image and structured data

### Output Format
```json
{
  "relevance": "financial",
  "sector": "Energy", 
  "signal": "Bearish",
  "confidence": 8,
  "affected_etfs": ["XLE", "TAN"],
  "reasoning": "Solar subsidies cut, affecting TAN ETF outlook",
  "market_impact": "Short-term bearish pressure on solar stocks",
  "image_url": "https://iad.microlink.io/article-preview.png"
}
```

### Alert Thresholds
- **Confidence ≥7**: Pushover alert + Notion logging
- **Confidence ≥8**: High-priority alert
- **All relevant**: Console logging

## 🐛 Common Issues & Solutions

### Gmail Connection Problems
- **App Password**: Use Gmail App Password, not account password
- **2FA Required**: Enable 2-Step Verification first
- **IMAP Access**: Ensure IMAP is enabled in Gmail settings

### No Alerts Found
- **Google Alerts**: Verify alerts are set up and arriving
- **Email Filters**: Check spam folder and Gmail filters
- **Keywords**: Use energy-specific terms for better results

### API Errors
- **OpenAI Credits**: Check API key has sufficient balance
- **Rate Limits**: Built-in retry logic handles temporary failures
- **Network**: Verify internet connectivity

### Notion Issues
```bash
# Test Notion setup
python notion_setup.py --test

# Common fixes
# 1. Share database with your integration
# 2. Check integration permissions
# 3. Verify database ID is correct
```

### Pushover Not Working
```bash
# Test Pushover
./marketman test --pushover

# Verify credentials in .env file
# Check Pushover app is active
```

## 🔧 Advanced Configuration

### Alternative AI Providers
```python
# Switch to DeepSeek (modify analyze_energy_news function)
response = requests.post(
    "https://api.deepseek.com/v1/chat/completions",
    headers={"Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}"},
    json={
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1
    }
)
```

### Custom Monitoring Targets
Edit `marketman_monitor.py` to add your servers:
```python
SERVERS = [
    "yang.prox",
    "your-server.com",
    "192.168.1.100"
]
```

### Automated Deployment
```bash
# Install as systemd service
sudo ./marketman service install

# Alternative: cron job
echo "*/15 * * * * cd /root/marketMan && ./marketman monitor" | crontab -
```

## � What's New in v2.0

### ✅ **Unified Pushover System**
- Reusable `pushover_utils.py` matching your proven server monitor pattern
- Smart energy alerts with auto-formatting and priorities
- System alerts compatible with existing yang.prox workflow
- Clean notification links to Notion analysis pages (no more messy Google redirects)

### ✅ **Enhanced Architecture** 
- Modular design with clear separation of concerns
- Production-ready error handling and recovery
- CLI interface for easy management and testing
- Systemd service support for automated deployment

### ✅ **Bug Fixes Applied**
- **Non-Energy Filtering**: AI now skips irrelevant content (Mode Mobile, etc.)
- **JSON Parsing**: Improved consistency with better prompts and error handling
- **UI Element Noise**: Filters out "Flag as irrelevant" and other Google Alert UI
- **Notion Integration**: Graceful degradation when database isn't configured
- **Article Extraction**: Better regex patterns for current Google Alert HTML
- **🔗 Google URL Cleaning**: Automatically extracts real URLs from Google redirects
- **🖼️ Image Integration**: Cover images work without requiring new database properties
- **📱 Rich Notifications**: Pushover gets clean URLs and working image attachments

### ✅ **Key Improvements**
- Early .env validation with helpful error messages
- Duplicate database prevention in Notion setup
- Auto-updating .env files with new database IDs
- Comprehensive testing suite with `--test` commands
- Better logging with debug information for troubleshooting

## 📚 Dependencies

Core requirements automatically installed by `setup.sh`:
- `openai` - GPT-4 API integration
- `python-dotenv` - Environment management  
- `requests` - HTTP requests
- `imaplib`, `email` - Gmail integration (built-in)

## 🔄 Future Enhancements

- **Multiple AI Providers**: Claude, DeepSeek, local LLMs
- **Portfolio Integration**: Brokerage API connections
- **Advanced Analytics**: Backtesting and accuracy metrics
- **Team Notifications**: Slack/Discord integration
- **Risk Management**: Position sizing recommendations
- **Extended Asset Coverage**: Commodities, crypto, bonds analysis

---

## 📖 Quick Reference

```bash
# Setup
./setup.sh && cp .env.example .env
# Edit .env with your credentials

# Test system
./marketman test --all

# Run with rich media
./marketman monitor --loop 15

# Deploy
./marketman service install && ./marketman service start
```

**🎯 You now have a production-ready system with rich visual notifications and professional coaching insights - like having your own hedge fund analysis team!**
