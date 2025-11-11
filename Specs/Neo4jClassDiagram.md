# Neo4j Container Sync - Class Diagram

## Class Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                     launcher/core.py                            │
│                                                                 │
│  main()                                                         │
│    └─> Neo4jManager.check_and_sync() -> SyncDecision          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ creates
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    neo4j/manager.py                             │
│                                                                 │
│  class Neo4jManager:                                            │
│    + __init__(docker_client, env_path)                         │
│    + check_and_sync() -> SyncDecision                          │
│    - _handle_no_containers() -> SyncDecision                   │
│    - _handle_existing_containers(containers) -> SyncDecision   │
│    - _display_container_info(container, credentials)           │
│    - _get_user_choice(num_choices) -> int                      │
│    - _execute_use_existing(...) -> SyncDecision                │
│    - _execute_create_new() -> SyncDecision                     │
│    - _find_available_ports() -> Tuple[int, int]               │
│                                                                 │
│  @dataclass SyncDecision:                                       │
│    action: str                                                  │
│    container: Optional[Neo4jContainer]                         │
│    credentials: Optional[Neo4jCredentials]                     │
└─────────────────────────────────────────────────────────────────┘
                    │                    │
                    │                    │
          ┌─────────┴────────┐  ┌────────┴─────────┐
          │ uses             │  │ uses             │
          ▼                  │  ▼                  │
┌──────────────────────┐     │  ┌──────────────────────────┐
│  neo4j/detector.py   │     │  │ neo4j/credential_sync.py │
│                      │     │  │                          │
│  class Neo4jDetector:│     │  │  class CredentialExtractor:│
│    + __init__(...)   │     │  │    + __init__(...)       │
│    + find_containers()│    │  │    + extract(...)        │
│      -> List[Neo4j...│    │  │      -> Neo4jCredentials │
│    + is_neo4j_...()  │    │  │    - _check_env_vars()  │
│    + extract_ports() │    │  │    - _check_docker_...() │
│                      │     │  │                          │
│  @dataclass          │     │  │  @dataclass              │
│  Neo4jContainer:     │     │  │  Neo4jCredentials:       │
│    container_id: str │     │  │    username: str         │
│    name: str         │     │  │    password: str         │
│    status: str       │     │  │    http_port: int        │
│    ports: Dict       │     │  │    bolt_port: int        │
│    image: str        │     │  │    source: str           │
│    created: datetime │     │  │                          │
└──────────────────────┘     │  │  class CredentialSync...:│
                             │  │    + __init__(...)       │
                             │  │    + read_current()      │
                             │  │    + sync(...)           │
                             │  │    + backup() -> Path    │
                             │  └──────────────────────────┘
                             │
                             └─> Both used by Neo4jManager
```

## Data Flow Sequence

```
User starts launcher
        │
        ▼
launcher/core.main()
        │
        │ Create Docker client
        ▼
Neo4jManager.check_and_sync()
        │
        │ Call find_containers()
        ▼
Neo4jDetector.find_containers()
        │
        │ Query Docker daemon
        ▼
Return List[Neo4jContainer]
        │
        ▼
Neo4jManager: Check if empty
        │
        ├─> Empty: _handle_no_containers()
        │            │
        │            │ Display: Create new or skip?
        │            ▼
        │          Get user choice
        │            │
        │            └─> Return SyncDecision
        │
        └─> Has containers: _handle_existing_containers()
                     │
                     │ Get most recent container
                     ▼
            CredentialExtractor.extract(container)
                     │
                     │ Check NEO4J_AUTH, NEO4J_PASSWORD, etc.
                     ▼
            Return Neo4jCredentials (or None)
                     │
                     ▼
            Manager: Display container info + credentials
                     │
                     │ Show 4 choices:
                     │   1. Use existing
                     │   2. Create new
                     │   3. Manual config
                     │   4. Skip
                     ▼
            Get user choice (1-4)
                     │
                     ├─> Choice 1: _execute_use_existing()
                     │              │
                     │              │ Call sync(credentials)
                     │              ▼
                     │    CredentialSynchronizer.sync()
                     │              │
                     │              │ Backup .env
                     │              │ Update NEO4J_* keys
                     │              │ Write .env
                     │              ▼
                     │    Return SyncDecision(action='use_existing')
                     │
                     ├─> Choice 2: _execute_create_new()
                     │              │
                     │              │ Find available ports
                     │              │ Generate password
                     │              │ Update .env
                     │              ▼
                     │    Return SyncDecision(action='create_new')
                     │
                     ├─> Choice 3: Return SyncDecision(action='manual')
                     │
                     └─> Choice 4: Return SyncDecision(action='skip')
                                    │
                                    ▼
                     Return to launcher/core.main()
                                    │
                                    ▼
                     Continue launcher startup
```

## Module Dependencies

```
┌─────────────────────────────────────────────────────┐
│                External Dependencies                │
│                                                     │
│  - docker (Docker Python SDK)                       │
│  - pathlib (stdlib)                                 │
│  - dataclasses (stdlib)                             │
│  - typing (stdlib)                                  │
│  - datetime (stdlib)                                │
│  - secrets (stdlib)                                 │
│  - socket (stdlib)                                  │
│  - shutil (stdlib)                                  │
└─────────────────────────────────────────────────────┘
                         │
                         │ Used by all modules
                         ▼
┌─────────────────────────────────────────────────────┐
│                 neo4j/detector.py                   │
│                                                     │
│  Dependencies:                                      │
│    - docker                                         │
│    - dataclasses                                    │
│    - datetime                                       │
│    - typing                                         │
│                                                     │
│  Exports:                                           │
│    - Neo4jContainer (dataclass)                    │
│    - Neo4jDetector (class)                         │
│                                                     │
│  No internal amplihack dependencies                 │
└─────────────────────────────────────────────────────┘
                         │
                         │ Imported by
                         ▼
┌─────────────────────────────────────────────────────┐
│             neo4j/credential_sync.py                │
│                                                     │
│  Dependencies:                                      │
│    - docker                                         │
│    - pathlib                                        │
│    - dataclasses                                    │
│    - typing                                         │
│    - shutil                                         │
│    - neo4j.detector (Neo4jContainer)               │
│                                                     │
│  Exports:                                           │
│    - Neo4jCredentials (dataclass)                  │
│    - CredentialExtractor (class)                   │
│    - CredentialSynchronizer (class)                │
└─────────────────────────────────────────────────────┘
                         │
                         │ Both imported by
                         ▼
┌─────────────────────────────────────────────────────┐
│                 neo4j/manager.py                    │
│                                                     │
│  Dependencies:                                      │
│    - docker                                         │
│    - pathlib                                        │
│    - dataclasses                                    │
│    - typing                                         │
│    - secrets                                        │
│    - socket                                         │
│    - neo4j.detector (all)                          │
│    - neo4j.credential_sync (all)                   │
│                                                     │
│  Exports:                                           │
│    - SyncDecision (dataclass)                      │
│    - Neo4jManager (class)                          │
└─────────────────────────────────────────────────────┘
                         │
                         │ Imported by
                         ▼
┌─────────────────────────────────────────────────────┐
│                 launcher/core.py                    │
│                                                     │
│  Modification:                                      │
│    - Import Neo4jManager                            │
│    - Call check_and_sync() in main()               │
│    - Handle SyncDecision return                     │
│                                                     │
│  Dependencies added:                                │
│    - neo4j.manager (Neo4jManager, SyncDecision)    │
│    - docker                                         │
└─────────────────────────────────────────────────────┘
```

## Error Handling Flow

```
Any Module
    │
    │ Exception occurs
    ▼
Try/Except Block
    │
    ├─> DockerException
    │   │
    │   │ Log warning: "Docker not available"
    │   │ Return default/skip value
    │   └─> Continue execution
    │
    ├─> IOError (.env issues)
    │   │
    │   │ Log error: "Cannot write to .env"
    │   │ Return manual configuration decision
    │   └─> Continue execution
    │
    ├─> ValueError (port conflicts)
    │   │
    │   │ Log error: "No available ports"
    │   │ Return manual configuration decision
    │   └─> Continue execution
    │
    └─> Exception (catch-all)
        │
        │ Log error with traceback
        │ Return skip decision
        └─> Continue launcher startup

IMPORTANT: Never crash the launcher
           Always return valid SyncDecision
           Always log what happened
```

## Testing Strategy by Module

```
┌──────────────────────────────────────────────────────┐
│              neo4j/detector.py Tests                 │
│                                                      │
│  Unit Tests (mocked Docker):                         │
│    ✓ find_containers() with running container       │
│    ✓ find_containers() with stopped container       │
│    ✓ find_containers() with no containers           │
│    ✓ find_containers() with multiple containers     │
│    ✓ is_neo4j_container() true/false                │
│    ✓ extract_ports() standard ports                 │
│    ✓ extract_ports() custom ports                   │
│    ✓ extract_ports() no ports exposed               │
│                                                      │
│  Integration Tests (real Docker):                    │
│    ✓ Detect actual Neo4j container                  │
│    ✓ Handle Docker daemon down                       │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│          neo4j/credential_sync.py Tests              │
│                                                      │
│  Unit Tests:                                         │
│    ✓ extract() from NEO4J_AUTH env var              │
│    ✓ extract() from NEO4J_PASSWORD env var          │
│    ✓ extract() returns None for no credentials      │
│    ✓ extract() from Docker secrets                  │
│    ✓ read_current() parses .env correctly           │
│    ✓ sync() updates existing .env                   │
│    ✓ sync() creates new .env                        │
│    ✓ sync() preserves other values                  │
│    ✓ backup() creates timestamped backup            │
│                                                      │
│  Integration Tests:                                  │
│    ✓ Full extract + sync flow                       │
│    ✓ Backup and restore .env                        │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│              neo4j/manager.py Tests                  │
│                                                      │
│  Unit Tests (mocked submodules):                     │
│    ✓ check_and_sync() no containers found           │
│    ✓ check_and_sync() container found               │
│    ✓ _handle_no_containers() user choice 1          │
│    ✓ _handle_no_containers() user choice 2          │
│    ✓ _handle_existing_containers() all choices      │
│    ✓ _get_user_choice() valid input                 │
│    ✓ _get_user_choice() invalid input retry         │
│    ✓ _execute_use_existing() success                │
│    ✓ _execute_create_new() success                  │
│    ✓ _find_available_ports() default available      │
│    ✓ _find_available_ports() conflict resolution    │
│                                                      │
│  Integration Tests:                                  │
│    ✓ Full flow: detect -> extract -> user -> sync   │
│    ✓ Error handling: Docker down                    │
│    ✓ Error handling: .env not writable              │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│            launcher/core.py Tests                    │
│                                                      │
│  Integration Tests:                                  │
│    ✓ Launcher starts with Neo4j sync                │
│    ✓ Launcher continues on sync failure             │
│    ✓ Launcher handles missing neo4j module          │
│                                                      │
│  Manual Tests:                                       │
│    ✓ Run launcher with Neo4j container              │
│    ✓ Run launcher without Neo4j container           │
│    ✓ Run launcher with Docker down                  │
│    ✓ Test all 4 user choices                        │
└──────────────────────────────────────────────────────┘
```

## Implementation Checklist

### Phase 1: Detector (Day 1)
- [ ] Create `neo4j/__init__.py`
- [ ] Create `neo4j/detector.py`
- [ ] Define `Neo4jContainer` dataclass
- [ ] Implement `Neo4jDetector.__init__()`
- [ ] Implement `Neo4jDetector.find_containers()`
- [ ] Implement `Neo4jDetector.is_neo4j_container()`
- [ ] Implement `Neo4jDetector.extract_ports()`
- [ ] Write unit tests for detector
- [ ] Run tests (ensure all pass)
- [ ] Manual test with real Docker container

### Phase 2: Credentials (Day 2)
- [ ] Create `neo4j/credential_sync.py`
- [ ] Define `Neo4jCredentials` dataclass
- [ ] Implement `CredentialExtractor.__init__()`
- [ ] Implement `CredentialExtractor.extract()`
- [ ] Implement `CredentialExtractor._check_env_vars()`
- [ ] Implement `CredentialExtractor._check_docker_secrets()`
- [ ] Implement `CredentialSynchronizer.__init__()`
- [ ] Implement `CredentialSynchronizer.read_current()`
- [ ] Implement `CredentialSynchronizer.sync()`
- [ ] Implement `CredentialSynchronizer.backup()`
- [ ] Write unit tests for credential sync
- [ ] Run tests (ensure all pass)
- [ ] Integration test: detect + extract

### Phase 3: Manager (Day 3)
- [ ] Create `neo4j/manager.py`
- [ ] Define `SyncDecision` dataclass
- [ ] Implement `Neo4jManager.__init__()`
- [ ] Implement `Neo4jManager.check_and_sync()`
- [ ] Implement `Neo4jManager._handle_no_containers()`
- [ ] Implement `Neo4jManager._handle_existing_containers()`
- [ ] Implement `Neo4jManager._display_container_info()`
- [ ] Implement `Neo4jManager._get_user_choice()`
- [ ] Implement `Neo4jManager._execute_use_existing()`
- [ ] Implement `Neo4jManager._execute_create_new()`
- [ ] Implement `Neo4jManager._find_available_ports()`
- [ ] Write unit tests for manager
- [ ] Run tests (ensure all pass)
- [ ] Integration test: full flow

### Phase 4: Integration (Day 4)
- [ ] Modify `launcher/core.py`
- [ ] Add Neo4j import and error handling
- [ ] Add check_and_sync() call in main()
- [ ] Handle SyncDecision return value
- [ ] Test launcher with Neo4j container present
- [ ] Test launcher with no Neo4j container
- [ ] Test launcher with Docker down
- [ ] Test all 4 user choice paths
- [ ] Run full test suite
- [ ] Run ruff and pyright checks
- [ ] Update documentation

### Phase 5: Validation (Day 5)
- [ ] Manual testing: All edge cases
- [ ] Code review: Check against spec
- [ ] Performance test: Startup time impact
- [ ] Documentation: Add to README if needed
- [ ] Create GitHub issue comment with results
- [ ] Mark issue #1170 as complete

## File Structure Summary

```
amplihack/
├── neo4j/                          # NEW
│   ├── __init__.py                 # NEW - Package exports
│   ├── detector.py                 # NEW - Container detection
│   ├── credential_sync.py          # NEW - Credential extraction & sync
│   └── manager.py                  # NEW - Orchestration & user interaction
├── launcher/
│   └── core.py                     # MODIFIED - Add Neo4j hook
├── tests/                          # NEW tests
│   └── neo4j/
│       ├── test_detector.py
│       ├── test_credential_sync.py
│       └── test_manager.py
└── Specs/
    ├── Neo4jContainerSync.md       # THIS FILE (detailed spec)
    └── Neo4jClassDiagram.md        # THIS FILE (visual reference)
```

## Key Design Decisions Documented

1. **Why three modules instead of one?**
   - Separation of concerns (Docker, .env, user interaction)
   - Independent testability
   - Clear ownership of responsibilities
   - Follows existing pattern (proxy/manager, docker/detector)

2. **Why dataclasses for data structures?**
   - Immutable, type-safe data containers
   - Auto-generated __init__, __repr__, __eq__
   - Clear contracts between modules
   - Better than dicts (type hints work)

3. **Why integrate in launcher/core.py?**
   - Single entry point for all startup tasks
   - Consistent error handling
   - User sees Neo4j prompt at appropriate time
   - Non-blocking (launcher continues on failure)

4. **Why backup .env before modification?**
   - User safety (can restore if something wrong)
   - Standard practice for config file changes
   - Low cost (one file copy)
   - High value (prevents user frustration)

5. **Why 4 choices instead of 2?**
   - User requirement (explicit in issue)
   - Covers all real-world scenarios:
     - Use existing (most common)
     - Create new (multi-environment dev)
     - Manual (power users)
     - Skip (optional feature)

6. **Why find available ports for new containers?**
   - Multiple Neo4j instances common in dev
   - Avoid port conflicts
   - Better UX (just works)
   - Low complexity (socket.bind check)

7. **Why fail gracefully instead of raising exceptions?**
   - Neo4j is optional feature
   - Shouldn't block launcher startup
   - User can continue with manual setup
   - Follows Unix philosophy (warnings not errors)

## Anti-Patterns Avoided

1. ❌ **Monolithic Module**
   - Would have put everything in one file
   - Hard to test, maintain, understand
   - Violates single responsibility

2. ❌ **Abstract Base Classes**
   - No need for interfaces/protocols here
   - Concrete implementations sufficient
   - YAGNI (You Aren't Gonna Need It)

3. ❌ **Configuration File for Feature**
   - Feature is self-contained
   - No settings to configure
   - Would add complexity without value

4. ❌ **Async/Threading**
   - Startup task (run once)
   - Docker operations fast enough
   - Complexity not justified

5. ❌ **Database/State Persistence**
   - Container detection is stateless
   - No need to remember previous decisions
   - .env is source of truth

6. ❌ **Plugin System**
   - Only one container type (Neo4j)
   - No need for extensibility
   - Would over-engineer solution

## Success Metrics

**Code Quality:**
- [ ] Ruff linting: 0 errors
- [ ] Pyright type checking: 0 errors
- [ ] Test coverage: >80%
- [ ] Cyclomatic complexity: <10 per function

**Functionality:**
- [ ] All 4 user choices work correctly
- [ ] All edge cases handled gracefully
- [ ] No launcher crashes on any input
- [ ] .env correctly updated in all scenarios

**User Experience:**
- [ ] Clear, understandable prompts
- [ ] Fast execution (<2s for detection)
- [ ] Helpful error messages
- [ ] .env backup created before changes

**Integration:**
- [ ] No conflicts with existing code
- [ ] Follows amplihack patterns
- [ ] Clean git history
- [ ] Documentation updated
