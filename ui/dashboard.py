import time
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from core.provider import Provider

console = Console(legacy_windows=False)

class Dashboard:
    def __init__(self, phone_str: str, mode: str, total_providers: int):
        self.phone_str = phone_str
        self.mode = mode.upper()
        self.total_providers = total_providers

    def print_target_info(self, concurrency: int, rounds: int, proxy_count: int):
        table = Table(title="[bold yellow]Target Configuration[/bold yellow]", border_style="cyan")
        table.add_column("Parameter", style="bright_white", justify="left")
        table.add_column("Value", style="bold green", justify="left")

        table.add_row("Target Phone", self.phone_str)
        table.add_row("Attack Mode", f"[bold magenta]{self.mode}[/bold magenta]")
        table.add_row("Loaded Providers", str(self.total_providers))
        table.add_row("Concurrency Limit", str(concurrency))
        table.add_row("Rounds", "Infinite (Loop)" if rounds <= 0 else str(rounds))
        table.add_row("Active Proxies", f"{proxy_count} Loaded" if proxy_count > 0 else "Direct (No Proxy)")

        console.print(table)
        console.print()

    def log_result(self, provider: Provider, success: bool, status_code: int, latency_ms: float, error_msg: str = None):
        type_badge = "[bold yellow] CALL [/bold yellow]" if provider.type == "call" else "[bold cyan] SMS  [/bold cyan]"
        
        if success:
            status_badge = f"[bold green][OK] ({status_code})[/bold green]"
        else:
            reason = error_msg if error_msg else str(status_code)
            status_badge = f"[bold red][FAIL] ({reason})[/bold red]"

        latency_text = f"[bright_black]{latency_ms:>6.1f}ms[/bright_black]"
        prov_name = f"[bold white]{provider.name:<22}[/bold white]"

        timestamp = time.strftime("%H:%M:%S")
        console.print(f"[bright_black][{timestamp}][/bright_black] {type_badge} {prov_name} {status_badge} {latency_text}")

    def print_summary(self, stats):
        table = Table(title="[bold green]═══ Execution Summary ═══[/bold green]", border_style="green")
        table.add_column("Metric", style="bright_white")
        table.add_column("Score", style="bold yellow")

        table.add_row("Total Requests Sent", str(stats.total_sent))
        table.add_row("Successful Requests", f"[green]{stats.success}[/green]")
        table.add_row("Failed Requests", f"[red]{stats.failed}[/red]")
        table.add_row("Call OTP Triggered", f"[yellow]{stats.call_success} OK[/yellow] / [red]{stats.call_failed} Fail[/red]")
        table.add_row("SMS OTP Triggered", f"[cyan]{stats.sms_success} OK[/cyan] / [red]{stats.sms_failed} Fail[/red]")
        table.add_row("Total Elapsed Time", f"{stats.elapsed:.2f}s")
        table.add_row("Throughput Speed", f"{stats.req_per_sec:.2f} req/s")

        console.print()
        console.print(table)
