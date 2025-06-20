#!/usr/bin/env python3
"""
Combined MarketMan Monitor
Integrates system monitoring with news analysis for unified alerting

This brings together your proven server monitoring with news analysis
so you get both "yang.prox is down" and "TAN is tanking 👀" alerts
"""

import time
import subprocess
import sys
from datetime import datetime
from pushover_utils import send_system_alert, send_pushover_notification
from news_gpt_analyzer import NewsAnalyzer
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SystemMonitor:
    """System monitoring functionality (like your server_monitor.py)"""
    
    def __init__(self, hosts=None):
        self.hosts = hosts or [
            "yang.prox",
            "8.8.8.8",  # Google DNS as backup
            "1.1.1.1"   # Cloudflare DNS as backup
        ]
    
    def ping_host(self, host, timeout=5):
        """Ping a host and return True if reachable"""
        try:
            # Use ping command (works on Linux)
            result = subprocess.run(
                ['ping', '-c', '1', '-W', str(timeout), host],
                capture_output=True,
                text=True,
                timeout=timeout + 2
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error pinging {host}: {e}")
            return False
    
    def check_all_hosts(self):
        """Check all hosts and return status"""
        results = {}
        for host in self.hosts:
            is_up = self.ping_host(host)
            results[host] = is_up
            
            status = "UP" if is_up else "DOWN"
            logger.info(f"{host}: {status}")
            
            # Send alert for down hosts
            if not is_up:
                send_system_alert(
                    service_name=host,
                    status="DOWN",
                    details=f"Host unreachable at {datetime.now().strftime('%H:%M:%S')}"
                )
        
        return results

class MarketManMonitor:
    """Combined monitoring system"""
    
    def __init__(self):
        self.system_monitor = SystemMonitor()
        self.news_analyzer = NewsAnalyzer()
    
    def run_system_check(self):
        """Run system monitoring check"""
        logger.info("🖥️  Running system check...")
        try:
            results = self.system_monitor.check_all_hosts()
            up_count = sum(1 for status in results.values() if status)
            total_count = len(results)
            
            logger.info(f"System check complete: {up_count}/{total_count} hosts up")
            return results
        except Exception as e:
            logger.error(f"System check failed: {e}")
            send_system_alert("System Monitor", "ERROR", f"Monitor crashed: {e}")
            return {}
    
    def run_news_check(self):
        """Run news analysis check"""
        logger.info("📰 Running news analysis...")
        try:
            self.news_analyzer.process_alerts()
            logger.info("News analysis complete")
        except Exception as e:
            logger.error(f"News analysis failed: {e}")
            send_system_alert("News Analyzer", "ERROR", f"Analysis failed: {e}")
    
    def run_full_check(self):
        """Run both system and news checks"""
        logger.info("🚀 Starting MarketMan full check...")
        
        # System monitoring
        system_results = self.run_system_check()
        
        # News analysis
        self.run_news_check()
        
        # Summary notification for successful run
        up_hosts = sum(1 for status in system_results.values() if status)
        total_hosts = len(system_results)
        
        send_pushover_notification(
            message=f"✅ MarketMan check complete\n🖥️ System: {up_hosts}/{total_hosts} hosts up\n📰 News analysis completed",
            title="MarketMan Status",
            priority=-1  # Quiet notification
        )
        
        logger.info("🎉 MarketMan check complete")

def main():
    """Main function for CLI usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MarketMan Combined Monitor")
    parser.add_argument("--system-only", action="store_true", help="Run only system monitoring")
    parser.add_argument("--news-only", action="store_true", help="Run only news analysis") 
    parser.add_argument("--loop", type=int, help="Run continuously with interval in minutes")
    parser.add_argument("--test", action="store_true", help="Test Pushover connectivity")
    
    args = parser.parse_args()
    
    monitor = MarketManMonitor()
    
    if args.test:
        print("🧪 Testing Pushover connectivity...")
        from pushover_utils import test_pushover
        success = test_pushover()
        sys.exit(0 if success else 1)
    
    if args.loop:
        logger.info(f"🔄 Starting continuous monitoring (every {args.loop} minutes)")
        while True:
            try:
                if args.system_only:
                    monitor.run_system_check()
                elif args.news_only:
                    monitor.run_news_check()
                else:
                    monitor.run_full_check()
                
                logger.info(f"💤 Sleeping for {args.loop} minutes...")
                time.sleep(args.loop * 60)
                
            except KeyboardInterrupt:
                logger.info("👋 Stopping monitor...")
                break
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    else:
        # Single run
        if args.system_only:
            monitor.run_system_check()
        elif args.news_only:
            monitor.run_news_check()
        else:
            monitor.run_full_check()

if __name__ == "__main__":
    main()
