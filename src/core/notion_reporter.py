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
        """Build position recommendations with tiered conviction system using centralized config"""
        # Import the conviction tier function
        from .report_consolidator import get_conviction_tier, safe_get_position_data
        
        position_recommendations = []
        
        if strong_buys:
            # Determine conviction tier based on actual scores using centralized function
            max_conviction = max([pos.get('conviction', 0) for pos in strong_buys])
            tier_config = get_conviction_tier(max_conviction)
            
            position_recommendations.append(f"{tier_config['emoji']} {tier_config['label']} BUYS:")
            for pos in strong_buys[:3]:  # Top 3
                safe_pos = safe_get_position_data(pos)
                position_recommendations.append(f"• {safe_pos['ticker']}: Entry ${safe_pos['entry_price']:.2f} | Score {safe_pos['conviction']:.1f}/10 | Vol {safe_pos['volume']:,}")
                position_recommendations.append(f"  Size: {tier_config['size']}, Stop: {tier_config['stop']}, Target: {tier_config['target']}")
        
        if strong_sells:
            # Enhanced tactical sell recommendations with macro context
            max_sell_conviction = max([pos.get('conviction', 0) for pos in strong_sells])
            sell_tier_config = get_conviction_tier(max_sell_conviction)
            
            if max_sell_conviction >= 2.0:
                tier = "🔻 HIGH CONVICTION SELLS"
                narrative = "Strong bearish signals warrant defensive positioning"
            elif max_sell_conviction >= 1.5:
                tier = "⚠️ TACTICAL SELLS" 
                narrative = "Moderate bearish pressure suggests hedging"
            else:
                tier = "👀 WATCH FOR WEAKNESS"
                narrative = "Early warning signals for potential downside"
                
            position_recommendations.append(f"{tier}:")
            position_recommendations.append(f"{narrative}")
            
            for pos in strong_sells[:2]:  # Top 2
                safe_pos = safe_get_position_data(pos)
                # Get inverse ticker recommendations
                inverse_ticker = self._get_inverse_ticker(safe_pos['ticker'])
                position_recommendations.append(f"• {safe_pos['ticker']}: Entry ${safe_pos['entry_price']:.2f} | Score {safe_pos['conviction']:.1f}/10")
                position_recommendations.append(f"  Hedge: {inverse_ticker} | Size: 1-3% inverse exposure")
                position_recommendations.append(f"  Context: Technical breakdown + macro headwinds")
        
        if not strong_buys and not strong_sells:
            position_recommendations.append("📊 MARKET HOLD:")
            position_recommendations.append("Signals lack conviction threshold (>1.5/10) for position sizing.")
            position_recommendations.append("• Monitoring for volume confirmation and momentum shifts")
            if watchlist:
                position_recommendations.append(f"• Watchlist: {', '.join(watchlist[:3])} - awaiting breakouts")
            position_recommendations.append("• Cash position maintained for clearer opportunities")
        
        return position_recommendations
    
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
        
        # Position Recommendations
        if position_text:
            children.extend(self._build_position_blocks(position_text, strong_buys, strong_sells))
        
        # Risk Assessment
        children.append(self._build_risk_assessment_block(report_data, strong_buys, strong_sells))
        
        # Session Articles
        if report_data.get('session_articles'):
            children.append(self._build_articles_block(report_data['session_articles']))
        
        return children
    
    def _build_position_blocks(self, position_text, strong_buys, strong_sells):
        """Build position recommendation blocks"""
        blocks = []
        
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "💼 Position Recommendations"}}]
            }
        })
        
        blocks.append({
            "object": "block",
            "type": "code",
            "code": {
                "rich_text": [{"type": "text", "text": {"content": position_text}}],
                "language": "plain text"
            }
        })
        
        # Add enhanced execution strategy for strong buys using centralized config
        if strong_buys:
            from .report_consolidator import get_conviction_tier, safe_get_position_data
            
            max_conviction = max([pos.get('conviction', 0) for pos in strong_buys])
            tier_config = get_conviction_tier(max_conviction)
            
            trading_notes = f"📈 EXECUTION PLAYBOOK ({tier_config['urgency']}):\n"
            trading_notes += f"Timeframe: {tier_config['timeframe']} | Risk Level: {tier_config['tier']} conviction signals\n\n"
            
            for i, pos in enumerate(strong_buys[:2], 1):
                safe_pos = safe_get_position_data(pos)
                trading_notes += f"{i}. {safe_pos['ticker']} @ ${safe_pos['entry_price']:.2f}\n"
                trading_notes += f"   • Score: {safe_pos['conviction']:.1f}/10 | Volume: {safe_pos['volume']:,}\n"
                trading_notes += f"   • Entry: Limit order -1% below current\n"
                trading_notes += f"   • Stop: {tier_config['stop']} | Target: {tier_config['target']}\n\n"
            
            blocks.append({
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{"type": "text", "text": {"content": trading_notes}}],
                    "icon": {"emoji": "📈"}
                }
            })
        
        # Add macro context for sells
        if strong_sells:
            sell_context = "🔻 MARKET HEADWINDS:\n"
            sell_context += "Technical breakdown coincides with macro uncertainty.\n\n"
            
            for pos in strong_sells[:2]:
                inverse_ticker = self._get_inverse_ticker(pos['ticker'])
                sell_context += f"• {pos['ticker']}: Bearish divergence detected\n"
                sell_context += f"  Hedge via {inverse_ticker} (1-3% allocation)\n"
                sell_context += f"  Context: Volume selling + momentum breakdown\n\n"
            
            sell_context += "Risk-off positioning recommended until trend clarity emerges."
            
            blocks.append({
                "object": "block",
                "type": "callout", 
                "callout": {
                    "rich_text": [{"type": "text", "text": {"content": sell_context}}],
                    "icon": {"emoji": "⚠️"}
                }
            })
        
        # Add HOLD strategy explanation if no strong positions
        if not strong_buys and not strong_sells:
            hold_strategy = """📊 PATIENCE STRATEGY:
Current signals below action threshold (1.5/10 conviction).

• Market lacks clear directional momentum
• Monitoring for volume breakouts and trend confirmation  
• Cash position preserved for higher-probability setups
• Watchlist tracking key technical levels for deployment

Strategy: Wait for 2.0+ conviction scores before sizing positions."""
            
            blocks.append({
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{"type": "text", "text": {"content": hold_strategy}}],
                    "icon": {"emoji": "⏸️"}
                }
            })
        
        return blocks
    
    def _build_risk_assessment_block(self, report_data, strong_buys, strong_sells):
        """Build risk assessment block with enhanced warnings"""
        risk_content = f"""📊 MARKET METRICS:
• Sentiment: {report_data.get('market_sentiment', 'Mixed')}
• Conviction: {report_data.get('conviction_level', 'Medium')}
• Risk Level: {report_data.get('risk_level', 'Medium')}
• Session Signals: {len(report_data.get('session_articles', []))}
• Strong Positions: {len(strong_buys + strong_sells)}

⚠️ KEY RISK FACTORS:
• 🔴 Portfolio concentration in thematic ETFs - MAJOR RISK
• Market volatility may impact momentum strategies
• Consider diversification across sectors
• Thematic ETFs can experience high correlation during drawdowns"""
        
        return {
            "object": "block",
            "type": "toggle",
            "toggle": {
                "rich_text": [{"type": "text", "text": {"content": f"⚠️ Risk Assessment - {report_data.get('risk_level', 'Medium')} Risk"}}],
                "children": [
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": risk_content.strip()}}]
                        }
                    }
                ]
            }
        }
    
    def _build_articles_block(self, session_articles):
        """Build session articles block with enhanced context"""
        article_list = []
        for i, article in enumerate(session_articles[:10]):
            confidence = article.get('confidence', 0)
            title = article.get('title', 'Unknown')
            signal = article.get('signal', 'Neutral')
            search_term = article.get('search_term', '')
            
            # Create 5-word summary from title
            title_words = title.split()
            summary = ' '.join(title_words[:5]) + ('...' if len(title_words) > 5 else '')
            
            signal_emoji = "📈" if signal == "Bullish" else "📉" if signal == "Bearish" else "➖"
            
            article_text = f"{signal_emoji} (Confidence: {confidence}/10) – \"{summary}\" [{search_term}]"
            
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
                "rich_text": [{"type": "text", "text": {"content": f"📰 Source Articles ({len(session_articles)})"}}],
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
