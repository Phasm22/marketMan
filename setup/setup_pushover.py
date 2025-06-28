#!/usr/bin/env python3
"""
Pushover Setup Script for MarketMan

Helps users configure Pushover notifications with interactive setup.
"""

import os
import sys
import yaml
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.integrations.pushover_client import pushover_notifier


def get_user_input(prompt: str, default: str = "") -> str:
    """Get user input with optional default value"""
    if default:
        user_input = input(f"{prompt} [{default}]: ").strip()
        return user_input if user_input else default
    else:
        return input(f"{prompt}: ").strip()


def update_settings_file(api_token: str, user_token: str) -> bool:
    """Update the settings.yaml file with Pushover credentials"""
    settings_path = Path("config/settings.yaml")
    
    if not settings_path.exists():
        print("❌ config/settings.yaml not found!")
        return False
    
    try:
        # Read current settings
        with open(settings_path, 'r') as f:
            settings = yaml.safe_load(f)
        
        # Update Pushover settings
        if 'integrations' not in settings:
            settings['integrations'] = {}
        
        if 'pushover' not in settings['integrations']:
            settings['integrations']['pushover'] = {}
        
        settings['integrations']['pushover']['api_token'] = api_token
        settings['integrations']['pushover']['user_token'] = user_token
        settings['integrations']['pushover']['enabled'] = True
        
        # Write updated settings
        with open(settings_path, 'w') as f:
            yaml.dump(settings, f, default_flow_style=False, indent=2)
        
        print("✅ Settings updated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error updating settings: {e}")
        return False


def test_pushover_configuration() -> bool:
    """Test the Pushover configuration"""
    print("\n🧪 Testing Pushover configuration...")
    
    status = pushover_notifier.get_rate_limit_status()
    
    print(f"  Enabled: {status['enabled']}")
    print(f"  Configured: {status['configured']}")
    print(f"  Confidence Threshold: {status['confidence_threshold']}")
    print(f"  Risk Warnings: {status['risk_warnings_enabled']}")
    
    if not status['configured']:
        print("❌ Pushover not properly configured")
        return False
    
    # Test connection
    print("\n📱 Sending test notification...")
    success = pushover_notifier.test_connection()
    
    if success:
        print("✅ Test notification sent successfully!")
        print("   Check your device for the test message.")
        return True
    else:
        print("❌ Test notification failed")
        print("   Please check your credentials and try again.")
        return False


def show_configuration_help():
    """Show help for manual configuration"""
    print("\n📋 Manual Configuration Instructions:")
    print("=" * 50)
    print("1. Go to https://pushover.net/")
    print("2. Create an account (if you don't have one)")
    print("3. Get your User Key from the main page")
    print("4. Create a new application:")
    print("   - Click 'Create an Application'")
    print("   - Name: MarketMan")
    print("   - Description: Trading signal notifications")
    print("   - Get the API Token")
    print("5. Install Pushover on your devices")
    print("6. Run this setup script again")
    print("\n💡 You can also edit config/settings.yaml manually:")
    print("   integrations:")
    print("     pushover:")
    print("       api_token: 'your_api_token'")
    print("       user_token: 'your_user_key'")


def main():
    """Main setup function"""
    print("📱 MarketMan Pushover Setup")
    print("=" * 30)
    
    # Check if already configured
    status = pushover_notifier.get_rate_limit_status()
    if status['configured']:
        print("✅ Pushover appears to be configured!")
        response = get_user_input("Do you want to test the current configuration? (y/n)", "y")
        if response.lower() in ['y', 'yes']:
            if test_pushover_configuration():
                print("\n🎉 Pushover is working correctly!")
                return
            else:
                print("\n⚠️ Configuration test failed. Let's reconfigure...")
    
    # Get credentials
    print("\n🔑 Pushover Credentials Setup")
    print("=" * 30)
    
    api_token = get_user_input("Enter your Pushover API Token")
    user_token = get_user_input("Enter your Pushover User Key")
    
    if not api_token or not user_token:
        print("❌ Both API Token and User Key are required!")
        show_configuration_help()
        return
    
    # Update settings
    print("\n💾 Updating configuration...")
    if not update_settings_file(api_token, user_token):
        return
    
    # Test configuration
    if test_pushover_configuration():
        print("\n🎉 Pushover setup complete!")
        print("\n📊 Available commands:")
        print("  marketman pushover test     - Test connectivity")
        print("  marketman pushover status   - Show status")
        print("  marketman pushover signal   - Send test signal")
        print("  marketman pushover warning  - Send test warning")
        print("\n📈 Trading signals will now be sent automatically")
        print("   when confidence is above the threshold (7/10 by default)")
    else:
        print("\n❌ Setup incomplete. Please check your credentials.")
        show_configuration_help()


if __name__ == "__main__":
    main() 