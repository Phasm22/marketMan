import os
import openai
import imaplib
import email
import re
import json
import requests
import time
from datetime import datetime
from email.header import decode_header
from dotenv import load_dotenv
import logging
import sys

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.integrations.pushover_utils import send_energy_alert, send_system_alert
from src.core.market_memory import MarketMemory
from src.core.alert_batcher import queue_alert, process_alert_queue, BatchStrategy

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

def generate_tactical_explanation(analysis_result, article_title):
    """Generate a tactical, conversational explanation of the trading signal"""
    try:
        signal = analysis_result.get('signal', 'Neutral')
        confidence = analysis_result.get('confidence', 0)
        etfs = analysis_result.get('affected_etfs', [])
        reasoning = analysis_result.get('reasoning', '')
        sector = analysis_result.get('sector', 'Mixed')
        
        # Only generate tactical explanations for high-confidence signals
        if confidence < 7:
            return None
            
        prompt = f"""
You are MarketMan's senior portfolio strategist. Generate a tactical trading brief using proper financial terminology and specific actionable recommendations.

SIGNAL DATA:
- Article: "{article_title}"
- Signal: {signal} ({confidence}/10 conviction)
- Sector: {sector}
- Target ETFs: {', '.join(etfs[:5])}
- Market Thesis: "{reasoning}"

Write a professional trading brief in this format:

"**TACTICAL BRIEF - {signal.upper()} SIGNAL**

**Market Thesis:**
[2-3 sentences explaining the fundamental catalyst and why this creates an opportunity]

**Recommended Positioning:**
That {signal.upper()} signal translates to:
• **Primary Trade**: [Specific ETF] - [Entry strategy with price levels]
• **Position Size**: [Risk-appropriate allocation %]
• **Stop Loss**: [Specific price level or %]
• **Profit Target**: [Price target with timeline]

**Risk Management:**
• **Upside Scenario**: [Best case outcome and price targets]
• **Downside Risk**: [Key risk factors and hedge strategies]  
• **Time Horizon**: [Short/medium/long-term outlook]

**Execution Notes:**
[Specific entry timing, volume considerations, or alternative plays]"

Use proper financial terminology: entry/exit levels, position sizing, risk-reward ratios, stop-losses, profit targets. Be specific with actionable price levels and percentages. Maximum 250 words.
"""

        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,  # Slightly higher for more personality
            max_tokens=400
        )

        tactical_explanation = response['choices'][0]['message']['content'].strip()
        logger.info(f"💡 Generated tactical explanation ({len(tactical_explanation)} chars)")
        return tactical_explanation
        
    except Exception as e:
        logger.warning(f"⚠️ Failed to generate tactical explanation: {e}")
        return None

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

def get_fallback_cover_image(session_analyses):
    """Get cover image from the first available article in the session"""
    for analysis in session_analyses:
        source_article = analysis.get('source_article', {})
        article_link = source_article.get('link')
        
        if article_link:
            logger.info(f"🖼️ Trying cover image from: {source_article.get('title', 'Unknown')[:50]}...")
            cover_image = get_microlink_image(article_link)
            if cover_image:
                return cover_image
    
    logger.debug("⚠️ No cover images found for any articles in session")
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
        """Main function to process Google Alerts - now creates consolidated reports"""
        logger.info("Starting to process Google Alerts...")

        # Fetch alerts from Gmail
        alerts = self.gmail_poller.get_google_alerts()

        if not alerts:
            logger.info("No new alerts found")
            return

        # Collect all analyses for consolidated reporting
        session_analyses = []
        session_timestamp = datetime.now().isoformat()
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

                    # Add metadata for consolidated reporting
                    analysis['source_article'] = {
                        'title': article['title'],
                        'link': article['link'],
                        'search_term': alert['search_term'],
                        'timestamp': alert['timestamp']
                    }

                    # Focus ETFs using sector intelligence
                    focused_etfs, primary_sector = categorize_etfs_by_sector(analysis.get('affected_etfs', []))
                    analysis['focused_etfs'] = focused_etfs
                    analysis['primary_sector'] = primary_sector
                    
                    # Track for pattern analysis
                    all_mentioned_etfs.update(focused_etfs)
                    
                    # Add to session collection
                    session_analyses.append(analysis)
                    
                    signal = analysis.get('signal', 'Neutral')
                    confidence = analysis.get('confidence', 0)
                    
                    logger.info(f"📊 {signal} signal ({confidence}/10) - {primary_sector or 'Mixed'} - {article['title'][:60]}...")

                except Exception as e:
                    logger.error(f"Error processing article '{article['title']}': {e}")
                    continue
        
        # Create consolidated signal report if we have analyses
        if session_analyses:
            logger.info(f"� Creating consolidated report from {len(session_analyses)} analyses...")
            
            consolidated_report = create_consolidated_signal_report(session_analyses, session_timestamp)
            
            if consolidated_report:
                # Log consolidated report to Notion
                notion_url = self.gmail_poller.log_consolidated_report_to_notion(consolidated_report)
                
                # Queue high-conviction signals for alerts
                high_conviction_signals = [a for a in session_analyses if a.get('confidence', 0) >= 8]
                
                if high_conviction_signals:
                    logger.info(f"📋 Queueing {len(high_conviction_signals)} high-conviction signals...")
                    
                    for analysis in high_conviction_signals:
                        alert_id = queue_alert(
                            signal=analysis.get('signal', 'Neutral'),
                            confidence=analysis.get('confidence', 0),
                            title=f"High Conviction: {analysis.get('primary_sector', 'Mixed')} Signal",
                            reasoning=analysis.get('reasoning', ''),
                            etfs=analysis.get('focused_etfs', []),
                            sector=analysis.get('primary_sector', 'Mixed'),
                            article_url=notion_url,
                            search_term="consolidated_report",
                            strategy=CURRENT_BATCH_STRATEGY
                        )
                        logger.info(f"✅ Alert queued: {alert_id[:8]}")
                else:
                    logger.info("⏭️ No high-conviction signals to queue")
        
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
            
            # Decode HTML entities properly
            import html
            title = html.unescape(title)
            
            # Get corresponding description
            description = ""
            if i < len(descriptions):
                description = re.sub(r'<[^>]+>', '', descriptions[i]).strip()
                description = html.unescape(description)
            
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
                    "Status": {
                        "select": {"name": "New"}
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
            children = []
            
            # Add tactical explanation for high-confidence signals
            if confidence >= 7:
                tactical_explanation = generate_tactical_explanation(analysis_data, analysis_data.get("title", ""))
                if tactical_explanation:
                    tactical_toggle = {
                        "object": "block",
                        "type": "toggle",
                        "toggle": {
                            "rich_text": [{"type": "text", "text": {"content": "🎯 Tactical Brief"}}],
                            "children": [
                                {
                                    "object": "block",
                                    "type": "paragraph",
                                    "paragraph": {
                                        "rich_text": [{"type": "text", "text": {"content": tactical_explanation}}]
                                    }
                                }
                            ]
                        }
                    }
                    children.append(tactical_toggle)
            
            # Add memory insights toggle block if available (skip redundant reasoning callout)
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
                session_articles = report_data.get('session_articles', [])
                default_etfs = ["ICLN", "TAN", "QCLN", "PBW", "ITA"][:3]  # CleanTech focus based on recent alerts
                etf_list.extend(default_etfs)
            
            logger.info(f"📊 ETFs to add to Notion: {etf_list}")
            
            # Build position summary text with prices for display in reasoning
            position_summary = []
            
            if strong_buys:
                position_summary.append(f"🟢 STRONG BUYS ({len(strong_buys)})")
                for pos in strong_buys[:3]:  # Top 3
                    position_summary.append(f"• {pos['ticker']}: ENTRY ${pos['entry_price']:.2f} | CONVICTION {pos['conviction']:.1f}/10 | VOL {pos['volume']:,}")
            
            if strong_sells:
                position_summary.append(f"🔴 STRONG SELLS ({len(strong_sells)})")
                for pos in strong_sells[:2]:  # Top 2
                    position_summary.append(f"• {pos['ticker']}: ENTRY ${pos['entry_price']:.2f} | CONVICTION {pos['conviction']:.1f}/10 | VOL {pos['volume']:,}")
            
            if watchlist:
                position_summary.append(f"👁️ WATCHLIST: {', '.join(watchlist[:5])}")
            
            position_text = '\n'.join(position_summary)
            logger.info(f"📋 Position summary prepared with {len(position_summary)} sections")

            # Get first article link for the Link field
            session_articles = report_data.get('session_articles', [])
            first_article_link = ""
            for article in session_articles:
                link = article.get('link', '')
                if link and link.strip() and link.startswith('http'):
                    first_article_link = link.strip()
                    break
            
            # If no valid link found, try to use a default or construct one
            if not first_article_link and session_articles:
                # Try to find any article with a title that might have a link
                for article in session_articles:
                    title = article.get('title', '')
                    if title and 'http' in title:
                        # Extract URL from title if embedded
                        import re
                        url_match = re.search(r'https?://[^\s]+', title)
                        if url_match:
                            first_article_link = url_match.group()
                            break
            
            logger.info(f"🔗 Link field will be set to: {first_article_link or 'None'}")

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
                        "multi_select": [{"name": etf_name} for etf_name in etf_list[:5]]  # Limit to 5 to avoid Notion limits
                    },
                    "Link": {
                        "url": first_article_link if first_article_link else "https://example.com"  # Fallback URL
                    },
                    "Sector": {
                        "select": {"name": "Portfolio Report"}
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
                        "rich_text": [{"text": {"content": "consolidated_report"}}]
                    }
                }
            }

            # Try to get cover image from session articles
            cover_image = None
            session_articles = report_data.get('session_articles', [])
            if session_articles:
                # Try to get cover from first article that has a link
                for article_data in session_articles:
                    article_link = article_data.get('link')
                    if article_link and article_link.strip():
                        logger.info(f"🖼️ Trying cover image from: {article_data.get('title', 'Unknown')[:50]}...")
                        cover_image = get_microlink_image(article_link)
                        if cover_image:
                            logger.info(f"✅ Found cover image: {cover_image[:100]}...")
                            break
                        else:
                            logger.debug(f"❌ No image found for: {article_link[:100]}...")
                
                # If no cover found, log the issue
                if not cover_image:
                    logger.info(f"⚠️ No cover images found from {len(session_articles)} session articles")

            # Add cover image if found
            if cover_image:
                data["cover"] = {
                    "type": "external",
                    "external": {"url": cover_image}
                }
                logger.info(f"🖼️ Adding cover image to consolidated report")
            else:
                logger.debug("⚠️ No cover image found for consolidated report")

            # --- Build enhanced children blocks for financial report ---
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
            
            # Position Recommendations with Financial Details
            if position_text:
                children.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "💼 Position Recommendations"}}]
                    }
                })
                
                children.append({
                    "object": "block",
                    "type": "code",
                    "code": {
                        "rich_text": [{"type": "text", "text": {"content": position_text}}],
                        "language": "plain text"
                    }
                })
                
                # Add specific trading instructions
                if strong_buys:
                    trading_notes = "📈 EXECUTION NOTES:\n"
                    for pos in strong_buys[:2]:
                        trading_notes += f"• {pos['ticker']}: Consider 2-5% position size, set stop-loss at -8%, target +15-20%\n"
                    
                    children.append({
                        "object": "block",
                        "type": "callout",
                        "callout": {
                            "rich_text": [{"type": "text", "text": {"content": trading_notes}}],
                            "icon": {"emoji": "📈"}
                        }
                    })
            
            # Risk Assessment with Financial Metrics
            risk_content = f"""
📊 MARKET METRICS:
• Sentiment: {report_data.get('market_sentiment', 'Mixed')}
• Conviction: {report_data.get('conviction_level', 'Medium')}
• Risk Level: {report_data.get('risk_level', 'Medium')}
• Session Signals: {len(report_data.get('session_articles', []))}
• Strong Positions: {len(strong_buys + strong_sells)}

⚠️ RISK FACTORS:
• Portfolio concentration in thematic ETFs
• Market volatility may impact momentum strategies
• Consider diversification across sectors
"""
            
            children.append({
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
            })
            
            # Session Articles (collapsible)
            if report_data.get('session_articles'):
                article_list = []
                for i, article in enumerate(report_data['session_articles'][:10]):
                    confidence = article.get('confidence', 0)
                    title = article.get('title', 'Unknown')
                    article_list.append({
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [{"type": "text", "text": {"content": f"{title} (Confidence: {confidence}/10)"}}]
                        }
                    })
                
                children.append({
                    "object": "block",
                    "type": "toggle",
                    "toggle": {
                        "rich_text": [{"type": "text", "text": {"content": f"📰 Source Articles ({len(report_data['session_articles'])})"}}],
                        "children": article_list
                    }
                })

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
                logger.info("✅ Consolidated report logged to Notion with financial details")
                return page_url
            else:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                logger.error(f"Failed to log consolidated report to Notion: {error_data}")
                return False

        except Exception as e:
            logger.error(f"Error logging consolidated report to Notion: {e}")
            return False
    
    # ... existing code ...

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
    
    dominant_sector = max(primary_sectors.keys(), key=lambda s: primary_sectors[s]) if primary_sectors else 'Mixed'
    
    # Create consolidated report
    report = {
        'title': f"MarketMan Signal Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        'session_timestamp': session_timestamp,
        'executive_summary': f"Analyzed {total_signals} market signals. Primary focus: {dominant_sector}. {len(strong_buys)} strong buy recommendations, {len(strong_sells)} strong sell recommendations.",
        'market_sentiment': 'Bullish' if len([a for a in all_analyses if a.get('signal') == 'Bullish']) > len(all_analyses) / 2 else 'Bearish' if len([a for a in all_analyses if a.get('signal') == 'Bearish']) > len(all_analyses) / 2 else 'Mixed',
        'conviction_level': 'High' if len(high_conviction) > 0 else 'Medium' if len(medium_conviction) > 0 else 'Low',
        'strong_buys': strong_buys[:5],  # Top 5
        'strong_sells': strong_sells[:3],  # Top 3
        'watchlist': [etf for etf, data in etf_positions.items() if 0.3 <= abs(data['net_score']) < 1.0][:10],
        'risk_level': 'High' if any(a.get('sector') == 'Volatility' for a in high_conviction) else 'Medium',
        'session_articles': [
            {
                'title': a.get('title', ''),
                'confidence': a.get('confidence', 0),
                'link': a.get('source_article', {}).get('link', '')
            } for a in all_analyses
        ],
        'analysis_timestamp': datetime.now().isoformat()
    }
    
    return report

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

def test_tactical_explanation():
    """Test the tactical explanation generation"""
    test_analysis = {
        'signal': 'Bullish',
        'confidence': 8,
        'affected_etfs': ['QQQ', 'TQQQ', 'VTI'],
        'reasoning': 'Strong earnings beats from tech giants driving sector momentum',
        'sector': 'Technology'
    }
    
    test_title = "Tech Giants Report Blowout Earnings, AI Revenue Surges"
    
    print("\n🧪 Testing tactical explanation generation...")
    explanation = generate_tactical_explanation(test_analysis, test_title)
    
    if explanation:
        print(f"✅ Generated tactical explanation ({len(explanation)} characters):")
        print("=" * 60)
        print(explanation)
        print("=" * 60)
    else:
        print("❌ Failed to generate tactical explanation")
    
    return explanation is not None

def test_consolidated_reporting():
    """Test the consolidated reporting with multiple mock analyses"""
    print("\n🧪 Testing consolidated signal reporting...")
    
    # Mock multiple analyses
    mock_analyses = [
        {
            'signal': 'Bullish',
            'confidence': 9,
            'affected_etfs': ['BOTZ', 'ROBO', 'ARKQ'],
            'reasoning': 'Strong AI sector momentum with institutional inflows',
            'sector': 'AI',
            'market_snapshot': {
                'BOTZ': {'price': 31.42, 'volume': 359773},
                'ROBO': {'price': 57.93, 'volume': 32891},
                'ARKQ': {'price': 85.74, 'volume': 103217}
            },
            'source_article': {'title': 'AI ETFs See Record Inflows', 'search_term': 'AI ETF'}
        },
        {
            'signal': 'Bullish',
            'confidence': 8,
            'affected_etfs': ['ITA', 'XAR', 'DFEN'],
            'reasoning': 'Defense spending increases drive sector optimism',
            'sector': 'Defense',
            'market_snapshot': {
                'ITA': {'price': 181.76, 'volume': 726277},
                'XAR': {'price': 200.79, 'volume': 111597},
                'DFEN': {'price': 46.63, 'volume': 528594}
            },
            'source_article': {'title': 'Defense Budget Increases', 'search_term': 'defense ETF'}
        },
        {
            'signal': 'Bearish',
            'confidence': 7,
            'affected_etfs': ['XLE'],
            'reasoning': 'Oil prices under pressure from supply concerns',
            'sector': 'Energy',
            'market_snapshot': {
                'XLE': {'price': 84.80, 'volume': 27289474}
            },
            'source_article': {'title': 'Oil Prices Decline', 'search_term': 'energy sector'}
        }
    ]
    
    # Test consolidated report creation
    consolidated_report = create_consolidated_signal_report(mock_analyses, datetime.now().isoformat())
    
    if consolidated_report:
        print("✅ Successfully created consolidated report!")
        print("\n" + "="*60)
        print("📊 CONSOLIDATED SIGNAL REPORT:")
        print("="*60)
        
        print(f"📋 Executive Summary:")
        print(f"   {consolidated_report['executive_summary']}")
        
        print(f"\n💼 Market Sentiment: {consolidated_report['market_sentiment']}")
        print(f"⚡ Conviction Level: {consolidated_report['conviction_level']}")
        
        if consolidated_report['strong_buys']:
            print(f"\n🟢 STRONG BUYS ({len(consolidated_report['strong_buys'])}):")
            for pos in consolidated_report['strong_buys']:
                print(f"   • {pos['ticker']}: ${pos['entry_price']:.2f} (Conviction: {pos['conviction']:.1f}, {pos['signals_count']} signals)")
        
        if consolidated_report['strong_sells']:
            print(f"\n🔴 STRONG SELLS ({len(consolidated_report['strong_sells'])}):")
            for pos in consolidated_report['strong_sells']:
                print(f"   • {pos['ticker']}: ${pos['entry_price']:.2f} (Conviction: {pos['conviction']:.1f}, {pos['signals_count']} signals)")
        
        if consolidated_report['watchlist']:
            print(f"\n👁️ WATCHLIST: {', '.join(consolidated_report['watchlist'])}")
        
        print("="*60)
        return True
    else:
        print("❌ Failed to create consolidated report")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and "--test-tactical" in sys.argv:
        success = test_tactical_explanation()
        sys.exit(0 if success else 1)
    if len(sys.argv) > 1 and "--test-consolidated" in sys.argv:
        success = test_consolidated_reporting()
        sys.exit(0 if success else 1)
    # Normal operation
    logger.info("🚀 Starting MarketMan marketMan system...")
    
    # Initialize the news analyzer
    analyzer = NewsAnalyzer()
    
    # Process new Google Alerts
    analyzer.process_alerts()
    
    logger.info("✅ Marketman analysis cycle complete")