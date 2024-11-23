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
        header_table.add_row("")  # Empty line for spacing
        header_table.add_row("[cyan bold]Automated Network Monitoring System")
        header_table.add_row("[cyan bold]Author: Nullx")
        
        header = Panel(
            header_table,
            title="[bold cyan]NULL X SYSTEM",
            border_style="cyan",
            box=box.ROUNDED,
            padding=(1, 2),
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
        for activity in self.recent_activity[-5:]:
            timestamp = f"[{activity['time'].strftime('%H:%M:%S')}]"
            status = "✓" if activity.get('success', False) else "✗"
            status_style = "green bold" if activity.get('success', False) else "red bold"
            activity_text.append(timestamp, style="cyan")
            activity_text.append(f" {status} ", style=status_style)
            activity_text.append(f"{activity['message']}\n")
        activity = Panel(activity_text or "No recent activity", title="[bold cyan]RECENT ACTIVITY", border_style="blue")

        # Enhanced proxy status panel
        proxy_table = Table(box=box.SIMPLE, show_header=False, pad_edge=False)
        proxy_table.add_column("Proxy", style="cyan")
        proxy_table.add_column("Status", style="green")
        for proxy, stats in self.proxy_stats.items():
            success_rate = (stats["success"] / stats["total"]) * 100 if stats["total"] > 0 else 0
            status_style = "green bold" if success_rate > 90 else "yellow bold" if success_rate > 50 else "red bold"
            proxy_table.add_row(
                f"{proxy[:30]}...",
                Text(f"Active ({success_rate:.1f}%)", style=status_style)
            )
        proxies = Panel(proxy_table or "No active proxies", title="[bold cyan]PROXY STATUS", border_style="blue")

        # Combine all panels with spacing
        layout.split(
            Layout(header, size=7),
            Layout(metrics, size=8),
            Layout(network, size=6),
            Layout(activity, size=8),
            Layout(proxies)
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
        self.recent_activity = self.recent_activity[-5:]  # Keep only last 5 activities
        
        if activity_data.get('success', False):
            self.last_success = activity_data['time'].strftime('%H:%M:%S')

    def add_error(self, error_message: str, proxy: str = None):
        self.recent_activity.append({
            'time': datetime.now(),
            'success': False,
            'message': error_message,
            'status': 'Failed'
        })
        self.recent_activity = self.recent_activity[-5:]
        self.failed_pings += 1
        self.log_failed_ping(error_message, proxy)  

    def update_stats(self, success: bool, proxy: str):
        self.total_pings += 1
        if not success:
            self.failed_pings += 1
        
        if proxy not in self.proxy_stats:
            self.proxy_stats[proxy] = {"total": 0, "success": 0}
        
        self.proxy_stats[proxy]["total"] += 1
        if success:
            self.proxy_stats[proxy]["success"] += 1