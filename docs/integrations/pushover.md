# Pushover Integration for MarketMan

## Overview

MarketMan includes a comprehensive Pushover notification system that provides instant push alerts for high-confidence trading signals, risk warnings, and system alerts. The integration features configurable confidence thresholds, rate limiting, and intelligent message formatting.

## Features

### ✅ Core Features
- **Instant push alerts** on high-confidence signals (configurable threshold)
- **Risk warnings** for market volatility and other risk factors
- **System monitoring alerts** for service status
- **Rate limiting** to prevent notification spam
- **Configurable priorities** based on signal confidence
- **URL integration** linking to full analysis in Notion

### ✅ Configuration Options
- Confidence threshold filtering (default: 7/10)
- Risk warning toggles
- Rate limiting (default: 10 notifications/hour)
- Priority settings for different alert types
- Device-specific targeting

## Setup Instructions

### 1. Get Pushover Credentials

1. Go to [https://pushover.net/](https://pushover.net/)
2. Create an account (if you don't have one)
3. Get your **User Key** from the main page
4. Create a new application:
   - Click "Create an Application"
   - Name: `MarketMan`
   - Description: `Trading signal notifications`
   - Get the **API Token**

### 2. Configure MarketMan

#### Option A: Interactive Setup (Recommended)
```bash
python setup/setup_pushover.py
```

#### Option B: Manual Configuration
Edit `config/settings.yaml`:
```yaml
integrations:
  pushover:
    enabled: true
    api_token: "your_api_token_here"
    user_token: "your_user_key_here"
    confidence_threshold: 7
    risk_warnings_enabled: true
    rate_limit_per_hour: 10
    priority_settings:
      high_confidence: 0
      medium_confidence: 0
      low_confidence: -1
      system_alerts: 1
      risk_warnings: 1
```

### 3. Test Configuration

```bash
# Test basic connectivity
./bin/marketman pushover test

# Check status
./bin/marketman pushover status

# Send test signal
./bin/marketman pushover signal \
  --signal Bullish \
  --confidence 8 \
  --title "Test Signal" \
  --message "This is a test trading signal"

# Send test warning
./bin/marketman pushover warning \
  --warning-type "Volatility Spike" \
  --message "Market volatility has increased"
```

## Usage

### CLI Commands

```bash
# Test connectivity
./bin/marketman pushover test

# Show status and rate limit info
./bin/marketman pushover status

# Send trading signal
./bin/marketman pushover signal \
  --signal Bullish \
  --confidence 9 \
  --title "Clean Energy Bill Passes" \
  --message "Major renewable energy legislation approved" \
  --etfs "ICLN,TAN,QCLN"

# Send risk warning
./bin/marketman pushover warning \
  --warning-type "Market Stress" \
  --message "VIX increased 25% in last hour" \
  --etfs "VIXY,VXX"
```

### Programmatic Usage

```python
from src.integrations.pushover_client import (
    send_trading_signal,
    send_risk_warning,
    send_system_alert
)

# Send trading signal
send_trading_signal(
    signal="Bullish",
    confidence=9,
    title="Clean Energy Bill Passes Senate",
    reasoning="Major renewable energy legislation approved",
    etfs=["ICLN", "TAN", "QCLN"],
    risk_factors=["Market volatility", "Regulatory uncertainty"]
)

# Send risk warning
send_risk_warning(
    warning_type="Volatility Spike",
    message="VIX has increased 25% in the last hour",
    affected_symbols=["VIXY", "VXX", "UVXY"]
)

# Send system alert
send_system_alert(
    service_name="MarketMan Database",
    status="WARNING",
    details="High memory usage detected (85%)"
)
```

## Configuration Options

### Confidence Thresholds

```yaml
integrations:
  pushover:
    confidence_threshold: 7  # Minimum confidence for notifications
```

- **9-10**: High confidence (CRITICAL level)
- **7-8**: Medium confidence (HIGH/STANDARD level)
- **<7**: Filtered out (below threshold)

### Priority Settings

```yaml
priority_settings:
  high_confidence: 0    # Normal priority for 9-10 confidence
  medium_confidence: 0  # Normal priority for 7-8 confidence
  low_confidence: -1    # Quiet priority for <7 confidence
  system_alerts: 1      # High priority for system issues
  risk_warnings: 1      # High priority for risk warnings
```

Priority levels:
- **-2**: Silent (no sound/vibration)
- **-1**: Quiet (low priority)
- **0**: Normal (default)
- **1**: High (requires acknowledgment)
- **2**: Emergency (bypasses quiet hours)

### Rate Limiting

```yaml
rate_limit_per_hour: 10  # Maximum notifications per hour
```

Prevents notification spam while ensuring important alerts get through.

## Message Formatting

### Trading Signals

```
↗ BULLISH Signal (9/10)

Clean Energy Bill Passes Senate with Strong Bipartisan Support...

Reason: Major renewable energy legislation approved, unlocking $50B+ in sector investment

ETFs: ICLN, TAN, QCLN, PBW

⚠️ Risk Factors:
• Market volatility
• Regulatory timeline uncertainty
```

### Risk Warnings

```
⚠️ Market volatility has increased significantly

Affected: VIXY, VXX, UVXY
```

### System Alerts

```
⚠️ MarketMan Database is WARNING

High memory usage detected (85%)
```

## Integration Points

### Automatic Notifications

The Pushover integration is automatically triggered by:

1. **News Analysis**: High-confidence signals from `NewsSignalOrchestrator`
2. **Alert Batching**: Batched notifications from `AlertBatcher`
3. **System Monitoring**: Service status alerts from `MarketManMonitor`
4. **Risk Detection**: Automated risk warnings from market analysis

### Alert Batching

The system uses intelligent batching to prevent notification fatigue:

- **Immediate**: High-confidence signals (9-10)
- **Smart Batch**: Medium confidence signals grouped by time/content
- **Daily Digest**: Low-priority signals summarized daily

## Troubleshooting

### Common Issues

#### "Pushover credentials not configured"
- Check that `api_token` and `user_token` are set in `config/settings.yaml`
- Verify credentials are correct at [pushover.net](https://pushover.net/)

#### "Rate limit exceeded"
- Wait for the hourly limit to reset
- Check current status: `./bin/marketman pushover status`
- Consider increasing `rate_limit_per_hour` if needed

#### "Test notification failed"
- Verify internet connectivity
- Check Pushover service status
- Ensure device has Pushover app installed

### Debug Mode

Enable debug logging to see detailed Pushover activity:

```yaml
app:
  debug: true
  log_level: "DEBUG"
```

### Status Check

```bash
./bin/marketman pushover status
```

Shows:
- Configuration status
- Rate limit usage
- Current settings
- Connection status

## Advanced Configuration

### Device-Specific Targeting

Add device targeting to your settings:

```yaml
integrations:
  pushover:
    device: "iPhone"  # Target specific device
```

### Sound Customization

```yaml
integrations:
  pushover:
    sound: "cosmic"  # Custom notification sound
```

Available sounds: [pushover.net/api#sounds](https://pushover.net/api#sounds)

### URL Integration

Notifications automatically include links to full analysis in Notion when available.

## Security Notes

- API tokens are stored in `config/settings.yaml`
- Consider using environment variables for production
- Rate limiting prevents abuse
- No sensitive trading data is sent in notifications

## Support

For issues with the Pushover integration:

1. Check the troubleshooting section above
2. Verify Pushover service status
3. Review MarketMan logs: `tail -f logs/marketman.log`
4. Test with: `./bin/marketman pushover test`

## Examples

### Demo Script

Run the demo to see all features in action:

```bash
python test_pushover_demo.py
```

### Real-World Usage

The integration is automatically used by:

- News analysis pipeline
- System monitoring
- Risk detection systems
- Alert batching system

No manual intervention required once configured! 