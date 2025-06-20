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
    Send notification via Pushover
    
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

def send_energy_alert(signal, confidence, title, reasoning, etfs=None, article_url=None):
    """
    Specialized function for energy sector alerts
    
    Args:
        signal (str): Bullish/Bearish/Neutral
        confidence (int): Confidence score 1-10
        title (str): Article title
        reasoning (str): AI reasoning
        etfs (list): Affected ETFs
        article_url (str): Link to article
    
    Returns:
        bool: True if sent successfully
    """
    # Determine priority based on confidence
    if confidence >= 8:
        priority = 1  # High priority
        priority_emoji = "🚨"
    elif confidence >= 7:
        priority = 0  # Normal priority
        priority_emoji = "📊"
    else:
        return False  # Don't send low confidence alerts
    
    # Format signal with emoji
    signal_emoji = {
        "Bullish": "📈",
        "Bearish": "📉", 
        "Neutral": "➖"
    }.get(signal, "❓")
    
    # Build message
    message = f"""
{signal_emoji} {signal} Signal ({confidence}/10)

{title}

💡 {reasoning}
"""
    
    if etfs:
        message += f"\n🎯 ETFs: {', '.join(etfs)}"
    
    alert_title = f"{priority_emoji} Energy Alert: {signal}"
    
    return send_pushover_notification(
        message=message.strip(),
        title=alert_title,
        priority=priority,
        url=article_url,
        url_title="View in Notion" if article_url else None
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

if __name__ == "__main__":
    # Test the Pushover setup
    print("🧪 Testing Pushover configuration...")
    success = test_pushover()
    if success:
        print("🎉 Pushover is configured correctly!")
    else:
        print("❌ Pushover test failed. Check your credentials.")
