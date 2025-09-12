"""
Cookie refresh utility for Indeed API authentication
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def refresh_indeed_cookies():
    """
    Refresh Indeed cookies by opening a browser session
    Returns updated cookie string
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print("🔄 Refreshing Indeed cookies...")
        
        # Go to Indeed resume search
        driver.get("https://resumes.indeed.com/")
        time.sleep(3)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Get all cookies
        cookies = driver.get_cookies()
        
        # Build cookie string
        cookie_parts = []
        for cookie in cookies:
            cookie_parts.append(f"{cookie['name']}={cookie['value']}")
        
        cookie_string = "; ".join(cookie_parts)
        
        print("✅ Cookies refreshed successfully")
        return cookie_string
        
    except Exception as e:
        print(f"❌ Error refreshing cookies: {e}")
        return None
    finally:
        driver.quit()

def get_fresh_headers():
    """
    Get fresh headers with updated cookies
    """
    fresh_cookies = refresh_indeed_cookies()
    
    if not fresh_cookies:
        print("⚠️  Using fallback cookies")
        return None
    
    # Return updated headers
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Referer': 'https://resumes.indeed.com/',
        'content-type': 'application/json',
        'indeed-api-key': '0f2b0de1b8ff96890172eeeba0816aaab662605e3efebbc0450745798c4b35ae',
        'indeed-ctk': '1itk4s1n0gmv5800',
        'indeed-client-sub-app': 'rezemp-discovery',
        'indeed-client-sub-app-component': './Root',
        'Origin': 'https://resumes.indeed.com',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Cookie': fresh_cookies,
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'Sec-GPC': '1',
        'Priority': 'u=4',
        'TE': 'trailers'
    }

if __name__ == "__main__":
    # Test cookie refresh
    headers = get_fresh_headers()
    if headers:
        print("✅ Fresh headers obtained")
        print(f"Cookie length: {len(headers['Cookie'])} characters")
    else:
        print("❌ Failed to get fresh headers")