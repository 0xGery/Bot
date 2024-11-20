import aiohttp
import asyncio
from datetime import datetime
import secrets
from colorama import Fore, Style
from .proxy import ProxyManager

class SentinelMonitor:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.proxy_manager = ProxyManager(config, logger)
        
        # Initialize statistics
        self.stats = {
            'total_pings': 0,
            'successful_pings': 0,
            'failed_pings': 0,
            'start_time': datetime.now(),
            'last_success': None,
            'active_proxies': set(),
            'mode': None,
            'avg_response': 0,
            'memory_usage': 0,
            'cpu_percent': 0
        }
        
        self.current_status = None

    async def start_session(self, token, proxy=None):
        """Initialize session with token and optional proxy"""
        try:
            session_data = await self._get_session_data(token, proxy)
            
            if proxy:
                self.stats['active_proxies'].add(proxy['host'])
                
            self.logger.info(f"Session started for UID: {session_data['uid']}")
            return session_data
            
        except Exception as e:
            self.logger.error(f"Session initialization failed: {str(e)}")
            raise

    async def run(self, token, proxy=None):
        """Main bot operation loop"""
        try:
            session_data = await self.start_session(token, proxy)
            
            while True:
                try:
                    await self._send_ping(session_data, token, proxy)
                    await asyncio.sleep(self.config.RETRY_INTERVAL)
                except Exception as e:
                    self.logger.error(f"Ping failed: {str(e)}")
                    await asyncio.sleep(5)  # Short delay before retry
                    
        except Exception as e:
            self.logger.error(f"Bot operation failed: {str(e)}")

    async def _get_session_data(self, token, proxy=None):
        """Get session data from API"""
        async with aiohttp.ClientSession() as session:
            headers = {
                'Authorization': f'Bearer {token}',
                'User-Agent': self.config.USER_AGENT,
                'Accept': 'application/json'
            }
            
            proxy_url = self.proxy_manager._build_url(proxy) if proxy else None
            
            async with session.post(
                self.config.SESSION_URL,
                headers=headers,
                proxy=proxy_url
            ) as response:
                if response.status != 200:
                    raise Exception('Session request failed')
                data = await response.json()
                return data['data']

    async def _send_ping(self, session_data, token, proxy=None):
        """Send ping to maintain connection"""
        ping_data = {
            'id': session_data['uid'],
            'browser_id': session_data.get('browser_id', secrets.token_hex(8)),
            'timestamp': int(datetime.now().timestamp()),
            'version': self.config.VERSION
        }
        
        async with aiohttp.ClientSession() as session:
            headers = {
                'Authorization': f'Bearer {token}',
                'User-Agent': self.config.USER_AGENT,
                'Accept': 'application/json'
            }
            
            proxy_url = self.proxy_manager._build_url(proxy) if proxy else None
            
            try:
                async with session.post(
                    self.config.PING_URL,
                    json=ping_data,
                    headers=headers,
                    proxy=proxy_url
                ) as response:
                    if response.status != 200:
                        raise Exception('Ping failed')

                    self._update_stats(True, proxy)  # Add proxy parameter
                    self._set_success_status(session_data, proxy)
                    
            except Exception as e:
                self._update_stats(False, proxy)  # Add proxy parameter
                self._set_error_status(session_data, proxy, str(e))
                raise

    def _update_stats(self, success, proxy=None):
        """Update bot statistics"""
        self.stats['total_pings'] += 1
        if success:
            self.stats['successful_pings'] += 1
            self.stats['last_success'] = datetime.now()
            
            # Update proxy stats
            if proxy:
                if 'proxy_stats' not in self.stats:
                    self.stats['proxy_stats'] = {}
                if proxy['host'] not in self.stats['proxy_stats']:
                    self.stats['proxy_stats'][proxy['host']] = {'total': 0, 'success': 0}
                
                self.stats['proxy_stats'][proxy['host']]['total'] += 1
                self.stats['proxy_stats'][proxy['host']]['success'] += 1
                
                # Calculate success rate
                proxy_stats = self.stats['proxy_stats'][proxy['host']]
                proxy_stats['success_rate'] = (proxy_stats['success'] / proxy_stats['total']) * 100
        else:
            self.stats['failed_pings'] += 1
            # Update proxy failure
            if proxy and 'proxy_stats' in self.stats and proxy['host'] in self.stats['proxy_stats']:
                self.stats['proxy_stats'][proxy['host']]['total'] += 1
                proxy_stats = self.stats['proxy_stats'][proxy['host']]
                proxy_stats['success_rate'] = (proxy_stats['success'] / proxy_stats['total']) * 100

    def _set_success_status(self, session_data, proxy):
        """Set success status message"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.current_status = f"{Fore.CYAN}│{Style.RESET_ALL} {Fore.GREEN}[{timestamp}] ✓ Ping Successful{Style.RESET_ALL}\n\
{Fore.CYAN}│{Style.RESET_ALL} └─ UID: {Fore.YELLOW}{session_data['uid']}{Style.RESET_ALL}\n\
{Fore.CYAN}│{Style.RESET_ALL}    ├─ Via: {Fore.CYAN}{proxy['host'] if proxy else 'direct'}{Style.RESET_ALL}\n\
{Fore.CYAN}│{Style.RESET_ALL}    ├─ Response: {Fore.GREEN}{self.stats.get('last_response_time', 0):.2f}ms{Style.RESET_ALL}\n\
{Fore.CYAN}│{Style.RESET_ALL}    └─ Status: {Fore.GREEN}Active{Style.RESET_ALL}"

    def _set_error_status(self, session_data, proxy, error):
        """Set error status message"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.current_status = f"{Fore.CYAN}│{Style.RESET_ALL} {Fore.RED}[{timestamp}] ✗ Ping Failed{Style.RESET_ALL}\n\
{Fore.CYAN}│{Style.RESET_ALL} └─ UID: {Fore.YELLOW}{session_data['uid']}{Style.RESET_ALL}\n\
{Fore.CYAN}│{Style.RESET_ALL}    ├─ Via: {Fore.CYAN}{proxy['host'] if proxy else 'direct'}{Style.RESET_ALL}\n\
{Fore.CYAN}│{Style.RESET_ALL}    ├─ Error: {Fore.RED}{error}{Style.RESET_ALL}\n\
{Fore.CYAN}│{Style.RESET_ALL}    └─ Status: {Fore.RED}Failed{Style.RESET_ALL}"

    def _set_error_status(self, session_data, proxy, error):
        """Set error status message"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.current_status = f"""
{Fore.CYAN}│{Style.RESET_ALL} {Fore.RED}[{timestamp}] ✗ Ping Failed{Style.RESET_ALL}
{Fore.CYAN}│{Style.RESET_ALL} └─ UID: {Fore.YELLOW}{session_data['uid']}{Style.RESET_ALL}
{Fore.CYAN}│{Style.RESET_ALL}    ├─ Via: {Fore.CYAN}{proxy['host'] if proxy else 'direct'}{Style.RESET_ALL}
{Fore.CYAN}│{Style.RESET_ALL}    ├─ Error: {Fore.RED}{error}{Style.RESET_ALL}
{Fore.CYAN}│{Style.RESET_ALL}    └─ Status: {Fore.RED}Failed{Style.RESET_ALL}"""

class RetryHandler:
    def __init__(self, max_retries=3, backoff_factor=1.5):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    async def execute(self, func, *args, **kwargs):
        retries = 0
        while retries < self.max_retries:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                retries += 1
                if retries == self.max_retries:
                    raise
                wait_time = self.backoff_factor ** retries
                await asyncio.sleep(wait_time)
