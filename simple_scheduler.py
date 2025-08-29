#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple 60-minute scheduler for LaCentrale scraping
Imports and calls the main() function directly - no subprocess issues!

Usage: python simple_scheduler.py
"""

import time
import sys
from datetime import datetime

def run_scraping():
    """Import and run the main() function from optimized_scraping"""
    try:
        print(f"🚀 [{datetime.now().strftime('%H:%M:%S')}] Starting scraping...")
        
        # Import the main function from optimized_scraping
        from optimized_scraping import main
        
        # Call the main function directly
        main()
        
        print(f"✅ [{datetime.now().strftime('%H:%M:%S')}] Scraping completed successfully!")
        return True
        
    except KeyboardInterrupt:
        print(f"\n🛑 [{datetime.now().strftime('%H:%M:%S')}] Scraping interrupted by user")
        return False
    except Exception as e:
        print(f"❌ [{datetime.now().strftime('%H:%M:%S')}] Error: {e}")
        return False

def main_scheduler():
    """Main scheduler loop - runs every 60 minutes"""
    print("🕐 Simple 60-Minute LaCentrale Scheduler")
    print("=" * 50)
    print("📅 Schedule: Every 60 minutes")
    print("🎯 Method: Direct function call")
    print("🛑 Press Ctrl+C to stop")
    print("=" * 50)
    
    # Run immediately on start
    run_scraping()
    
    try:
        while True:
            print(f"\n⏰ [{datetime.now().strftime('%H:%M:%S')}] Waiting 60 minutes for next run...")
            next_run = datetime.now().replace(minute=(datetime.now().minute + 60) % 60, second=0)
            print(f"   Next run at: {next_run.strftime('%H:%M:%S')}")
            
            # Wait 60 minutes (3600 seconds)
            time.sleep(3600)
            
            # Run the scraping
            run_scraping()
            
    except KeyboardInterrupt:
        print(f"\n🛑 [{datetime.now().strftime('%H:%M:%S')}] Scheduler stopped by user")
    except Exception as e:
        print(f"\n❌ [{datetime.now().strftime('%H:%M:%S')}] Unexpected error: {e}")

if __name__ == "__main__":
    main_scheduler()
