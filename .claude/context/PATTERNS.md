# Development Patterns & Solutions

This document captures proven patterns, solutions to common problems, and lessons learned from development. It serves as a quick reference for recurring challenges.

## Pattern: Documentation Discovery Before Code Analysis

### Challenge

During investigations, agents often dive directly into code exploration without checking if existing documentation (README, ARCHITECTURE, design docs) already explains the systems being investigated. This leads to:

- Reinventing the wheel (re-discovering what's already documented)
- Missing important context that documentation provides
- Unable to identify gaps between documentation and implementation
- Slower investigations when good docs exist

### Solution

Always perform a documentation discovery phase before code analysis:

```markdown
## Documentation Discovery Process

1. **Search for Documentation Files** (using Glob):
   - \*\*/README.md - Project and module overviews
   - \*\*/ARCHITECTURE.md - System design documentation
   - **/docs/**/\*.md - Detailed documentation
   - \*_/_.md (in investigation scope) - Any other markdown docs

2. **Filter by Relevance** (using Grep):
   - Extract keywords from investigation topic
   - Search documentation for related terms
   - Prioritize: README > ARCHITECTURE > specific docs
   - Limit initial reading to top 5 most relevant files

3. **Read Relevant Documentation** (using Read):
   - Extract: Purpose, architecture, key concepts
   - Identify: What features are documented
   - Note: Design decisions and constraints
   - Map: Component relationships and dependencies

4. **Establish Documentation Baseline**:
   - What does documentation claim exists?
   - What architectural patterns are described?
   - What is well-documented vs. poorly documented?

5. **Use Documentation to Guide Analysis**:
   - Verify: Does code implement what docs describe?
   - Find Gaps: What code exists but isn't documented?
   - Identify Drift: Where do docs and code diverge?
   - Report Discrepancies: Flag doc/code inconsistencies
```

### Example Usage in Agent

```markdown
Before analyzing [TOPIC], I'll first discover existing documentation:

[Run Glob for **/README.md, **/ARCHITECTURE.md, **/docs/**/*.md]
[Run Grep for keywords related to TOPIC]
[Read top 5 most relevant files]

Documentation Discovery Results:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Found: 15 documentation files
✓ Relevant: 3 files analyzed
✓ Key Claims:

- Feature X is implemented using pattern Y
- Module Z handles authentication
- Architecture follows microservices pattern
  ⚠ Documentation Gaps:
- API endpoints not documented
- Error handling strategy unclear
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Now proceeding to code analysis to verify these claims...
```

### Key Points

- **Always discover docs first** - Mandatory step before code analysis
- **30-second limit** - Quick discovery doesn't slow investigations
- **Graceful degradation** - Handle missing/outdated docs without failing
- **Gap identification** - Report doc/code discrepancies as valuable findings
- **Reusable pattern** - Copy to any agent that performs investigations

### Benefits

- More comprehensive investigations leveraging existing knowledge
- Ability to identify gaps between documentation and implementation
- Faster understanding when good documentation exists
- Better context for code exploration
- Reduces wasted effort re-discovering documented information

### Integrated In

- `.claude/agents/amplihack/specialized/analyzer.md` - All three modes (TRIAGE, DEEP, SYNTHESIS)
- Can be added to other investigation or analysis agents

## Pattern: Claude Code SDK Integration

### Challenge

Integrating Claude Code SDK for AI-powered operations requires proper environment setup and timeout handling.

### Solution

```python
import asyncio
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions

async def extract_with_claude_sdk(prompt: str, timeout_seconds: int = 120):
    """Extract using Claude Code SDK with proper timeout handling"""
    try:
        # Always use 120-second timeout for SDK operations
        async with asyncio.timeout(timeout_seconds):
            async with ClaudeSDKClient(
                options=ClaudeCodeOptions(
                    system_prompt="Extract information...",
                    max_turns=1,
                )
            ) as client:
                await client.query(prompt)

                response = ""
                async for message in client.receive_response():
                    if hasattr(message, "content"):
                        content = getattr(message, "content", [])
                        if isinstance(content, list):
                            for block in content:
                                if hasattr(block, "text"):
                                    response += getattr(block, "text", "")
                return response
    except asyncio.TimeoutError:
        print(f"Claude Code SDK timed out after {timeout_seconds} seconds")
        return ""
```

### Key Points

- **120-second timeout is optimal** - Gives SDK enough time without hanging forever
- **SDK only works in Claude Code environment** - Accept empty results outside
- **Handle markdown in responses** - Strip ```json blocks before parsing

## Pattern: Resilient Batch Processing

### Challenge

Processing large batches where individual items might fail, but we want to maximize successful processing.

### Solution

```python
class ResilientProcessor:
    async def process_batch(self, items):
        results = {"succeeded": [], "failed": []}

        for item in items:
            try:
                result = await self.process_item(item)
                results["succeeded"].append(result)
                # Save progress immediately
                self.save_results(results)
            except Exception as e:
                results["failed"].append({
                    "item": item,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
                # Continue processing other items
                continue

        return results
```

### Key Points

- **Save after every item** - Never lose progress
- **Continue on failure** - Don't let one failure stop the batch
- **Track failure reasons** - Distinguish between types of failures
- **Support selective retry** - Only retry failed items

## Pattern: File I/O with Cloud Sync Resilience

### Challenge

File operations can fail mysteriously when directories are synced with cloud services (OneDrive, Dropbox).

### Solution

```python
import time
from pathlib import Path

def write_with_retry(filepath: Path, data: str, max_retries: int = 3):
    """Write file with exponential backoff for cloud sync issues"""
    retry_delay = 0.1

    for attempt in range(max_retries):
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_text(data)
            return
        except OSError as e:
            if e.errno == 5 and attempt < max_retries - 1:
                if attempt == 0:
                    print(f"File I/O error - retrying. May be cloud sync issue.")
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                raise
```

### Key Points

- **Retry with exponential backoff** - Give cloud sync time to complete
- **Inform user about cloud sync** - Help them understand delays
- **Create parent directories** - Ensure path exists before writing

## Pattern: Async Context Management

### Challenge

Nested asyncio event loops cause hangs when integrating async SDKs.

### Solution

```python
# WRONG - Creates nested event loops
class Service:
    def process(self, data):
        return asyncio.run(self._async_process(data))  # Creates new loop

# Called from async context:
await loop.run_in_executor(None, service.process, data)  # Nested loops!

# RIGHT - Pure async throughout
class Service:
    async def process(self, data):
        return await self._async_process(data)  # No new loop

# Called from async context:
await service.process(data)  # Clean async chain
```

### Key Points

- **Never mix sync/async APIs** - Choose one approach
- **Avoid asyncio.run() in libraries** - Let caller manage the event loop
- **Design APIs to be fully async or fully sync** - Not both

## Pattern: Module Regeneration Structure

### Challenge

Creating modules that can be regenerated by AI without breaking system integration.

### Solution

```
module_name/
├── __init__.py         # Public interface ONLY via __all__
├── README.md           # Contract specification (required)
├── core.py             # Main implementation
├── models.py           # Data structures
├── tests/
│   ├── test_contract.py    # Verify public interface
│   └── test_core.py         # Unit tests
└── examples/
    └── basic_usage.py       # Working example
```

### Key Points

- **Contract in README.md** - AI can regenerate from this spec
- \***\*all** defines public interface\*\* - Clear boundary
- **Tests verify contract** - Not implementation details
- **Examples must work** - Validated by tests

## Pattern: Zero-BS Implementation

### Challenge

Avoiding stub code and placeholders that serve no purpose.

### Solution

```python
# BAD - Stub that does nothing
def process_payment(amount):
    # TODO: Implement Stripe integration
    raise NotImplementedError("Coming soon")

# GOOD - Working implementation
def process_payment(amount, payments_file="payments.json"):
    """Record payment locally - fully functional."""
    payment = {
        "amount": amount,
        "timestamp": datetime.now().isoformat(),
        "id": str(uuid.uuid4())
    }

    # Load and update
    payments = []
    if Path(payments_file).exists():
        payments = json.loads(Path(payments_file).read_text())

    payments.append(payment)
    Path(payments_file).write_text(json.dumps(payments, indent=2))

    return payment
```

### Key Points

- **Every function must work** - Or not exist
- **Use files instead of external services** - Start simple
- **No TODOs without code** - Implement or remove
- **Legitimate empty patterns are OK** - e.g., `pass` in Click groups

## Pattern: Incremental Processing

### Challenge

Supporting resumable, incremental processing of large datasets.

### Solution

```python
class IncrementalProcessor:
    def __init__(self, state_file="processing_state.json"):
        self.state_file = Path(state_file)
        self.state = self.load_state()

    def load_state(self):
        if self.state_file.exists():
            return json.loads(self.state_file.read_text())
        return {"processed": [], "failed": [], "last_id": None}

    def save_state(self):
        self.state_file.write_text(json.dumps(self.state, indent=2))

    def process_items(self, items):
        for item in items:
            if item.id in self.state["processed"]:
                continue  # Skip already processed

            try:
                self.process_item(item)
                self.state["processed"].append(item.id)
                self.state["last_id"] = item.id
                self.save_state()  # Save after each item
            except Exception as e:
                self.state["failed"].append({
                    "id": item.id,
                    "error": str(e)
                })
                self.save_state()
```

### Key Points

- **Save state after every item** - Resume from exact position
- **Track both success and failure** - Know what needs retry
- **Use fixed filenames** - Easy to find and resume
- **Support incremental updates** - Add new items without reprocessing

## Pattern: Configuration Single Source of Truth

### Challenge

Configuration scattered across multiple files causes drift and maintenance burden.

### Solution

```python
# Single source: pyproject.toml
[tool.myapp]
exclude = [".venv", "__pycache__", "node_modules"]
timeout = 30
batch_size = 100

# Read from single source
import tomllib

def load_config():
    with open("pyproject.toml", "rb") as f:
        config = tomllib.load(f)
    return config["tool"]["myapp"]

# Use everywhere
config = load_config()
excludes = config["exclude"]  # Don't hardcode these elsewhere
```

### Key Points

- **One authoritative location** - pyproject.toml for Python projects
- **Read, don't duplicate** - Load config at runtime
- **Document the source** - Make it clear where config lives
- **Accept minimal duplication** - Only for bootstrap/emergency

## Pattern: Parallel Task Execution

### Challenge

Executing multiple independent operations efficiently.

### Solution

```python
# WRONG - Sequential execution
results = []
for item in items:
    result = await process(item)
    results.append(result)

# RIGHT - Parallel execution
tasks = [process(item) for item in items]
results = await asyncio.gather(*tasks)

# With error handling
async def safe_process(item):
    try:
        return await process(item)
    except Exception as e:
        return {"error": str(e), "item": item}

tasks = [safe_process(item) for item in items]
results = await asyncio.gather(*tasks)
```

### Key Points

- **Use asyncio.gather() for parallel work** - Much faster
- **Wrap in error handlers** - Prevent one failure from stopping all
- **Consider semaphores for rate limiting** - Control concurrency
- **Return errors as values** - Don't let exceptions propagate

## Pattern: CI Failure Rapid Diagnosis

### Challenge

CI failures require systematic investigation across multiple dimensions (environment, syntax, logic, dependencies) while minimizing time to resolution. Traditional sequential debugging can take 45+ minutes.

### Solution

Deploy specialized agents in parallel for comprehensive diagnosis, targeting 20-25 minute resolution:

```python
# Parallel Agent Orchestration for CI Debugging
async def diagnose_ci_failure(pr_number: str, failure_logs: str):
    """Rapid CI failure diagnosis using parallel agent deployment"""

    # Phase 1: Environment Quick Check (2-3 minutes)
    basic_checks = await asyncio.gather(
        check_environment_setup(),
        validate_dependencies(),
        verify_branch_status()
    )

    if basic_checks_pass(basic_checks):
        # Phase 2: Parallel Specialized Diagnosis (8-12 minutes)
        diagnostic_tasks = [
            # Core diagnostic agents
            Task("ci-diagnostics", f"Analyze CI logs for {pr_number}"),
            Task("silent-failure-detector", "Identify silent test failures"),
            Task("pattern-matcher", "Match against known failure patterns")
        ]

        # Deploy all agents simultaneously
        results = await asyncio.gather(*[
            agent.execute(task) for agent, task in zip(
                [ci_diagnostics_agent, silent_failure_agent, pattern_agent],
                diagnostic_tasks
            )
        ])

        # Phase 3: Synthesis and Action (5-8 minutes)
        diagnosis = synthesize_findings(results)
        action_plan = create_fix_strategy(diagnosis)

        return {
            "root_cause": diagnosis.primary_issue,
            "fix_strategy": action_plan,
            "confidence": diagnosis.confidence_score,
            "estimated_fix_time": action_plan.time_estimate
        }

    return {"requires_escalation": True, "basic_check_failures": basic_checks}
```

### Agent Coordination Workflow

```
┌─── Environment Check (2-3 min) ───┐
│   ├── Dependencies valid?          │
│   ├── Branch conflicts?            │
│   └── Basic setup correct?         │
└─────────────┬───────────────────────┘
              │
              ▼ (if environment OK)
┌─── Parallel Diagnosis (8-12 min) ──┐
│   ├── ci-diagnostics.md            │
│   │   └── Parse logs, find errors  │
│   ├── silent-failure-detector.md   │
│   │   └── Find hidden failures     │
│   └── pattern-matcher.md           │
│       └── Match known patterns     │
└─────────────┬───────────────────────┘
              │
              ▼
┌─── Synthesis & Action (5-8 min) ───┐
│   ├── Combine findings             │
│   ├── Identify root cause          │
│   ├── Generate fix strategy        │
│   └── Execute solution             │
└─────────────────────────────────────┘
```

### Decision Points

```python
def should_escalate(diagnosis_results):
    """Decide whether to escalate or continue automated fixing"""
    escalate_triggers = [
        diagnosis_results.confidence < 0.7,
        diagnosis_results.estimated_fix_time > 30,  # minutes
        diagnosis_results.requires_infrastructure_change,
        diagnosis_results.affects_multiple_systems
    ]
    return any(escalate_triggers)

def should_parallel_debug(initial_scan):
    """Determine if parallel agent deployment is worth it"""
    return (
        initial_scan.environment_healthy and
        initial_scan.failure_complexity > "simple" and
        initial_scan.logs_available
    )
```

### Tool Integration

```bash
# Environment checks (use built-in tools)
gh pr view ${PR_NUMBER} --json statusCheckRollup
git status --porcelain
npm test --dry-run  # or equivalent

# Agent delegation (use Task tool)
Task("ci-diagnostics", {
    "pr_number": pr_number,
    "logs": failure_logs,
    "focus": "error_identification"
})

# Pattern capture (update DISCOVERIES.md)
echo "## CI Pattern: ${failure_type}
- Root cause: ${root_cause}
- Solution: ${solution}
- Time to resolve: ${resolution_time}
- Confidence: ${confidence_score}" >> DISCOVERIES.md
```

### Specialized Agents Used

1. **ci-diagnostics.md**: Parse CI logs, identify error patterns, suggest fixes
2. **silent-failure-detector.md**: Find tests that pass but shouldn't, timeout issues
3. **pattern-matcher.md**: Match against historical failures, suggest proven solutions

### Time Optimization Strategies

- **Environment First**: Eliminate basic issues before deep diagnosis (saves 10-15 min)
- **Parallel Deployment**: Run all diagnostic agents simultaneously (saves 15-20 min)
- **Pattern Matching**: Use historical data to shortcut common issues (saves 5-10 min)
- **Confidence Thresholds**: Escalate low-confidence diagnoses early (prevents wasted time)

### Learning Loop Integration

```python
def capture_ci_pattern(failure_type, solution, resolution_time):
    """Capture successful patterns for future use"""
    pattern_entry = {
        "failure_signature": extract_signature(failure_type),
        "solution_steps": solution.steps,
        "resolution_time": resolution_time,
        "confidence_score": solution.confidence,
        "timestamp": datetime.now().isoformat()
    }

    # Add to DISCOVERIES.md for pattern recognition
    append_to_discoveries(pattern_entry)

    # Update pattern-matcher agent with new pattern
    update_pattern_database(pattern_entry)
```

### Success Metrics

- **Target Resolution Time**: 20-25 minutes (down from 45+ minutes)
- **Confidence Threshold**: >0.7 for automated fixes
- **Escalation Rate**: <20% of CI failures
- **Pattern Recognition Hit Rate**: >60% for repeat issues

### Key Points

- **Environment checks prevent wasted effort** - Always validate basics first
- **Parallel agent deployment is crucial** - Don't debug sequentially
- **Capture patterns immediately** - Update DISCOVERIES.md after every resolution
- **Use confidence scores for escalation** - Don't waste time on uncertain diagnoses
- **Historical patterns accelerate resolution** - Build and use pattern database
- **Specialized agents handle complexity** - Each agent has focused expertise

### Integration with Existing Patterns

- **Combines with Parallel Task Execution** - Uses asyncio.gather() for agent coordination
- **Follows Zero-BS Implementation** - All diagnostic code must work, no stubs
- **Uses Configuration Single Source** - CI settings centralized in pyproject.toml
- **Implements Incremental Processing** - Builds pattern database over time

## Pattern: Unified Validation Flow

### Challenge

Systems with multiple execution modes (UVX, normal) that have divergent validation paths, causing inconsistent behavior and hard-to-debug issues.

### Solution

Move all validation logic before execution mode branching to ensure consistent behavior across all modes.

```python
class SystemLauncher:
    def prepare_launch(self) -> bool:
        """Unified validation before mode-specific logic"""

        # Universal validation for ALL modes - no exceptions
        target_dir = self.detector.find_target_directory()
        if not target_dir:
            print("No valid target directory found")
            return False

        # Validate directory security and accessibility
        if not self.validate_directory_security(target_dir):
            print(f"Directory failed security validation: {target_dir}")
            return False

        # Now branch to mode-specific handling with validated directory
        if self.is_special_mode():
            return self._handle_special_mode(target_dir)
        else:
            return self._handle_normal_mode(target_dir)
```

### Key Points

- **Validate before branching** - Ensure all modes get same validation
- **No execution mode should bypass validation** - Creates divergent behavior
- **Pass validated data to mode handlers** - Don't re-validate
- **Log validation results** - Help debug validation failures

### Real Impact

From PR #148: Fixed UVX users ending up in wrong directory by moving directory validation before UVX/normal mode branching.

## Pattern: Modular User Visibility

### Challenge

Background processes that appear broken because users can't see progress, but adding visibility shouldn't break existing functionality.

### Solution

Create dedicated display modules that can be imported optionally and provide graceful fallbacks.

```python
# display.py - Standalone visibility module
def show_progress(message: str, stage: str = "info"):
    """User-visible progress indicator with emoji-based stages"""
    stage_icons = {
        "start": "🤖",
        "progress": "🔍",
        "success": "✅",
        "warning": "⚠️",
        "complete": "🏁"
    }

    print(f"{stage_icons.get(stage, 'ℹ️')} {message}")

def show_analysis_header(total_items: int):
    """Clear analysis start indicator"""
    print(f"\n{'=' * 60}")
    print(f"🤖 AI ANALYSIS STARTING")
    print(f"📊 Processing {total_items} items...")
    print(f"{'=' * 60}")

# In main processing module
def analyze_data(data):
    """Analysis with optional user feedback"""
    try:
        from .display import show_progress, show_analysis_header
        show_analysis_header(len(data))

        for i, item in enumerate(data):
            show_progress(f"Processing item {i+1}/{len(data)}")
            result = process_item(item)

        show_progress("Analysis complete", "complete")
        return results

    except ImportError:
        # Graceful fallback when display module unavailable
        return process_silently(data)
```

### Key Points

- **Optional dependency on display module** - System works without it
- **Clear progress indicators** - Use emoji and consistent formatting
- **Modular design** - Display logic separate from business logic
- **Environment-controlled verbosity** - Respect user preferences

### Real Impact

From PR #147: Made reflection system visible to users while maintaining all existing functionality through optional display module.

## Pattern: Multi-Layer Security Sanitization

### Challenge

Sensitive data (passwords, tokens, system paths) appearing in user output, logs, or stored analysis files across multiple processing layers.

### Solution

Implement sanitization at every data transformation point with safe fallbacks.

```python
# security.py - Dedicated security module
import re
from typing import Dict, List

class ContentSanitizer:
    """Multi-layer content sanitization with fallback strategies"""

    SENSITIVE_PATTERNS = [
        r'password["\s]*[:=]["\s]*[^\s"]+',
        r'token["\s]*[:=]["\s]*[^\s"]+',
        r'api[_-]?key["\s]*[:=]["\s]*[^\s"]+',
        r'secret["\s]*[:=]["\s]*[^\s"]+',
        r'auth["\s]*[:=]["\s]*[^\s"]+',
    ]

    SYSTEM_PATHS = [
        r'/etc/[^\s]*',
        r'/private/etc/[^\s]*',
        r'/usr/bin/[^\s]*',
        r'/System/Library/[^\s]*',
    ]

    def sanitize_content(self, content: str, max_length: int = 10000) -> str:
        """Comprehensive content sanitization"""
        if not content:
            return content

        # Length limit to prevent information leakage
        if len(content) > max_length:
            content = content[:max_length] + "... [truncated for security]"

        # Remove sensitive credentials
        for pattern in self.SENSITIVE_PATTERNS:
            content = re.sub(pattern, "[REDACTED]", content, flags=re.IGNORECASE)

        # Remove system paths
        for pattern in self.SYSTEM_PATHS:
            content = re.sub(pattern, "[SYSTEM_PATH]", content)

        return content

# In processing modules - sanitize at every layer
def process_user_input(raw_input: str) -> str:
    """Input sanitization layer"""
    try:
        from .security import ContentSanitizer
        sanitizer = ContentSanitizer()
        return sanitizer.sanitize_content(raw_input)
    except ImportError:
        # Safe fallback sanitization
        return basic_sanitize(raw_input)

def store_analysis(data: Dict) -> None:
    """Storage sanitization layer"""
    try:
        from .security import ContentSanitizer
        sanitizer = ContentSanitizer()

        # Sanitize all string values before storage
        sanitized_data = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized_data[key] = sanitizer.sanitize_content(value)
            else:
                sanitized_data[key] = value

        save_to_file(sanitized_data)
    except ImportError:
        # Sanitize with basic patterns if security module unavailable
        save_to_file(basic_sanitize_dict(data))

def display_to_user(content: str) -> None:
    """Output sanitization layer"""
    try:
        from .security import ContentSanitizer
        sanitizer = ContentSanitizer()
        print(sanitizer.sanitize_content(content))
    except ImportError:
        print(basic_sanitize(content))

def basic_sanitize(content: str) -> str:
    """Fallback sanitization when security module unavailable"""
    # Basic patterns for critical security
    patterns = [
        (r'password["\s]*[:=]["\s]*[^\s"]+', '[REDACTED]'),
        (r'token["\s]*[:=]["\s]*[^\s"]+', '[REDACTED]'),
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)

    return content
```

### Key Points

- **Sanitize at every transformation** - Input, processing, storage, output
- **Safe fallback patterns** - Basic sanitization if security module fails
- **Length limits prevent leakage** - Truncate very long content
- **Multiple pattern types** - Credentials, paths, personal data
- **Never fail on security errors** - Always provide fallback

### Real Impact

From PR #147: Implemented comprehensive sanitization that prevented sensitive data exposure while maintaining system functionality through fallback strategies.

## Pattern: Intelligent Caching with Lifecycle Management

### Challenge

Expensive operations (path resolution, environment detection) repeated unnecessarily, but naive caching leads to memory leaks and stale data.

### Solution

Implement smart caching with invalidation strategies and resource management.

```python
from functools import lru_cache
from typing import Optional, Dict, Any
import threading

class SmartCache:
    """Intelligent caching with lifecycle management"""

    def __init__(self, max_size: int = 128):
        self.max_size = max_size
        self._cache_stats = {"hits": 0, "misses": 0}
        self._lock = threading.RLock()

    @lru_cache(maxsize=128)
    def expensive_operation(self, input_data: str) -> str:
        """Cached expensive operation with automatic size management"""
        # Expensive computation here
        result = self._compute_expensive_result(input_data)

        # Track cache performance
        with self._lock:
            cache_info = self.expensive_operation.cache_info()
            if cache_info.hits > self._cache_stats["hits"]:
                self._cache_stats["hits"] = cache_info.hits
            else:
                self._cache_stats["misses"] += 1

        return result

    def invalidate_cache(self) -> None:
        """Clear cache when data might be stale"""
        with self._lock:
            self.expensive_operation.cache_clear()
            self._cache_stats = {"hits": 0, "misses": 0}

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance metrics"""
        with self._lock:
            cache_info = self.expensive_operation.cache_info()
            return {
                "hits": cache_info.hits,
                "misses": cache_info.misses,
                "current_size": cache_info.currsize,
                "max_size": cache_info.maxsize,
                "hit_rate": cache_info.hits / max(1, cache_info.hits + cache_info.misses)
            }

# Thread-safe lazy initialization pattern
class LazyResource:
    """Lazy initialization with thread safety"""

    def __init__(self):
        self._resource = None
        self._initialized = False
        self._lock = threading.RLock()

    def _ensure_initialized(self) -> None:
        """Thread-safe lazy initialization"""
        with self._lock:
            if not self._initialized:
                self._resource = self._create_expensive_resource()
                self._initialized = True

    def get_resource(self):
        """Get resource, initializing if needed"""
        self._ensure_initialized()
        return self._resource

    def invalidate(self) -> None:
        """Force re-initialization on next access"""
        with self._lock:
            self._resource = None
            self._initialized = False
```

### Key Points

- **Use lru_cache for automatic size management** - Prevents unbounded growth
- **Thread safety is essential** - Multiple threads may access simultaneously
- **Provide invalidation methods** - Cache must be clearable when stale
- **Track cache performance** - Monitor hit rates for optimization
- **Lazy initialization with locks** - Don't initialize until needed

### Real Impact

From PR #148: Added intelligent caching that achieved 4.1x and 10x performance improvements while maintaining thread safety and preventing memory leaks.

## Pattern: Graceful Environment Adaptation

### Challenge

Systems that need different behavior in different environments (UVX, normal, testing) without hard-coding environment-specific logic everywhere.

### Solution

Detect environment automatically and adapt behavior through configuration objects and environment variables.

```python
class EnvironmentAdapter:
    """Automatic environment detection and adaptation"""

    def __init__(self):
        self._environment = None
        self._config = None

    def detect_environment(self) -> str:
        """Automatically detect current execution environment"""
        if self._environment:
            return self._environment

        # Detection logic
        if self._is_uvx_environment():
            self._environment = "uvx"
        elif self._is_testing_environment():
            self._environment = "testing"
        else:
            self._environment = "normal"

        return self._environment

    def get_config(self) -> Dict[str, Any]:
        """Get environment-specific configuration"""
        if self._config:
            return self._config

        env = self.detect_environment()

        # Environment-specific configurations
        configs = {
            "uvx": {
                "use_add_dir": True,
                "validate_paths": True,
                "working_directory": "auto_detect",
                "timeout_multiplier": 1.5,
            },
            "normal": {
                "use_add_dir": False,
                "validate_paths": True,
                "working_directory": "change_to_project",
                "timeout_multiplier": 1.0,
            },
            "testing": {
                "use_add_dir": False,
                "validate_paths": False,  # Faster tests
                "working_directory": "temp",
                "timeout_multiplier": 0.5,
            }
        }

        self._config = configs.get(env, configs["normal"])

        # Allow environment variable overrides
        self._apply_env_overrides()

        return self._config

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides"""
        import os

        # Map environment variables to config keys
        env_mappings = {
            "AMPLIHACK_USE_ADD_DIR": ("use_add_dir", lambda x: x.lower() == "true"),
            "AMPLIHACK_VALIDATE_PATHS": ("validate_paths", lambda x: x.lower() == "true"),
            "AMPLIHACK_TIMEOUT_MULTIPLIER": ("timeout_multiplier", float),
        }

        for env_var, (config_key, converter) in env_mappings.items():
            if env_var in os.environ:
                try:
                    self._config[config_key] = converter(os.environ[env_var])
                except (ValueError, TypeError):
                    # Log but don't fail on invalid environment variables
                    pass

# Usage pattern
class SystemManager:
    def __init__(self):
        self.adapter = EnvironmentAdapter()

    def execute(self):
        """Execute with environment-appropriate behavior"""
        config = self.adapter.get_config()

        if config["use_add_dir"]:
            return self._execute_with_add_dir()
        else:
            return self._execute_with_directory_change()
```

### Key Points

- **Automatic environment detection** - Don't require manual configuration
- **Configuration objects over scattered conditionals** - Centralize environment logic
- **Environment variable overrides** - Allow runtime customization
- **Sensible defaults for each environment** - Work out of the box
- **Graceful degradation** - Handle invalid configurations

### Real Impact

From PR #148: Enabled seamless operation across UVX and normal environments while maintaining consistent behavior and allowing user customization.

## Pattern: Reflection-Driven Self-Improvement

### Challenge

Systems that repeat the same mistakes because they don't learn from user interactions or identify improvement opportunities automatically.

### Solution

Implement AI-powered analysis of user sessions to automatically identify patterns and create improvement issues.

```python
class SessionReflector:
    """AI-powered session analysis for self-improvement"""

    def analyze_session(self, messages: List[Dict]) -> Dict:
        """Analyze session for improvement opportunities"""

        # Extract session patterns
        patterns = self._extract_patterns(messages)

        # Use AI to analyze patterns
        improvement_opportunities = self._ai_analyze_patterns(patterns)

        # Prioritize opportunities
        prioritized = self._prioritize_improvements(improvement_opportunities)

        return {
            "session_stats": self._get_session_stats(messages),
            "patterns": patterns,
            "improvements": prioritized,
            "automation_candidates": self._identify_automation_candidates(prioritized)
        }

    def _extract_patterns(self, messages: List[Dict]) -> List[Dict]:
        """Extract behavioral patterns from session"""
        patterns = []

        # Error patterns
        error_count = 0
        error_types = {}

        for msg in messages:
            content = str(msg.get("content", ""))

            if "error" in content.lower():
                error_count += 1
                # Extract error type
                error_type = self._classify_error(content)
                error_types[error_type] = error_types.get(error_type, 0) + 1

        if error_count > 2:
            patterns.append({
                "type": "error_handling",
                "severity": "high" if error_count > 5 else "medium",
                "details": {"total_errors": error_count, "error_types": error_types}
            })

        # Repetition patterns
        repeated_actions = self._find_repeated_actions(messages)
        if repeated_actions:
            patterns.append({
                "type": "workflow_inefficiency",
                "severity": "medium",
                "details": {"repeated_actions": repeated_actions}
            })

        return patterns

    def _ai_analyze_patterns(self, patterns: List[Dict]) -> List[Dict]:
        """Use AI to suggest improvements for patterns"""
        improvements = []

        for pattern in patterns:
            if pattern["type"] == "error_handling":
                improvements.append({
                    "type": "error_handling",
                    "priority": "high",
                    "suggestion": "Improve error handling and user feedback",
                    "evidence": f"Found {pattern['details']['total_errors']} errors",
                    "implementation_hint": "Add try-catch blocks with user-friendly messages"
                })

            elif pattern["type"] == "workflow_inefficiency":
                improvements.append({
                    "type": "automation",
                    "priority": "medium",
                    "suggestion": "Automate repetitive workflow steps",
                    "evidence": f"User repeated actions: {pattern['details']['repeated_actions']}",
                    "implementation_hint": "Create compound commands for common sequences"
                })

        return improvements

    def create_improvement_issue(self, improvement: Dict) -> Optional[str]:
        """Automatically create GitHub issue for improvement"""

        title = f"AI-detected {improvement['type']}: {improvement['suggestion'][:60]}"

        body = f"""# AI-Detected Improvement Opportunity

**Type**: {improvement['type']}
**Priority**: {improvement['priority']}
**Evidence**: {improvement.get('evidence', 'Detected during session analysis')}

## Suggestion
{improvement['suggestion']}

## Implementation Hint
{improvement.get('implementation_hint', 'See analysis for details')}

## Analysis Details
This improvement was identified by AI analysis of session logs. The system detected patterns indicating this area needs attention.

**Labels**: ai-improvement, {improvement['type']}, {improvement['priority']}-priority
"""

        # Create issue using GitHub CLI
        result = subprocess.run([
            "gh", "issue", "create",
            "--title", title,
            "--body", body,
            "--label", f"ai-improvement,{improvement['type']},{improvement['priority']}-priority"
        ], capture_output=True, text=True)

        if result.returncode == 0:
            issue_url = result.stdout.strip()
            return issue_url.split("/")[-1]  # Extract issue number

        return None
```

### Key Points

- **Analyze actual user behavior** - Don't guess at improvements
- **Use AI for pattern recognition** - Identify complex behavioral patterns
- **Automatic issue creation** - Convert insights to actionable work items
- **Evidence-based improvements** - Link suggestions to actual session data
- **Prioritization based on impact** - Focus on high-value improvements first

### Real Impact

From PR #147: Created self-improving system that analyzes 1,338+ session files and automatically creates GitHub issues for detected improvement opportunities.

## Pattern: Safe Subprocess Wrapper with Comprehensive Error Handling

### Challenge

Subprocess calls fail with cryptic error messages that don't help users understand what went wrong or how to fix it. Different subprocess errors (FileNotFoundError, PermissionError, TimeoutExpired) need different user-facing guidance.

### Solution

Create a safe subprocess wrapper that catches all error types and provides user-friendly, actionable error messages with context.

```python
def safe_subprocess_call(
    cmd: List[str],
    context: str,
    timeout: Optional[int] = 30,
) -> Tuple[int, str, str]:
    """Safely execute subprocess with comprehensive error handling.

    Args:
        cmd: Command and arguments to execute
        context: Human-readable context for what this command does
        timeout: Timeout in seconds (default 30)

    Returns:
        Tuple of (returncode, stdout, stderr)
        On error, returncode is non-zero and stderr contains helpful message
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr

    except FileNotFoundError:
        # Command not found - most common error
        cmd_name = cmd[0] if cmd else "command"
        error_msg = f"Command not found: {cmd_name}\n"
        if context:
            error_msg += f"Context: {context}\n"
        error_msg += "Please ensure the tool is installed and in your PATH."
        return 127, "", error_msg

    except PermissionError:
        cmd_name = cmd[0] if cmd else "command"
        error_msg = f"Permission denied: {cmd_name}\n"
        if context:
            error_msg += f"Context: {context}\n"
        error_msg += "Please check file permissions or run with appropriate privileges."
        return 126, "", error_msg

    except subprocess.TimeoutExpired:
        cmd_name = cmd[0] if cmd else "command"
        error_msg = f"Command timed out after {timeout}s: {cmd_name}\n"
        if context:
            error_msg += f"Context: {context}\n"
        error_msg += "The operation took too long to complete."
        return 124, "", error_msg

    except OSError as e:
        cmd_name = cmd[0] if cmd else "command"
        error_msg = f"OS error running {cmd_name}: {str(e)}\n"
        if context:
            error_msg += f"Context: {context}\n"
        return 1, "", error_msg

    except Exception as e:
        # Catch-all for unexpected errors
        cmd_name = cmd[0] if cmd else "command"
        error_msg = f"Unexpected error running {cmd_name}: {str(e)}\n"
        if context:
            error_msg += f"Context: {context}\n"
        return 1, "", error_msg
```

### Key Points

- **Standard exit codes** - Use conventional exit codes (127 for command not found, 126 for permission denied)
- **Context parameter is critical** - Always tell users what operation failed ("checking git version", "installing npm package")
- **User-friendly messages** - Avoid technical jargon, provide actionable guidance
- **No exceptions propagate** - Always return error info via return values
- **Default timeout** - 30 seconds prevents hanging on network issues

### When to Use

- ANY subprocess call in your codebase
- Especially when calling external tools (git, npm, uv, etc.)
- When users need to understand and fix issues themselves
- Replace all direct subprocess.run() calls with this wrapper

### Benefits

- Consistent error handling across entire codebase
- Users get actionable error messages
- No cryptic Python tracebacks for tool issues
- Easy to track what operation failed via context string

### Trade-offs

- Slightly more verbose than bare subprocess.run()
- Must provide context string (but this is a feature, not a bug)

### Related Patterns

- Combines with Platform-Specific Installation Guidance pattern
- Used by Fail-Fast Prerequisite Checking pattern

### Real Impact

From PR #457: Eliminated cryptic subprocess errors, making it clear when tools like npm or git are missing and exactly how to install them.

## Pattern: Platform-Specific Installation Guidance

### Challenge

Users on different platforms (macOS, Linux, WSL, Windows) need different installation commands. Providing generic "install X" guidance wastes user time looking up platform-specific instructions.

### Solution

Detect platform automatically and provide exact installation commands for that platform.

```python
from enum import Enum
import platform
from pathlib import Path

class Platform(Enum):
    """Supported platforms for prerequisite checking."""
    MACOS = "macos"
    LINUX = "linux"
    WSL = "wsl"
    WINDOWS = "windows"
    UNKNOWN = "unknown"

class PrerequisiteChecker:
    # Installation commands by platform and tool
    INSTALL_COMMANDS = {
        Platform.MACOS: {
            "node": "brew install node",
            "git": "brew install git",
        },
        Platform.LINUX: {
            "node": "# Ubuntu/Debian:\nsudo apt install nodejs\n# Fedora/RHEL:\nsudo dnf install nodejs\n# Arch:\nsudo pacman -S nodejs",
            "git": "# Ubuntu/Debian:\nsudo apt install git\n# Fedora/RHEL:\nsudo dnf install git\n# Arch:\nsudo pacman -S git",
        },
        Platform.WSL: {
            "node": "# Ubuntu/Debian:\nsudo apt install nodejs\n# Fedora/RHEL:\nsudo dnf install nodejs",
            "git": "sudo apt install git  # or your WSL distro's package manager",
        },
        Platform.WINDOWS: {
            "node": "winget install OpenJS.NodeJS\n# Or: choco install nodejs",
            "git": "winget install Git.Git\n# Or: choco install git",
        },
    }

    # Documentation links for each tool
    DOCUMENTATION_LINKS = {
        "node": "https://nodejs.org/",
        "git": "https://git-scm.com/",
    }

    def __init__(self):
        self.platform = self._detect_platform()

    def _detect_platform(self) -> Platform:
        """Detect the current platform."""
        system = platform.system()

        if system == "Darwin":
            return Platform.MACOS
        elif system == "Linux":
            if self._is_wsl():
                return Platform.WSL
            return Platform.LINUX
        elif system == "Windows":
            return Platform.WINDOWS
        else:
            return Platform.UNKNOWN

    def _is_wsl(self) -> bool:
        """Check if running under Windows Subsystem for Linux."""
        try:
            proc_version = Path("/proc/version")
            if proc_version.exists():
                content = proc_version.read_text().lower()
                return "microsoft" in content
        except (OSError, PermissionError):
            pass
        return False

    def get_install_command(self, tool: str) -> str:
        """Get platform-specific installation command for a tool."""
        platform_commands = self.INSTALL_COMMANDS.get(
            self.platform, self.INSTALL_COMMANDS.get(Platform.UNKNOWN, {})
        )
        return platform_commands.get(tool, f"Please install {tool} manually")

    def format_missing_prerequisites(self, missing_tools: List[str]) -> str:
        """Format user-friendly message with installation instructions."""
        lines = []
        lines.append("=" * 70)
        lines.append("MISSING PREREQUISITES")
        lines.append("=" * 70)
        lines.append("")
        lines.append("The following required tools are not installed:")
        lines.append("")

        for tool in missing_tools:
            lines.append(f"  ✗ {tool}")
        lines.append("")

        lines.append("=" * 70)
        lines.append("INSTALLATION INSTRUCTIONS")
        lines.append("=" * 70)
        lines.append("")
        lines.append(f"Platform detected: {self.platform.value}")
        lines.append("")

        for tool in missing_tools:
            lines.append(f"To install {tool}:")
            lines.append("")
            install_cmd = self.get_install_command(tool)
            for cmd_line in install_cmd.split("\n"):
                lines.append(f"  {cmd_line}")
            lines.append("")

            if tool in self.DOCUMENTATION_LINKS:
                lines.append(f"  Documentation: {self.DOCUMENTATION_LINKS[tool]}")
                lines.append("")

        lines.append("=" * 70)
        lines.append("")
        lines.append("After installing the missing tools, please run this command again.")

        return "\n".join(lines)
```

### Key Points

- **Automatic platform detection** - No user input needed
- **WSL detection is critical** - WSL needs different commands than native Linux
- **Multiple package managers** - Support apt, dnf, pacman, yum for Linux
- **Documentation links** - Give users official docs for complex installations
- **Clear formatting** - Use separators and indentation for readability

### When to Use

- Any tool that requires external dependencies
- CLI tools that users need to install before using your system
- Cross-platform Python applications
- Systems with multiple required tools

### Benefits

- Users get copy-paste commands that work
- No time wasted looking up installation instructions
- Supports Linux diversity (apt, dnf, pacman)
- WSL users get appropriate guidance

### Trade-offs

- Must maintain commands for each platform
- Commands may become outdated over time
- Doesn't cover all Linux distributions

### Related Patterns

- Works with Safe Subprocess Wrapper pattern
- Part of Fail-Fast Prerequisite Checking pattern

### Real Impact

From PR #457: Users on Windows/WSL got exact installation commands instead of generic "install Node.js" guidance, reducing setup time significantly.

## Pattern: Fail-Fast Prerequisite Checking

### Challenge

Users start using a tool, get cryptic errors mid-workflow when missing dependencies are discovered. This wastes time and creates frustration.

### Solution

Check all prerequisites at startup with clear, actionable error messages before any other operations.

```python
@dataclass
class ToolCheckResult:
    """Result of checking a single tool prerequisite."""
    tool: str
    available: bool
    path: Optional[str] = None
    version: Optional[str] = None
    error: Optional[str] = None

@dataclass
class PrerequisiteResult:
    """Result of checking all prerequisites."""
    all_available: bool
    missing_tools: List[ToolCheckResult] = field(default_factory=list)
    available_tools: List[ToolCheckResult] = field(default_factory=list)

class PrerequisiteChecker:
    # Required tools with their version check arguments
    REQUIRED_TOOLS = {
        "node": "--version",
        "npm": "--version",
        "uv": "--version",
        "git": "--version",
    }

    def check_tool(self, tool: str, version_arg: Optional[str] = None) -> ToolCheckResult:
        """Check if a single tool is available."""
        tool_path = shutil.which(tool)

        if not tool_path:
            return ToolCheckResult(
                tool=tool,
                available=False,
                error=f"{tool} not found in PATH",
            )

        # Tool found - optionally check version
        version = None
        if version_arg:
            returncode, stdout, stderr = safe_subprocess_call(
                [tool, version_arg],
                context=f"checking {tool} version",
                timeout=5,
            )
            if returncode == 0:
                version = stdout.strip().split("\n")[0] if stdout else None

        return ToolCheckResult(
            tool=tool,
            available=True,
            path=tool_path,
            version=version,
        )

    def check_all_prerequisites(self) -> PrerequisiteResult:
        """Check all required prerequisites."""
        missing_tools = []
        available_tools = []

        for tool, version_arg in self.REQUIRED_TOOLS.items():
            result = self.check_tool(tool, version_arg)

            if result.available:
                available_tools.append(result)
            else:
                missing_tools.append(result)

        return PrerequisiteResult(
            all_available=len(missing_tools) == 0,
            missing_tools=missing_tools,
            available_tools=available_tools,
        )

    def check_and_report(self) -> bool:
        """Check prerequisites and print report if any are missing.

        Returns:
            True if all prerequisites available, False otherwise
        """
        result = self.check_all_prerequisites()

        if result.all_available:
            return True

        # Print detailed report
        print(self.format_missing_prerequisites(result.missing_tools))
        return False

# Integration with launcher
class ClaudeLauncher:
    def prepare_launch(self) -> bool:
        """Prepare for launch - check prerequisites FIRST"""
        # Check prerequisites before anything else
        checker = PrerequisiteChecker()
        if not checker.check_and_report():
            return False

        # Now proceed with other setup
        return self._setup_environment()
```

### Key Points

- **Check at entry point** - Before any other operations
- **Check all at once** - Don't fail on first missing tool, show all issues
- **Structured results** - Use dataclasses for clear data contracts
- **Version checking optional** - Can verify specific versions if needed
- **Never auto-install** - User control and security first

### When to Use

- CLI tools with external dependencies
- Systems that call external tools (git, npm, docker)
- Before any operation that will fail without prerequisites
- At application startup, not mid-workflow

### Benefits

- Users know all issues upfront
- No time wasted in failed workflows
- Clear data structures for testing
- Easy to mock in tests

### Trade-offs

- Slight startup delay (typically < 1 second)
- May check tools that won't be used in this run
- Requires maintenance as tools change

### Related Patterns

- Uses Safe Subprocess Wrapper for checks
- Uses Platform-Specific Installation Guidance for error messages
- Part of TDD Testing Pyramid pattern

### Real Impact

From PR #457: Prevented users from starting workflows that would fail 5 minutes later due to missing npm, providing clear guidance immediately.

## Pattern: TDD Testing Pyramid for System Utilities

### Challenge

System utility modules interact with external tools and platform-specific behavior, making them hard to test comprehensively while maintaining fast test execution.

### Solution

Follow testing pyramid with 60% unit tests, 30% integration tests, 10% E2E tests, using strategic mocking for speed.

```python
"""Tests for prerequisites module - TDD approach.

Following the testing pyramid:
- 60% Unit tests (18 tests)
- 30% Integration tests (9 tests)
- 10% E2E tests (3 tests)
"""

# ============================================================================
# UNIT TESTS (60% - 18 tests)
# ============================================================================

class TestPlatformDetection:
    """Unit tests for platform detection."""

    def test_detect_macos(self):
        """Test macOS platform detection."""
        with patch("platform.system", return_value="Darwin"):
            checker = PrerequisiteChecker()
            assert checker.platform == Platform.MACOS

    def test_detect_wsl(self):
        """Test WSL platform detection."""
        with patch("platform.system", return_value="Linux"), \
             patch("pathlib.Path.exists", return_value=True), \
             patch("pathlib.Path.read_text", return_value="Linux version microsoft"):
            checker = PrerequisiteChecker()
            assert checker.platform == Platform.WSL

class TestToolChecking:
    """Unit tests for individual tool checking."""

    def test_check_tool_found(self):
        """Test checking for a tool that exists."""
        checker = PrerequisiteChecker()
        with patch("shutil.which", return_value="/usr/bin/git"):
            result = checker.check_tool("git")
            assert result.available is True
            assert result.path == "/usr/bin/git"

    def test_check_tool_with_version(self):
        """Test checking tool with version verification."""
        checker = PrerequisiteChecker()
        with patch("shutil.which", return_value="/usr/bin/node"), \
             patch("subprocess.run", return_value=Mock(returncode=0, stdout="v20.0.0", stderr="")):
            result = checker.check_tool("node", version_arg="--version")
            assert result.available is True
            assert result.version == "v20.0.0"

# ============================================================================
# INTEGRATION TESTS (30% - 9 tests)
# ============================================================================

class TestPrerequisiteIntegration:
    """Integration tests for prerequisite checking workflow."""

    def test_full_check_workflow_all_present(self):
        """Test complete prerequisite check when all tools present."""
        checker = PrerequisiteChecker()
        with patch("shutil.which") as mock_which:
            mock_which.side_effect = lambda x: f"/usr/bin/{x}"
            result = checker.check_all_prerequisites()

            assert result.all_available is True
            assert len(result.available_tools) == 4

    def test_platform_specific_install_commands(self):
        """Test that platform detection affects install commands."""
        platforms = [
            ("Darwin", Platform.MACOS, "brew"),
            ("Linux", Platform.LINUX, "apt"),
            ("Windows", Platform.WINDOWS, "winget"),
        ]

        for system, expected_platform, expected_cmd in platforms:
            with patch("platform.system", return_value=system):
                checker = PrerequisiteChecker()
                assert checker.platform == expected_platform
                install_cmd = checker.get_install_command("git")
                assert expected_cmd in install_cmd.lower()

# ============================================================================
# E2E TESTS (10% - 3 tests)
# ============================================================================

class TestEndToEnd:
    """End-to-end tests for complete prerequisite checking workflows."""

    def test_e2e_missing_prerequisites_with_guidance(self):
        """E2E: Complete workflow with missing prerequisites and user guidance."""
        with patch("platform.system", return_value="Darwin"):
            checker = PrerequisiteChecker()

            with patch("shutil.which", return_value=None):
                result = checker.check_all_prerequisites()
                assert result.all_available is False

                message = checker.format_missing_prerequisites(result.missing_tools)

                # Message should contain all missing tools
                assert all(tool in message.lower() for tool in ["node", "npm", "uv", "git"])
                # Installation commands
                assert "brew install" in message
                # Helpful context
                assert "prerequisite" in message.lower()
```

### Key Points

- **60% unit tests** - Fast, focused tests with heavy mocking
- **30% integration tests** - Multiple components working together
- **10% E2E tests** - Complete workflows with minimal mocking
- **Explicit test organization** - Comment blocks separate test levels
- **Strategic mocking** - Mock platform.system(), shutil.which(), subprocess calls
- **Test data structures** - Verify dataclass behavior

### When to Use

- System utilities that interact with OS/external tools
- Modules with platform-specific behavior
- Code that calls subprocess frequently
- Any module that needs fast tests despite external dependencies

### Benefits

- Fast test execution (all tests run in seconds)
- High confidence without slow E2E tests
- Easy to run in CI
- Clear test organization

### Trade-offs

- Heavy mocking may miss integration issues
- Platform-specific behavior harder to test comprehensively
- Mock maintenance when APIs change

### Related Patterns

- Tests the Fail-Fast Prerequisite Checking pattern
- Verifies Safe Subprocess Wrapper behavior
- Validates Platform-Specific Installation Guidance

### Real Impact

From PR #457: 70 tests run in < 2 seconds, providing comprehensive coverage of platform detection, tool checking, and error formatting without requiring actual tools installed.

## Pattern: Standard Library Only for Core Utilities

### Challenge

Core system utilities gain external dependencies, causing circular dependency issues or installation problems for users without those dependencies.

### Solution

Use only Python standard library for core utility modules. If advanced features need external dependencies, make them optional.

```python
"""Prerequisite checking and installation guidance.

Philosophy:
- Standard library only (no dependencies)
- Safe subprocess error handling throughout
- Platform-specific installation commands
- Never auto-install (user control and security)

Public API:
    PrerequisiteChecker: Main class for checking prerequisites
    safe_subprocess_call: Safe wrapper for all subprocess operations
    Platform: Enum of supported platforms
"""

import platform
import shutil
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple

# No external dependencies - only stdlib

class PrerequisiteChecker:
    """Check prerequisites using only standard library."""

    def check_tool(self, tool: str) -> bool:
        """Check if tool is available using stdlib shutil.which()"""
        return shutil.which(tool) is not None

    def _detect_platform(self) -> str:
        """Detect platform using stdlib platform module"""
        system = platform.system()

        if system == "Darwin":
            return "macos"
        elif system == "Linux":
            # Check for WSL using /proc/version (stdlib pathlib)
            proc_version = Path("/proc/version")
            if proc_version.exists():
                if "microsoft" in proc_version.read_text().lower():
                    return "wsl"
            return "linux"
        elif system == "Windows":
            return "windows"
        else:
            return "unknown"
```

### Key Points

- **Zero external dependencies** - Only use Python stdlib
- **Document in module docstring** - Make constraint clear
- **Use stdlib alternatives** - shutil.which(), platform.system(), pathlib
- **Optional advanced features** - If needed, make them try/except imports
- **Clear **all** exports** - Define public API explicitly

### When to Use

- Core utility modules
- Modules imported early in startup
- System-level functionality (platform detection, path resolution)
- Modules that check for other dependencies

### Benefits

- No circular dependency issues
- Works immediately after Python installation
- Easy to vendor or copy between projects
- Faster import time

### Trade-offs

- May need to reimplement features available in external packages
- More verbose code without helper libraries
- Limited to stdlib capabilities

### Related Patterns

- Enables Fail-Fast Prerequisite Checking (no bootstrap problem)
- Supports Bricks & Studs modular design
- Follows Zero-BS Implementation (all code works)

### Real Impact

From PR #457: Prerequisites module has zero dependencies, preventing circular import issues when checking for tools needed by other parts of the system.

## Pattern: Bricks & Studs Module Design with Clear Public API

### Challenge

Modules become tightly coupled, making it hard to regenerate or replace them. Internal implementation details leak into public usage.

### Solution

Design modules as self-contained "bricks" with clear "studs" (public API) defined via **all**.

```python
"""Prerequisite checking and installation guidance.

This module provides comprehensive prerequisite checking for all required tools.

Philosophy:
- Check prerequisites early and fail fast with helpful guidance
- Provide platform-specific installation commands
- Never auto-install (user control and security)
- Standard library only (no dependencies)

Public API (the "studs" that other modules connect to):
    PrerequisiteChecker: Main class for checking prerequisites
    safe_subprocess_call: Safe wrapper for all subprocess operations
    Platform: Enum of supported platforms
    PrerequisiteResult: Results of prerequisite checking
    ToolCheckResult: Results of individual tool checking
"""

# ... implementation ...

# Define public API explicitly
__all__ = [
    "Platform",
    "ToolCheckResult",
    "PrerequisiteResult",
    "PrerequisiteChecker",
    "safe_subprocess_call",
    "check_prerequisites",
]
```

### Module Structure

```
src/amplihack/utils/
└── prerequisites.py          # Self-contained module (428 lines)
    ├── Module docstring      # Philosophy and public API
    ├── Platform enum         # Platform types
    ├── ToolCheckResult      # Individual tool results
    ├── PrerequisiteResult   # Overall results
    ├── safe_subprocess_call # Safe subprocess wrapper
    ├── PrerequisiteChecker  # Main class
    └── __all__              # Explicit public API

tests/
├── test_prerequisites.py              # 35 unit tests
├── test_subprocess_error_handling.py  # 22 error handling tests
└── test_prerequisite_integration.py   # 13 integration tests
```

### Key Points

- **Single file module** - One file, one responsibility
- **Module docstring documents philosophy** - Explain design decisions
- **Public API in docstring** - List all public exports
- \***\*all** defines studs\*\* - Explicit public interface
- **Standard library only** - No external dependencies (when possible)
- **Comprehensive tests** - Test the public API contract

### When to Use

- Any utility module
- Modules that might be regenerated by AI
- Shared functionality used across codebase
- System-level utilities

### Benefits

- Clear contract for consumers
- Easy to regenerate from specification
- No accidental tight coupling
- Simple to replace or refactor

### Trade-offs

- May have some internal code duplication
- Resists sharing internal helpers
- Larger single files

### Related Patterns

- Enables Module Regeneration Structure
- Follows Zero-BS Implementation
- Works with Standard Library Only pattern

### Real Impact

From PR #457: Prerequisites module can be used by any part of the system without worrying about internal implementation details. Clear **all** makes public API obvious.

## Pattern: API Validation Before Implementation

### Challenge

Amplihack agents frequently call invalid APIs during implementation, causing immediate tool failures and wasted development time. Common issues include:

- Invalid model names (`claude-3-5-sonnet-20241022` with wrong separators instead of `claude-3-sonnet-20241022`)
- Non-existent imports (`from eval_recipes.claim_verification import verify_claims` where module doesn't exist)
- Wrong parameter types (passing string `"1024"` instead of integer `1024` for `max_tokens`)
- Missing required parameters (forgetting required `messages` array in API calls)
- Unhandled error conditions (no retry logic for rate limits)

These failures cause:

- 20-30 minute debug cycles after implementation already started
- Lost test execution time
- Frustration for users seeing tool crash with cryptic errors
- Preventable failures that could be caught in design phase

**Root Cause**: No explicit guidance on validating external APIs before writing code. Agents make assumptions about API structure without verification.

**Cost Comparison**:

- Validation in design phase: 5-15 minutes to verify (depending on API complexity), catches error immediately
- Debug after implementation: 20-30 minutes to identify, debug, rewrite, test again
- Prevention value: 3-6x time savings when done upfront

### Solution

Implement systematic API validation **before implementation begins**, covering four critical categories:

1. **Model/LLM API Validation** - Verify model names, parameters, endpoints (5-7 minutes)
2. **Import/Library Validation** - Verify imports exist and have correct signatures (5-8 minutes)
3. **Service/Configuration Validation** - Verify endpoints, credentials, schemas (7-10 minutes)
4. **Error Handling Validation** - Verify all failure paths are handled (3-5 minutes)

**Validation Approach**:

The pattern requires builders to complete a validation checklist for each external API call **before writing any implementation code**. Validation uses evidence from official documentation, working examples, and test verification rather than assumptions.

**Key Principle**: Catch errors in design phase (2 min fix), not implementation phase (20 min debug cycle).

---

## Category 1: Model/LLM API Validation

### What Needs Validation

- Model name format and existence
- Parameter names, types, and requirements
- API endpoint version and path
- Authentication/credential format
- Rate limiting assumptions

### Validation Checklist

**Step 1: Verify Model Name Format**

```
□ Check official Anthropic documentation for valid model names
□ List all valid formats (e.g., claude-3-{family}-{version})
□ Verify model name spelling character-by-character
□ Confirm model is publicly available (not alpha-only)
□ Document model version date for tracking
□ Check model hasn't been sunset/deprecated

Examples of VALID models:
  ✓ claude-3-opus-20240229
  ✓ claude-3-sonnet-20241022
  ✓ claude-3-haiku-20240307

Examples of INVALID models:
  ✗ claude-3-5-sonnet-20241022 (extra "-5", wrong separators)
  ✗ claude-4-ultra (doesn't exist)
  ✗ gpt-4 (wrong provider)
```

**Step 2: Validate Model Parameters**

```
□ Get complete parameter list from API documentation
□ For each parameter being used:
  □ Verify parameter name matches exactly
  □ Check parameter type (int, string, list, dict, etc.)
  □ Verify parameter is required or optional
  □ Check if parameter has default value
  □ Verify parameter constraints (ranges, enum values, etc.)

Example: max_tokens parameter
  - Required: No (optional)
  - Type: integer
  - Constraint: Must be > 0
  - Default: Determined by model
  - INVALID: max_tokens="1024" (string, should be int)
  - VALID: max_tokens=1024 (integer)
```

**Step 3: Verify API Endpoint**

```
□ Confirm endpoint path from documentation
□ Check API version (v1, v2, etc.)
□ Verify authentication method
□ Confirm base URL is correct
□ Check for regional endpoints if applicable

Standard Anthropic endpoints:
  - Base URL: https://api.anthropic.com
  - Messages: POST /v1/messages
  - Auth: Bearer {API_KEY}
```

**Step 4: Test Accessibility (When Possible)**

```
□ Verify API credentials are in correct format
□ Attempt minimal test request if safe
□ Check response structure matches expectations
□ Verify error response format
□ Document test results
```

### Code Example: Model Validation

```python
# BEFORE: Assumptions without verification
async def call_model(prompt: str) -> str:
    """Call Claude model - no validation."""
    client = Anthropic()
    message = await client.messages.create(
        model="claude-3-5-sonnet-20241022",  # ❌ NOT VERIFIED
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

# AFTER: Validated approach
from anthropic import Anthropic

# Step 1: Define valid models from documentation
VALID_MODELS = {
    "claude-3-opus-20240229": {
        "max_tokens": 200000,
        "context_window": 200000
    },
    "claude-3-sonnet-20241022": {
        "max_tokens": 200000,
        "context_window": 200000
    },
    "claude-3-haiku-20240307": {
        "max_tokens": 200000,
        "context_window": 200000
    }
}

async def call_model_validated(prompt: str, model: str) -> str:
    """Call Claude model with validation."""

    # Step 2: Validate model name
    if model not in VALID_MODELS:
        raise ValueError(
            f"Invalid model: {model}\n"
            f"Valid models: {list(VALID_MODELS.keys())}"
        )

    # Step 3: Validate parameters
    max_tokens = 1024
    model_config = VALID_MODELS[model]

    if not isinstance(max_tokens, int):
        raise TypeError(f"max_tokens must be integer, got {type(max_tokens)}")

    if max_tokens > model_config["max_tokens"]:
        raise ValueError(
            f"max_tokens {max_tokens} exceeds limit "
            f"{model_config['max_tokens']} for {model}"
        )

    if max_tokens <= 0:
        raise ValueError("max_tokens must be positive integer")

    # Step 4: Make validated API call
    client = Anthropic()
    try:
        message = await client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text

    except Exception as e:
        # Error handling (see Error Handling category)
        raise RuntimeError(f"Model call failed: {e}")
```

### Real Failure Examples

**Failure 1: Wrong Model Name Separators**

```python
# Agent code (not validated)
model = "claude-3-5-sonnet-20241022"  # ❌ Has "-5" separator

# Result
Error: 404 Client Error: Not Found
Message: Model 'claude-3-5-sonnet-20241022' not found

# Validation would catch
Format check: claude-3-{family}-{version}
Actual: claude-3-5-sonnet-20241022
Issue: Extra "-5" in middle
Fix: Use claude-3-sonnet-20241022 instead
```

**Failure 2: Non-existent Model**

```python
# Agent code
model = "claude-4-ultra"  # ❌ Doesn't exist yet

# Result
Error: 404 Client Error: Not Found

# Validation would catch
Check against VALID_MODELS list
Result: Model not in list
Action: Skip this implementation or request clarification
```

**Failure 3: Wrong Parameter Type**

```python
# Agent code
response = client.messages.create(
    model="claude-3-sonnet-20241022",
    max_tokens="1024",  # ❌ String instead of int
    messages=[...]
)

# Result
Error: ValueError: max_tokens must be integer

# Validation would catch
Parameter type check: max_tokens should be int
Actual: "1024" (str)
Fix: Use 1024 not "1024"
```

---

## Category 2: Import/Library Validation

### What Needs Validation

- Import path exists in the package
- Function/class is exported (in `__all__` or publicly available)
- Function signature matches expected usage
- Version compatibility with installed package
- Package is actively maintained

### Validation Checklist

**Step 1: Verify Package Exists**

```
□ Check package name on PyPI (https://pypi.org)
□ Verify package is actively maintained
□ Check installation status:
  $ pip show {package_name}
□ Verify current version number
□ Check for known security issues
□ Review package documentation
```

**Step 2: Verify Import Path**

```
□ Get correct import from official documentation
□ Try import in Python interpreter first:
  $ python -c "from {module} import {name}"
□ Check if module exports via __all__
□ Verify import succeeds without errors
□ Document the correct import statement
□ Check for any deprecation warnings
```

**Step 3: Verify Function/Class Contract**

```
□ Get function signature from official docs
□ Note all required parameters
□ Note all optional parameters with defaults
□ Check return type documentation
□ List exceptions that can be raised
□ Find working examples in documentation
□ Compare your planned usage to examples
```

**Step 4: Check Version Compatibility**

```
□ Identify minimum required package version
□ Check for maximum version constraints (breaking changes in newer versions)
□ Check current installed version
□ Verify function exists in minimum version
□ Check release notes for breaking changes between min and current
□ Review major version upgrades for API changes
□ Test with minimum version if critical
□ Document version assumptions and constraints in code
```

**Step 5: Verify Usage is Correct**

```
□ Find working code example in package docs
□ Compare your usage to documentation
□ Test import in minimal script
□ Verify parameter names match exactly
□ Check for any special initialization needed
```

### Code Example: Import Validation

```python
# BEFORE: Assumptions without verification
from eval_recipes.claim_verification import verify_claims  # ❌ NOT VERIFIED

def verify_text_claims(text: str):
    """Verify claims in text."""
    result = verify_claims(text)
    return result

# AFTER: Validated approach
import importlib.util
import inspect
from typing import Optional

def validate_claims_module() -> bool:
    """Validate that claims module is available and correct."""

    # Step 1: Verify package exists
    try:
        import eval_recipes
        print(f"Package found: eval_recipes")
    except ImportError as e:
        print(f"Package not found: {e}")
        print("Install with: pip install eval-recipes")
        return False

    # Step 2: Verify module path exists
    try:
        spec = importlib.util.find_spec("eval_recipes.claim_verification")
        if spec is None:
            print("Module not found: eval_recipes.claim_verification")
            return False
    except ImportError as e:
        print(f"Module not found: {e}")
        return False

    # Step 3: Try import and verify function
    try:
        from eval_recipes.claim_verification import verify_claims
        print("Import successful")
    except ImportError as e:
        print(f"Import failed: {e}")
        return False

    # Step 4: Verify function signature
    try:
        sig = inspect.signature(verify_claims)
        params = list(sig.parameters.keys())
        print(f"Function signature: verify_claims{sig}")

        # Check expected parameters
        if 'text' not in params and 'input' not in params:
            print(f"Warning: Expected 'text' or 'input' parameter")
            print(f"Actual parameters: {params}")
            return False

    except Exception as e:
        print(f"Cannot inspect function: {e}")
        return False

    # Step 5: Test basic usage
    try:
        test_result = verify_claims("Test claim")
        print(f"Basic test successful: {type(test_result)}")
    except Exception as e:
        print(f"Test call failed: {e}")
        return False

    return True

# Usage
if validate_claims_module():
    from eval_recipes.claim_verification import verify_claims
    result = verify_claims("Some text with claims")
else:
    print("Validation failed - cannot use this module")
```

### Real Failure Examples

**Failure 1: Module Doesn't Exist**

```python
# Agent code
from eval_recipes.claim_verification import verify_claims  # ❌ NOT IN PACKAGE

# Result
Error: ModuleNotFoundError: No module named 'eval_recipes.claim_verification'

# Validation would catch
$ python -c "from eval_recipes.claim_verification import verify_claims"
ModuleNotFoundError
Action: Check package structure, find alternative or request clarification
```

**Failure 2: Function Doesn't Exist**

```python
# Agent code
from anthropic import complete_text  # ❌ FUNCTION DOESN'T EXIST

# Result
Error: ImportError: cannot import name 'complete_text'

# Validation would catch
Check docs for available functions
Correct: from anthropic import Anthropic
Fix: Use Anthropic client instead of non-existent function
```

**Failure 3: Wrong Import Path**

```python
# Agent code (wrong)
from anthropic.client import Anthropic

# Correct
from anthropic import Anthropic

# Validation would catch
Try both paths in interpreter
Only correct one succeeds
Use successful import
```

**Failure 4: Signature Mismatch**

```python
# Documentation shows
def process(data, version=1):  # version parameter exists

# Agent code
result = process(my_data)  # version parameter not provided
# This works - version has default

# Agent code (assuming old signature)
result = process(my_data, extra_param=True)  # parameter doesn't exist
# This fails - extra_param not recognized

# Validation would catch
Inspect signature: process(data, version=1)
Check all your parameters match exactly
```

**Failure 5: Version Incompatibility**

```python
# Old version (1.0)
from anthropic import complete_text

# New version (2.0) - BREAKING CHANGE
from anthropic import Anthropic
client = Anthropic()
message = client.messages.create(...)

# Validation would catch
Check installed version: pip show anthropic
Check if function exists in this version
Review release notes for breaking changes
```

---

## Category 3: Service/Configuration Validation

### What Needs Validation

- External service endpoint URLs are valid
- Authentication credentials are properly formatted
- Configuration schema matches service requirements
- Response format matches expectations
- Rate limits and quotas are understood

### Validation Checklist

**Step 1: Verify Service Availability**

```
□ Check official service documentation
□ Verify endpoint URL is correct and not deprecated
□ Confirm service is available in your region
□ Check for known outages or maintenance windows
□ Verify HTTPS certificate is valid
□ Test connectivity if safe to do
```

**Step 2: Validate Configuration Schema**

```
□ List all required configuration fields
□ Define type for each field (string, int, bool, etc.)
□ Mark as required or optional
□ Document default values if optional
□ Document any constraints (ranges, patterns, enums)
□ Create schema or dataclass representation
```

**Step 3: Verify Credentials Format**

```
□ Check credential requirements (API key, token, password)
□ Verify format matches (length, characters, encoding)
□ Check expiration requirements
□ Verify credentials are properly escaped
□ Confirm credentials won't be logged/exposed
□ Document credential acquisition
```

**Step 4: Test Endpoint Connectivity (When Safe)**

```
□ Make simple test request to verify access
□ Check response format matches documentation
□ Verify error response format
□ Check timeout settings are reasonable
□ Document any required headers
```

**Step 5: Verify Rate Limits and Quotas**

```
□ Check documented rate limits
□ Estimate request volume needed
□ Plan for rate limit handling (backoff, retry)
□ Verify quota limits for your use case
□ Document rate limit assumptions
```

### Code Example: Configuration Validation

```python
# BEFORE: Configuration without validation
import requests

config = {
    "api_url": "https://api.example.com",
    "api_key": os.getenv("API_KEY"),
    "timeout": 30
}

response = requests.get(
    config["api_url"],
    headers={"Authorization": f"Bearer {config['api_key']}"},
    timeout=config["timeout"]
)
# ❌ No validation of configuration

# AFTER: Validated configuration approach
from dataclasses import dataclass
from urllib.parse import urlparse
import os
import requests

@dataclass
class ServiceConfig:
    """External service configuration with validation."""
    api_url: str
    api_key: str
    timeout: int = 30
    max_retries: int = 3

    def validate(self) -> tuple[bool, str]:
        """Validate configuration before use.

        Returns:
            (is_valid, error_message) tuple
        """

        # Step 1: Validate URL format
        try:
            parsed = urlparse(self.api_url)
            if not parsed.scheme in ('http', 'https'):
                return False, f"Invalid URL scheme: {parsed.scheme}"
            if not parsed.netloc:
                return False, "Invalid URL: missing domain"
            if not self.api_url.startswith('https'):
                return False, "URL must use HTTPS for security"
        except Exception as e:
            return False, f"Invalid URL format: {e}"

        # Step 2: Validate API key
        if not self.api_key:
            return False, "API key is required"
        if len(self.api_key) < 10:
            return False, "API key too short"
        if ' ' in self.api_key:
            return False, "API key contains spaces"

        # Step 3: Validate timeout
        if not isinstance(self.timeout, int):
            return False, f"Timeout must be integer, got {type(self.timeout)}"
        if self.timeout <= 0 or self.timeout > 300:
            return False, f"Timeout {self.timeout} out of range (1-300)"

        # Step 4: Validate max_retries
        if not isinstance(self.max_retries, int) or self.max_retries < 0:
            return False, "max_retries must be non-negative integer"
        if self.max_retries > 5:
            return False, "max_retries should not exceed 5"

        return True, ""

    def test_connectivity(self) -> tuple[bool, str]:
        """Test that service is reachable.

        Returns:
            (is_reachable, error_message) tuple
        """
        try:
            response = requests.head(
                self.api_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=self.timeout
            )

            # Check for expected status codes
            if response.status_code in [200, 204]:
                return True, "Service reachable and authenticated"
            elif response.status_code == 401:
                return False, "Authentication failed: Invalid API key"
            elif response.status_code == 403:
                return False, "Access denied: Insufficient permissions"
            elif response.status_code >= 500:
                return False, f"Server error {response.status_code}"
            else:
                return True, f"Service responded: {response.status_code}"

        except requests.Timeout:
            return False, f"Timeout after {self.timeout}s"
        except requests.ConnectionError as e:
            return False, f"Cannot connect: {e}"
        except Exception as e:
            return False, f"Connectivity test failed: {e}"

# Usage: Validate before implementation
def setup_service() -> requests.Session:
    """Set up and validate service connection."""

    # Load configuration from environment
    config = ServiceConfig(
        api_url=os.getenv("SERVICE_URL", "https://api.example.com"),
        api_key=os.getenv("SERVICE_API_KEY"),
        timeout=int(os.getenv("SERVICE_TIMEOUT", "30"))
    )

    # Validate configuration
    is_valid, error = config.validate()
    if not is_valid:
        raise ValueError(f"Configuration invalid: {error}")

    # Test connectivity
    is_reachable, message = config.test_connectivity()
    if not is_reachable:
        raise RuntimeError(f"Cannot reach service: {message}")

    # Set up session
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {config.api_key}"
    })

    return session

# Call with validation
try:
    session = setup_service()
    response = session.get(config.api_url, timeout=config.timeout)
except ValueError as e:
    print(f"Configuration error: {e}")
except RuntimeError as e:
    print(f"Service error: {e}")
```

### Real Failure Examples

**Failure 1: Malformed URL**

```python
# Agent code
api_url = "http://api..com"  # ❌ Missing domain parts

# Validation would catch
Parse URL: api..com
Result: Invalid domain
Fix: Use correct URL like "https://api.example.com"
```

**Failure 2: Empty API Key**

```python
# Agent code
api_key = ""  # ❌ Empty string
headers = {"Authorization": f"Bearer {api_key}"}

# Validation would catch
Check: len(api_key) > 0
Result: API key empty
Fix: Provide valid API key from environment
```

**Failure 3: Unreasonable Timeout**

```python
# Agent code
timeout = 0.001  # ❌ Too short

# Result
Timeout immediately on all requests

# Validation would catch
Check: 0 < timeout <= 300
Result: timeout too short
Fix: Use reasonable timeout like 30 seconds
```

---

## Category 4: Error Handling & Recovery Validation

### What Needs Validation

- All failure points are identified
- Error conditions are caught
- Error messages are user-friendly
- Recovery strategies are planned
- Logging is adequate for debugging

### Validation Checklist

**Step 1: Identify All Failure Points**

```
□ List all external API calls
□ List all network operations
□ List all file operations
□ List all parsing operations
□ Identify invalid response scenarios
□ Identify authentication failures
□ Identify rate limiting scenarios
□ Identify timeout scenarios
```

**Step 2: Plan Error Handling Strategy**

```
□ For each failure point, decide:
  - Should we retry? (transient failures)
  - Should we fall back? (fallback options)
  - Should we fail? (unrecoverable errors)
□ Define retry logic:
  - How many retries?
  - What backoff strategy?
  - Which errors are retryable?
□ Define fallback strategies:
  - What data can we use instead?
  - How do we notify user?
```

**Step 3: Implement Clear Error Messages**

```
□ Error message is user-friendly (not technical jargon)
□ Error explains what went wrong
□ Error provides next steps
□ Error distinguishes user error vs system error
□ Error logs include technical details for debugging
□ Error doesn't expose sensitive data
□ Error message is actionable
```

**Step 4: Plan Recovery and Notifications**

```
□ Define retry logic with exponential backoff
□ Plan fallback strategies
□ Document unrecoverable scenarios
□ Plan notification to user
□ Design failure state that's clear
□ Plan logging strategy
```

**Step 5: Test Error Paths**

```
□ Test each error condition (if safe)
□ Verify error message clarity
□ Verify recovery works correctly
□ Check error logging is complete
□ Ensure error doesn't leak sensitive data
□ Verify timeout handling works
```

**Step 6: Test Error Paths Safely**

```
□ Use mocks for external API errors (avoid triggering real errors)
□ Create test stubs for error scenarios:
  - Network failures (connection refused, timeout)
  - Authentication failures (401, 403)
  - Rate limiting (429)
  - Server errors (500, 503)
□ Test retry logic with mock delays
□ Verify error messages in controlled environment
□ Test recovery strategies with simulated failures
□ Use pytest fixtures or unittest.mock for isolation
□ Document which errors can be safely tested in production vs require mocks
□ Ensure tests don't leave side effects or consume API quota
```

**Example: Safe Error Testing with Mocks**

```python
# Testing error paths safely with pytest and unittest.mock
import pytest
from unittest.mock import Mock, patch
import requests

def test_api_timeout_retry():
    """Test that timeout triggers retry logic."""
    with patch('requests.get') as mock_get:
        # Simulate timeout on first two attempts, success on third
        mock_get.side_effect = [
            requests.Timeout("Connection timeout"),
            requests.Timeout("Connection timeout"),
            Mock(status_code=200, json=lambda: {"result": "success"})
        ]

        result = call_api_safe("https://api.example.com", "test-key")

        # Verify retry happened
        assert mock_get.call_count == 3
        assert result == {"result": "success"}

def test_api_authentication_error():
    """Test that 401 raises UnretryableError without retry."""
    with patch('requests.get') as mock_get:
        mock_get.return_value = Mock(status_code=401, text="Unauthorized")

        with pytest.raises(UnretryableError, match="Authentication failed"):
            call_api_safe("https://api.example.com", "bad-key")

        # Should not retry auth errors
        assert mock_get.call_count == 1

def test_api_rate_limit_backoff():
    """Test that rate limit triggers exponential backoff."""
    with patch('requests.get') as mock_get, patch('time.sleep') as mock_sleep:
        # Simulate rate limit twice, then success
        mock_get.side_effect = [
            Mock(status_code=429, text="Rate limited"),
            Mock(status_code=429, text="Rate limited"),
            Mock(status_code=200, json=lambda: {"result": "success"})
        ]

        result = call_api_safe("https://api.example.com", "test-key")

        # Verify backoff delays: 1s, then 2s
        assert mock_sleep.call_count == 2
        assert mock_sleep.call_args_list[0][0][0] == 1.0
        assert mock_sleep.call_args_list[1][0][0] == 2.0
```

### Code Example: Error Handling

```python
# BEFORE: Insufficient error handling
def call_api(url: str, api_key: str) -> dict:
    """Call API - no error handling."""
    response = requests.get(
        url,
        headers={"Authorization": api_key}
    )
    return response.json()  # ❌ NO ERROR HANDLING

# AFTER: Comprehensive error handling
import logging
import time
from enum import Enum

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Custom exception for API errors."""
    pass

class RetryableError(APIError):
    """Error that should be retried."""
    pass

class UnretryableError(APIError):
    """Error that should not be retried."""
    pass

def call_api_safe(
    url: str,
    api_key: str,
    max_retries: int = 3,
    initial_backoff: float = 1.0
) -> dict:
    """Call API with comprehensive error handling.

    Args:
        url: API endpoint URL
        api_key: API authentication key
        max_retries: Maximum retry attempts
        initial_backoff: Initial backoff in seconds

    Returns:
        Response JSON dict

    Raises:
        ValueError: Configuration validation failed
        UnretryableError: Permanent failure (auth, not found)
        RetryableError: Temporary failure (timeout, server error)
    """

    # Step 1: Validate inputs before attempting
    if not url or not url.startswith('https://'):
        raise ValueError(f"Invalid URL: {url}")
    if not api_key:
        raise ValueError("API key required")

    logger.info(f"Calling API: {url}")

    # Step 2: Retry loop with exponential backoff
    backoff = initial_backoff
    last_error = None

    for attempt in range(max_retries):
        try:
            logger.debug(f"API call attempt {attempt + 1}/{max_retries}")

            # Make request
            response = requests.get(
                url,
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=30
            )

            # Step 3: Handle response status
            if response.status_code == 200:
                logger.info("API call successful")
                return response.json()

            # Handle specific error codes
            elif response.status_code == 401:
                error = "Authentication failed: Invalid API key"
                logger.error(error)
                raise UnretryableError(error)

            elif response.status_code == 403:
                error = "Access denied: Insufficient permissions"
                logger.error(error)
                raise UnretryableError(error)

            elif response.status_code == 404:
                error = "Endpoint not found"
                logger.error(error)
                raise UnretryableError(error)

            elif response.status_code == 429:
                # Rate limited - should retry
                error = "Rate limited by service"
                logger.warning(error)
                if attempt < max_retries - 1:
                    logger.info(f"Retrying after {backoff}s")
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                raise RetryableError(f"{error} - retries exhausted")

            elif response.status_code >= 500:
                # Server error - should retry
                error = f"Server error: {response.status_code}"
                logger.warning(error)
                if attempt < max_retries - 1:
                    logger.info(f"Retrying after {backoff}s")
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                raise RetryableError(f"{error} - retries exhausted")

            else:
                error = f"Unexpected status {response.status_code}"
                logger.error(error)
                raise RetryableError(error)

        except requests.Timeout as e:
            last_error = f"Request timeout: {e}"
            logger.warning(last_error)
            if attempt < max_retries - 1:
                logger.info(f"Retrying after {backoff}s")
                time.sleep(backoff)
                backoff *= 2
                continue
            raise RetryableError(f"Timeout after retries: {last_error}")

        except requests.ConnectionError as e:
            last_error = f"Connection failed: {e}"
            logger.warning(last_error)
            if attempt < max_retries - 1:
                logger.info(f"Retrying after {backoff}s")
                time.sleep(backoff)
                backoff *= 2
                continue
            raise RetryableError(f"Connection error after retries: {last_error}")

        except requests.RequestException as e:
            # Unexpected request error
            error = f"Request error: {e}"
            logger.error(error)
            raise UnretryableError(error)

        except ValueError as e:
            # JSON parse error
            error = f"Invalid response format: {e}"
            logger.error(error)
            raise UnretryableError(error)

    # Should not reach here, but just in case
    error = f"All retries exhausted: {last_error}"
    logger.error(error)
    raise RetryableError(error)
```

### Real Failure Examples

**Failure 1: No Error Handling**

```python
# Agent code
response = requests.get(url)
data = response.json()  # ❌ Crashes if network fails

# Validation would catch
Identify failure points: network request, JSON parse
Plan error handling: catch exceptions, retry, log
Add try/except blocks
```

**Failure 2: Cryptic Error Messages**

```python
# Agent code
try:
    response = requests.get(url)
except Exception as e:
    print("Error")  # ❌ User doesn't know what happened

# Validation would catch
Error message should explain:
- What failed (network request, auth, etc)
- Why it failed (timeout, 404, etc)
- What to do next (retry, check credentials, etc)
```

**Failure 3: No Retry Logic**

```python
# Agent code
response = requests.get(url, timeout=0.1)  # ❌ Very short timeout, no retry
# Will timeout frequently on slow connections

# Validation would catch
Design retry strategy:
- Timeout is too short
- Add exponential backoff
- Retry up to 3 times
```

---

## Implementation Guide

### How to Apply This Pattern

**Before Writing Implementation Code**:

1. **Identify External APIs**: List all external services, models, or imports
2. **Categorize**: Place each in one of 4 categories (Model/Import/Service/Error)
3. **Complete Checklist**: For each API, complete the relevant validation checklist
4. **Gather Evidence**: Document findings from official documentation
5. **Implement Validation**: Include validation code in implementation (not just comments)
6. **Plan Errors**: Design error handling before writing code
7. **Proceed to Code**: Only after validation is complete and documented

### When Builder Applies This

- **During Design Phase**: Before any code is written
- **When Choosing Libraries**: Before committing to import
- **When Selecting Models**: Before API call is made
- **When Planning Integration**: Before service connection code

---

## Integration with Workflow

This pattern integrates into the DEFAULT_WORKFLOW.md at **Step 3: Architecture & Design** and **Step 4: API Design**, before any code is written in Step 5 (Implementation).

### Workflow Integration Points

**Step 3: Architecture & Design**

- Architect identifies which external APIs will be used
- Documents assumptions about API structure and behavior
- **TRIGGERS API VALIDATION**: Before proceeding to implementation

**Step 4: API Design**

- API designer defines contracts for external integrations
- **APPLIES THIS PATTERN**: Validates all external API assumptions
- Documents validation evidence in design specs

**Step 5: Implementation** (Builder Phase)

- Builder receives validated API contracts from architect/designer
- References validation evidence during implementation
- Does NOT make new API assumptions without validation

**Step 7: Code Review**

- Reviewer verifies validation was performed
- Checks that validation evidence is documented
- Ensures error handling matches design

### Should Validation Be a Distinct Workflow Step?

**Recommendation**: NO - Validation should be embedded within existing steps rather than a separate step.

**Rationale**:

- Validation is a quality check, not a deliverable
- Adds cognitive overhead if treated as separate step
- Naturally fits within design and review phases
- Keeps workflow focused on deliverables (specs, code, tests)

**How to Apply**:

- **Within Step 3/4**: Architects/designers validate APIs during design
- **Within Step 5**: Builders reference validation evidence
- **Within Step 7**: Reviewers verify validation occurred

### Builder Agent: Apply During Implementation

Builders should reference this pattern when:

- Choosing which models to use
- Deciding which libraries to import
- Calling external services
- Designing error handling

**When Builder Invokes This Pattern**:

1. **During Step 4 (API Design)**: If builder is also doing API design
   - Before committing to any external API
   - Document validation evidence in design specs

2. **During Step 5 (Implementation)**: If validation wasn't done in design
   - Stop implementation immediately
   - Complete validation before continuing
   - Document findings for reviewer

3. **Never Skip**: Even if time-pressured
   - 5-15 minute validation saves 20-30 minutes later
   - Prevents complete tool failure
   - Catches issues before CI/CD

**Builder Checklist**:

```
Before writing code that calls external APIs:
□ Category identified (Model/Import/Service/Error)
□ Validation checklist for this category completed
□ All checklist items verified (documentation, examples)
□ Evidence gathered (docs screenshot, working example)
□ Validation code included (not assumed)
□ Error handling designed (not added later)
```

### Reviewer Agent: Verify Compliance

Reviewers should check:

- Does code validate APIs before use?
- Are assumptions documented?
- Is error handling comprehensive?
- Are error messages user-friendly?
- Was checklist completed before implementation?

**When Reviewer Applies This Pattern**:

1. **During Step 7 (Code Review)**: Always check for validation
   - Verify validation evidence exists in commit/PR
   - Check that API usage matches documentation
   - Ensure error handling covers identified failure points

2. **If Validation Missing**: Request validation before approval
   - Builder must complete validation checklist
   - Evidence must be documented
   - May require architecture review

**Reviewer Checklist**:

```
For each external API call:
□ Validation code present (not just assumptions)
□ Error handling implemented (try/catch, retry)
□ Error messages are user-friendly
□ API assumptions documented in comments
□ Evidence from documentation referenced

If missing:
→ Request validation evidence
→ Ask for error handling justification
→ Require documentation of assumptions
```

### Tester Agent: Verify Error Handling

**When Tester Applies This Pattern**:

1. **During Step 8 (Testing)**: Verify error paths work correctly
   - Check that all identified error scenarios have tests
   - Verify mock-based testing for unsafe error conditions
   - Ensure error messages are clear and actionable

2. **Test Validation Coverage**:
   - Tests should cover each validation checklist item
   - Mock testing for external API failures
   - Integration tests verify happy path works

**Tester Checklist**:

```
For each external API in code:
□ Tests verify model/API exists and works
□ Tests cover authentication failure scenarios (mocked)
□ Tests cover rate limiting and retry logic (mocked)
□ Tests cover timeout and network errors (mocked)
□ Tests verify error messages are user-friendly
□ Integration tests verify real API calls (if safe)
```

---

## When to Use This Pattern

### Always Apply When

- Calling LLM models (Claude, GPT, etc.)
- Importing from external packages
- Calling REST APIs or services
- Using external tools or CLIs
- Accepting user configuration

### Optional When

- Using internal functions (same module)
- Using standard library functions
- Type-checked code (verification by type system)
- Already-tested utility functions
- Simple string/math operations

### Key Points

- **Always validate external APIs** - The 5-10 minute investment saves 20-30 minutes later
- **Catch errors in design phase** - Before implementation even starts
- **Use evidence** - Always verify with documentation, never assume
- **Plan error handling** - Design recovery before code
- **Be comprehensive** - All 4 categories deserve equal scrutiny
- **Document assumptions** - Make them clear in code comments

### Real Impact

**Success Story**:

- Agent validates model name format
- Checks documentation: `claude-3-sonnet-20241022` ✓ valid
- Writes correct code first try
- No debug cycle needed
- Tool works immediately

**Failure Averted**:

- Agent would have used: `claude-3-5-sonnet-20241022` (wrong)
- Would fail with 404 error
- 20-30 minute debug cycle
- **Prevention time saved**: 25 minutes

---

## Related Patterns

- **Zero-BS Implementation** - All code must work, no stubs or assumptions
- **Ruthless Simplicity** - Validation approach is straightforward
- **Decision-Making Framework** - Always verify assumptions before proceeding
- **Safe Subprocess Wrapper** - Handles external tool calls with error recovery

---

## Remember

These validation steps take 5-10 minutes. Skipping them costs 20-30 minutes in debugging later. The pattern is not meant to be bureaucratic - it's meant to save massive amounts of time by catching preventable errors before implementation starts.

When you see an API call being planned, before any code is written:

1. Ask: "Is this API verified?"
2. Check: "Where's the evidence?"
3. Verify: "Against official documentation?"
4. Plan: "What errors might happen?"

That's the pattern. Use it ruthlessly.

## Remember

These patterns represent hard-won knowledge from real development challenges. When facing similar problems:

1. **Check this document first** - Don't reinvent solutions
2. **Update when you learn something new** - Keep patterns current
3. **Include context** - Explain why, not just how
4. **Show working code** - Examples should be copy-pasteable
5. **Document the gotchas** - Save others from the same pain
