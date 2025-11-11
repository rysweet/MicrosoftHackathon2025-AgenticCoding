# Neo4j Container Sync - Builder Quick Reference

## TL;DR for Builder Agent

You are building a Neo4j container detection and credential synchronization feature. This guide gives you everything needed to implement it correctly.

## What You're Building

**User Story:**
When launcher starts, detect existing Neo4j containers, show user their options, and sync credentials to .env based on their choice.

**4 User Choices (REQUIRED):**
1. Use existing container (sync its credentials to .env)
2. Create new container (prep .env, don't actually create yet)
3. Manual configuration (user will handle .env themselves)
4. Skip Neo4j setup (continue without Neo4j)

## Implementation Order (CRITICAL)

**Build in this exact order:**

1. **neo4j/detector.py** (no dependencies on new code)
2. **neo4j/credential_sync.py** (depends on detector)
3. **neo4j/manager.py** (depends on both above)
4. **launcher/core.py modification** (depends on manager)

## File Structure

```
neo4j/
├── __init__.py          # Package exports
├── detector.py          # Container detection logic
├── credential_sync.py   # Credential extraction & .env sync
└── manager.py           # User interaction & orchestration
```

## Core Data Structures

```python
# neo4j/detector.py
@dataclass
class Neo4jContainer:
    container_id: str
    name: str
    status: str              # 'running' or 'exited'
    ports: Dict[str, int]    # {'http': 7474, 'bolt': 7687}
    image: str
    created: datetime

# neo4j/credential_sync.py
@dataclass
class Neo4jCredentials:
    username: str
    password: str
    http_port: int
    bolt_port: int
    source: str              # 'env_var', 'docker_secret', 'default'

# neo4j/manager.py
@dataclass
class SyncDecision:
    action: str              # 'use_existing', 'create_new', 'manual', 'skip'
    container: Optional[Neo4jContainer]
    credentials: Optional[Neo4jCredentials]
```

## Key Implementation Details

### 1. Detector: Finding Containers

```python
# neo4j/detector.py
class Neo4jDetector:
    def find_containers(self) -> List[Neo4jContainer]:
        """Find all Neo4j containers (running and stopped)."""
        # Use docker.from_env()
        # Filter: all=True (include stopped)
        # Check: 'neo4j' in image name
        # Sort: by creation time (newest first)
        # Extract: ports from container.attrs['NetworkSettings']['Ports']
```

**Port Extraction Logic:**
```python
def extract_ports(self, container) -> Dict[str, int]:
    ports = {}
    port_bindings = container.attrs['NetworkSettings']['Ports']

    # HTTP: 7474/tcp -> 7474
    if '7474/tcp' in port_bindings:
        ports['http'] = port_bindings['7474/tcp'][0]['HostPort']

    # Bolt: 7687/tcp -> 7687
    if '7687/tcp' in port_bindings:
        ports['bolt'] = port_bindings['7687/tcp'][0]['HostPort']

    return ports
```

### 2. Credentials: Extraction & Sync

```python
# neo4j/credential_sync.py
class CredentialExtractor:
    def extract(self, container: Neo4jContainer) -> Optional[Neo4jCredentials]:
        """Extract credentials from container env vars."""
        # Priority 1: NEO4J_AUTH (format: username/password)
        # Priority 2: NEO4J_PASSWORD (username defaults to 'neo4j')
        # Priority 3: Return None (can't determine)

        env_vars = {e.split('=')[0]: e.split('=')[1]
                    for e in container.attrs['Config']['Env']}

        if 'NEO4J_AUTH' in env_vars:
            username, password = env_vars['NEO4J_AUTH'].split('/')
            return Neo4jCredentials(username, password, ..., 'env_var')

        if 'NEO4J_PASSWORD' in env_vars:
            return Neo4jCredentials('neo4j', env_vars['NEO4J_PASSWORD'], ..., 'env_var')

        return None  # Can't extract
```

```python
class CredentialSynchronizer:
    def sync(self, credentials: Neo4jCredentials) -> None:
        """Update .env with credentials."""
        # 1. Backup .env to .env.backup.<timestamp>
        # 2. Read .env into dict
        # 3. Update these keys:
        #    - NEO4J_USER
        #    - NEO4J_PASSWORD
        #    - NEO4J_HTTP_PORT
        #    - NEO4J_BOLT_PORT
        # 4. Write back to .env (preserve other keys)
```

**.env Update Pattern:**
```python
def sync(self, credentials: Neo4jCredentials) -> None:
    # Backup first
    self.backup()

    # Read existing
    env_dict = {}
    if self.env_path.exists():
        with open(self.env_path) as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    env_dict[key] = value

    # Update Neo4j keys
    env_dict['NEO4J_USER'] = credentials.username
    env_dict['NEO4J_PASSWORD'] = credentials.password
    env_dict['NEO4J_HTTP_PORT'] = str(credentials.http_port)
    env_dict['NEO4J_BOLT_PORT'] = str(credentials.bolt_port)

    # Write back
    with open(self.env_path, 'w') as f:
        for key, value in env_dict.items():
            f.write(f'{key}={value}\n')
```

### 3. Manager: User Interaction

```python
# neo4j/manager.py
class Neo4jManager:
    def check_and_sync(self) -> SyncDecision:
        """Main entry point."""
        containers = self.detector.find_containers()

        if not containers:
            return self._handle_no_containers()

        return self._handle_existing_containers(containers)
```

**User Prompt Format (EXACT):**
```
Neo4j Container Detected!

Found: neo4j-dev (running)
Ports: HTTP=7474, Bolt=7687
Credentials: neo4j / ******** (from NEO4J_AUTH)

Choose an option:
1. Use existing container (sync credentials to .env)
2. Create new container (amplihack managed, different ports)
3. Manual configuration (I'll set .env myself)
4. Skip Neo4j setup

Enter choice (1-4): _
```

**Choice Handling:**
```python
def _handle_existing_containers(self, containers: List[Neo4jContainer]) -> SyncDecision:
    container = containers[0]  # Most recent
    credentials = self.extractor.extract(container)

    self._display_container_info(container, credentials)
    choice = self._get_user_choice(4)

    if choice == 1:
        return self._execute_use_existing(container, credentials)
    elif choice == 2:
        return self._execute_create_new()
    elif choice == 3:
        return SyncDecision(action='manual', container=container, credentials=credentials)
    else:
        return SyncDecision(action='skip', container=None, credentials=None)
```

**Port Availability Check:**
```python
def _find_available_ports(self) -> Tuple[int, int]:
    """Find available ports starting from 7474/7687."""
    http_port = 7474
    while not self._is_port_available(http_port):
        http_port += 1

    bolt_port = 7687
    while not self._is_port_available(bolt_port):
        bolt_port += 1

    return (http_port, bolt_port)

def _is_port_available(self, port: int) -> bool:
    """Check if port is available."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('localhost', port))
        sock.close()
        return True
    except OSError:
        return False
```

### 4. Integration: Launcher Hook

```python
# launcher/core.py (in main() function)
def main():
    """Main entry point."""
    # ... existing proxy setup ...

    # Neo4j Container Detection & Sync (NEW)
    try:
        from neo4j.manager import Neo4jManager
        import docker

        docker_client = docker.from_env()
        neo4j_mgr = Neo4jManager(docker_client)
        decision = neo4j_mgr.check_and_sync()

        if decision.action == 'create_new':
            logger.info("Neo4j container creation requested (not yet implemented)")

    except ImportError:
        logger.warning("Neo4j management not available")
    except docker.errors.DockerException:
        logger.warning("Docker not available - skipping Neo4j detection")
    except Exception as e:
        logger.error(f"Neo4j detection failed: {e}")

    # ... existing main loop ...
```

## Error Handling (CRITICAL)

**Never crash the launcher.** Every possible error must be caught and handled gracefully.

```python
# Docker daemon down
try:
    docker_client = docker.from_env()
except docker.errors.DockerException:
    logger.warning("Docker daemon not available - skipping Neo4j detection")
    return SyncDecision(action='skip', container=None, credentials=None)

# .env not writable
try:
    synchronizer.sync(credentials)
except IOError as e:
    logger.error(f"Cannot write to .env: {e}")
    return SyncDecision(action='manual', container=container, credentials=credentials)

# User input EOF (Ctrl+C)
try:
    choice = input("Enter choice (1-4): ")
except EOFError:
    return SyncDecision(action='skip', container=None, credentials=None)

# Invalid user input (re-prompt)
try:
    choice = int(input("Enter choice (1-4): "))
    if choice not in range(1, 5):
        print("Invalid choice. Please enter 1-4.")
        # Retry
except ValueError:
    print("Invalid input. Please enter a number.")
    # Retry
```

## Testing Requirements

### Unit Tests (Required)

**neo4j/detector.py:**
- `test_find_containers_running()` - Detect running container
- `test_find_containers_stopped()` - Detect stopped container
- `test_find_containers_none()` - Handle no containers
- `test_is_neo4j_container()` - Filter logic
- `test_extract_ports()` - Port extraction

**neo4j/credential_sync.py:**
- `test_extract_from_neo4j_auth()` - NEO4J_AUTH parsing
- `test_extract_from_neo4j_password()` - NEO4J_PASSWORD parsing
- `test_extract_none()` - No credentials case
- `test_sync_new_env()` - Create new .env
- `test_sync_existing_env()` - Update existing .env
- `test_backup()` - .env backup creation

**neo4j/manager.py:**
- `test_check_and_sync_no_containers()` - No containers flow
- `test_check_and_sync_with_containers()` - With containers flow
- `test_user_choice_1_through_4()` - Each choice path
- `test_invalid_user_input()` - Re-prompt logic
- `test_find_available_ports()` - Port conflict resolution

### Integration Tests (Required)

- `test_full_flow_detect_extract_sync()` - End-to-end with real Docker
- `test_docker_down_graceful_failure()` - Docker unavailable
- `test_env_not_writable()` - Permission error handling

### Manual Testing Checklist

- [ ] Start launcher with Neo4j container running
- [ ] Start launcher with Neo4j container stopped
- [ ] Start launcher with no Neo4j container
- [ ] Start launcher with Docker down
- [ ] Test choice 1 (use existing) - verify .env updated
- [ ] Test choice 2 (create new) - verify .env updated with new ports
- [ ] Test choice 3 (manual) - verify no .env changes
- [ ] Test choice 4 (skip) - verify no .env changes
- [ ] Test invalid input (letters, out of range) - verify re-prompt
- [ ] Test Ctrl+C during prompt - verify graceful exit
- [ ] Test multiple Neo4j containers - verify newest shown

## Common Pitfalls to Avoid

### ❌ Don't Do This:

1. **Hardcode port numbers**
   ```python
   # BAD
   return {'http': 7474, 'bolt': 7687}

   # GOOD
   return self.extract_ports(container)
   ```

2. **Crash on missing credentials**
   ```python
   # BAD
   credentials = self.extractor.extract(container)
   password = credentials.password  # Could be None!

   # GOOD
   credentials = self.extractor.extract(container)
   if credentials is None:
       print("Could not extract credentials")
       # Offer manual configuration
   ```

3. **Modify .env without backup**
   ```python
   # BAD
   with open('.env', 'w') as f:
       f.write(new_content)

   # GOOD
   self.synchronizer.backup()
   self.synchronizer.sync(credentials)
   ```

4. **Raise exceptions in manager**
   ```python
   # BAD
   raise ValueError("Invalid choice")

   # GOOD
   print("Invalid choice. Please enter 1-4.")
   return self._get_user_choice(num_choices)  # Retry
   ```

5. **Use relative imports**
   ```python
   # BAD
   from .detector import Neo4jDetector

   # GOOD
   from neo4j.detector import Neo4jDetector
   ```

## Code Style Requirements

**Type Hints (REQUIRED):**
```python
def find_containers(self) -> List[Neo4jContainer]:
    pass

def extract(self, container: Neo4jContainer) -> Optional[Neo4jCredentials]:
    pass
```

**Docstrings (REQUIRED):**
```python
def sync(self, credentials: Neo4jCredentials) -> None:
    """
    Update .env with new credentials.

    Creates backup before modification.
    Preserves other .env values.

    Args:
        credentials: Neo4j credentials to sync

    Raises:
        IOError: If .env not writable
    """
```

**Logging (REQUIRED):**
```python
import logging
logger = logging.getLogger(__name__)

logger.info("Found 3 Neo4j containers")
logger.warning("Could not extract credentials")
logger.error(f"Failed to sync: {e}")
```

## Definition of Done

- [ ] All files created in correct locations
- [ ] All classes and methods implemented (no stubs)
- [ ] All type hints present
- [ ] All docstrings present
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Manual testing checklist complete
- [ ] Ruff linting: 0 errors
- [ ] Pyright type checking: 0 errors
- [ ] Code review against spec completed
- [ ] Feature works end-to-end in launcher

## Quick Implementation Template

### neo4j/__init__.py
```python
"""Neo4j container management for amplihack."""

from neo4j.detector import Neo4jContainer, Neo4jDetector
from neo4j.credential_sync import (
    Neo4jCredentials,
    CredentialExtractor,
    CredentialSynchronizer,
)
from neo4j.manager import Neo4jManager, SyncDecision

__all__ = [
    'Neo4jContainer',
    'Neo4jDetector',
    'Neo4jCredentials',
    'CredentialExtractor',
    'CredentialSynchronizer',
    'Neo4jManager',
    'SyncDecision',
]
```

### Import Structure
```python
# neo4j/detector.py
import docker
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

# neo4j/credential_sync.py
import docker
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
import shutil
from neo4j.detector import Neo4jContainer

# neo4j/manager.py
import docker
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Tuple
import secrets
import socket
from neo4j.detector import Neo4jDetector, Neo4jContainer
from neo4j.credential_sync import (
    CredentialExtractor,
    CredentialSynchronizer,
    Neo4jCredentials,
)
```

## Questions to Ask If Stuck

1. **Does this match the spec?** (Check Specs/Neo4jContainerSync.md)
2. **Is this the simplest solution?** (No over-engineering)
3. **Does this handle errors gracefully?** (Never crash)
4. **Is this testable?** (Can you write a unit test?)
5. **Does this follow existing patterns?** (Check proxy/manager.py)

## Need More Detail?

- **Full Specification:** `/Users/ryan/src/amplihack/Specs/Neo4jContainerSync.md`
- **Class Diagrams:** `/Users/ryan/src/amplihack/Specs/Neo4jClassDiagram.md`
- **Existing Patterns:** Check `proxy/manager.py` and `docker/detector.py`

## Start Building

**First command:**
```bash
cd /Users/ryan/src/amplihack
mkdir -p neo4j
touch neo4j/__init__.py
```

**First file to implement:**
`neo4j/detector.py` - Has no dependencies on new code, easiest to test.

Good luck! Remember: Simple, tested, working code beats clever code every time.
