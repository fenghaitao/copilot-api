"""Debug command implementation."""

import asyncio
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import sys
import platform

from ..lib.paths import ensure_paths, PATHS
from ..lib.state import state
from ..lib.token import setup_github_token, setup_copilot_token
from ..lib.utils import cache_models, cache_vscode_version
from ..services.github.get_user import get_github_user

console = Console()


async def run_debug(verbose: bool, show_token: bool):
    """Run debug diagnostics."""
    if verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
        console.print("🔍 Verbose logging enabled", style="yellow")
    
    state.show_token = show_token
    
    console.print("🔧 Running Copilot API Debug Diagnostics", style="bold blue")
    
    # System Information
    system_table = Table(title="System Information")
    system_table.add_column("Property", style="cyan")
    system_table.add_column("Value", style="green")
    
    system_table.add_row("Python Version", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    system_table.add_row("Platform", platform.platform())
    system_table.add_row("Architecture", platform.architecture()[0])
    system_table.add_row("Machine", platform.machine())
    
    console.print(system_table)
    console.print()
    
    # Configuration Paths
    paths_table = Table(title="Configuration Paths")
    paths_table.add_column("Path Type", style="cyan")
    paths_table.add_column("Location", style="green")
    paths_table.add_column("Exists", style="yellow")
    
    await ensure_paths()
    
    paths_table.add_row("Config Directory", str(PATHS.config_dir), "✅" if PATHS.config_dir.exists() else "❌")
    paths_table.add_row("GitHub Token", str(PATHS.github_token_path), "✅" if PATHS.github_token_path.exists() else "❌")
    paths_table.add_row("VS Code Version", str(PATHS.vscode_version_path), "✅" if PATHS.vscode_version_path.exists() else "❌")
    
    console.print(paths_table)
    console.print()
    
    # Authentication Status
    auth_status = Table(title="Authentication Status")
    auth_status.add_column("Service", style="cyan")
    auth_status.add_column("Status", style="green")
    auth_status.add_column("Details", style="yellow")
    
    try:
        await setup_github_token()
        github_status = "✅ Authenticated"
        try:
            user = await get_github_user()
            github_details = f"User: {user.get('login', 'Unknown')}"
        except Exception as e:
            github_details = f"Error getting user: {str(e)[:50]}..."
    except Exception as e:
        github_status = "❌ Failed"
        github_details = str(e)[:50] + "..." if len(str(e)) > 50 else str(e)
    
    auth_status.add_row("GitHub", github_status, github_details)
    
    try:
        await setup_copilot_token()
        copilot_status = "✅ Token Retrieved"
        copilot_details = "Active" if state.copilot_token else "No Token"
    except Exception as e:
        copilot_status = "❌ Failed"
        copilot_details = str(e)[:50] + "..." if len(str(e)) > 50 else str(e)
    
    auth_status.add_row("Copilot", copilot_status, copilot_details)
    
    console.print(auth_status)
    console.print()
    
    # Models and Version Information
    info_table = Table(title="Service Information")
    info_table.add_column("Service", style="cyan")
    info_table.add_column("Status", style="green")
    info_table.add_column("Details", style="yellow")
    
    try:
        await cache_vscode_version()
        version_status = "✅ Retrieved"
        version_details = f"Version: {state.vscode_version}"
    except Exception as e:
        version_status = "❌ Failed"
        version_details = str(e)[:50] + "..." if len(str(e)) > 50 else str(e)
    
    info_table.add_row("VS Code Version", version_status, version_details)
    
    try:
        await cache_models()
        if state.models and "data" in state.models:
            models_status = "✅ Retrieved"
            model_count = len(state.models["data"])
            models_details = f"{model_count} models available"
        else:
            models_status = "⚠️ No Data"
            models_details = "No models found"
    except Exception as e:
        models_status = "❌ Failed"
        models_details = str(e)[:50] + "..." if len(str(e)) > 50 else str(e)
    
    info_table.add_row("Models", models_status, models_details)
    
    console.print(info_table)
    
    # Available Models (if retrieved)
    if state.models and "data" in state.models and state.models["data"]:
        console.print()
        models_panel = Panel(
            "\n".join([f"• {model['id']}" for model in state.models["data"]]),
            title="Available Models",
            border_style="green"
        )
        console.print(models_panel)
    
    # State Information
    if verbose:
        console.print()
        state_table = Table(title="Internal State")
        state_table.add_column("Property", style="cyan")
        state_table.add_column("Value", style="green")
        
        state_table.add_row("Account Type", state.account_type)
        state_table.add_row("Manual Approve", str(state.manual_approve))
        state_table.add_row("Rate Limit Wait", str(state.rate_limit_wait))
        state_table.add_row("Rate Limit Seconds", str(state.rate_limit_seconds))
        state_table.add_row("Show Token", str(state.show_token))
        state_table.add_row("Has GitHub Token", str(bool(state.github_token)))
        state_table.add_row("Has Copilot Token", str(bool(state.copilot_token)))
        
        if state.show_token:
            if state.github_token:
                state_table.add_row("GitHub Token", f"{state.github_token[:10]}...")
            if state.copilot_token:
                state_table.add_row("Copilot Token", f"{state.copilot_token[:10]}...")
        
        console.print(state_table)
    
    console.print()
    console.print("✅ Debug diagnostics complete!", style="bold green")


@click.command()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging and show internal state")
@click.option("--show-token", is_flag=True, help="Show GitHub and Copilot tokens (truncated)")
def debug_command(verbose, show_token):
    """Run debug diagnostics and show system information."""
    asyncio.run(run_debug(verbose, show_token))