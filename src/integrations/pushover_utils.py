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

def send_pushover_notification(message, title="Alert", priority=0, url=None, url_title=None):
    """
    Send notification via Pushover (text only - images are for Notion)
    
    Args:
        message (str): Main notification message
        title (str): Notification title
        priority (int): -2 (silent), -1 (quiet), 0 (normal), 1 (high), 2 (emergency)
        url (str): Optional URL to include
        url_title (str): Optional title for the URL
    
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

    try:
        response = requests.post("https://api.pushover.net/1/messages.json", data=data)
        if response.status_code == 200:
            print(f"✅ Pushover sent: {title}")
            return True
        else:
            print(f"❌ Pushover failed: {response.text}")
            return False
    except Exception as e:
        print(f"🔥 Error sending Pushover notification: {e}")
        return False

def send_energy_alert(signal, confidence, title, reasoning, etfs=None, article_url=None, analysis=None):
    """
    Concise energy sector alerts - detailed analysis goes to Notion (no images in Pushover)
    
    Args:
        signal (str): Bullish/Bearish/Neutral
        confidence (int): Confidence score 1-10
        title (str): Article title
        reasoning (str): Brief AI reasoning (contextual insights stay in Notion)
        etfs (list): Affected ETFs
        article_url (str): Link to Notion page with full analysis
        analysis (dict): Full analysis (not used in alert to keep it concise)
    
    Returns:
        bool: True if sent successfully
    """
    # Determine priority based on confidence - keep it professional, not alarming
    if confidence >= 9:
        priority = 0  # Normal priority (even for 9/10)
        alert_level = "CRITICAL"
    elif confidence >= 8:
        priority = 0  # Normal priority 
        alert_level = "HIGH"
    elif confidence >= 7:
        priority = 0  # Normal priority
        alert_level = "STANDARD"
    else:
        return False  # Don't send low confidence alerts
    
    # Use text indicators instead of emojis for better compatibility
    signal_indicator = {
        "Bullish": "↗ BULLISH",
        "Bearish": "↘ BEARISH", 
        "Neutral": "→ NEUTRAL"
    }.get(signal, "? UNKNOWN")
    
    # Build concise message - keep it short and actionable
    message = f"""{signal_indicator} Signal ({confidence}/10)

{title[:80]}{'...' if len(title) > 80 else ''}

Reason: {reasoning}"""
    
    # Add affected ETFs if available - use simple text formatting
    if etfs and len(etfs) > 0:
        etf_list = ', '.join(etfs[:4])  # Show max 4 ETFs
        if len(etfs) > 4:
            etf_list += f" +{len(etfs)-4} more"
        message += f"\n\nETFs: {etf_list}"
    
    alert_title = f"MarketMan {alert_level}"
    
    return send_pushover_notification(
        message=message.strip(),
        title=alert_title,
        priority=priority,
        url=article_url,
        url_title="Full Analysis" if article_url else None
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
