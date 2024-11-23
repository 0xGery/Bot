import json
import uuid
import asyncio
import aiohttp
import aiohttp_socks
from aiohttp import ClientWebSocketResponse
from colorama import Fore
from datetime import datetime

class Bot:
    def __init__(self, config, display_manager):
        self.config = config
        self.display = display_manager
        self.live = None

    async def get_proxy_ip(self, proxy: str) -> dict:
        try:
            if proxy:
                proxy_type = proxy.split('://')[0]
                if proxy_type.lower() == 'socks5':
                    connector = aiohttp_socks.ProxyConnector.from_url(proxy)
                    async with aiohttp.ClientSession(connector=connector) as session:
                        async with session.get(self.config.ip_check_url) as response:
                            if response.status == 200:
                                return await response.json()
                else:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(self.config.ip_check_url, proxy=proxy) as response:
                            if response.status == 200:
                                return await response.json()
            else:
                async with aiohttp.ClientSession() as session:
                    async with session.get(self.config.ip_check_url) as response:
                        if response.status == 200:
                            return await response.json()
            return None
        except Exception as e:
            self.display.add_error(f"IP check error for {proxy}: {str(e)}")
            return None

    async def create_websocket_connection(self, proxy: str = None):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0',
            'Pragma': 'no-cache',
            'Accept-Language': 'uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cache-Control': 'no-cache',
            'OS': 'Windows',
            'Platform': 'Desktop',
            'Browser': 'Mozilla',
            'Origin': 'https://getgrass.io',
            'Referer': 'https://getgrass.io/'
        }

        session = None
        try:
            if proxy:
                if proxy.startswith('socks5://'):
                    connector = aiohttp_socks.ProxyConnector.from_url(proxy, ssl=self.config.ssl_context)
                    session = aiohttp.ClientSession(connector=connector)
                else:
                    session = aiohttp.ClientSession()
                    headers['proxy'] = proxy
            else:
                session = aiohttp.ClientSession()

            websocket = await session.ws_connect(
                f"wss://{self.config.wss_host}",
                headers=headers,
                ssl=self.config.ssl_context,
                timeout=self.config.timeout,
                heartbeat=20
            )
            
            return websocket, session

        except Exception as e:
            if session:
                await session.close()
            raise Exception(f"WebSocket connection failed: {str(e)}")

    async def send_ping(self, websocket: ClientWebSocketResponse, proxy_ip: str):
        while True:
            try:
                ping_message = {
                    'id': str(uuid.uuid4()),
                    'version': '1.0.0',
                    'action': 'PING',
                    'data': {}
                }
                await websocket.send_json(ping_message)
                self.display.add_activity({
                    'time': datetime.now(),
                    'success': True,
                    'message': f'Ping sent via {proxy_ip}',
                    'status': 'Active'
                })
                self.display.update_stats(success=True, proxy=proxy_ip)
                self.display.update_display(self.live)
                await asyncio.sleep(26)
            except Exception as e:
                self.display.add_error(f"Ping error: {str(e)}")
                break

    async def handle_websocket(self, websocket: ClientWebSocketResponse, user_id: str, proxy_ip: str):
        try:
            async for msg in websocket:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    message = json.loads(msg.data)
                    
                    activity_data = {
                        'time': datetime.now(),
                        'success': True,
                        'message': 'Ping Successful',
                        'uid': user_id,
                        'proxy': proxy_ip,
                        'url': self.config.wss_host,
                        'response': '0.00',
                        'status': 'Active'
                    }
                    
                    try:
                        self.display.add_activity(activity_data)
                        self.display.update_stats(success=True, proxy=proxy_ip)
                        if self.live:
                            self.display.update_display(self.live)
                    except Exception as display_error:
                        print(f"Display update error: {str(display_error)}")

                    if message.get('action') == 'AUTH':
                        auth_response = {
                            'id': message['id'],
                            'origin_action': 'AUTH',
                            'result': {
                                'browser_id': str(uuid.uuid4()),
                                'user_id': user_id,
                                'user_agent': 'Mozilla/5.0',
                                'timestamp': int(datetime.now().timestamp()),
                                'device_type': 'desktop',
                                'version': '4.28.2'
                            }
                        }
                        await websocket.send_json(auth_response)
                        print(f"{Fore.GREEN}Sent auth response: {json.dumps(auth_response)}")
                    
                    elif message.get('action') == 'PONG':
                        print(f"{Fore.BLUE}Received PONG: {json.dumps(message)}")

                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print(f"{Fore.RED}WebSocket error: {websocket.exception()}")
                    break

        except Exception as e:
            activity_data = {
                'time': datetime.now(),
                'success': False,
                'message': f'Error: {str(e)}',
                'uid': user_id,
                'proxy': proxy_ip,
                'url': self.config.wss_host,
                'response': '0.00',
                'status': 'Failed'
            }
            self.display.add_activity(activity_data)
            self.display.update_stats(success=False, proxy=proxy_ip)
            self.display.update_display(self.live)
            print(f"{Fore.RED}WebSocket error: {str(e)}")
            return

    async def connect_with_proxy(self, proxy: str, user_id: str):
        while True:
            session = None
            websocket = None
            try:
                # Add proxy to used proxies set
                self.display.used_proxies.add(proxy)
                
                # Debug log
                self.display.add_activity({
                    'time': datetime.now(),
                    'success': True,
                    'message': f'Attempting to connect with proxy {proxy}',
                    'status': 'Connecting'
                })
                self.display.update_display(self.live)

                proxy_info = await self.get_proxy_ip(proxy)
                if not proxy_info:
                    self.display.add_error(f"Failed to get IP info for proxy {proxy}")
                    await asyncio.sleep(self.config.retry_interval)
                    continue

                # Format proxy like the Node.js version
                formatted_proxy = proxy.strip()
                if not (formatted_proxy.startswith('socks5://') or formatted_proxy.startswith('http')):
                    formatted_proxy = f'socks5://{formatted_proxy}'

                # Create WebSocket connection
                websocket, session = await self.create_websocket_connection(formatted_proxy)
                
                # Debug log successful connection
                self.display.add_activity({
                    'time': datetime.now(),
                    'success': True,
                    'message': f'Connected to {self.config.wss_host} via {proxy}',
                    'status': 'Connected'
                })
                self.display.update_display(self.live)

                # Start ping task
                ping_task = asyncio.create_task(self.send_ping(websocket, proxy_info.get('ip', 'Unknown')))
                
                try:
                    await self.handle_websocket(websocket, user_id, proxy_info.get('ip', 'Unknown'))
                finally:
                    ping_task.cancel()
                    if websocket and not websocket.closed:
                        await websocket.close()
                    if session:
                        await session.close()

            except Exception as e:
                self.display.add_error(f"Connection error with proxy {proxy}: {str(e)}", proxy)
                if websocket and not websocket.closed:
                    await websocket.close()
                if session:
                    await session.close()
            
            self.display.update_display(self.live)
            await asyncio.sleep(self.config.retry_interval)

    async def connect_directly(self, user_id: str):
        while True:
            try:
                websocket = await self.create_websocket_connection()
                print(f"{Fore.CYAN}Connected directly without proxy")

                proxy_info = await self.get_proxy_ip(None)
                ip = proxy_info.get('ip', 'Direct IP') if proxy_info else 'Direct IP'

                ping_task = asyncio.create_task(self.send_ping(websocket, ip))
                await self.handle_websocket(websocket, user_id, ip)
                ping_task.cancel()

            except Exception as e:
                print(f"{Fore.RED}Failed to connect directly: {str(e)}")
            
            await asyncio.sleep(self.config.retry_interval)