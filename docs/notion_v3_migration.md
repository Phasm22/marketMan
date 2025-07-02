# Notion v3 Schema Migration Guide

## Overview

This document outlines the migration from the multi-version schema system to a simplified v3-only schema for MarketMan's Notion integration.

## Changes Made

### 1. Removed Schema Versioning

**Before**: The system supported multiple schema versions (v1, v2, v3) with complex version checking and fallback logic.

**After**: Only v3 schema fields are supported, eliminating the need for schema version tracking.

### 2. Simplified Signal Fields

**Removed Fields**:
- `speculative` (boolean)
- `needs_confirmation` (boolean) 
- `confidence_capped` (boolean)
- `custom_reasoning` (text)
- `signal_schema_version` (number)

**Kept Fields** (v3 actionable fields):
- `if_then_scenario` (text) - Validation logic for signals
- `contradictory_signals` (text) - Opposing signals/risks
- `uncertainty_metric` (text) - Confidence with context
- `price_anchors` (text) - ETF price context
- `position_risk_bracket` (text) - Position sizing guidance

### 3. Updated Files

#### Core Integration Files
- `src/integrations/notion_journal.py` - Simplified `log_signal()` method
- `src/core/ingestion/news_orchestrator.py` - Removed old schema fields
- `src/core/signals/etf_signal_engine.py` - Removed schema version tracking

#### Documentation
- `docs/integrations/notion.md` - Updated with v3-only schema
- `docs/notion_v3_migration.md` - This migration guide

#### Setup Tools
- `scripts/setup_notion_v3.py` - New setup and validation script

## Required Notion Database Schema

Your Notion signals database must have these fields:

| Property Name | Type | Description |
|---------------|------|-------------|
| Title | Title | Signal title |
| Signal | Select | Bullish, Bearish, Neutral |
| Confidence | Number | 1-10 confidence score |
| ETFs | Multi-select | Affected ETF tickers |
| Sector | Select | Market sector |
| Timestamp | Date | Signal timestamp |
| Reasoning | Text | Signal reasoning (bullet-pointed) |
| Status | Select | New, Reviewed, Acted On, Archived |
| If-Then Scenario | Text | Validation logic for signal |
| Contradictory Signals | Text | Opposing signals/risks |
| Uncertainty Metric | Text | Confidence with context |
| Position Risk Bracket | Text | Position sizing guidance |
| Price Anchors | Text | ETF price context |

**Optional Fields**:
- Journal Notes (Text) - For manual notes and review

## Migration Steps

### 1. Update Your Notion Database

If you have an existing database with old schema fields:

1. **Remove old fields** (if present):
   - Speculative
   - Needs Confirmation
   - Confidence Capped
   - Custom Reasoning
   - Signal Schema Version

2. **Add v3 fields** (if missing):
   - If-Then Scenario
   - Contradictory Signals
   - Uncertainty Metric
   - Position Risk Bracket
   - Price Anchors

### 2. Validate Your Setup

Run the setup script to validate your database:

```bash
# Show setup instructions
python scripts/setup_notion_v3.py

# Validate existing database
python scripts/setup_notion_v3.py --validate

# Test signal creation
python scripts/setup_notion_v3.py --validate --test
```

### 3. Update Environment Variables

Ensure your `.env` file has:

```bash
NOTION_TOKEN=secret_your_integration_token_here
SIGNALS_DATABASE_ID=your_signals_database_id
```

## Benefits of v3 Schema

### 1. **Simplified Maintenance**
- No more schema version checking
- Single source of truth for field definitions
- Easier to debug and maintain

### 2. **Actionable Insights**
- `if_then_scenario` provides clear validation logic
- `contradictory_signals` highlights risks
- `uncertainty_metric` gives confidence context
- `position_risk_bracket` guides position sizing
- `price_anchors` provides real-time context

### 3. **Better Trading Decisions**
- All fields are designed to help traders make informed decisions
- Clear risk/reward assessment
- Specific validation criteria
- Position sizing guidance

## Troubleshooting

### Common Issues

#### "Missing v3 fields" Error
**Solution**: Add the missing fields to your Notion database using the setup script.

#### "Incorrect field types" Error
**Solution**: Ensure field types match exactly (e.g., "rich_text" not "text" for v3 fields).

#### "Database not found" Error
**Solution**: Check your `SIGNALS_DATABASE_ID` environment variable and database permissions.

### Validation Commands

```bash
# Check your setup
python scripts/setup_notion_v3.py --validate

# Test signal creation
python scripts/setup_notion_v3.py --validate --test

# View setup instructions
python scripts/setup_notion_v3.py
```

## Backward Compatibility

**Note**: This migration removes backward compatibility with older schema versions. If you have existing signals with old schema fields, they will continue to work but new signals will only use v3 fields.

## Support

If you encounter issues during migration:

1. Run the validation script to identify problems
2. Check the Notion API documentation for field types
3. Ensure your integration has proper database permissions
4. Review the setup instructions in `docs/integrations/notion.md` 