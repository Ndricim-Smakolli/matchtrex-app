"""
Header randomization utility for avoiding detection
"""

import random
import time

def get_random_user_agent():
    """Get a random realistic user agent"""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36"
    ]
    return random.choice(user_agents)

def get_random_viewport():
    """Get a random viewport size"""
    viewports = [
        (1920, 1080),
        (1366, 768),
        (1536, 864),
        (1440, 900),
        (1280, 720),
        (1600, 900),
        (1920, 1200),
        (2560, 1440),
        (1680, 1050),
        (1280, 800)
    ]
    return random.choice(viewports)

def get_random_chrome_version():
    """Get a random Chrome version"""
    versions = [
        "120.0.6099.109",
        "119.0.6045.160",
        "121.0.6167.85",
        "118.0.5993.117",
        "120.0.6099.216",
        "119.0.6045.199",
        "121.0.6167.139"
    ]
    return random.choice(versions)

def get_random_accept_language():
    """Get a random accept language"""
    languages = [
        "en-US,en;q=0.9",
        "en-GB,en;q=0.9",
        "en-US,en;q=0.9,de;q=0.8",
        "en-GB,en-US;q=0.9,en;q=0.8",
        "de-DE,de;q=0.9,en;q=0.8",
        "en-US,en;q=0.9,fr;q=0.8",
        "en-US,en;q=0.9,es;q=0.8"
    ]
    return random.choice(languages)

def get_random_sec_ch_ua():
    """Get a random sec-ch-ua header"""
    sec_ch_uas = [
        '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        '"Not_A Brand";v="8", "Chromium";v="119", "Google Chrome";v="119"',
        '"Not_A Brand";v="8", "Chromium";v="121", "Google Chrome";v="121"',
        '"Not A(Brand";v="99", "Google Chrome";v="120", "Chromium";v="120"',
        '"Not A(Brand";v="99", "Google Chrome";v="119", "Chromium";v="119"'
    ]
    return random.choice(sec_ch_uas)

def get_random_timing():
    """Get random timing values"""
    return {
        'page_load_delay': random.uniform(0.5, 2.0),
        'content_wait_delay': random.uniform(0.3, 1.5),
        'between_requests_delay': random.uniform(1.0, 3.0)
    }

def get_randomized_chrome_options():
    """Get randomized Chrome options"""
    from selenium.webdriver.chrome.options import Options
    
    chrome_options = Options()
    
    # Random user agent
    user_agent = get_random_user_agent()
    chrome_options.add_argument(f"--user-agent={user_agent}")
    
    # Random viewport
    width, height = get_random_viewport()
    chrome_options.add_argument(f"--window-size={width},{height}")
    
    # Headless mode
    chrome_options.add_argument("--headless=new")
    
    # Basic arguments
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Performance optimizations
    chrome_options.add_argument("--disable-images")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-features=TranslateUI")
    chrome_options.add_argument("--disable-default-apps")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--no-default-browser-check")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--single-process")
    
    # Memory management
    chrome_options.add_argument("--memory-pressure-off")
    chrome_options.add_argument("--max_old_space_size=4096")
    
    # Remove automation indicators
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Additional stability options
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    chrome_options.add_argument("--disable-ipc-flooding-protection")
    
    # Random accept language
    accept_lang = get_random_accept_language()
    chrome_options.add_argument(f"--lang={accept_lang.split(',')[0]}")
    
    # Random sec-ch-ua
    sec_ch_ua = get_random_sec_ch_ua()
    chrome_options.add_argument(f"--user-agent-metadata={sec_ch_ua}")
    
    return chrome_options

def randomize_browser_fingerprint(driver):
    """Randomize browser fingerprint after creation"""
    user_agent = get_random_user_agent()
    accept_lang = get_random_accept_language()
    
    # Inject randomized properties
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": user_agent,
        "acceptLanguage": accept_lang,
        "platform": "Win32"
    })
    
    # Randomize navigator properties
    driver.execute_script(f"""
        Object.defineProperty(navigator, 'userAgent', {{
            get: () => '{user_agent}'
        }});
        
        Object.defineProperty(navigator, 'language', {{
            get: () => '{accept_lang.split(',')[0]}'
        }});
        
        Object.defineProperty(navigator, 'languages', {{
            get: () => {[f'"{lang.split(";")[0]}"' for lang in accept_lang.split(',')]}
        }});
        
        Object.defineProperty(navigator, 'hardwareConcurrency', {{
            get: () => {random.randint(4, 16)}
        }});
        
        Object.defineProperty(navigator, 'deviceMemory', {{
            get: () => {random.choice([4, 8, 16, 32])}
        }});
        
        Object.defineProperty(screen, 'width', {{
            get: () => {random.choice([1920, 1366, 1536, 1440, 1280, 1600, 2560])}
        }});
        
        Object.defineProperty(screen, 'height', {{
            get: () => {random.choice([1080, 768, 864, 900, 720, 1200, 1440])}
        }});
        
        Object.defineProperty(navigator, 'platform', {{
            get: () => '{random.choice(["Win32", "MacIntel", "Linux x86_64"])}'
        }});
    """)

def add_random_delays():
    """Add random delays to mimic human behavior"""
    timing = get_random_timing()
    
    # Random delay between actions
    delay = random.uniform(0.1, 0.5)
    time.sleep(delay)
    
    return timing

if __name__ == "__main__":
    # Test randomization
    print("Testing header randomization...")
    
    for i in range(5):
        print(f"\nTest {i+1}:")
        print(f"User Agent: {get_random_user_agent()}")
        print(f"Viewport: {get_random_viewport()}")
        print(f"Language: {get_random_accept_language()}")
        print(f"Timing: {get_random_timing()}")