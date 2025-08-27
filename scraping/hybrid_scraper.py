# -*- coding: utf-8 -*-
"""
Hybrid Scraper Implementation - LaCentrale Car Data
Direct database insertion with smart buffering and automatic indexing
Uses undetected_chromedriver for stealth scraping

HYBRID APPROACH:
- Primary: Direct PostgreSQL insertion (no JSON files)
- Buffer: 3000 cars in memory before DB flush
- Backup: JSON files only on database errors
- Indexing: Automatic performance optimization
- Stealth: undetected_chromedriver for anti-detection

@author: dduong
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
import concurrent.futures
import threading
import queue
from bs4 import BeautifulSoup as BS4
import re
import demjson3
from sqlalchemy import text
from database.db_utils import DatabaseManager, bulk_insert_car_listings
from data.save_data import validate_car_data
from scraping.utils import random_delay, random_delay_fast, pass_accepter, pass_accepter_fast, gradual_scroll, fast_scroll, get_undetected_driver, get_optimized_undetected_driver, cleanup_chrome_processes, cleanup_worker_directories, debug_page_elements


class HybridScraper:
    """
    Hybrid high-performance scraper with automatic indexing and undetected_chromedriver
    """
    
    def __init__(self, connection_string: str, approach: str = "normalized"):
        """
        Initialize hybrid scraper
        
        Args:
            connection_string: PostgreSQL connection string
            approach: Database approach ("normalized" or "denormalized")
        """
        self.db_manager = DatabaseManager(connection_string, approach)
        self.approach = approach
        self.connection_string = connection_string
        self.driver = None  # Will be initialized with undetected_chromedriver
        
        # Hybrid configuration
        self.buffer_size = 2000  # Large buffer for better performance
        self.optimized_mode = False  # Can be enabled for speed optimization
        self.memory_buffer = []
        self.backup_enabled = True  # JSON backup only on errors
        self.auto_index = True  # Automatic index creation
        
        # Statistics
        self.stats = {
            'pages_scraped': 0,
            'cars_found': 0,
            'cars_saved': 0,
            'cars_skipped': 0,
            'errors': 0,
            'db_insertions': 0,
            'json_backups': 0,
            'new_cars': 0,
            'existing_cars_skipped': 0
        }
        
        # Incremental scraping state
        self.state_file = "data/scraping_state.json"
        self.existing_references: Set[str] = set()
        self.last_scrape_time: Optional[datetime] = None
        self.incremental_mode = False
        
        # Create backup directory
        if self.backup_enabled:
            os.makedirs("data/backup", exist_ok=True)
        
        print(f"🚀 HYBRID SCRAPER INITIALIZED")
        print(f"   Database: {approach} approach")
        print(f"   Strategy: Direct DB insertion + Smart buffering")
        print(f"   Buffer size: {self.buffer_size} cars")
        print(f"   Backup: Only on errors")
        print(f"   Auto-indexing: {'Enabled' if self.auto_index else 'Disabled'}")
        print(f"   Driver: undetected_chromedriver (stealth mode)")
        print(f"   Optimized mode: {'Enabled' if self.optimized_mode else 'Disabled'}")
    
    def initialize_driver(self):
        """
        Initialize undetected Chrome driver for stealth scraping
        """
        print("\n🌐 INITIALIZING UNDETECTED CHROME DRIVER")
        print("=" * 60)
        
        try:
            if self.optimized_mode:
                self.driver = get_optimized_undetected_driver()
                print("✅ Optimized undetected Chrome driver initialized successfully!")
            else:
                self.driver = get_undetected_driver()
                print("✅ Undetected Chrome driver initialized successfully!")
            return self.driver
        except Exception as e:
            print(f"❌ Failed to initialize driver: {e}")
            raise
    
    def close_driver(self):
        """
        Safely close the Chrome driver with Windows compatibility
        """
        if self.driver:
            try:
                # Close all windows first
                for handle in self.driver.window_handles:
                    self.driver.switch_to.window(handle)
                    self.driver.close()
                
                # Then quit the driver
                self.driver.quit()
                print("✅ Chrome driver closed successfully!")
            except Exception as e:
                # Suppress common Windows cleanup errors
                if "Descripteur non valide" in str(e) or "WinError 6" in str(e):
                    print("✅ Chrome driver closed (Windows cleanup warning ignored)")
                else:
                    print(f"⚠️  Warning while closing driver: {e}")
            finally:
                self.driver = None
                # Force garbage collection to help with cleanup
                import gc
                gc.collect()
    
    def _safe_close_driver(self):
        """
        Safe driver close with Windows-specific error handling
        """
        if not self.driver:
            return
            
        try:
            # Suppress Windows cleanup warnings during shutdown
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self.close_driver()
        except SystemExit:
            # Allow normal exit
            pass
        except:
            # Silently handle any remaining cleanup issues
            self.driver = None
        finally:
            # Windows-specific process cleanup
            cleanup_chrome_processes()
    
    def enable_optimized_mode(self):
        """
        Enable optimized scraping mode for maximum speed
        - Uses optimized Chrome driver with disabled features
        - Uses fast delays and scrolling
        - Uses fast cookie consent handling
        """
        print("\n⚡ ENABLING OPTIMIZED SCRAPING MODE")
        print("=" * 60)
        
        self.optimized_mode = True
        self.buffer_size = 3000  # Even larger buffer
        
        print("✅ Optimized mode enabled!")
        print("   • Optimized Chrome driver (images/plugins disabled)")
        print("   • Fast delays (0.1-0.3 seconds)")
        print("   • Fast scrolling (single scroll)")
        print("   • Fast cookie consent (1 second timeout)")
        print(f"   • Increased buffer size ({self.buffer_size} cars)")
        print("   ⚠️  Note: Less human-like behavior, higher detection risk")
    

    
    def enable_incremental_scraping(self):
        """
        Enable incremental scraping mode to only get new listings
        """
        print("\n🔄 ENABLING INCREMENTAL SCRAPING MODE")
        print("=" * 60)
        
        self.incremental_mode = True
        
        # Load previous scraping state
        self._load_scraping_state()
        
        # Load existing car references from database
        self._load_existing_references()
        
        print(f"✅ Incremental mode enabled!")
        print(f"   Last scrape: {self.last_scrape_time or 'Never'}")
        print(f"   Known cars: {len(self.existing_references):,}")
    
    def _load_scraping_state(self):
        """
        Load the last scraping state from file
        """
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    
                self.last_scrape_time = datetime.fromisoformat(state.get('last_scrape_time')) if state.get('last_scrape_time') else None
                print(f"   Loaded state: Last scrape at {self.last_scrape_time}")
            else:
                print("   No previous state found - will perform full scraping")
                
        except Exception as e:
            print(f"   ⚠️  Failed to load scraping state: {e}")
            self.last_scrape_time = None
    
    def _save_scraping_state(self):
        """
        Save the current scraping state to file
        """
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            
            state = {
                'last_scrape_time': datetime.now().isoformat(),
                'cars_found': self.stats['new_cars'],
                'total_known_cars': len(self.existing_references)
            }
            
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
                
            print(f"   💾 Saved scraping state to {self.state_file}")
            
        except Exception as e:
            print(f"   ⚠️  Failed to save scraping state: {e}")
    
    def _load_existing_references(self):
        """
        Load existing car references from database to avoid duplicates
        """
        try:
            # Get all existing car references from database
            table_name = "car_listings_flat" if self.approach == "denormalized" else "car_listings"
            
            with self.db_manager.engine.connect() as conn:
                result = conn.execute(text(f"SELECT reference FROM {table_name}"))
                self.existing_references = {row[0] for row in result}
                
            print(f"   Loaded {len(self.existing_references):,} existing car references from database")
            
        except Exception as e:
            print(f"   ⚠️  Failed to load existing references: {e}")
            self.existing_references = set()
    
    def setup_database_with_indexes(self):
        """
        Setup database tables and create performance indexes
        """
        print("\n🏗️  SETTING UP DATABASE WITH HYBRID APPROACH")
        print("=" * 60)
        
        try:
            # Create tables
            print("📋 Creating database tables...")
            self.db_manager.create_tables()
            
            # Create performance indexes if enabled
            if self.auto_index:
                print("⚡ Creating performance indexes...")
                self._create_essential_indexes()
            
            print("✅ Database setup completed successfully!")
            
        except Exception as e:
            print(f"❌ Database setup failed: {e}")
            raise
    
    def _create_essential_indexes(self):
        """
        Create essential indexes for performance
        """
        
        essential_indexes = [
            # Critical performance indexes
            {
                'name': 'idx_price_performance',
                'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_price_performance ON car_listings (price DESC, created_at DESC)',
                'description': 'Price searches with date sorting'
            },
            {
                'name': 'idx_make_model_year',
                'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_make_model_year ON vehicles (manufacturer_id, car_model_id, year DESC)',
                'description': 'Make/model/year searches'
            },
            {
                'name': 'idx_location_search',
                'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_location_search ON dealers (visit_place)',
                'description': 'Location-based searches'
            },
            {
                'name': 'idx_reference_lookup',
                'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reference_lookup ON car_listings USING hash (reference)',
                'description': 'Exact reference lookups'
            },
            {
                'name': 'idx_energy_gearbox',
                'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_energy_gearbox ON vehicles (energy, gearbox, year DESC)',
                'description': 'Energy and gearbox filtering'
            }
        ]
        
        # Alternative indexes for denormalized approach
        if self.approach == "denormalized":
            essential_indexes = [
                {
                    'name': 'idx_flat_comprehensive',
                    'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_flat_comprehensive ON car_listings_flat (make, model, year DESC, price ASC)',
                    'description': 'Comprehensive search index'
                },
                {
                    'name': 'idx_flat_price_location',
                    'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_flat_price_location ON car_listings_flat (price ASC, dealer_visit_place)',
                    'description': 'Price and location searches'
                },
                {
                    'name': 'idx_flat_energy_specs',
                    'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_flat_energy_specs ON car_listings_flat (energy, gearbox, year DESC)',
                    'description': 'Energy and specifications'
                }
            ]
        
        # Create indexes using autocommit mode to avoid transaction issues
        for idx in essential_indexes:
            try:
                print(f"   Creating {idx['name']}...")
                # Get raw connection and handle it properly
                raw_conn = self.db_manager.engine.raw_connection()
                try:
                    raw_conn.autocommit = True
                    cursor = raw_conn.cursor()
                    try:
                        # Remove CONCURRENTLY to avoid transaction issues
                        sql_command = idx['sql'].replace('CREATE INDEX CONCURRENTLY IF NOT EXISTS', 'CREATE INDEX IF NOT EXISTS')
                        cursor.execute(sql_command)
                        print(f"   ✅ {idx['description']}")
                    finally:
                        cursor.close()
                finally:
                    raw_conn.close()
            except Exception as e:
                print(f"   ⚠️  {idx['name']}: {e}")
                # If index creation fails, it might already exist - continue
                continue
    
    def scrape_with_hybrid_approach(self, start_page: int = 2, end_page: int = 10, auto_close: bool = True):
        """
        Main scraping function using hybrid approach with undetected_chromedriver
        
        Args:
            start_page: Starting page number
            end_page: Ending page number
            auto_close: Whether to automatically close driver after scraping
        """
        print(f"\n🎯 STARTING HYBRID SCRAPING (pages {start_page}-{end_page})")
        print("=" * 60)
        
        try:
            # Initialize driver if not already done
            if not self.driver:
                self.initialize_driver()
            
            # Main scraping loop - using same logic as scraper.py
            for page_num in range(start_page, end_page + 1):
                try:
                    self._scrape_single_page_lacentrale(page_num)
                    self.stats['pages_scraped'] += 1
                    
                    # Smart buffer management
                    if len(self.memory_buffer) >= self.buffer_size:
                        self._flush_buffer_to_database()
                    
                    # Progress update every 5 pages
                    if page_num % 5 == 0:
                        self._print_progress()
                    
                except KeyboardInterrupt:
                    print(f"\n⚠️  Scraping interrupted by user at page {page_num}")
                    break
                except Exception as e:
                    print(f"❌ Error scraping page {page_num}: {e}")
                    self.stats['errors'] += 1
                    continue
            
            # Final flush
            self._flush_buffer_to_database()
            
            # Save scraping state for incremental mode
            if self.incremental_mode:
                self._save_scraping_state()
            
            self._print_final_stats()
            
        except Exception as e:
            print(f"❌ Critical error in hybrid scraping: {e}")
            self._flush_buffer_to_database()  # Save what we have
            
            # Save state even on error for incremental mode
            if self.incremental_mode:
                self._save_scraping_state()
        finally:
            # Auto-close driver if requested
            if auto_close:
                self._safe_close_driver()
    
    def scrape_with_parallel_approach(self, start_page: int = 1, end_page: int = 10, num_workers: int = 2, auto_close: bool = True):
        """
        Parallel scraping approach using multiple workers for maximum speed
        
        Args:
            start_page: Starting page number
            end_page: Ending page number
            num_workers: Number of parallel workers (recommended: 3-5)
            auto_close: Whether to automatically close drivers after scraping
        """
        print(f"\n🚀 STARTING PARALLEL SCRAPING ({num_workers} workers, pages {start_page}-{end_page})")
        print("=" * 60)
        print(f"⚠️  WARNING: Parallel mode may increase detection risk")
        print(f"   Recommended for private/testing environments")
        
        # Create page queue
        page_queue = queue.Queue()
        for page in range(start_page, end_page + 1):
            page_queue.put(page)
        
        # Shared results collection
        results_queue = queue.Queue()
        workers_finished = threading.Event()
        
        def worker(worker_id):
            """Worker function that processes pages"""
            # Each worker gets its own driver
            worker_driver = None
            cars_processed = 0
            
            try:
                print(f"   🔧 Worker {worker_id}: Initializing driver...")
                if self.optimized_mode:
                    worker_driver = get_optimized_undetected_driver(worker_id=worker_id)
                else:
                    worker_driver = get_undetected_driver(worker_id=worker_id)
                
                while True:
                    try:
                        page_num = page_queue.get(timeout=2)
                        print(f"   📄 Worker {worker_id}: Processing page {page_num}")
                        
                        # Scrape single page with this worker's driver
                        cars = self._scrape_single_page_with_driver(worker_driver, page_num)
                        results_queue.put((worker_id, page_num, cars))
                        cars_processed += len(cars)
                        
                        page_queue.task_done()
                        
                    except queue.Empty:
                        # No more pages to process
                        break
                        
                print(f"   ✅ Worker {worker_id}: Finished processing {cars_processed} cars")
                        
            except Exception as e:
                print(f"   ❌ Worker {worker_id}: Error - {e}")
            finally:
                if worker_driver:
                    try:
                        # Safe driver cleanup with Windows compatibility
                        worker_driver.quit()
                        print(f"   ✅ Worker {worker_id}: Driver closed safely")
                    except Exception as cleanup_error:
                        # Suppress Windows-specific cleanup errors
                        if "Descripteur non valide" in str(cleanup_error) or "WinError 6" in str(cleanup_error):
                            print(f"   ✅ Worker {worker_id}: Driver closed (Windows cleanup warning ignored)")
                        else:
                            print(f"   ⚠️  Worker {worker_id}: Warning during driver cleanup: {cleanup_error}")
                    finally:
                        # Force cleanup for this worker
                        cleanup_chrome_processes()
        
        # Start worker threads
        workers = []
        try:
            print(f"   🚀 Starting {num_workers} worker threads...")
            
            for i in range(num_workers):
                worker_thread = threading.Thread(target=worker, args=(i+1,))
                worker_thread.start()
                workers.append(worker_thread)
            
            # Collect results as they come in
            total_cars_collected = 0
            results_buffer = []
            
            while any(worker.is_alive() for worker in workers) or not results_queue.empty():
                try:
                    worker_id, page_num, cars = results_queue.get(timeout=1)
                    
                    if cars:
                        results_buffer.extend(cars)
                        total_cars_collected += len(cars)
                        self.stats['cars_found'] += len(cars)
                        print(f"   📊 Collected {len(cars)} cars from page {page_num} (Total: {total_cars_collected})")
                        
                        # Flush buffer when it gets large
                        if len(results_buffer) >= self.buffer_size:
                            self._flush_cars_to_database(results_buffer)
                            results_buffer = []
                    
                except queue.Empty:
                    continue
            
            # Wait for all workers to finish
            for worker in workers:
                worker.join()
            
            # Final flush of remaining cars
            if results_buffer:
                self._flush_cars_to_database(results_buffer)
            
            # Save scraping state for incremental mode
            if self.incremental_mode:
                self._save_scraping_state()
            
            print(f"\n🎉 PARALLEL SCRAPING COMPLETED!")
            print(f"   Total cars found: {total_cars_collected}")
            print(f"   Workers used: {num_workers}")
            self._print_final_stats()
            
        except KeyboardInterrupt:
            print(f"\n⚠️ Parallel scraping interrupted by user")
            # Signal workers to stop
            workers_finished.set()
            
        except Exception as e:
            print(f"❌ Critical error in parallel scraping: {e}")
            
        finally:
            # Ensure all workers are terminated
            for worker in workers:
                if worker.is_alive():
                    worker.join(timeout=5)
            
            # Final cleanup of temporary worker directories
            try:
                cleanup_worker_directories()
                print("✅ Cleaned up temporary worker directories")
            except Exception as e:
                print(f"⚠️  Warning during worker directory cleanup: {e}")
    
    def _scrape_single_page_with_driver(self, driver, page_num: int):
        """
        Scrape a single page with a specific driver (for parallel processing)
        """
        try:
            # Navigate to page
            if self.optimized_mode:
                random_delay_fast()
            else:
                random_delay()
            
            driver.get(f"https://www.lacentrale.fr/listing?options=&page={page_num}&sortBy=firstOnlineDateDesc")
            
            # Handle cookie consent
            if self.optimized_mode:
                pass_accepter_fast(driver, max_wait=1)
            else:
                pass_accepter(driver)

            # Scroll
            gradual_scroll(driver)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            fast_scroll(driver)
                
            # Parse page content
            html_content = driver.page_source
            soup = BS4(html_content, 'html.parser')

            # Find script tag with preloaded state
            script_tag = soup.find('script', string=re.compile('window.__PRELOADED_STATE_LISTING__'))
            if not script_tag:
                return []
            
            # Extract JSON
            script_text = script_tag.text
            match = re.search(r"window\.__PRELOADED_STATE_LISTING__\s*=\s*(\{.*\})\s*;\s*", script_text, re.DOTALL)
            if not match:
                return []
            
            preloaded_state = demjson3.decode(match.group(1))
            
            # Find car links
            car_links = {}
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                if 'auto-occasion-annonce' in href:
                    parent_div = a_tag.find_parent("div", attrs={"data-tracking-meta": True})
                    if parent_div:
                        try:
                            tracking_meta = json.loads(parent_div["data-tracking-meta"].replace("&quot;", "\""))
                            classified_ref = tracking_meta.get("classified_ref")
                            if classified_ref:
                                car_links[classified_ref] = "https://www.lacentrale.fr" + href
                        except (json.JSONDecodeError, KeyError):
                            continue

            # Process cars
            list_cars = preloaded_state['search']['hits']
            cars_to_save = []
            
            for car in list_cars:
                car_ref = car['item']['reference']
                
                # Check incremental mode
                if self.incremental_mode and car_ref in self.existing_references:
                    continue
                
                if car_ref in car_links:
                    car["url"] = car_links[car_ref]
                    
                    if validate_car_data(car):
                        cars_to_save.append(car)
                        if self.incremental_mode:
                            self.existing_references.add(car_ref)
            
            return cars_to_save
            
        except Exception as e:
            print(f"   ❌ Error scraping page {page_num}: {e}")
            return []
    
    def _flush_cars_to_database(self, cars_data: List[Dict]):
        """
        Flush cars to database (thread-safe version)
        """
        if not cars_data:
            return
        
        try:
            success_count = bulk_insert_car_listings(self.db_manager, cars_data)
            self.stats['cars_saved'] += success_count
            self.stats['db_insertions'] += 1
            print(f"   💾 Flushed {success_count} cars to database")
            
        except Exception as e:
            print(f"   ❌ Database flush error: {e}")
            if self.backup_enabled:
                self._save_json_backup(cars_data, "parallel_db_failure")
    
    def _scrape_single_page_lacentrale(self, page_num: int):
        """
        Scrape a single page using exact logic from scraper.py
        """
        print(f"📄 Scraping page {page_num}...")
        
        # Navigate to page using optimized or standard pattern
        if self.optimized_mode:
            random_delay_fast()
        else:
            random_delay()
        
        self.driver.get(f"https://www.lacentrale.fr/listing?options=&page={page_num}&sortBy=firstOnlineDateDesc")
        
        # Handle cookie consent with optimized or standard approach
        if self.optimized_mode:
            consent_handled = pass_accepter_fast(self.driver, max_wait=1)
        else:
            consent_handled = pass_accepter(self.driver)
            if not consent_handled and page_num == 2:  # Only debug on first page
                print(f"   🔍 Cookie consent failed on page {page_num}, debugging...")
                debug_page_elements(self.driver)
        
        # Use optimized or standard scrolling
        # if self.optimized_mode:
        #     fast_scroll(self.driver)
        # else:
        gradual_scroll(self.driver)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    
        html_content = self.driver.page_source
        soup = BS4(html_content, 'html.parser')

        # Find <script> tag with name "window.__PRELOADED_STATE_LISTING__" - exact same logic as scraper.py
        script_tag = soup.find('script', string=re.compile('window.__PRELOADED_STATE_LISTING__'))
        if script_tag:
            print(f"   Found script tag with name 'window.__PRELOADED_STATE_LISTING__' on page {page_num}")
            
            # Extract JSON part using regex (exact same pattern as scraper.py)
            script_text = script_tag.text
            match = re.search(r"window\.__PRELOADED_STATE_LISTING__\s*=\s*(\{.*\})\s*;\s*", script_text, re.DOTALL)
            if match:
                json_str = match.group(1)
                preloaded_state = demjson3.decode(match.group(1))
                print(f"   Preloaded state keys: {preloaded_state.keys()}")
            else:
                print(f"   ❌ No match found for 'window.__PRELOADED_STATE_LISTING__' on page {page_num}")
                return
        else:
            print(f"   ❌ Script tag with name 'window.__PRELOADED_STATE_LISTING__' not found on page {page_num}")
            return

        # Find the list of car's link by using "auto-occasion-annonce" in the href - exact same logic as scraper.py
        car_links = {}
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if 'auto-occasion-annonce' in href:
                # Find the nearest parent with 'data-tracking-meta'
                parent_div = a_tag.find_parent("div", attrs={"data-tracking-meta": True})
                if parent_div:
                    try:
                        tracking_meta = json.loads(parent_div["data-tracking-meta"].replace("&quot;", "\""))
                        classified_ref = tracking_meta.get("classified_ref")
                        if classified_ref:
                            car_links[classified_ref] = "https://www.lacentrale.fr" + href
                    except (json.JSONDecodeError, KeyError):
                        continue

        # Find the list of cars in "search/hits" key - exact same logic as scraper.py
        list_cars = preloaded_state['search']['hits']
        print(f"   Found {len(list_cars)} cars on page {page_num}")
        
        # Prepare cars for bulk saving - same validation logic as scraper.py
        cars_to_save = []
        new_cars_count = 0
        
        for car in list_cars: 
            car_ref = car['item']['reference']
            
            # Check if this is a new car (for incremental scraping)
            if self.incremental_mode and car_ref in self.existing_references:
                self.stats['existing_cars_skipped'] += 1
                continue  # Skip existing cars in incremental mode
            
            if car_ref in car_links:
                car["url"] = car_links[car_ref]
                
                # Validate car data before saving
                if validate_car_data(car):
                    cars_to_save.append(car)
                    self.stats['cars_found'] += 1
                    
                    # Track new cars in incremental mode
                    if self.incremental_mode:
                        new_cars_count += 1
                        self.stats['new_cars'] += 1
                        self.existing_references.add(car_ref)  # Add to known references
                        print(f"   🆕 NEW car {car_ref} prepared for saving")
                    else:
                        print(f"   ✅ Prepared car {car_ref} for saving")
                else:
                    self.stats['cars_skipped'] += 1
                    print(f"   ⚠️  Skipping invalid car data for {car_ref}")
            else:
                self.stats['cars_skipped'] += 1
                print(f"   ⚠️  No URL found for car {car_ref}")
        
        # Add to memory buffer instead of immediate saving
        self.memory_buffer.extend(cars_to_save)
        
        if self.incremental_mode:
            print(f"   💾 Added {len(cars_to_save)} cars to buffer ({new_cars_count} NEW, {self.stats['existing_cars_skipped']} existing skipped)")
            print(f"   📊 Buffer size: {len(self.memory_buffer)} | Total new cars this session: {self.stats['new_cars']}")
        else:
            print(f"   💾 Added {len(cars_to_save)} cars to buffer (buffer size: {len(self.memory_buffer)})")
    

    
    def _flush_buffer_to_database(self):
        """
        Hybrid buffer flush: Database first, JSON backup on error
        """
        if not self.memory_buffer:
            return
        
        buffer_size = len(self.memory_buffer)
        
        try:
            # PRIMARY: Insert to database
            success_count = bulk_insert_car_listings(self.db_manager, self.memory_buffer)
            self.stats['cars_saved'] += success_count
            self.stats['db_insertions'] += 1
            
            if success_count == buffer_size:
                print(f"   💾 Successfully inserted {success_count} cars to database")
            else:
                print(f"   ⚠️  Inserted {success_count}/{buffer_size} cars (some duplicates)")
            
            # BACKUP: Save to JSON only if database failed partially
            if success_count < buffer_size and self.backup_enabled:
                failed_cars = self.memory_buffer[success_count:]
                self._save_json_backup(failed_cars, "partial_failure")
            
        except Exception as e:
            print(f"   ❌ Database insertion failed: {e}")
            self.stats['errors'] += 1
            
            # BACKUP: Save entire buffer to JSON on complete failure
            if self.backup_enabled:
                self._save_json_backup(self.memory_buffer, "db_failure")
        
        # Clear buffer
        self.memory_buffer = []
    
    def _save_json_backup(self, cars_data: List[Dict], reason: str = "backup"):
        """
        Save cars to JSON backup file (only when needed)
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_file = f"data/backup/{reason}_{timestamp}_{len(cars_data)}_cars.json"
        
        try:
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(cars_data, f, indent=2, ensure_ascii=False)
            
            print(f"   💾 Saved JSON backup: {backup_file}")
            self.stats['json_backups'] += 1
            
        except Exception as e:
            print(f"   ❌ Failed to save JSON backup: {e}")
    
    def _print_progress(self):
        """Print current progress"""
        print(f"\n📊 HYBRID SCRAPER PROGRESS:")
        print(f"   Pages scraped: {self.stats['pages_scraped']}")
        print(f"   Cars found: {self.stats['cars_found']}")
        print(f"   Cars saved to DB: {self.stats['cars_saved']}")
        print(f"   Cars in buffer: {len(self.memory_buffer)}")
        print(f"   DB insertions: {self.stats['db_insertions']}")
        print(f"   JSON backups: {self.stats['json_backups']}")
        print(f"   Errors: {self.stats['errors']}")
        
        if self.incremental_mode:
            print(f"   🆕 NEW cars found: {self.stats['new_cars']}")
            print(f"   ⏭️  Existing cars skipped: {self.stats['existing_cars_skipped']}")
        print()
    
    def _print_final_stats(self):
        """Print final statistics"""
        print("\n" + "=" * 60)
        print("🎉 HYBRID SCRAPING COMPLETED!")
        print("=" * 60)
        print(f"📊 Final Statistics:")
        print(f"   Pages scraped: {self.stats['pages_scraped']}")
        print(f"   Cars found: {self.stats['cars_found']}")
        print(f"   Cars saved to database: {self.stats['cars_saved']}")
        print(f"   Cars skipped (invalid): {self.stats['cars_skipped']}")
        print(f"   Database insertions: {self.stats['db_insertions']}")
        print(f"   JSON backups created: {self.stats['json_backups']}")
        print(f"   Errors encountered: {self.stats['errors']}")
        
        # Incremental mode statistics
        if self.incremental_mode:
            print(f"\n🆕 INCREMENTAL SCRAPING RESULTS:")
            print(f"   NEW cars found: {self.stats['new_cars']}")
            print(f"   Existing cars skipped: {self.stats['existing_cars_skipped']}")
            print(f"   Total known cars: {len(self.existing_references):,}")
            
            if self.stats['new_cars'] > 0:
                print(f"   🎉 Found {self.stats['new_cars']} new car listings since last scrape!")
            else:
                print(f"   ℹ️  No new cars found - database is up to date")
        
        success_rate = (self.stats['cars_saved'] / max(self.stats['cars_found'], 1)) * 100
        print(f"\n   Success rate: {success_rate:.1f}%")
        
        # Hybrid approach benefits
        print(f"\n✅ HYBRID APPROACH BENEFITS:")
        print(f"   • Primary storage: PostgreSQL database")
        print(f"   • Backup files: {self.stats['json_backups']} (only on errors)")
        print(f"   • Memory efficient: {self.buffer_size}-car buffering")
        print(f"   • Performance optimized: Auto-indexing enabled")
        if self.incremental_mode:
            print(f"   • Incremental scraping: Only new listings processed")
            print(f"   • State tracking: Automatic progress persistence")


def create_hybrid_scraper(connection_string: str, approach: str = "normalized") -> HybridScraper:
    """
    Create and configure a hybrid scraper with undetected_chromedriver
    
    Args:
        connection_string: PostgreSQL connection string
        approach: "normalized" or "denormalized"
    
    Returns:
        Configured HybridScraper instance
    """
    scraper = HybridScraper(connection_string, approach)
    
    # Optimal configuration for 10,000+ cars/day
    scraper.buffer_size = 3000      # Larger buffer for high volume
    scraper.backup_enabled = True   # Safety net
    scraper.auto_index = True       # Performance optimization
    
    return scraper


if __name__ == "__main__":
    print("🚀 HYBRID SCRAPER - LaCentrale Car Data with Undetected Chrome")
    print("=" * 60)
    print("\nHYBRID APPROACH:")
    print("✅ Direct PostgreSQL insertion (primary)")
    print("✅ Smart memory buffering (500-1000 cars)")
    print("✅ JSON backup only on database errors")
    print("✅ Automatic performance indexing")
    print("✅ Real-time statistics and monitoring")
    print("✅ Undetected Chrome driver for stealth scraping")
    
    print(f"\n💡 Usage example:")
    print(f"""
# 1. Create hybrid scraper with built-in undetected Chrome
connection_string = "postgresql://user:pass@localhost:5432/lacentrale_db"
scraper = create_hybrid_scraper(connection_string, "normalized")

# 2. Setup database with indexes
scraper.setup_database_with_indexes()

# 3. Start scraping (driver is automatically initialized and managed)
scraper.scrape_with_hybrid_approach(start_page=2, end_page=50, auto_close=True)

# Driver is automatically closed when done!
""")