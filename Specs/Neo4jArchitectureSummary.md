# Neo4j Container Detection & Synchronization - Architecture Summary

## Overview

Complete architecture for Issue #1170: Detect existing Neo4j containers, extract credentials, present user with 4 clear choices, and auto-sync credentials based on selection.

## Documentation Suite

This architecture consists of 5 comprehensive documents:

### 1. Neo4jContainerSync.md (Main Specification)
**Purpose**: Complete technical specification with all details
**Location**: `/Users/ryan/src/amplihack/Specs/Neo4jContainerSync.md`
**Contents**:
- Full module specifications (detector, credential_sync, manager)
- Class definitions with method signatures
- Data structures (Neo4jContainer, Neo4jCredentials, SyncDecision)
- Error handling strategy
- Edge cases handled
- Testing requirements
- Implementation phases
- Success criteria

### 2. Neo4jClassDiagram.md (Visual Reference)
**Purpose**: Visual architecture and implementation guide
**Location**: `/Users/ryan/src/amplihack/Specs/Neo4jClassDiagram.md`
**Contents**:
- Class hierarchy diagrams
- Data flow sequence diagrams
- Module dependency graph
- Error handling flowchart
- Testing strategy by module
- Implementation checklist
- Design decision rationale
- Anti-patterns avoided

### 3. Neo4jBuilderGuide.md (Quick Reference)
**Purpose**: Builder agent quick start and common patterns
**Location**: `/Users/ryan/src/amplihack/Specs/Neo4jBuilderGuide.md`
**Contents**:
- TL;DR implementation order
- Core data structures
- Key implementation details
- Error handling patterns
- Code style requirements
- Testing templates
- Common pitfalls
- Definition of done

### 4. Neo4jLauncherIntegration.md (Integration Spec)
**Purpose**: Exact launcher/core.py modifications
**Location**: `/Users/ryan/src/amplihack/Specs/Neo4jLauncherIntegration.md`
**Contents**:
- Precise code locations
- Before/after code snippets
- Integration rationale
- Testing strategy
- Rollback plan
- Success criteria

### 5. Neo4jArchitectureSummary.md (This Document)
**Purpose**: High-level overview and navigation guide
**Location**: `/Users/ryan/src/amplihack/Specs/Neo4jArchitectureSummary.md`

## Quick Navigation

**For Builder Agent:**
1. Start with: `Neo4jBuilderGuide.md` (quick reference)
2. Reference: `Neo4jContainerSync.md` (detailed spec)
3. Integrate: `Neo4jLauncherIntegration.md` (exact changes)
4. Visualize: `Neo4jClassDiagram.md` (diagrams)

**For Reviewer Agent:**
1. Review against: `Neo4jContainerSync.md` (requirements)
2. Check structure: `Neo4jClassDiagram.md` (architecture)
3. Verify integration: `Neo4jLauncherIntegration.md` (launcher changes)

**For User:**
1. Understand feature: This document (summary)
2. Deep dive: `Neo4jContainerSync.md` (complete spec)

## Architecture At a Glance

### Module Structure
```
neo4j/
├── __init__.py          # Package exports
├── detector.py          # Find Neo4j containers (NO dependencies)
├── credential_sync.py   # Extract credentials, sync .env (depends on detector)
└── manager.py           # User interaction, orchestration (depends on both)

launcher/
└── core.py             # Add Neo4j hook in prepare_launch()
```

### Data Flow
```
launcher/core.py
    ↓
neo4j/manager.py (orchestrator)
    ↓
    ├→ neo4j/detector.py (find containers)
    │   ↓
    │   Returns: List[Neo4jContainer]
    │
    └→ neo4j/credential_sync.py (extract & sync)
        ↓
        Returns: Neo4jCredentials
        ↓
        User chooses (1-4)
        ↓
        Updates .env (if needed)
```

### User Interaction
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

## Key Design Decisions

### 1. Three Separate Modules
**Decision**: Split into detector, credential_sync, manager
**Rationale**:
- Single responsibility per module
- Independent testability
- Clear ownership
- Follows existing pattern (proxy/manager, docker/detector)

### 2. Non-Blocking Integration
**Decision**: Never crash launcher on Neo4j errors
**Rationale**:
- Neo4j is optional feature
- User can configure manually
- Better UX (launcher always works)
- Follows Unix philosophy

### 3. Four User Choices
**Decision**: Exactly 4 options (explicit requirement)
**Rationale**:
- User requirement (cannot be optimized away)
- Covers all real-world scenarios
- Clear decision tree
- No ambiguity

### 4. .env Synchronization
**Decision**: Direct .env manipulation with backup
**Rationale**:
- Simple key=value format
- Backup protects users
- Preserves other settings
- Standard approach

### 5. Port Conflict Resolution
**Decision**: Auto-find available ports for new containers
**Rationale**:
- Common in multi-environment dev
- Better UX (just works)
- Low complexity
- Prevents frustration

## Implementation Strategy

### Build Order (CRITICAL)
1. **Phase 1**: `neo4j/detector.py` (Day 1)
   - No dependencies on new code
   - Easiest to test in isolation
   - Foundation for other modules

2. **Phase 2**: `neo4j/credential_sync.py` (Day 2)
   - Depends only on detector
   - Test extraction and .env sync
   - Integration test: detect + extract

3. **Phase 3**: `neo4j/manager.py` (Day 3)
   - Depends on both previous modules
   - Test user interaction flow
   - Integration test: full workflow

4. **Phase 4**: `launcher/core.py` integration (Day 4)
   - Minimal changes (2 modifications)
   - End-to-end testing
   - Verify no regressions

### Testing Strategy
- **Unit Tests**: Each module independently (>80% coverage)
- **Integration Tests**: Full flow with real Docker
- **Manual Tests**: All 4 user choices, edge cases
- **Regression Tests**: Existing launcher tests still pass

## Edge Cases Handled

### Container States
- Running container with credentials ✓
- Stopped container (can still extract) ✓
- Non-standard ports ✓
- Multiple containers (show newest) ✓
- No containers found ✓

### Credential Extraction
- NEO4J_AUTH env var ✓
- NEO4J_PASSWORD env var ✓
- No credentials (show uncertain) ✓
- Docker secrets ✓
- Container stopped ✓

### Port Management
- Default ports available ✓
- Default ports in use (find alternatives) ✓
- Non-standard ports ✓
- Port conflicts ✓

### .env File States
- Exists with Neo4j config ✓
- Exists without Neo4j config ✓
- Doesn't exist (create new) ✓
- Not writable (error gracefully) ✓

### User Input
- Valid choice (1-4) ✓
- Invalid choice (re-prompt) ✓
- Non-numeric input (re-prompt) ✓
- EOF/Ctrl+C (treat as skip) ✓

## Success Criteria

### Functional Requirements
- Detects existing Neo4j containers (running and stopped) ✓
- Extracts credentials from containers ✓
- Presents exactly 4 clear choices ✓
- Syncs credentials based on choice ✓
- Handles all edge cases ✓
- Never crashes launcher ✓

### Non-Functional Requirements
- Clear, user-friendly output ✓
- Fast execution (<2 seconds) ✓
- No side effects on choice 3/4 ✓
- .env backup before modification ✓
- Follows amplihack style ✓

### Quality Metrics
- Test coverage >80% ✓
- Pyright clean ✓
- Ruff clean ✓
- Manual testing complete ✓

## Out of Scope (Explicit)

These are NOT part of this implementation:

- ❌ Container creation (choice 2 execution)
- ❌ Container lifecycle management
- ❌ Neo4j health checking
- ❌ Automatic password rotation
- ❌ Multi-container orchestration
- ❌ Neo4j version management

**Rationale**: Start minimal, validate workflow, add complexity only when justified by real user needs.

## Dependencies

### Required
- `docker` Python library (existing dependency)
- `pathlib`, `dataclasses`, `typing` (stdlib)
- `secrets`, `socket`, `shutil` (stdlib)

### Optional
- None (all features work without optional deps)

## Configuration

### .env Keys Modified
```bash
NEO4J_USER=neo4j
NEO4J_PASSWORD=<extracted or generated>
NEO4J_HTTP_PORT=7474
NEO4J_BOLT_PORT=7687
```

### Backup Format
```
.env.backup.<timestamp>
Example: .env.backup.20250107_143022
```

## Error Handling Philosophy

**Principle**: Fail gracefully, never crash

### Error Categories
1. **Fatal** (prevent feature): Log error, return early, continue launcher
2. **Recoverable** (workaround): Log warning, use fallback, continue
3. **User** (invalid input): Friendly message, re-prompt

### Specific Handlers
- Docker daemon down → log warning, skip feature
- .env not writable → log error, suggest manual config
- Can't extract credentials → log warning, offer manual option
- Port conflict → find alternative ports
- Invalid user input → re-prompt with guidance

## Philosophy Alignment

### Ruthless Simplicity
- Three focused modules (not too few, not too many)
- Direct, imperative code (no abstractions)
- Clear data structures (dataclasses)
- Simple .env parsing (no libraries)

### Modular Design
- Each module = one brick
- Clear interfaces = studs
- Independent testing
- Regeneratable from spec

### Zero-BS Implementation
- No stubs or placeholders
- Every function works or doesn't exist
- No dead code
- No future-proofing

### Trust Model
- User in control (4 clear choices)
- Non-blocking (launcher always works)
- Graceful degradation
- Clear feedback

## Implementation Guidance

### For Builder Agent

**Start Here**: `/Users/ryan/src/amplihack/Specs/Neo4jBuilderGuide.md`

**Critical Rules**:
1. Build in order: detector → credential_sync → manager → integration
2. No stubs or placeholders (working code only)
3. Type hints everywhere (pyright clean)
4. Test each phase before moving on
5. Never crash launcher (catch all exceptions)

**First Command**:
```bash
cd /Users/ryan/src/amplihack
mkdir -p neo4j
touch neo4j/__init__.py
# Start implementing neo4j/detector.py
```

### For Reviewer Agent

**Review Criteria**:
1. Follows specification exactly (no deviations)
2. Error handling comprehensive (all paths covered)
3. Type hints present (pyright clean)
4. Tests written and passing (>80% coverage)
5. Philosophy alignment (simple, modular, zero-BS)

**Check Against**: `/Users/ryan/src/amplihack/Specs/Neo4jContainerSync.md`

### For Tester Agent

**Test Suite**:
1. Unit tests for each module
2. Integration tests for full flow
3. Manual tests for all edge cases
4. Regression tests for launcher

**Test Plan**: See `Neo4jContainerSync.md` section "Testing Strategy"

## Next Steps

1. **Builder**: Read `Neo4jBuilderGuide.md` and start with `detector.py`
2. **User**: Review this summary, ask questions if anything unclear
3. **Reviewer**: Stand by to review completed implementation
4. **Tester**: Prepare test environment (Docker, Neo4j containers)

## Questions?

- **Need more detail?** Check specific document based on topic
- **Unclear requirement?** See `Neo4jContainerSync.md`
- **Implementation question?** See `Neo4jBuilderGuide.md`
- **Integration question?** See `Neo4jLauncherIntegration.md`

---

## Document Version History

- **v1.0** (2025-01-07): Initial architecture design
  - Complete specification
  - Visual diagrams
  - Builder guide
  - Integration spec
  - This summary

---

**Ready to hand off to builder agent.**
