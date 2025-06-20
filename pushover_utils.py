"""
Reusable Pushover Utility
Matches the pattern from server_monitor.py for consistent notification handling
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

PUSHOVER_USER_KEY = os.getenv("PUSHOVER_USER")
PUSHOVER_API_TOKEN = os.getenv("PUSHOVER_TOKEN")

def send_pushover_notification(message, title="Alert", priority=0, url=None, url_title=None, image_url=None):
    """
    Send notification via Pushover
    
    Args:
        message (str): Main notification message
        title (str): Notification title
        priority (int): -2 (silent), -1 (quiet), 0 (normal), 1 (high), 2 (emergency)
        url (str): Optional URL to include
        url_title (str): Optional title for the URL
        image_url (str): Optional image URL to attach
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not PUSHOVER_USER_KEY or not PUSHOVER_API_TOKEN:
        print("⚠️  Pushover credentials not set.")
        return False

    data = {
        "token": PUSHOVER_API_TOKEN,
        "user": PUSHOVER_USER_KEY,
        "message": message,
        "title": title,
        "priority": priority
    }
    
    # Add optional URL
    if url:
        data["url"] = url
    if url_title:
        data["url_title"] = url_title

    files = None
    # Add image attachment if provided
    if image_url:
        try:
            print(f"📷 Downloading image for Pushover: {image_url[:80]}...")
            img_response = requests.get(image_url, timeout=10)
            if img_response.status_code == 200 and len(img_response.content) < 2500000:  # 2.5MB limit
                files = {"attachment": ("article_image.jpg", img_response.content, "image/jpeg")}
                print("✅ Image attached to Pushover notification")
            else:
                print("⚠️  Image too large or failed to download for Pushover")
        except Exception as e:
            print(f"⚠️  Error downloading image for Pushover: {e}")

    try:
        response = requests.post("https://api.pushover.net/1/messages.json", data=data, files=files)
        if response.status_code == 200:
            print(f"✅ Pushover sent: {title}")
            return True
        else:
            print(f"❌ Pushover failed: {response.text}")
            return False
    except Exception as e:
        print(f"🔥 Error sending Pushover notification: {e}")
        return False

def send_energy_alert(signal, confidence, title, reasoning, etfs=None, article_url=None, image_url=None, analysis=None):
    """
    Enhanced coaching-style energy sector alerts with real-time market data
    
    Args:
        signal (str): Bullish/Bearish/Neutral
        confidence (int): Confidence score 1-10
        title (str): Article title
        reasoning (str): AI reasoning
        etfs (list): Affected ETFs
        article_url (str): Link to article
        image_url (str): Article preview image
        analysis (dict): Full analysis with coaching insights and market data
    
    Returns:
        bool: True if sent successfully
    """
    # Determine priority based on confidence
    if confidence >= 9:
        priority = 1  # High priority (emergency needs extra params)
        priority_emoji = "🚨"
        alert_level = "CRITICAL"
    elif confidence >= 8:
        priority = 1  # High priority
        priority_emoji = "⚡"
        alert_level = "HIGH"
    elif confidence >= 7:
        priority = 0  # Normal priority
        priority_emoji = "📊"
        alert_level = "STANDARD"
    else:
        return False  # Don't send low confidence alerts
    
    # Format signal with emoji
    signal_emoji = {
        "Bullish": "📈",
        "Bearish": "📉", 
        "Neutral": "➖"
    }.get(signal, "❓")
    
    # Build comprehensive coaching-style message
    message = f"""🎯 MARKETMAN - {alert_level} ALERT

{signal_emoji} {signal} Signal ({confidence}/10)

📰 SITUATION:
{title}

💡 STRATEGIC ANALYSIS:
{reasoning}
"""
    
    # Add market snapshot if available
    if analysis and analysis.get('market_snapshot'):
        market_data = analysis['market_snapshot']
        if market_data:
            message += f"\n📊 LIVE MARKET DATA:"
            for symbol, data in list(market_data.items())[:4]:  # Show top 4 ETFs
                change_sign = "+" if data['change_pct'] >= 0 else ""
                trend_emoji = "📈" if data['change_pct'] > 0 else "📉" if data['change_pct'] < 0 else "➖"
                message += f"\n• {symbol}: ${data['price']} ({change_sign}{data['change_pct']}%) {trend_emoji}"
    
    # Add coaching insights
    if analysis and analysis.get('coaching_tone'):
        message += f"\n\n🧠 COACH'S PERSPECTIVE:\n{analysis['coaching_tone']}"
    
    # Add strategic advice
    if analysis and analysis.get('strategic_advice'):
        message += f"\n\n🎯 STRATEGIC GUIDANCE:\n{analysis['strategic_advice']}"
        
    # Add risk factors
    if analysis and analysis.get('risk_factors'):
        message += f"\n\n⚠️ RISK WATCH:\n{analysis['risk_factors']}"
        
    # Add opportunity thesis
    if analysis and analysis.get('opportunity_thesis'):
        message += f"\n\n💰 OPPORTUNITY:\n{analysis['opportunity_thesis']}"
    
    # Add price action analysis
    if analysis and analysis.get('price_action'):
        message += f"\n\n� PRICE ACTION:\n{analysis['price_action']}"
    
    if etfs:
        message += f"\n\n🎯 FOCUS ETFs: {', '.join(etfs)}"
    
    alert_title = f"{priority_emoji} Energy Market Intelligence"
    
    return send_pushover_notification(
        message=message.strip(),
        title=alert_title,
        priority=priority,
        url=article_url,
        url_title="📊 View Full Analysis" if article_url else None,
        image_url=image_url
    )

def send_system_alert(service_name, status, details=None):
    """
    System monitoring alerts (to match your server_monitor.py pattern)
    
    Args:
        service_name (str): Name of the service/server
        status (str): UP/DOWN/WARNING
        details (str): Additional details
    """
    status_emoji = {
        "UP": "✅",
        "DOWN": "❌", 
        "WARNING": "⚠️"
    }.get(status, "❓")
    
    priority = 1 if status == "DOWN" else 0
    
    message = f"{status_emoji} {service_name} is {status}"
    if details:
        message += f"\n\n{details}"
    
    return send_pushover_notification(
        message=message,
        title=f"System Alert: {service_name}",
        priority=priority
    )

def test_pushover():
    """Test Pushover configuration"""
    return send_pushover_notification(
        message="Test notification from marketMan system",
        title="🧪 Test Alert",
        priority=0
    )

def test_coaching_alert():
    """Test the enhanced coaching-style energy alert"""
    # Simulate a sample analysis
    sample_analysis = {
        'coaching_tone': "This development represents a classic sector rotation opportunity. Smart money is positioning for the next energy cycle, and early movers could capture significant alpha.",
        'strategic_advice': "Consider scaling into clean energy positions on any near-term weakness. The regulatory tailwinds are strengthening, and valuations are becoming more attractive.",
        'risk_factors': "Watch for broader market volatility and potential commodity price swings that could impact sector momentum.",
        'opportunity_thesis': "Multi-year secular growth trend in renewable energy infrastructure spending creates compelling investment runway.",
        'price_action': "Expect continued volatility but with an upward bias as institutional flows accelerate into the space.",
        'market_snapshot': {
            'ICLN': {'price': 22.45, 'change_pct': 2.3, 'name': 'iShares Global Clean Energy'},
            'TAN': {'price': 55.67, 'change_pct': -1.2, 'name': 'Invesco Solar ETF'},
            'XLE': {'price': 89.12, 'change_pct': 0.8, 'name': 'Energy Select Sector SPDR'},
        }
    }
    
    return send_energy_alert(
        signal="Bullish",
        confidence=8,
        title="Clean Energy Legislation Gains Momentum in Senate",
        reasoning="Bipartisan support emerging for renewable energy tax credits extension, potentially unlocking $50B+ in sector investment over next 3 years.",
        etfs=["ICLN", "TAN", "QCLN"],
        analysis=sample_analysis
    )

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "coaching":
        # Test the enhanced coaching alert
        print("🧪 Testing enhanced coaching-style alert...")
        success = test_coaching_alert()
        if success:
            print("🎉 Enhanced coaching alert sent successfully!")
        else:
            print("❌ Enhanced coaching alert failed. Check your credentials.")
    else:
        # Test basic Pushover setup
        print("🧪 Testing basic Pushover configuration...")
        success = test_pushover()
        if success:
            print("🎉 Pushover is configured correctly!")
            print("💡 Run 'python pushover_utils.py coaching' to test the enhanced coaching alerts")
        else:
            print("❌ Pushover test failed. Check your credentials.")
