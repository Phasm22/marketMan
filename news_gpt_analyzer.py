import os
import openai
import imaplib
import email
import re
import json
import requests
from datetime import datetime
from email.header import decode_header
from dotenv import load_dotenv
import logging
from pushover_utils import send_energy_alert, send_system_alert
from market_memory import MarketMemory
from alert_batcher import queue_alert, process_alert_queue, BatchStrategy

# Set up logging with debug control
DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"
log_level = logging.DEBUG if DEBUG_MODE else logging.INFO
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Alert batching configuration
ALERT_STRATEGY = os.getenv("ALERT_STRATEGY", "smart_batch").lower()
BATCH_STRATEGY_MAP = {
    "immediate": BatchStrategy.IMMEDIATE,
    "time_window": BatchStrategy.TIME_WINDOW,
    "daily_digest": BatchStrategy.DAILY_DIGEST,
    "smart_batch": BatchStrategy.SMART_BATCH
}
CURRENT_BATCH_STRATEGY = BATCH_STRATEGY_MAP.get(ALERT_STRATEGY, BatchStrategy.SMART_BATCH)

# Initialize MarketMemory for contextual tracking
memory = MarketMemory()

def get_microlink_image(url):
    """Fetch article preview image using Microlink API (OG image, fallback to logo)"""
    try:
        logger.debug(f"🖼️ Fetching image for: {url}")
        params = {
            "url": url,
            "meta": "true",
            "screenshot": "false"
        }
        response = requests.get("https://api.microlink.io", params=params, timeout=10)
        if response.status_code == 200:
            data = response.json().get("data", {})
            image_url = data.get("image", {}).get("url")
            if image_url:
                logger.info("✅ Found OG image via Microlink")
                return image_url
            # Fallback to logo if no OG image
            logo_url = data.get("logo", {}).get("url")
            if logo_url:
                logger.info("✅ Fallback to logo via Microlink")
                return logo_url
            logger.warning("⚠️ No image or logo found in Microlink response")
        else:
            logger.warning(f"⚠️ Microlink API error: {response.status_code}")
    except Exception as e:
        logger.warning(f"⚠️ Error fetching image: {e}")
    return None

def clean_google_redirect_url(url):
    """Extract the actual URL from Google's redirect URL"""
    if 'google.com/url' in url:
        try:
            import urllib.parse
            import html
            
            # First decode HTML entities like &amp;
            url = html.unescape(url)
            
            # Parse the URL parameters
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)
            
            # Extract the actual URL from the 'url' parameter
            if 'url' in params:
                actual_url = params['url'][0]
                logger.debug(f"🔗 Cleaned Google redirect: {actual_url[:100]}...")
                return actual_url
        except Exception as e:
            logger.warning(f"⚠️ Error cleaning Google URL: {e}")
    
    return url

def get_etf_prices(etf_symbols):
    """Fetch current ETF prices for market snapshot with rate limiting"""
    try:
        import yfinance as yf
        import time
        import random
        
        prices = {}
        
        logger.info(f"💰 Fetching real-time prices for {len(etf_symbols)} ETFs...")
        
        for i, symbol in enumerate(etf_symbols):
            try:
                # Add random delay to avoid rate limits
                if i > 0:
                    delay = random.uniform(0.5, 1.5)
                    time.sleep(delay)

                ticker = yf.Ticker(symbol)

                # Fetch last 2 days for close/open logic
                hist = ticker.history(period="2d")

                if not hist.empty:
                    # Use 2-day logic for prev_close/current_price
                    if len(hist) >= 2:
                        prev_close = hist['Close'].iloc[-2]
                        current_price = hist['Close'].iloc[-1]
                    else:
                        current_price = hist['Close'].iloc[-1]
                        prev_close = hist['Open'].iloc[-1] if len(hist) > 0 else current_price

                    # Calculate percentage change
                    change_pct = ((current_price - prev_close) / prev_close) * 100 if prev_close and prev_close != 0 else 0

                    # Get volume data if available
                    volume = hist['Volume'].iloc[-1] if 'Volume' in hist.columns else 0

                    prices[symbol] = {
                        "price": round(current_price, 2),
                        "change_pct": round(change_pct, 2),
                        "name": f"{symbol} ETF",  # Simplified name to avoid API calls
                        "volume": int(volume) if volume else 0,
                    }

                    trend_emoji = "📈" if change_pct > 0 else "📉" if change_pct < 0 else "➖"
                    if DEBUG_MODE:
                        logger.debug(f"💰 {symbol}: ${current_price:.2f} ({change_pct:+.2f}%) {trend_emoji}")
                    else:
                        logger.info(f"💰 {symbol}: ${current_price:.2f} ({change_pct:+.2f}%)")
                else:
                    logger.warning(f"⚠️ No price data for {symbol}")

            except Exception as e:
                if DEBUG_MODE:
                    logger.warning(f"⚠️ Error fetching price for {symbol}: {str(e)[:100]}...")
                continue  # Continue with next symbol
                
        logger.info(f"✅ Successfully fetched prices for {len(prices)}/{len(etf_symbols)} ETFs")
        return prices
        
    except ImportError:
        logger.warning("⚠️ yfinance not installed, skipping price data")
        return {}
    except Exception as e:
        logger.warning(f"⚠️ Error fetching ETF prices: {e}")
        return {}

def build_prompt(headline, summary, snippet="", etf_prices=None, contextual_insight=None):
    # Build comprehensive ETF price context if available
    price_context = ""
    if etf_prices:
        price_context = "\n\n📊 LIVE MARKET SNAPSHOT:\n"
        for symbol, data in etf_prices.items():
            change_sign = "+" if data['change_pct'] >= 0 else ""
            trend_emoji = "📈" if data['change_pct'] > 0 else "📉" if data['change_pct'] < 0 else "➖"
            price_context += f"• {symbol} ({data.get('name', symbol)}): ${data['price']} ({change_sign}{data['change_pct']}%) {trend_emoji}\n"
        price_context += "\nUse this real-time data to inform your strategic analysis.\n"

    return f"""
You are MarketMan — a tactical ETF strategist focused on identifying high-momentum opportunities in defense, AI, energy, clean tech, and volatility hedging. Your job is to turn breaking market intelligence into ETF positioning signals.

Analyze the following news and market context to determine if there's an actionable ETF play:

🧠 PATTERN MEMORY:
{contextual_insight or 'None'}

📊 MARKET SNAPSHOT:
{price_context or 'No price data'}

📰 ARTICLE:
Title: "{headline}"
Summary: "{summary}"
Additional Context: "{snippet}"

If this content is NOT relevant to thematic ETF investing, return:
{{"relevance": "not_financial", "confidence": 0}}

Otherwise, return:
{{
  "relevance": "financial",
  "sector": "Defense|AI|CleanTech|Volatility|Uranium|Broad Market",
  "signal": "Bullish|Bearish|Neutral",
  "confidence": 1-10,
  "affected_etfs": ["ITA", "XAR", "ICLN", etc],
  "reasoning": "Short rationale for signal",
  "market_impact": "Brief on broader ETF strategy",
  "price_action": "Expected ETF movements",
  "strategic_advice": "Tactical recommendations",
  "coaching_tone": "Professional insight with momentum focus",
  "risk_factors": "Key risks to monitor",
  "opportunity_thesis": "Thematic investment thesis",
  "theme_category": "AI/Robotics|Defense/Aerospace|CleanTech/Climate|Volatility/Hedge|Broad Market"
}}

Keep responses focused, precise, and relevant to ETF positioning.
"""

def analyze_thematic_etf_news(headline, summary, snippet=""):
    # Compact logging for production, detailed for debug
    if DEBUG_MODE:
        logger.debug(f"🤖 MarketMan ANALYZING:")
        logger.debug(f"   Title: '{headline}'")
        logger.debug(f"   Summary: '{summary}'") 
        logger.debug(f"   Snippet: '{snippet}'")
    else:
        logger.info(f"🤖 Analyzing: {headline[:60]}...")
    
    # Fetch current ETF prices for comprehensive market context (expanded for thematic coverage)
    major_etfs = [
        # AI & Tech Theme
        "BOTZ", "ROBO", "IRBO", "ARKQ", "SMH", "SOXX",
        # Defense & Aerospace  
        "ITA", "XAR", "DFEN", "PPA",
        # Nuclear & Uranium
        "URNM", "NLR", "URA",
        # Clean Energy & Climate
        "ICLN", "TAN", "QCLN", "PBW", "LIT", "REMX",
        # Volatility & Inverse
        "VIXY", "VXX", "SQQQ", "SPXS",
        # Traditional Sectors (for context)
        "XLE", "XLF", "XLK", "QQQ", "SPY"
    ]
    
    logger.debug(f"📊 Fetching market data for strategic context...")
    etf_prices = get_etf_prices(major_etfs)
    
    # Get contextual insights from memory (do a preliminary analysis to get ETFs)
    temp_analysis = {"signal": "Neutral", "affected_etfs": major_etfs}
    contextual_insight = memory.get_contextual_insight(temp_analysis, major_etfs)
    
    prompt = build_prompt(headline, summary, snippet, etf_prices, contextual_insight)

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1  # Lower temperature for more consistent JSON
        )

        result = response['choices'][0]['message']['content'].strip()
        
        if DEBUG_MODE:
            logger.debug(f"🤖 MarketMan RESPONSE: {result}")
        else:
            logger.debug(f"🤖 Response received ({len(result)} chars)")
        
        # Clean up common JSON formatting issues
        result = result.replace('```json', '').replace('```', '')
        result = result.strip()
        
        # Try to parse as JSON
        try:
            json_result = json.loads(result)
            
            # Check if content is not financial/ETF related
            if json_result.get('relevance') == 'not_financial':
                logger.info(f"🚫 MarketMan says: Not ETF/thematic content: {headline[:50]}...")
                return None
                
            # Add price data to the analysis result for downstream use
            json_result['market_snapshot'] = etf_prices
            json_result['analysis_timestamp'] = datetime.now().isoformat()
            
            # Store the analysis in memory for contextual tracking
            try:
                memory.store_signal(json_result, headline)
                logger.debug("💾 Analysis stored in MarketMemory")
            except Exception as mem_error:
                logger.warning(f"⚠️ Failed to store analysis in memory: {mem_error}")
                
            return json_result
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse MarketMan response as JSON: {e}")
            if DEBUG_MODE:
                logger.error(f"Raw response: {result}")
            
            # Try to extract signal from text if JSON parsing fails
            if "not energy related" in result.lower() or "not_financial" in result.lower():
                logger.info(f"🚫 MarketMan detected non-ETF content: {headline[:50]}...")
                return None
                
            # Return a basic structure if we can't parse JSON
            return {
                "relevance": "financial",
                "sector": "Thematic",
                "signal": "Neutral",
                "confidence": 1,
                "affected_etfs": [],
                "reasoning": "Failed to parse AI response",
                "market_snapshot": etf_prices,
                "raw_response": result
            }
            
    except Exception as e:
        logger.error(f"❌ Error calling OpenAI API: {e}")
        return None

class NewsAnalyzer:
    def __init__(self):
        self.gmail_poller = GmailPoller()
    
    def process_alerts(self):
        """Main function to process Google Alerts"""
        logger.info("Starting to process Google Alerts...")

        # Fetch alerts from Gmail
        alerts = self.gmail_poller.get_google_alerts()

        if not alerts:
            logger.info("No new alerts found")
            return

        # Track all ETFs mentioned in this batch for pattern analysis
        all_mentioned_etfs = set()
        
        for alert in alerts:
            logger.info(f"Processing alert for: {alert['search_term']}")

            for article in alert['articles']:
                try:
                    # Analyze the article
                    analysis = analyze_thematic_etf_news(
                        article['title'],
                        article['snippet'],
                        article['snippet']
                    )

                    if not analysis:
                        continue

                    # Fetch article image using Microlink
                    article_image = get_microlink_image(article['link'])
                    
                    signal = analysis.get('signal', 'Neutral')
                    confidence = analysis.get('confidence', 0)
                    etfs = analysis.get('affected_etfs', [])
                    
                    # Focus ETFs using sector intelligence
                    focused_etfs, primary_sector = categorize_etfs_by_sector(etfs)
                    
                    # Track ETFs for pattern analysis
                    all_mentioned_etfs.update(focused_etfs)
                    
                    # Get fresh contextual insights for this specific analysis
                    contextual_insight = memory.get_contextual_insight(analysis, focused_etfs)
                    
                    logger.info(f"📊 {signal} signal ({confidence}/10) - {primary_sector or 'Mixed'} - {article['title'][:60]}...")
                    
                    if contextual_insight:
                        logger.info(f"🧠 Context: {contextual_insight[:100]}...")
                    
                    if DEBUG_MODE:
                        logger.debug(f"🔗 Article URL: {article['link']}")
                        if article_image:
                            logger.debug(f"🖼️ Image URL: {article_image}")
                        if contextual_insight:
                            logger.debug(f"🧠 Full Context: {contextual_insight}")

                    # Prepare data for logging
                    analysis_data = {
                        "title": article['title'],
                        "signal": signal,
                        "confidence": confidence,
                        "etfs": focused_etfs,  # Use focused ETFs instead of full list
                        "sector": primary_sector,  # Add primary sector
                        "reasoning": analysis.get('reasoning', ''),
                        "timestamp": alert['timestamp'],
                        "link": article['link'],
                        "search_term": alert['search_term'],
                        "image_url": article_image,
                        "contextual_insight": contextual_insight
                    }
                    
                    # Log to Notion and get the page URL
                    notion_url = self.gmail_poller.log_to_notion(analysis_data)
                    
                    # Queue alert for batching (replaces direct Pushover send)
                    if confidence >= 7:
                        logger.info(f"📋 Queueing alert: {signal} ({confidence}/10) - {article['title'][:50]}...")
                        alert_id = queue_alert(
                            signal=signal,
                            confidence=confidence,
                            title=article['title'],
                            reasoning=analysis.get('reasoning', ''),
                            etfs=focused_etfs,
                            sector=primary_sector,
                            article_url=notion_url,
                            search_term=alert['search_term'],
                            strategy=CURRENT_BATCH_STRATEGY
                        )
                        logger.info(f"✅ Alert queued: {alert_id[:8]}")
                    else:
                        logger.info(f"⏭️ Skipping low confidence alert: {confidence}/10")

                    logger.info(f"✅ Processed: {signal} ({confidence}/10)")

                except Exception as e:
                    logger.error(f"Error processing article '{article['title']}': {e}")
                    continue
        
        # After processing all alerts, check for significant new patterns
        if all_mentioned_etfs:
            logger.info("🧠 Analyzing patterns for mentioned ETFs...")
            significant_patterns = []
            
            for etf in all_mentioned_etfs:
                patterns = memory.detect_patterns(etf_symbol=etf)
                # Only include patterns with high confidence or long streaks
                for pattern in patterns:
                    if (pattern.get('consecutive_days', 0) >= 3 or 
                        pattern.get('average_confidence', 0) >= 7):
                        significant_patterns.append(pattern)
            
            if significant_patterns:
                logger.info(f"📊 Found {len(significant_patterns)} significant patterns")
                # Log significant patterns to Notion
                self.gmail_poller.log_memory_patterns_to_notion(significant_patterns)
        
        # Process any pending alert batches at the end of the cycle
        logger.info("📱 Processing alert queue...")
        batch_results = process_alert_queue()
        
        if batch_results:
            for strategy, success in batch_results.items():
                status = "✅" if success else "❌"
                logger.info(f"{status} Batch sent via {strategy} strategy")
        else:
            logger.info("📭 No batches ready to send")

def send_email_alert(subject, body, recipient):
    # Placeholder for future email alerting implementation
    pass

class GmailPoller:
    def __init__(self):
        self.imap_server = "imap.gmail.com"
        self.email_user = os.getenv("GMAIL_USER")
        self.email_password = os.getenv("GMAIL_APP_PASSWORD")  # Use App Password for security
        self.notion_token = os.getenv("NOTION_TOKEN")
        self.notion_database_id = os.getenv("NOTION_DATABASE_ID")
        
    def connect_to_gmail(self):
        """Connect to Gmail via IMAP"""
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.email_user, self.email_password)
            logger.info("Successfully connected to Gmail")
            return mail
        except Exception as e:
            logger.error(f"Failed to connect to Gmail: {e}")
            return None
    
    def get_google_alerts(self):
        """Fetch unread Google Alerts from Gmail"""
        mail = self.connect_to_gmail()
        if not mail:
            return []
        
        try:
            mail.select("inbox")
            
            # Search for unread emails from Google Alerts
            status, messages = mail.search(None, 'UNSEEN FROM "googlealerts-noreply@google.com"')
            
            if status != "OK":
                logger.error("Failed to search emails")
                return []
            
            alerts = []
            message_ids = messages[0].split()
            
            for msg_id in message_ids:
                try:
                    status, msg_data = mail.fetch(msg_id, "(RFC822)")
                    if status != "OK":
                        continue
                    
                    # Parse email
                    email_body = msg_data[0][1]
                    email_message = email.message_from_bytes(email_body)
                    
                    # Extract content
                    alert_data = self.parse_google_alert(email_message)
                    if alert_data:
                        alerts.append(alert_data)
                        
                except Exception as e:
                    logger.error(f"Error parsing email {msg_id}: {e}")
                    continue
            
            mail.close()
            mail.logout()
            logger.info(f"Found {len(alerts)} Google Alerts")
            return alerts
            
        except Exception as e:
            logger.error(f"Error fetching Google Alerts: {e}")
            return []
    
    def parse_google_alert(self, email_message):
        """Parse Google Alert email to extract title, summary, and article snippet"""
        try:
            # Get subject
            subject = decode_header(email_message["Subject"])[0][0]
            if isinstance(subject, bytes):
                subject = subject.decode()
            
            # Extract the search term from subject (format: "Google Alert - YOUR_SEARCH_TERM")
            search_term = re.search(r'Google Alert - (.+)', subject)
            search_term = search_term.group(1) if search_term else "Unknown"
            
            # Get email body
            body = ""
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/html":
                        body = part.get_payload(decode=True).decode()
                        break
            else:
                body = email_message.get_payload(decode=True).decode()
            
            # Extract articles from HTML body
            articles = self.extract_articles_from_html(body)
            
            return {
                "search_term": search_term,
                "timestamp": datetime.now().isoformat(),
                "articles": articles
            }
            
        except Exception as e:
            logger.error(f"Error parsing Google Alert: {e}")
            return None
    
    def extract_articles_from_html(self, html_body):
        """Extract article titles, links, and snippets from Google Alert HTML"""
        # Debug: Save the HTML to see what we're working with
        logger.info("📧 DEBUG: Analyzing email HTML structure...")
        
        # Write HTML to file for debugging
        with open('debug_email.html', 'w', encoding='utf-8') as f:
            f.write(html_body)
        logger.info("📧 HTML saved to debug_email.html for inspection")
        
        articles = []
        
        # Updated regex patterns for current Google Alert structure
        # Look for article titles in the itemprop="name" spans
        title_pattern = r'<span itemprop="name">.*?<b>.*?</b>.*?([^<]+).*?</span>'
        title_link_pattern = r'<a href="([^"]*)" itemprop="url"[^>]*>\s*<span itemprop="name"[^>]*>(.*?)</span>'
        description_pattern = r'<div itemprop="description"[^>]*>(.*?)</div>'
        
        # Find title links and descriptions
        title_links = re.findall(title_link_pattern, html_body, re.DOTALL)
        descriptions = re.findall(description_pattern, html_body, re.DOTALL)
        
        logger.info(f"📧 Found {len(title_links)} articles with {len(descriptions)} descriptions")
        
        # Skip common Google Alert UI elements
        skip_titles = [
            "flag as irrelevant", "see more results", "edit this alert", 
            "create alert", "manage alerts", "unsubscribe", "view all",
            "help", "settings", "privacy", "terms"
        ]
        
        # Process the extracted articles
        for i, (link, title_html) in enumerate(title_links):
            # Clean up the title (remove HTML tags and decode)
            title = re.sub(r'<[^>]+>', '', title_html).strip()
            title = title.replace('&nbsp;', ' ').replace('&amp;', '&')
            
            # Get corresponding description
            description = ""
            if i < len(descriptions):
                description = re.sub(r'<[^>]+>', '', descriptions[i]).strip()
                description = description.replace('&nbsp;', ' ').replace('&amp;', '&')
            
            logger.info(f"📧 Extracted article: '{title}' -> {description[:100]}...")
            
            # Skip obvious UI elements (shouldn't be needed with new pattern)
            if len(title) < 10 or "flag as irrelevant" in title.lower():
                continue
            
            # Clean Google redirect URLs
            cleaned_link = clean_google_redirect_url(link)
            logger.debug(f"🔗 Cleaned: {cleaned_link}")
            
            articles.append({
                "title": title,
                "link": cleaned_link,
                "snippet": description
            })
        
        logger.info(f"📧 Extracted {len(articles)} valid articles after filtering")
        for i, article in enumerate(articles):
            logger.info(f"📧 Article {i+1}: '{article['title'][:80]}...'")
        
        return articles
    
    def log_to_notion(self, analysis_data):
        """Log analysis result to Notion database with enhanced contextual insights and Notion children blocks"""
        if not self.notion_token or not self.notion_database_id:
            logger.debug("Notion credentials not configured, skipping logging")
            return False

        try:
            headers = {
                "Authorization": f"Bearer {self.notion_token}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }

            # Build comprehensive reasoning (no longer append memory insights inline)
            full_reasoning = analysis_data.get("reasoning", "")
            contextual_insight = analysis_data.get("contextual_insight", "")

            # Prepare formatted_insights for use in Notion children blocks (not for inline reasoning)
            formatted_insights = []
            if contextual_insight:
                for insight in contextual_insight.split('.'):
                    insight = insight.strip()
                    if insight and len(insight) > 10:
                        formatted_insights.append(insight)

            # Determine simple actionable recommendation
            confidence = analysis_data.get("confidence", 0)
            signal = analysis_data.get("signal", "Neutral")

            # Simple BUY/SELL/HOLD logic
            if confidence >= 7:
                if signal == "Bullish":
                    action_recommendation = "BUY"
                elif signal == "Bearish":
                    action_recommendation = "SELL"
                else:
                    action_recommendation = "HOLD"
            else:
                action_recommendation = "HOLD"

            data = {
                "parent": {"database_id": self.notion_database_id},
                "properties": {
                    "Title": {
                        "title": [{"text": {"content": analysis_data.get("title", "")}}]
                    },
                    "Signal": {
                        "select": {"name": analysis_data.get("signal", "Neutral")}
                    },
                    "Confidence": {
                        "number": analysis_data.get("confidence", 0)
                    },
                    "ETFs": {
                        "multi_select": [{"name": etf} for etf in analysis_data.get("etfs", [])]
                    },
                    "Sector": {
                        "select": {"name": analysis_data.get("sector", "Mixed")}
                    },
                    "Reasoning": {
                        "rich_text": [{"text": {"content": full_reasoning}}]
                    },
                    "Action": {
                        "select": {"name": action_recommendation}
                    },
                    "Timestamp": {
                        "date": {"start": analysis_data.get("timestamp", datetime.now().isoformat())}
                    },
                    "Link": {
                        "url": analysis_data.get("link", "")
                    },
                    "Search Term": {
                        "rich_text": [{"text": {"content": analysis_data.get("search_term", "")}}]
                    }
                }
            }

            # Add cover image if available (this works without needing an Image property)
            image_url = analysis_data.get("image_url")
            if image_url:
                data["cover"] = {
                    "type": "external",
                    "external": {"url": image_url}
                }
                logger.info(f"🖼️ Adding cover image to Notion page")

            # --- Build Notion children blocks ---
            # 1. Reasoning summary (first 200 chars of full_reasoning)
            reasoning_summary = full_reasoning[:200]
            if len(full_reasoning) > 200:
                reasoning_summary += "..."

            children = []
            # Add callout summary block
            children.append({
                "object": "block",
                "type": "callout",
                "callout": {
                    "icon": {"type": "emoji", "emoji": "📰"},
                    "rich_text": [{"type": "text", "text": {"content": reasoning_summary}}]
                }
            })

            # Add memory insights toggle block if available
            if formatted_insights:
                toggle_block = {
                    "object": "block",
                    "type": "toggle",
                    "toggle": {
                        "rich_text": [{"type": "text", "text": {"content": "🧠 Memory Insights"}}],
                        "children": [
                            {
                                "object": "block",
                                "type": "bulleted_list_item",
                                "bulleted_list_item": {
                                    "rich_text": [{"type": "text", "text": {"content": insight}}]
                                }
                            } for insight in formatted_insights
                        ]
                    }
                }
                children.append(toggle_block)

            # Assign children blocks to the data dict
            data["children"] = children

            response = requests.post(
                "https://api.notion.com/v1/pages",
                headers=headers,
                json=data
            )

            if response.status_code == 200:
                result = response.json()
                page_url = result.get('url', '')
                logger.info("Successfully logged to Notion")
                return page_url  # Return the Notion page URL instead of True
            else:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                if "object_not_found" in str(error_data):
                    logger.warning("Notion database not found or not shared with integration. Skipping logging.")
                else:
                    logger.error(f"Failed to log to Notion: {error_data}")
                return False

        except Exception as e:
            logger.error(f"Error logging to Notion: {e}")
            return False
    
    def log_memory_patterns_to_notion(self, patterns):
        """Log detected memory patterns to Notion for strategic insights"""
        if not self.notion_token or not patterns:
            return False
        
        try:
            # Create a patterns summary page
            headers = {
                "Authorization": f"Bearer {self.notion_token}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }
            
            # Build pattern summary content
            pattern_content = "# 🧠 MarketMan Memory Patterns\n\n"
            pattern_content += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            for pattern in patterns:
                pattern_content += f"## {pattern.get('etf_symbol', 'Unknown')} - {pattern.get('type', '').title()} Pattern\n"
                pattern_content += f"**Description:** {pattern.get('description', '')}\n"
                pattern_content += f"**Duration:** {pattern.get('consecutive_days', 0)} days\n"
                pattern_content += f"**Signal:** {pattern.get('signal_type', '')}\n"
                pattern_content += f"**Avg Confidence:** {pattern.get('average_confidence', 0):.1f}/10\n"
                pattern_content += f"**Period:** {pattern.get('start_date', '')} to {pattern.get('end_date', '')}\n\n"
            
            # Create a new page for patterns (could be in a separate database)
            page_data = {
                "parent": {"page_id": "your_patterns_page_id"},  # You'd need to create this
                "properties": {
                    "title": {
                        "title": [{"text": {"content": f"Memory Patterns - {datetime.now().strftime('%Y-%m-%d')}"}}]
                    }
                },
                "children": [
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": pattern_content}}]
                        }
                    }
                ]
            }
            
            # Note: This would require a separate patterns page/database setup
            logger.debug("🧠 Memory patterns ready for Notion (requires patterns page setup)")
            return True
            
        except Exception as e:
            logger.error(f"Error logging patterns to Notion: {e}")
            return False

def categorize_etfs_by_sector(etfs):
    """Group ETFs by sector and return primary sector + key ETFs"""
    sector_mapping = {
        # Defense & Aerospace
        'Defense': ['ITA', 'XAR', 'DFEN', 'PPA'],
        # AI & Robotics
        'AI': ['BOTZ', 'ROBO', 'IRBO', 'ARKQ', 'SMH', 'SOXX'],
        # Clean Energy & Climate
        'CleanTech': ['ICLN', 'TAN', 'QCLN', 'PBW', 'LIT', 'REMX'],
        # Nuclear & Uranium
        'Nuclear': ['URNM', 'NLR', 'URA'],
        # Volatility & Inverse
        'Volatility': ['VIXY', 'VXX', 'SQQQ', 'SPXS'],
        # Traditional Sectors
        'Energy': ['XLE'],
        'Finance': ['XLF'],
        'Tech': ['XLK', 'QQQ'],
        'Market': ['SPY']
    }
    
    # Find which sectors are represented
    sector_matches = {}
    for etf in etfs:
        for sector, sector_etfs in sector_mapping.items():
            if etf in sector_etfs:
                if sector not in sector_matches:
                    sector_matches[sector] = []
                sector_matches[sector].append(etf)
    
    # Return top 2-3 ETFs per sector, prioritizing most mentioned
    focused_etfs = []
    primary_sector = None
    
    if sector_matches:
        # Find primary sector (most ETFs mentioned)
        primary_sector = max(sector_matches.keys(), key=lambda s: len(sector_matches[s]))
        
        # Take top 2-3 ETFs from primary sector + 1-2 from others
        for sector, sector_etfs in sector_matches.items():
            if sector == primary_sector:
                focused_etfs.extend(sector_etfs[:3])  # Top 3 from primary
            else:
                focused_etfs.extend(sector_etfs[:2])  # Top 2 from others
    
    return focused_etfs, primary_sector

# EXAMPLE USAGE
if __name__ == "__main__":
    import sys
    
    # Check for debug flag
    if "--debug" in sys.argv:
        os.environ["DEBUG"] = "true"
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("🐛 Debug mode enabled")
    
    # Check for test mode
    if "test" in sys.argv:
        logger.info("🧪 Running MarketMan test analysis...")
        logger.info("🤖 Testing MarketMan analysis engine...")
        
        # Example test analysis
        headline = "AI ETF BOTZ Sees Record Inflows as Robotics Automation Accelerates"
        summary = "Robotics and AI ETFs are experiencing unprecedented investor interest as companies accelerate automation adoption. BOTZ, ROBO, and ARKQ lead the charge with significant institutional inflows."
        snippet = "The AI and robotics sector is seeing massive capital deployment as businesses pivot to automation technologies following recent AI breakthroughs."
        
        analysis_result = analyze_thematic_etf_news(headline, summary, snippet)
        
        if analysis_result:
            logger.info("✅ MarketMan analysis successful!")
            print("\n" + "="*60)
            print("🎯 MarketMan ANALYSIS RESULT:")
            print("="*60)
            print(json.dumps(analysis_result, indent=2))
            print("="*60)
            
            # Test Pushover alert using batching system
            logger.info("📱 Testing alert batching...")
            
            # Get focused ETFs and primary sector
            focused_etfs, primary_sector = categorize_etfs_by_sector(analysis_result.get('affected_etfs', []))
            
            # Queue the test alert
            alert_id = queue_alert(
                signal=analysis_result.get('signal', 'Neutral'),
                confidence=analysis_result.get('confidence', 0),
                title=headline,
                reasoning=analysis_result.get('reasoning', ''),
                etfs=focused_etfs,
                sector=primary_sector or 'AI',
                search_term="test_analysis",
                strategy=CURRENT_BATCH_STRATEGY
            )
            
            logger.info(f"✅ Test alert queued: {alert_id[:8]}")
            
            # Process the queue to send any ready batches
            logger.info("🚀 Processing alert queue...")
            batch_results = process_alert_queue()
            
            if batch_results:
                for strategy, success in batch_results.items():
                    if success:
                        logger.info("✅ Enhanced batched alert sent successfully!")
                    else:
                        logger.warning("⚠️ Batched alert failed to send")
            else:
                logger.info("📋 Alert queued but not ready to send yet (check strategy logic)")
        else:
            logger.error("❌ Test analysis failed")
    else:
        # Normal operation
        logger.info("🚀 Starting MarketMan marketMan system...")
        
        # Initialize the news analyzer
        analyzer = NewsAnalyzer()
        
        # Process new Google Alerts
        analyzer.process_alerts()
        
        logger.info("✅ Marketman analysis cycle complete")