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

# Set up logging with debug control
DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"
log_level = logging.DEBUG if DEBUG_MODE else logging.INFO
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize MarketMemory for contextual tracking
memory = MarketMemory()

def get_microlink_image(url):
    """Fetch article preview image using Microlink API"""
    try:
        logger.debug(f"🖼️ Fetching image for: {url}")
        params = {
            "url": url,
            "screenshot": "true",
            "meta": "false"
        }
        
        response = requests.get("https://api.microlink.io", params=params, timeout=10)
        if response.status_code == 200:
            data = response.json().get("data", {})
            
            # Try different image sources in order of preference
            for image_key in ["screenshot", "image", "logo"]:
                image_data = data.get(image_key, {})
                if image_data and image_data.get("url"):
                    image_url = image_data["url"]
                    logger.info(f"✅ Found {image_key} image")
                    return image_url
            
            logger.warning("⚠️ No image found in Microlink response")
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
    
    # Add contextual insights from MarketMemory if available
    context_section = ""
    if contextual_insight:
        context_section = f"\n\n🧠 RECENT PATTERN ANALYSIS:\n{contextual_insight}\n\nConsider these recent patterns when formulating your analysis and strategic advice.\n"
    
    return f"""
You are Mr.MarketMan, a seasoned thematic ETF strategist with 15+ years of experience in momentum investing and sector rotation. Your role is to identify high-potential ETF opportunities across AI, defense, clean energy, thematic investing, and emerging market trends.

📰 MARKET INTELLIGENCE BRIEF:
Title: "{headline}"
Summary: "{summary}"
Context: "{snippet}"{price_context}{context_section}

ANALYSIS FRAMEWORK:
If this content is NOT related to ETF investing, thematic trends, or market flows, respond with:
{{"relevance": "not_financial", "confidence": 0}}

If relevant to ETF/thematic investing, provide your strategic analysis in this JSON format:
{{
    "relevance": "financial",
    "sector": "AI/Tech|Defense|Clean Energy|Nuclear|Thematic|Flows|Volatility|Broad Market",
    "signal": "Bullish|Bearish|Neutral",
    "confidence": 1-10,
    "affected_etfs": ["BOTZ", "ITA", "URNM", "ICLN", "VIXY", "SPY", etc.],
    "reasoning": "One clear, compelling sentence explaining the core market impact",
    "market_impact": "Strategic implications for thematic ETF positioning (2-3 sentences)",
    "price_action": "Expected ETF price movements and momentum drivers (2-3 sentences)",
    "strategic_advice": "Specific tactical recommendations for ETF positioning (2-3 sentences)",
    "coaching_tone": "Professional coaching insight with momentum/thematic perspective (2-3 sentences)",
    "risk_factors": "Key risks to monitor going forward (1-2 sentences)",
    "opportunity_thesis": "Core thematic investment opportunity or threat (1-2 sentences)",
    "theme_category": "AI/Robotics|Defense/Aerospace|Nuclear/Uranium|CleanTech/Climate|Flows/Technical|Volatility/Hedge|Broad Market"
}}

THEMATIC FOCUS AREAS:
🤖 AI/ROBOTICS: BOTZ, ROBO, IRBO, ARKQ, SMH, SOXX
🛡️ DEFENSE/AEROSPACE: ITA, XAR, DFEN, PPA  
☢️ NUCLEAR/URANIUM: URNM, NLR, URA
🌱 CLEAN ENERGY/CLIMATE: ICLN, TAN, QCLN, PBW, LIT, REMX
📊 VOLATILITY/HEDGE: VIXY, VXX, SQQQ, SPXS
💰 MARKET FLOWS: Any ETF with significant fund flows or institutional activity

COACHING PRINCIPLES:
✅ Focus on momentum and thematic narratives driving ETF flows
✅ Identify early-stage trends before they go mainstream
✅ Connect news to specific ETF opportunities, not just sectors
✅ Balance momentum plays with risk management
✅ Use fund flow data and technical momentum as key signals
✅ Think like a tactical asset allocator, not a buy-and-hold investor

RESPOND WITH VALID JSON ONLY - NO MARKDOWN OR EXPLANATIONS."""

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
                    
                    # Track ETFs for pattern analysis
                    all_mentioned_etfs.update(etfs)
                    
                    # Get fresh contextual insights for this specific analysis
                    contextual_insight = memory.get_contextual_insight(analysis, etfs)
                    
                    logger.info(f"📊 {signal} signal ({confidence}/10) - {article['title'][:60]}...")
                    
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
                        "etfs": etfs,
                        "reasoning": analysis.get('reasoning', ''),
                        "timestamp": alert['timestamp'],
                        "link": article['link'],
                        "search_term": alert['search_term'],
                        "image_url": article_image,  # Add image URL
                        "contextual_insight": contextual_insight  # Add contextual insight
                    }
                    
                    # Log to Notion and get the page URL
                    notion_url = self.gmail_poller.log_to_notion(analysis_data)
                    
                    # Send Pushover alert using the new utility
                    if confidence >= 7:
                        # Enhance reasoning with contextual insight if available
                        enhanced_reasoning = analysis.get('reasoning', '')
                        if contextual_insight:
                            enhanced_reasoning += f"\n\n🧠 Context: {contextual_insight}"
                        
                        send_energy_alert(
                            title=article['title'],
                            signal=signal,
                            confidence=confidence,
                            reasoning=enhanced_reasoning,
                            etfs=etfs,
                            article_url=notion_url
                        )

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
        """Log analysis result to Notion database with enhanced contextual insights"""
        if not self.notion_token or not self.notion_database_id:
            logger.debug("Notion credentials not configured, skipping logging")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.notion_token}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }
            
            # Build comprehensive reasoning that includes contextual insights
            full_reasoning = analysis_data.get("reasoning", "")
            contextual_insight = analysis_data.get("contextual_insight", "")
            
            if contextual_insight:
                full_reasoning += f"\n\n🧠 MARKET MEMORY INSIGHTS:\n{contextual_insight}"
            
            # Determine actionable recommendation based on signal and confidence
            confidence = analysis_data.get("confidence", 0)
            signal = analysis_data.get("signal", "Neutral")
            
            action_recommendation = "HOLD - Monitor for developments"
            if confidence >= 8:
                if signal == "Bullish":
                    action_recommendation = "🟢 STRONG BUY - High confidence bullish signal"
                elif signal == "Bearish":
                    action_recommendation = "🔴 STRONG SELL - High confidence bearish signal"
            elif confidence >= 6:
                if signal == "Bullish":
                    action_recommendation = "🟡 CONSIDER BUY - Moderate bullish signal"
                elif signal == "Bearish":
                    action_recommendation = "🟡 CONSIDER SELL - Moderate bearish signal"
            elif confidence >= 4:
                if signal == "Bullish":
                    action_recommendation = "🟢 WATCH - Weak bullish signal"
                elif signal == "Bearish":
                    action_recommendation = "🔴 WATCH - Weak bearish signal"
            
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
                    "Reasoning": {
                        "rich_text": [{"text": {"content": full_reasoning}}]
                    },
                    "Action": {
                        "rich_text": [{"text": {"content": action_recommendation}}]
                    },
                    "Timestamp": {
                        "date": {"start": analysis_data.get("timestamp", datetime.now().isoformat())}
                    },
                    "Link": {
                        "url": analysis_data.get("link", "")
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
            
            # Test Pushover alert
            logger.info("📱 Testing enhanced Pushover alert...")
            success = send_energy_alert(
                title=headline,
                signal=analysis_result.get('signal', 'Neutral'),
                confidence=analysis_result.get('confidence', 0),
                reasoning=analysis_result.get('reasoning', ''),
                etfs=analysis_result.get('affected_etfs', []),
                article_url=None
            )
            
            if success:
                logger.info("✅ Enhanced coaching alert sent successfully!")
            else:
                logger.warning("⚠️ Alert not sent (may be due to confidence threshold or missing credentials)")
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