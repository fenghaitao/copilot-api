"""Check usage command implementation."""

import asyncio
import click
from rich.console import Console
from rich.table import Table

from ..lib.paths import ensure_paths
from ..lib.state import state
from ..lib.token import setup_github_token
from ..services.github.get_copilot_usage import get_copilot_usage

console = Console()


async def run_check_usage(verbose: bool, show_token: bool):
    """Check Copilot usage statistics."""
    if verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
        console.print("🔍 Verbose logging enabled", style="yellow")
    
    state.show_token = show_token
    
    await ensure_paths()
    await setup_github_token()
    
    try:
        usage_data = await get_copilot_usage()
        
        # Extract quota information (matching TypeScript implementation)
        quota_snapshots = usage_data.get("quota_snapshots", {})
        premium = quota_snapshots.get("premium_interactions", {})
        chat = quota_snapshots.get("chat", {})
        completions = quota_snapshots.get("completions", {})
        
        # Calculate premium usage
        premium_total = premium.get("entitlement", 0)
        premium_remaining = premium.get("remaining", 0)
        premium_used = premium_total - premium_remaining
        premium_percent_used = (premium_used / premium_total * 100) if premium_total > 0 else 0
        premium_percent_remaining = premium.get("percent_remaining", 0)
        
        def summarize_quota(name: str, quota_data: dict) -> str:
            """Summarize quota data similar to TypeScript version."""
            if not quota_data:
                return f"{name}: N/A"
            
            total = quota_data.get("entitlement", 0)
            remaining = quota_data.get("remaining", 0)
            used = total - remaining
            percent_used = (used / total * 100) if total > 0 else 0
            percent_remaining = quota_data.get("percent_remaining", 0)
            
            return f"{name}: {used}/{total} used ({percent_used:.1f}% used, {percent_remaining:.1f}% remaining)"
        
        # Format the output similar to TypeScript version
        plan = usage_data.get("copilot_plan", "Unknown")
        reset_date = usage_data.get("quota_reset_date", "Unknown")
        
        premium_line = f"Premium: {premium_used}/{premium_total} used ({premium_percent_used:.1f}% used, {premium_percent_remaining:.1f}% remaining)"
        chat_line = summarize_quota("Chat", chat)
        completions_line = summarize_quota("Completions", completions)
        
        # Create a panel similar to the TypeScript box output
        from rich.panel import Panel
        
        usage_content = (
            f"Copilot Usage (plan: {plan})\n"
            f"Quota resets: {reset_date}\n\n"
            f"Quotas:\n"
            f"  {premium_line}\n"
            f"  {chat_line}\n"
            f"  {completions_line}"
        )
        
        console.print(Panel(usage_content, title="GitHub Copilot Usage", border_style="green"))
        
        if verbose:
            console.print("\n📊 Raw usage data:", style="yellow")
            console.print(usage_data)
        
    except Exception as error:
        console.print(f"❌ Failed to get usage data: {error}", style="red")
        raise error


@click.command()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--show-token", is_flag=True, help="Show GitHub token")
def check_usage_command(verbose, show_token):
    """Check GitHub Copilot usage statistics."""
    asyncio.run(run_check_usage(verbose, show_token))