"""Start command implementation."""

import asyncio
import click
import pyperclip
from rich.console import Console
from rich.prompt import Prompt
import uvicorn

from ..lib.paths import ensure_paths
from ..lib.state import state
from ..lib.token import setup_github_token, setup_copilot_token
from ..lib.utils import cache_models, cache_vscode_version
from ..lib.shell import generate_env_script

console = Console()


async def run_server(
    port: int,
    verbose: bool,
    account_type: str,
    manual: bool,
    rate_limit: int = None,
    rate_limit_wait: bool = False,
    github_token: str = None,
    claude_code: bool = False,
    show_token: bool = False,
):
    """Run the Copilot API server."""
    if verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
        console.print("🔍 Verbose logging enabled", style="yellow")
    
    state.account_type = account_type
    if account_type != "individual":
        console.print(f"🏢 Using {account_type} plan GitHub account", style="blue")
    
    state.manual_approve = manual
    state.rate_limit_seconds = rate_limit
    state.rate_limit_wait = rate_limit_wait
    state.show_token = show_token
    
    await ensure_paths()
    await cache_vscode_version()
    
    if github_token:
        state.github_token = github_token
        console.print("🔑 Using provided GitHub token", style="green")
    else:
        await setup_github_token()
    
    await setup_copilot_token()
    await cache_models()
    
    if state.models:
        model_list = "\n".join(f"- {model['id']}" for model in state.models["data"])
        console.print(f"🤖 Available models:\n{model_list}", style="cyan")
    
    server_url = f"http://localhost:{port}"
    
    if claude_code and state.models:
        # Interactive model selection
        model_options = [model["id"] for model in state.models["data"]]
        
        console.print("🎯 Select a model to use with Claude Code:", style="bold")
        for i, model in enumerate(model_options, 1):
            console.print(f"  {i}. {model}")
        
        while True:
            try:
                choice = int(Prompt.ask("Enter choice")) - 1
                if 0 <= choice < len(model_options):
                    selected_model = model_options[choice]
                    break
                else:
                    console.print("❌ Invalid choice", style="red")
            except ValueError:
                console.print("❌ Please enter a number", style="red")
        
        console.print("🎯 Select a small model to use with Claude Code:", style="bold")
        for i, model in enumerate(model_options, 1):
            console.print(f"  {i}. {model}")
        
        while True:
            try:
                choice = int(Prompt.ask("Enter choice")) - 1
                if 0 <= choice < len(model_options):
                    selected_small_model = model_options[choice]
                    break
                else:
                    console.print("❌ Invalid choice", style="red")
            except ValueError:
                console.print("❌ Please enter a number", style="red")
        
        command = generate_env_script(
            {
                "ANTHROPIC_BASE_URL": server_url,
                "ANTHROPIC_AUTH_TOKEN": "dummy",
                "ANTHROPIC_MODEL": selected_model,
                "ANTHROPIC_SMALL_FAST_MODEL": selected_small_model,
            },
            "claude"
        )
        
        try:
            pyperclip.copy(command)
            console.print("📋 Copied Claude Code command to clipboard!", style="green")
        except Exception:
            console.print("⚠️  Failed to copy to clipboard. Here is the Claude Code command:", style="yellow")
            console.print(command, style="code")
    
    console.print(
        f"🌐 Usage Viewer: https://ericc-ch.github.io/copilot-api?endpoint={server_url}/usage",
        style="bold blue"
    )
    
    # Start the server
    config = uvicorn.Config(
        "copilot_api.server:app",
        host="0.0.0.0",
        port=port,
        log_level="info" if not verbose else "debug"
    )
    server = uvicorn.Server(config)
    await server.serve()


@click.command()
@click.option("--port", "-p", default=4141, help="Port to listen on")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--account-type", "-a", default="individual", 
              help="Account type (individual, business, enterprise)")
@click.option("--manual", is_flag=True, help="Enable manual request approval")
@click.option("--rate-limit", "-r", type=int, help="Rate limit in seconds between requests")
@click.option("--wait", "-w", is_flag=True, 
              help="Wait instead of error when rate limit is hit")
@click.option("--github-token", "-g", help="Provide GitHub token directly")
@click.option("--claude-code", "-c", is_flag=True, 
              help="Generate command to launch Claude Code with Copilot API config")
@click.option("--show-token", is_flag=True, 
              help="Show GitHub and Copilot tokens on fetch and refresh")
def start_command(port, verbose, account_type, manual, rate_limit, wait, 
                 github_token, claude_code, show_token):
    """Start the Copilot API server."""
    asyncio.run(run_server(
        port=port,
        verbose=verbose,
        account_type=account_type,
        manual=manual,
        rate_limit=rate_limit,
        rate_limit_wait=wait,
        github_token=github_token,
        claude_code=claude_code,
        show_token=show_token,
    ))