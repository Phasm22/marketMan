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

# Set up logging with debug control
DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"
log_level = logging.DEBUG if DEBUG_MODE else logging.INFO
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

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

def build_prompt(headline, summary, snippet="", etf_prices=None):
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
You are Mr.MarketMan, a seasoned energy markets strategist with 15+ years of experience. Your role is to provide strategic, actionable market intelligence with the wisdom of a mentor and the precision of a professional trader.

📰 MARKET INTELLIGENCE BRIEF:
Title: "{headline}"
Summary: "{summary}"
Context: "{snippet}"{price_context}

ANALYSIS FRAMEWORK:
If this content is NOT energy/financial sector related, respond with:
{{"relevance": "not_financial", "confidence": 0}}

If energy/financial relevant, provide your strategic analysis in this JSON format:
{{
    "relevance": "financial",
    "sector": "Energy",
    "signal": "Bullish|Bearish|Neutral",
    "confidence": 1-10,
    "affected_etfs": ["XLE", "ICLN", "TAN", "QCLN", "PBW", etc.],
    "reasoning": "One clear, compelling sentence explaining the core market impact",
    "market_impact": "Strategic implications for energy sector positioning (2-3 sentences)",
    "price_action": "Expected ETF price movements and momentum drivers (2-3 sentences)",
    "strategic_advice": "Specific tactical recommendations for portfolio positioning (2-3 sentences)",
    "coaching_tone": "Professional coaching insight with strategic perspective (2-3 sentences)",
    "risk_factors": "Key risks to monitor going forward (1-2 sentences)",
    "opportunity_thesis": "Core investment opportunity or threat (1-2 sentences)"
}}

COACHING PRINCIPLES:
✅ Think like a strategic advisor, not just an analyst
✅ Connect news to real portfolio implications
✅ Balance opportunity assessment with risk management
✅ Provide actionable guidance, not just commentary
✅ Use current price data to validate or challenge the thesis
✅ Maintain professional, confident tone with strategic depth

RESPOND WITH VALID JSON ONLY - NO MARKDOWN OR EXPLANATIONS."""

def analyze_energy_news(headline, summary, snippet=""):
    # Compact logging for production, detailed for debug
    if DEBUG_MODE:
        logger.debug(f"🤖 MarketMan ANALYZING:")
        logger.debug(f"   Title: '{headline}'")
        logger.debug(f"   Summary: '{summary}'") 
        logger.debug(f"   Snippet: '{snippet}'")
    else:
        logger.info(f"🤖 Analyzing: {headline[:60]}...")
    
    # Fetch current ETF prices for comprehensive market context (reduced to avoid rate limits)
    major_etfs = [
        "XLE",   # Energy Select Sector SPDR
        "ICLN",  # iShares Global Clean Energy
        "TAN",   # Invesco Solar ETF
        "QCLN",  # First Trust NASDAQ Clean Edge Green Energy
        "PBW"    # Invesco WilderHill Clean Energy
    ]
    
    logger.debug(f"📊 Fetching market data for strategic context...")
    etf_prices = get_etf_prices(major_etfs)
    
    prompt = build_prompt(headline, summary, snippet, etf_prices)

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
            
            # Check if content is not energy related
            if json_result.get('relevance') == 'not_financial':
                logger.info(f"🚫 MarketMan says: Not energy/financial content: {headline[:50]}...")
                return None
                
            # Add price data to the analysis result for downstream use
            json_result['market_snapshot'] = etf_prices
            json_result['analysis_timestamp'] = datetime.now().isoformat()
                
            return json_result
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse MarketMan response as JSON: {e}")
            if DEBUG_MODE:
                logger.error(f"Raw response: {result}")
            
            # Try to extract signal from text if JSON parsing fails
            if "not energy related" in result.lower() or "not_financial" in result.lower():
                logger.info(f"🚫 MarketMan detected non-energy content: {headline[:50]}...")
                return None
                
            # Return a basic structure if we can't parse JSON
            return {
                "relevance": "financial",
                "sector": "Energy",
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

        for alert in alerts:
            logger.info(f"Processing alert for: {alert['search_term']}")

            for article in alert['articles']:
                try:
                    # Analyze the article
                    analysis = analyze_energy_news(
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
                    logger.info(f"📊 {signal} signal ({confidence}/10) - {article['title'][:60]}...")
                    
                    if DEBUG_MODE:
                        logger.debug(f"🔗 Article URL: {article['link']}")
                        if article_image:
                            logger.debug(f"🖼️ Image URL: {article_image}")

                    # Prepare data for logging
                    analysis_data = {
                        "title": article['title'],
                        "signal": signal,
                        "confidence": confidence,
                        "etfs": analysis.get('affected_etfs', []),
                        "reasoning": analysis.get('reasoning', ''),
                        "timestamp": alert['timestamp'],
                        "link": article['link'],
                        "search_term": alert['search_term'],
                        "image_url": article_image  # Add image URL
                    }
                    
                    # Log to Notion and get the page URL
                    notion_url = self.gmail_poller.log_to_notion(analysis_data)
                    
                    # Send Pushover alert using the new utility
                    if confidence >= 7:
                        send_energy_alert(
                            title=article['title'],
                            signal=signal,
                            confidence=confidence,
                            reasoning=analysis.get('reasoning', ''),
                            etfs=analysis.get('affected_etfs', []),
                            article_url=notion_url
                        )

                    logger.info(f"✅ Processed: {signal} ({confidence}/10)")

                except Exception as e:
                    logger.error(f"Error processing article '{article['title']}': {e}")
                    continue

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
        """Log analysis result to Notion database"""
        if not self.notion_token or not self.notion_database_id:
            logger.debug("Notion credentials not configured, skipping logging")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.notion_token}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }
            
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
                        "rich_text": [{"text": {"content": analysis_data.get("reasoning", "")}}]
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
        headline = "Solar Industry Sees Record Q3 Growth as Federal Tax Credits Extended"
        summary = "Solar installations surged 40% year-over-year in Q3, driven by renewed federal tax credit certainty and falling panel costs. Major utilities are accelerating clean energy procurement."
        snippet = "The solar sector posted its strongest quarterly performance in over two years, with residential and utility-scale installations both showing robust growth."
        
        analysis_result = analyze_energy_news(headline, summary, snippet)
        
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