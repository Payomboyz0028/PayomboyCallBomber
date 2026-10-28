from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console(legacy_windows=False)

BANNER_ART = r"""
██████╗  █████╗ ██╗   ██╗ ██████╗ ███╗   ███╗██████╗  ██████╗ ██╗   ██╗
██╔══██╗██╔══██╗╚██╗ ██╔╝██╔═══██╗████╗ ████║██╔══██╗██╔═══██╗╚██╗ ██╔╝
██████╔╝███████║ ╚████╔╝ ██║   ██║██╔████╔██║██████╔╝██║   ██║ ╚████╔╝ 
██╔═══╝ ██╔══██║  ╚██╔╝  ██║   ██║██║╚██╔╝██║██╔══██╗██║   ██║  ╚██╔╝  
██║     ██║  ██║   ██║   ╚██████╔╝██║ ╚═╝ ██║██████╔╝╚██████╔╝   ██║   
╚═╝     ╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═╝     ╚═╝╚═════╝  ╚═════╝    ╚═╝   
             [ CALL & SMS SECURITY STRESS-TEST ENGINE ]
"""

def print_banner():
    banner_text = Text(BANNER_ART, style="bold cyan")
    subtext = Text("  Engine: Python 3.11 Asyncio/HTTPX  •  Author: PayomboyZ RedTeam  •  v2.0.0\n", style="bold magenta")
    panel = Panel(
        banner_text + subtext,
        border_style="bright_blue",
        title="[bold green]>> PAYOMBOY CALL BOMBER <<[/bold green]",
        subtitle="[bold red]STRESS-TEST BENCH[/bold red]"
    )
    console.print(panel)
