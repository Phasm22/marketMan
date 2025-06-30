# Troubleshooting Guide

Common issues and solutions for MarketMan.

## 📋 Table of Contents

- [Common Issues](#common-issues)
- [Configuration Problems](#configuration-problems)
- [API Issues](#api-issues)
- [Database Issues](#database-issues)
- [Performance Issues](#performance-issues)
- [Integration Issues](#integration-issues)
- [Getting Help](#getting-help)

## 🚨 Common Issues

### "ModuleNotFoundError: No module named 'src'"

**Problem**: Python can't find the MarketMan modules.

**Solution**: Ensure you're running from the project root directory.

```bash
# Make sure you're in the marketMan directory
cd /path/to/marketMan

# Run commands from project root
python marketman news status
```

### "Configuration file not found"

**Problem**: MarketMan can't find the configuration file.

**Solution**: Create the required configuration files.

```bash
# Create settings.yaml if it doesn't exist
cp config/settings.yaml.example config/settings.yaml

# Edit with your API keys
nano config/settings.yaml
```

### "Database file not found"

**Problem**: Database files don't exist.

**Solution**: Initialize the database.

```bash
# Create data directory
mkdir -p data

# Initialize database
python -c "from src.core.database.db_manager import DatabaseManager; db = DatabaseManager('data/marketman.db'); db.init_database()"
```

## ⚙️ Configuration Problems

### Missing API Keys

**Problem**: "Missing required API key" errors.

**Solution**: Add API keys to `config/settings.yaml`.

```yaml
# Edit config/settings.yaml:
openai:
  api_key: your_openai_key_here

finnhub:
  api_key: your_finnhub_key_here

newsapi:
  api_key: your_newsapi_key_here

newdata:
  api_key: your_newdata_key_here
```

### Invalid Configuration Values

**Problem**: Configuration validation fails.

**Solution**: Check configuration values.

```bash
# Validate configuration
python marketman config validate

# Show current configuration
python marketman config show
```

### Configuration File Permissions

**Problem**: "Permission denied" when reading config files.

**Solution**: Fix file permissions.

```bash
# Fix permissions
chmod 644 config/settings.yaml
chmod 644 config/strategies.yaml
chmod 644 config/brokers.yaml

# Ensure readable by the user running MarketMan
chown $USER:$USER config/*.yaml
```

## 🔌 API Issues

### Rate Limit Exceeded

**Problem**: "API rate limit exceeded" errors.

**Solution**: Reduce API call limits in `config/settings.yaml`.

```yaml
# Reduce API limits:
news_ingestion:
  max_daily_headlines: 25        # Reduce from 50
  max_daily_ai_calls: 50         # Reduce from 75
```

### Invalid API Keys

**Problem**: "Authentication failed" or "Invalid API key" errors.

**Solution**: Verify API keys are correct.

```bash
# Test API connectivity
python marketman news test

# Check specific API
python -c "
import requests
response = requests.get('https://finnhub.io/api/v1/quote?symbol=AAPL&token=YOUR_KEY')
print('Status:', response.status_code)
print('Response:', response.text[:200])
"
```

### Network Connectivity Issues

**Problem**: "Connection timeout" or "Network unreachable" errors.

**Solution**: Check network connectivity.

```bash
# Test internet connectivity
ping 8.8.8.8

# Test API endpoints
curl -I https://finnhub.io/api/v1/quote?symbol=AAPL
curl -I https://newsapi.org/v2/everything
```

### OpenAI API Issues

**Problem**: "OpenAI API error" or "Insufficient credits" errors.

**Solution**: Check OpenAI account and billing.

```bash
# Check OpenAI API key
python -c "
import openai
openai.api_key = 'your_key_here'
try:
    response = openai.chat.completions.create(
        model='gpt-4',
        messages=[{'role': 'user', 'content': 'Hello'}],
        max_tokens=10
    )
    print('OpenAI API working')
except Exception as e:
    print('OpenAI API error:', e)
"
```

## 🗄️ Database Issues

### Database Locked

**Problem**: "Database is locked" errors.

**Solution**: Check for other processes using the database.

```bash
# Check for processes using the database
lsof data/marketman.db

# Kill processes if needed
pkill -f marketman

# Or restart the system
sudo systemctl restart marketman
```

### Database Corruption

**Problem**: "Database disk image is malformed" errors.

**Solution**: Restore from backup or reinitialize.

```bash
# Backup current database
cp data/marketman.db data/marketman_backup_$(date +%Y%m%d_%H%M%S).db

# Reinitialize database
rm data/marketman.db
python -c "from src.core.database.db_manager import DatabaseManager; db = DatabaseManager('data/marketman.db'); db.init_database()"
```

### Insufficient Disk Space

**Problem**: "No space left on device" errors.

**Solution**: Free up disk space.

```bash
# Check disk usage
df -h

# Clean up old logs
find logs/ -name "*.log" -mtime +7 -delete

# Clean up old database backups
find data/ -name "marketman_backup_*.db" -mtime +30 -delete
```

### Database Permissions

**Problem**: "Permission denied" when accessing database.

**Solution**: Fix database file permissions.

```bash
# Fix database permissions
chmod 644 data/marketman.db
chown $USER:$USER data/marketman.db

# Ensure data directory is writable
chmod 755 data/
chown $USER:$USER data/
```

## ⚡ Performance Issues

### High Memory Usage

**Problem**: System becomes slow or crashes due to high memory usage.

**Solution**: Optimize memory usage in `config/settings.yaml`.

```yaml
# Reduce memory usage:
news_ingestion:
  max_daily_headlines: 25        # Reduce from 50
  batch_size: 5                  # Reduce from 10

# Optimize database
database:
  backup_enabled: false          # Disable if not needed
  cleanup_old_records: true      # Enable cleanup
```

### Slow Processing

**Problem**: News processing or signal generation is very slow.

**Solution**: Optimize processing settings.

```yaml
# Optimize for speed:
news_ingestion:
  batch_size: 15                 # Increase batch size
  min_relevance_score: 0.2       # Increase threshold

alerts:
  batch_strategy: immediate      # Use immediate instead of smart_batch
```

### High CPU Usage

**Problem**: System uses excessive CPU resources.

**Solution**: Reduce processing load.

```yaml
# Reduce CPU usage:
news_ingestion:
  max_daily_ai_calls: 25         # Reduce AI calls
  batch_size: 3                  # Smaller batches

# Disable unused features
options_scalping:
  enabled: false                 # Disable if not using
```

## 🔗 Integration Issues

### Pushover Notifications Not Working

**Problem**: Pushover notifications not being sent.

**Solution**: Check Pushover configuration.

```bash
# Test Pushover connectivity
python src/monitoring/marketman_monitor.py --test

# Check configuration
python -c "
import yaml
with open('config/settings.yaml') as f:
    config = yaml.safe_load(f)
print('Pushover token:', config.get('pushover', {}).get('token', 'NOT_SET'))
print('Pushover user:', config.get('pushover', {}).get('user_key', 'NOT_SET'))
"
```

### Notion Integration Issues

**Problem**: Notion integration not working.

**Solution**: Check Notion configuration and permissions.

```bash
# Test Notion connectivity
python -c "
import yaml
from src.integrations.notion_reporter import NotionReporter

with open('config/settings.yaml') as f:
    config = yaml.safe_load(f)

notion_config = config.get('notion', {})
if notion_config.get('token') and notion_config.get('database_id'):
    try:
        reporter = NotionReporter(notion_config)
        print('Notion integration configured')
    except Exception as e:
        print('Notion error:', e)
else:
    print('Notion not configured')
"
```

### Fidelity Integration Issues

**Problem**: Fidelity trade import not working.

**Solution**: Check Fidelity credentials and setup.

```bash
# Test Fidelity setup
python marketman journal setup-fidelity --email your@email.com

# Check Fidelity configuration
python -c "
import yaml
with open('config/settings.yaml') as f:
    config = yaml.safe_load(f)
fidelity_config = config.get('fidelity', {})
print('Fidelity email:', fidelity_config.get('email', 'NOT_SET'))
"
```

### Gmail Integration Issues

**Problem**: Gmail organization not working.

**Solution**: Check Gmail API credentials.

```bash
# Test Gmail integration
python src/monitoring/marketman_monitor.py --gmail-only

# Check Gmail configuration
python -c "
import yaml
with open('config/settings.yaml') as f:
    config = yaml.safe_load(f)
gmail_config = config.get('gmail', {})
print('Gmail client ID:', gmail_config.get('client_id', 'NOT_SET'))
print('Gmail refresh token:', gmail_config.get('refresh_token', 'NOT_SET'))
"
```

## 🔍 Debugging

### Enable Verbose Logging

Enable detailed logging for troubleshooting:

```bash
# Enable verbose logging
python marketman --verbose news cycle

# Check log files
tail -f logs/marketman.log
tail -f logs/marketman_cli.log
```

### Test Individual Components

Test specific components to isolate issues:

```bash
# Test news sources
python marketman news test

# Test signal generation
python marketman signals run

# Test alert system
python marketman alerts check

# Test performance tracking
python marketman journal performance
```

### Check System Status

Get comprehensive system status:

```bash
# Check news system status
python marketman news status

# Check signal status
python marketman signals status

# Check alert status
python marketman alerts status

# Check configuration
python marketman config show
```

### Database Diagnostics

Check database health:

```bash
# Check database integrity
python -c "
import sqlite3
conn = sqlite3.connect('data/marketman.db')
cursor = conn.cursor()
cursor.execute('PRAGMA integrity_check')
result = cursor.fetchone()
print('Database integrity:', result[0])
conn.close()
"

# Check table sizes
python -c "
import sqlite3
conn = sqlite3.connect('data/marketman.db')
cursor = conn.cursor()
tables = ['news_items', 'signals', 'trades', 'alerts']
for table in tables:
    cursor.execute(f'SELECT COUNT(*) FROM {table}')
    count = cursor.fetchone()[0]
    print(f'{table}: {count} records')
conn.close()
"
```

## 📊 Performance Monitoring

### Monitor System Resources

Check system resource usage:

```bash
# Monitor CPU and memory
htop

# Monitor disk usage
df -h

# Monitor disk I/O
iotop

# Monitor network usage
iftop
```

### Monitor API Usage

Track API usage to avoid rate limits:

```bash
# Check API usage in logs
grep "API call" logs/marketman.log | tail -20

# Count API calls by type
grep "API call" logs/marketman.log | awk '{print $NF}' | sort | uniq -c
```

### Monitor Database Performance

Check database performance:

```bash
# Check database size
ls -lh data/marketman.db

# Check slow queries
grep "slow query" logs/marketman.log

# Monitor database locks
grep "database locked" logs/marketman.log
```

## 🆘 Getting Help

### Before Asking for Help

1. **Check this guide** for your specific issue
2. **Enable verbose logging** and check logs
3. **Test individual components** to isolate the problem
4. **Check configuration** with `python marketman config validate`
5. **Verify API keys** are correct and have sufficient credits

### Information to Include

When asking for help, include:

1. **Error message** (exact text)
2. **Command** that caused the error
3. **Log output** (with verbose logging enabled)
4. **Configuration** (sanitized, without API keys)
5. **System information** (OS, Python version)
6. **Steps to reproduce** the issue

### Example Help Request

```
Error: ModuleNotFoundError: No module named 'src.core.signals'

Command: python marketman signals run

Log output:
[verbose log output here]

Configuration:
[relevant config sections]

System: Ubuntu 20.04, Python 3.9.7

Steps:
1. Cloned repository
2. Installed requirements
3. Ran command from project root
4. Got error above
```

### Common Solutions Summary

| Issue | Quick Fix |
|-------|-----------|
| Module not found | Run from project root directory |
| Config not found | Create `config/settings.yaml` |
| Database errors | Initialize database with `db.init_database()` |
| API rate limits | Reduce limits in config |
| Permission errors | Fix file permissions |
| High memory usage | Reduce batch sizes and limits |
| Slow processing | Increase relevance thresholds |

---

**Next**: [User Guide](user-guide.md) for usage instructions 