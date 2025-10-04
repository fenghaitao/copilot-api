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
        
        # Create a table to display usage information
        table = Table(title="GitHub Copilot Usage")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        # Add rows based on available data
        if "total_suggestions_count" in usage_data:
            table.add_row("Total Suggestions", str(usage_data["total_suggestions_count"]))
        
        if "total_acceptances_count" in usage_data:
            table.add_row("Total Acceptances", str(usage_data["total_acceptances_count"]))
        
        if "total_lines_suggested" in usage_data:
            table.add_row("Total Lines Suggested", str(usage_data["total_lines_suggested"]))
        
        if "total_lines_accepted" in usage_data:
            table.add_row("Total Lines Accepted", str(usage_data["total_lines_accepted"]))
        
        # Calculate acceptance rate if data is available
        if "total_suggestions_count" in usage_data and "total_acceptances_count" in usage_data:
            suggestions = usage_data["total_suggestions_count"]
            acceptances = usage_data["total_acceptances_count"]
            if suggestions > 0:
                acceptance_rate = (acceptances / suggestions) * 100
                table.add_row("Acceptance Rate", f"{acceptance_rate:.1f}%")
        
        console.print(table)
        
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