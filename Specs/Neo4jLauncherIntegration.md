# Neo4j Launcher Integration Specification

## Purpose

This document specifies the EXACT modification needed to integrate Neo4j container detection and synchronization into the existing launcher.

## Target File

`/Users/ryan/src/amplihack/MicrosoftHackathon2025-AgenticCoding/src/amplihack/launcher/core.py`

## Integration Point

Add Neo4j detection in the `ClaudeLauncher.prepare_launch()` method, **AFTER** proxy startup (step 5) and **BEFORE** return statement.

## Exact Code Addition

### Location

Insert after line 208 (after `return True` in `_start_proxy_if_needed()`) and before the final `return True` of `prepare_launch()`.

### Current Code (Lines 72-98)

```python
def prepare_launch(self) -> bool:
    """Prepare environment for launching Claude.

    Returns:
        True if preparation successful, False otherwise.
    """
    # 1. Check prerequisites first - fail fast with helpful guidance
    if not check_prerequisites():
        return False

    # 2. Handle repository checkout if needed
    if self.checkout_repo:
        if not self._handle_repo_checkout():
            return False

    # 3. Find and validate target directory
    target_dir = self._find_target_directory()
    if not target_dir:
        print("Failed to determine target directory")
        return False

    # 4. Handle directory change if needed (unless UVX with --add-dir)
    if not self._handle_directory_change(target_dir):
        return False

    # 5. Start proxy if needed
    return self._start_proxy_if_needed()
```

### Modified Code (Add Step 6)

```python
def prepare_launch(self) -> bool:
    """Prepare environment for launching Claude.

    Returns:
        True if preparation successful, False otherwise.
    """
    # 1. Check prerequisites first - fail fast with helpful guidance
    if not check_prerequisites():
        return False

    # 2. Handle repository checkout if needed
    if self.checkout_repo:
        if not self._handle_repo_checkout():
            return False

    # 3. Find and validate target directory
    target_dir = self._find_target_directory()
    if not target_dir:
        print("Failed to determine target directory")
        return False

    # 4. Handle directory change if needed (unless UVX with --add-dir)
    if not self._handle_directory_change(target_dir):
        return False

    # 5. Start proxy if needed
    if not self._start_proxy_if_needed():
        return False

    # 6. Neo4j container detection and synchronization
    self._handle_neo4j_sync()

    return True
```

### New Method to Add (Insert before `_paths_are_same_with_cache`, around line 380)

```python
def _handle_neo4j_sync(self) -> None:
    """Handle Neo4j container detection and credential synchronization.

    This is a non-blocking operation - failures will log warnings but
    won't prevent launcher from starting.
    """
    try:
        import docker
        from neo4j.manager import Neo4jManager
        import logging

        logger = logging.getLogger(__name__)

        # Create Docker client
        docker_client = docker.from_env()

        # Create Neo4j manager and run detection/sync
        neo4j_manager = Neo4jManager(docker_client)
        decision = neo4j_manager.check_and_sync()

        # Handle decision (currently only logging, container creation not implemented)
        if decision.action == 'create_new':
            logger.info("Neo4j container creation requested (not yet implemented)")
            logger.info("Please create a Neo4j container manually and re-run")
        elif decision.action == 'use_existing':
            logger.info(f"Using existing Neo4j container: {decision.container.name}")
        elif decision.action == 'manual':
            logger.info("User chose manual Neo4j configuration")
        elif decision.action == 'skip':
            logger.info("Neo4j setup skipped")

    except ImportError as e:
        # neo4j module not available - this is fine, feature is optional
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Neo4j management not available: {e}")
        # Don't print to user - this is expected if neo4j module doesn't exist yet

    except docker.errors.DockerException as e:
        # Docker not available - this is fine, user might not need it
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("Docker not available - skipping Neo4j detection")
        logger.debug(f"Docker error: {e}")

    except Exception as e:
        # Any other error - log but don't crash launcher
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Neo4j detection failed: {e}")
        logger.debug("Continuing launcher startup without Neo4j")
```

## Import Additions

**No import additions needed at module level** - all imports are done inside the try/except block to avoid ImportError if neo4j module doesn't exist yet.

## Design Decisions

### Why in `prepare_launch()` instead of `__init__()`?

- `prepare_launch()` is called right before Claude starts
- It's where all environment setup happens (proxy, directory changes)
- User sees Neo4j prompt at the right time (after basic setup, before Claude starts)
- Consistent with existing pattern (proxy start is in prepare_launch)

### Why new method instead of inline?

- **Single Responsibility**: `prepare_launch()` orchestrates, `_handle_neo4j_sync()` executes
- **Testability**: Can mock/test Neo4j sync independently
- **Readability**: Keeps `prepare_launch()` clean and easy to understand
- **Consistency**: Matches existing pattern (_start_proxy_if_needed, _handle_repo_checkout)

### Why non-blocking (doesn't return False on error)?

- Neo4j is optional feature
- Shouldn't prevent Claude from starting
- User can configure manually if auto-detection fails
- Follows Unix philosophy: warnings not errors

### Why lazy imports inside try/except?

- No ImportError if neo4j module doesn't exist
- No crash if docker library not installed
- Graceful degradation
- Feature can be added incrementally

### Why logging instead of print?

- Consistent with existing launcher logging
- User can control verbosity
- Debug mode shows more details
- Matches project patterns

## Testing Strategy

### Unit Tests

```python
def test_handle_neo4j_sync_success(mocker):
    """Test successful Neo4j sync."""
    mock_manager = mocker.patch('neo4j.manager.Neo4jManager')
    mock_manager.return_value.check_and_sync.return_value = \
        SyncDecision(action='use_existing', container=mock_container, credentials=mock_creds)

    launcher = ClaudeLauncher()
    launcher._handle_neo4j_sync()  # Should not raise

def test_handle_neo4j_sync_import_error(mocker):
    """Test graceful handling when neo4j module missing."""
    mocker.patch('neo4j.manager.Neo4jManager', side_effect=ImportError)

    launcher = ClaudeLauncher()
    launcher._handle_neo4j_sync()  # Should not raise

def test_handle_neo4j_sync_docker_error(mocker):
    """Test graceful handling when Docker unavailable."""
    mocker.patch('docker.from_env', side_effect=docker.errors.DockerException)

    launcher = ClaudeLauncher()
    launcher._handle_neo4j_sync()  # Should not raise
```

### Integration Tests

```python
def test_prepare_launch_with_neo4j():
    """Test full prepare_launch() with Neo4j detection."""
    launcher = ClaudeLauncher()
    result = launcher.prepare_launch()
    assert result == True  # Neo4j sync shouldn't block launch

def test_prepare_launch_without_neo4j():
    """Test prepare_launch() when neo4j module doesn't exist."""
    # Temporarily rename neo4j module
    launcher = ClaudeLauncher()
    result = launcher.prepare_launch()
    assert result == True  # Should still succeed
```

### Manual Tests

- [ ] Run launcher with Neo4j container present
- [ ] Run launcher with no Neo4j container
- [ ] Run launcher with Docker stopped
- [ ] Run launcher before neo4j module exists
- [ ] Run launcher with corrupted .env file
- [ ] Verify launcher continues in all cases
- [ ] Check log output for appropriate messages

## Rollback Plan

If Neo4j integration causes issues:

1. Comment out step 6 in `prepare_launch()`:
```python
# 6. Neo4j container detection and synchronization
# self._handle_neo4j_sync()
```

2. Or remove the `_handle_neo4j_sync()` method entirely

The launcher will work exactly as before - no other changes needed.

## Success Criteria

- [ ] Launcher starts successfully with Neo4j detection
- [ ] Launcher starts successfully without neo4j module
- [ ] Launcher starts successfully with Docker down
- [ ] Neo4j sync prompts appear at correct time
- [ ] User can complete all 4 choice workflows
- [ ] Launcher never crashes due to Neo4j code
- [ ] All existing launcher tests still pass
- [ ] New launcher tests pass

## Future Enhancements (Out of Scope)

These are explicitly NOT part of this integration:

- Container creation (choice 2 execution)
- Container lifecycle management
- Neo4j health checking
- Automatic container restart
- Neo4j version management

Keep the integration minimal and focused.

## Implementation Notes for Builder

### Key Points

1. **Minimal Changes**: Only 2 modifications to launcher/core.py
   - Add step 6 to prepare_launch()
   - Add _handle_neo4j_sync() method

2. **No Imports at Module Level**: All imports inside try/except
   - Prevents ImportError if neo4j module doesn't exist
   - Allows incremental feature rollout

3. **Error Handling**: Never crash launcher
   - ImportError -> log debug, continue
   - DockerException -> log warning, continue
   - Any Exception -> log error, continue

4. **User Experience**: Neo4j prompt appears between proxy start and Claude launch
   - Clear timing: after infrastructure, before main tool
   - Non-blocking: can skip or fail without issues

5. **Logging Strategy**:
   - DEBUG: Expected conditions (module missing)
   - WARNING: Abnormal but recoverable (Docker down)
   - ERROR: Unexpected failures (exceptions)
   - INFO: Normal operations (container selected)

### Testing Order

1. Unit test `_handle_neo4j_sync()` in isolation
2. Integration test with `prepare_launch()`
3. Manual test with real Docker/containers
4. Verify no regression in existing launcher tests

### Common Issues to Avoid

- ❌ Don't make Neo4j sync blocking (return False on error)
- ❌ Don't add module-level imports for neo4j
- ❌ Don't print to stdout directly (use logging)
- ❌ Don't call docker.from_env() multiple times
- ❌ Don't modify ClaudeLauncher.__init__() signature

## Code Review Checklist

- [ ] Only 2 modifications to launcher/core.py
- [ ] No module-level imports added
- [ ] _handle_neo4j_sync() returns None (not bool)
- [ ] All exceptions caught and logged
- [ ] Logging uses appropriate levels
- [ ] prepare_launch() still returns bool
- [ ] Existing tests still pass
- [ ] New tests added and passing
- [ ] Manual test checklist complete

## Definition of Done

- [ ] Code integrated into launcher/core.py
- [ ] All error paths tested
- [ ] Logging verified at all levels
- [ ] No crashes on any error condition
- [ ] Existing launcher functionality unchanged
- [ ] New tests pass
- [ ] Existing tests pass
- [ ] Manual testing complete
- [ ] Code review approved
