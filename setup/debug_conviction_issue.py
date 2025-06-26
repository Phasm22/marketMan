#!/usr/bin/env python3
"""
Debug script to identify the conviction calculation issue
"""

import sys
import os
sys.path.append('/root/marketMan/src')

from core.report_consolidator import create_consolidated_signal_report
from core.notion_reporter import NotionReporter

def debug_conviction_issue():
    """Debug the exact scenario the user described"""
    
    # Create a scenario that matches the user's description:
    # 9 total analyses, with BOTZ mentioned in 3, ROBO in 3, IRBO in 3
    mock_analyses = [
        # BOTZ mentioned in analyses 1, 2, 3
        {'confidence': 8.0, 'signal': 'Bullish', 'affected_etfs': ['BOTZ'], 'sector': 'AI', 'reasoning': 'AI boom 1', 'source_article': {'title': 'AI Rally 1', 'search_term': 'AI', 'link': 'http://example.com/1'}},
        {'confidence': 7.0, 'signal': 'Bullish', 'affected_etfs': ['BOTZ'], 'sector': 'AI', 'reasoning': 'AI boom 2', 'source_article': {'title': 'AI Rally 2', 'search_term': 'AI', 'link': 'http://example.com/2'}},
        {'confidence': 7.8, 'signal': 'Bullish', 'affected_etfs': ['BOTZ'], 'sector': 'AI', 'reasoning': 'AI boom 3', 'source_article': {'title': 'AI Rally 3', 'search_term': 'AI', 'link': 'http://example.com/3'}},
        
        # ROBO mentioned in analyses 4, 5, 6
        {'confidence': 7.5, 'signal': 'Bullish', 'affected_etfs': ['ROBO'], 'sector': 'Robotics', 'reasoning': 'Robot surge 1', 'source_article': {'title': 'Robot News 1', 'search_term': 'robotics', 'link': 'http://example.com/4'}},
        {'confidence': 8.0, 'signal': 'Bullish', 'affected_etfs': ['ROBO'], 'sector': 'Robotics', 'reasoning': 'Robot surge 2', 'source_article': {'title': 'Robot News 2', 'search_term': 'robotics', 'link': 'http://example.com/5'}},
        {'confidence': 7.3, 'signal': 'Bullish', 'affected_etfs': ['ROBO'], 'sector': 'Robotics', 'reasoning': 'Robot surge 3', 'source_article': {'title': 'Robot News 3', 'search_term': 'robotics', 'link': 'http://example.com/6'}},
        
        # IRBO mentioned in analyses 7, 8, 9
        {'confidence': 6.8, 'signal': 'Bullish', 'affected_etfs': ['IRBO'], 'sector': 'Robotics', 'reasoning': 'Intl robots 1', 'source_article': {'title': 'Intl Robot 1', 'search_term': 'robotics', 'link': 'http://example.com/7'}},
        {'confidence': 6.5, 'signal': 'Bullish', 'affected_etfs': ['IRBO'], 'sector': 'Robotics', 'reasoning': 'Intl robots 2', 'source_article': {'title': 'Intl Robot 2', 'search_term': 'robotics', 'link': 'http://example.com/8'}},
        {'confidence': 6.7, 'signal': 'Bullish', 'affected_etfs': ['IRBO'], 'sector': 'Robotics', 'reasoning': 'Intl robots 3', 'source_article': {'title': 'Intl Robot 3', 'search_term': 'robotics', 'link': 'http://example.com/9'}},
    ]
    
    print(f"🔍 DEBUGGING CONVICTION CALCULATION ISSUE")
    print("=" * 60)
    print(f"📊 Setup: 9 total analyses")
    print(f"   • BOTZ mentioned in 3 analyses: 8.0, 7.0, 7.8 (should avg 7.6)")
    print(f"   • ROBO mentioned in 3 analyses: 7.5, 8.0, 7.3 (should avg 7.6)")  
    print(f"   • IRBO mentioned in 3 analyses: 6.8, 6.5, 6.7 (should avg 6.7)")
    
    # Create consolidated report
    report = create_consolidated_signal_report(mock_analyses, "debug_session")
    
    if report and report.get('strong_buys'):
        print(f"\n🔍 RAW DATA FROM CONSOLIDATOR:")
        print("-" * 40)
        for pos in report['strong_buys']:
            ticker = pos.get('ticker')
            mention_count = pos.get('mention_count', 0)
            cumulative_confidence = pos.get('cumulative_confidence', 0)
            conviction = pos.get('conviction', 0)  # This is the adjusted score
            calc_avg = cumulative_confidence / mention_count if mention_count > 0 else 0
            
            print(f"\n{ticker}:")
            print(f"  mention_count: {mention_count}")
            print(f"  cumulative_confidence: {cumulative_confidence}")
            print(f"  conviction (adjusted): {conviction:.2f}")
            print(f"  calculated_avg: {calc_avg:.2f}")
        
        print(f"\n🖼️ NOTION REPORTER OUTPUT:")
        print("-" * 40)
        notion_reporter = NotionReporter()
        position_recs = notion_reporter._build_position_recommendations(
            report['strong_buys'], [], []
        )
        
        for line in position_recs:
            if line.strip():
                print(f"  {line}")
        
        print(f"\n🔍 DETAILED CALCULATION CHECK:")
        print("-" * 40)
        for pos in report['strong_buys']:
            ticker = pos.get('ticker')
            
            # These are the values the notion_reporter.py is using
            etf_hits = pos.get('mention_count', 1)
            etf_cumulative_confidence = pos.get('cumulative_confidence', pos.get('conviction', 0))
            etf_avg_confidence = etf_cumulative_confidence / etf_hits if etf_hits > 0 else 0
            
            print(f"\n{ticker} Notion Calculation:")
            print(f"  etf_hits = pos.get('mention_count', 1) = {etf_hits}")
            print(f"  etf_cumulative_confidence = pos.get('cumulative_confidence', pos.get('conviction', 0)) = {etf_cumulative_confidence}")
            print(f"  etf_avg_confidence = {etf_cumulative_confidence} / {etf_hits} = {etf_avg_confidence:.2f}")
            
            # Check if user's complaint would match this
            total_session_length = len(mock_analyses)
            wrong_calc = etf_cumulative_confidence / total_session_length if total_session_length > 0 else 0
            print(f"  ❌ IF using session length: {etf_cumulative_confidence} / {total_session_length} = {wrong_calc:.2f}")
    
    else:
        print("❌ No strong buys found in report")

if __name__ == "__main__":
    debug_conviction_issue()
