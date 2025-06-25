"""
Report Consolidator - Creates consolidated reports from multiple analyses
"""
import logging
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

def get_conviction_tier(score):
    """Get conviction tier configuration based on score"""
    if score >= 2.5:
        return {
            "tier": "High", 
            "emoji": "🎯", 
            "label": "HIGH CONVICTION",
            "size": "3-5%", 
            "stop": "-8%", 
            "target": "+20-30%",
            "urgency": "⚡ IMMEDIATE",
            "timeframe": "1-2 days"
        }
    elif score >= 1.5:
        return {
            "tier": "Medium", 
            "emoji": "📈", 
            "label": "MEDIUM CONVICTION",
            "size": "2-3%", 
            "stop": "-6%", 
            "target": "+15-20%",
            "urgency": "📅 PLANNED",
            "timeframe": "3-5 days"
        }
    else:
        return {
            "tier": "Tactical", 
            "emoji": "⚡", 
            "label": "TACTICAL",
            "size": "1-2%", 
            "stop": "-5%", 
            "target": "+10-15%",
            "urgency": "👁️ MONITOR",
            "timeframe": "5-10 days"
        }

def safe_get_position_data(pos):
    """Safely extract position data with defaults"""
    return {
        'ticker': pos.get('ticker', 'UNKNOWN'),
        'conviction': pos.get('conviction', 0.0),
        'entry_price': pos.get('entry_price', 0.0),
        'volume': pos.get('volume', 0),
        'signals_count': pos.get('signals_count', 0)
    }

def calculate_adaptive_confidence(strong_buys, strong_sells):
    """Calculate adaptive confidence score from actual positions"""
    all_positions = strong_buys + strong_sells
    if not all_positions:
        return 5.0  # Neutral default
    
    # Get top 3 conviction scores for adaptive confidence
    conv_scores = [pos.get('conviction', 0) for pos in all_positions]
    top_scores = sorted(conv_scores, reverse=True)[:3]
    
    if top_scores:
        avg_score = sum(top_scores) / len(top_scores)
        # Scale to 1-10 range (conviction scores are typically 0-4 range)
        scaled_score = min(10, max(1, avg_score * 2.5))
        return round(scaled_score, 1)
    
    return 5.0

def create_consolidated_signal_report(all_analyses, session_timestamp):
    """Create a single consolidated report from multiple analyses with proper financial terminology"""
    if not all_analyses:
        return None
    
    # Group analyses by sector and signal strength with refined thresholds
    high_conviction = [a for a in all_analyses if a.get('confidence', 0) >= 7]
    medium_conviction = [a for a in all_analyses if 5 <= a.get('confidence', 0) < 7]
    low_conviction = [a for a in all_analyses if 3 <= a.get('confidence', 0) < 5]
    
    # Determine overall conviction level with more precision
    if len(high_conviction) >= 2:
        overall_conviction = 'High'
    elif len(high_conviction) >= 1 or len(medium_conviction) >= 2:
        overall_conviction = 'Medium'
    elif len(medium_conviction) >= 1 or len(low_conviction) >= 2:
        overall_conviction = 'Low-Medium'
    else:
        overall_conviction = 'Low'
    
    # Aggregate ETF recommendations with frequency + confidence scoring
    etf_positions = {}
    total_signals = len(all_analyses)
    
    for analysis in all_analyses:
        for etf in analysis.get('affected_etfs', []):
            if etf not in etf_positions:
                etf_positions[etf] = {
                    'signals': [],
                    'net_score': 0,
                    'current_price': 0,
                    'volume': 0,
                    'mention_count': 0,
                    'cumulative_confidence': 0
                }
            
            # Track frequency and cumulative confidence
            etf_positions[etf]['mention_count'] += 1
            etf_positions[etf]['cumulative_confidence'] += analysis.get('confidence', 0)
            
            # Score: Bullish=+1, Bearish=-1, Neutral=0, weighted by confidence
            # Use confidence as-is (1-10 scale), not as percentage
            signal_weight = analysis.get('confidence', 0) / 10 * 2  # Scale to make it more sensitive
            if analysis.get('signal') == 'Bullish':
                etf_positions[etf]['net_score'] += signal_weight
            elif analysis.get('signal') == 'Bearish':
                etf_positions[etf]['net_score'] -= signal_weight
            
            etf_positions[etf]['signals'].append({
                'signal': analysis.get('signal'),
                'confidence': analysis.get('confidence'),
                'reasoning': analysis.get('reasoning', '')[:100] + '...'
            })
            
            # Get current market data
            market_data = analysis.get('market_snapshot', {}).get(etf, {})
            if market_data:
                etf_positions[etf]['current_price'] = market_data.get('price', 0)
                etf_positions[etf]['volume'] = market_data.get('volume', 0)
    
    # Determine top recommendations with more nuanced scoring
    strong_buys = []
    strong_sells = []
    moderate_buys = []
    moderate_sells = []
    
    for etf, data in etf_positions.items():
        signal_count = len(data.get('signals', []))
        net_score = data.get('net_score', 0.0)
        
        # Strong positions now require both frequency AND confidence thresholds
        if signal_count >= 2:  # Multiple confirmations required
            frequency_bonus = min(data.get('mention_count', 0) / 2, 1.0)  # Up to 100% bonus for frequency
            adjusted_score = net_score * (1 + frequency_bonus)
            
            # Use safe data extraction with defaults
            position_data = {
                'ticker': etf,
                'conviction': adjusted_score,  # Now includes frequency bonus
                'entry_price': data.get('current_price', 0.0),
                'volume': data.get('volume', 0),
                'signals_count': signal_count,
                'mention_count': data.get('mention_count', 0),
                'cumulative_confidence': data.get('cumulative_confidence', 0)
            }
            
            if net_score >= 0.8:  # Adjusted threshold for new scoring
                strong_buys.append(position_data)
            elif net_score <= -0.8:  # Adjusted threshold for new scoring
                position_data['conviction'] = abs(net_score)
                strong_sells.append(position_data)
            elif 0.4 <= net_score < 0.8:  # Moderate bullish
                moderate_buys.append(position_data)
            elif -0.8 < net_score <= -0.4:  # Moderate bearish
                position_data['conviction'] = abs(net_score)
                moderate_sells.append(position_data)
    
    # If no strong signals, promote moderate signals
    if not strong_buys and moderate_buys:
        strong_buys = moderate_buys
    if not strong_sells and moderate_sells:
        strong_sells = moderate_sells
    
    # Sort by conviction
    strong_buys.sort(key=lambda x: x['conviction'], reverse=True)
    strong_sells.sort(key=lambda x: x['conviction'], reverse=True)
    
    # Generate executive summary
    primary_sectors = {}
    for analysis in all_analyses:
        sector = analysis.get('sector', 'Mixed')
        if sector not in primary_sectors:
            primary_sectors[sector] = 0
        primary_sectors[sector] += analysis.get('confidence', 0)
    
    # Calculate dominant sector from AI analysis (not search terms)
    dominant_sector = max(primary_sectors.keys(), key=lambda s: primary_sectors[s]) if primary_sectors else 'Mixed'
    
    # Map AI sectors to clean display names
    sector_display_map = {
        'AI': 'Artificial Intelligence',
        'CleanTech': 'Clean Energy',
        'Defense': 'Defense & Aerospace', 
        'Volatility': 'Volatility & Hedge',
        'Uranium': 'Nuclear & Uranium',
        'Broad Market': 'Broad Market',
        'Mixed': 'Mixed Signals'
    }
    
    # Use the properly classified sector from AI analysis
    display_sector = sector_display_map.get(dominant_sector, dominant_sector)
    
    # Get search terms for reference but don't use as sector
    search_terms = set()
    for analysis in all_analyses:
        search_term = analysis.get('source_article', {}).get('search_term', '')
        if search_term:
            search_terms.add(search_term)
    
    # Create consolidated report with Mountain Time
    mountain_tz = pytz.timezone('America/Denver')
    local_time = datetime.now(mountain_tz)
    
    # Calculate adaptive confidence from actual positions
    adaptive_confidence = calculate_adaptive_confidence(strong_buys, strong_sells)
    
    report = {
        'title': f"MarketMan Signal Report - {local_time.strftime('%Y-%m-%d %H:%M MT')}",
        'session_timestamp': session_timestamp,
        'executive_summary': f"Analyzed {total_signals} market signals. Primary focus: {display_sector}. {len(strong_buys)} strong buy recommendations, {len(strong_sells)} strong sell recommendations.",
        'market_sentiment': 'Bullish' if len([a for a in all_analyses if a.get('signal') == 'Bullish']) > len(all_analyses) / 2 else 'Bearish' if len([a for a in all_analyses if a.get('signal') == 'Bearish']) > len(all_analyses) / 2 else 'Mixed',
        'conviction_level': overall_conviction,
        'adaptive_confidence': adaptive_confidence,  # New adaptive score
        'strong_buys': strong_buys[:5],  # Top 5
        'strong_sells': strong_sells[:3],  # Top 3
        'watchlist': [etf for etf, data in etf_positions.items() if 0.3 <= abs(data.get('net_score', 0)) < 1.0][:10],
        'risk_level': 'High' if any(a.get('sector') == 'Volatility' for a in high_conviction) else 'Medium',
        'primary_search_term': display_sector,  # Now uses clean sector name instead of search term
        'search_terms': list(search_terms),
        'session_articles': [
            {
                'title': a.get('source_article', {}).get('title', a.get('title', '')),
                'confidence': a.get('confidence', 0),
                'link': a.get('source_article', {}).get('link', ''),
                'search_term': a.get('source_article', {}).get('search_term', ''),
                'signal': a.get('signal', 'Neutral')
            } for a in all_analyses
        ],
        'analysis_timestamp': local_time.isoformat()
    }
    
    return report
