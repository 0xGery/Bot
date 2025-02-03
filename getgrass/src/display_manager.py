import os
from datetime import datetime
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.text import Text
from rich.style import Style

class DisplayManager:
    def __init__(self):
        self.console = Console()
        self.start_time = datetime.now()
        self.total_pings = 0
        self.failed_pings = 0
        self.last_success = None
        self.recent_activity = []
        self.proxy_stats = {}
        self.active_proxies = 0
        self.errors = []
        self.is_running = True
        self.total_proxies = 0
        self.used_proxies = set()
        
        # Ensure data directory exists
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        self.error_log_path = os.path.join(self.data_dir, 'error.log')

    def normalize_proxy(self, proxy: str) -> str:
        """Normalize proxy string to consistent format."""
        if not proxy:
            return proxy
        # Extract just the host:port if it's a full URL
        if '@' in proxy:
            return proxy.split('@')[-1].split(':')[0]
        return proxy.split(':')[0]

    def generate_layout(self) -> Layout:
        layout = Layout()
        
        # Create header using Table for perfect centering
        header_table = Table(
            show_header=False,
            box=None,
            padding=0,
            expand=True
        )
        header_table.add_column("", justify="center")
        header_table.add_row("[cyan bold]GetGrass Bot V.2.1")
        header_table.add_row("[cyan bold]Author: Nullx")
        
        header = Panel(
            header_table,
            title="[bold cyan]NULL X SYSTEM",
            border_style="cyan",
            box=box.ROUNDED,
            padding=(1, 1),
            expand=True
        )

        # Enhanced metrics panel
        metrics_table = Table(box=box.SIMPLE, show_header=False, pad_edge=False)
        metrics_table.add_column("Key", style="bold cyan")
        metrics_table.add_column("Value", style="green")
        metrics_table.add_row("Runtime", self.get_runtime())
        metrics_table.add_row("Total Pings", str(self.total_pings))
        metrics_table.add_row("Failed Pings", str(self.failed_pings))
        metrics_table.add_row("Success Rate", f"{self.get_success_rate()}%")
        metrics_table.add_row("Proxies", f"{len(self.used_proxies)}/{self.total_proxies}")
        metrics = Panel(metrics_table, title="[bold cyan]METRICS", border_style="blue")

        # Enhanced network status panel
        network_table = Table(box=box.SIMPLE, show_header=False, pad_edge=False)
        network_table.add_column("Key", style="bold cyan")
        network_table.add_column("Value", style="green")
        network_table.add_row("Last Success", self.last_success or "N/A")
        network_table.add_row("Active Mode", "Single Account")
        status_style = "green bold" if self.last_success else "red bold"
        network_table.add_row("Network State", Text("Connected" if self.last_success else "Disconnected", style=status_style))
        network = Panel(network_table, title="[bold cyan]NETWORK STATUS", border_style="blue")

        # Enhanced activity panel with colored status indicators
        activity_text = Text()
        for activity in self.recent_activity[-30:]:
            timestamp = f"[{activity['time'].strftime('%H:%M:%S')}]"
            status = "✓" if activity.get('success', False) else "✗"
            status_style = "green bold" if activity.get('success', False) else "red bold"
            activity_text.append(timestamp, style="cyan")
            activity_text.append(f" {status} ", style=status_style)
            activity_text.append(f"{activity['message']}\n")
        activity = Panel(activity_text or "No recent activity", title="[bold cyan]RECENT ACTIVITY", border_style="blue")

        # Enhanced proxy status panel with sorted proxies and inactive proxies
        proxy_table = Table(box=box.SIMPLE, show_header=True, pad_edge=False)
        proxy_table.add_column("Proxy", style="cyan", width=30)
        proxy_table.add_column("Success", style="green", justify="center")
        proxy_table.add_column("Total", style="blue", justify="center")
        proxy_table.add_column("Rate", style="yellow", justify="center")
        proxy_table.add_column("Status", style="green", justify="center")

        # Normalize proxy stats to prevent duplicates
        normalized_stats = {}
        for proxy, stats in self.proxy_stats.items():
            normalized_proxy = self.normalize_proxy(proxy)
            if normalized_proxy not in normalized_stats:
                normalized_stats[normalized_proxy] = stats.copy()  # Use copy to prevent reference issues
            else:
                # Combine stats if proxy appears in different formats
                normalized_stats[normalized_proxy]["total"] += stats["total"]
                normalized_stats[normalized_proxy]["success"] += stats["success"]

        # First add failed/poor performing proxies
        inactive_proxies = set()
        poor_proxies = []
        active_proxies = []

        for proxy, stats in normalized_stats.items():
            success_rate = (stats["success"] / stats["total"]) * 100 if stats["total"] > 0 else 0
            if success_rate < 50:  # Consider proxies with <50% success rate as poor
                poor_proxies.append((proxy, stats))
            else:
                active_proxies.append((proxy, stats))

        # Add any unused proxies to inactive
        for proxy in self.used_proxies:
            normalized_proxy = self.normalize_proxy(proxy)
            if normalized_proxy not in normalized_stats:
                inactive_proxies.add(normalized_proxy)

        # Add inactive proxies first
        for proxy in inactive_proxies:
            proxy_table.add_row(
                proxy,
                "0",
                "0",
                "0.0%",
                Text("Inactive", style="red bold")
            )

        # Then add poor performing proxies
        for proxy, stats in poor_proxies:
            success_rate = (stats["success"] / stats["total"]) * 100
            proxy_table.add_row(
                proxy,
                str(stats["success"]),
                str(stats["total"]),
                f"{success_rate:.1f}%",
                Text("Poor", style="red bold")
            )

        # Finally add active proxies sorted by success rate
        sorted_active = sorted(
            active_proxies,
            key=lambda x: (x[1]["success"] / x[1]["total"] if x[1]["total"] > 0 else -1),
            reverse=True  # Show best performing first
        )

        for proxy, stats in sorted_active:
            success_rate = (stats["success"] / stats["total"]) * 100
            status_text = (
                "Excellent" if success_rate > 90
                else "Good" if success_rate > 70
                else "Fair"
            )
            status_style = (
                "green bold" if success_rate > 90
                else "yellow bold" if success_rate > 70
                else "yellow"
            )
            
            proxy_table.add_row(
                proxy,
                str(stats["success"]),
                str(stats["total"]),
                f"{success_rate:.1f}%",
                Text(status_text, style=status_style)
            )

        working_proxies = len(active_proxies)
        total_inactive = len(inactive_proxies) + len(poor_proxies)

        proxies = Panel(
            proxy_table or "No active proxies", 
            title="[bold cyan]PROXY STATUS", 
            border_style="blue",
            subtitle=f"[cyan]Working: {working_proxies}/{self.total_proxies} │ Failed/Inactive: {total_inactive}"
        )

        # Combine all panels with spacing
        layout.split(
            Layout(header, size=6),
            Layout(metrics, size=8),
            Layout(network, size=6),
            Layout(proxies, size=20),
            Layout(activity)
        )

        return layout

    def get_runtime(self):
        delta = datetime.now() - self.start_time
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def get_success_rate(self):
        if self.total_pings == 0:
            return "0.00"
        return f"{((self.total_pings - self.failed_pings) / self.total_pings * 100):.2f}"

    def update_display(self, live):
        try:
            if live and self.is_running:
                live.update(self.generate_layout())
        except Exception as e:
            print(f"Display update error: {str(e)}")

    def add_activity(self, activity_data: dict):
        self.recent_activity.append(activity_data)
        self.recent_activity = self.recent_activity[-30:]  # Keep only last 30 activities
        
        if activity_data.get('success', False):
            self.last_success = activity_data['time'].strftime('%H:%M:%S')

    def log_error(self, error_message: str, proxy: str = None):
        """Log error to file with timestamp and proxy info"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        proxy_info = f" [Proxy: {proxy}]" if proxy else ""
        log_entry = f"[{timestamp}]{proxy_info} {error_message}\n"
        
        try:
            with open(self.error_log_path, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Failed to write to error log: {str(e)}")

    def add_error(self, error_message: str, proxy: str = None):
        # Log to file
        self.log_error(error_message, proxy)
        
        # Add to display
        self.recent_activity.append({
            'time': datetime.now(),
            'success': False,
            'message': error_message,
            'status': 'Failed'
        })
        self.recent_activity = self.recent_activity[-30:]
        self.failed_pings += 1
        
        # Update proxy stats if proxy is provided
        if proxy:
            if proxy not in self.proxy_stats:
                self.proxy_stats[proxy] = {"total": 0, "success": 0}
            self.proxy_stats[proxy]["total"] += 1

    def update_stats(self, success: bool, proxy: str):
        self.total_pings += 1
        if not success:
            self.failed_pings += 1
        
        if proxy not in self.proxy_stats:
            self.proxy_stats[proxy] = {"total": 0, "success": 0}
        
        self.proxy_stats[proxy]["total"] += 1
        if success:
            self.proxy_stats[proxy]["success"] += 1