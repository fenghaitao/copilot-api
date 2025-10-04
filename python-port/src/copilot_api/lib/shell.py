"""Shell command generation utilities."""

import os
from typing import Dict


def generate_env_script(env_vars: Dict[str, str], command: str) -> str:
    """Generate shell script to set environment variables and run command."""
    if os.name == "nt":  # Windows
        env_lines = [f"set {key}={value}" for key, value in env_vars.items()]
        return "\n".join(env_lines + [command])
    else:  # Unix-like systems
        env_lines = [f"export {key}='{value}'" for key, value in env_vars.items()]
        return "\n".join(env_lines + [command])