#!/usr/bin/env python3
"""
MarketMan Configuration Validator
Validates all user-defined variables and settings for soundness and consistency
"""
import sys
import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.utils.config_loader import get_config

def validate_risk_settings(config: Dict[str, Any]) -> List[Tuple[str, str, str]]:
    """Validate risk management settings"""
    issues = []
    risk_config = config.get('risk', {})
    
    # Check daily loss limits
    max_daily_loss = risk_config.get('max_daily_loss', 0)
    max_daily_loss_percent = risk_config.get('max_daily_loss_percent', 0)
    
    if max_daily_loss_percent > 5:
        issues.append(('WARNING', 'risk.max_daily_loss_percent', 
                      f'{max_daily_loss_percent}% is quite aggressive. Consider 2-3% for conservative trading.'))
    
    if max_daily_loss_percent < 1:
        issues.append(('INFO', 'risk.max_daily_loss_percent', 
                      f'{max_daily_loss_percent}% is very conservative. May limit trading opportunities.'))
    
    # Check position sizing
    max_position_size = risk_config.get('max_position_size', 0)
    max_position_size_percent = risk_config.get('max_position_size_percent', 0)
    
    if max_position_size_percent > 10:
        issues.append(('WARNING', 'risk.max_position_size_percent', 
                      f'{max_position_size_percent}% is high. Consider 2-5% for better diversification.'))
    
    # Check Kelly criterion
    max_kelly = risk_config.get('max_kelly_fraction', 0)
    if max_kelly > 0.3:
        issues.append(('WARNING', 'risk.max_kelly_fraction', 
                      f'{max_kelly} is aggressive. Consider 0.15-0.25 for conservative approach.'))
    
    return issues

def validate_api_limits(config: Dict[str, Any]) -> List[Tuple[str, str, str]]:
    """Validate API rate limits and costs"""
    issues = []
    api_config = config.get('api_limits', {})
    
    # Check OpenAI costs
    openai_config = api_config.get('openai', {})
    max_requests = openai_config.get('max_requests_per_day', 0)
    max_tokens = openai_config.get('max_tokens_per_request', 0)
    
    # Estimate daily cost (rough calculation)
    estimated_cost = (max_requests * max_tokens * 0.000002)  # Approximate GPT-4 cost
    if estimated_cost > 5:
        issues.append(('WARNING', 'api_limits.openai', 
                      f'Estimated daily cost: ${estimated_cost:.2f}. Consider reducing limits if cost is a concern.'))
    
    # Check Finnhub limits
    finnhub_config = api_config.get('finnhub', {})
    calls_per_day = finnhub_config.get('calls_per_day', 0)
    if calls_per_day > 1000:
        issues.append(('INFO', 'api_limits.finnhub', 
                      f'{calls_per_day} calls/day may exceed free tier limits.'))
    
    return issues

def validate_broker_settings(config: Dict[str, Any]) -> List[Tuple[str, str, str]]:
    """Validate broker configuration"""
    issues = []
    
    # Load broker config
    config_loader = get_config()
    broker_config = config_loader.load_brokers()
    
    paper_trading = broker_config.get('paper_trading', {})
    initial_balance = paper_trading.get('initial_balance', 0)
    
    if initial_balance > 50000:
        issues.append(('INFO', 'brokers.paper_trading.initial_balance', 
                      f'${initial_balance:,} is high for testing. Consider $10k-25k for realistic testing.'))
    
    if initial_balance < 5000:
        issues.append(('WARNING', 'brokers.paper_trading.initial_balance', 
                      f'${initial_balance:,} may be too low for meaningful position sizing.'))
    
    # Check global broker settings
    global_settings = broker_config.get('global_settings', {})
    max_position = global_settings.get('max_position_size', 0)
    max_daily_loss = global_settings.get('max_daily_loss', 0)
    
    if max_position > initial_balance * 0.1:
        issues.append(('WARNING', 'brokers.global_settings.max_position_size', 
                      f'${max_position:,} is >10% of account size. Consider smaller positions.'))
    
    if max_daily_loss > initial_balance * 0.05:
        issues.append(('WARNING', 'brokers.global_settings.max_daily_loss', 
                      f'${max_daily_loss:,} is >5% of account size. Consider tighter risk management.'))
    
    return issues

def validate_alert_settings(config: Dict[str, Any]) -> List[Tuple[str, str, str]]:
    """Validate alert and notification settings"""
    issues = []
    alert_config = config.get('alerts', {})
    
    max_daily_alerts = alert_config.get('max_daily_alerts', 0)
    if max_daily_alerts > 20:
        issues.append(('INFO', 'alerts.max_daily_alerts', 
                      f'{max_daily_alerts} alerts/day may cause notification fatigue.'))
    
    # Check Pushover settings
    integrations = config.get('integrations', {})
    pushover = integrations.get('pushover', {})
    
    if pushover.get('enabled', False):
        rate_limit = pushover.get('rate_limit_per_hour', 0)
        if rate_limit > 15:
            issues.append(('INFO', 'integrations.pushover.rate_limit_per_hour', 
                          f'{rate_limit} notifications/hour may be excessive.'))
    
    return issues

def validate_news_settings(config: Dict[str, Any]) -> List[Tuple[str, str, str]]:
    """Validate news ingestion settings"""
    issues = []
    news_config = config.get('news_ingestion', {})
    
    max_daily_headlines = news_config.get('max_daily_headlines', 0)
    max_daily_ai_calls = news_config.get('max_daily_ai_calls', 0)
    
    if max_daily_ai_calls > 100:
        issues.append(('WARNING', 'news_ingestion.max_daily_ai_calls', 
                      f'{max_daily_ai_calls} AI calls/day may be expensive. Consider reducing.'))
    
    if max_daily_headlines > 100:
        issues.append(('INFO', 'news_ingestion.max_daily_headlines', 
                      f'{max_daily_headlines} headlines/day may be excessive for processing.'))
    
    # Check filtering thresholds
    advanced_filtering = news_config.get('advanced_filtering', {})
    min_relevance = advanced_filtering.get('min_relevance_score', 0)
    
    if min_relevance < 0.1:
        issues.append(('WARNING', 'news_ingestion.advanced_filtering.min_relevance_score', 
                      f'{min_relevance} is very low. May result in poor quality signals.'))
    
    return issues

def main():
    """Main validation function"""
    print("🔍 MarketMan Configuration Validator")
    print("=" * 50)
    
    try:
        # Load configuration
        config_loader = get_config()
        config = config_loader.load_settings()
        
        all_issues = []
        
        # Run all validations
        all_issues.extend(validate_risk_settings(config))
        all_issues.extend(validate_api_limits(config))
        all_issues.extend(validate_broker_settings(config))
        all_issues.extend(validate_alert_settings(config))
        all_issues.extend(validate_news_settings(config))
        
        # Group issues by severity
        warnings = [issue for issue in all_issues if issue[0] == 'WARNING']
        infos = [issue for issue in all_issues if issue[0] == 'INFO']
        
        # Display results
        if warnings:
            print("\n⚠️  WARNINGS:")
            print("-" * 30)
            for severity, setting, message in warnings:
                print(f"  {setting}: {message}")
        
        if infos:
            print("\nℹ️  RECOMMENDATIONS:")
            print("-" * 30)
            for severity, setting, message in infos:
                print(f"  {setting}: {message}")
        
        if not all_issues:
            print("\n✅ Configuration looks good!")
        else:
            print(f"\n📊 Summary: {len(warnings)} warnings, {len(infos)} recommendations")
        
        # Show current key settings
        print("\n📋 Current Key Settings:")
        print("-" * 30)
        
        risk_config = config.get('risk', {})
        print(f"  Max Daily Loss: {risk_config.get('max_daily_loss_percent', 'N/A')}%")
        print(f"  Max Position Size: {risk_config.get('max_position_size_percent', 'N/A')}%")
        print(f"  Kelly Fraction: {risk_config.get('max_kelly_fraction', 'N/A')}")
        
        api_config = config.get('api_limits', {})
        openai_config = api_config.get('openai', {})
        print(f"  OpenAI Requests/Day: {openai_config.get('max_requests_per_day', 'N/A')}")
        
        alert_config = config.get('alerts', {})
        print(f"  Max Daily Alerts: {alert_config.get('max_daily_alerts', 'N/A')}")
        
        news_config = config.get('news_ingestion', {})
        print(f"  Max Daily Headlines: {news_config.get('max_daily_headlines', 'N/A')}")
        print(f"  Max AI Calls: {news_config.get('max_daily_ai_calls', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Error validating configuration: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 