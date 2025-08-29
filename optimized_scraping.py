#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Aug 9 2025

@author: dduong

Optimized LaCentrale Scraping - Optimized Mode
Optimized version with all performance improvements enabled

Usage: python optimized_scraping.py
"""


def main():
    """
    Optimized scraping workflow - Maximum speed configuration
    """
    print(">>> LaCentrale OPTIMIZED Scraping - MAXIMUM SPEED MODE")
    print("=" * 70)

    # =================================================================
    # SIMPLE CONFIGURATION - EDIT YOUR DATABASE CREDENTIALS BELOW
    # =================================================================
    
    # Database connection - UPDATE WITH YOUR EXISTING DATABASE CREDENTIALS
    # Method 1: Connect to existing database (edit with your real credentials)
    # connection_string = "postgresql://postgres:YOUR_PASSWORD##@localhost:5432/lacentrale_db"
    
    # Method 1b: If database is on different host/port:
    # connection_string = "postgresql://postgres:your_password_here@your_host:5432/lacentrale_db"
    
    # Method 2: Use environment variables (recommended)
    # Create a .env file with POSTGRES_PASSWORD=your_password
    # Uncomment the lines below:
    import os
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file
    password = os.getenv('POSTGRES_PASSWORD', 'your_password_here')
    connection_string = f"postgresql://postgres:{password}@localhost:5432/lacentrale_db"

    # Optimized scraping configuration
    database_approach = "normalized"  # or "denormalized"
    start_page = 1
    end_page = 30 # Smaller range for testing
    auto_close_driver = False
    incremental_mode = True

    # PERFORMANCE SETTINGS
    optimized_mode = True       # Fast delays, optimized Chrome
    parallel_mode = True        # Parallel processing
    num_workers = 2            # Number of parallel workers

    print(f">>> OPTIMIZED Configuration:")
    print(f"   Database: {database_approach} approach")
    print(f"   Pages: {start_page} to {end_page}")
    print(f"   Mode: Maximum speed (6-30x faster)")
    print(f"   Optimized Chrome: Enabled (images/plugins disabled)")
    print(f"   Fast delays: 0.1-0.3 seconds")
    print(f"   Parallel workers: {num_workers}")
    print(f"   Expected time: ~{(end_page - start_page + 1) / num_workers / 10:.1f} minutes (vs ~{(end_page - start_page + 1):.0f} minutes normal)")
    
    # =================================================================
    # STEP 1: INITIALIZE OPTIMIZED HYBRID SCRAPER
    # =================================================================

    from scraping.hybrid_scraper import create_hybrid_scraper

    try: 
        print(f"\n Step 1: Initializing optimized hybrid scraper...")
        scraper = create_hybrid_scraper(connection_string, database_approach)

        # Maximum performance configuration
        scraper.buffer_size = 3000              # Large buffer
        scraper.backup_enabled = True           # Safety net
        scraper.auto_index = True               # Performance optimization
        scraper.enable_optimized_mode()         # Enable all optimizations             
        print("[OK] Optimized hybrid scraper initialized successfully!")
        
    except Exception as e:
        print(f"[ERROR] Failed to initialize scraper: {e}")
        print("NOTE: Check your database connection string and ensure PostgreSQL is running")
        return
    
    # =================================================================
    # STEP 2: SETUP DATABASE WITH PERFORMANCE INDEXES
    # =================================================================

    try:
        print(f"\n>>> Step 2: Setting up database with performance indexes...")
        scraper.setup_database_with_indexes()
        print("[OK] Database setup completed successfully!")
        
    except Exception as e:
        print(f"[ERROR] Database setup failed: {e}")
        print("NOTE: Ensure you have CREATE privileges on the database")
        return
    
    # =================================================================
    # STEP 3: CONFIGURE INCREMENTAL SCRAPING
    # =================================================================
    
    if incremental_mode:
        try:
            print(f"\n>>> Step 3: Configuring incremental scraping...")
            scraper.enable_incremental_scraping()
        except Exception as e:
            print(f"[ERROR] Failed to enable incremental mode: {e}")
            print("NOTE: Continuing with full scraping mode")
            incremental_mode = False
    else:
        print(f"\n>>> Step 3: Full scraping mode enabled")
    

    # =================================================================
    # STEP 4: START OPTIMIZED SCRAPING
    # =================================================================
    
    try:
        print(f"\n>>> Step 4: Starting MAXIMUM SPEED scraping...")
        print(f"   Strategy: Parallel + Optimized + Direct DB")
        print(f"   Workers: {num_workers} parallel Chrome instances")
        print(f"   Optimizations: All enabled")
        print(f"   Expected speed: 20-30x faster than normal")
        
        # Start parallel optimized scraping
        scraper.scrape_with_parallel_approach(
            start_page=start_page,
            end_page=end_page,
            num_workers=num_workers,
            auto_close=auto_close_driver
        )
        
    except KeyboardInterrupt:
        print(f"\n[WARNING] Scraping interrupted by user")
        print("INFO: Partial results have been saved to database")
        
    except Exception as e:
        print(f"[ERROR] Scraping error: {e}")
        print("NOTE: Check website accessibility and network connection")
        
    finally:
        print(f"\n>>> OPTIMIZED SCRAPING COMPLETED!")
        print(f"=" * 60)
        print(f">>> MAXIMUM SPEED MODE BENEFITS:")
        print(f"   • Optimized Chrome driver (disabled images/plugins)")
        print(f"   • Fast delays (0.1-0.3 seconds)")
        print(f"   • Fast cookie consent (1 second timeout)")
        print(f"   • Fast scrolling (single scroll)")
        print(f"   • Parallel processing ({num_workers} workers)")
        print(f"   • Large database buffer (3000 cars)")
        print(f"   • Expected speed improvement: 20-30x")
        
        print(f"\n>>> Next steps:")
        print(f"   1. Run query examples: python query_examples.py")
        print(f"   2. Compare performance with normal mode")
        print(f"   3. Monitor for any detection issues")
        print(f"   4. Adjust num_workers if needed (2-5 recommended)")

if __name__ == "__main__":
    print(">>> LaCentrale OPTIMIZED Scraping - MAXIMUM SPEED MODE")
    print("=" * 70)
    main()