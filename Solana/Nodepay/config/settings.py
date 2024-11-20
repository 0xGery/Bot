class AppConfig:
    # App Information
    NAME = "NullxNodePay Sentinel"
    VERSION = "3.0.0"
    AUTHOR = "Nullx"
    
    # API Endpoints
    BASE_URL = 'http://nodepay.org'
    IP_CHECK_URL = 'http://ipinfo.io/json'
    PING_URL = 'http://13.215.134.222/api/network/ping'
    SESSION_URL = 'https://api.nodepay.ai/api/auth/session'
    
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