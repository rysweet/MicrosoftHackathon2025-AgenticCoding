"""Proxy lifecycle management."""

import atexit
import os
import signal
import subprocess
import time
from pathlib import Path
from typing import Optional

from .config import ProxyConfig
from .env import ProxyEnvironment


class ProxyManager:
    """Manages claude-code-proxy lifecycle."""

    def __init__(self, proxy_config: Optional[ProxyConfig] = None):
        """Initialize proxy manager.

        Args:
            proxy_config: Proxy configuration object.
        """
        self.proxy_config = proxy_config
        self.proxy_process: Optional[subprocess.Popen] = None
        self.proxy_dir = Path.home() / ".amplihack" / "proxy"
        self.env_manager = ProxyEnvironment()
        self.proxy_port = 8080

    def ensure_proxy_installed(self) -> bool:
        """Ensure claude-code-proxy is installed.

        Returns:
            True if proxy is ready to use, False otherwise.
        """
        proxy_repo = self.proxy_dir / "claude-code-proxy"

        if not proxy_repo.exists():
            print("Claude-code-proxy not found. Cloning...")
            try:
                self.proxy_dir.mkdir(parents=True, exist_ok=True)
                subprocess.run(
                    [
                        "git",
                        "clone",
                        "https://github.com/codewithcheese/claude-code-proxy.git",
                        str(proxy_repo),
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                print(f"Successfully cloned claude-code-proxy to {proxy_repo}")
            except subprocess.CalledProcessError as e:
                print(f"Failed to clone claude-code-proxy: {e}")
                return False

        return proxy_repo.exists()

    def setup_proxy_config(self) -> bool:
        """Set up proxy configuration.

        Returns:
            True if configuration is set up successfully, False otherwise.
        """
        if not self.proxy_config or not self.proxy_config.config_path:
            return True  # No config to set up

        proxy_repo = self.proxy_dir / "claude-code-proxy"
        target_env = proxy_repo / ".env"

        # Copy .env file to proxy directory
        try:
            self.proxy_config.save_to(target_env)
            print(f"Copied proxy configuration to {target_env}")
            return True
        except Exception as e:
            print(f"Failed to copy proxy configuration: {e}")
            return False

    def start_proxy(self) -> bool:
        """Start the claude-code-proxy server.

        Returns:
            True if proxy started successfully, False otherwise.
        """
        if self.proxy_process and self.proxy_process.poll() is None:
            print("Proxy is already running")
            return True

        if not self.ensure_proxy_installed():
            return False

        if not self.setup_proxy_config():
            return False

        proxy_repo = self.proxy_dir / "claude-code-proxy"

        try:
            # Start the proxy process
            print(f"Starting claude-code-proxy on port {self.proxy_port}...")

            # Create environment for the proxy process
            proxy_env = os.environ.copy()
            if self.proxy_config:
                proxy_env.update(self.proxy_config.to_env_dict())

            self.proxy_process = subprocess.Popen(
                ["npm", "start"],
                cwd=str(proxy_repo),
                env=proxy_env,
                stdout=subprocess.DEVNULL,  # Prevent buffer accumulation
                stderr=subprocess.DEVNULL,  # Prevent buffer accumulation
                text=True,
                preexec_fn=os.setsid if os.name != "nt" else None,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
            )

            # Register cleanup on exit
            atexit.register(self.stop_proxy)

            # Wait a moment for the proxy to start
            time.sleep(2)

            # Check if proxy is still running
            if self.proxy_process.poll() is not None:
                print(
                    f"Proxy failed to start. Process exited with code {self.proxy_process.returncode}"
                )
                return False

            # Set up environment variables
            api_key = self.proxy_config.get("ANTHROPIC_API_KEY") if self.proxy_config else None
            self.env_manager.setup(self.proxy_port, api_key)

            print(f"Proxy started successfully on port {self.proxy_port}")
            return True

        except Exception as e:
            print(f"Failed to start proxy: {e}")
            return False

    def stop_proxy(self) -> None:
        """Stop the claude-code-proxy server."""
        if not self.proxy_process:
            return

        if self.proxy_process.poll() is None:
            print("Stopping claude-code-proxy...")
            try:
                if os.name == "nt":
                    # Windows
                    self.proxy_process.terminate()
                else:
                    # Unix-like
                    os.killpg(os.getpgid(self.proxy_process.pid), signal.SIGTERM)

                # Wait for graceful shutdown
                try:
                    self.proxy_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if not responding
                    if os.name == "nt":
                        self.proxy_process.kill()
                    else:
                        os.killpg(os.getpgid(self.proxy_process.pid), signal.SIGKILL)
                    self.proxy_process.wait()

                print("Proxy stopped successfully")
            except Exception as e:
                print(f"Error stopping proxy: {e}")

        # Restore environment variables
        self.env_manager.restore()
        self.proxy_process = None

    def is_running(self) -> bool:
        """Check if proxy is running.

        Returns:
            True if proxy is running, False otherwise.
        """
        return self.proxy_process is not None and self.proxy_process.poll() is None

    def get_proxy_url(self) -> str:
        """Get the proxy URL.

        Returns:
            URL of the running proxy.
        """
        return f"http://localhost:{self.proxy_port}"

    def __enter__(self):
        """Context manager entry - starts proxy.

        Returns:
            Self for context manager use.
        """
        self.start_proxy()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - stops proxy.

        Args:
            exc_type: Exception type if any.
            exc_val: Exception value if any.
            exc_tb: Exception traceback if any.
        """
        self.stop_proxy()
