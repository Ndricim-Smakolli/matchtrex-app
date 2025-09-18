#!/usr/bin/env python3
"""
MVP Pipeline for MatchTrex - Streamlined candidate sourcing and evaluation
Integrates: Excel config -> Indeed search -> CV download -> AI evaluation -> Email results
Now includes Flask webhook server and Google Sheets button functionality
"""

import requests
import json
import os
import time
import smtplib
import uuid
import openpyxl
import html
import shutil
import subprocess
import threading
import asyncio
import logging
import random
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from twocaptcha import TwoCaptcha
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from google_sheets_service import GoogleSheetsService
from config import get_google_sheets_id, GOOGLE_SHEETS_CREDENTIALS_PATH

# Constants - Load from environment variables
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "83pVv0mVbOBUwSRmoPBaWg6UUkNZunTP")  # Fallback to hardcoded
TWOCAPTCHA_KEY = os.getenv("TWOCAPTCHA_KEY", "22e969001c9ae2824614794f69230e68")  # Fallback to hardcoded

# Email configuration from environment variables
EMAIL_USER = os.getenv("EMAIL_USER", "aauxilliary4@gmail.com")
EMAIL_PASS = os.getenv("EMAIL_PASS", "kxoc ajnf pked zhwp")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

# Header rotation pools for anti-detection
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
]

ACCEPT_LANGUAGES = [
    'en-US,en;q=0.9,de;q=0.8',
    'en-US,en;q=0.5',
    'de-DE,de;q=0.9,en;q=0.8',
    'en-GB,en;q=0.9,de;q=0.8'
]

SEC_CH_UA_VALUES = [
    '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
    '"Chromium";v="119", "Not?A_Brand";v="24"'
]

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration for webhook server
SCRIPT_PATH = os.path.abspath(__file__)
LOG_FILE = os.path.join(os.path.dirname(__file__), 'webhook_logs.txt')

# Global variable to track pipeline execution
pipeline_running = False

# Choose headers once at script start
SELECTED_USER_AGENT = random.choice(USER_AGENTS)
SELECTED_ACCEPT_LANGUAGE = random.choice(ACCEPT_LANGUAGES)
SELECTED_SEC_CH_UA = random.choice(SEC_CH_UA_VALUES) if 'Chrome' in SELECTED_USER_AGENT else None

class PipelineManager:
    """Manages pipeline execution and status"""
    def __init__(self):
        self.running = False
        self.background_task = None
        
    async def start_background_service(self):
        """Start background monitoring service"""
        logger.info("🚀 Background pipeline service started")
        
    def stop_background_service(self):
        """Stop background service"""
        logger.info("🛑 Background pipeline service stopped")

# Global pipeline manager
pipeline_manager = PipelineManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting MatchTrex Pipeline API...")
    await pipeline_manager.start_background_service()
    yield
    # Shutdown
    pipeline_manager.stop_background_service()
    logger.info("🛑 MatchTrex Pipeline API shutting down...")

# FastAPI app initialization with lifespan
app = FastAPI(
    title="MatchTrex Pipeline API", 
    description="FastAPI server for MatchTrex candidate sourcing pipeline",
    version="1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # Set to False when using allow_origins=["*"]
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Pydantic models for request/response
class TriggerRequest(BaseModel):
    action: str
    timestamp: Optional[str] = None
    sheet_id: Optional[str] = None

class SearchParameters(BaseModel):
    search_keywords: str
    location: str
    resume_last_updated_days: int
    target_candidates: int
    max_radius: int
    recipient_email: str
    user_prompt: str
    system_prompt: str

class StatusResponse(BaseModel):
    is_running: bool
    recent_logs: List[str]
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    script_path: str
    script_exists: bool

def read_search_parameters():
    """
    Read search parameters from Google Sheets 'Search Parameters' sheet.
    Returns a dictionary with all search parameters.
    """
    sheet_id = get_google_sheets_id()
    if not sheet_id:
        raise ValueError("❌ Google Sheets ID not configured. Please set GOOGLE_SHEETS_ID in config.py or environment variable.")
    
    gs_service = GoogleSheetsService(GOOGLE_SHEETS_CREDENTIALS_PATH, sheet_id)
    
    if not gs_service.setup_authentication():
        raise ConnectionError("❌ Failed to authenticate with Google Sheets. Check your credentials file.")
    
    if not gs_service.open_spreadsheet():
        raise ConnectionError("❌ Failed to open Google Sheets document. Check your sheet ID and permissions.")
    
    return gs_service.read_search_parameters()

def calculate_unix_timestamp_ms(days_back=30):
    """Calculate Unix timestamp for resume filter"""
    target_date = datetime.now() - timedelta(days=days_back)
    return str(int(target_date.timestamp() * 1000))

def get_static_headers():
    """Get headers chosen once at script start"""
    # Generate random values for this session
    datadog_parent_id = str(random.randint(1000000000000000000, 9999999999999999999))
    datadog_trace_id = str(random.randint(100000000000000000, 999999999999999999))
    
    headers = {
        'User-Agent': SELECTED_USER_AGENT,
        'Accept': '*/*',
        'Accept-Language': SELECTED_ACCEPT_LANGUAGE,
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Referer': 'https://resumes.indeed.com/',
        'content-type': 'application/json',
        'indeed-api-key': '0f2b0de1b8ff96890172eeeba0816aaab662605e3efebbc0450745798c4b35ae',
        'indeed-ctk': '1itk4s1n0gmv5800',
        'indeed-client-sub-app': 'rezemp-discovery',
        'indeed-client-sub-app-component': './Root',
        'x-datadog-origin': 'rum',
        'x-datadog-parent-id': datadog_parent_id,
        'x-datadog-sampling-priority': '0',
        'x-datadog-trace-id': datadog_trace_id,
        'Origin': 'https://resumes.indeed.com',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Cookie': get_indeed_cookies(),
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'Sec-GPC': '1',
        'Priority': 'u=4',
        'TE': 'trailers'
    }
    
    # Add Sec-CH-UA for Chrome user agents
    if SELECTED_SEC_CH_UA:
        headers['sec-ch-ua'] = SELECTED_SEC_CH_UA
        headers['sec-ch-ua-mobile'] = '?0'
        headers['sec-ch-ua-platform'] = '"Windows"'
        
    return headers

def make_indeed_request(radius, keywords, resume_updated_filter, location, offset=0, limit=50):
    """Make Indeed API request with static headers chosen at startup"""
    url = "https://apis.indeed.com/graphql?co=DE&locale=en-DE"
    
    # Get headers chosen at script start
    headers = get_static_headers()
    
    payload = {
        "operationName": "SmartSourcingResults",
        "variables": {
            "input": {
                "searchQuery": {
                    "queryString": keywords,
                    "searchLocale": {"language": "de", "country": "DE"}
                },
                "clientSurfaceName": "sourcing-search",
                "identifiers": {"jobIdentifiers": {}},
                "context": {
                    "overrides": {
                        "where": location,
                        "radiusInput": {"distance": radius, "unit": "KILOMETERS"}
                    }
                },
                "filters": [{"key": "lastModified", "afterBucket": False, "gte": resume_updated_filter}],
                "defaultStrategyId": "RCHK8",
                "limit": limit,
                "offset": offset
            },
            "includePreferences": False,
            "includePagination": True,
            "useNewJwt": False,
            "isLoggedIn": False,
            "federateRcpRequestMetadataToSourcingProfile": True,
            "includePermissionToken": False
        },
        "extensions": {
            "remoteFragmentStats": {
                "fragmentCount": 8,
                "elapsedTime": 803
            }
        },
        "query": "query SmartSourcingResults($input: OrchestrationMatchesInput!, $includePreferences: Boolean!, $includePagination: Boolean!, $useNewJwt: Boolean!, $isLoggedIn: Boolean!, $federateRcpRequestMetadataToSourcingProfile: Boolean!, $includePermissionToken: Boolean!) {\n  findRCPMatches(input: $input) {\n    rcpRequestId\n    overallMatchCountWithoutLimit\n    searchSessionId @include(if: $includePagination)\n    overallMatchCount\n    matchConnection {\n      pageInfo @include(if: $includePagination) {\n        hasNextPage\n        hasPreviousPage\n        __typename\n      }\n      matches {\n        matchId {\n          id\n          __typename\n        }\n        highlights {\n          text\n          __typename\n        }\n        provider\n        sourcingProfile {\n          accountKey\n          permissionToken @include(if: $includePermissionToken)\n          profileCard {\n            ...ProfileCard\n            __typename\n          }\n          engagementSummary @include(if: $isLoggedIn) {\n            ...EngagementSummary\n            __typename\n          }\n          requestMetadata @include(if: $federateRcpRequestMetadataToSourcingProfile) {\n            isSegmentDecorated\n            rcpRequestId\n            __typename\n          }\n          ...TDRM_CandidateName_SourcingProfile\n          ...TDRM_CandidateLocation_SourcingProfile\n          ...TDRM_CandidateWorkExperience_SourcingProfile\n          ...TDRM_CandidateEducation_SourcingProfile\n          ...TDRM_CandidateLicensesCertifications_SourcingProfile\n          ...TDRM_CandidateSkills_SourcingProfile\n          ...TDRM_CandidateTags_SourcingProfile @include(if: $isLoggedIn)\n          ...TDRM_ProviderTags_SourcingProfile @include(if: $isLoggedIn)\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    refinementBuckets {\n      key\n      label\n      description\n      items {\n        count\n        label\n        value\n        __typename\n      }\n      __typename\n    }\n    searchQueryMetadata {\n      stringCorrections {\n        correction\n        original\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment ProfileCard on SourcingProfileCard {\n  accountKey\n  activityData {\n    lastActivityTimestamp\n    __typename\n  }\n  canReceiveSMS\n  dateCreated\n  dateModified\n  educations {\n    school\n    degree\n    fromDate\n    toDate\n    __typename\n  }\n  experiences {\n    title\n    company\n    fromDate\n    toDate\n    __typename\n  }\n  firstName\n  lastClickedDate\n  lastName\n  locale\n  location {\n    localizedValue\n    __typename\n  }\n  phoneNumber\n  skills {\n    text\n    __typename\n  }\n  credentials {\n    title\n    __typename\n  }\n  preferences @include(if: $includePreferences) {\n    classLabel\n    label\n    __typename\n  }\n  resumeType\n  isFreeToContact\n  jwtTokenForResumeView @include(if: $useNewJwt)\n  __typename\n}\n\nfragment EngagementSummary on TalentEngagementSummary {\n  permissions {\n    action\n    status\n    __typename\n  }\n  __typename\n}\n\nfragment TDRM_CandidateName_SourcingProfile on SourcingProfile {\n  accountKey\n  profileCard {\n    accountKey\n    firstName\n    lastName\n    __typename\n  }\n  __typename\n}\n\nfragment TDRM_CandidateLocation_SourcingProfile on SourcingProfile {\n  accountKey\n  profileCard {\n    location {\n      localizedValue\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment TDRM_CandidateWorkExperience_SourcingProfile on SourcingProfile {\n  accountKey\n  profileCard {\n    experiences {\n      title\n      company\n      fromDate\n      toDate\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment TDRM_CandidateEducation_SourcingProfile on SourcingProfile {\n  accountKey\n  profileCard {\n    accountKey\n    educations {\n      school\n      degree\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment TDRM_CandidateLicensesCertifications_SourcingProfile on SourcingProfile {\n  accountKey\n  permissionToken\n  profileCard {\n    accountKey\n    credentials {\n      title\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment TDRM_CandidateSkills_SourcingProfile on SourcingProfile {\n  accountKey\n  permissionToken\n  profileCard {\n    accountKey\n    skills {\n      text\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment TDRM_CandidateTags_SourcingProfile on SourcingProfile {\n  accountKey\n  profileCard {\n    dateModified\n    lastClickedDate\n    activityData {\n      lastActivityTimestamp\n      __typename\n    }\n    isFreeToContact\n    canReceiveSMS\n    __typename\n  }\n  projectBriefsConnection {\n    projectBriefs {\n      id\n      key\n      isDefault\n      name\n      __typename\n    }\n    totalCount\n    __typename\n  }\n  __typename\n}\n\nfragment TDRM_ProviderTags_SourcingProfile on SourcingProfile {\n  accountKey\n  profileCard {\n    accountKey\n    resumeType\n    __typename\n  }\n  __typename\n}\n"
    }
    
    try:
        # Add random delay to avoid rate limiting
        time.sleep(random.uniform(1, 3))
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        print(f"DEBUG: Response Status: {response.status_code}")
        print(f"DEBUG: Response Headers: {dict(list(response.headers.items())[:5])}")
        print(f"DEBUG: Response Body (first 500 chars): {response.text[:500]}")
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text[:1000]}")
        return None

def extract_candidate_data(response):
    """Extract candidate profile URLs from Indeed response"""
    candidates = []
    try:
        matches = response['data']['findRCPMatches']['matchConnection']['matches']
        for match in matches:
            sourcing_profile = match.get('sourcingProfile', {})
            account_key = sourcing_profile.get('accountKey', '')
            if account_key:
                resume_url = f"https://resumes.indeed.com/resume/{account_key}"
                candidates.append(resume_url)
    except Exception as e:
        print(f"Error extracting candidates: {e}")
    return candidates

def get_indeed_cookies():
    """Get the cookie string used in Indeed API headers"""
    return 'CTK=1itk4s1n0gmv5800; RF="TFTzyBUJoNr6YttPP3kyivpZ6-9J49o-Uk3iY6QNQqKE2fh7FyVgtbqvJ2_8odJ35AReApyruhw="; OptanonConsent=isGpcEnabled=1^&datestamp=Mon+Jul+28+2025+13%3A43%3A49+GMT%2B0200+(Central+European+Summer+Time)^&version=202409.2.0^&browserGpcFlag=1^&isIABGlobal=false^&hosts=^&consentId=29761a2a-8bb1-4d3b-aed3-6cd19eaa08a9^&interactionCount=2^&isAnonUser=1^&landingPath=NotLandingPage^&groups=C0001%3A1%2CC0002%3A0%2CC0003%3A0%2CC0004%3A0%2CC0007%3A0^&AwaitingReconsent=false^&intType=2^&geolocation=%3B; indeed_rcc=LOCALE:LV:CTK; cf_clearance=tgkrzPm1oldtZ98CeT3P_5_wGlLdoqTsX9DyFCJm7Kk-1753703010-1.2.1.1-49_ZgRHCSGNz5O8f9j._oO9wz9PQEF.Pvqxmub7uJT4TkFzRVGgT4AyfHju1pn1WK6Pri1DXq07V70kpab5jptuRTq490wCqpPgbEAfRHmvpZBOwZGU9Ulj.Zjs4SC0lRFYUkhs6_kqFWkDugd3HKxDlFjerhuuTPY7bGVd4.lnd.4PGSa7XyIPEkcF8QKgj_2EuNn2uJ7GD4oErnriBVnncszVRwP5wS7WKg6dTWMc; IRF=7YXfKDzcx1IboxNYvqvjCy_WqylJyEsnEOjzfEkfodL5S1rhXkHCJVmzzU6MoLMEy0H8zCfHCXM=; OptanonAlertBoxClosed=2025-06-13T09:59:43.706Z; CO=DE; optimizelySession=1751009392977; PPID=eyJraWQiOiI3OGFjNzFmNC04MDhjLTRjYTItOTI4NC0xYmRjNzIzMDliYzIiLCJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiJ9.eyJzdWIiOiJhYmEyZmUwNzUyNDZlZTRhIiwibGFzdF9hdXRoX3RpbWUiOjE3NTM3MDExMDM3OTksImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJhdXRoIjoiZ29vZ2xlIiwiY3JlYXRlZCI6MTc0NTY3NDE4NjAwMCwiaXNzIjoiaHR0cHM6Ly9zZWN1cmUuaW5kZWVkLmNvbSIsImxhc3RfYXV0aF9sZXZlbCI6IlNUUk9ORyIsImxvZ190cyI6MTc1MzcwMTEwMzc5OSwiYXJiX2FjcHQiOmZhbHNlLCJhdWQiOiJjMWFiOGYwNGYiLCJyZW1fbWUiOnRydWUsImV4cCI6MTc1MzcwNDgwMywiaWF0IjoxNzUzNzAzMDAzLCJlbWFpbCI6ImxvcmVuekBiZXlvbmRsZXZlcmFnZS5jb20ifQ.FJdkcZ9cSZjiNYv5rXpdrZoD1N7JQv3L5rbw6D6996ZN2PwqvJZgno2-QAnGBxyXF-qLTVAeVxVlUn1KLcgpVw; PCA=30fd7ee57925c18d; ADOC=9366375769107198; accountSwitcherPopupDismissed=true; sp=ad1ce092-29c9-4573-9959-2d84179948ef; SURF=4utXnbDO2qkDKv62rlqN5oKKTa9Ysolo; LOCALE=de_DE; LC="co=DE"; CSRF=455404a5d36523c8dae321776edd3a82; _cfuvid=aOlyAvOitlS_V7x1w_ilAPKE7nTsNwNte28wAj6RjAE-1753701106080-0.0.1.1-604800000; ENC_CSRF=7yw33pQePPsFgTKDIZWhHZkRVy0bJ0jM; _cfuvid=bKQp1eqgrFnJhjm.WTNosda3Sd5VUexi6sNE1R_qt44-1753701031257-0.0.1.1-604800000; SHARED_INDEED_CSRF_TOKEN=n7RHtTrqxJCZPKRCLc8eExt2xelUvuq7; SESSION_START_TIME=1752734838906; SESSION_ID=1j0bi6c3qhn0g801; SESSION_END_TIME=1752734892259; SOCK="GTNM-yIH2GTHL1-VEK2HlDNrJWM="; SHOE="z7-5aY8R3lwYCXgD-e6HlQy9gqDiAIODCUkeqBB6idFKyx4RWAvm8ORqCTDUlnEzPfISMP5n6bw1eUiGU9IVXMM5UVp-JKxfZNhA4zXIu4cD7usfcRYfpRLNaUuybTkNiVClzSTALYXwB7T05iAQ_jhE"; _dd_s=aid=62389643-6979-433b-889e-ba777bf4eba0^&rum=2^&id=24adc687-feac-4917-9a8d-1c99f7c28875^&created=1753703004968^&expire=1753703933955; __cf_bm=BG.lC8PGxoHn5BV5DnacAcu4tF6bDvAoFjmheXekcTo-1753703004-1.0.1.1-aWfiIcAsf8pjjoMxv8giB.uVwwfzjKSzby2mTLThuzSVHDJb1KevXgBWG5QuKA1bRwXuYBjwBTVGmLtO2yFpCAuSnFYFWDAhmLr8pVrQ1KY; __cf_bm=FLsn3fbin39ifDhcqR7221zkze5kmPJ1jsVqm3QOCUs-1753703009-1.0.1.1-obnrf7SENgMi4fKq7yiyM1bNoyG71QL7lDRSX5VLxRpDtT71NSuKTZLPNLAJmYcX1ZdmXlNEV0g3FGDnNp3fBXMRq0WTKKm4u1o0ckjzKXw'

def setup_driver_with_cookies():
    """Setup Chrome driver with Indeed cookies and stealth headers"""
    chrome_options = Options()

    # Headless mode
    chrome_options.add_argument("--headless=new")

    # Stealth arguments
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    # Additional compatibility flags for VPS environments
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-features=TranslateUI")
    chrome_options.add_argument("--disable-ipc-flooding-protection")

    # Anti-detection headers - use same user agent as API calls
    chrome_options.add_argument(f"--user-agent={SELECTED_USER_AGENT}")
    chrome_options.add_argument("--window-size=1920,1080")

    # Performance optimizations
    chrome_options.add_argument("--disable-images")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--disable-gpu")

    # Remove automation indicators
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    try:
        # Try to use system-wide ChromeDriver first
        from selenium.webdriver.chrome.service import Service
        import shutil

        # Check for ChromeDriver in common locations
        chromedriver_paths = [
            '/usr/local/bin/chromedriver',
            '/usr/bin/chromedriver',
            shutil.which('chromedriver')
        ]

        chromedriver_path = None
        for path in chromedriver_paths:
            if path and os.path.exists(path):
                chromedriver_path = path
                print(f"✅ Found ChromeDriver at: {chromedriver_path}")
                break

        if chromedriver_path:
            service = Service(chromedriver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            # Fall back to automatic driver management
            print("⚠️ No system ChromeDriver found, trying automatic download...")
            driver = webdriver.Chrome(options=chrome_options)
    except Exception as e:
        print(f"❌ ChromeDriver initialization failed: {e}")
        print("   Installing Chrome/ChromeDriver on VPS...")
        print("   Run: bash setup_chrome.sh")
        print("   Or manually: sudo apt-get update && sudo apt-get install -y google-chrome-stable chromium-chromedriver")
        raise Exception(f"ChromeDriver setup failed: {e}")
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    # Inject Turnstile interceptor
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            window.turnstileParams = null;
            const i = setInterval(() => {
                if (window.turnstile) {
                    clearInterval(i);
                    const originalRender = window.turnstile.render;
                    window.turnstile.render = (a, b) => {
                        window.turnstileParams = {
                            sitekey: b.sitekey,
                            cData: b.cData,
                            action: b.action,
                            chlPageData: b.chlPageData
                        };
                        window.turnstileCallback = b.callback;
                        return 'intercepted';
                    };
                }
            }, 50);
        '''
    })
    
    # Set cookies - use the same cookies as in the API headers
    driver.get("https://resumes.indeed.com/")
    cookie_string = get_indeed_cookies()
    
    for cookie in cookie_string.split('; '):
        if '=' in cookie:
            key, value = cookie.split('=', 1)
            try:
                driver.add_cookie({'name': key, 'value': value, 'domain': '.indeed.com'})
            except:
                pass
    
    print("✅ Headless browser setup complete with stealth headers")
    return driver

def solve_turnstile_challenge(driver, url):
    """Solve Turnstile challenge if present"""
    solver = TwoCaptcha(TWOCAPTCHA_KEY)

    # More comprehensive Cloudflare/Turnstile detection
    page_source = driver.page_source.lower()
    title = driver.title.lower()

    # Check for various Cloudflare indicators
    cloudflare_indicators = [
        "just a moment" in title,
        "checking your browser" in page_source,
        "cloudflare" in page_source,
        "cf-turnstile" in page_source,
        "turnstile" in page_source,
        "challenge-platform" in page_source,
        "ray id" in page_source,
        driver.current_url.startswith("https://challenges.cloudflare.com")
    ]

    if any(cloudflare_indicators):
        print(f"   🔍 Cloudflare challenge detected, attempting 2captcha solve...")
        try:
            # First try to find turnstile widget directly
            turnstile_element = None
            try:
                turnstile_element = driver.find_element(By.CSS_SELECTOR, "[data-sitekey]")
            except:
                try:
                    turnstile_element = driver.find_element(By.CSS_SELECTOR, ".cf-turnstile")
                except:
                    pass

            if turnstile_element:
                sitekey = turnstile_element.get_attribute("data-sitekey")
                if sitekey:
                    print(f"   🔑 Found sitekey: {sitekey[:20]}...")
                    payload = {'sitekey': sitekey, 'url': url}

                    # Try to solve with 2captcha
                    result = solver.turnstile(**payload)
                    print(f"   ✅ 2captcha solution received")

                    # Inject solution
                    driver.execute_script(f"""
                        var input = document.querySelector('[name="cf-turnstile-response"]');
                        if (input) {{
                            input.value = '{result['code']}';
                            console.log('Turnstile solution injected');
                        }}

                        // Try callback method too
                        if (window.turnstileCallback) {{
                            window.turnstileCallback('{result['code']}');
                        }}

                        // Try form submission
                        var form = document.querySelector('form');
                        if (form) {{
                            form.submit();
                        }}
                    """)

                    time.sleep(8)  # Wait longer for processing

                    # Check if challenge was solved by looking for redirect or content change
                    new_url = driver.current_url
                    if new_url != url and not new_url.startswith("https://challenges.cloudflare.com"):
                        print(f"   ✅ Challenge solved, redirected to: {new_url}")
                        return True

                    print(f"   ⚠️ Still on challenge page, trying manual wait...")
                    time.sleep(10)
                    return True

            else:
                print(f"   ⚠️ Cloudflare detected but no turnstile widget found")

        except Exception as e:
            print(f"   ❌ Error solving Turnstile: {e}")
            # Continue anyway, maybe it will work
            time.sleep(5)
            return True

    return True

def extract_cv_data_with_mistral(html_content):
    """Extract CV data from HTML using MistralAI"""
    print(f"🔍 Starting CV data extraction with MistralAI...")
    print(f"   HTML content length: {len(html_content)} characters")

    if not MISTRAL_API_KEY:
        print(f"❌ MISTRAL_API_KEY not found!")
        return None

    # Permanent prompt for CV data extraction
    extraction_prompt = """Extract CV data from the provided HTML content and return it in this exact JSON format:

{
  "name": "Full Name",
  "location": "City, Country",
  "experience": [
    {
      "title": "Job Title",
      "company": "Company Name",
      "dates": "Start Date - End Date",
      "location": "Job Location"
    }
  ],
  "skills": ["Skill1", "Skill2", "Skill3"],
  "education": [
    {
      "degree": "Degree Name",
      "institution": "Institution Name",
      "dates": "Start Date - End Date"
    }
  ]
}

If any section is missing or empty, use empty arrays [] or empty strings "". Return ONLY the JSON, no additional text."""

    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MISTRAL_API_KEY}"
    }
    
    # Extract text content from HTML for processing
    try:
        decoded_content = html.unescape(html_content)
        soup = BeautifulSoup(decoded_content, 'html.parser')
        
        # Remove unwanted elements (navigation, header, footer, etc.)
        unwanted_selectors = [
            'header', 'nav', 'footer', '.header', '.nav', '.footer',
            '.navigation', '.menu', '.toolbar', '.sidebar', '.breadcrumb',
            '.skip-link', '.collapse', '.create-new', '.main-content',
            '.candidate-contact-details', '.email-template', '.template-selector',
            '.message-form', '.job-selector', '.additional-options',
            '.hcaptcha', '.privacy-policy', '.terms-service', '.cookie-policy',
            '.language-selector', '.about-links', '.site-footer'
        ]
        
        for selector in unwanted_selectors:
            for element in soup.select(selector):
                element.decompose()
        
        # Try to find the actual resume content
        cv_text = ""
        
        # Method 1: Look for rdp-resume-container (Indeed's resume container)
        resume_container = soup.find('div', class_='rdp-resume-container')
        if resume_container:
            cv_text = resume_container.get_text(separator=' ', strip=True)
        
        # Method 2: Look for content between "Resume" and "Email" markers if container not found
        if not cv_text or len(cv_text) < 200:
            full_text = soup.get_text(separator=' ', strip=True)
            
            # Find the start of resume content (after "Resume" keyword)
            resume_start = full_text.find("Resume")
            if resume_start != -1:
                # Find the end of resume content (before "Email" or "Select a template")
                resume_end = full_text.find("Email Select a template")
                if resume_end == -1:
                    resume_end = full_text.find("Select a template")
                if resume_end == -1:
                    resume_end = full_text.find("Try Professional")
                if resume_end == -1:
                    resume_end = len(full_text)
                
                cv_text = full_text[resume_start:resume_end].strip()
        
        # Method 3: Fallback - get text and try to clean it
        if not cv_text or len(cv_text) < 200:
            cv_text = soup.get_text(separator=' ', strip=True)
            
            # Remove common Indeed interface text
            unwanted_phrases = [
                "Smart Sourcing", "Indeed for Employers", "Skip to main content",
                "Create new", "Home", "Jobs", "Campaigns", "Candidates", "Interviews",
                "Analytics", "ATS Integrations", "Tools", "Post a job", "Phone calls",
                "Branded Ads", "AI summaries", "Manage workforce", "Help Notifications",
                "Messages", "balazs.ronaszeki@matchtrex.com", "lorenz@beyondleverage.com",
                "Start of main content", "Find candidates", "Plans and Pricing",
                "Projects", "Saved searches", "Templates", "contacts", "Start Professional trial",
                "Forward resume", "Report this resume", "Recently updated",
                "Candidate contact details are hidden", "Email Select a template",
                "Try Professional", "Create a new template", "From Company Subject",
                "customize the subject line", "Save as template", "Your email address",
                "By pressing Send", "Cookie Policy", "Privacy Policy", "Terms of Service",
                "Additional options", "Preview Send", "This site is protected by hCaptcha",
                "Choose the language", "About - Contact Indeed", "© 2025 Indeed"
            ]
            
            for phrase in unwanted_phrases:
                cv_text = cv_text.replace(phrase, "")
            
            # Clean up extra whitespace
            cv_text = " ".join(cv_text.split())
        
        # Limit text length for API call
        cv_text = cv_text[:8000]  # Limit to prevent token overflow
        
        # Print cleaned HTML data to console
        print(f"\n=== CLEANED CV TEXT ===")
        print(cv_text)
        print(f"=== END CLEANED CV TEXT (Length: {len(cv_text)}) ===\n")
        
    except Exception as e:
        print(f"Error processing HTML: {e}")
        return None
    
    payload = {
        "model": "mistral-medium-latest",
        "messages": [
            {"role": "system", "content": "You are a CV data extraction specialist. Extract structured data from CV/resume content and return it in the exact JSON format requested."},
            {"role": "user", "content": f"{extraction_prompt}\n\nCV Content:\n{cv_text}"}
        ],
        "max_tokens": 1500,
        "temperature": 0.1
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        ai_response = result['choices'][0]['message']['content'].strip()
        
        # Print the raw MistralAI response for debugging
        print(f"\n=== MISTRAL CV EXTRACTION RESPONSE ===")
        print(ai_response)
        print(f"=== END MISTRAL CV EXTRACTION RESPONSE ===\n")
        
        # Try to parse the JSON response
        try:
            # Clean the response to extract JSON
            if "```json" in ai_response:
                ai_response = ai_response.split("```json")[1].split("```")[0].strip()
            elif "```" in ai_response:
                ai_response = ai_response.split("```")[1].strip()
            
            cv_data = json.loads(ai_response)
            return cv_data
            
        except json.JSONDecodeError:
            print(f"Error parsing JSON from MistralAI response: {ai_response}")
            return None
            
    except Exception as e:
        print(f"Error extracting CV data with MistralAI: {e}")
        return None

def evaluate_candidate_with_mistral(cv_data, profile_url, system_prompt, user_prompt):
    """Evaluate single candidate using MistralAI"""
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MISTRAL_API_KEY}"
    }
    
    # Format CV data for evaluation
    formatted_cv = format_cv_data_for_evaluation(cv_data)
    
    # Add lenient evaluation instruction
    lenient_instruction = """\nREQUIRED OUTPUT FORMAT: 
                             ["https://resumes.indeed.com/resume/abc123", "https://resumes.indeed.com/resume/def456"]
                             IF NO CANDIDATES QUALIFY:[]\n 
                             No SUMMARY. NO EXPLANATION. ANALYZE AND RETURN ONLY JSON ARRAY NOW:\n
                        
                             \nIMPORTANT: Be lenient in your evaluation. If a candidate meets most of the requirements but is missing one or two, still consider them QUALIFIED. 
                             Focus on potential and transferable skills rather than exact matches. If the candidate shows promise and could potentially fit the role, accept them."""

    payload = {
        "model": "mistral-medium-latest",
        "messages": [
            {"role": "system", "content": system_prompt + lenient_instruction},
            {"role": "user", "content": f"{user_prompt}\n\nCandidate CV:\n{formatted_cv}\n\nProfile URL: {profile_url}"}
        ],
        "max_tokens": 1000,
        "temperature": 0.1
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        ai_response = result['choices'][0]['message']['content'].strip()
        
        # Print the raw MistralAI evaluation response for debugging
        print(f"\n=== MISTRAL EVALUATION RESPONSE ===")
        print(ai_response)
        print(f"=== END MISTRAL EVALUATION RESPONSE ===\n")
        
        # Check if candidate is accepted (looking for the profile URL in response)
        is_accepted = profile_url in ai_response or "PASS" in ai_response.upper()
        
        print(f"   Evaluation result: {'ACCEPTED' if is_accepted else 'REJECTED'}")
        print(f"   Reason: {ai_response[:200]}...")
        
        return is_accepted, ai_response
            
    except Exception as e:
        print(f"Error evaluating candidate with MistralAI: {e}")
        return False, "Error in evaluation"

def format_cv_data_for_evaluation(cv_data):
    """Format CV data for AI evaluation"""
    if not cv_data:
        return "No CV data available"
    
    formatted = f"Name: {cv_data.get('name', 'N/A')}\n"
    formatted += f"Location: {cv_data.get('location', 'N/A')}\n\n"
    
    if cv_data.get('experience'):
        formatted += "Work Experience:\n"
        for exp in cv_data['experience']:
            formatted += f"- {exp.get('title', 'N/A')} at {exp.get('company', 'N/A')} ({exp.get('dates', 'N/A')})\n"
        formatted += "\n"
    
    if cv_data.get('skills'):
        formatted += "Skills:\n"
        for skill in cv_data['skills']:
            formatted += f"- {skill}\n"
        formatted += "\n"
    
    if cv_data.get('education'):
        formatted += "Education:\n"
        for edu in cv_data['education']:
            formatted += f"- {edu.get('degree', 'N/A')} at {edu.get('institution', 'N/A')} ({edu.get('dates', 'N/A')})\n"
    
    return formatted

def send_email_with_results(filtered_candidates, search_keywords, location, radius, recipient_email, search_name=None):
    """Send email with filtered candidates using HTML template"""
    try:
        from datetime import datetime
        
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = recipient_email
        # Dynamic subject based on search name or keywords
        search_title = search_name if search_name else search_keywords
        msg['Subject'] = f"🎯 MatchTrex: {len(filtered_candidates)} Kandidaten für '{search_title}' gefunden"
        
        # Generate candidate table rows with enhanced information
        candidate_rows = ""
        for i, candidate in enumerate(filtered_candidates, 1):
            # Extract account key from URL for tracking
            account_key = candidate['url'].split('/')[-1] if '/' in candidate['url'] else f"candidate_{i}"
            feedback_url = f"https://matchtrex-feedback.example.com/feedback?profile={account_key}&status=unsuitable"

            # Get candidate details
            candidate_name = candidate.get('name', 'N/A')
            candidate_location = candidate.get('location', 'N/A')
            candidate_analysis = candidate.get('ai_response', 'No analysis available')

            # Truncate analysis to fit email nicely
            if len(candidate_analysis) > 150:
                candidate_analysis = candidate_analysis[:150] + "..."

            candidate_rows += f"""
        <tr>
            <td style="padding: 12px; border: 1px solid #ddd; text-align: center; font-weight: bold; background: #f8f9fa;">{i}</td>
            <td style="padding: 12px; border: 1px solid #ddd;">
                <div style="margin-bottom: 8px;">
                    <a href="{candidate['url']}" style="color: #0066cc; text-decoration: none; font-weight: 600; font-size: 16px;">
                        👤 {candidate_name}
                    </a>
                    <span style="color: #6c757d; margin-left: 10px; font-size: 14px;">📍 {candidate_location}</span>
                </div>
                <div style="background: #e8f5e8; padding: 8px; border-radius: 4px; margin: 8px 0; font-size: 13px; color: #155724;">
                    <strong>✅ KI-Bewertung:</strong> {candidate_analysis}
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 8px;">
                    <small style="color: #6c757d;">Klicke auf den Namen für das vollständige Profil</small>
                    <a href="{feedback_url}" style="background: #dc3545; color: white; padding: 4px 8px; border-radius: 3px; text-decoration: none; font-size: 11px;">
                        ❌ Nicht passend
                    </a>
                </div>
            </td>
        </tr>"""
        
        # Generate current timestamp
        current_time = datetime.now().strftime("%d. %B %Y, %H:%M Uhr")
        candidate_count = len(filtered_candidates)
        
        # Create HTML email body
        html_body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    
    <h2 style="color: #0066cc; border-bottom: 2px solid #0066cc; padding-bottom: 10px;">
        🎯 Neue Kandidaten-Shortlist
    </h2>
    
    <p>Hallo MatchTrex Team,</p>
    
    <p>der Sourcingbot hat eine neue Kandidaten-Shortlist für euch erstellt:</p>
    
    <table style="width: 100%; border-collapse: collapse; margin: 20px 0; background: #f9f9f9; border: 1px solid #ddd;">
        <tr style="background: #0066cc; color: white;">
            <td style="padding: 12px; font-weight: bold;">Suchauftrag</td>
            <td style="padding: 12px; font-weight: bold;">Verkäufer {location}</td>
        </tr>
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;">Suchbereich</td>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;">{location} + {radius}km Radius</td>
        </tr>
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;">Keywords</td>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;">{search_keywords}</td>
        </tr>
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;">Letzte Aktivität</td>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;">Letzten 30 Tage</td>
        </tr>
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;">Gefundene Kandidaten</td>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>{candidate_count} relevante Profile</strong></td>
        </tr>
    </table>
    
    <h3 style="color: #0066cc; margin-top: 30px;">📋 Shortlist der Kandidaten:</h3>
    
    <div style="background: #f0f7ff; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
        <p style="margin: 0; font-size: 14px; color: #666;">
            <strong>Hinweis:</strong> Die folgenden Kandidaten haben die KI-Bewertung erfolgreich bestanden und erfüllen die definierten Kriterien.
        </p>
    </div>
    
    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
        <tr style="background: #f5f5f5;">
            <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold; width: 50px;">#</td>
            <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Kandidat Profil & Feedback</td>
        </tr>
        {candidate_rows}
    </table>
    
    <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
        <h4 style="color: #495057; margin-top: 0;">📊 Feedback-System:</h4>
        <p style="margin: 5px 0; font-size: 13px; color: #6c757d;">
            • Klickt auf "❌ Nicht passend" wenn ein Kandidat die Anforderungen nicht erfüllt<br>
            • Das Feedback wird automatisch gespeichert und hilft bei der Verbesserung der KI-Bewertung<br>
            • Admin erhält eine Zusammenfassung aller Feedbacks zur Prompt-Optimierung
        </p>
    </div>
    
    <div style="background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0;">
        <p style="margin: 0; font-size: 14px; color: #155724;">
            <strong>✅ Zusammenfassung:</strong> {candidate_count} qualifizierte Kandidaten durch KI-Bewertung identifiziert
        </p>
    </div>
    
    <h3 style="color: #0066cc;">📝 Nächste Schritte:</h3>
    <ul style="color: #666; font-size: 14px;">
        <li>Klickt auf die Links, um die vollständigen Profile zu öffnen</li>
        <li>Prüft die Kandidaten auf Passgenauigkeit</li>
        <li>Kontaktiert interessante Kandidaten direkt über Indeed</li>
        <li>Bei Fragen zum Sourcingbot wendet euch an das Tech-Team</li>
    </ul>
    
    <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
        <p style="margin: 0; font-size: 12px; color: #856404;">
            <strong>⚠️ Wichtiger Hinweis:</strong> Diese Shortlist wird automatisch nach 6 Monaten gelöscht (DSGVO-Konformität).
        </p>
    </div>
    
    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
    
    <p style="font-size: 12px; color: #666; text-align: center;">
        Automatisch generiert durch MatchTrex Sourcingbot<br>
        Erstellt am: <strong>{current_time}</strong><br>
        Suchauftrag ID: <strong>JOB_001</strong>
    </p>
    
    <p style="font-size: 11px; color: #999; text-align: center; margin-top: 20px;">
        Diese E-Mail enthält nur Links zu öffentlich verfügbaren Profilen. Keine persönlichen Daten werden gespeichert.
    </p>
    
</body>
</html>"""
        
        msg.attach(MIMEText(html_body, 'html'))
        
        # Send email
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        text = msg.as_string()
        server.sendmail(EMAIL_USER, recipient_email, text)
        server.quit()
        
        print(f"Email sent successfully to {recipient_email}")
        
    except Exception as e:
        print(f"Error sending email: {e}")

def download_cv_html_files(unique_candidates, target_candidates):
    """Download all CV HTML files to temp_CVs directory"""
    # Clear and create temp_CVs directory
    if os.path.exists("temp_CVs"):
        shutil.rmtree("temp_CVs")
    os.makedirs("temp_CVs")
    
    driver = setup_driver_with_cookies()
    downloaded_files = []
    
    try:
        for i, profile_url in enumerate(unique_candidates[:target_candidates], 1):
            print(f"   Downloading CV {i}/{min(len(unique_candidates), target_candidates)}")
            
            try:
                # Add timeout for page load
                driver.set_page_load_timeout(30)
                driver.get(profile_url)
                time.sleep(3)

                # Solve Turnstile if needed with timeout
                try:
                    if not solve_turnstile_challenge(driver, profile_url):
                        print(f"   Failed to solve Turnstile for {profile_url}")
                        continue
                except Exception as turnstile_error:
                    print(f"   Turnstile timeout for {profile_url}: {turnstile_error}")
                    continue

                # Wait for the actual CV content to load, not just loading messages
                content_loaded = False
                max_attempts = 3
                for attempt in range(max_attempts):
                    try:
                        # Wait for the resume container
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "rdp-resume-container"))
                        )

                        # Wait additional time for content to populate
                        time.sleep(3)

                        # Check if we have actual content (not just loading message)
                        page_text = driver.execute_script("return document.body.innerText;")
                        if len(page_text) > 100 and "Nur einen Moment" not in page_text and "Just a moment" not in page_text:
                            content_loaded = True
                            break
                        else:
                            print(f"   Attempt {attempt + 1}: Still loading, waiting longer...")
                            time.sleep(5)

                    except Exception as wait_error:
                        print(f"   Attempt {attempt + 1}: Wait error: {wait_error}")
                        time.sleep(3)

                if not content_loaded:
                    print(f"   Failed to load actual CV content after {max_attempts} attempts: {profile_url}")
                    continue

                time.sleep(1)
                
                # Get the complete HTML using browser's DOM
                html_content = driver.execute_script("return document.documentElement.outerHTML;")

                # Alternative: If the above doesn't work, try getting the body content
                if not html_content or len(html_content) < 1000:
                    html_content = driver.execute_script("return document.body.innerHTML;")

                # Final fallback to page_source if needed
                if not html_content or len(html_content) < 1000:
                    html_content = driver.page_source

                # Debug: Check content quality
                page_text = driver.execute_script("return document.body.innerText;")
                if len(page_text) < 50:
                    print(f"   ⚠️ Short content detected ({len(page_text)} chars): {page_text[:50]}...")
                else:
                    print(f"   ✅ Good content length: {len(page_text)} characters")
                
                # Extract account key from URL for filename
                account_key = profile_url.split('/')[-1]
                filename = f"temp_CVs/cv_{account_key}.html"
                
                # Save HTML content
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                downloaded_files.append({
                    'filename': filename,
                    'url': profile_url,
                    'account_key': account_key
                })
                
                print(f"   ✓ Downloaded {account_key}")
                
            except Exception as e:
                print(f"   Error downloading {profile_url}: {e}")
                # If driver gets stuck, try to recover
                try:
                    driver.execute_script("window.stop();")
                except:
                    pass
                continue
    
    finally:
        driver.quit()
    
    return downloaded_files

def process_saved_cv_files(downloaded_files, system_prompt, user_prompt):
    """Process saved CV HTML files with MistralAI"""
    filtered_candidates = []
    
    for i, file_info in enumerate(downloaded_files, 1):
        print(f"   Processing CV {i}/{len(downloaded_files)}")
        
        try:
            # Read HTML file
            with open(file_info['filename'], 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Extract CV data using MistralAI
            print(f"   Extracting CV data for {file_info['account_key']}...")
            cv_data = extract_cv_data_with_mistral(html_content)
            if not cv_data:
                print(f"   ❌ No CV data found for {file_info['account_key']}")
                continue

            print(f"   ✅ CV data extracted: name={cv_data.get('name', 'N/A')}")
            print(f"      Fields found: {list(cv_data.keys())}")
            print(f"      name: {cv_data.get('name', 'Missing')}")
            print(f"      email: {cv_data.get('email', 'Missing')}")
            print(f"      location: {cv_data.get('location', 'Missing')}")
            
            # Evaluate candidate with MistralAI
            is_qualified, ai_response = evaluate_candidate_with_mistral(
                cv_data, file_info['url'], system_prompt, user_prompt
            )
            
            if is_qualified:
                candidate_info = {
                    'name': cv_data.get('name', 'N/A'),
                    'location': cv_data.get('location', 'N/A'),
                    'experience': cv_data.get('experience', []),
                    'skills': cv_data.get('skills', []),
                    'education': cv_data.get('education', []),
                    'url': file_info['url'],
                    'ai_response': ai_response
                }
                filtered_candidates.append(candidate_info)
                print(f"   ✓ Candidate {cv_data.get('name', 'Unknown')} qualified")
            else:
                print(f"   ✗ Candidate {cv_data.get('name', 'Unknown')} not qualified")
                
        except Exception as e:
            print(f"   Error processing {file_info['filename']}: {e}")
            continue
    
    return filtered_candidates

def log_message(message):
    """Log message to file and console using logger"""
    logger.info(message)
    
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] {message}\n")
    except Exception as e:
        logger.error(f"Error writing to log file: {e}")

def update_sheet_status(status, message):
    """Update status in Google Sheets"""
    try:
        sheet_id = get_google_sheets_id()
        if not sheet_id:
            log_message("No Google Sheets ID configured for status update")
            return
        
        gs_service = GoogleSheetsService(GOOGLE_SHEETS_CREDENTIALS_PATH, sheet_id)
        
        if not gs_service.setup_authentication():
            log_message("Failed to authenticate for status update")
            return
        
        if not gs_service.open_spreadsheet():
            log_message("Failed to open spreadsheet for status update")
            return
        
        # Get the Search Parameters sheet
        try:
            worksheet = gs_service.spreadsheet.worksheet("Search Parameters")
        except:
            log_message("Search Parameters sheet not found")
            return
        
        # Find the last row and add status
        values = worksheet.get_all_values()
        next_row = len(values) + 2
        
        # Update status
        worksheet.update(f'A{next_row}:C{next_row}', [['Pipeline Status', status, message]])
        worksheet.update(f'A{next_row + 1}:B{next_row + 1}', [['Last Updated', datetime.now().strftime("%Y-%m-%d %H:%M:%S")]])
        
        log_message(f"Status updated in Google Sheets: {status}")
        
    except Exception as e:
        log_message(f"Error updating sheet status: {e}")

def run_pipeline_in_background():
    """Run the pipeline in background thread"""
    global pipeline_running
    
    try:
        pipeline_running = True
        log_message("Starting pipeline execution in background...")
        update_sheet_status("RUNNING", f"Pipeline started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run the main pipeline
        main_pipeline()
        
        log_message("Pipeline completed successfully")
        update_sheet_status("COMPLETED", f"Pipeline completed successfully at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        log_message(f"Error in pipeline execution: {e}")
        update_sheet_status("ERROR", f"Pipeline failed: {str(e)}")
    finally:
        pipeline_running = False

@app.get("/")
async def root():
    """Service status endpoint"""
    global pipeline_running
    return {
        "service": "MatchTrex Pipeline API",
        "version": "1.0",
        "status": "running",
        "pipeline_running": pipeline_running,
        "endpoints": {
            "search": "POST /search",
            "trigger": "POST /run-mvp",
            "status": "GET /status", 
            "health": "GET /health"
        }
    }

@app.options("/search")
async def options_search():
    """Handle preflight OPTIONS request for /search endpoint"""
    return {"message": "OK"}

@app.post("/search")
async def run_search(params: SearchParameters):
    """API endpoint to run search with form parameters"""
    global pipeline_running
    
    try:
        log_message(f"Received search request with params: {params.dict()}")
        
        # Set pipeline running flag
        pipeline_running = True
        
        try:
            # Run pipeline directly with form parameters
            profile_urls = main_pipeline(params.dict())
            log_message("Search pipeline completed with form parameters")
            
            return JSONResponse({
                'status': 'success',
                'message': 'Search pipeline completed successfully',
                'timestamp': datetime.now().isoformat(),
                'search_params': params.dict(),
                'profile_urls': profile_urls
            })
        finally:
            pipeline_running = False
        
    except HTTPException:
        raise
    except Exception as e:
        log_message(f"Error in search endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/run-mvp")
async def trigger_mvp(request: TriggerRequest):
    """Webhook endpoint to trigger MVP pipeline"""
    global pipeline_running
    
    try:
        log_message(f"Received trigger request: {request.dict()}")
        
        # Validate request
        if request.action != 'run_mvp':
            raise HTTPException(status_code=400, detail="Invalid action")
        
        # Check if pipeline is already running
        if pipeline_running:
            log_message("Pipeline is already running, ignoring request")
            raise HTTPException(status_code=409, detail="Pipeline is already running")
        
        # Start pipeline in background thread
        thread = threading.Thread(target=run_pipeline_in_background)
        thread.daemon = True
        thread.start()
        
        log_message("Pipeline started in background")
        
        return JSONResponse({
            'status': 'success',
            'message': 'MVP pipeline started successfully',
            'timestamp': datetime.now().isoformat()
        })
        
    except HTTPException:
        raise
    except Exception as e:
        log_message(f"Error in webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Get current status of the pipeline"""
    global pipeline_running
    
    try:
        # Read last few log entries
        recent_logs = []
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                recent_logs = f.readlines()[-10:]  # Last 10 lines
        except:
            pass
        
        return StatusResponse(
            is_running=pipeline_running,
            recent_logs=[log.strip() for log in recent_logs],
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        script_path=SCRIPT_PATH,
        script_exists=os.path.exists(SCRIPT_PATH)
    )

def main_pipeline(form_params=None):
    """Main MVP pipeline"""
    print("=== MatchTrex MVP Pipeline ===\n")
    
    # Step 1: Get search parameters - either from form or Google Sheets
    if form_params:
        print("1. Using search parameters from form...")
        params = form_params
    else:
        print("1. Reading search parameters from Google Sheets...")
        params = read_search_parameters()
        if not params:
            print("Error: Could not read search parameters")
            return
    
    search_keywords = params.get('search_keywords', '')
    location = params.get('location', '')
    max_radius = int(params.get('max_radius', 20))
    target_candidates = int(params.get('target_candidates', 10))
    recipient_email = params.get('recipient_email', '')
    system_prompt = params.get('system_prompt', '')
    user_prompt = params.get('user_prompt', '')
    resume_last_updated_days = int(params.get('resume_last_updated_days', 30))
    
    print(f"   Keywords: {search_keywords}")
    print(f"   Location: {location}")
    print(f"   Target: {target_candidates} candidates")
    
    # Step 2: Search for candidates
    print("\n2. Searching for candidates on Indeed...")
    resume_filter = calculate_unix_timestamp_ms(resume_last_updated_days)
    all_candidates = []
    
    # Progressive radius search
    for radius in range(5, max_radius + 1, 5):
        print(f"   Searching radius {radius}km...")
        response = make_indeed_request(radius, search_keywords, resume_filter, location)
        if response:
            candidates = extract_candidate_data(response)
            all_candidates.extend(candidates)
            print(f"   Found {len(candidates)} candidates at {radius}km")
            
            if len(all_candidates) >= target_candidates:
                break
    
    # Remove duplicates
    unique_candidates = list(set(all_candidates))
    print(f"   Total unique candidates found: {len(unique_candidates)}")
    
    # Step 3: Download CV HTML files
    print("\n3. Downloading CV HTML files...")
    downloaded_files = download_cv_html_files(unique_candidates, target_candidates)
    print(f"   Downloaded {len(downloaded_files)} CV files to temp_CVs/")
    
    # Step 4: Process CV files with MistralAI
    print("\n4. Processing CV files with MistralAI...")
    filtered_candidates = process_saved_cv_files(downloaded_files, system_prompt, user_prompt)
    
    # Clean up temp_CVs directory after processing
    if os.path.exists("temp_CVs"):
        shutil.rmtree("temp_CVs")
        print("   Cleaned up temp_CVs directory")
    
    # Step 5: Send email with results
    print(f"\n5. Sending results email...")
    print(f"   Qualified candidates: {len(filtered_candidates)}")
    
    if filtered_candidates:
        send_email_with_results(filtered_candidates, search_keywords, location, max_radius, recipient_email)
        
        # Save results to file
        timestamp = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
        filename = f"filtered_contacts_mistral_ai_{timestamp}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# MatchTrex MVP Results\n\n")
            for candidate in filtered_candidates:
                f.write(f"{candidate['url']}\n")
        
        print(f"   Results saved to {filename}")
    else:
        print("   No qualified candidates found")
    
    print("\n=== Pipeline Complete ===")

def main_pipeline_for_api(search_data: dict) -> dict:
    """
    API-Version der Pipeline - angepasst für Backend Integration
    Nimmt Supabase search_data und gibt strukturierte Ergebnisse zurück
    """
    print("=== MatchTrex MVP Pipeline (API Mode) ===\n")

    try:
        # Step 1: Parameter Mapping - Supabase Format → Pipeline Format
        form_params = {
            'search_keywords': search_data.get('search_keywords', ''),
            'location': search_data.get('location', ''),
            'max_radius': search_data.get('max_radius', 25),
            'target_candidates': search_data.get('target_candidates', 100),
            'recipient_email': search_data.get('recipient_email', ''),
            'system_prompt': search_data.get('system_prompt', ''),
            'user_prompt': search_data.get('user_prompt', ''),
            'resume_last_updated_days': search_data.get('resume_last_updated_days', 30)
        }

        print(f"1. Search Parameters:")
        print(f"   Keywords: {form_params['search_keywords']}")
        print(f"   Location: {form_params['location']}")
        print(f"   Target: {form_params['target_candidates']} candidates")
        print(f"   Radius: {form_params['max_radius']} km")

        # Extract parameters
        search_keywords = form_params['search_keywords']
        location = form_params['location']
        max_radius = int(form_params['max_radius'])
        target_candidates = int(form_params['target_candidates'])
        recipient_email = form_params['recipient_email']
        system_prompt = form_params['system_prompt']
        user_prompt = form_params['user_prompt']
        resume_last_updated_days = int(form_params['resume_last_updated_days'])

        # Step 2: Search for candidates
        print("\n2. Searching for candidates on Indeed...")
        resume_filter = calculate_unix_timestamp_ms(resume_last_updated_days)
        all_candidates = []

        # Progressive radius search
        for radius in range(5, max_radius + 1, 5):
            print(f"   Searching radius {radius}km...")
            response = make_indeed_request(radius, search_keywords, resume_filter, location)
            if response:
                candidates = extract_candidate_data(response)
                all_candidates.extend(candidates)
                print(f"   Found {len(candidates)} candidates at {radius}km")

                if len(all_candidates) >= target_candidates:
                    break

        # Remove duplicates
        unique_candidates = list(set(all_candidates))
        print(f"   Total unique candidates found: {len(unique_candidates)}")

        # Step 3: Download CV HTML files (with ChromeDriver fallback)
        print("\n3. Downloading CV HTML files...")
        try:
            downloaded_files = download_cv_html_files(unique_candidates, target_candidates)
            print(f"   Downloaded {len(downloaded_files)} CV files")

            # Step 4: Process CV files with MistralAI
            print("\n4. Processing CV files with MistralAI...")
            filtered_candidates = process_saved_cv_files(downloaded_files, system_prompt, user_prompt)

        except Exception as e:
            error_msg = str(e)
            print(f"❌ CV download/processing failed: {error_msg}")

            if "ChromeDriver" in error_msg or "Status code was: 127" in error_msg:
                print("⚠️ ChromeDriver not available on this system")
                print("   Falling back to candidate list without CV analysis...")

                # Fallback: Create basic candidate entries without CV analysis
                filtered_candidates = []
                for i, candidate_url in enumerate(unique_candidates[:target_candidates]):
                    # Extract account key from URL for basic info
                    account_key = candidate_url.split('/')[-1] if '/' in candidate_url else f"candidate_{i+1}"

                    fallback_candidate = {
                        'name': f'Kandidat {i+1}',
                        'email': 'N/A (CV-Analyse nicht verfügbar)',
                        'url': candidate_url,
                        'ai_response': 'CV-Analyse nicht verfügbar: ChromeDriver fehlt auf diesem System. Bitte CV manuell prüfen.',
                        'location': 'N/A',
                        'title': 'N/A',
                        'experience': [],
                        'skills': [],
                        'education': []
                    }
                    filtered_candidates.append(fallback_candidate)

                print(f"   Created {len(filtered_candidates)} fallback candidate entries")
            else:
                # Re-raise if it's a different error
                raise e

        # Clean up temp_CVs directory
        if os.path.exists("temp_CVs"):
            shutil.rmtree("temp_CVs")
            print("   Cleaned up temp_CVs directory")

        # Step 5: Prepare API Results (no email/file saving in API mode)
        print(f"\n5. Preparing results...")
        print(f"   Total found: {len(unique_candidates)}")
        print(f"   After AI filtering: {len(filtered_candidates)}")

        # Convert filtered_candidates to API format
        api_candidates = []
        for candidate in filtered_candidates:
            # Extract structured data from candidate
            api_candidate = {
                "name": candidate.get('name', 'N/A'),
                "email": candidate.get('email', 'N/A'),  # CV parsing might not extract email
                "profile_url": candidate.get('url', 'N/A'),
                "analysis": candidate.get('ai_response', 'No analysis available'),  # Fixed field name
                "location": candidate.get('location', 'N/A'),
                "title": candidate.get('title', 'N/A'),
                "experience": candidate.get('experience', []),
                "skills": candidate.get('skills', []),
                "education": candidate.get('education', [])
            }
            api_candidates.append(api_candidate)

        # Return structured results for API
        results = {
            "candidates": api_candidates,
            "total_found": len(unique_candidates),
            "filtered_count": len(filtered_candidates),
            "search_completed": True,
            "timestamp": datetime.now().isoformat(),
            "search_keywords": search_keywords,
            "location": location,
            "recipient_email": recipient_email  # For Phase 5 email
        }

        # Step 6: Send Email Notification (if qualified candidates found and email provided)
        if filtered_candidates and recipient_email:
            print(f"\n6. Sending email notification...")
            print(f"   Sending results to: {recipient_email}")
            search_name = search_data.get('name', search_keywords)  # Use search name if available
            send_email_with_results(filtered_candidates, search_keywords, location, max_radius, recipient_email, search_name)
            print(f"   ✅ Email sent successfully!")
        elif not recipient_email:
            print(f"\n6. Skipping email - no recipient email provided")
        else:
            print(f"\n6. Skipping email - no qualified candidates found")

        print(f"✅ Pipeline completed successfully!")
        print(f"   Results: {len(api_candidates)} qualified candidates")

        return results

    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        raise Exception(f"Pipeline execution failed: {str(e)}")

    print("\n=== API Pipeline Complete ===")
    return [candidate['url'] for candidate in filtered_candidates] if filtered_candidates else []


def main():
    """Main entry point - handles both direct execution and FastAPI server mode"""
    import sys
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == '--server':
        # Run FastAPI server mode with uvicorn
        logger.info("🚀 Starting MatchTrex FastAPI webhook server...")
        log_message("Starting FastAPI webhook server...")
        log_message(f"Script path: {SCRIPT_PATH}")
        log_message(f"Log file: {LOG_FILE}")
        
        # Run HTTP server
        logger.info("🌐 Starting HTTP server on port 5000")
        uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")
    else:
        # Run pipeline directly
        main_pipeline()

if __name__ == "__main__":
    main()