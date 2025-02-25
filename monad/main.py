import asyncio
import random
from datetime import datetime, time, timedelta
from src.automation import MonadAutomation
from loguru import logger
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

def is_between_7am_10am():
    """Check if current time is between 7 AM and 10 AM"""
    now = datetime.now().time()
    start = time(7, 0)  # 7 AM
    end = time(10, 0)   # 10 AM
    return start <= now <= end

async def wait_until_next_run():
    """Wait until next run time (randomly between 7 AM and 10 AM tomorrow)"""
    now = datetime.now()
    tomorrow = now.date() + timedelta(days=1)
    
    # Generate random time between 7 AM and 10 AM
    random_hour = random.randint(7, 9)
    random_minute = random.randint(0, 59)
    next_run = datetime.combine(tomorrow, time(random_hour, random_minute))
    
    # Calculate wait time
    wait_seconds = (next_run - now).total_seconds()
    
    logger.info(f"{Fore.YELLOW}Next automation run scheduled for: {next_run.strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
    logger.info(f"{Fore.YELLOW}Waiting {wait_seconds/3600:.2f} hours...{Style.RESET_ALL}")
    
    await asyncio.sleep(wait_seconds)

async def main():
    first_run = True
    
    while True:
        try:
            # Run immediately on first start
            if first_run:
                logger.info(f"{Fore.MAGENTA}Starting initial Monad Random Pattern Automation{Style.RESET_ALL}")
                automation = MonadAutomation()
                await automation.run_automation()
                first_run = False
                # After first run, wait until next scheduled time
                await wait_until_next_run()
                continue
            
            # For subsequent runs, check the time window
            if is_between_7am_10am():
                logger.info(f"{Fore.MAGENTA}Starting Monad Random Pattern Automation{Style.RESET_ALL}")
                automation = MonadAutomation()
                await automation.run_automation()
                await wait_until_next_run()
            else:
                await wait_until_next_run()
                
        except Exception as e:
            logger.error(f"{Fore.RED}Error in main loop: {str(e)}{Style.RESET_ALL}")
            # Wait 5 minutes before retrying on error
            await asyncio.sleep(300)

if __name__ == "__main__":
    logger.info(f"{Fore.MAGENTA}Starting Monad Automation Service{Style.RESET_ALL}")
    asyncio.run(main()) 