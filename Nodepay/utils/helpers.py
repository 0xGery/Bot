import asyncio
from datetime import datetime

async def read_file(filepath):
    try:
        with open(filepath, 'r') as file:
            return [line.strip() for line in file if line.strip()]
    except Exception as e:
        raise Exception(f"Failed to read {filepath}: {str(e)}")

def parse_proxy(proxy_line):
    try:
        host, port, username, password = proxy_line.split(':')
        return {
            'host': host,
            'port': port,
            'username': username,
            'password': password
        }
    except ValueError:
        raise Exception(f"Invalid proxy format: {proxy_line}")

def get_timestamp():
    return datetime.now().strftime('%H:%M:%S')