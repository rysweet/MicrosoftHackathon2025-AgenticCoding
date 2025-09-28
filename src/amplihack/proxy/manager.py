"""Proxy lifecycle management."""

import atexit
import os
import subprocess
import time
from pathlib import Path
from typing import List, Optional

from ..errors import (
    ConfigurationError,
    NetworkError,
    ProcessError,
    RetryConfig,
    format_error_message,
    log_error,
    retry_on_error,
)
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
        # Read PORT from proxy_config if available, otherwise use default
        if proxy_config and proxy_config.get("PORT"):
            self.proxy_port = int(proxy_config.get("PORT"))
            print(f"Using proxy port from config: {self.proxy_port}")
        else:
            self.proxy_port = 8080  # Default port
            print(f"Using default proxy port: {self.proxy_port}")

    @retry_on_error(RetryConfig(max_attempts=3, base_delay=2.0))
    def ensure_proxy_installed(self) -> bool:
        """Ensure claude-code-proxy is installed.

        Returns:
            True if proxy is ready to use, False otherwise.

        Raises:
            ProcessError: If installation fails after retries
            NetworkError: If git clone fails due to network issues
        """
        proxy_repo = self.proxy_dir / "claude-code-proxy"

        if proxy_repo.exists() and (proxy_repo / ".git").exists():
            print(f"Claude-code-proxy already installed at {proxy_repo}")
            return True

        print("Claude-code-proxy not found. Installing...")

        try:
            # Ensure directory exists
            self.proxy_dir.mkdir(parents=True, exist_ok=True)

            # Clone the repository
            subprocess.run(
                [
                    "git",
                    "clone",
                    "https://github.com/fuergaosi233/claude-code-proxy.git",
                    str(proxy_repo),
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=120,  # 2-minute timeout for clone
            )

            print(f"Successfully cloned claude-code-proxy to {proxy_repo}")

            # Verify installation
            if not (proxy_repo.exists() and (proxy_repo / ".git").exists()):
                error = ProcessError(
                    "Proxy installation incomplete - repository directory missing",
                    context={"proxy_repo": str(proxy_repo)},
                )
                log_error(error)
                raise error

            return True

        except subprocess.TimeoutExpired as e:
            error = NetworkError(
                format_error_message(
                    "NETWORK_TIMEOUT",
                    url="https://github.com/fuergaosi233/claude-code-proxy.git",
                    timeout=120,
                ),
                context={
                    "url": "https://github.com/fuergaosi233/claude-code-proxy.git",
                    "timeout": 120.0,
                    "cause": str(e),
                },
            )
            log_error(error)
            raise error

        except subprocess.CalledProcessError as e:
            error = ProcessError(
                f"Git clone failed: {e.stderr or str(e)}",
                return_code=e.returncode,
                context={"command": "git clone", "stderr": e.stderr, "cause": str(e)},
            )
            log_error(error)
            raise error

        except Exception as e:
            error = ProcessError(
                f"Failed to install claude-code-proxy: {e}", context={"cause": str(e)}
            )
            log_error(error)
            raise error

    def setup_proxy_config(self) -> bool:
        """Set up proxy configuration.

        Returns:
            True if configuration is set up successfully, False otherwise.

        Raises:
            ConfigurationError: If configuration setup fails
        """

        if not self.proxy_config or not self.proxy_config.config_path:
            print("No proxy configuration to set up")
            return True  # No config to set up

        proxy_repo = self.proxy_dir / "claude-code-proxy"
        target_env = proxy_repo / ".env"

        # Verify proxy repo exists
        if not proxy_repo.exists():
            error = ConfigurationError(
                "Cannot setup config: proxy repository not found",
                context={"config_file": str(target_env), "proxy_repo": str(proxy_repo)},
            )
            log_error(error)
            raise error

        # Copy .env file to proxy directory
        try:
            self.proxy_config.save_to(target_env)
            print(f"Copied proxy configuration to {target_env}")

            # Verify configuration was saved
            if not target_env.exists():
                error = ConfigurationError(
                    "Configuration file was not created successfully",
                    context={"config_file": str(target_env)},
                )
                log_error(error)
                raise error

            return True

        except Exception as e:
            error = ConfigurationError(
                f"Failed to copy proxy configuration: {e}",
                context={"config_file": str(target_env), "cause": str(e)},
            )
            log_error(error)
            raise error

    @retry_on_error(RetryConfig(max_attempts=2, base_delay=3.0))
    def start_proxy(self) -> bool:
        """Start the claude-code-proxy server.

        Returns:
            True if proxy started successfully, False otherwise.

        Raises:
            ProcessError: If proxy startup fails
            ConfigurationError: If proxy configuration is invalid
            NetworkError: If proxy port is already in use
        """

        # Check if already running
        if self.proxy_process and self.proxy_process.poll() is None:
            print("Proxy is already running")
            return True

        try:
            # Ensure proxy is installed
            if not self.ensure_proxy_installed():
                error = ProcessError("Cannot start proxy: installation failed")
                log_error(error)
                raise error

            # Setup configuration
            if not self.setup_proxy_config():
                error = ConfigurationError("Cannot start proxy: configuration setup failed")
                log_error(error)
                raise error

        except (ProcessError, ConfigurationError):
            raise  # Re-raise our own errors
        except Exception as e:
            error = ProcessError(
                f"Failed to prepare proxy for startup: {e}", context={"cause": str(e)}
            )
            log_error(error)
            raise error

        proxy_repo = self.proxy_dir / "claude-code-proxy"

        try:
            # Install dependencies with proper error handling
            self._install_proxy_dependencies(proxy_repo)

            # Start the proxy process
            return self._start_proxy_process(proxy_repo)

        except (ProcessError, ConfigurationError, NetworkError):
            raise  # Re-raise our own errors
        except Exception as e:
            error = ProcessError(f"Failed to start proxy server: {e}", context={"cause": str(e)})
            log_error(error)
            raise error

    def _install_proxy_dependencies(self, proxy_repo: Path) -> None:
        """Install proxy dependencies.

        Args:
            proxy_repo: Path to proxy repository

        Raises:
            ProcessError: If dependency installation fails
        """
        requirements_txt = proxy_repo / "requirements.txt"
        package_json = proxy_repo / "package.json"

        # Install Python dependencies if needed
        if requirements_txt.exists():
            print("Installing Python proxy dependencies...")
            # Try uv first (preferred in uvx context), fall back to pip
            pip_commands = [
                ["uv", "pip", "install", "-r", "requirements.txt"],
                ["pip", "install", "-r", "requirements.txt"],
            ]

            install_result = None
            for pip_cmd in pip_commands:
                try:
                    install_result = subprocess.run(
                        pip_cmd,
                        cwd=str(proxy_repo),
                        capture_output=True,
                        text=True,
                        timeout=300,  # 5-minute timeout
                    )
                    if install_result.returncode == 0:
                        print("Python dependencies installed successfully")
                        return
                except subprocess.TimeoutExpired:
                    continue  # Try next command

            # All pip commands failed
            error_msg = "Failed to install Python dependencies"
            if install_result and install_result.stderr:
                error_msg += f": {install_result.stderr}"

            error = ProcessError(
                format_error_message("PROXY_INSTALLATION_FAILED", reason=error_msg),
                return_code=install_result.returncode if install_result else -1,
                context={
                    "command": " ".join(pip_commands[-1]) if pip_commands else "pip install",
                    "stderr": install_result.stderr if install_result else None,
                },
            )
            log_error(error)
            raise error

        # Install npm dependencies if needed
        elif package_json.exists():
            node_modules = proxy_repo / "node_modules"
            if not node_modules.exists():
                print("Installing npm proxy dependencies...")
                try:
                    install_result = subprocess.run(
                        ["npm", "install"],
                        cwd=str(proxy_repo),
                        capture_output=True,
                        text=True,
                        timeout=300,  # 5-minute timeout
                    )
                    if install_result.returncode != 0:
                        error = ProcessError(
                            format_error_message(
                                "PROXY_INSTALLATION_FAILED",
                                reason=f"npm install failed: {install_result.stderr}",
                            ),
                            return_code=install_result.returncode,
                            context={
                                "command": "npm install",
                                "stderr": install_result.stderr,
                            },
                        )
                        log_error(error)
                        raise error
                    print("npm dependencies installed successfully")

                except subprocess.TimeoutExpired as e:
                    error = ProcessError(
                        "npm install timed out after 5 minutes",
                        context={"command": "npm install", "cause": str(e)},
                    )
                    log_error(error)
                    raise error

    def _start_proxy_process(self, proxy_repo: Path) -> bool:
        """Start the actual proxy process.

        Args:
            proxy_repo: Path to proxy repository

        Returns:
            True if proxy started successfully

        Raises:
            ProcessError: If proxy startup fails
            NetworkError: If port is already in use
        """
        print(f"Starting claude-code-proxy on port {self.proxy_port}...")

        # Create environment for the proxy process
        proxy_env = os.environ.copy()
        if self.proxy_config:
            proxy_env.update(self.proxy_config.to_env_dict())
        # Ensure PORT is set for the proxy process
        proxy_env["PORT"] = str(self.proxy_port)

        # Determine start command based on project structure
        start_command = self._determine_start_command(proxy_repo)

        try:
            self.proxy_process = subprocess.Popen(
                start_command,
                cwd=str(proxy_repo),
                env=proxy_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
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
                stdout, stderr = self.proxy_process.communicate(timeout=0.1)
                error_msg = f"Proxy failed to start. Exit code: {self.proxy_process.returncode}"
                if stderr:
                    error_msg += f". Error output: {stderr}"

                error = ProcessError(
                    error_msg,
                    return_code=self.proxy_process.returncode,
                    context={
                        "command": " ".join(start_command),
                        "stdout": stdout,
                        "stderr": stderr,
                    },
                )
                log_error(error)
                raise error

            # Set up environment variables
            api_key = self.proxy_config.get("ANTHROPIC_API_KEY") if self.proxy_config else None
            self.env_manager.setup(self.proxy_port, api_key)

            print(f"Proxy started successfully on port {self.proxy_port}")
            return True

        except Exception as e:
            if isinstance(e, ProcessError):
                raise

            # Check if it's a port conflict
            if "address already in use" in str(e).lower() or "bind" in str(e).lower():
                error = NetworkError(
                    f"Port {self.proxy_port} is already in use",
                    context={"url": f"localhost:{self.proxy_port}", "cause": str(e)},
                )
                log_error(error)
                raise error

            error = ProcessError(
                f"Failed to start proxy process: {e}",
                context={"command": " ".join(start_command), "cause": str(e)},
            )
            log_error(error)
            raise error

    def _determine_start_command(self, proxy_repo: Path) -> List[str]:
        """Determine the appropriate start command for the proxy.

        Args:
            proxy_repo: Path to proxy repository

        Returns:
            List of command arguments
        """
        # Check if we should use 'npm start' or 'python' based on project structure
        start_command = ["npm", "start"]
        if (proxy_repo / "start_proxy.py").exists():
            # It's a Python project - try uv run first, fall back to python
            # Check if uv is available
            uv_check = subprocess.run(["which", "uv"], capture_output=True, shell=True)
            if uv_check.returncode == 0:
                start_command = ["uv", "run", "python", "start_proxy.py"]
            else:
                start_command = ["python", "start_proxy.py"]
        elif (proxy_repo / "src" / "proxy.py").exists():
            # Alternative Python structure
            uv_check = subprocess.run(["which", "uv"], capture_output=True, shell=True)
            if uv_check.returncode == 0:
                start_command = ["uv", "run", "python", "-m", "src.proxy"]
            else:
                start_command = ["python", "-m", "src.proxy"]

        return start_command

    def stop_proxy(self) -> None:
        """Stop the claude-code-proxy server with enhanced error handling."""

        if not self.proxy_process:
            return

        if self.proxy_process.poll() is None:
            print("Stopping claude-code-proxy...")
            try:
                # Use ProcessManager for consistent termination
                from ..utils.process import ProcessManager

                ProcessManager.terminate_process_group(self.proxy_process, timeout=5)
                print("Proxy stopped successfully")

            except Exception as e:
                error = ProcessError(
                    f"Error stopping proxy: {e}",
                    context={
                        "pid": self.proxy_process.pid if self.proxy_process else None,
                        "cause": str(e),
                    },
                )
                log_error(error)
                # Don't raise here - stopping should be best effort

        # Restore environment variables
        try:
            self.env_manager.restore()
        except Exception as e:
            error = ProcessError(f"Error restoring environment: {e}", context={"cause": str(e)})
            log_error(error)

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
