import os
import asyncio
from datetime import datetime
from colorama import Fore, Style
import time

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def display_header():
    clear_screen()
    print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════╗
               {Fore.WHITE}NodePay Sentinel v3.0.0{Fore.CYAN}                  
                                                          
  {Fore.WHITE}Automated Network Monitoring System{Fore.CYAN}                    
  {Fore.WHITE}Author: Nullx{Fore.CYAN}                                     
╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
""")

async def show_menu():
    print(f"\n{Fore.YELLOW}┌─ Operation Mode ─┐{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}│{Style.RESET_ALL} 1. Single Account{Fore.YELLOW}│{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}│{Style.RESET_ALL} 2. Multi-Account {Fore.YELLOW}│{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}└──────────────────┘{Style.RESET_ALL}")
    
    while True:
        choice = input(f"\n{Fore.CYAN}❯{Style.RESET_ALL} Select mode (1-2): ")
        if choice in ['1', '2']:
            return "Single Account" if choice == '1' else "Multi-Account"
        print(f"{Fore.RED}✗ Invalid choice. Try again.{Style.RESET_ALL}")

def format_uptime(start_time):
    uptime = datetime.now() - start_time
    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def render_dashboard(stats, status=None):
    clear_screen()
    display_header()
    
    # Calculate metrics
    uptime = format_uptime(stats['start_time'])
    success_rate = (stats['successful_pings'] / stats['total_pings'] * 100) if stats['total_pings'] > 0 else 0
    
    # Main Stats
    print(f"\n{Fore.CYAN}┌─────────────── SYSTEM METRICS ───────────────┐{Style.RESET_ALL}")
    print(f"{Fore.CYAN}│{Style.RESET_ALL} Runtime       : {Fore.GREEN}{uptime}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}│{Style.RESET_ALL} Total Pings   : {Fore.YELLOW}{stats['total_pings']}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}│{Style.RESET_ALL} Success Rate  : {Fore.GREEN}{success_rate:.1f}%{Style.RESET_ALL}")
    print(f"{Fore.CYAN}│{Style.RESET_ALL} Failed Pings  : {Fore.RED}{stats['failed_pings']}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}│{Style.RESET_ALL} Active Proxies: {Fore.GREEN}{len(stats['active_proxies'])}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}└──────────────────────────────────────────────┘{Style.RESET_ALL}")

    # Network Status
    print(f"\n{Fore.CYAN}┌─────────────── NETWORK STATUS ───────────────┐{Style.RESET_ALL}")
    print(f"{Fore.CYAN}│{Style.RESET_ALL} Last Success  : {Fore.GREEN}{stats.get('last_success', 'N/A')}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}│{Style.RESET_ALL} Active Mode   : {Fore.YELLOW}{stats.get('mode', 'Unknown')}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}│{Style.RESET_ALL} Network State : {Fore.GREEN}Connected{Style.RESET_ALL}")
    print(f"{Fore.CYAN}└──────────────────────────────────────────────┘{Style.RESET_ALL}")

    # Recent Activity Log
    if status:
        print(f"\n{Fore.CYAN}┌─────────────── RECENT ACTIVITY ──────────────┐{Style.RESET_ALL}")
        print(f"{status}")
        print(f"{Fore.CYAN}└──────────────────────────────────────────────┘{Style.RESET_ALL}")

    # Add Proxy Status section if there are active proxies
    if stats['active_proxies']:
        print(f"\n{Fore.CYAN}┌─────────────── PROXY STATUS ─────────────────┐{Style.RESET_ALL}")
        for proxy in list(stats['active_proxies'])[:3]:  # Show top 3 proxies
            proxy_stats = stats.get('proxy_stats', {}).get(proxy, {})
            print(f"{Fore.CYAN}│{Style.RESET_ALL} {proxy:<15} : {Fore.GREEN}Active{Style.RESET_ALL} ({proxy_stats.get('success_rate', 0):.1f}%)")
        if len(stats['active_proxies']) > 3:
            print(f"{Fore.CYAN}│{Style.RESET_ALL} ... and {len(stats['active_proxies'])-3} more")
        print(f"{Fore.CYAN}└──────────────────────────────────────────────┘{Style.RESET_ALL}")

async def loading_animation(message, duration=2):
    frames = ["◐", "◓", "◑", "◒"]
    end_time = time.time() + duration
    
    while time.time() < end_time:
        for frame in frames:
            print(f"\r{Fore.CYAN}{frame} {message}...{Style.RESET_ALL}", end="")
            await asyncio.sleep(0.1)
    print()
