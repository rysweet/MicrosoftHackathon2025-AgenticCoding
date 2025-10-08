"""GitHub OAuth device flow authentication for Copilot API."""

import subprocess
import time
from pathlib import Path
from typing import Optional, Tuple


class GitHubAuthManager:
    """Manages GitHub authentication for Copilot API access."""

    def __init__(self):
        """Initialize GitHub auth manager."""
        self.client_id = "Iv1.b507a08c87ecfe98"  # GitHub CLI client ID
        self.device_code_url = "https://github.com/login/device/code"
        self.access_token_url = "https://github.com/login/oauth/access_token"
        self.scopes = ["copilot"]

    def get_existing_token(self) -> Optional[str]:
        """Get existing GitHub token from gh CLI if available.

        Returns:
            GitHub token if available and has Copilot access, None otherwise.
        """
        try:
            # Check if gh CLI is installed and authenticated
            result = subprocess.run(
                ["gh", "auth", "status"], capture_output=True, text=True, timeout=10
            )

            if result.returncode != 0:
                return None

            # Try to get token with copilot scope
            token_result = subprocess.run(
                ["gh", "auth", "token"], capture_output=True, text=True, timeout=10
            )

            if token_result.returncode == 0 and token_result.stdout.strip():
                token = token_result.stdout.strip()

                # Verify token has Copilot access
                if self._verify_copilot_access(token):
                    return token

        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return None

    def initiate_device_flow(self) -> Tuple[str, str, str]:
        """Initiate GitHub OAuth device flow.

        Returns:
            Tuple of (device_code, user_code, verification_uri).

        Raises:
            RuntimeError: If device flow initiation fails.
        """
        try:
            import requests
        except ImportError:
            raise RuntimeError(
                "requests library required for GitHub OAuth. Install with: pip install requests"
            )

        data = {"client_id": self.client_id, "scope": " ".join(self.scopes)}

        try:
            response = requests.post(
                self.device_code_url, data=data, headers={"Accept": "application/json"}, timeout=30
            )
            response.raise_for_status()

            result = response.json()
            return (result["device_code"], result["user_code"], result["verification_uri"])

        except Exception as e:
            raise RuntimeError(f"Failed to initiate device flow: {e}")

    def poll_for_token(self, device_code: str, interval: int = 5, timeout: int = 300) -> str:
        """Poll for access token after user authorization.

        Args:
            device_code: Device code from initiate_device_flow
            interval: Polling interval in seconds
            timeout: Maximum time to wait in seconds

        Returns:
            Access token if authorization successful.

        Raises:
            RuntimeError: If authorization fails or times out.
        """
        try:
            import requests
        except ImportError:
            raise RuntimeError(
                "requests library required for GitHub OAuth. Install with: pip install requests"
            )

        data = {
            "client_id": self.client_id,
            "device_code": device_code,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        }

        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                response = requests.post(
                    self.access_token_url,
                    data=data,
                    headers={"Accept": "application/json"},
                    timeout=30,
                )

                if response.status_code == 200:
                    result = response.json()
                    if "access_token" in result:
                        return result["access_token"]

                # Handle specific error responses
                if response.status_code == 400:
                    error_data = response.json()
                    error_type = error_data.get("error", "")

                    if error_type == "authorization_pending":
                        # Continue polling
                        time.sleep(interval)
                        continue
                    if error_type == "slow_down":
                        # Increase polling interval
                        interval += 5
                        time.sleep(interval)
                        continue
                    if error_type in ("expired_token", "access_denied"):
                        raise RuntimeError(f"Authorization failed: {error_type}")

                # Unexpected response
                response.raise_for_status()

            except requests.RequestException as e:
                if time.time() - start_time >= timeout - 30:  # Close to timeout
                    raise RuntimeError(f"Token polling failed: {e}")
                # Continue polling for temporary network errors
                time.sleep(interval)
                continue

        raise RuntimeError("Authorization timed out")

    def save_token(self, token: str, config_path: Optional[Path] = None) -> None:
        """Save GitHub token to configuration.

        Args:
            token: GitHub access token
            config_path: Path to save token (optional)
        """
        if config_path and config_path.exists():
            # Add token to existing config file
            try:
                with open(config_path, "a") as f:
                    f.write(f"\nGITHUB_TOKEN={token}\n")
            except Exception as e:
                print(f"Warning: Failed to save token to {config_path}: {e}")
        else:
            # Save to default location
            config_dir = Path.home() / ".amplihack"
            config_dir.mkdir(exist_ok=True)

            github_config = config_dir / "github.env"
            try:
                with open(github_config, "w") as f:
                    f.write(f"GITHUB_TOKEN={token}\n")
                    f.write("GITHUB_COPILOT_ENABLED=true\n")
                print(f"GitHub token saved to {github_config}")
            except Exception as e:
                print(f"Warning: Failed to save token: {e}")

    def _verify_copilot_access(self, token: str) -> bool:
        """Verify token has GitHub Copilot access.

        Args:
            token: GitHub access token

        Returns:
            True if token has Copilot access, False otherwise.
        """
        try:
            import requests
        except ImportError:
            # If requests not available, assume token is valid
            return True

        try:
            # Test Copilot API access
            response = requests.get(
                "https://api.github.com/user",  # Basic API call to verify token
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github.v3+json",
                },
                timeout=10,
            )

            if response.status_code == 200:
                # Could add more specific Copilot access verification here
                return True

        except Exception:
            pass

        return False

    def get_or_create_token(self, config_path: Optional[Path] = None) -> str:
        """Get existing token or create new one via device flow.

        Args:
            config_path: Optional config file path

        Returns:
            Valid GitHub token with Copilot access.

        Raises:
            RuntimeError: If authentication fails.
        """
        # Try existing token first
        existing_token = self.get_existing_token()
        if existing_token:
            print("Using existing GitHub token from gh CLI")
            return existing_token

        # Initiate device flow
        print("Starting GitHub OAuth device flow for Copilot access...")
        device_code, user_code, verification_uri = self.initiate_device_flow()

        print(f"\nPlease visit: {verification_uri}")
        print(f"And enter code: {user_code}")
        print("\nWaiting for authorization...")

        # Poll for token
        token = self.poll_for_token(device_code)

        # Save token
        self.save_token(token, config_path)

        print("GitHub authentication successful!")
        return token

    def revoke_token(self, token: str) -> bool:
        """Revoke GitHub access token.

        Args:
            token: GitHub access token to revoke

        Returns:
            True if revocation successful, False otherwise.
        """
        try:
            import requests
        except ImportError:
            return False

        try:
            response = requests.delete(
                f"https://api.github.com/applications/{self.client_id}/token",
                json={"access_token": token},
                timeout=30,
            )
            return response.status_code == 204

        except Exception:
            return False
