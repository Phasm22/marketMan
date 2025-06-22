# MarketMan Alert Batching System

## Overview

The MarketMan Alert Batching System prevents notification fatigue and rate limiting by intelligently grouping and timing your market alerts. Instead of sending every alert immediately, the system can batch alerts based on different strategies.

## Batching Strategies

### 1. Immediate (⚡)
- **Behavior**: Send alerts immediately (original behavior)
- **Use Case**: When you want every alert right away
- **Best For**: Low-volume setups or when monitoring just a few keywords

### 2. Smart Batch (🧠) - **Recommended**
- **Behavior**: Intelligent batching based on confidence and timing
  - High confidence (9+): Send immediately
  - Medium confidence (7-8): Batch groups of 2+ or after 45 minutes
  - Low confidence (<7): Don't send
- **Use Case**: Balanced approach for most users
- **Best For**: Multiple alert setups with varying importance

### 3. Time Window (⏰)
- **Behavior**: Batch alerts within 30-minute windows or groups of 3+
- **Use Case**: Regular batching regardless of confidence
- **Best For**: High-volume setups where you want frequent but grouped updates

### 4. Daily Digest (📅)
- **Behavior**: One comprehensive summary per day
- **Use Case**: Low-noise, daily market overview
- **Best For**: Long-term investors who don't need real-time alerts

## Configuration

### Set Your Strategy

Add to your `.env` file:

```bash
# Choose your alert strategy
ALERT_STRATEGY=smart_batch

# Options: immediate, smart_batch, time_window, daily_digest
```

If not set, defaults to `smart_batch`.

### Verify Configuration

```bash
./marketman-alerts config
```

## Usage

### Check Queue Status
```bash
./marketman-alerts stats
```

### Process Pending Alerts
```bash
./marketman-alerts process
```

### View Pending Alerts
```bash
./marketman-alerts pending
```

### Test the System
```bash
./marketman-alerts test
```

### Cleanup Old Records
```bash
./marketman-alerts cleanup --days 7
```

## Automation

### With Cron (Recommended)

For Smart Batch or Time Window strategies, process the queue every 15 minutes:

```bash
# Add to crontab (crontab -e)
*/15 * * * * cd /root/marketMan && ./marketman-alerts process >> /var/log/marketman-alerts.log 2>&1
```

For Daily Digest, process once per day:

```bash
# Daily at 8 AM
0 8 * * * cd /root/marketMan && ./marketman-alerts process >> /var/log/marketman-alerts.log 2>&1
```

### Run Analysis + Processing Together

The main analyzer now automatically processes the queue after analysis:

```bash
python news_gpt_analyzer.py
```

This will:
1. Analyze new alerts
2. Queue them based on your strategy
3. Process any ready batches
4. Send notifications

## Alert Formats

### Single Alert (Immediate or High Confidence)
```
↗ BULLISH Signal (9/10)

Clean Energy Bill Passes Senate...

Reason: Bipartisan legislation unlocks $50B investment
ETFs: ICLN, TAN, QCLN
```

### Batched Alerts (Multiple Signals)
```
🎯 Market Batch Update (3 signals)

Signals: ↗ 2 Bullish | ↘ 1 Bearish

🔥 High Confidence Alerts:
• Bullish Clean Energy: Senate passes major infrastructure bill...
• Bearish Traditional Energy: OPEC production cuts announced...

📈 Sectors Active:
• Clean Energy: ICLN, TAN, QCLN
• Traditional Energy: XLE, USO
```

### Daily Digest
```
📊 Daily Market Summary (8 signals)

Signals: ↗ 5 Bullish | ↘ 2 Bearish | → 1 Neutral

🔥 High Confidence Alerts:
• Bullish Electric Vehicles: Tesla reports record deliveries...
• Bullish Clean Energy: Infrastructure spending approved...
• Bearish Traditional Energy: Oil demand concerns rise...

📈 Sectors Active:
• Clean Energy: ICLN, TAN, QCLN
• Electric Vehicles: LIT, DRIV, ARKQ
• Traditional Energy: XLE, USO, XOP
```

## Monitoring

### Check System Health
```bash
# View recent statistics
./marketman-alerts stats

# See what's pending
./marketman-alerts pending

# Check logs
tail -f /var/log/marketman-alerts.log
```

### Queue Management

The system automatically:
- Removes alerts after sending
- Cleans up old batch records (7 days)
- Handles failed sends gracefully
- Prevents duplicate alerts

### Troubleshooting

1. **No alerts being sent?**
   ```bash
   ./marketman-alerts pending
   ./marketman-alerts process
   ```

2. **Too many immediate alerts?**
   - Change to `smart_batch` or `time_window`
   - Increase confidence thresholds

3. **Missing daily digest?**
   - Check if alerts are being queued: `./marketman-alerts stats`
   - Manually process: `./marketman-alerts process`

4. **Want to reset the queue?**
   ```bash
   rm /root/marketMan/alert_batch.db
   ```

## Integration Tips

### Multiple Google Alerts
With multiple Google Alerts running, Smart Batch is ideal:
- Critical market events (conf 9+) send immediately
- Related signals get batched together
- Sector-based grouping reduces noise

### High-Volume Monitoring
For scanning many keywords:
1. Use `time_window` or `daily_digest`
2. Set up cron for automatic processing
3. Monitor queue size with `stats` command

### Custom Workflows
The batching system integrates with your existing:
- Notion logging (still happens immediately)
- Memory tracking (patterns still detected)
- ETF sector categorization (preserved in batches)

## Database Schema

The system uses SQLite for reliability:
- `pending_alerts`: Queued alerts waiting to be sent
- `sent_batches`: History of sent notifications

Located at: `/root/marketMan/alert_batch.db`

## Rate Limiting Protection

Pushover limits:
- 7,500 messages per month
- 30 messages per minute

The batching system helps you stay within these limits while still getting timely market intelligence.
