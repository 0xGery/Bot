import random
import ssl

class Config:
    def __init__(self):
        self.ip_check_url = 'https://ipinfo.io/json'
        self.wss_list = ['proxy2.wynd.network:4444', 'proxy2.wynd.network:4650']
        self.retry_interval = 20  # seconds
        self.wss_host = random.choice(self.wss_list)
        self.ssl_verify = False
        self.timeout = 30
        
        # SSL context
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE