"""Cross-platform process management utilities."""

import os
import signal
import subprocess
import sys
from typing import Dict, List, Optional

from ..errors import (
    ProcessError,
    RetryConfig,
    TimeoutError,
    format_process_error,
    log_error,
    retry_on_error,
)


class ProcessManager:
    """Cross-platform process management utilities."""

    @staticmethod
    def is_windows() -> bool:
        """Check if running on Windows.

        Returns:
            True if Windows, False otherwise.
        """
        return sys.platform == "win32" or os.name == "nt"

    @staticmethod
    def is_unix() -> bool:
        """Check if running on Unix-like system.

        Returns:
            True if Unix-like, False otherwise.
        """
        return not ProcessManager.is_windows()

    @staticmethod
    def create_process_group(popen_args: Dict) -> Dict:
        """Add process group creation flags to Popen arguments.

        Args:
            popen_args: Dictionary of Popen arguments.

        Returns:
            Modified dictionary with process group flags.
        """
        if ProcessManager.is_windows():
            # CREATE_NEW_PROCESS_GROUP is Windows-specific
            import subprocess

            if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
                popen_args["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP")
        else:
            popen_args["preexec_fn"] = os.setsid
        return popen_args

    @staticmethod
    def terminate_process_group(process: subprocess.Popen, timeout: int = 5) -> None:
        """Terminate a process and its group.

        Args:
            process: Process to terminate.
            timeout: Timeout in seconds for graceful shutdown.

        Raises:
            ProcessError: If process termination fails
        """
        if process.poll() is not None:
            return  # Already terminated

        try:
            if ProcessManager.is_windows():
                # Windows: terminate the process
                process.terminate()
            else:
                # Unix: terminate the process group
                pgid = os.getpgid(process.pid)
                os.killpg(pgid, signal.SIGTERM)

            # Wait for graceful shutdown
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                # Force kill if not responding
                if ProcessManager.is_windows():
                    process.kill()
                else:
                    try:
                        os.killpg(pgid, signal.SIGKILL)  # type: ignore
                    except (NameError, UnboundLocalError):
                        process.kill()  # Fallback if pgid not defined

                # Final wait with timeout
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    error = ProcessError(
                        "Process failed to terminate after force kill",
                        context={"pid": process.pid, "timeout": timeout},
                    )
                    log_error(error)
                    raise error

        except ProcessError:
            raise  # Re-raise our own errors
        except Exception as e:
            # Try direct kill as fallback
            try:
                process.kill()
                process.wait(timeout=2)
            except Exception as fallback_error:
                error = ProcessError(
                    "Failed to terminate process and fallback failed",
                    context={
                        "pid": process.pid,
                        "original_error": str(e),
                        "fallback_error": str(fallback_error),
                        "cause": str(e),
                    },
                )
                log_error(error)
                raise error

    @staticmethod
    @retry_on_error(RetryConfig(max_attempts=2, base_delay=0.1))
    def check_command_exists(command: str) -> bool:
        """Check if a command exists in PATH.

        Args:
            command: Command name to check.

        Returns:
            True if command exists, False otherwise.

        Raises:
            ProcessError: If command checking fails unexpectedly
        """

        try:
            if ProcessManager.is_windows():
                # Windows: use where command
                result = subprocess.run(
                    ["where", command], capture_output=True, text=True, check=False, timeout=10
                )
            else:
                # Unix: use which command
                result = subprocess.run(
                    ["which", command], capture_output=True, text=True, check=False, timeout=10
                )
            return result.returncode == 0

        except subprocess.TimeoutExpired as e:
            error = TimeoutError(
                f"Command existence check timed out for '{command}'",
                context={
                    "timeout_duration": 10.0,
                    "operation": f"check_command_exists({command})",
                    "cause": str(e),
                },
            )
            log_error(error)
            return False  # Assume command doesn't exist if check times out

        except Exception as e:
            error = ProcessError(
                f"Failed to check if command '{command}' exists",
                context={"command": command, "cause": str(e)},
            )
            log_error(error)
            return False  # Assume command doesn't exist on error

    @staticmethod
    @retry_on_error(RetryConfig(max_attempts=3, base_delay=1.0))
    def run_command(
        command: List[str],
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        capture_output: bool = True,
        timeout: Optional[float] = None,
        retry_config: Optional[RetryConfig] = None,
    ) -> subprocess.CompletedProcess:
        """Run a command with cross-platform compatibility and retry logic.

        Args:
            command: Command and arguments as list.
            cwd: Working directory.
            env: Environment variables.
            capture_output: Whether to capture output.
            timeout: Command timeout in seconds.
            retry_config: Custom retry configuration.

        Returns:
            CompletedProcess instance.

        Raises:
            ProcessError: If command execution fails
            TimeoutError: If command times out
        """

        # Validate command
        if not command or not command[0]:
            error = ProcessError(
                "Command cannot be empty",
                context={"command": str(command)},
            )
            log_error(error)
            raise error

        # Check if command exists
        if not ProcessManager.check_command_exists(command[0]):
            error = ProcessError(
                format_process_error(command[0], return_code=127),
                return_code=127,
                context={"command": " ".join(command)},
            )
            log_error(error)
            raise error

        kwargs = {
            "cwd": cwd,
            "env": env,
            "capture_output": capture_output,
            "text": True,
            "timeout": timeout or 300,  # Default 5-minute timeout
        }

        # Add shell=True for Windows if needed
        if ProcessManager.is_windows() and command[0] in ["npm", "npx", "node"]:
            # These commands often need shell on Windows
            kwargs["shell"] = True

        try:
            result = subprocess.run(command, **kwargs)

            # Check if command failed
            if result.returncode != 0:
                error = ProcessError(
                    format_process_error(
                        " ".join(command),
                        return_code=result.returncode,
                        stderr=result.stderr,
                    ),
                    return_code=result.returncode,
                    context={
                        "command": " ".join(command),
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                    },
                )
                log_error(error)
                raise error

            return result

        except subprocess.TimeoutExpired as e:
            error = TimeoutError(
                f"Command timed out after {timeout or 300} seconds: {' '.join(command)}",
                context={
                    "timeout_duration": timeout or 300,
                    "operation": f"run_command({' '.join(command)})",
                    "cause": str(e),
                },
            )
            log_error(error)
            raise error

        except ProcessError:
            raise  # Re-raise our own errors

        except Exception as e:
            error = ProcessError(
                f"Unexpected error running command: {e}",
                context={"command": " ".join(command), "cause": str(e)},
            )
            log_error(error)
            raise error

    @staticmethod
    def run_command_safe(
        command: List[str],
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        capture_output: bool = True,
        timeout: Optional[float] = None,
    ) -> Optional[subprocess.CompletedProcess]:
        """Run a command safely, returning None on failure instead of raising.

        Args:
            command: Command and arguments as list.
            cwd: Working directory.
            env: Environment variables.
            capture_output: Whether to capture output.
            timeout: Command timeout in seconds.

        Returns:
            CompletedProcess instance on success, None on failure.
        """
        try:
            return ProcessManager.run_command(
                command=command, cwd=cwd, env=env, capture_output=capture_output, timeout=timeout
            )
        except (ProcessError, TimeoutError):
            # Errors are already logged by run_command
            return None
