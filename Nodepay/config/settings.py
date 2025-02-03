import json
import os

class AppConfig:
    # App Information
    NAME = "NullxNodePay Sentinel"
    VERSION = "3.0.0"
    AUTHOR = "Nullx"
    
    # Load API endpoints from JSON
    try:
        with open('data/endpoints.json', 'r') as f:
            endpoints = json.load(f)
            BASE_URL = endpoints['base_url']
            IP_CHECK_URL = endpoints['ip_check']
            SESSION_URL = endpoints['session']
            PING_URLS = endpoints['ping_urls']
    except Exception as e:
        print(f"Error loading endpoints.json: {e}")
        PING_URLS = ["http://13.215.134.222/api/network/ping"]  # fallback
    
    # Timing Configuration
    RETRY_INTERVAL = 30  # seconds
    DASHBOARD_UPDATE_INTERVAL = 1  # seconds
    
    # File Paths
    TOKEN_FILE = 'data/token.txt'
    PROXY_FILE = 'data/proxies.txt'
    LOG_FILE = 'data/sentinel.log'
    
    # HTTP Configuration
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    
    # Cache Configuration
    PROXY_CACHE_TTL = 2 * 60 * 60  # 2 hours in seconds