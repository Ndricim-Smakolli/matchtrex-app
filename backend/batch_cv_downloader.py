import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from twocaptcha import TwoCaptcha
import time
import re
import json
import os
import shutil
from datetime import datetime

def get_indeed_headers():
    """Get headers from main.py with authentication"""
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
        'x-datadog-origin': 'rum',
        'x-datadog-parent-id': '2930520531491405788',
        'x-datadog-sampling-priority': '0',
        'x-datadog-trace-id': '914046465001288166',
        'Origin': 'https://resumes.indeed.com',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Cookie': 'CTK=1itk4s1n0gmv5800; RF=wKGgxUwMHWUX5YFUwWOHJWllKOBtkHCypm6q6XELpbojtsnO9ZC_yE8zLeFvxzKc; OptanonConsent=isGpcEnabled=1^&datestamp=Mon+Jul+14+2025+09%3A04%3A20+GMT%2B0200+(Central+European+Summer+Time)^&version=202409.2.0^&browserGpcFlag=1^&isIABGlobal=false^&hosts=^&consentId=29761a2a-8bb1-4d3b-aed3-6cd19eaa08a9^&interactionCount=2^&isAnonUser=1^&landingPath=NotLandingPage^&groups=C0001%3A1%2CC0002%3A0%2CC0003%3A0%2CC0004%3A0%2CC0007%3A0^&AwaitingReconsent=false^&intType=2^&geolocation=%3B; indeed_rcc=LOCALE:CTK; cf_clearance=8Qz65PJtRDuR1lY5.nqjaBivTBgDhJpHfboNtu89KgE-1752475997-1.2.1.1-1bJdhTq5OiBglLE6uHJ0gPoLwhba7unZ43ajqkqawVhXVV1oc6w7En5btkeojOJuGw.IoAqvBIn4hKFgZ7PvT57TfDes0Pcxpi04ICYcefQ2uE_goi5JohYz.XVLo0djATpqhkvu3Ieg6oeroONYD2Ci90y.yKdRmgOg_tFLHJFuS5JD9M_jzbhsauatiEkdwy0b4b7yPXFBtT0Tredw4HmbxaCzq3b9_HMci4KL5JQ; IRF=2OjkVS608cRBJyDN80nHtHDzwzzxoxWIV0Ae_fa5Cq-OutJyB0t_LQ==; OptanonAlertBoxClosed=2025-06-13T09:59:43.706Z; CO=DE; optimizelySession=1751009392977; PPID=eyJraWQiOiI3OGFjNzFmNC04MDhjLTRjYTItOTI4NC0xYmRjNzIzMDliYzIiLCJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiJ9.eyJzdWIiOiJhYmEyZmUwNzUyNDZlZTRhIiwibGFzdF9hdXRoX3RpbWUiOjE3NTEwMDk3NzQxOTEsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJhdXRoIjoiZ29vZ2xlIiwiY3JlYXRlZCI6MTc0NTY3NDE4NjAwMCwiaXNzIjoiaHR0cHM6Ly9zZWN1cmUuaW5kZWVkLmNvbSIsImxhc3RfYXV0aF9sZXZlbCI6IlNUUk9ORyIsImxvZ190cyI6MTc1MTAwOTc3NDE5MSwiYXJiX2FjcHQiOmZhbHNlLCJhdWQiOiJjMWFiOGYwNGYiLCJyZW1fbWUiOnRydWUsImV4cCI6MTc1MjQ3Nzc3OCwiaWF0IjoxNzUyNDc1OTc4LCJlbWFpbCI6ImxvcmVuekBiZXlvbmRsZXZlcmFnZS5jb20ifQ.ahVONSblwrh1iUWRxbn9HEfqydzxkbOq302jK6B5PyxRZ_Dcii19hz3h0O16JRNRxyOKCzRcnH6KHhM476yd-Q; SOCK="ZaFLiaYTrg8KhpCkHQcI7ylG41k="; SHOE="6jHL9VNDfzRqUfAyKY8J-SeimanGhqPrx2q5gcRnOvOlidUf-C-7rkxJzUQNrGIlCvsaw7uTcHc5yaHRcp1anmFG4Chz9-7XwYshFq2ODQucVmOtrq9zaEANXe89h30rigDb9VfvLA928_FoTkK7egPO"; PCA=30fd7ee57925c18d; ADOC=9366375769107198; accountSwitcherPopupDismissed=true; sp=ad1ce092-29c9-4573-9959-2d84179948ef; CSRF=455404a5d36523c8dae321776edd3a82; _cfuvid=Ww3hZpbHcX47hRwgim.RoE0VLZlRjwO8cBA0ByxNuSg-1752475980326-0.0.1.1-604800000; ENC_CSRF=7yw33pQePPsFgTKDIZWhHZkRVy0bJ0jM; LOCALE=en_DE; _cfuvid=bj8Enb2uHT6qV9sDsZsKPbHWW14InxmsWR8vqvcy3Co-1752475978267-0.0.1.1-604800000; __cf_bm=9w4cJcH_AeUMVE6Pw4KltR2ax0G0v4N6i0D9sf_tDK4-1752475978-1.0.1.1-2cCyaxQo6Job2d3PLnpA_q4p9UIwSqic6qcGVCgVRn3iFQv8_HffGyXmd7PZ3k9VlPe1eUvoYfk4LXt3ugu8g06YuECA4Sd0wdNbgPE8rkQ; __cf_bm=tajrcCHwt8kDROdY0hpGJqpSuH1y5YOdJSm8Z87ZkE0-1752476660-1.0.1.1-66_Kwxt9c9V423TDc1WPIftX8qGHKB0qxOHZrfWba9TIxv1hnFsRIh50IgAc3NB.tA9cKEXpNX0YIjw5pFAkOY7Om6tQh_OLDANPxq4Iz4k; _dd_s=rum=2^&id=2f5b3be1-d20b-42e5-800b-9a8d84637b89^&created=1752476015025^&expire=1752477559533; SURF=4utXnbDO2qkDKv62rlqN5oKKTa9Ysolo',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'Sec-GPC': '1',
        'Priority': 'u=4',
        'TE': 'trailers'
    }

def read_urls_from_file(filename):
    """Read URLs from the filtered contacts file"""
    urls = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and line.startswith('https://resumes.indeed.com/resume/'):
                    urls.append(line)
        print(f"Found {len(urls)} URLs to process")
        return urls
    except FileNotFoundError:
        print(f"File {filename} not found")
        return []

def setup_driver_with_cookies():
    """Setup Chrome driver with Indeed cookies for authenticated session"""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    # Inject Turnstile interceptor
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            window.turnstileParams = null;
            console.log('Turnstile interceptor injected');
            
            const i = setInterval(() => {
                if (window.turnstile) {
                    clearInterval(i);
                    console.log('Turnstile detected, intercepting render...');
                    
                    const originalRender = window.turnstile.render;
                    window.turnstile.render = (a, b) => {
                        console.log('Turnstile render intercepted!');
                        
                        window.turnstileParams = {
                            sitekey: b.sitekey,
                            cData: b.cData,
                            action: b.action,
                            chlPageData: b.chlPageData
                        };
                        
                        window.turnstileCallback = b.callback;
                        console.log('Stored turnstile params:', window.turnstileParams);
                        return 'intercepted';
                    };
                }
            }, 50);
        '''
    })
    
    # Navigate to Indeed and set cookies
    driver.get("https://resumes.indeed.com/")
    
    # Extract cookies from the headers and set them
    cookie_string = get_indeed_headers()['Cookie']
    cookies = {}
    for cookie in cookie_string.split('; '):
        if '=' in cookie:
            key, value = cookie.split('=', 1)
            cookies[key] = value
    
    # Set cookies in the driver
    for name, value in cookies.items():
        try:
            driver.add_cookie({
                'name': name,
                'value': value,
                'domain': '.indeed.com'
            })
        except Exception as e:
            print(f"Could not set cookie {name}: {e}")
    
    return driver

def solve_turnstile_challenge(driver, url):
    """Solve Turnstile challenge if present"""
    solver = TwoCaptcha("22e969001c9ae2824614794f69230e68")
    
    if "Just a moment..." in driver.title or "cf-turnstile-response" in driver.page_source:
        print("Cloudflare challenge detected!")
        
        try:
            turnstile_params = driver.execute_script("return window.turnstileParams;")
            if turnstile_params and turnstile_params.get('sitekey'):
                print("Solving Turnstile with intercepted parameters...")
                
                payload = {
                    'sitekey': turnstile_params['sitekey'],
                    'url': url
                }
                
                if turnstile_params.get('cData'):
                    payload['data'] = turnstile_params['cData']
                if turnstile_params.get('action'):
                    payload['action'] = turnstile_params['action']
                if turnstile_params.get('chlPageData'):
                    payload['pagedata'] = turnstile_params['chlPageData']
                
                result = solver.turnstile(**payload)
                
                # Inject solution
                driver.execute_script(f"""
                    if (window.turnstileCallback) {{
                        window.turnstileCallback('{result['code']}');
                        console.log('Solution injected via callback');
                    }} else {{
                        var input = document.querySelector('[name="cf-turnstile-response"]');
                        if (input) {{
                            input.value = '{result['code']}';
                            console.log('Solution injected via input');
                        }}
                    }}
                """)
                
                time.sleep(5)
                print("Turnstile solved!")
                return True
                
        except Exception as e:
            print(f"Error solving Turnstile: {e}")
            return False
    
    return True

def setup_temp_cvs_folder():
    """Setup temp_CVs folder, clearing it if it exists"""
    folder_path = "temp_CVs"
    
    if os.path.exists(folder_path):
        print(f"Clearing existing {folder_path} folder...")
        shutil.rmtree(folder_path)
    
    os.makedirs(folder_path)
    print(f"Created {folder_path} folder")
    return folder_path


def download_cv_pages():
    """Main function to download all CV pages"""
    print("Starting batch CV download with authenticated session...")
    
    # Setup temp_CVs folder
    temp_folder = setup_temp_cvs_folder()
    
    # Read URLs
    urls = read_urls_from_file("filtered_contacts_mistral_ai_17_07_2025_10_59_49.txt")
    if not urls:
        print("No URLs found to process")
        return
    
    # Setup driver with cookies
    driver = setup_driver_with_cookies()
    
    try:
        successful = 0
        failed = 0
        
        for i, url in enumerate(urls, 1):
            print(f"\\nProcessing CV {i}/{len(urls)}: {url}")
            
            try:
                # Navigate to CV page
                driver.get(url)
                time.sleep(5)
                
                # Solve Turnstile if needed
                if not solve_turnstile_challenge(driver, url):
                    print(f"Failed to solve Turnstile for {url}")
                    failed += 1
                    continue
                
                # Wait for page to load
                time.sleep(5)
                
                # Check if we're still on a login/challenge page
                if "login" in driver.current_url.lower() or "challenge" in driver.current_url.lower():
                    print(f"Still on login/challenge page for {url}")
                    failed += 1
                    continue
                
                # Get page content
                html_content = driver.page_source
                
                # Extract resume ID from URL
                resume_id = url.split('/')[-1]
                
                # Save full HTML content to temp_CVs folder
                filename = f"cv_{resume_id}.html"
                file_path = os.path.join(temp_folder, filename)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                print(f"✓ Saved CV: {filename}")
                successful += 1
                
                # Small delay between requests
                time.sleep(2)
                
            except Exception as e:
                print(f"✗ Error downloading {url}: {e}")
                failed += 1
        
        print(f"\\n=== Batch Download Complete ===")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Total: {len(urls)}")
        print(f"CV files saved in: {temp_folder}")
        
    finally:
        input("Press Enter to close browser...")
        driver.quit()

if __name__ == "__main__":
    download_cv_pages()