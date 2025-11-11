# Security Analysis: Neo4j Container Detection & Credential Synchronization

**Issue:** #1170
**Feature:** Extract Neo4j credentials from Docker containers and synchronize to .env file
**Analysis Date:** 2025-11-07
**Analyst:** Security Agent (Claude Code)

---

## Executive Summary

This feature introduces significant security considerations around credential management, Docker API access, filesystem operations, and user input handling. While the design is solid, several critical security requirements must be implemented to prevent credential exposure, injection attacks, and privilege escalation.

**Risk Level:** MEDIUM-HIGH (handles sensitive credentials and Docker access)

**Critical Security Requirements:** 11 MUST-implement items identified

---

## 1. Threat Model

### Assets at Risk

1. **Neo4j Credentials** (passwords, usernames)
2. **.env File** (contains application secrets)
3. **Docker Daemon Access** (container manipulation capability)
4. **User System** (file permissions, process isolation)
5. **Container Data** (environment variables, secrets)

### Threat Actors

1. **Malicious Container Image** - Could inject fake Neo4j credentials
2. **Compromised Docker Daemon** - Could expose all container secrets
3. **Local Attacker** - Could read .env file if permissions incorrect
4. **MITM Attacker** - Could intercept Neo4j traffic if unencrypted
5. **Insider Threat** - Could abuse Docker API access for lateral movement

### Attack Vectors

1. **Container Name Injection** - Malicious container names executing commands
2. **Environment Variable Injection** - Crafted NEO4J_AUTH values
3. **Path Traversal** - Manipulated .env file paths
4. **Docker Inspect Exploitation** - Extracting secrets from other containers
5. **Port Conflict Attack** - Binding to privileged ports
6. **Race Conditions** - .env file modification timing attacks
7. **Memory Disclosure** - Password strings in memory/logs
8. **Privilege Escalation** - Docker socket access abuse

---

## 2. Credential Handling Security

### 2.1 Password Extraction

**Current Implementation Gap:**
```python
# Spec shows: docker inspect extracts NEO4J_AUTH, NEO4J_PASSWORD
auth = container.attrs['Config']['Env'].get('NEO4J_AUTH')
password = container.attrs['Config']['Env'].get('NEO4J_PASSWORD')
```

**CRITICAL SECURITY REQUIREMENTS:**

#### SR-1: Never Log or Print Passwords
```python
# MUST IMPLEMENT
class CredentialExtractor:
    def extract(self, container: Neo4jContainer) -> Optional[Neo4jCredentials]:
        password = self._extract_password(container)

        # NEVER do this
        # logger.info(f"Extracted password: {password}")  # ❌ FORBIDDEN
        # print(f"Password: {password}")  # ❌ FORBIDDEN

        # Instead
        logger.info(f"Successfully extracted credentials from {container.name}")  # ✅

        return Neo4jCredentials(username="neo4j", password=password, ...)
```

#### SR-2: Sanitize Credential Display
```python
def _display_container_info(self, container: Neo4jContainer,
                            credentials: Optional[Neo4jCredentials]) -> None:
    """Display container details with masked credentials."""
    print(f"Found: {container.name} ({container.status})")
    print(f"Ports: HTTP={container.ports.get('http')}, Bolt={container.ports.get('bolt')}")

    if credentials:
        # MASK the password - show only source
        masked_pwd = "*" * min(len(credentials.password), 12)
        print(f"Credentials: {credentials.username} / {masked_pwd} (from {credentials.source})")
    else:
        print("Credentials: Unable to extract")
```

#### SR-3: Secure Password String Handling
```python
# MUST IMPLEMENT: Use memory-safe string handling
import secrets
from typing import Optional

class SecureString:
    """Wrapper for sensitive strings with secure cleanup."""

    def __init__(self, value: str):
        self._value = value

    def get(self) -> str:
        """Get value (use sparingly)."""
        return self._value

    def __del__(self):
        """Overwrite memory on deletion (best-effort)."""
        if hasattr(self, '_value'):
            # Python strings are immutable, but we can try to clear reference
            self._value = None

    def __repr__(self) -> str:
        return "<SecureString [REDACTED]>"

    def __str__(self) -> str:
        return "[REDACTED]"

@dataclass
class Neo4jCredentials:
    username: str
    password: SecureString  # Not str!
    http_port: int
    bolt_port: int
    source: str
```

**Implementation Note:** Python's immutable strings make true memory wiping impossible. Consider using `mlock` via `ctypes` for production systems handling highly sensitive credentials.

#### SR-4: Validate Extracted Credentials
```python
def _validate_password(self, password: str) -> bool:
    """Validate password meets minimum security requirements."""
    if not password:
        return False

    # Reject obviously insecure passwords
    WEAK_PASSWORDS = {'neo4j', 'admin', 'password', '123456', 'test'}
    if password.lower() in WEAK_PASSWORDS:
        logger.warning(f"Container using insecure default password (source: {source})")
        # Allow but warn - user may have intentionally set this for dev

    # Check for injection patterns
    if any(char in password for char in ['\n', '\r', '\0', ';', '|', '&']):
        logger.error("Password contains invalid control characters")
        return False

    # Minimum length check
    if len(password) < 8:
        logger.warning(f"Password is shorter than recommended minimum (8 chars)")

    return True
```

### 2.2 .env File Security

#### SR-5: Enforce Strict File Permissions (CRITICAL)
```python
import os
import stat

class CredentialSynchronizer:
    def sync(self, credentials: Neo4jCredentials) -> None:
        """Update .env with strict permissions."""
        # MUST IMPLEMENT: Check current permissions
        if self.env_path.exists():
            current_perms = self.env_path.stat().st_mode & 0o777
            if current_perms != 0o600:
                logger.warning(f".env has insecure permissions: {oct(current_perms)}")
                logger.info("Fixing permissions to 0600 (owner read/write only)")

        # Create backup with secure permissions
        backup_path = self.backup()
        backup_path.chmod(0o600)

        # Write new .env atomically
        temp_path = self.env_path.with_suffix('.env.tmp')

        try:
            # Write to temp file with secure permissions BEFORE writing content
            temp_path.touch(mode=0o600, exist_ok=False)

            with open(temp_path, 'w') as f:
                f.write(self._build_env_content(credentials))

            # Verify permissions before atomic rename
            temp_perms = temp_path.stat().st_mode & 0o777
            if temp_perms != 0o600:
                temp_path.chmod(0o600)

            # Atomic rename
            temp_path.replace(self.env_path)

        except Exception as e:
            # Cleanup temp file on error
            if temp_path.exists():
                temp_path.unlink()
            raise

        # Final verification
        final_perms = self.env_path.stat().st_mode & 0o777
        if final_perms != 0o600:
            logger.error(f"Failed to set secure permissions on .env: {oct(final_perms)}")
            raise SecurityError("Cannot ensure .env file security")

        logger.info("✓ .env updated with secure permissions (0600)")
```

#### SR-6: Atomic File Operations (Prevent Race Conditions)
```python
def sync(self, credentials: Neo4jCredentials) -> None:
    """Atomic .env update to prevent race conditions."""
    import tempfile
    import shutil

    # MUST IMPLEMENT: Use atomic write pattern
    # 1. Write to temp file in same directory (ensures same filesystem)
    temp_fd, temp_path = tempfile.mkstemp(
        dir=self.env_path.parent,
        prefix='.env.tmp.',
        text=True
    )

    try:
        # Close fd and set permissions BEFORE writing content
        os.close(temp_fd)
        os.chmod(temp_path, 0o600)

        # Write content
        with open(temp_path, 'w') as f:
            f.write(self._build_env_content(credentials))

        # Atomic rename (POSIX guarantees atomicity)
        Path(temp_path).replace(self.env_path)

    except Exception as e:
        # Cleanup on failure
        Path(temp_path).unlink(missing_ok=True)
        raise IOError(f"Failed to update .env atomically: {e}")
```

#### SR-7: Path Traversal Protection
```python
def __init__(self, env_path: Path = Path('.env')):
    """Initialize with path validation."""
    # MUST IMPLEMENT: Resolve and validate path
    self.env_path = env_path.resolve()

    # Prevent path traversal attacks
    cwd = Path.cwd().resolve()
    try:
        self.env_path.relative_to(cwd)
    except ValueError:
        raise SecurityError(
            f"Invalid .env path: {env_path} is outside working directory"
        )

    # Reject suspicious paths
    if '..' in env_path.parts:
        raise SecurityError("Path traversal attempt detected in .env path")

    # Validate filename
    if self.env_path.name not in {'.env', '.env.local', '.env.development'}:
        logger.warning(f"Unusual .env filename: {self.env_path.name}")
```

### 2.3 Password Generation Security

#### SR-8: Strong Password Generation
```python
import secrets
import string

def _generate_password(self, length: int = 32) -> str:
    """Generate cryptographically secure password."""
    # MUST IMPLEMENT: Use secrets module (not random!)

    # Use URL-safe characters (base64-like)
    # Avoids special chars that might cause issues in URLs/configs
    password = secrets.token_urlsafe(length)

    # Alternative: More control over character set
    # alphabet = string.ascii_letters + string.digits + '-_=+'
    # password = ''.join(secrets.choice(alphabet) for _ in range(length))

    logger.info(f"Generated secure password ({length} chars)")
    return password

# Spec says: secrets.token_urlsafe(16) - GOOD! ✅
# Ensure this is actually used, not random.choice() ❌
```

---

## 3. Docker Security

### 3.1 Docker Socket Access

**RISK:** Docker socket access is equivalent to root access on the host.

#### SR-9: Docker Permission Validation
```python
import docker
from docker.errors import DockerException

class DockerSecurityValidator:
    """Validates Docker access security."""

    @staticmethod
    def validate_docker_access() -> bool:
        """Check Docker access is appropriate."""
        try:
            client = docker.from_env()

            # Check if running as root (security risk indicator)
            if os.getuid() == 0:
                logger.warning(
                    "Running as root with Docker access - potential security risk"
                )

            # Verify we can only access our own containers
            # (can't enforce, but can warn if too many containers visible)
            all_containers = client.containers.list(all=True)
            if len(all_containers) > 50:
                logger.warning(
                    f"Docker access can see {len(all_containers)} containers - "
                    "ensure this is expected"
                )

            return True

        except DockerException as e:
            logger.error(f"Docker access validation failed: {e}")
            return False
```

#### SR-10: Container Inspection Limits
```python
class Neo4jDetector:
    def find_containers(self) -> List[Neo4jContainer]:
        """Find Neo4j containers with security limits."""
        try:
            # MUST IMPLEMENT: Only list containers (don't inspect all)
            all_containers = self.docker.containers.list(
                all=True,
                filters={'ancestor': 'neo4j'}  # Filter at Docker level
            )

            # Limit to reasonable number (prevent DoS)
            MAX_CONTAINERS = 100
            if len(all_containers) > MAX_CONTAINERS:
                logger.warning(
                    f"Found {len(all_containers)} Neo4j containers, "
                    f"limiting to {MAX_CONTAINERS}"
                )
                all_containers = all_containers[:MAX_CONTAINERS]

            # Only inspect Neo4j containers
            neo4j_containers = []
            for container in all_containers:
                if self.is_neo4j_container(container):
                    neo4j_containers.append(self._extract_info(container))

            return sorted(neo4j_containers, key=lambda c: c.created, reverse=True)

        except docker.errors.APIError as e:
            logger.error(f"Docker API error: {e}")
            raise DockerException("Failed to list containers") from e
```

### 3.2 Container Name Injection Prevention

#### SR-11: Sanitize Container Data
```python
import re

def _sanitize_container_name(self, name: str) -> str:
    """Sanitize container name to prevent injection."""
    # MUST IMPLEMENT: Validate and sanitize container names

    # Docker container names must match: [a-zA-Z0-9][a-zA-Z0-9_.-]*
    if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9_.-]*$', name):
        logger.warning(f"Container has unusual name: {name}")
        # Remove dangerous characters
        sanitized = re.sub(r'[^a-zA-Z0-9_.-]', '_', name)
        logger.info(f"Sanitized to: {sanitized}")
        return sanitized

    return name

def _extract_env_value(self, env_vars: List[str], key: str) -> Optional[str]:
    """Safely extract environment variable value."""
    for env in env_vars:
        if '=' not in env:
            continue

        env_key, env_value = env.split('=', 1)
        if env_key == key:
            # MUST IMPLEMENT: Validate extracted value
            if '\0' in env_value:
                logger.error(f"Null byte detected in {key} - possible injection")
                return None

            # Check for suspicious patterns
            if any(pattern in env_value for pattern in ['$(', '`', '${', '|', ';']):
                logger.warning(f"Suspicious pattern in {key}: {env_value[:50]}")

            return env_value

    return None
```

### 3.3 Docker Image Validation

```python
def is_neo4j_container(self, container) -> bool:
    """Validate container is legitimate Neo4j."""
    # MUST IMPLEMENT: Check image source
    image_name = container.image.tags[0] if container.image.tags else ""

    # Allowlist official images
    TRUSTED_IMAGES = [
        'neo4j',
        'neo4j:latest',
        'neo4j:5',
        'neo4j:4',
        'docker.io/library/neo4j',
    ]

    # Check if official or warn
    if not any(image_name.startswith(trusted) for trusted in TRUSTED_IMAGES):
        logger.warning(
            f"Container {container.name} uses non-official image: {image_name}"
        )
        # Continue but log for audit

    return 'neo4j' in image_name.lower()
```

---

## 4. User Input Validation

### 4.1 Choice Validation

#### SR-12: Input Sanitization
```python
import select
import sys

def _get_user_choice(self, num_choices: int, timeout: int = 30) -> Optional[int]:
    """Get validated user choice with timeout."""
    # MUST IMPLEMENT: Timeout to prevent hangs
    MAX_ATTEMPTS = 3
    attempt = 0

    while attempt < MAX_ATTEMPTS:
        attempt += 1
        print(f"\nEnter choice (1-{num_choices}): ", end='', flush=True)

        # Timeout after 30 seconds
        if sys.platform != 'win32':
            ready, _, _ = select.select([sys.stdin], [], [], timeout)
            if not ready:
                logger.info("Input timeout - defaulting to skip")
                return None

        try:
            user_input = input().strip()

            # Validate input
            if not user_input:
                print("Error: Empty input")
                continue

            # Must be numeric
            if not user_input.isdigit():
                print(f"Error: Invalid input '{user_input}' - must be a number")
                continue

            choice = int(user_input)

            # Must be in range
            if choice < 1 or choice > num_choices:
                print(f"Error: Choice must be between 1 and {num_choices}")
                continue

            return choice

        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user")
            return None
        except EOFError:
            print("\n\nEOF detected - skipping Neo4j setup")
            return None
        except ValueError:
            print(f"Error: Invalid number format")
            continue

    logger.warning(f"Max attempts ({MAX_ATTEMPTS}) exceeded")
    return None
```

---

## 5. Network Security

### 5.1 Port Binding Security

#### SR-13: Prevent Privileged Port Binding
```python
def _find_available_ports(self) -> Tuple[int, int]:
    """Find available ports with security checks."""
    import socket

    # MUST IMPLEMENT: Prevent binding to privileged ports
    MIN_PORT = 1024  # Avoid privileged ports (< 1024)
    MAX_PORT = 65535

    def is_port_available(port: int) -> bool:
        """Check if port is available and safe to use."""
        if port < MIN_PORT:
            logger.error(f"Attempted to bind privileged port {port}")
            return False

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                # Bind to localhost only (not 0.0.0.0)
                s.bind(('127.0.0.1', port))
                return True
        except OSError:
            return False

    # Start from default ports
    http_port = 7474
    bolt_port = 7687

    # Find available HTTP port
    while http_port < MAX_PORT and not is_port_available(http_port):
        http_port += 1

    if http_port >= MAX_PORT:
        raise RuntimeError("No available ports for Neo4j HTTP")

    # Find available Bolt port (must not conflict with HTTP)
    while bolt_port < MAX_PORT and (bolt_port == http_port or not is_port_available(bolt_port)):
        bolt_port += 1

    if bolt_port >= MAX_PORT:
        raise RuntimeError("No available ports for Neo4j Bolt")

    logger.info(f"Selected ports: HTTP={http_port}, Bolt={bolt_port}")
    return http_port, bolt_port
```

### 5.2 Connection Security Guidance

```python
def _write_security_notice(self, env_path: Path) -> None:
    """Write security notice to .env file."""
    notice = """
# SECURITY NOTICE:
# - Neo4j credentials are stored in plaintext in this file
# - Ensure this file has permissions 0600 (owner read/write only)
# - Never commit this file to version control
# - Use encrypted connection (bolt+s://) in production
# - Change default password immediately
# - Consider using Docker secrets for production deployments
"""

    # Append to .env if not already present
    with open(env_path, 'r') as f:
        content = f.read()

    if 'SECURITY NOTICE' not in content:
        with open(env_path, 'a') as f:
            f.write(notice)
```

---

## 6. Attack Scenario Analysis

### Scenario 1: Malicious Container Name Injection

**Attack:**
```python
# Attacker creates container with malicious name
docker run --name "neo4j; rm -rf /" neo4j:latest
```

**Mitigation:**
- SR-11: Sanitize container names
- Never use container names in shell commands
- Use parameterized Docker API calls only

**Test Case:**
```python
def test_malicious_container_name():
    malicious_names = [
        "neo4j; rm -rf /",
        "neo4j`whoami`",
        "neo4j$(curl evil.com)",
        "neo4j/../../../etc/passwd",
    ]
    for name in malicious_names:
        sanitized = detector._sanitize_container_name(name)
        assert ';' not in sanitized
        assert '`' not in sanitized
        assert '$' not in sanitized
        assert '..' not in sanitized
```

### Scenario 2: Environment Variable Injection

**Attack:**
```python
# Attacker sets NEO4J_AUTH with injection payload
docker run -e "NEO4J_AUTH=admin/password\nADMIN_TOKEN=stolen" neo4j
```

**Mitigation:**
- SR-4: Validate password format
- Reject passwords with newlines, null bytes
- Log suspicious patterns

**Test Case:**
```python
def test_password_injection():
    malicious_passwords = [
        "pass\nADMIN_TOKEN=evil",
        "pass\0hidden",
        "pass;ls -la",
        "pass`whoami`",
    ]
    for password in malicious_passwords:
        assert not validator._validate_password(password)
```

### Scenario 3: .env File Permission Race

**Attack:**
```bash
# Attacker monitors .env creation and reads before chmod
while true; do cat .env 2>/dev/null && break; done
```

**Mitigation:**
- SR-5: Create file with secure permissions BEFORE writing content
- SR-6: Use atomic operations
- Verify permissions after write

**Test Case:**
```python
def test_env_file_permissions_race():
    import threading
    import time

    def attacker_thread(stop_event):
        while not stop_event.is_set():
            try:
                with open('.env', 'r') as f:
                    perms = os.stat('.env').st_mode & 0o777
                    if perms != 0o600:
                        raise SecurityError(f"Insecure permissions detected: {oct(perms)}")
            except FileNotFoundError:
                pass
            time.sleep(0.001)

    stop = threading.Event()
    attacker = threading.Thread(target=attacker_thread, args=(stop,))
    attacker.start()

    try:
        # Perform sync
        synchronizer.sync(credentials)
    finally:
        stop.set()
        attacker.join()
```

### Scenario 4: Docker Socket Privilege Escalation

**Attack:**
```python
# If attacker compromises Neo4j sync, they have Docker access
# They can inspect ALL containers and extract secrets
```

**Mitigation:**
- SR-9: Validate Docker access is appropriate
- SR-10: Limit container inspection scope
- Principle of Least Privilege: only request what's needed

**Test Case:**
```python
def test_docker_access_limits():
    # Ensure we only inspect Neo4j containers
    detector = Neo4jDetector(docker_client)
    containers = detector.find_containers()

    for container in containers:
        assert 'neo4j' in container.image.lower()
```

### Scenario 5: Password Logging/Memory Disclosure

**Attack:**
```bash
# Attacker reads logs or memory dumps to find passwords
grep -r "NEO4J_PASSWORD" /var/log/
strings /proc/$(pidof python)/mem | grep neo4j
```

**Mitigation:**
- SR-1: Never log passwords
- SR-2: Mask password display
- SR-3: Use SecureString wrapper (best effort in Python)

**Test Case:**
```python
def test_no_password_in_logs(caplog):
    extractor.extract(container)

    # Check no password appears in logs
    for record in caplog.records:
        assert 'secretpassword123' not in record.message.lower()
        assert 'password' not in record.message.lower() or '***' in record.message
```

---

## 7. Security Requirements Summary

### MUST IMPLEMENT (Critical)

| ID | Requirement | Component | Priority |
|----|-------------|-----------|----------|
| SR-1 | Never log or print passwords | CredentialExtractor | CRITICAL |
| SR-2 | Mask passwords in display | Neo4jManager | CRITICAL |
| SR-3 | Secure password string handling | Neo4jCredentials | HIGH |
| SR-4 | Validate extracted passwords | CredentialExtractor | HIGH |
| SR-5 | Enforce .env permissions (0600) | CredentialSynchronizer | CRITICAL |
| SR-6 | Atomic file operations | CredentialSynchronizer | HIGH |
| SR-7 | Path traversal protection | CredentialSynchronizer | HIGH |
| SR-8 | Strong password generation | Neo4jManager | HIGH |
| SR-9 | Docker permission validation | DockerSecurityValidator | MEDIUM |
| SR-10 | Container inspection limits | Neo4jDetector | MEDIUM |
| SR-11 | Sanitize container data | Neo4jDetector | HIGH |
| SR-12 | Input validation with timeout | Neo4jManager | MEDIUM |
| SR-13 | Prevent privileged port binding | Neo4jManager | MEDIUM |

### SHOULD IMPLEMENT (Important)

1. **Audit Logging** - Log all security-relevant events (credential extraction, .env modification)
2. **Security Notices** - Add security warnings to .env file
3. **Connection Encryption** - Recommend bolt+s:// for production
4. **Credential Rotation** - Document password rotation best practices
5. **Docker Image Validation** - Warn on non-official Neo4j images

### COULD IMPLEMENT (Nice to Have)

1. **Encrypted .env Storage** - Use system keyring for credentials
2. **Docker Secrets Integration** - Support reading from Docker secrets
3. **TLS Certificate Validation** - Verify Neo4j TLS certificates
4. **Rate Limiting** - Limit Docker API calls
5. **Anomaly Detection** - Flag unusual credential patterns

---

## 8. Testing Strategy for Security

### Unit Tests

```python
# test_security.py

class TestCredentialSecurity:
    """Security-focused tests for credential handling."""

    def test_no_password_logging(self, caplog):
        """Ensure passwords never appear in logs."""
        extractor = CredentialExtractor(mock_docker)
        creds = extractor.extract(mock_container)

        for record in caplog.records:
            assert creds.password not in record.message

    def test_password_masking_display(self, capsys):
        """Ensure passwords are masked in output."""
        manager._display_container_info(container, credentials)
        captured = capsys.readouterr()

        assert credentials.password not in captured.out
        assert '***' in captured.out or 'REDACTED' in captured.out

    def test_env_file_permissions(self, tmp_path):
        """Verify .env has secure permissions."""
        env_path = tmp_path / '.env'
        synchronizer = CredentialSynchronizer(env_path)
        synchronizer.sync(credentials)

        perms = env_path.stat().st_mode & 0o777
        assert perms == 0o600, f"Insecure permissions: {oct(perms)}"

    def test_atomic_file_write(self, tmp_path):
        """Ensure .env writes are atomic."""
        env_path = tmp_path / '.env'
        env_path.write_text("OLD=value\n")

        # Simulate crash mid-write
        with pytest.raises(Exception):
            with mock.patch('pathlib.Path.replace', side_effect=OSError):
                synchronizer.sync(credentials)

        # Original file should be unchanged
        assert env_path.read_text() == "OLD=value\n"

    def test_path_traversal_prevention(self):
        """Reject path traversal attempts."""
        malicious_paths = [
            Path('../../../etc/passwd'),
            Path('/etc/passwd'),
            Path('../../.env'),
        ]
        for path in malicious_paths:
            with pytest.raises(SecurityError):
                CredentialSynchronizer(path)

    def test_container_name_sanitization(self):
        """Sanitize malicious container names."""
        malicious_names = [
            "neo4j; rm -rf /",
            "neo4j`whoami`",
            "neo4j$(curl evil.com)",
        ]
        for name in malicious_names:
            sanitized = detector._sanitize_container_name(name)
            assert ';' not in sanitized
            assert '`' not in sanitized
            assert '$(' not in sanitized

    def test_password_validation(self):
        """Validate password format."""
        # Should reject control characters
        assert not validator._validate_password("pass\n")
        assert not validator._validate_password("pass\0")
        assert not validator._validate_password("pass;cmd")

        # Should warn on weak passwords
        with pytest.warns(UserWarning):
            validator._validate_password("neo4j")

    def test_privileged_port_rejection(self):
        """Prevent binding to privileged ports."""
        with mock.patch('socket.socket') as mock_socket:
            # Port 80 should be rejected
            with pytest.raises(ValueError):
                manager._find_available_ports(start_http=80)

    def test_input_timeout(self, monkeypatch):
        """Ensure input timeout works."""
        def mock_select(*args):
            return [], [], []  # Timeout

        monkeypatch.setattr('select.select', mock_select)
        choice = manager._get_user_choice(4, timeout=1)
        assert choice is None  # Should timeout

    def test_docker_access_validation(self):
        """Validate Docker access is appropriate."""
        validator = DockerSecurityValidator()
        assert validator.validate_docker_access()

        # Should warn if too many containers
        with mock.patch.object(mock_client.containers, 'list', return_value=[mock] * 100):
            with pytest.warns(UserWarning):
                validator.validate_docker_access()
```

### Integration Tests

```python
class TestSecurityIntegration:
    """End-to-end security tests."""

    @pytest.mark.docker
    def test_real_container_credential_extraction(self):
        """Test with real Neo4j container."""
        # Start container with known password
        container = docker_client.containers.run(
            'neo4j:latest',
            environment={'NEO4J_AUTH': 'neo4j/testpass123'},
            detach=True,
            remove=True
        )

        try:
            detector = Neo4jDetector(docker_client)
            containers = detector.find_containers()
            assert len(containers) > 0

            extractor = CredentialExtractor(docker_client)
            creds = extractor.extract(containers[0])

            assert creds.username == 'neo4j'
            assert creds.password == 'testpass123'
            assert creds.source == 'env_var'

        finally:
            container.stop()

    def test_full_sync_flow_security(self, tmp_path):
        """Test complete flow maintains security."""
        env_path = tmp_path / '.env'

        manager = Neo4jManager(docker_client, env_path)
        with mock.patch('builtins.input', return_value='1'):
            decision = manager.check_and_sync()

        # Verify .env has secure permissions
        assert env_path.stat().st_mode & 0o777 == 0o600

        # Verify backup has secure permissions
        backup_files = list(tmp_path.glob('.env.backup.*'))
        assert len(backup_files) == 1
        assert backup_files[0].stat().st_mode & 0o777 == 0o600

        # Verify no passwords in logs
        # (requires caplog fixture)
```

### Penetration Testing Scenarios

```python
class TestPenetrationScenarios:
    """Adversarial security tests."""

    def test_concurrent_env_file_access(self, tmp_path):
        """Test race condition on .env file."""
        import threading
        import time

        env_path = tmp_path / '.env'
        synchronizer = CredentialSynchronizer(env_path)

        results = {'insecure_read': False}

        def attacker_thread():
            for _ in range(100):
                try:
                    if env_path.exists():
                        perms = env_path.stat().st_mode & 0o777
                        if perms != 0o600:
                            results['insecure_read'] = True
                except FileNotFoundError:
                    pass
                time.sleep(0.001)

        attacker = threading.Thread(target=attacker_thread)
        attacker.start()

        # Perform 10 syncs while attacker watches
        for _ in range(10):
            synchronizer.sync(make_credentials())
            time.sleep(0.01)

        attacker.join()
        assert not results['insecure_read'], "Race condition detected"

    def test_command_injection_via_container_name(self):
        """Attempt command injection through container name."""
        malicious_container = mock.Mock()
        malicious_container.name = "neo4j; curl http://evil.com"
        malicious_container.status = "running"

        detector = Neo4jDetector(mock_client)
        sanitized_name = detector._sanitize_container_name(malicious_container.name)

        # Should not contain command injection chars
        assert ';' not in sanitized_name
        assert 'curl' not in sanitized_name or ';' not in sanitized_name

    def test_env_variable_injection(self):
        """Attempt injection via NEO4J_AUTH environment variable."""
        malicious_auth = "admin/pass\\nADMIN=true\\nROOT_ACCESS=1"

        extractor = CredentialExtractor(mock_client)
        username, password = extractor._parse_neo4j_auth(malicious_auth)

        # Should only get username and password, not additional injected vars
        assert '\\n' not in password or password == malicious_auth.split('/')[1]
        # Additional validation should reject this
        assert not extractor._validate_password(password)
```

---

## 9. Mitigation Strategies by Attack Vector

| Attack Vector | Mitigation | Implementation |
|---------------|------------|----------------|
| Password Logging | SR-1: No logging | Review all log statements |
| Memory Disclosure | SR-3: SecureString | Wrap sensitive strings |
| .env Race Condition | SR-6: Atomic writes | Use temp file + rename |
| .env Permissions | SR-5: Mode 0600 | Set before writing content |
| Path Traversal | SR-7: Path validation | Check relative_to(cwd) |
| Container Name Injection | SR-11: Sanitize names | Regex validation |
| Env Var Injection | SR-4: Validate passwords | Check for control chars |
| Port Privilege Escalation | SR-13: Port range limits | min_port = 1024 |
| Docker Access Abuse | SR-9, SR-10: Validate scope | Limit inspection |
| User Input Injection | SR-12: Input validation | Timeout + validation |
| Weak Passwords | SR-8: Strong generation | secrets.token_urlsafe(32) |
| MITM on Neo4j | Documentation | Recommend bolt+s:// |

---

## 10. Security Checklist for Implementation

### Before Coding
- [ ] Review all security requirements (SR-1 through SR-13)
- [ ] Understand threat model
- [ ] Set up security testing environment

### During Implementation
- [ ] No passwords in log statements
- [ ] No passwords in print statements
- [ ] Mask passwords in user-facing output
- [ ] .env file created with mode 0600
- [ ] Atomic file operations for .env
- [ ] Path validation for .env location
- [ ] Container name sanitization
- [ ] Password format validation
- [ ] Docker access scope limitation
- [ ] User input timeout and validation
- [ ] Port range validation (>= 1024)
- [ ] Strong password generation (secrets module)

### Code Review
- [ ] Search codebase for `print.*password` (should be 0 results)
- [ ] Search codebase for `log.*password` (should be 0 results)
- [ ] Verify all .env operations use atomic writes
- [ ] Verify all path operations validate traversal
- [ ] Verify all user input is validated
- [ ] Check Docker API calls are scoped appropriately

### Testing
- [ ] Run all security unit tests
- [ ] Run penetration test scenarios
- [ ] Manual test with malicious container names
- [ ] Manual test with malicious env vars
- [ ] Verify .env permissions after sync
- [ ] Test concurrent access scenarios

### Documentation
- [ ] Document security assumptions
- [ ] Add security notices to .env file
- [ ] Document credential rotation process
- [ ] Provide secure configuration examples

---

## 11. Security Assumptions and Limitations

### Assumptions

1. **Docker Daemon is Trusted** - We assume the Docker daemon itself is not compromised
2. **Filesystem is Secure** - We assume the underlying filesystem enforces permissions correctly
3. **User is Legitimate** - We assume the user running the tool is authorized
4. **No Physical Access** - We assume attacker doesn't have physical access to the machine
5. **Python Runtime is Secure** - We assume Python interpreter and stdlib are not compromised

### Known Limitations

1. **Python String Immutability** - Cannot truly wipe passwords from memory (SR-3 is best effort)
2. **Docker Socket Access** - Access to Docker socket is equivalent to root (cannot prevent abuse)
3. **.env is Plaintext** - Credentials stored in plaintext (OS keyring would be better)
4. **No Secret Rotation** - Feature doesn't include automatic credential rotation
5. **No Encryption in Transit** - Feature doesn't enforce TLS for Neo4j connections

### Out of Scope

The following security concerns are explicitly out of scope for this feature:

- Neo4j database security (authentication, authorization, encryption)
- Docker container security hardening
- Network segmentation and firewall rules
- Secret management systems integration (Vault, etc.)
- Audit logging infrastructure
- Security monitoring and alerting
- Credential rotation automation
- Encrypted .env storage

---

## 12. Compliance Considerations

### GDPR (if Neo4j stores personal data)

- .env file may contain credentials that access personal data
- Ensure .env is not backed up to insecure locations
- Document data retention for .env.backup files

### SOC 2 (if applicable)

- Implement audit logging for credential access
- Document security controls in this analysis
- Maintain change log for .env modifications

### PCI DSS (if Neo4j stores payment data)

- .env file permissions (0600) satisfy "restrict access" requirement
- Avoid default passwords (SR-4 validates this)
- Implement logging for security-relevant events

---

## 13. Recommendations for Future Enhancement

### Short Term (Next Sprint)

1. **Audit Logging Module** - Log all credential operations to secure audit log
2. **Security Test Suite** - Implement all tests from Section 8
3. **Documentation** - Security best practices guide for users

### Medium Term (Next Quarter)

1. **Keyring Integration** - Store credentials in OS keyring instead of .env
2. **Docker Secrets Support** - Read from Docker secrets when available
3. **TLS Enforcement** - Validate Neo4j TLS certificates

### Long Term (Future)

1. **Credential Rotation** - Automated password rotation
2. **Security Scanning** - Integrate with secret scanning tools
3. **HSM Support** - Hardware security module for credential storage

---

## 14. Conclusion

The Neo4j container detection and credential synchronization feature introduces **MEDIUM-HIGH** security risk due to:

1. **Sensitive Credential Handling** - Passwords extracted and stored in plaintext
2. **Docker Socket Access** - Equivalent to root access on host
3. **Filesystem Operations** - Race conditions and permission issues possible

**Critical Path to Secure Implementation:**

1. ✅ Implement all 13 security requirements (SR-1 through SR-13)
2. ✅ Execute comprehensive security test suite
3. ✅ Conduct code review with security focus
4. ✅ Document security assumptions and limitations
5. ✅ Provide user security guidance

**If implemented correctly with all security requirements, this feature is SAFE to deploy.**

**If security requirements are skipped or partially implemented, this feature poses SIGNIFICANT RISK.**

---

## Appendix A: Security Requirement Traceability Matrix

| Requirement | File | Method | Test |
|-------------|------|--------|------|
| SR-1: No password logging | credential_sync.py | CredentialExtractor.extract() | test_no_password_logging |
| SR-2: Mask password display | manager.py | Neo4jManager._display_container_info() | test_password_masking_display |
| SR-3: Secure string handling | credential_sync.py | Neo4jCredentials dataclass | test_secure_string_wrapper |
| SR-4: Validate passwords | credential_sync.py | CredentialExtractor._validate_password() | test_password_validation |
| SR-5: .env permissions | credential_sync.py | CredentialSynchronizer.sync() | test_env_file_permissions |
| SR-6: Atomic operations | credential_sync.py | CredentialSynchronizer.sync() | test_atomic_file_write |
| SR-7: Path traversal | credential_sync.py | CredentialSynchronizer.__init__() | test_path_traversal_prevention |
| SR-8: Strong passwords | manager.py | Neo4jManager._generate_password() | test_password_strength |
| SR-9: Docker validation | detector.py | DockerSecurityValidator.validate() | test_docker_access_validation |
| SR-10: Inspection limits | detector.py | Neo4jDetector.find_containers() | test_container_limit |
| SR-11: Sanitize names | detector.py | Neo4jDetector._sanitize_container_name() | test_container_name_sanitization |
| SR-12: Input validation | manager.py | Neo4jManager._get_user_choice() | test_input_timeout |
| SR-13: Port validation | manager.py | Neo4jManager._find_available_ports() | test_privileged_port_rejection |

---

## Appendix B: Security Code Review Checklist

```bash
# Run these checks before merging

# 1. No password in logs
grep -r "log.*password" src/amplihack/neo4j/
# Expected: 0 results (except in comments about NOT logging)

# 2. No password in prints
grep -r "print.*password" src/amplihack/neo4j/
# Expected: 0 results (except masked output)

# 3. .env permissions set
grep -r "chmod.*0600" src/amplihack/neo4j/
# Expected: At least 2 results (initial + verification)

# 4. Atomic file operations
grep -r "\.replace(" src/amplihack/neo4j/
# Expected: At least 1 result (atomic rename)

# 5. Path validation
grep -r "relative_to" src/amplihack/neo4j/
# Expected: At least 1 result (path traversal check)

# 6. Password generation uses secrets
grep -r "secrets\.token" src/amplihack/neo4j/
# Expected: At least 1 result

# 7. Input validation with timeout
grep -r "select\.select" src/amplihack/neo4j/
# Expected: At least 1 result (timeout implementation)

# 8. Container name sanitization
grep -r "sanitize.*name" src/amplihack/neo4j/
# Expected: At least 1 result

# 9. Run security tests
pytest tests/test_security.py -v
# Expected: All pass

# 10. Type checking
pyright src/amplihack/neo4j/
# Expected: 0 errors

# 11. Linting
ruff check src/amplihack/neo4j/
# Expected: 0 errors
```

---

**Document Version:** 1.0
**Last Updated:** 2025-11-07
**Next Review:** Before PR merge for Issue #1170
**Owner:** Security Agent (Claude Code)
**Status:** Final - Ready for Implementation Review
