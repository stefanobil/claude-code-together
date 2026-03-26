import os
import sys

# Ensure the project root is in path
sys.path.append(os.getcwd())

from logger_manager import log_trade, log_error, get_performance_summary
from rich.console import Console
from rich.panel import Panel

console = Console()

def test_logging_system():
    console.print(Panel("🧪 Initializing V7.0 Auditor Test Suite", style="bold magenta"))
    
    # 1. Test Trade Entry Logging
    console.print("[cyan]Testing Trade Entry Logging...[/cyan]")
    log_trade(
        symbol="BTC/USDT",
        side="LONG",
        type_trade="🚀 DIRECTIONNEL",
        entry_price=65000.0,
        exit_price=0.0,
        pnl_usd=0.0,
        pnl_pct=0.0,
        duration=0,
        reason="Test: SMC Demand Zone + ADX > 25"
    )
    console.print("[green]✅ Entry Logged.[/green]")

    # 2. Test Trade Exit Logging
    console.print("[cyan]Testing Trade Exit Logging...[/cyan]")
    log_trade(
        symbol="BTC/USDT",
        side="LONG",
        type_trade="EXIT",
        entry_price=65000.0,
        exit_price=67000.0,
        pnl_usd=2000.0,
        pnl_pct=3.07,
        duration=3600,
        reason="Test: Hit Take Profit"
    )
    console.print("[green]✅ Exit Logged.[/green]")

    # 3. Test Error Logging
    console.print("[cyan]Testing Error Logging...[/cyan]")
    log_error("TEST_MODULE", "This is a simulated system audit error.", critical=False)
    console.print("[green]✅ Error Logged.[/green]")

    # 4. Verify Performance Summary
    console.print("[cyan]Fetching Performance Summary...[/cyan]")
    perf = get_performance_summary()
    console.print(Panel(str(perf), title="📊 Performance Audit Result", style="bold green"))

    if perf['total_trades'] > 0:
        console.print("[bold yellow]🎉 V7.0 LOGGING SYSTEM VERIFIED![/bold yellow]")
    else:
        console.print("[bold red]❌ Verification Failed: No trades found in logs.[/bold red]")

if __name__ == "__main__":
    test_logging_system()
