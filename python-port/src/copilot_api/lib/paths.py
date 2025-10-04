"""Path management for configuration files."""

import os
from pathlib import Path
from typing import Dict


class Paths:
    """Manages configuration file paths."""
    
    def __init__(self):
        # Use XDG Base Directory specification or fallback to home directory
        config_home = os.environ.get('XDG_CONFIG_HOME')
        if config_home:
            self.config_dir = Path(config_home) / "copilot-api"
        else:
            self.config_dir = Path.home() / ".config" / "copilot-api"
        
        self.github_token_path = self.config_dir / "github_token"
        self.vscode_version_path = self.config_dir / "vscode_version"
    
    def ensure_paths(self) -> None:
        """Ensure all necessary directories exist."""
        self.config_dir.mkdir(parents=True, exist_ok=True)


# Global paths instance
PATHS = Paths()


async def ensure_paths() -> None:
    """Async wrapper for path creation."""
    PATHS.ensure_paths()