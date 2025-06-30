# Troubleshooting Guide

Common issues and solutions for MarketMan.

## 📋 Table of Contents

- [Common Issues](#common-issues)
- [API Problems](#api-problems)
- [Configuration Issues](#configuration-issues)
- [Database Problems](#database-problems)
- [Performance Issues](#performance-issues)
- [Debugging](#debugging)
- [Getting Help](#getting-help)

## 🚨 Common Issues

### "ModuleNotFoundError: No module named 'src.core.alert_batcher'"

**Problem**: Import error when running MarketMan commands.

**Solution**:
```bash
# Check if the module exists
ls src/core/alert_batcher.py

# If missing, create the wrapper module
python -c "
from src.core.journal.alert_batcher import *
import sys
sys.path.insert(0, 'src/core')
"

# Or reinstall the package
pip install -e .
```

**Prevention**: Always run `python marketman config validate` after installation.

### "Configuration validation failed"

**Problem**: Configuration settings are invalid or missing.

**Solution**:
```bash
# Validate configuration
python marketman config validate

# Check specific settings
python marketman config show

# Common fixes:
# 1. Ensure .env file exists and has API keys
# 2. Check YAML syntax in config files
# 3. Verify file permissions
```

**Common Causes**:
- Missing API keys in `.env`
- Invalid YAML syntax
- Incorrect file paths
- Permission issues

### "No signals generated"

**Problem**: System runs but doesn't generate any trading signals.

**Solution**:
```bash
# Check news processing
python marketman news status

# Check signal generation
python marketman signals status

# Lower confidence threshold temporarily
# Edit config/settings.yaml:
# min_confidence_threshold: 5  # Lower from 7

# Check if news sources are working
python marketman news cycle --debug
```

**Common Causes**:
- Confidence threshold too high
- No relevant news found
- API rate limits exceeded
- News sources not working

### "API rate limit exceeded"

**Problem**: API calls are being rate limited.

**Solution**:
```bash
# Check current usage
python marketman status

# Reduce API limits in config/settings.yaml:
api_limits:
  finnhub:
    calls_per_day: 500  # Reduce from 1000
  openai:
    max_requests_per_day: 25  # Reduce from 50

# Implement better batching
alerts:
  batch_strategy: smart_batch
```

**Prevention**:
- Monitor API usage regularly
- Use conservative limits
- Implement proper batching
- Check API tier limits

## 🔌 API Problems

### OpenAI API Issues

#### "Invalid API key"

**Solution**:
```bash
# Check API key format
echo $OPENAI_API_KEY | head -c 20

# Should start with: sk-proj- or sk-

# Regenerate API key at:
# https://platform.openai.com/api-keys
```

#### "Rate limit exceeded"

**Solution**:
```yaml
# Reduce usage in config/settings.yaml:
news_ingestion:
  max_daily_ai_calls: 25  # Reduce from 75
  max_tokens_per_request: 500  # Reduce from 1000
```

### Finnhub API Issues

#### "API key not found"

**Solution**:
```bash
# Get new API key at: https://finnhub.io/
# Add to .env:
FINNHUB_KEY=your-new-key
```

#### "Daily limit exceeded"

**Solution**:
```yaml
# Reduce limits in config/settings.yaml:
api_limits:
  finnhub:
    calls_per_day: 500  # Free tier limit
    calls_per_minute: 30  # Reduce from 60
```

### NewsAPI Issues

#### "API key disabled"

**Solution**:
```bash
# Check account status at: https://newsapi.org/account
# Verify email address
# Check usage limits
```

#### "Quota exceeded"

**Solution**:
```yaml
# Reduce usage in config/settings.yaml:
api_limits:
  newsapi:
    calls_per_day: 50  # Reduce from 100
```

## ⚙️ Configuration Issues

### Environment Variables

#### "Environment variable not found"

**Solution**:
```bash
# Check .env file exists
ls -la .env

# Create if missing
cp .env.example .env

# Add required variables:
OPENAI_API_KEY=your-key
FINNHUB_KEY=your-key
NEWS_API=your-key
NEWS_DATA_KEY=your-key
PUSHOVER_TOKEN=your-token
PUSHOVER_USER=your-user-key
```

#### "Invalid configuration format"

**Solution**:
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config/settings.yaml'))"

# Check for common YAML errors:
# - Missing quotes around strings with special characters
# - Incorrect indentation
# - Invalid boolean values (use true/false, not True/False)
```

### File Permissions

#### "Permission denied"

**Solution**:
```bash
# Fix file permissions
chmod 644 config/*.yaml
chmod 600 .env
chmod 755 bin/*

# Check directory permissions
ls -la config/
ls -la bin/
```

## 🗄️ Database Problems

### "Database locked"

**Problem**: SQLite database is locked by another process.

**Solution**:
```bash
# Check for running processes
ps aux | grep marketman

# Kill any hanging processes
pkill -f marketman

# Or restart the system
sudo systemctl restart marketman
```

### "Database corrupted"

**Problem**: Database file is corrupted.

**Solution**:
```bash
# Backup current database
cp data/marketman.db data/marketman.db.backup

# Remove corrupted database
rm data/marketman.db

# Reinitialize database
python -c "from src.core.database.db_manager import init_database; init_database()"

# Or restore from backup
cp data/marketman.db.backup data/marketman.db
```

### "Table not found"

**Problem**: Database tables are missing.

**Solution**:
```bash
# Reinitialize database schema
python -c "from src.core.database.db_manager import init_database; init_database()"

# Check table structure
sqlite3 data/marketman.db ".schema"
```

## ⚡ Performance Issues

### "System is slow"

**Problem**: MarketMan is running slowly.

**Solution**:
```bash
# Check system resources
htop
df -h
free -h

# Optimize configuration:
# 1. Reduce batch sizes
# 2. Increase timeouts
# 3. Use caching
# 4. Optimize database queries
```

### "Memory usage high"

**Problem**: High memory consumption.

**Solution**:
```yaml
# Optimize memory usage in config/settings.yaml:
news_ingestion:
  max_daily_headlines: 25  # Reduce from 50
  max_batch_size: 5  # Reduce from 8

database:
  cleanup_old_records: true
  max_records_per_table: 5000  # Reduce from 10000
```

### "API calls taking too long"

**Problem**: API calls are slow or timing out.

**Solution**:
```yaml
# Increase timeouts in config/settings.yaml:
api_limits:
  timeout_seconds: 30  # Increase from 10
  retry_attempts: 3
  retry_delay: 5
```

## 🔍 Debugging

### Enable Debug Mode

```bash
# Set debug environment variable
export DEBUG=true

# Run with debug output
python marketman news cycle --debug

# Check debug logs
tail -f logs/marketman.log
```

### Check Logs

```bash
# View recent logs
tail -n 100 logs/marketman.log

# Search for errors
grep -i error logs/marketman.log

# Search for specific issues
grep -i "rate limit" logs/marketman.log
grep -i "api" logs/marketman.log
grep -i "database" logs/marketman.log
```

### System Diagnostics

```bash
# Run system diagnostics
python marketman status

# Check API connectivity
python marketman test api

# Check database connectivity
python marketman test database

# Check configuration
python marketman config validate
```

### Performance Profiling

```bash
# Profile a specific command
python -m cProfile -o profile.stats marketman news cycle

# Analyze profile results
python -c "
import pstats
p = pstats.Stats('profile.stats')
p.sort_stats('cumulative')
p.print_stats(10)
"
```

## 🆘 Getting Help

### Before Asking for Help

1. **Check this troubleshooting guide**
2. **Run system diagnostics**: `python marketman status`
3. **Check logs**: `tail -f logs/marketman.log`
4. **Validate configuration**: `python marketman config validate`
5. **Search existing issues**: GitHub issues page

### When Creating an Issue

Include the following information:

```markdown
## Problem Description
Brief description of the issue

## Steps to Reproduce
1. Run command: `python marketman news cycle`
2. Expected: Signals generated
3. Actual: No signals generated

## System Information
- OS: Ubuntu 20.04
- Python: 3.9.7
- MarketMan version: 1.0.0

## Error Messages
```
Traceback (most recent call last):
  File "marketman", line 13, in <module>
    from src.core.alert_batcher import AlertBatcher
ModuleNotFoundError: No module named 'src.core.alert_batcher'
```

## Configuration
- API keys configured: Yes
- Configuration validated: Yes
- Debug mode: Yes

## Logs
```
[2024-01-01 10:00:00] ERROR: API rate limit exceeded
```

## Additional Context
Any other relevant information
```

### Useful Commands

```bash
# System status
python marketman status

# Configuration validation
python marketman config validate

# Test specific components
python marketman test api
python marketman test database
python marketman test news

# Performance monitoring
python marketman performance show

# Debug mode
DEBUG=true python marketman news cycle

# Check version
python marketman --version
```

### External Resources

- **[User Guide](user-guide.md)** - Complete usage instructions
- **[Configuration Guide](configuration.md)** - Setup and configuration
- **[Development Guide](development.md)** - For developers
- **[GitHub Issues](https://github.com/your-repo/issues)** - Bug reports
- **[GitHub Discussions](https://github.com/your-repo/discussions)** - Questions

---

**Still stuck?** Create a detailed issue with the information above, and we'll help you resolve it. 