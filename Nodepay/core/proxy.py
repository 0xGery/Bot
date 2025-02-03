import aiohttp
import ssl
import certifi
from datetime import datetime
import asyncio
from colorama import Fore, Style

class ProxyManager:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self._cache = {}
        
    async def validate_proxy(self, proxy):
        """Test proxy connectivity and get location info"""
        try:
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            proxy_url = self._build_url(proxy)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'http://ip-api.com/json',
                    proxy=proxy_url,
                    timeout=10,
                    ssl=ssl_context
                ) as response:
                    data = await response.json()
                    
                    # Cache the IP info
                    self._cache[proxy['host']] = {
                        'info': data,
                        'timestamp': datetime.now()
                    }
                    
                    return {
                        'success': True,
                        'ip': data['query'],
                        'country': data['country'],
                        'city': data.get('city', 'Unknown'),
                        'isp': data.get('isp', 'Unknown')
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _build_url(self, proxy):
        """Build proxy URL with authentication if provided"""
        if not proxy or not proxy.get('host'):
            return None
            
        auth = ''
        if proxy.get('username') and proxy.get('password'):
            auth = f"{proxy['username']}:{proxy['password']}@"
            
        return f"http://{auth}{proxy['host']}:{proxy['port']}"

    def get_cached_info(self, proxy_host):
        """Get cached proxy information if available"""
        cached = self._cache.get(proxy_host)
        if cached and (datetime.now() - cached['timestamp']).seconds < self.config.PROXY_CACHE_TTL:
            return cached['info']
        return None