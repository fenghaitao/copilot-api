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


async def run_check_usage(verbose: bool, show_token: bool, since: str = None, until: str = None, history: bool = False):
    """Check Copilot usage statistics."""
    if verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
        console.print("🔍 Verbose logging enabled", style="yellow")
    
    state.show_token = show_token
    
    await ensure_paths()
    await setup_github_token()
    
    try:
        # If history flag is set, show last 3 months (but limited to 28 days per GitHub API)
        if history:
            from datetime import datetime, timedelta
            today = datetime.now()
            months_data = []
            
            # GitHub API only supports 28 days lookback, so we'll show current month and previous month
            for i in range(2):  # Changed from 3 to 2 months
                if i == 0:
                    # Current month
                    month_start = today.replace(day=1)
                    month_end = today
                else:
                    # Previous month
                    first_of_current = today.replace(day=1)
                    month_end = first_of_current - timedelta(days=1)
                    month_start = month_end.replace(day=1)
                
                since_str = month_start.strftime("%Y-%m-%d")
                until_str = month_end.strftime("%Y-%m-%d")
                
                console.print(f"\n📅 Fetching usage for {month_start.strftime('%B %Y')}...", style="cyan")
                try:
                    usage_data = await get_copilot_usage(since_str, until_str)
                    months_data.append((month_start.strftime('%B %Y'), usage_data))
                except Exception as e:
                    if verbose:
                        console.print(f"  ⚠️  Error: {e}", style="yellow")
                    else:
                        # Show first line of error only
                        error_msg = str(e).split('\n')[0]
                        console.print(f"  ⚠️  {error_msg}", style="yellow")
                    months_data.append((month_start.strftime('%B %Y'), None))
            
            # Display all months in a table
            table = Table(title="Copilot Usage History")
            table.add_column("Month", style="cyan")
            table.add_column("Active Users", justify="right")
            table.add_column("Engaged Users", justify="right")
            
            for month_name, data in months_data:
                if data is None:
                    table.add_row(month_name, "Error", "Error")
                elif isinstance(data, list) and len(data) > 0:
                    # Sum up daily metrics for the month
                    total_active = sum(d.get("total_active_users", 0) for d in data)
                    total_engaged = sum(d.get("total_engaged_users", 0) for d in data)
                    # Calculate average per day
                    avg_active = total_active / len(data) if len(data) > 0 else 0
                    avg_engaged = total_engaged / len(data) if len(data) > 0 else 0
                    table.add_row(
                        month_name, 
                        f"{avg_active:.1f} avg/day",
                        f"{avg_engaged:.1f} avg/day"
                    )
                else:
                    table.add_row(month_name, "N/A", "N/A")
            
            console.print(table)
            return
        
        # Date range query
        if since or until:
            usage_data = await get_copilot_usage(since, until)
            
            if isinstance(usage_data, list):
                table = Table(title="Copilot Usage Metrics")
                table.add_column("Date", style="cyan")
                table.add_column("Active Users", justify="right")
                table.add_column("Engaged Users", justify="right")
                
                for day_data in usage_data:
                    table.add_row(
                        day_data.get("date", "N/A"),
                        str(day_data.get("total_active_users", 0)),
                        str(day_data.get("total_engaged_users", 0))
                    )
                
                console.print(table)
                
                if verbose:
                    console.print("\n📊 Raw usage data:", style="yellow")
                    console.print(usage_data)
                return
        
        # Default: current month quota
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
@click.option("--since", help="Show usage since this date (YYYY-MM-DD, max 28 days ago)")
@click.option("--until", help="Show usage until this date (YYYY-MM-DD)")
@click.option("--history", is_flag=True, help="Show monthly usage history (last 2 months, requires org owner/billing permissions)")
def check_usage_command(verbose, show_token, since, until, history):
    """Check GitHub Copilot usage statistics."""
    asyncio.run(run_check_usage(verbose, show_token, since, until, history))