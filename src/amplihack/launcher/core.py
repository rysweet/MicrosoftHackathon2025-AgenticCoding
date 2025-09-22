"""Core launcher functionality for Claude Code."""

import os
import signal
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from ..proxy.manager import ProxyManager
from .detector import ClaudeDirectoryDetector


class ClaudeLauncher:
    """Launches Claude Code with proper configuration."""

    def __init__(
        self,
        proxy_manager: Optional[ProxyManager] = None,
        append_system_prompt: Optional[Path] = None,
    ):
        """Initialize Claude launcher.

        Args:
            proxy_manager: Optional proxy manager for Azure integration.
            append_system_prompt: Optional path to system prompt to append.
        """
        self.proxy_manager = proxy_manager
        self.append_system_prompt = append_system_prompt
        self.detector = ClaudeDirectoryDetector()
        self.claude_process: Optional[subprocess.Popen] = None

    def prepare_launch(self) -> bool:
        """Prepare environment for launching Claude.

        Returns:
            True if preparation successful, False otherwise.
        """
        # Try UVX staging if no .claude directory found
        claude_dir = self.detector.find_claude_directory()
        if not claude_dir:
            try:
                from ..utils.uvx_staging import is_uvx_deployment, stage_uvx_framework

                if is_uvx_deployment():
                    print("UVX deployment detected, attempting to stage framework files...")
                    if stage_uvx_framework():
                        print("Framework files staged successfully")
                        # Check again for .claude directory
                        claude_dir = self.detector.find_claude_directory()
                    else:
                        print("Framework staging failed")
            except ImportError:
                pass  # UVX staging not available

        # Check for .claude directory (again, after potential staging)
        if claude_dir:
            print(f"Found .claude directory at: {claude_dir}")
            project_root = self.detector.get_project_root(claude_dir)
            os.chdir(project_root)
            print(f"Changed directory to project root: {project_root}")
        else:
            print("No .claude directory found in current or parent directories")

        # Start proxy if configured
        if self.proxy_manager:
            if not self.proxy_manager.start_proxy():
                print("Failed to start proxy")
                return False
            print(f"Proxy running at: {self.proxy_manager.get_proxy_url()}")

        return True

    def build_claude_command(self) -> List[str]:
        """Build the Claude command with arguments.

        Returns:
            List of command arguments for subprocess.
        """
        cmd = ["claude", "--dangerously-skip-permissions"]

        # Add system prompt if provided
        if self.append_system_prompt and self.append_system_prompt.exists():
            cmd.extend(["--append-system-prompt", str(self.append_system_prompt)])

        return cmd

    def launch(self) -> int:
        """Launch Claude Code with configuration.

        Returns:
            Exit code from Claude process.
        """
        if not self.prepare_launch():
            return 1

        try:
            cmd = self.build_claude_command()
            print(f"Launching Claude with command: {' '.join(cmd)}")

            # Set up signal handling for graceful shutdown
            def signal_handler(sig, frame):
                print("\nReceived interrupt signal. Shutting down...")
                if self.claude_process:
                    self.claude_process.terminate()
                if self.proxy_manager:
                    self.proxy_manager.stop_proxy()
                sys.exit(0)

            signal.signal(signal.SIGINT, signal_handler)
            if sys.platform != "win32":
                signal.signal(signal.SIGTERM, signal_handler)

            # Launch Claude
            self.claude_process = subprocess.Popen(cmd)

            # Wait for Claude to finish
            exit_code = self.claude_process.wait()

            return exit_code

        except Exception as e:
            print(f"Error launching Claude: {e}")
            return 1
        finally:
            # Clean up proxy
            if self.proxy_manager:
                self.proxy_manager.stop_proxy()

    def launch_interactive(self) -> int:
        """Launch Claude in interactive mode with live output.

        Returns:
            Exit code from Claude process.
        """
        if not self.prepare_launch():
            return 1

        try:
            cmd = self.build_claude_command()
            print(f"Launching Claude with command: {' '.join(cmd)}")

            # Set up signal handling for graceful shutdown
            def signal_handler(sig, frame):
                print("\nReceived interrupt signal. Shutting down...")
                if self.proxy_manager:
                    self.proxy_manager.stop_proxy()
                sys.exit(0)

            signal.signal(signal.SIGINT, signal_handler)
            if sys.platform != "win32":
                signal.signal(signal.SIGTERM, signal_handler)

            # Launch Claude with direct I/O (interactive mode)
            exit_code = subprocess.call(cmd)

            return exit_code

        except Exception as e:
            print(f"Error launching Claude: {e}")
            return 1
        finally:
            # Clean up proxy
            if self.proxy_manager:
                self.proxy_manager.stop_proxy()
