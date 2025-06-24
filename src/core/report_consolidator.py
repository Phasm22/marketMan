"""
Report Consolidator - Creates consolidated reports from multiple analyses
"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def create_consolidated_signal_report(all_analyses, session_timestamp):
    """Create a single consolidated report from multiple analyses with proper financial terminology"""
    if not all_analyses:
        return None
    
    # Group analyses by sector and signal strength
    high_conviction = [a for a in all_analyses if a.get('confidence', 0) >= 8]
    medium_conviction = [a for a in all_analyses if 6 <= a.get('confidence', 0) < 8]
    
    # Aggregate ETF recommendations with current prices
    etf_positions = {}
    total_signals = len(all_analyses)
    
    for analysis in all_analyses:
        for etf in analysis.get('affected_etfs', []):
            if etf not in etf_positions:
                etf_positions[etf] = {
                    'signals': [],
                    'net_score': 0,
                    'current_price': 0,
                    'volume': 0
                }
            
            # Score: Bullish=+1, Bearish=-1, Neutral=0, weighted by confidence
            signal_weight = analysis.get('confidence', 0) / 10
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
    
    # Determine top recommendations (minimum 2 signals, net score > 0.5)
    strong_buys = []
    strong_sells = []
    
    for etf, data in etf_positions.items():
        if len(data['signals']) >= 2:  # Multiple confirmations
            if data['net_score'] >= 1.0:  # Strong bullish consensus
                strong_buys.append({
                    'ticker': etf,
                    'conviction': data['net_score'],
                    'entry_price': data['current_price'],
                    'volume': data['volume'],
                    'signals_count': len(data['signals'])
                })
            elif data['net_score'] <= -1.0:  # Strong bearish consensus
                strong_sells.append({
                    'ticker': etf,
                    'conviction': abs(data['net_score']),
                    'entry_price': data['current_price'],
                    'volume': data['volume'],
                    'signals_count': len(data['signals'])
                })
    
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
    
    # Create consolidated report
    report = {
        'title': f"MarketMan Signal Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        'session_timestamp': session_timestamp,
        'executive_summary': f"Analyzed {total_signals} market signals. Primary focus: {display_sector}. {len(strong_buys)} strong buy recommendations, {len(strong_sells)} strong sell recommendations.",
        'market_sentiment': 'Bullish' if len([a for a in all_analyses if a.get('signal') == 'Bullish']) > len(all_analyses) / 2 else 'Bearish' if len([a for a in all_analyses if a.get('signal') == 'Bearish']) > len(all_analyses) / 2 else 'Mixed',
        'conviction_level': 'High' if len(high_conviction) > 0 else 'Medium' if len(medium_conviction) > 0 else 'Low',
        'strong_buys': strong_buys[:5],  # Top 5
        'strong_sells': strong_sells[:3],  # Top 3
        'watchlist': [etf for etf, data in etf_positions.items() if 0.3 <= abs(data['net_score']) < 1.0][:10],
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
        'analysis_timestamp': datetime.now().isoformat()
    }
    
    return report
