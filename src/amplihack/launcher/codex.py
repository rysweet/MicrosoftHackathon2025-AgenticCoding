"""Codex CLI launcher - wrapper around OpenAI Codex command."""

import json
import os
import subprocess
from pathlib import Path
from typing import List, Optional


def check_codex() -> bool:
    """Check if Codex CLI is installed."""
    try:
        subprocess.run(["codex", "--version"], capture_output=True, timeout=5, check=False)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def install_codex() -> bool:
    """Install OpenAI Codex CLI via npm."""
    print("Installing OpenAI Codex CLI...")
    try:
        result = subprocess.run(["npm", "install", "-g", "@openai/codex-cli"], check=False)
        if result.returncode == 0:
            print("✓ Codex CLI installed")
            return True
        print("✗ Installation failed")
        return False
    except FileNotFoundError:
        print("Error: npm not found. Install Node.js first.")
        return False


def configure_codex() -> bool:
    """Configure Codex CLI with approval_mode: auto.

    Creates or updates ~/.openai/codex/config.json to set approval_mode to auto.

    Returns:
        True if configuration succeeded, False otherwise
    """
    try:
        config_dir = Path.home() / ".openai" / "codex"
        config_file = config_dir / "config.json"

        # Create config directory if it doesn't exist
        config_dir.mkdir(parents=True, exist_ok=True)

        # Read existing config or create new one
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
        else:
            config = {}

        # Set approval_mode to auto if not already set
        if config.get("approval_mode") != "auto":
            config["approval_mode"] = "auto"

            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)

            print("✓ Codex configured with approval_mode: auto")
            return True

        print("Codex already configured")
        return True

    except Exception as e:
        print(f"Warning: Failed to configure Codex: {e}")
        return False


def launch_codex(args: Optional[List[str]] = None, interactive: bool = True) -> int:
    """Launch Codex CLI.

    Args:
        args: Arguments to pass to codex exec
        interactive: If True, exec to replace process

    Returns:
        Exit code (only for non-interactive mode)
    """
    # Ensure codex is installed
    if not check_codex():
        if not install_codex() or not check_codex():
            print("Failed to install Codex CLI")
            return 1

    # Auto-configure approval mode
    configure_codex()

    # Build command - Codex uses "codex exec" for command execution
    cmd = ["codex"]

    # If args contain a prompt (via -p flag or direct prompt), use exec command
    if args:
        # Check if this is a direct exec prompt
        if "-p" in args:
            # Remove -p flag and extract prompt
            idx = args.index("-p")
            if idx + 1 < len(args):
                prompt = args[idx + 1]
                cmd.extend(["exec", prompt])
                # Add any remaining args after the prompt
                if idx + 2 < len(args):
                    cmd.extend(args[idx + 2 :])
            else:
                print("Error: -p flag requires a prompt argument")
                return 1
        else:
            # Pass args directly to codex
            cmd.extend(args)
    else:
        # Interactive mode without args - just launch codex
        pass

    # Launch
    if interactive and not args:
        # Interactive mode with no args - replace process
        os.execvp(cmd[0], cmd)  # Replace process - never returns
        # This line is unreachable but helps type checkers
        return 0  # pragma: no cover

    # Non-interactive mode or mode with args
    result = subprocess.run(cmd, check=False)
    return result.returncode
