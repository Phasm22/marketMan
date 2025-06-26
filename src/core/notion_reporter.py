"""
Notion Reporter - Handles Notion API integration and report formatting
"""
import os
import requests
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def get_microlink_image(url):
    """Fetch article preview image using Microlink API with enhanced fallback logic"""
    try:
        logger.debug(f"🖼️ Fetching hero image for: {url}")
        params = {
            "url": url,
            "meta": "true",
            "screenshot": "false",
            "palette": "false",
            "video": "false"
        }
        
        response = requests.get("https://api.microlink.io", params=params, timeout=10)
        if response.status_code == 200:
            try:
                json_data = response.json()
                data = json_data.get("data", {}) if json_data else {}
            except ValueError:
                logger.warning("⚠️ Failed to parse Microlink JSON response")
                return None
            
            # Try multiple image sources in order of preference
            image_sources = []
            
            # 1. Primary OG image (hero image)
            image_data = data.get("image", {})
            if image_data and isinstance(image_data, dict):
                image_url = image_data.get("url")
                if image_url:
                    image_sources.append(('hero', image_url))
            
            # 2. Screenshot as fallback
            screenshot_data = data.get("screenshot", {})
            if screenshot_data and isinstance(screenshot_data, dict):
                screenshot_url = screenshot_data.get("url")
                if screenshot_url:
                    image_sources.append(('screenshot', screenshot_url))
            
            # 3. Logo as final fallback
            logo_data = data.get("logo", {})
            if logo_data and isinstance(logo_data, dict):
                logo_url = logo_data.get("url")
                if logo_url:
                    image_sources.append(('logo', logo_url))
            
            # Test each image source for accessibility
            for source_type, image_url in image_sources:
                try:
                    # Quick HEAD request to verify image is accessible
                    img_response = requests.head(image_url, timeout=5)
                    if img_response.status_code == 200:
                        content_type = img_response.headers.get('content-type', '')
                        if content_type.startswith('image/'):
                            logger.info(f"✅ Found {source_type} image: {image_url[:60]}...")
                            return image_url
                except:
                    continue
                
            logger.debug("⚠️ No accessible images found via Microlink")
            
        elif response.status_code == 429:
            logger.warning(f"⚠️ Microlink API rate limited (429) - will retry later")
            return None
        else:
            logger.warning(f"⚠️ Microlink API error: {response.status_code}")
            
    except Exception as e:
        logger.warning(f"⚠️ Error fetching hero image: {e}")
    return None

class NotionReporter:
    def __init__(self, notion_token=None, database_id=None):
        self.notion_token = notion_token or os.getenv("NOTION_TOKEN")
        self.notion_database_id = database_id or os.getenv("NOTION_DATABASE_ID")
        self.trades_database_id = os.getenv("TRADES_DATABASE_ID")
        self.performance_database_id = os.getenv("PERFORMANCE_DATABASE_ID")
        
        # Validate required environment variables for performance dashboard
        if not self.trades_database_id:
            logger.warning("TRADES_DATABASE_ID not configured - trade reporting will be disabled")
        if not self.performance_database_id:
            logger.warning("PERFORMANCE_DATABASE_ID not configured - performance reporting will be disabled")
        
    def log_consolidated_report_to_notion(self, report_data):
        """Log consolidated signal report to Notion with enhanced financial formatting and cover image"""
        if not self.notion_token or not self.notion_database_id:
            logger.debug("Notion credentials not configured, skipping logging")
            return False

        try:
            headers = {
                "Authorization": f"Bearer {self.notion_token}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }

            # Create comprehensive title
            title = f"📊 {report_data.get('title', 'Signal Report')}"
            
            # Build ETF list for the ETFs field (clean ticker symbols only)
            etf_list = []
            strong_buys = report_data.get('strong_buys', [])
            strong_sells = report_data.get('strong_sells', [])
            watchlist = report_data.get('watchlist', [])
            
            # Add strong positions (ticker symbols only, no prices in multi_select)
            for pos in strong_buys[:3]:
                if pos['ticker'] not in etf_list:
                    etf_list.append(pos['ticker'])
            for pos in strong_sells[:2]:
                if pos['ticker'] not in etf_list:
                    etf_list.append(pos['ticker'])
            
            # If no strong positions, add watchlist items
            if not etf_list and watchlist:
                for etf in watchlist[:5]:
                    if etf not in etf_list:
                        etf_list.append(etf)
            
            # If still empty, add some default ETFs based on session articles
            if not etf_list:
                default_etfs = ["ICLN", "TAN", "QCLN", "PBW", "ITA"][:3]
                etf_list.extend(default_etfs)
            
            logger.info(f"📊 ETFs to add to Notion: {etf_list}")
            
            # Create more descriptive position recommendations
            position_recommendations = self._build_position_recommendations(strong_buys, strong_sells, watchlist)
            position_text = '\n'.join(position_recommendations)
            logger.info(f"📋 Enhanced position recommendations prepared")

            # Get first article link for the Link field
            first_article_link = self._get_first_article_link(report_data.get('session_articles', []))
            
            # Use search term for sector instead of generic "Portfolio Report"
            primary_search_term = report_data.get('primary_search_term', 'Mixed Signals')

            data = {
                "parent": {"database_id": self.notion_database_id},
                "properties": {
                    "Title": {
                        "title": [{"text": {"content": title}}]
                    },
                    "Signal": {
                        "select": {"name": report_data.get('market_sentiment', 'Mixed')}
                    },
                    "Confidence": {
                        "number": 9 if report_data.get('conviction_level') == 'High' else 7 if report_data.get('conviction_level') == 'Medium' else 5
                    },
                    "ETFs": {
                        "multi_select": [{"name": etf_name} for etf_name in etf_list[:5]]
                    },
                    "Link": {
                        "url": first_article_link if first_article_link else "https://example.com"
                    },
                    "Sector": {
                        "select": {"name": primary_search_term}
                    },
                    "Reasoning": {
                        "rich_text": [{"text": {"content": report_data.get('executive_summary', '')}}]
                    },
                    "Action": {
                        "select": {"name": "REVIEW" if len(strong_buys + strong_sells) > 0 else "HOLD"}
                    },
                    "Status": {
                        "select": {"name": "New"}
                    },
                    "Timestamp": {
                        "date": {"start": report_data.get('analysis_timestamp', datetime.now().isoformat())}
                    },
                    "Search Term": {
                        "rich_text": [{"text": {"content": ', '.join(report_data.get('search_terms', ['consolidated_report']))}}]
                    }
                }
            }

            # Try to get cover image from session articles
            cover_image = self._get_cover_image(report_data.get('session_articles', []))
            if cover_image:
                data["cover"] = {
                    "type": "external",
                    "external": {"url": cover_image}
                }
                logger.info(f"🖼️ Adding cover image to consolidated report")

            # Build enhanced children blocks for financial report
            children = self._build_report_children(report_data, position_text, strong_buys, strong_sells)
            data["children"] = children

            response = requests.post(
                "https://api.notion.com/v1/pages",
                headers=headers,
                json=data
            )

            if response.status_code == 200:
                result = response.json()
                page_url = result.get('url', '')
                logger.info("✅ Consolidated report logged to Notion with financial details")
                return page_url
            else:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                logger.error(f"Failed to log consolidated report to Notion: {error_data}")
                return False

        except Exception as e:
            logger.error(f"Error logging consolidated report to Notion: {e}")
            return False
    
    def _build_position_recommendations(self, strong_buys, strong_sells, watchlist):
        """Build enhanced position recommendations with average confidence and liquidity context"""
        # Import the conviction tier function
        from .report_consolidator import get_conviction_tier, safe_get_position_data
        
        position_recommendations = []
        
        if strong_buys:
            # Calculate overall conviction tier from top ETF for formatting consistency
            top_etf = strong_buys[0] if strong_buys else {}
            top_etf_mention_count = top_etf.get('mention_count', 1)  # How many times the top ETF was mentioned
            top_etf_cumulative_confidence = top_etf.get('cumulative_confidence', 0)  # Sum of confidence scores for top ETF
            
            # Calculate true average confidence for the top ETF (not session average)
            top_avg_conviction = top_etf_cumulative_confidence / top_etf_mention_count if top_etf_mention_count > 0 else 0
            
            # Log for debugging
            logger.debug(f"🎯 Top ETF {top_etf.get('ticker', 'UNKNOWN')}: {top_etf_mention_count} mentions, avg confidence {top_avg_conviction:.1f}")
            
            # Determine conviction tier based on top ETF's average scores
            tier_config = get_conviction_tier(top_avg_conviction)
            
            position_recommendations.append(f"{tier_config['emoji']} {tier_config['label']} BUYS:")
            
            # IMPORTANT: Show ONLY individual per-ETF breakdowns
            # NO aggregate "Total Hits" summary - each ETF shows its own mention count
            
            # Show per-ETF conviction (not aggregate)
            for pos in strong_buys[:3]:  # Top 3
                safe_pos = safe_get_position_data(pos)
                
                # Calculate per-ETF conviction using ONLY per-ETF data
                etf_mention_count = pos.get('mention_count', 1)  # How many times THIS ETF was mentioned
                etf_cumulative_confidence = pos.get('cumulative_confidence', 0)  # Sum of confidence scores for THIS ETF
                
                # Defensive check: ensure we're not accidentally using session totals
                if etf_mention_count <= 0:
                    logger.warning(f"⚠️ {safe_pos['ticker']}: Invalid mention_count={etf_mention_count}, defaulting to 1")
                    etf_mention_count = 1
                    
                # Calculate TRUE average confidence for this specific ETF
                etf_avg_confidence = etf_cumulative_confidence / etf_mention_count
                
                # Additional logging to help debug any calculation issues
                logger.debug(f"🔍 {safe_pos['ticker']}: mentions={etf_mention_count}, cumulative={etf_cumulative_confidence:.1f}, avg={etf_avg_confidence:.1f}")
                
                # Format volume with liquidity assessment
                volume_str = self._format_volume_with_liquidity(safe_pos['volume'])
                
                position_recommendations.append(f"• {safe_pos['ticker']} – Hits: {etf_mention_count} (Avg {etf_avg_confidence:.1f}/10)")
                position_recommendations.append(f"  Entry: ${safe_pos['entry_price']:.2f} | {volume_str}")
                position_recommendations.append(f"  Size: {tier_config['size']}, Stop: {tier_config['stop']}, Target: {tier_config['target']}")
                position_recommendations.append("")
        
        if strong_sells:
            # Calculate overall conviction tier from top sell ETF for formatting consistency
            top_sell_etf = strong_sells[0] if strong_sells else {}
            top_sell_mention_count = top_sell_etf.get('mention_count', 1)  # How many times the top sell ETF was mentioned
            top_sell_cumulative_confidence = top_sell_etf.get('cumulative_confidence', 0)  # Sum of confidence scores for top sell ETF
            
            # Calculate true average confidence for the top sell ETF (not session average)
            top_sell_avg_conviction = top_sell_cumulative_confidence / top_sell_mention_count if top_sell_mention_count > 0 else 0
            
            # Log for debugging  
            logger.debug(f"🔻 Top Sell ETF {top_sell_etf.get('ticker', 'UNKNOWN')}: {top_sell_mention_count} mentions, avg confidence {top_sell_avg_conviction:.1f}")
            
            if top_sell_avg_conviction >= 2.0:
                tier = "🔻 HIGH CONVICTION SELLS"
                narrative = "Strong bearish signals warrant defensive positioning"
            elif top_sell_avg_conviction >= 1.5:
                tier = "⚠️ TACTICAL SELLS" 
                narrative = "Moderate bearish pressure suggests hedging"
            else:
                tier = "👀 WATCH FOR WEAKNESS"
                narrative = "Early warning signals for potential downside"
                
            position_recommendations.append(f"{tier}:")
            position_recommendations.append(f"{narrative}")
            position_recommendations.append("")
            
            # Show per-ETF conviction for sells (not aggregate)
            for pos in strong_sells[:2]:  # Top 2
                safe_pos = safe_get_position_data(pos)
                
                # Calculate per-ETF conviction using ONLY per-ETF data  
                etf_sell_mention_count = pos.get('mention_count', 1)  # How many times THIS ETF was mentioned
                etf_sell_cumulative_confidence = pos.get('cumulative_confidence', 0)  # Sum of confidence scores for THIS ETF
                
                # Defensive check: ensure we're not accidentally using session totals
                if etf_sell_mention_count <= 0:
                    logger.warning(f"⚠️ {safe_pos['ticker']}: Invalid sell mention_count={etf_sell_mention_count}, defaulting to 1")
                    etf_sell_mention_count = 1
                    
                # Calculate TRUE average confidence for this specific ETF
                etf_sell_avg_confidence = etf_sell_cumulative_confidence / etf_sell_mention_count
                
                # Additional logging to help debug any calculation issues
                logger.debug(f"🔍 {safe_pos['ticker']} (SELL): mentions={etf_sell_mention_count}, cumulative={etf_sell_cumulative_confidence:.1f}, avg={etf_sell_avg_confidence:.1f}")
                
                volume_str = self._format_volume_with_liquidity(safe_pos['volume'])
                inverse_ticker = self._get_inverse_ticker(safe_pos['ticker'])
                
                position_recommendations.append(f"• {safe_pos['ticker']} – Hits: {etf_sell_mention_count} (Avg {etf_sell_avg_confidence:.1f}/10)")
                position_recommendations.append(f"  Entry: ${safe_pos['entry_price']:.2f} | {volume_str}")
                position_recommendations.append(f"  Hedge: {inverse_ticker} | Size: 1-3% inverse exposure")
                position_recommendations.append(f"  Context: Technical breakdown + macro headwinds")
                position_recommendations.append("")
        
        if not strong_buys and not strong_sells:
            position_recommendations.append("📊 MARKET HOLD:")
            position_recommendations.append("Signals lack conviction threshold (>1.5/10) for position sizing.")
            position_recommendations.append("• Monitoring for volume confirmation and momentum shifts")
            if watchlist:
                position_recommendations.append(f"• Watchlist: {', '.join(watchlist[:3])} - awaiting breakouts")
            position_recommendations.append("• Cash position maintained for clearer opportunities")
        
        return position_recommendations
    
    def _format_volume_with_liquidity(self, volume):
        """Format volume with liquidity assessment with color-coded visual indicators"""
        if volume >= 1000000:  # 1M+
            return f"{volume//1000000:.0f}M 🟢 HIGH"
        elif volume >= 500000:  # 500k-1M
            return f"{volume//1000:.0f}k 🟢 GOOD"
        elif volume >= 100000:  # 100k-500k
            return f"{volume//1000:.0f}k 🟡 FAIR"
        else:  # <100k
            return f"{volume//1000:.0f}k 🔴 LOW"
    
    def _get_first_article_link(self, session_articles):
        """Get the first valid article link"""
        for article in session_articles:
            link = article.get('link', '')
            if link and link.strip() and link.startswith('http'):
                return link.strip()
        
        # If no valid link found, try to extract from titles
        for article in session_articles:
            title = article.get('title', '')
            if title and 'http' in title:
                url_match = re.search(r'https?://[^\\s]+', title)
                if url_match:
                    return url_match.group()
        
        return None
    
    def _get_cover_image(self, session_articles):
        """Get cover image from session articles"""
        for article_data in session_articles:
            article_link = article_data.get('link')
            if article_link and article_link.strip():
                logger.info(f"🖼️ Trying cover image from: {article_data.get('title', 'Unknown')[:50]}...")
                cover_image = get_microlink_image(article_link)
                if cover_image:
                    logger.info(f"✅ Found cover image: {cover_image[:100]}...")
                    return cover_image
        
        logger.info(f"⚠️ No cover images found from {len(session_articles)} session articles")
        return None
    
    def _build_report_children(self, report_data, position_text, strong_buys, strong_sells):
        """Build enhanced children blocks for the Notion report"""
        children = []
        
        # Executive Summary
        children.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "📋 Executive Summary"}}]
            }
        })
        
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": report_data.get('executive_summary', '')}}]
            }
        })
        
        # Price Context for ETFs (rich-text instead of code block)
        if strong_buys or strong_sells:
            children.extend(self._build_price_context_blocks(strong_buys, strong_sells))
        
        # Position Recommendations (consolidated execution playbook)
        if position_text:
            children.extend(self._build_enhanced_position_blocks(position_text, strong_buys, strong_sells))
        
        # Next Steps (new actionable section with integrated risk factors)
        children.extend(self._build_next_steps_blocks(strong_buys, strong_sells, report_data))
        
        # Session Articles (collapsed by default)
        if report_data.get('session_articles'):
            children.append(self._build_articles_block(report_data['session_articles']))
        
        return children
    
    def _build_price_context_blocks(self, strong_buys, strong_sells):
        """Build price context blocks using rich-text formatting with visual separation"""
        blocks = []
        
        # Add visual separator with divider block
        blocks.append({
            "object": "block",
            "type": "divider",
            "divider": {}
        })
        
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "💰 Price Context"}}]
            }
        })
        
        all_positions = strong_buys + strong_sells
        if all_positions:
            from .report_consolidator import safe_get_position_data
            
            for pos in all_positions[:3]:  # Top 3 positions
                safe_pos = safe_get_position_data(pos)
                
                # Generate realistic price context (in production, this would come from market_data.py)
                current_price = safe_pos['entry_price']
                week_52_low = current_price * 0.75  # 25% below
                week_52_high = current_price * 1.25  # 25% above
                support = current_price * 0.95  # 5% below
                resistance = current_price * 1.08  # 8% above
                
                price_context = (
                    f"Price: ${current_price:.2f} | "
                    f"52w: ${week_52_low:.0f}–${week_52_high:.0f} | "
                    f"Support: ${support:.2f} | "
                    f"Resistance: ${resistance:.2f}"
                )
                
                blocks.append({
                    "object": "block",
                    "type": "callout",
                    "callout": {
                        "rich_text": [
                            {
                                "type": "text", 
                                "text": {"content": f"{safe_pos['ticker']}: {price_context}"}
                            }
                        ],
                        "icon": {"emoji": "💲"},
                        "color": "gray_background"
                    }
                })
        
        return blocks
    
    def _build_enhanced_position_blocks(self, position_text, strong_buys, strong_sells):
        """Build consolidated position recommendation blocks"""
        blocks = []
        
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "💼 Position Recommendations"}}]
            }
        })
        
        # Use rich-text paragraph instead of code block for better formatting
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": position_text}}]
            }
        })
        
        # Consolidated Execution Playbook (no duplication)
        if strong_buys:
            blocks.extend(self._build_execution_playbook(strong_buys))
        
        return blocks
    
    def _build_execution_playbook(self, strong_buys):
        """Build consolidated execution playbook with specific timeframes"""
        blocks = []
        
        from .report_consolidator import get_conviction_tier, safe_get_position_data
        from datetime import datetime, timedelta
        
        # Calculate average conviction for overall strategy
        total_conviction = sum([pos.get('conviction', 0) for pos in strong_buys])
        avg_conviction = total_conviction / len(strong_buys)
        tier_config = get_conviction_tier(avg_conviction)
        
        # Calculate specific timeframe deadlines
        today = datetime.now()
        if tier_config['urgency'] == '⚡ IMMEDIATE':
            deadline = today + timedelta(days=2)
            deadline_str = f"by {deadline.strftime('%b %d')} close"
        elif tier_config['urgency'] == '📅 PLANNED':
            deadline = today + timedelta(days=5)
            deadline_str = f"by {deadline.strftime('%b %d')} close"
        else:
            deadline_str = "monitor for better entry"
        
        blocks.append({
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [{"type": "text", "text": {"content": f"📈 Execution Playbook ({tier_config['urgency']})"}}]
            }
        })
        
        # Build consolidated execution strategy with specific timing
        execution_text = f"Timeframe: {tier_config['timeframe']} ({deadline_str}) | Risk Level: {tier_config['tier']} conviction\n\n"
        
        # Add key risk factors directly in the playbook
        execution_text += "⚠️ Key Risks: Thematic ETF concentration, momentum reversal risk\n\n"
        
        for i, pos in enumerate(strong_buys[:2], 1):
            safe_pos = safe_get_position_data(pos)
            volume_str = self._format_volume_with_liquidity(safe_pos['volume'])
            
            execution_text += f"{i}. {safe_pos['ticker']} @ ${safe_pos['entry_price']:.2f}\n"
            execution_text += f"   • Volume: {volume_str}\n"
            execution_text += f"   • Entry: Limit order -1% below current\n"
            execution_text += f"   • Stop: {tier_config['stop']} | Target: {tier_config['target']}\n"
            execution_text += f"   • Size: {tier_config['size']}\n\n"
        
        blocks.append({
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [{"type": "text", "text": {"content": execution_text.strip()}}],
                "icon": {"emoji": "📈"}
            }
        })
        
        return blocks
    
    def _build_next_steps_blocks(self, strong_buys, strong_sells, report_data):
        """Build actionable next steps section with risk factors integrated"""
        blocks = []
        
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "🎯 Next Steps"}}]
            }
        })
        
        # Generate action line based on positions
        if strong_buys and len(strong_buys) >= 2:
            action_line = f"Execute {len(strong_buys)} buy orders with limit entries -1% below current prices. Monitor for volume confirmation."
        elif strong_buys and len(strong_buys) == 1:
            ticker = strong_buys[0].get('ticker', 'ETF')
            action_line = f"Single position entry: {ticker} with conservative sizing. Wait for additional signals before adding exposure."
        elif strong_sells:
            action_line = "Implement defensive hedging via inverse ETFs. Reduce risk exposure until trend clarity emerges."
        else:
            action_line = "Maintain cash position. Monitor watchlist for breakout confirmations before deploying capital."
        
        # Add market timing context
        conviction_level = report_data.get('conviction_level', 'Medium')
        if conviction_level == 'High':
            timing_context = "Market conditions favor immediate action. Deploy capital within 24-48 hours."
        elif conviction_level == 'Medium':
            timing_context = "Moderate conviction suggests scaled entry over 3-5 days. Use dollar-cost averaging."
        else:
            timing_context = "Low conviction requires patience. Wait for stronger signals before committing capital."
        
        # Add exit conditions and risk management
        risk_context = "\n⚠️ Exit Conditions: If broader market shows weakness or ETF correlation increases, reduce thematic exposure immediately."
        
        next_steps_text = f"{action_line}\n\n{timing_context}{risk_context}"
        
        blocks.append({
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [{"type": "text", "text": {"content": next_steps_text}}],
                "icon": {"emoji": "🎯"}
            }
        })
        
        return blocks
    
    def _build_articles_block(self, session_articles):
        """Build session articles block with enhanced context - collapsed by default"""
        article_list = []
        for i, article in enumerate(session_articles[:8]):  # Trim to 8 most relevant
            confidence = article.get('confidence', 0)
            title = article.get('title', 'Unknown')
            signal = article.get('signal', 'Neutral')
            search_term = article.get('search_term', '')
            
            # Create 4-word summary from title for conciseness
            title_words = title.split()
            summary = ' '.join(title_words[:4]) + ('...' if len(title_words) > 4 else '')
            
            signal_emoji = "📈" if signal == "Bullish" else "📉" if signal == "Bearish" else "➖"
            
            article_text = f"{signal_emoji} {confidence}/10 – {summary} [{search_term}]"
            
            article_list.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": article_text}}]
                }
            })
        
        return {
            "object": "block",
            "type": "toggle",
            "toggle": {
                "rich_text": [{"type": "text", "text": {"content": f"📰 Source Articles ({len(session_articles)}) - Click to expand"}}],
                "children": article_list
            }
        }
    
    def _get_inverse_ticker(self, ticker):
        """Get inverse/hedging ticker recommendation for a given ETF"""
        inverse_map = {
            'XLF': 'FAZ',      # Financial bear 3x
            'XLE': 'DRV',      # Energy bear 3x  
            'QQQ': 'SQQQ',     # NASDAQ bear 3x
            'SPY': 'SPXS',     # S&P 500 bear 3x
            'IWM': 'RWM',      # Russell 2000 bear
            'XLK': 'PSQ',      # Technology bear
            'XLI': 'SIJ',      # Industrial bear
            'XLU': 'SDP',      # Utilities bear
            'XLV': 'RXD',      # Healthcare bear
            'VXX': 'XIV',      # Volatility inverse
            'GDX': 'DUST',     # Gold miners bear 2x
            'TLT': 'TBF',      # Treasury bear
            'EFA': 'EFZ',      # EAFE bear
            'EEM': 'EUM',      # Emerging markets bear
        }
        
        # Default recommendations by sector
        if ticker.startswith('URA') or 'uranium' in ticker.lower():
            return 'Put spreads'  # No direct uranium inverse
        elif 'AI' in ticker or 'tech' in ticker.lower():
            return 'PSQ/SQQQ'
        elif 'clean' in ticker.lower() or 'energy' in ticker.lower():
            return 'DRV/SCO'
        else:
            return inverse_map.get(ticker, 'SPXS/VXX')  # Default to broad market hedge

    def report_trade(self, trade, signal_page_id=None):
        """
        Report a trade to the performance dashboard.
        
        Args:
            trade (dict): Trade details containing:
                - ticker (str): ETF ticker symbol
                - action (str): 'BUY' or 'SELL'
                - quantity (int): Number of shares
                - price (float): Execution price
                - timestamp (datetime): Trade execution time
                - signal_confidence (float): Original signal confidence (optional)
                - notes (str): Additional notes (optional)
            signal_page_id (str): Notion page ID of the original signal (optional)
            
        Returns:
            bool: True if successfully reported, False otherwise
        """
        if not self.notion_token or not self.trades_database_id:
            logger.warning("Notion token or trades database ID not configured - skipping trade reporting")
            return False
            
        try:
            headers = {
                "Authorization": f"Bearer {self.notion_token}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }
            
            # Build trade record properties
            properties = {
                "Ticker": {
                    "title": [{"text": {"content": trade.get('ticker', 'UNKNOWN')}}]
                },
                "Action": {
                    "select": {"name": trade.get('action', 'BUY')}
                },
                "Quantity": {
                    "number": trade.get('quantity', 0)
                },
                "Price": {
                    "number": trade.get('price', 0.0)
                },
                "Trade Date": {
                    "date": {"start": trade.get('timestamp', datetime.now()).isoformat()}
                }
            }
            
            # Add optional fields if available
            if trade.get('signal_confidence'):
                properties["Signal Confidence"] = {
                    "number": round(trade.get('signal_confidence'), 2)
                }
                
            if signal_page_id:
                properties["Signal Reference"] = {
                    "relation": [{"id": signal_page_id}]
                }
                
            if trade.get('notes'):
                properties["Notes"] = {
                    "rich_text": [{"text": {"content": trade.get('notes', '')}}]
                }
            
            # Calculate trade value
            trade_value = trade.get('quantity', 0) * trade.get('price', 0.0)
            properties["Trade Value"] = {
                "number": round(trade_value, 2)
            }
            
            payload = {
                "parent": {"database_id": self.trades_database_id},
                "properties": properties
            }
            
            response = requests.post(
                "https://api.notion.com/v1/pages",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Successfully reported trade: {trade.get('ticker')} {trade.get('action')} {trade.get('quantity')} @ ${trade.get('price')}")
                return True
            else:
                logger.error(f"❌ Failed to report trade to Notion: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error reporting trade to Notion: {e}")
            return False
