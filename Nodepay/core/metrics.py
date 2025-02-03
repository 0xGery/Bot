import time
import psutil
from collections import deque
from datetime import datetime, timedelta

class MetricsCollector:
    def __init__(self, max_history=1000):
        self.response_times = deque(maxlen=max_history)
        self.error_history = deque(maxlen=max_history)
        self.proxy_performance = {}
        self.start_time = datetime.now()

    def add_response_time(self, duration, proxy_host=None):
        self.response_times.append(duration)
        if proxy_host:
            if proxy_host not in self.proxy_performance:
                self.proxy_performance[proxy_host] = deque(maxlen=100)
            self.proxy_performance[proxy_host].append(duration)

    def get_system_metrics(self):
        process = psutil.Process()
        return {
            'cpu_percent': process.cpu_percent(),
            'memory_usage': process.memory_info().rss / 1024 / 1024,  # MB
            'avg_response': self.get_average_response_time(),
            'uptime': (datetime.now() - self.start_time).total_seconds()
        }

    def get_average_response_time(self):
        return sum(self.response_times) / len(self.response_times) if self.response_times else 0