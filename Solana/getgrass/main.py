import asyncio
import os
from rich.live import Live
from rich.console import Console
from src.bot import Bot
from src.config import Config
from src.proxy_manager import read_lines, auto_detect_proxy_source
from src.display_manager import DisplayManager
from datetime import datetime
from colorama import Fore

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
console = Console()

def setup_sync():
    os.makedirs(DATA_DIR, exist_ok=True)
    proxy_source = auto_detect_proxy_source()
    if proxy_source['type'] == 'file':
        print(f"{Fore.CYAN}Found proxy list, using proxy mode")
    else:
        print(f"{Fore.CYAN}No proxy list found, using direct connection mode")
    return proxy_source

async def setup_async(proxy_source):
    proxies = []
    if proxy_source['type'] == 'file':
        proxies = await read_lines(proxy_source['source'])
        if not proxies:
            console.print("[red]No proxies found in the proxy file. Switching to direct connection...")
            proxy_source['type'] = 'none'
    
    user_ids = await read_lines('data/uid.txt')
    if not user_ids:
        console.print("[red]No user IDs found in data/uid.txt. Exiting...")
        return None, None

    return proxies, user_ids

async def main():
    try:
        # Clear the screen before starting
        os.system('clear' if os.name == 'posix' else 'cls')
        
        proxy_source = setup_sync()
        proxies, user_ids = await setup_async(proxy_source)
        if not user_ids:
            return

        display_manager = DisplayManager()
        display_manager.total_proxies = len(proxies) if proxy_source['type'] != 'none' else 1
        
        config = Config()
        bot = Bot(config, display_manager)

        # Create the Live display
        live = Live(
            display_manager.generate_layout(),
            refresh_per_second=4,
            screen=True,
            console=Console()
        )

        tasks = []
        try:
            # Start the live display
            live.start()
            bot.live = live
            
            # Debug log
            display_manager.add_activity({
                'time': datetime.now(),
                'success': True,
                'message': 'Starting bot with configuration...',
                'status': 'Starting'
            })
            display_manager.update_display(live)

            # Create tasks for each proxy and user ID combination
            for user_id in user_ids:
                if proxy_source['type'] != 'none':
                    for proxy in proxies:
                        task = asyncio.create_task(bot.connect_with_proxy(proxy, user_id))
                        tasks.append(task)
                else:
                    task = asyncio.create_task(bot.connect_directly(user_id))
                    tasks.append(task)

            display_manager.add_activity({
                'time': datetime.now(),
                'success': True,
                'message': f'Created {len(tasks)} connection tasks',
                'status': 'Starting'
            })
            display_manager.update_display(live)

            try:
                # Keep running until interrupted
                while display_manager.is_running:
                    # Update display
                    display_manager.update_display(live)
                    
                    # Wait for any completed tasks
                    done, pending = await asyncio.wait(
                        tasks, 
                        timeout=1,
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    # Check for failed tasks
                    for task in done:
                        if task.exception():
                            display_manager.add_error(f"Task failed: {str(task.exception())}")
                            # Recreate failed tasks
                            tasks = [t for t in tasks if t not in done]
                            tasks.extend(pending)
                    
                    # Short sleep to prevent CPU overuse
                    await asyncio.sleep(0.1)

            except KeyboardInterrupt:
                display_manager.is_running = False
                console.print("\n[yellow]Stopping bot...")
            finally:
                # Clean up
                display_manager.is_running = False
                for task in tasks:
                    if not task.done():
                        task.cancel()
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                live.stop()

        except Exception as e:
            console.print(f"[red]Error in main loop: {str(e)}")
            raise

    except Exception as e:
        console.print(f"[red]Setup error: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.set_debug(True)
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Bot stopped by user")
    except Exception as e:
        console.print(f"[red]Unexpected error: {str(e)}")
    finally:
        loop.close()