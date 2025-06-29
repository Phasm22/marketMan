#!/usr/bin/env python3
"""
MarketMan Filtering Tuning Script
Analyzes filtering performance and suggests optimizations
"""
import sys
import os
import logging
from datetime import datetime, timedelta
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.utils.config_loader import get_config
from src.core.ingestion import create_news_orchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_filtering_performance():
    """Analyze current filtering performance and suggest optimizations"""
    
    print("🔍 MarketMan Filtering Performance Analysis")
    print("=" * 60)
    
    # Load configuration
    config_loader = get_config()
    config = config_loader.load_settings()
    
    # Create orchestrator
    orchestrator = create_news_orchestrator(config)
    
    # Get tracked tickers
    tracked_tickers = config.get('news_ingestion', {}).get('tracked_tickers', [])
    
    print(f"📊 Current Configuration:")
    print(f"  • Tracked ETFs: {len(tracked_tickers)}")
    print(f"  • Keywords: {len(config['news_ingestion']['keywords'])}")
    print(f"  • Daily Headlines Limit: {config['news_ingestion']['max_daily_headlines']}")
    print(f"  • Daily AI Calls Limit: {config['news_ingestion']['max_daily_ai_calls']}")
    print(f"  • Min Relevance Score: {config['news_ingestion']['advanced_filtering']['min_relevance_score']}")
    print(f"  • Min Sentiment Strength: {config['news_ingestion']['advanced_filtering']['min_sentiment_strength']}")
    print(f"  • Market Hours: {config['news_ingestion']['market_hours']['start']} - {config['news_ingestion']['market_hours']['end']}")
    
    print(f"\n🔄 Running Test Analysis...")
    
    # Run test cycle
    results = orchestrator.process_news_cycle(
        tickers=tracked_tickers[:10],  # Test with first 10 tickers
        hours_back=24
    )
    
    print(f"\n📈 Analysis Results:")
    print(f"  • Raw News Items: {results['raw_news_count']}")
    print(f"  • Filtered Items: {results['filtered_news_count']}")
    print(f"  • Batches Created: {results['batches_created']}")
    print(f"  • AI Processed: {results['ai_processed_batches']}")
    print(f"  • Acceptance Rate: {(results['filtered_news_count'] / results['raw_news_count'] * 100):.1f}%")
    
    # Analyze filter reasons
    filter_stats = results.get('filter_stats', {})
    if filter_stats.get('reasons'):
        print(f"\n🚫 Filter Reasons Breakdown:")
        for reason, count in filter_stats['reasons'].items():
            percentage = (count / results['raw_news_count']) * 100
            print(f"  • {reason}: {count} items ({percentage:.1f}%)")
    
    # Provide recommendations
    print(f"\n💡 Optimization Recommendations:")
    
    acceptance_rate = (results['filtered_news_count'] / results['raw_news_count']) * 100
    
    if acceptance_rate < 5:
        print(f"  ⚠️  Very low acceptance rate ({acceptance_rate:.1f}%) - consider:")
        print(f"     • Lowering min_relevance_score from {config['news_ingestion']['advanced_filtering']['min_relevance_score']} to 0.10")
        print(f"     • Extending market hours to 06:00-20:00")
        print(f"     • Adding more sector-specific keywords")
        print(f"     • Lowering min_sentiment_strength from {config['news_ingestion']['advanced_filtering']['min_sentiment_strength']} to 0.05")
    
    elif acceptance_rate < 15:
        print(f"  📊 Moderate acceptance rate ({acceptance_rate:.1f}%) - consider:")
        print(f"     • Fine-tuning relevance score to 0.12-0.18 range")
        print(f"     • Adding more sources to source_weights")
        print(f"     • Optimizing keyword list")
    
    else:
        print(f"  ✅ Good acceptance rate ({acceptance_rate:.1f}%) - system is well-tuned")
    
    # Check for specific issues
    if filter_stats.get('reasons'):
        if 'outside_market_hours' in filter_stats['reasons']:
            market_hours_count = filter_stats['reasons']['outside_market_hours']
            market_hours_pct = (market_hours_count / results['raw_news_count']) * 100
            if market_hours_pct > 30:
                print(f"  ⏰ High market hours filtering ({market_hours_pct:.1f}%) - consider extending hours")
        
        if 'low_relevance_score_0.00' in filter_stats['reasons']:
            low_score_count = filter_stats['reasons']['low_relevance_score_0.00']
            low_score_pct = (low_score_count / results['raw_news_count']) * 100
            if low_score_pct > 40:
                print(f"  🎯 High zero-relevance filtering ({low_score_pct:.1f}%) - consider adding more keywords")
    
    # Cost analysis
    cost_stats = results.get('cost_stats', {})
    if cost_stats:
        print(f"\n💰 Cost Analysis:")
        print(f"  • Daily AI Calls Used: {cost_stats.get('daily_ai_calls', 0)}")
        print(f"  • Monthly Cost: ${cost_stats.get('monthly_ai_cost', 0.0):.2f}")
        print(f"  • Cost per Signal: ${cost_stats.get('monthly_ai_cost', 0.0) / max(results['ai_processed_batches'], 1):.2f}")
    
    return results

def suggest_parameter_adjustments():
    """Suggest specific parameter adjustments based on common scenarios"""
    
    print(f"\n🎛️  Parameter Adjustment Scenarios:")
    print(f"=" * 60)
    
    scenarios = [
        {
            "name": "Conservative (Low Cost, High Quality)",
            "description": "Minimize costs while maintaining high signal quality",
            "params": {
                "max_daily_headlines": 25,
                "max_daily_ai_calls": 40,
                "min_relevance_score": 0.25,
                "min_sentiment_strength": 0.2,
                "market_hours": "09:30-16:00"
            }
        },
        {
            "name": "Balanced (Recommended)",
            "description": "Good balance of coverage and quality",
            "params": {
                "max_daily_headlines": 50,
                "max_daily_ai_calls": 75,
                "min_relevance_score": 0.15,
                "min_sentiment_strength": 0.1,
                "market_hours": "08:00-18:00"
            }
        },
        {
            "name": "Aggressive (High Coverage)",
            "description": "Maximum coverage with higher costs",
            "params": {
                "max_daily_headlines": 100,
                "max_daily_ai_calls": 150,
                "min_relevance_score": 0.1,
                "min_sentiment_strength": 0.05,
                "market_hours": "06:00-20:00"
            }
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['name']}")
        print(f"   {scenario['description']}")
        print(f"   Parameters:")
        for param, value in scenario['params'].items():
            print(f"     • {param}: {value}")

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == "suggest":
        suggest_parameter_adjustments()
    else:
        analyze_filtering_performance()

if __name__ == "__main__":
    main() 