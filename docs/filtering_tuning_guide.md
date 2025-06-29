# MarketMan News Filtering & Tuning Guide

## Overview

This guide provides a comprehensive approach to tuning the MarketMan news filtering system for optimal signal quality and cost efficiency.

## Current System Analysis

### Filtering Pipeline
1. **Raw News Collection** (125 items from 3 sources)
2. **Tier 1: Basic Filtering** (Cost control)
3. **Tier 2: Advanced Filtering** (Quality control)
4. **Tier 3: AI Processing** (Signal generation)

### Current Performance
- **Input**: 125 news items per cycle
- **Filtered Out**: 125 items (100% rejection rate)
- **Primary Reasons**:
  - 56%: Outside market hours
  - 31%: Low relevance score (0.00)
  - 13%: Low relevance score (0.04-0.14)

## Tiered Filtering Strategy

### Tier 1: Basic Filtering (Cost Control)
**Purpose**: Prevent excessive API costs while maintaining coverage

```yaml
max_daily_headlines: 50      # Increased from 20
max_daily_ai_calls: 75       # Increased from 50
max_monthly_ai_budget: 30.0  # Increased from 20.0
```

**Tuning Guidelines**:
- Start with higher limits and monitor usage
- Adjust based on signal quality vs. cost
- Consider market volatility (increase during earnings season)

### Tier 2: Advanced Filtering (Quality Control)
**Purpose**: Ensure only relevant, high-quality news reaches AI processing

```yaml
advanced_filtering:
  min_relevance_score: 0.15      # Lowered from 0.3
  min_sentiment_strength: 0.1    # Lowered from 0.2
  min_ticker_count: 1
  require_multiple_tickers: false
  max_title_length: 200
  min_content_length: 50
  exclude_clickbait: true
  require_financial_context: false
```

**Tuning Guidelines**:
- **Relevance Score**: 0.15-0.25 range (0.15 catches more, 0.25 more selective)
- **Sentiment Strength**: 0.1-0.3 range (0.1 includes neutral, 0.3 more directional)
- **Content Length**: 50-100 characters minimum (prevents clickbait)

### Tier 3: Market Hours Optimization
**Purpose**: Balance real-time coverage with market relevance

```yaml
market_hours:
  start: '08:00'  # Pre-market coverage
  end: '18:00'    # After-hours coverage
  flexible_hours:
    earnings_news: true
    regulatory_news: true
    breaking_news: true
```

**Tuning Guidelines**:
- **Conservative**: 09:30-16:00 (market hours only)
- **Moderate**: 08:00-18:00 (extended hours)
- **Aggressive**: 06:00-20:00 (24/7 coverage)

## Keyword Optimization

### Current Keywords (28)
Basic market events and ETFs

### Enhanced Keywords (60+)
Added sector-specific keywords for better relevance:

```yaml
keywords:
  # Market Events (existing)
  - ETF, SPY, QQQ, DIA, interest rate, Fed, earnings...
  
  # Sector-Specific (new)
  - AI, artificial intelligence, robotics, automation
  - clean energy, renewable, solar, wind
  - electric vehicle, EV, battery
  - semiconductor, chip, defense, military
  - cybersecurity, blockchain, crypto
  - biotech, healthcare, fintech
  - cloud, SaaS, 5G, quantum, space
  - AR, VR, metaverse, Web3, DeFi, NFT
```

## Source Validation Enhancement

### Current Sources (10)
Basic financial and tech sources

### Enhanced Sources (18)
Added more authoritative sources with weighted priorities:

```yaml
source_weights:
  # Tier 1: Premium Financial (5)
  Reuters: 5, Bloomberg: 5, Financial Times: 5, WSJ: 5
  
  # Tier 2: Major Financial (4)
  CNBC: 4, MarketWatch: 4, Barron's: 4, Forbes: 4, Fortune: 4
  
  # Tier 3: Established (3)
  Yahoo Finance: 3, Seeking Alpha: 3, Business Insider: 3, TechCrunch: 3
  
  # Tier 4: Specialized (2)
  Ars Technica: 2, The Verge: 2, Wired: 2, VentureBeat: 2
```

## Tuning Parameters by Use Case

### Conservative Strategy (Low Cost, High Quality)
```yaml
max_daily_headlines: 25
max_daily_ai_calls: 40
min_relevance_score: 0.25
min_sentiment_strength: 0.2
market_hours: 09:30-16:00
```

### Balanced Strategy (Recommended)
```yaml
max_daily_headlines: 50
max_daily_ai_calls: 75
min_relevance_score: 0.15
min_sentiment_strength: 0.1
market_hours: 08:00-18:00
```

### Aggressive Strategy (High Coverage, Higher Cost)
```yaml
max_daily_headlines: 100
max_daily_ai_calls: 150
min_relevance_score: 0.1
min_sentiment_strength: 0.05
market_hours: 06:00-20:00
```

## Monitoring & Optimization

### Key Metrics to Track
1. **Filtering Efficiency**: Items processed vs. signals generated
2. **Cost Efficiency**: AI calls per signal generated
3. **Signal Quality**: Confidence scores and accuracy
4. **Coverage**: Missed opportunities vs. false positives

### Optimization Process
1. **Baseline**: Run with current settings for 1 week
2. **Analyze**: Review filtering statistics and signal quality
3. **Adjust**: Modify parameters based on performance
4. **Validate**: Test changes for 3-5 days
5. **Iterate**: Refine based on results

### Performance Targets
- **Signal Generation Rate**: 10-30% of processed items
- **Cost per Signal**: <$0.50 per AI-generated signal
- **Signal Quality**: >7/10 average confidence score
- **Coverage**: <5% missed high-impact news

## Advanced Tuning Techniques

### 1. Dynamic Thresholds
Adjust filtering based on market conditions:
- **High Volatility**: Lower thresholds for more coverage
- **Low Volatility**: Higher thresholds for quality
- **Earnings Season**: Increase limits and lower thresholds

### 2. Sector-Specific Filtering
Different thresholds for different sectors:
```yaml
sector_filters:
  tech:
    min_relevance_score: 0.12
    keywords: [AI, semiconductor, cloud, SaaS]
  energy:
    min_relevance_score: 0.18
    keywords: [oil, gas, renewable, solar]
  healthcare:
    min_relevance_score: 0.20
    keywords: [biotech, FDA, clinical trial]
```

### 3. Time-Based Optimization
Adjust filtering based on time of day:
- **Pre-market**: Lower thresholds for earnings/news
- **Market hours**: Standard thresholds
- **After-hours**: Higher thresholds for breaking news

## Troubleshooting Common Issues

### Issue: Too Many Items Filtered Out
**Symptoms**: 90%+ rejection rate
**Solutions**:
- Lower `min_relevance_score` (0.15 → 0.10)
- Extend market hours
- Add more keywords
- Lower `min_sentiment_strength`

### Issue: Too Many Low-Quality Signals
**Symptoms**: Low confidence scores, false positives
**Solutions**:
- Increase `min_relevance_score` (0.15 → 0.20)
- Tighten source validation
- Increase `min_content_length`
- Enable `exclude_clickbait`

### Issue: High API Costs
**Symptoms**: Exceeding daily/monthly limits
**Solutions**:
- Reduce `max_daily_headlines`
- Increase `min_relevance_score`
- Tighten market hours
- Optimize batching settings

### Issue: Missing Important News
**Symptoms**: No signals during major events
**Solutions**:
- Add event-specific keywords
- Lower thresholds temporarily
- Extend market hours
- Add more sources

## Implementation Checklist

- [ ] Update configuration with new parameters
- [ ] Test with sample data
- [ ] Monitor initial performance
- [ ] Adjust based on results
- [ ] Document final settings
- [ ] Set up monitoring alerts
- [ ] Schedule regular reviews

## Conclusion

The key to successful filtering is finding the right balance between coverage and quality. Start with the balanced strategy and adjust based on your specific needs and market conditions. Regular monitoring and iterative optimization will lead to the best results. 