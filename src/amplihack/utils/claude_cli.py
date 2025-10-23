"""Claude CLI installation and detection.

Auto-installs Claude CLI when missing, with smart path resolution and validation.

Philosophy:
- Auto-installation enabled by default (can be disabled with AMPLIHACK_AUTO_INSTALL=0)
- User-local npm installation to avoid permission issues
- Platform-aware path detection (user-local npm paths, homebrew, npm global, system paths)
- Validate binary execution before use
- Standard library only (no external dependencies)
- Supply chain protection via --ignore-scripts flag

Public API:
    get_claude_cli_path: Get path to Claude CLI, optionally auto-installing
    ensure_claude_cli: Ensure Claude CLI is available, raise on failure
"""

__all__ = [
    "get_claude_cli_path",
    "ensure_claude_cli",
]

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional


def _is_uvx_mode() -> bool:
    """Check if running in UVX mode.

    Returns:
        True if running via UVX deployment (detected by UVX detection module).
    """
    try:
        from .uvx_detection import is_uvx_deployment

        return is_uvx_deployment()
    except ImportError:
        # Fallback to environment variable check if uvx_detection not available
        return os.getenv("AMPLIHACK_UVX_MODE", "").lower() in ("1", "true", "yes")


def _configure_user_local_npm() -> dict[str, str]:
    """Configure npm to use user-local installation paths.

    Sets up environment variables to install npm packages in ~/.npm-global
    instead of requiring sudo/root access.

    Returns:
        Dictionary of environment variables for npm user-local installation.
    """
    user_npm_dir = Path.home() / ".npm-global"
    user_npm_bin = user_npm_dir / "bin"

    # Create directory if it doesn't exist
    user_npm_dir.mkdir(parents=True, exist_ok=True)
    user_npm_bin.mkdir(parents=True, exist_ok=True)

    # Create environment with npm prefix for user-local installation
    env = os.environ.copy()
    env["NPM_CONFIG_PREFIX"] = str(user_npm_dir)

    # Add user npm bin to PATH if not already there
    current_path = env.get("PATH", "")
    user_bin_str = str(user_npm_bin)
    if user_bin_str not in current_path:
        env["PATH"] = f"{user_bin_str}:{current_path}"
        # Update current process PATH so subsequent shutil.which() calls find the binary
        os.environ["PATH"] = env["PATH"]

    return env


def _find_claude_in_common_locations() -> Optional[str]:
    """Search for claude in PATH.

    Returns:
        Path to claude binary if found, None otherwise.
    """
    # Use shutil.which() to search PATH - this respects the user's environment
    return shutil.which("claude")


def _validate_claude_binary(claude_path: str) -> bool:
    """Validate that claude binary works.

    Args:
        claude_path: Path to claude binary to validate.

    Returns:
        True if binary is valid and executable.
    """
    try:
        result = subprocess.run(
            [claude_path, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
        return False


def _install_claude_cli() -> bool:
    """Install Claude CLI via npm using user-local installation.

    Returns:
        True if installation succeeded, False otherwise.
    """
    npm_path = shutil.which("npm")
    if not npm_path:
        print("ERROR: npm not found in PATH. Cannot install Claude CLI.")
        print("Please install Node.js and npm first:")
        print("  https://nodejs.org/")
        return False

    # Configure user-local npm environment
    env = _configure_user_local_npm()
    user_npm_bin = Path.home() / ".npm-global" / "bin"

    print("Installing Claude CLI via npm (user-local)...")
    print(f"Target directory: {user_npm_bin}")
    print("Running: npm install -g @anthropic-ai/claude-code --ignore-scripts")

    try:
        # Use --ignore-scripts for supply chain security
        # Install to user-local directory using --prefix flag (overrides any npm config)
        user_npm_dir = Path.home() / ".npm-global"
        result = subprocess.run(
            [npm_path, "install", "-g", "--prefix", str(user_npm_dir), "@anthropic-ai/claude-code", "--ignore-scripts"],
            env=env,
            capture_output=True,
            text=True,
            timeout=120,  # 2 minutes for npm install
        )

        if result.returncode == 0:
            # Verify binary is at expected location (where we told npm to install it)
            expected_binary = user_npm_bin / "claude"

            if not expected_binary.exists():
                # Binary not where expected - check actual npm prefix
                print(f"❌ Binary not found at expected location: {expected_binary}")
                try:
                    prefix_result = subprocess.run(
                        [npm_path, "config", "get", "prefix"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    actual_prefix = prefix_result.stdout.strip()
                    print(f"Actual npm prefix: {actual_prefix}")
                    print(f"Expected: {user_npm_dir}")
                except Exception:
                    print("Could not determine actual npm prefix")

                print("\nManual installation:")
                print('  export NPM_CONFIG_PREFIX="$HOME/.npm-global"')
                print("  npm install -g @anthropic-ai/claude-code --ignore-scripts")
                print('  export PATH="$HOME/.npm-global/bin:$PATH"')
                return False

            # Validate the binary is executable
            if not _validate_claude_binary(str(expected_binary)):
                print(f"❌ Binary exists but failed validation: {expected_binary}")
                print("The binary may not be executable or is corrupted.")
                return False

            print("✅ Claude CLI installed and validated successfully")
            print(f"Binary location: {expected_binary}")

            # Remind user to add to shell profile for future sessions
            print("\n💡 Add to your shell profile for future sessions:")
            print('  export PATH="$HOME/.npm-global/bin:$PATH"')

            return True

        # Sanitized error - details logged, not exposed to user
        print("❌ Claude CLI installation failed")
        print("Check npm configuration and permissions")
        print("\nManual installation:")
        print('  export NPM_CONFIG_PREFIX="$HOME/.npm-global"')
        print("  npm install -g @anthropic-ai/claude-code --ignore-scripts")
        print('  export PATH="$HOME/.npm-global/bin:$PATH"')
        return False

    except subprocess.TimeoutExpired:
        print("❌ Claude CLI installation timed out after 120 seconds")
        print("Try manually:")
        print('  export NPM_CONFIG_PREFIX="$HOME/.npm-global"')
        print("  npm install -g @anthropic-ai/claude-code --ignore-scripts")
        return False
    except Exception:
        print("❌ Unexpected error installing Claude CLI")
        print("Try manually:")
        print('  export NPM_CONFIG_PREFIX="$HOME/.npm-global"')
        print("  npm install -g @anthropic-ai/claude-code --ignore-scripts")
        return False


def get_claude_cli_path(auto_install: bool = True) -> Optional[str]:
    """Get path to Claude CLI binary, optionally installing if missing.

    Args:
        auto_install: If True, attempt to install Claude CLI if not found.

    Returns:
        Path to claude binary if available, None if not found/installed.
    """
    # First, try to find existing installation
    claude_path = _find_claude_in_common_locations()

    if claude_path and _validate_claude_binary(claude_path):
        return claude_path

    # If not found and auto-install is enabled, try to install
    if auto_install:
        # Auto-install is enabled by default
        # Can be explicitly disabled with AMPLIHACK_AUTO_INSTALL=0
        auto_install_disabled = os.getenv("AMPLIHACK_AUTO_INSTALL", "").lower() in (
            "0",
            "false",
            "no",
        )

        if auto_install_disabled:
            print("\n⚠️  Claude CLI not found")
            print("Auto-installation disabled via AMPLIHACK_AUTO_INSTALL=0")
            print("\nTo install manually:")
            print('  export NPM_CONFIG_PREFIX="$HOME/.npm-global"')
            print("  npm install -g @anthropic-ai/claude-code --ignore-scripts")
            print('  export PATH="$HOME/.npm-global/bin:$PATH"')
            return None

        print("Claude CLI not found. Auto-installing...")
        if _install_claude_cli():
            # Installation succeeded - return the expected binary path
            # We already validated it in _install_claude_cli(), so no need to check again
            user_npm_bin = Path.home() / ".npm-global" / "bin"
            expected_binary = user_npm_bin / "claude"
            return str(expected_binary)

    # Installation failed or auto-install disabled - print manual instructions only once
    print("\n⚠️  Claude CLI installation failed or not found")
    print("Please install manually:")
    print('  export NPM_CONFIG_PREFIX="$HOME/.npm-global"')
    print("  npm install -g @anthropic-ai/claude-code --ignore-scripts")
    print('  export PATH="$HOME/.npm-global/bin:$PATH"')

    return None


def ensure_claude_cli() -> str:
    """Ensure Claude CLI is available, installing if needed.

    Returns:
        Path to claude binary.

    Raises:
        RuntimeError: If Claude CLI cannot be found or installed.
    """
    claude_path = get_claude_cli_path(auto_install=True)

    if not claude_path:
        raise RuntimeError(
            "Claude CLI not available and auto-installation failed. "
            "Please install manually: npm install -g @anthropic-ai/claude-code"
        )

    return claude_path
