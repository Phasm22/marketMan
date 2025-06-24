# 🕐 MarketMan Cron Update Summary

## ✅ What's New

### 🎯 Updated CLI Commands
- **`./bin/marketman run`** - Runs the refactored news analyzer (recommended)
- **`./bin/marketman run --legacy`** - Runs the legacy analyzer
- **`./bin/marketman run --test`** - Test mode for both versions
- **`./bin/marketman-alerts process`** - Process alert batches
- **`./bin/setup-cron`** - Helper script for cron management

### 🔄 Optimized Cron Schedule

#### Your Current Setup (Basic)
```bash
# Old approach - direct Python calls
*/15 * * * * cd /root/marketMan && python3 -m src.core.news_analyzer_refactored >> /var/log/marketman.log 2>&1
0 9 * * * cd /root/marketMan && ./bin/gmail-organizer auto >> /var/log/marketman.log 2>&1
```

#### Recommended Update (CLI-based)
```bash
# Core analysis every 15 minutes using CLI
*/15 * * * * cd /root/marketMan && ./bin/marketman run >> /var/log/marketman.log 2>&1

# Process alert batches every 10 minutes (smart batching)
*/10 * * * * cd /root/marketMan && ./bin/marketman-alerts process >> /var/log/marketman.log 2>&1

# Daily Gmail cleanup
0 9 * * * cd /root/marketMan && ./bin/gmail-organizer auto >> /var/log/marketman.log 2>&1

# Daily system health check
0 7 * * * cd /root/marketMan && ./bin/marketman monitor --system >> /var/log/marketman.log 2>&1

# Weekly memory cleanup (keep 30 days)
0 2 * * 0 cd /root/marketMan && ./bin/marketman memory --cleanup 30 >> /var/log/marketman.log 2>&1
```

## 🚀 Easy Installation

### Option 1: Use the Helper Script
```bash
# Install the recommended cron jobs
cd /root/marketMan
./bin/setup-cron install

# Check what was installed
./bin/setup-cron show

# Monitor logs
./bin/setup-cron logs
```

### Option 2: Manual Installation
```bash
# Copy the cron setup
cp /root/marketMan/cron-setup.txt /tmp/my-marketman-cron

# Edit if needed
nano /tmp/my-marketman-cron

# Install (removes old MarketMan crons first)
crontab /tmp/my-marketman-cron

# Verify
crontab -l | grep marketman
```

## 🎯 Benefits of the Update

### 🔧 **Better CLI Integration**
- **Consistent interface** - All commands go through CLI
- **Better error handling** - CLI provides standardized error codes
- **Easier debugging** - Clear command structure for troubleshooting

### 📊 **Enhanced Monitoring**
- **Smart alert batching** - Separate processing prevents missed notifications
- **System health checks** - Daily monitoring of component status
- **Memory management** - Automated cleanup prevents database bloat

### 🛠️ **Easier Maintenance**
- **Helper scripts** - Simple installation and management
- **Log consolidation** - All activity in `/var/log/marketman.log`
- **Flexible scheduling** - Easy to adjust frequency for different trading styles

## 📈 Trading Style Configurations

### 🏃 **High-Frequency Trading**
```bash
# Every 5 minutes analysis + 3-minute batch processing
*/5 * * * * cd /root/marketMan && ./bin/marketman run >> /var/log/marketman-hf.log 2>&1
*/3 * * * * cd /root/marketMan && ./bin/marketman-alerts process >> /var/log/marketman-hf.log 2>&1
```

### 🐌 **Conservative Trading**
```bash
# Twice daily (9 AM and 5 PM)
0 9,17 * * * cd /root/marketMan && ./bin/marketman run >> /var/log/marketman-conservative.log 2>&1
15 9,17 * * * cd /root/marketMan && ./bin/marketman-alerts process >> /var/log/marketman-conservative.log 2>&1
```

### ⚡ **Your Current Setup (Balanced)**
```bash
# Every 15 minutes - good balance of timeliness and resource usage
*/15 * * * * cd /root/marketMan && ./bin/marketman run >> /var/log/marketman.log 2>&1
*/10 * * * * cd /root/marketMan && ./bin/marketman-alerts process >> /var/log/marketman.log 2>&1
```

## 🎯 Next Steps

1. **Test the new CLI**: `./bin/marketman run --test`
2. **Install updated crons**: `./bin/setup-cron install`
3. **Monitor the logs**: `tail -f /var/log/marketman.log`
4. **Verify operation**: `./bin/setup-cron show`

Your MarketMan system will now have better reliability, monitoring, and maintainability! 🚀
