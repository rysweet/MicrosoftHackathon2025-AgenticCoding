# Neo4j Container Detection & Credential Synchronization

## Architecture Overview

### Problem Statement
Amplihack needs to detect existing Neo4j containers, extract credentials, and allow users to choose how to proceed with container management. The system must handle edge cases gracefully and integrate seamlessly with the launcher.

### Design Philosophy
- **Ruthless Simplicity**: Start with minimal necessary code
- **Modular Design**: Three focused modules with clear boundaries
- **Zero-BS**: No stubs, placeholders, or future-proofing
- **Fail-Fast**: Validate inputs, error clearly

---

## Module 1: neo4j/detector.py

### Purpose
Detect Neo4j containers (running or stopped) and extract basic information.

### Contract

**Input:**
- Docker client instance

**Output:**
```python
@dataclass
class Neo4jContainer:
    container_id: str        # Full container ID
    name: str                # Container name
    status: str              # 'running' or 'exited'
    ports: Dict[str, int]    # {'http': 7474, 'bolt': 7687}
    image: str               # Image name:tag
    created: datetime        # Container creation time
```

**Side Effects:**
- None (read-only Docker operations)

### Key Methods

```python
class Neo4jDetector:
    """Detects existing Neo4j containers."""

    def __init__(self, docker_client: docker.DockerClient):
        """Initialize detector with Docker client."""
        self.docker = docker_client

    def find_containers(self) -> List[Neo4jContainer]:
        """
        Find all Neo4j containers (running and stopped).

        Returns:
            List of Neo4jContainer instances, sorted by creation time (newest first)

        Raises:
            DockerException: If Docker daemon is unreachable
        """
        pass

    def is_neo4j_container(self, container) -> bool:
        """
        Check if container is Neo4j based on image name.

        Criteria:
        - Image name contains 'neo4j'
        - Not a sidecar or tool container

        Returns:
            True if container is Neo4j
        """
        pass

    def extract_ports(self, container) -> Dict[str, int]:
        """
        Extract HTTP and Bolt ports from container.

        Returns:
            {'http': 7474, 'bolt': 7687} or actual mapped ports
            Empty dict if ports not exposed
        """
        pass
```

### Dependencies
- `docker` Python library
- `dataclasses` (stdlib)
- `datetime` (stdlib)

### Implementation Notes
- Use `docker.from_env()` for client
- Filter containers with `all=True` to include stopped containers
- Sort by creation time to prioritize recent containers
- Handle port mapping: `container.attrs['NetworkSettings']['Ports']`

### Test Requirements
- Detect running Neo4j container
- Detect stopped Neo4j container
- Ignore non-Neo4j containers
- Handle no containers found
- Handle Docker daemon down

---

## Module 2: neo4j/credential_sync.py

### Purpose
Extract credentials from Neo4j containers and synchronize with .env file.

### Contract

**Input:**
- `Neo4jContainer` instance
- Docker client instance

**Output:**
```python
@dataclass
class Neo4jCredentials:
    username: str           # Default: 'neo4j'
    password: str           # Extracted from container
    http_port: int          # HTTP port (7474)
    bolt_port: int          # Bolt port (7687)
    source: str             # 'env_var', 'docker_secret', 'default'
```

**Side Effects:**
- Reads `.env` file
- Writes to `.env` file (when syncing)

### Key Methods

```python
class CredentialExtractor:
    """Extracts Neo4j credentials from containers."""

    def __init__(self, docker_client: docker.DockerClient):
        self.docker = docker_client

    def extract(self, container: Neo4jContainer) -> Optional[Neo4jCredentials]:
        """
        Extract credentials from container.

        Priority order:
        1. Environment variables (NEO4J_AUTH, NEO4J_PASSWORD)
        2. Docker secrets (if using secrets)
        3. Default ('neo4j'/'neo4j') - mark as uncertain

        Returns:
            Neo4jCredentials if found, None if cannot extract

        Raises:
            ContainerNotRunning: If container stopped and can't inspect
        """
        pass

    def _check_env_vars(self, container) -> Optional[Tuple[str, str]]:
        """Check NEO4J_AUTH and NEO4J_PASSWORD env vars."""
        pass

    def _check_docker_secrets(self, container) -> Optional[Tuple[str, str]]:
        """Check for Docker secrets mount."""
        pass


class CredentialSynchronizer:
    """Synchronizes credentials to .env file."""

    def __init__(self, env_path: Path = Path('.env')):
        self.env_path = env_path

    def read_current(self) -> Dict[str, str]:
        """
        Read current Neo4j settings from .env.

        Returns:
            Dict with keys: NEO4J_USER, NEO4J_PASSWORD, NEO4J_HTTP_PORT, NEO4J_BOLT_PORT
        """
        pass

    def sync(self, credentials: Neo4jCredentials) -> None:
        """
        Update .env with new credentials.

        Updates these keys:
        - NEO4J_USER
        - NEO4J_PASSWORD
        - NEO4J_HTTP_PORT
        - NEO4J_BOLT_PORT

        Preserves other .env values.
        Creates backup at .env.backup before modification.

        Raises:
            IOError: If .env not writable
        """
        pass

    def backup(self) -> Path:
        """Create timestamped backup of .env."""
        pass
```

### Dependencies
- `docker` Python library
- `pathlib` (stdlib)
- `dataclasses` (stdlib)
- `typing` (stdlib)
- `shutil` (stdlib) for backup

### Implementation Notes

**Credential Extraction Logic:**
```python
# Priority 1: NEO4J_AUTH env var
# Format: "username/password"
auth = container.attrs['Config']['Env'].get('NEO4J_AUTH')
if auth:
    return auth.split('/')

# Priority 2: NEO4J_PASSWORD env var
password = container.attrs['Config']['Env'].get('NEO4J_PASSWORD')
if password:
    return ('neo4j', password)

# Priority 3: Default (uncertain)
return ('neo4j', 'neo4j', 'default')
```

**.env Synchronization:**
- Use simple key=value parsing
- Preserve comments and formatting
- Update only Neo4j-related keys
- Atomic write: write to temp file, then rename

### Test Requirements
- Extract from NEO4J_AUTH env var
- Extract from NEO4J_PASSWORD env var
- Handle stopped container gracefully
- Sync credentials to new .env
- Sync credentials to existing .env
- Preserve other .env values
- Create backup before modification

---

## Module 3: neo4j/manager.py

### Purpose
Orchestrate Neo4j container detection, user interaction, and credential synchronization.

### Contract

**Input:**
- Docker client instance
- Path to .env file

**Output:**
```python
@dataclass
class SyncDecision:
    action: str              # 'use_existing', 'create_new', 'manual', 'skip'
    container: Optional[Neo4jContainer]
    credentials: Optional[Neo4jCredentials]
```

**Side Effects:**
- Prints to stdout (user interaction)
- Reads stdin (user choice)
- Modifies .env (if syncing)

### Key Methods

```python
class Neo4jManager:
    """Manages Neo4j container lifecycle and synchronization."""

    def __init__(self, docker_client: docker.DockerClient, env_path: Path = Path('.env')):
        self.docker = docker_client
        self.env_path = env_path
        self.detector = Neo4jDetector(docker_client)
        self.extractor = CredentialExtractor(docker_client)
        self.synchronizer = CredentialSynchronizer(env_path)

    def check_and_sync(self) -> SyncDecision:
        """
        Main orchestration method.

        Flow:
        1. Detect existing containers
        2. If found, extract credentials
        3. Present user with 4 choices
        4. Execute user choice
        5. Return decision

        Returns:
            SyncDecision with action taken
        """
        containers = self.detector.find_containers()

        if not containers:
            return self._handle_no_containers()

        return self._handle_existing_containers(containers)

    def _handle_no_containers(self) -> SyncDecision:
        """
        No containers found - offer to create new or skip.

        Choices:
        1. Create new Neo4j container (amplihack managed)
        2. Skip Neo4j setup (manual setup later)

        Returns:
            SyncDecision with user choice
        """
        pass

    def _handle_existing_containers(self, containers: List[Neo4jContainer]) -> SyncDecision:
        """
        Containers found - present 4 choices.

        Display:
        - Number of containers found
        - Details of most recent container (name, status, ports)
        - Extracted credentials (if available)

        Choices:
        1. Use existing container (sync credentials to .env)
        2. Create new container (amplihack managed, new ports)
        3. Manual configuration (I'll set .env myself)
        4. Skip Neo4j setup

        Returns:
            SyncDecision with user choice
        """
        pass

    def _display_container_info(self, container: Neo4jContainer, credentials: Optional[Neo4jCredentials]) -> None:
        """Display container details in user-friendly format."""
        pass

    def _get_user_choice(self, num_choices: int) -> int:
        """
        Get valid user choice (1-num_choices).

        Re-prompts on invalid input.
        Returns validated choice as int.
        """
        pass

    def _execute_use_existing(self, container: Neo4jContainer, credentials: Neo4jCredentials) -> SyncDecision:
        """
        Execute choice 1: Use existing container.

        Actions:
        1. Backup .env
        2. Sync credentials
        3. Display success message

        Returns:
            SyncDecision with action='use_existing'
        """
        pass

    def _execute_create_new(self) -> SyncDecision:
        """
        Execute choice 2: Create new container.

        Actions:
        1. Find available ports (avoid conflicts)
        2. Generate random password
        3. Update .env with new config
        4. Return decision (actual container creation handled elsewhere)

        Returns:
            SyncDecision with action='create_new'
        """
        pass

    def _find_available_ports(self) -> Tuple[int, int]:
        """
        Find available ports for HTTP and Bolt.

        Start from 7474/7687, increment if taken.

        Returns:
            (http_port, bolt_port)
        """
        pass
```

### Dependencies
- `neo4j.detector` (sibling module)
- `neo4j.credential_sync` (sibling module)
- `docker` Python library
- `pathlib` (stdlib)
- `secrets` (stdlib) for password generation
- `socket` (stdlib) for port checking

### Implementation Notes

**User Interaction Format:**
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

**Port Conflict Resolution:**
- Check if port in use: `socket.socket().bind(('localhost', port))`
- Increment by 1 until available port found
- Update .env with chosen ports

**Password Generation:**
- Use `secrets.token_urlsafe(16)` for new containers
- Strong, URL-safe passwords

### Test Requirements
- No containers found -> offer create/skip
- One container found -> extract and display
- Multiple containers found -> show most recent
- User chooses option 1 -> credentials synced
- User chooses option 2 -> .env updated with new config
- User chooses option 3 -> no .env changes
- User chooses option 4 -> no .env changes
- Invalid user input -> re-prompt
- Port conflict -> find alternative ports

---

## Integration Point: launcher/core.py

### Purpose
Hook Neo4j detection into launcher startup flow.

### Modification Spec

**Location:** `launcher/core.py` in `main()` function

**Integration Point:** After proxy initialization, before main event loop

```python
def main():
    """Main entry point."""
    # ... existing proxy setup ...

    # Neo4j Container Detection & Sync
    try:
        from neo4j.manager import Neo4jManager
        import docker

        docker_client = docker.from_env()
        neo4j_mgr = Neo4jManager(docker_client)
        decision = neo4j_mgr.check_and_sync()

        if decision.action == 'create_new':
            # Trigger container creation (future implementation)
            logger.info("Neo4j container creation requested (not yet implemented)")

    except ImportError:
        logger.warning("Neo4j management not available (missing dependencies)")
    except docker.errors.DockerException:
        logger.warning("Docker not available - skipping Neo4j detection")
    except Exception as e:
        logger.error(f"Neo4j detection failed: {e}")
        # Continue without Neo4j

    # ... existing main loop ...
```

### Design Decisions

**Why here?**
- After proxy setup (main infrastructure ready)
- Before event loop (one-time check)
- Non-blocking (failures don't crash launcher)

**Error Handling Strategy:**
- Missing docker library -> log warning, continue
- Docker daemon down -> log warning, continue
- User cancels -> continue without Neo4j
- Any exception -> log error, continue

**Philosophy:**
- Neo4j is optional (don't block startup)
- Fail gracefully (log and continue)
- Clear user feedback (explain what happened)

---

## Data Flow Diagram

```
launcher/core.py
    |
    | Creates Docker client
    v
neo4j/manager.py (Neo4jManager)
    |
    | Delegates detection
    v
neo4j/detector.py (Neo4jDetector)
    |
    | Returns List[Neo4jContainer]
    v
neo4j/manager.py
    |
    | Delegates credential extraction
    v
neo4j/credential_sync.py (CredentialExtractor)
    |
    | Returns Neo4jCredentials
    v
neo4j/manager.py
    |
    | Displays info, gets user choice
    v
USER INTERACTION (stdin/stdout)
    |
    | Returns choice (1-4)
    v
neo4j/manager.py
    |
    | Executes choice
    v
neo4j/credential_sync.py (CredentialSynchronizer)
    |
    | Updates .env
    v
SYNC COMPLETE
```

---

## Error Handling Strategy

### Principle: Fail Gracefully, Never Crash

**Categorization:**

1. **Fatal Errors** (prevent feature from working)
   - Log error, return early, continue launcher startup
   - Examples: Docker daemon down, .env not writable

2. **Recoverable Errors** (can work around)
   - Log warning, use fallback, continue
   - Examples: Can't extract credentials, port conflict

3. **User Errors** (invalid input)
   - Display friendly message, re-prompt
   - Examples: Invalid choice, non-numeric input

**Error Messages:**
- Clear explanation of what went wrong
- What the system will do instead
- How user can fix it (if applicable)

### Specific Handlers

```python
# Docker daemon unreachable
try:
    docker_client = docker.from_env()
except docker.errors.DockerException:
    logger.warning("Docker daemon not available - skipping Neo4j detection")
    logger.info("To enable Neo4j detection, ensure Docker is running")
    return SyncDecision(action='skip', container=None, credentials=None)

# Cannot extract credentials
credentials = extractor.extract(container)
if not credentials:
    logger.warning(f"Could not extract credentials from {container.name}")
    logger.info("You can still use this container with manual configuration")
    # Offer manual configuration option

# .env not writable
try:
    synchronizer.sync(credentials)
except IOError as e:
    logger.error(f"Cannot write to .env: {e}")
    logger.info("Please check file permissions and try again")
    return SyncDecision(action='manual', container=container, credentials=credentials)

# Port already in use
try:
    http_port, bolt_port = self._find_available_ports()
except RuntimeError:  # No ports available
    logger.error("Cannot find available ports for Neo4j")
    logger.info("Please free up ports 7474-7500 or configure manually")
    return SyncDecision(action='manual', container=None, credentials=None)
```

---

## Edge Cases Handled

### Container States
- ✅ Running container with credentials
- ✅ Stopped container (can still extract config)
- ✅ Container with non-standard ports
- ✅ Multiple Neo4j containers (show most recent)
- ✅ No containers found

### Credential Extraction
- ✅ NEO4J_AUTH env var (username/password)
- ✅ NEO4J_PASSWORD env var (username=neo4j)
- ✅ No credentials set (show as uncertain)
- ✅ Docker secrets (attempt to extract)
- ✅ Container stopped (limited extraction)

### Port Management
- ✅ Default ports available (7474/7687)
- ✅ Default ports in use (find alternatives)
- ✅ Non-standard ports in container
- ✅ Port conflicts with existing containers

### .env File States
- ✅ .env exists with Neo4j config
- ✅ .env exists without Neo4j config
- ✅ .env doesn't exist (create new)
- ✅ .env not writable (error gracefully)

### User Input
- ✅ Valid choice (1-4)
- ✅ Invalid choice (re-prompt)
- ✅ Non-numeric input (re-prompt)
- ✅ EOF/Ctrl+C (treat as skip)

---

## Testing Strategy

### Unit Tests

**neo4j/detector.py:**
- Mock Docker client responses
- Test container filtering logic
- Test port extraction
- Test edge cases (no ports, non-standard ports)

**neo4j/credential_sync.py:**
- Mock container attributes
- Test credential extraction priority
- Test .env parsing and writing
- Test backup creation

**neo4j/manager.py:**
- Mock user input
- Mock submodules (detector, extractor, synchronizer)
- Test decision flow logic
- Test error handling

### Integration Tests

- Run with actual Docker containers
- Test full flow from detection to sync
- Verify .env changes
- Test backup restoration

### Manual Testing Checklist

1. No Neo4j containers -> create new option works
2. Running Neo4j container -> detects and syncs
3. Stopped Neo4j container -> detects and offers options
4. Multiple containers -> shows most recent
5. Invalid user input -> re-prompts
6. Port conflicts -> finds alternatives
7. .env backup -> created and valid
8. Docker down -> graceful failure

---

## Implementation Order

### Phase 1: Foundation (Build First)
1. `neo4j/detector.py` - Detection logic
2. Unit tests for detector
3. Manual test with real containers

### Phase 2: Credentials (Build Second)
1. `neo4j/credential_sync.py` - Extraction and sync
2. Unit tests for credential modules
3. Integration test: detect + extract

### Phase 3: Orchestration (Build Third)
1. `neo4j/manager.py` - User interaction and decision flow
2. Unit tests for manager
3. Integration test: full flow

### Phase 4: Integration (Build Last)
1. Modify `launcher/core.py` - Hook into startup
2. End-to-end test with launcher
3. Edge case validation

**Rationale:**
- Build from bottom up (dependencies first)
- Test each layer before moving up
- Integration last (requires all pieces)

---

## Success Criteria

### Functional Requirements
- ✅ Detects existing Neo4j containers (running and stopped)
- ✅ Extracts credentials from containers
- ✅ Presents exactly 4 clear choices to user
- ✅ Syncs credentials to .env based on choice
- ✅ Handles all documented edge cases
- ✅ Never crashes launcher on error

### Non-Functional Requirements
- ✅ Clear, user-friendly output
- ✅ Fast execution (<2 seconds for detection)
- ✅ No side effects on user choice 3/4
- ✅ .env backup before modification
- ✅ Code follows amplihack style (ruff, pyright clean)

### Quality Metrics
- ✅ Test coverage >80% for all modules
- ✅ All pyright type checks pass
- ✅ All ruff linting passes
- ✅ Manual testing checklist complete

---

## Future Enhancements (Out of Scope)

These are explicitly NOT part of this spec:

- ❌ Container creation (choice 2 execution)
- ❌ Container lifecycle management (start/stop/restart)
- ❌ Neo4j health checking
- ❌ Automatic password rotation
- ❌ Multi-container orchestration
- ❌ Neo4j version management

**Justification:**
- Start minimal, add complexity only when needed
- Get detection and sync working first
- Validate user workflow before expanding
- Each enhancement should be separate spec

---

## Dependencies

### Required
- `docker` Python library (existing dependency)
- `pathlib` (stdlib)
- `dataclasses` (stdlib)
- `typing` (stdlib)

### Optional
- None (all features work without optional deps)

---

## Configuration

### .env Keys Modified

```bash
# Neo4j Configuration
NEO4J_USER=neo4j
NEO4J_PASSWORD=<extracted or generated>
NEO4J_HTTP_PORT=7474
NEO4J_BOLT_PORT=7687
```

### .env Backup Format

```
.env.backup.<timestamp>
Example: .env.backup.20250107_143022
```

---

## Appendix: Design Questions Answered

### Q: Do we actually need three separate modules?
**A:** Yes. Each has distinct responsibility:
- Detector: Docker interaction (single concern)
- CredentialSync: .env manipulation (single concern)
- Manager: User interaction and orchestration (single concern)

Combining them would create untestable, unmaintainable code.

### Q: What's the simplest solution?
**A:** This IS the simplest solution that meets requirements:
- No abstractions beyond necessary
- No future-proofing
- Direct, imperative code
- Clear data flow

### Q: Can this be more modular?
**A:** Current modularity is optimal:
- Three focused modules (not too few, not too many)
- Clean interfaces between modules
- Each module independently testable
- Clear ownership of responsibilities

### Q: Will this be easy to regenerate?
**A:** Yes:
- Complete specs with method signatures
- Clear contracts (inputs/outputs)
- Explicit dependencies
- Implementation notes included
- Test requirements defined

### Q: Does complexity add value?
**A:** Every piece of complexity is justified:
- Three modules: necessary for separation of concerns
- Error handling: required for production reliability
- User interaction: explicit requirement
- Credential extraction: core feature value

Nothing is included that doesn't directly serve requirements.

---

## Summary for Builder Agent

**What to Build:**
1. Three Python modules in `neo4j/` directory
2. One integration point in `launcher/core.py`
3. Unit tests for each module
4. Integration test for full flow

**Key Principles:**
- No stubs or placeholders (working code only)
- Fail gracefully (never crash launcher)
- Clear user feedback (explain what's happening)
- Type hints everywhere (pyright clean)

**Starting Point:**
Begin with `neo4j/detector.py` - it has no dependencies on other new modules.

**Definition of Done:**
- All tests pass
- Manual testing checklist complete
- Ruff and pyright clean
- Feature works end-to-end in launcher

**Critical Path:**
detector.py → credential_sync.py → manager.py → launcher integration

Build in this order, test at each stage.
