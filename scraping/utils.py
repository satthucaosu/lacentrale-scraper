import random
import time
import sys
import os
import warnings
import threading
import tempfile
import shutil
from pathlib import Path
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc

# Global lock for driver initialization to prevent file conflicts
_driver_init_lock = threading.Lock()

# Suppress Windows-specific undetected_chromedriver warnings
if sys.platform.startswith('win'):
    # Redirect stderr temporarily to suppress Windows handle errors
    import io
    from contextlib import redirect_stderr

class WindowsSafeChrome(uc.Chrome):
    """Windows-safe wrapper for undetected_chromedriver that suppresses cleanup errors"""
    
    def __del__(self):
        """Override destructor to suppress Windows handle errors"""
        if sys.platform.startswith('win'):
            try:
                # Suppress stderr during cleanup to hide Windows errors
                with open(os.devnull, 'w') as devnull:
                    with redirect_stderr(devnull):
                        super().__del__()
            except:
                # Silently ignore all cleanup errors on Windows
                pass
        else:
            # Normal cleanup on non-Windows systems
            try:
                super().__del__()
            except:
                pass

def _create_worker_driver_directory(worker_id=None):
    """
    Create a worker-specific directory for chromedriver to avoid file conflicts
    """
    if worker_id is None:
        worker_id = threading.current_thread().ident
    
    # Create a unique temp directory for this worker
    temp_dir = tempfile.mkdtemp(prefix=f"chromedriver_worker_{worker_id}_")
    
    # On Windows, we need to ensure the directory is writable
    if sys.platform.startswith('win'):
        try:
            # Test write permissions
            test_file = os.path.join(temp_dir, "test_write.tmp")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
        except Exception:
            # Fallback to system temp if there are permission issues
            temp_dir = tempfile.mkdtemp(prefix=f"uc_worker_{worker_id}_")
    
    return temp_dir

def get_undetected_driver(worker_id=None, max_retries=3):
    """
    Initialize undetected Chrome driver with worker isolation and retry mechanism
    """
    options = uc.ChromeOptions()
    options.add_argument("--disable-search-engine-choice-screen")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--no-first-run")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-gpu")  # Helps with Windows stability
    options.add_argument("--no-sandbox")  # Windows compatibility
    options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
    
    # Worker-specific user data directory to avoid conflicts
    if worker_id is not None:
        worker_temp_dir = _create_worker_driver_directory(worker_id)
        user_data_dir = os.path.join(worker_temp_dir, "chrome_profile")
        options.add_argument(f"--user-data-dir={user_data_dir}")
    
    for attempt in range(max_retries):
        try:
            # Use thread lock to prevent simultaneous driver creation
            with _driver_init_lock:
                # Add random delay to stagger worker initialization
                if worker_id is not None and attempt == 0:
                    delay = random.uniform(0.5, 2.0) * (worker_id if worker_id <= 5 else worker_id % 5)
                    time.sleep(delay)
                
                # Use our Windows-safe wrapper on Windows, regular driver elsewhere
                if sys.platform.startswith('win'):
                    driver = WindowsSafeChrome(options=options, version_main=None)
                else:
                    driver = uc.Chrome(options=options, version_main=None)
                return driver
                
        except Exception as e:
            if "Impossible de créer un fichier déjà existant" in str(e) or "WinError 183" in str(e):
                # File conflict error - retry with longer delay
                print(f"⚠️  Driver init attempt {attempt + 1} failed (file conflict): {e}")
                if attempt < max_retries - 1:
                    wait_time = random.uniform(2.0, 5.0) * (attempt + 1)
                    print(f"   Retrying in {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
                    continue
            else:
                print(f"⚠️  Driver init attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(1.0, 3.0))
                    continue
    
    # Final fallback with basic options
    print("⚠️  All attempts failed, trying fallback driver...")
    try:
        with _driver_init_lock:
            basic_options = uc.ChromeOptions()
            basic_options.add_argument("--no-sandbox")
            basic_options.add_argument("--disable-dev-shm-usage")
            
            if worker_id is not None:
                # Even for fallback, use worker-specific directory
                worker_temp_dir = _create_worker_driver_directory(worker_id)
                user_data_dir = os.path.join(worker_temp_dir, "chrome_profile_fallback")
                basic_options.add_argument(f"--user-data-dir={user_data_dir}")
            
            if sys.platform.startswith('win'):
                driver = WindowsSafeChrome(options=basic_options)
            else:
                driver = uc.Chrome(options=basic_options)
            return driver
    except Exception as e2:
        print(f"❌ Fallback driver initialization also failed: {e2}")
        raise

def get_optimized_undetected_driver(worker_id=None, max_retries=3):
    """Get optimized undetected Chrome driver with performance settings and worker isolation"""
    options = uc.ChromeOptions()
    
    # Basic options
    options.add_argument("--disable-search-engine-choice-screen")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--no-first-run")
    options.add_argument("--disable-popup-blocking")
    
    # Performance optimizations
    options.add_argument("--disable-images")                    # Skip image loading for speed
    options.add_argument("--disable-plugins")                   # Skip plugins
    options.add_argument("--disable-extensions")                # Skip extensions
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-renderer-backgrounding")
    
    # Memory and stability optimizations
    options.add_argument("--disable-gpu")                       # Windows stability
    options.add_argument("--no-sandbox")                        # Windows compatibility
    options.add_argument("--disable-dev-shm-usage")            # Limited resource problems
    options.add_argument("--memory-pressure-off")              # Reduce memory checks
    options.add_argument("--max-old-space-size=512")           # Limit memory usage
    
    # Worker-specific user data directory to avoid conflicts
    if worker_id is not None:
        worker_temp_dir = _create_worker_driver_directory(worker_id)
        user_data_dir = os.path.join(worker_temp_dir, "chrome_profile_optimized")
        options.add_argument(f"--user-data-dir={user_data_dir}")
    
    for attempt in range(max_retries):
        try:
            # Use thread lock to prevent simultaneous driver creation
            with _driver_init_lock:
                # Add random delay to stagger worker initialization
                if worker_id is not None and attempt == 0:
                    delay = random.uniform(0.5, 2.0) * (worker_id if worker_id <= 5 else worker_id % 5)
                    time.sleep(delay)
                
                # Use our Windows-safe wrapper on Windows, regular driver elsewhere
                if sys.platform.startswith('win'):
                    driver = WindowsSafeChrome(options=options, version_main=None)
                else:
                    driver = uc.Chrome(options=options, version_main=None)
                print("✅ Optimized Chrome driver initialized")
                return driver
                
        except Exception as e:
            if "Impossible de créer un fichier déjà existant" in str(e) or "WinError 183" in str(e):
                # File conflict error - retry with longer delay
                print(f"⚠️  Optimized driver init attempt {attempt + 1} failed (file conflict): {e}")
                if attempt < max_retries - 1:
                    wait_time = random.uniform(2.0, 5.0) * (attempt + 1)
                    print(f"   Retrying in {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
                    continue
            else:
                print(f"⚠️  Optimized driver init attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(1.0, 3.0))
                    continue
    
    print(f"⚠️  Optimized driver initialization failed after {max_retries} attempts")
    # Fallback to basic driver with same worker_id
    return get_undetected_driver(worker_id=worker_id, max_retries=max_retries)

def random_delay(min_sec=1.5, max_sec=3.5):
    """Sleep randomly between min and max seconds."""
    time.sleep(random.uniform(min_sec, max_sec))

def simulate_mouse_movements(driver, target_element, steps=30):
    """Moves the mouse slowly over an element in a human-like arc."""
    actions = ActionChains(driver)
    location = target_element.location_once_scrolled_into_view
    size = target_element.size

    center_x = location['x'] + size['width'] / 2
    center_y = location['y'] + size['height'] / 2

    # Start from random screen location
    start_x = random.randint(0, 300)
    start_y = random.randint(0, 300)

    for i in range(steps):
        inter_x = start_x + (center_x - start_x) * (i / steps)
        inter_y = start_y + (center_y - start_y) * (i / steps)
        actions.move_by_offset(inter_x - actions.w3c_actions.pointer_inputs[0].x,
                               inter_y - actions.w3c_actions.pointer_inputs[0].y)
        actions.pause(random.uniform(0.01, 0.05))

    actions.move_to_element(target_element).perform()
    random_delay(0.2, 0.4)

def gradual_scroll(driver, total_scrolls=5, max_scroll_px=400):
    """Scrolls down the page gradually in random increments."""
    for _ in range(total_scrolls):
        scroll_amount = random.randint(100, max_scroll_px)
        driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        random_delay(0.1, 0.3)

def fast_scroll(driver):
    """Fast scrolling - single scroll to bottom for optimized performance."""
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    random_delay(0.2, 0.5)  # Minimal delay

def pass_accepter(driver):
    """Pass the cookie consent button with multiple fallback strategies."""
    consent_selectors = [
        # Primary selector
        (By.ID, "didomi-notice-agree-button"),
        # Common alternative selectors for cookie consent
        (By.XPATH, "//button[contains(text(), 'Accepter')]"),
        (By.XPATH, "//button[contains(text(), 'Accept')]"),
        (By.XPATH, "//button[contains(text(), 'Tout accepter')]"),
        (By.XPATH, "//button[contains(text(), 'Fermer')]"),
        (By.CLASS_NAME, "didomi-notice-agree-button"),
        (By.CSS_SELECTOR, "[data-role='acceptAll']"),
        (By.CSS_SELECTOR, "button[id*='accept']"),
        (By.CSS_SELECTOR, "button[class*='accept']"),
        (By.CSS_SELECTOR, "button[class*='consent']"),
        # Generic close/accept buttons
        (By.XPATH, "//button[@role='button' and contains(., 'Accept')]"),
        (By.XPATH, "//div[@role='button' and contains(., 'Accept')]"),
    ]
    
    for i, (by_method, selector) in enumerate(consent_selectors):
        try:
            # Shorter wait time for each attempt
            wait = WebDriverWait(driver, 3)
            consent_button = wait.until(EC.element_to_be_clickable((by_method, selector)))
            consent_button.click()
            print(f"✅ Clicked cookie consent button (method {i+1}: {selector})")
            return True
        except Exception:
            continue  # Try next selector
    
    # If no button found, check if we're already past the consent screen
    try:
        # Look for main page elements to see if consent was already handled
        wait = WebDriverWait(driver, 2)
        main_content = wait.until(EC.presence_of_element_located((By.TAG_NAME, "main")))
        print("ℹ️  No cookie consent button found - likely already accepted or not present")
        return True
    except Exception:
        print("⚠️  Cookie consent handling failed - continuing anyway")
        return False

def pass_accepter_fast(driver, max_wait=1):
    """Fast cookie consent handler with minimal wait time - optimized for speed."""
    consent_selectors = [
        # Primary selectors only (most common)
        (By.ID, "didomi-notice-agree-button"),
        (By.XPATH, "//button[contains(text(), 'Accepter')]"),
        (By.XPATH, "//button[contains(text(), 'Accept')]"),
        (By.XPATH, "//button[contains(text(), 'Tout accepter')]"),
        (By.CLASS_NAME, "didomi-notice-agree-button"),
    ]
    
    for i, (by_method, selector) in enumerate(consent_selectors):
        try:
            # Very short wait time for each attempt
            wait = WebDriverWait(driver, max_wait)
            consent_button = wait.until(EC.element_to_be_clickable((by_method, selector)))
            consent_button.click()
            print(f"✅ Fast cookie consent clicked (method {i+1})")
            return True
        except Exception:
            continue  # Try next selector quickly
    
    # Quick check if we're already past consent (no long wait)
    try:
        driver.find_element(By.TAG_NAME, "main")
        print("ℹ️  No cookie consent needed - already accepted or not present")
        return True
    except Exception:
        print("⚠️  Fast cookie consent failed - continuing anyway")
        return False

def debug_page_elements(driver, search_terms=["accept", "consent", "cookie", "fermer", "accepter"]):
    """Debug function to find cookie consent elements on the page"""
    try:
        print("🔍 Debugging page elements for cookie consent...")
        
        # Search for buttons with relevant text
        for term in search_terms:
            try:
                elements = driver.find_elements(By.XPATH, f"//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{term.lower()}')]")
                for elem in elements:
                    print(f"   Found button with '{term}': {elem.text[:50]}... (ID: {elem.get_attribute('id')}, Class: {elem.get_attribute('class')})")
            except:
                continue
        
        # Search for divs with relevant text
        for term in search_terms:
            try:
                elements = driver.find_elements(By.XPATH, f"//div[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{term.lower()}')]")
                for elem in elements[:3]:  # Limit to first 3
                    print(f"   Found div with '{term}': {elem.text[:50]}... (ID: {elem.get_attribute('id')}, Class: {elem.get_attribute('class')})")
            except:
                continue
                
    except Exception as e:
        print(f"   Debug failed: {e}")

def cleanup_chrome_processes():
    """
    Windows-specific cleanup for Chrome processes
    Helps prevent the WinError 6 issue
    """
    import platform
    if platform.system() == "Windows":
        try:
            import subprocess
            import os
            # Kill any remaining chrome processes silently
            subprocess.run("taskkill /f /im chrome.exe >nul 2>&1", shell=True, check=False)
            subprocess.run("taskkill /f /im chromedriver.exe >nul 2>&1", shell=True, check=False)
        except:
            pass  # Ignore any errors during cleanup

def cleanup_worker_directories():
    """
    Clean up temporary worker directories created for chromedriver isolation
    """
    try:
        temp_root = tempfile.gettempdir()
        for item in os.listdir(temp_root):
            if item.startswith(('chromedriver_worker_', 'uc_worker_')):
                worker_dir = os.path.join(temp_root, item)
                try:
                    if os.path.isdir(worker_dir):
                        shutil.rmtree(worker_dir, ignore_errors=True)
                except:
                    pass  # Ignore cleanup errors
    except:
        pass  # Ignore any errors during cleanup