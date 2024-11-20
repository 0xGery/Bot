import asyncio
import colorama
from config.settings import AppConfig
from config.logger import setup_logger
from core.monitor import SentinelMonitor
from utils.interface import display_header, show_menu, render_dashboard, loading_animation
from utils.helpers import read_file, parse_proxy
from colorama import Fore, Style
from utils.cli import parse_arguments
from config.validator import ConfigValidator
from core.metrics import MetricsCollector
from core.health import HealthChecker

colorama.init()

# Create logger at module level
logger = setup_logger()

async def initialize_bot():
    """Initialize bot with configuration"""
    return SentinelMonitor(AppConfig, logger)

async def load_resources():
    """Load tokens and proxies"""
    tokens = await read_file(AppConfig.TOKEN_FILE)
    proxy_lines = await read_file(AppConfig.PROXY_FILE)
    proxies = [parse_proxy(line) for line in proxy_lines]
    return tokens, proxies

async def main():
    try:
        args = parse_arguments()
        config = ConfigValidator.validate_config(args.config)
        ConfigValidator.validate_files()
        
        # Initialize components
        metrics = MetricsCollector()
        health_checker = HealthChecker(AppConfig, logger)
        
        display_header()
        mode = await show_menu()
        
        await loading_animation("Initializing system")
        bot = await initialize_bot()
        
        # Set the mode in stats
        bot.stats['mode'] = mode
        
        tokens, proxies = await load_resources()
        
        tasks = []
        if mode == "Single Account":
            token = tokens[0]
            for proxy in proxies:
                tasks.append(asyncio.create_task(bot.run(token, proxy)))
        else:
            if len(tokens) < 2:
                print(f"{Fore.RED}✗ Multi-Account mode requires multiple accounts{Style.RESET_ALL}")
                return
                
            for i, token in enumerate(tokens):
                proxy = proxies[i] if i < len(proxies) else None
                tasks.append(asyncio.create_task(bot.run(token, proxy)))

        # Start dashboard update task
        async def update_dashboard():
            while True:
                render_dashboard(bot.stats, bot.current_status)
                await asyncio.sleep(AppConfig.DASHBOARD_UPDATE_INTERVAL)

        tasks.append(asyncio.create_task(update_dashboard()))
        
        await asyncio.gather(*tasks)

    except KeyboardInterrupt:
        print(f"\n{Fore.GREEN}✓ Shutting down gracefully...{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}✗ Fatal error: {str(e)}{Style.RESET_ALL}")

if __name__ == "__main__":
    asyncio.run(main())