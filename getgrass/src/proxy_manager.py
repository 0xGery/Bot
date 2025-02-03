import json
import os
from colorama import Fore

# Get the absolute path to the project root directory
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

async def read_lines(filename: str) -> list[str]:
    try:
        # Handle path resolution
        if os.path.isabs(filename):
            file_path = filename
        else:
            file_path = os.path.join(ROOT_DIR, filename)

        if not os.path.exists(file_path):
            print(f'{Fore.RED}File not found: {file_path}')
            return []
            
        with open(file_path, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]
            print(f'{Fore.GREEN}Successfully loaded {len(lines)} lines from {filename}')
            return lines
    except Exception as e:
        print(f'{Fore.RED}Failed to read {filename}: {str(e)}')
        return []

def auto_detect_proxy_source() -> dict:
    default_proxy_path = 'data/proxy.txt'
    file_path = os.path.join(ROOT_DIR, default_proxy_path)
    
    if os.path.exists(file_path):
        # Check if file has content
        try:
            with open(file_path, 'r') as f:
                content = f.read().strip()
                if content:  # If file has content
                    return {'type': 'file', 'source': default_proxy_path}
        except Exception:
            pass
    
    # If no proxy file or empty file, use direct connection
    return {'type': 'none'}

# Only keep this line for exports
__all__ = ['read_lines', 'auto_detect_proxy_source']