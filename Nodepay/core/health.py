from datetime import datetime
import aiohttp
import asyncio

class HealthChecker:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.health_status = {}

    async def check_proxy_health(self, proxy):
        try:
            start_time = datetime.now()
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.config.IP_CHECK_URL,
                    proxy=proxy['url'],
                    timeout=5
                ) as response:
                    if response.status == 200:
                        response_time = (datetime.now() - start_time).total_seconds() * 1000
                        self.health_status[proxy['host']] = {
                            'status': 'healthy',
                            'last_check': datetime.now(),
                            'response_time': response_time
                        }
                        return True
        except Exception as e:
            self.health_status[proxy['host']] = {
                'status': 'unhealthy',
                'last_check': datetime.now(),
                'error': str(e)
            }
            return False

    def get_health_report(self):
        return self.health_status