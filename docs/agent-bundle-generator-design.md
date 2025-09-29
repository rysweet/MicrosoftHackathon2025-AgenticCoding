# Agent Bundle Generator - Design Document

## Architecture Overview

The Agent Bundle Generator follows a pipeline architecture with clear module boundaries, implementing the "bricks & studs" philosophy where each component has a single responsibility and well-defined interfaces.

```mermaid
graph TD
    A[Natural Language Input] --> B[Prompt Parser]
    B --> C[Intent Extractor]
    C --> D[Requirements Generator]
    D --> E[Agent Generator]
    E --> F[Bundle Builder]
    F --> G[Package Manager]
    G --> H[Distribution System]
    H --> I[Executable Bundle]

    J[Template Library] --> E
    K[Base Amplihack] --> F
    L[Configuration] --> F
```

## Module Specifications

### 1. Prompt Parser Module

**Responsibility:** Parse natural language input into structured data

**Interface (Stud):**

```python
class PromptParser:
    def parse(self, prompt: str) -> ParsedPrompt:
        """Parse natural language prompt into structured format."""
        pass
```

**Internal Structure (Brick):**

- Tokenization engine
- Entity extraction
- Keyword identification
- Context analysis

**Dependencies:** None (self-contained)

### 2. Intent Extractor Module

**Responsibility:** Extract actionable intent from parsed prompts

**Interface (Stud):**

```python
class IntentExtractor:
    def extract(self, parsed_prompt: ParsedPrompt) -> Intent:
        """Extract intent and requirements from parsed prompt."""
        pass
```

**Internal Structure (Brick):**

- Pattern matching engine
- Intent classification
- Requirement extraction
- Ambiguity detection

**Dependencies:** Prompt Parser output

### 3. Agent Generator Module

**Responsibility:** Generate agent definitions from requirements

**Interface (Stud):**

```python
class AgentGenerator:
    def generate(self, intent: Intent) -> List[AgentDefinition]:
        """Generate agent definitions based on intent."""
        pass
```

**Internal Structure (Brick):**

- Template engine
- Agent customization
- Prompt generation
- Workflow creation

**Dependencies:** Template Library, Intent

### 4. Bundle Builder Module

**Responsibility:** Package complete agent bundle

**Interface (Stud):**

```python
class BundleBuilder:
    def build(self, agents: List[AgentDefinition]) -> Bundle:
        """Build complete agent bundle with all dependencies."""
        pass
```

**Internal Structure (Brick):**

- File system operations
- Dependency resolution
- Configuration management
- Test generation

**Dependencies:** Base Amplihack, Agent definitions

### 5. Package Manager Module

**Responsibility:** Create uvx-compatible packages

**Interface (Stud):**

```python
class PackageManager:
    def package(self, bundle: Bundle) -> Package:
        """Create uvx-compatible package from bundle."""
        pass
```

**Internal Structure (Brick):**

- pyproject.toml generation
- Entry point creation
- Dependency specification
- Metadata management

**Dependencies:** Bundle

### 6. Distribution System Module

**Responsibility:** Publish bundles for consumption

**Interface (Stud):**

```python
class DistributionSystem:
    def distribute(self, package: Package, target: str) -> URL:
        """Distribute package to specified target."""
        pass
```

**Internal Structure (Brick):**

- GitHub repository creation
- Git operations
- Release management
- URL generation

**Dependencies:** Package, GitHub API

## Data Flow Architecture

### Input Processing Flow

```
User Input → Validation → Parsing → Intent Extraction → Requirement Generation
```

### Generation Flow

```
Requirements → Template Selection → Agent Creation → Bundle Assembly → Packaging
```

### Distribution Flow

```
Package → Repository Creation → Upload → URL Generation → User Access
```

## Component Interactions

### Synchronous Interactions

1. **Prompt Parser → Intent Extractor**
   - Direct method calls
   - Structured data passing
   - Immediate response

2. **Agent Generator → Bundle Builder**
   - File-based communication
   - Agent definition transfer
   - Configuration sharing

### Asynchronous Interactions

1. **Distribution System → GitHub**
   - API calls with retries
   - Progress callbacks
   - Error handling

2. **Package Manager → File System**
   - Batch operations
   - Progress reporting
   - Concurrent processing

## Key Design Decisions

### Decision 1: File-Based Agent Definitions

**Choice:** Keep agents as markdown files rather than code

**Rationale:**

- Maintains amplihack's existing pattern
- Human-readable and editable
- Version control friendly
- Simple to generate and validate

**Trade-offs:**

- (+) Simplicity and transparency
- (+) Easy debugging and modification
- (-) Runtime parsing overhead
- (-) Limited type safety

### Decision 2: Template-Based Generation

**Choice:** Use templates with variable substitution

**Rationale:**

- Predictable output
- Easier testing
- Maintainable patterns
- Consistent quality

**Trade-offs:**

- (+) Reliability and consistency
- (+) Easy to extend
- (-) Less flexibility
- (-) May need many templates

### Decision 3: GitHub as Primary Distribution

**Choice:** Use GitHub repositories for bundle hosting

**Rationale:**

- Existing uvx integration
- Version control built-in
- Free hosting
- Familiar to developers

**Trade-offs:**

- (+) Zero infrastructure cost
- (+) Built-in versioning
- (-) GitHub dependency
- (-) Rate limits

### Decision 4: Minimal Runtime Dependencies

**Choice:** Bundle all dependencies at build time

**Rationale:**

- True zero-install experience
- Predictable execution
- Offline capability
- Version consistency

**Trade-offs:**

- (+) Reliability
- (+) Performance
- (-) Larger bundle size
- (-) Update complexity

## API Specifications

### CLI Interface

```bash
# Generate bundle from prompt
amplihack bundle generate "description" [options]
  --output PATH          Output directory
  --template TEMPLATE    Base template to use
  --repo REPO           Target GitHub repository
  --private             Create private repository

# Deploy bundle
amplihack bundle deploy BUNDLE_ID [options]
  --target PATH         Installation directory
  --force              Overwrite existing

# List available bundles
amplihack bundle list [options]
  --templates          Show templates only
  --local             Show local bundles
```

### REST API Interface

```yaml
# Generate bundle
POST /api/v1/bundles/generate
Content-Type: application/json
{
  "prompt": "string",
  "template": "string (optional)",
  "options": {}
}

# Get bundle status
GET /api/v1/bundles/{bundle_id}

# Deploy bundle
POST /api/v1/bundles/{bundle_id}/deploy
{
  "target": "github|local|package",
  "options": {}
}
```

### Python API Interface

```python
from amplihack.bundle_generator import BundleGenerator

# Create generator
generator = BundleGenerator()

# Generate bundle
bundle = generator.generate(
    prompt="create an agent for code review",
    template="base",
    output_dir="./my-bundle"
)

# Deploy bundle
url = bundle.deploy(target="github", repo="user/my-bundle")
```

## Configuration Management

### Bundle Configuration (bundle.yaml)

```yaml
name: security-amplihack
version: 1.0.0
base: amplihack
description: Security-focused agent bundle

agents:
  - name: security-scanner
    source: agents/security-scanner.md
    config:
      tools: [semgrep, bandit]

  - name: vulnerability-reporter
    source: agents/vuln-reporter.md

workflows:
  - name: security-audit
    steps:
      - agent: security-scanner
      - agent: vulnerability-reporter

dependencies:
  python: ">=3.9"
  packages:
    - semgrep
    - bandit

metadata:
  author: "Bundle Generator"
  license: "MIT"
  repository: "github.com/user/security-amplihack"
```

### Generator Configuration (.amplihack-bundle.yaml)

```yaml
generator:
  version: 1.0.0
  defaults:
    template: base
    output: ./bundles

templates:
  search_paths:
    - ~/.amplihack/templates
    - ./templates

github:
  organization: myorg
  default_visibility: public

uvx:
  python_version: "3.9"
  include_dev_deps: false
```

## Security Architecture

### Input Validation Pipeline

```
Input → Sanitization → Validation → AST Check → Security Scan → Approval
```

### Code Generation Security

1. **Template Validation**
   - Pre-validated templates only
   - No dynamic code execution
   - Import restrictions

2. **Generated Code Scanning**
   - AST analysis for patterns
   - Dependency vulnerability check
   - Secret detection

3. **Runtime Sandboxing**
   - Process isolation
   - Resource limits
   - Network restrictions

### Secret Management

```python
class SecretManager:
    """Manages secrets and prevents exposure."""

    def scan_bundle(self, bundle_path: Path) -> List[Issue]:
        """Scan bundle for exposed secrets."""

    def inject_runtime_secrets(self, config: dict) -> dict:
        """Inject secrets at runtime, not build time."""
```

## Testing Strategy

### Test Architecture

```
Unit Tests (60%)
├── Parser Tests
├── Generator Tests
├── Builder Tests
└── Package Tests

Integration Tests (30%)
├── End-to-end Generation
├── uvx Execution
└── GitHub Integration

E2E Tests (10%)
├── Complete Workflows
└── Real Bundle Creation
```

### Test Data Management

```python
# Fixture structure
fixtures/
├── prompts/
│   ├── valid/
│   └── invalid/
├── templates/
│   ├── base/
│   └── custom/
└── bundles/
    ├── expected/
    └── generated/
```

## Performance Optimization

### Generation Pipeline Optimization

1. **Parallel Processing**
   - Agent generation in parallel
   - File operations batching
   - Concurrent API calls

2. **Caching Strategy**
   - Template caching
   - Parsed prompt caching
   - Generated agent reuse

3. **Resource Management**
   - Memory pooling
   - File handle management
   - Connection pooling

### Target Performance Metrics

- Prompt parsing: < 100ms
- Agent generation: < 5s per agent
- Bundle building: < 10s
- Packaging: < 5s
- Distribution: < 10s
- **Total: < 30s**

## Error Handling

### Error Categories

1. **User Errors**
   - Invalid prompts
   - Missing configurations
   - Permission issues

2. **System Errors**
   - API failures
   - File system errors
   - Network issues

3. **Generation Errors**
   - Template failures
   - Validation errors
   - Packaging problems

### Error Recovery Strategy

```python
class ErrorRecovery:
    strategies = {
        'retry': RetryWithBackoff(),
        'fallback': UseFallbackTemplate(),
        'partial': GeneratePartialBundle(),
        'abort': CleanupAndAbort()
    }
```

## Monitoring and Observability

### Metrics Collection

```python
metrics = {
    'generation_time': Histogram(),
    'success_rate': Counter(),
    'bundle_size': Gauge(),
    'api_calls': Counter(),
    'errors': Counter()
}
```

### Logging Strategy

```python
# Structured logging
logger.info("bundle_generated", {
    "bundle_id": bundle.id,
    "generation_time": time_taken,
    "agent_count": len(agents),
    "size_bytes": bundle.size
})
```

## Migration and Upgrade Path

### Version Migration

```python
class BundleMigrator:
    """Migrate bundles between versions."""

    def migrate(self, bundle: Bundle, target_version: str) -> Bundle:
        """Migrate bundle to target version."""

    def check_compatibility(self, bundle: Bundle) -> List[Issue]:
        """Check bundle compatibility with current version."""
```

### Backward Compatibility

- Maintain v1 API indefinitely
- Deprecation warnings for 2 versions
- Migration tools provided
- Documentation for breaking changes

## Integration Patterns

### Claude Code SDK Integration

```python
from claude_code import Client, Message
import os
from typing import Optional

class ClaudeIntegration:
    """Integration with Claude Code SDK for agent generation."""

    def __init__(self):
        self.client = Client(
            api_key=os.environ.get("ANTHROPIC_API_KEY"),
            timeout=30,
            max_retries=3
        )
        self.rate_limiter = RateLimiter(
            max_requests_per_minute=50,
            max_tokens_per_minute=100000
        )

    async def generate_agent_content(self, intent: Intent) -> str:
        """Use Claude to generate agent content."""

        # Apply rate limiting
        await self.rate_limiter.acquire()

        try:
            response = await self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=4000,
                temperature=0.7,
                system="You are an expert at creating specialized AI agents.",
                messages=[
                    Message(
                        role="user",
                        content=self._build_generation_prompt(intent)
                    )
                ]
            )

            return response.content[0].text

        except Exception as e:
            logging.error(f"Claude API error: {e}")
            # Fallback to template-based generation
            return self._fallback_generation(intent)
```

### GitHub API Integration

```python
import github
from github import Github, GithubException

class GitHubIntegration:
    """Manage GitHub repository creation and management."""

    def __init__(self):
        self.github = Github(os.environ.get("GITHUB_TOKEN"))
        self.rate_limit_handler = GitHubRateLimitHandler()

    def create_bundle_repository(
        self,
        bundle_name: str,
        bundle_content: Bundle,
        private: bool = False
    ) -> str:
        """Create GitHub repository for bundle."""

        try:
            # Check rate limits
            if not self.rate_limit_handler.can_proceed():
                self.rate_limit_handler.wait_for_reset()

            # Create repository
            user = self.github.get_user()
            repo = user.create_repo(
                name=bundle_name,
                description=f"Agent bundle: {bundle_content.description}",
                private=private,
                auto_init=True
            )

            # Upload bundle files
            for file_path, content in bundle_content.files.items():
                self._upload_file(repo, file_path, content)

            # Create release
            repo.create_git_release(
                tag="v1.0.0",
                name=f"{bundle_name} v1.0.0",
                message="Initial bundle release"
            )

            return repo.clone_url

        except GithubException as e:
            if e.status == 403 and "rate limit" in str(e):
                # Handle rate limiting with exponential backoff
                self._handle_rate_limit(e)
                return self.create_bundle_repository(bundle_name, bundle_content, private)
            raise
```

### UVX Packaging Requirements

```python
class UvxPackager:
    """Package bundles for uvx execution."""

    def create_uvx_package(self, bundle: Bundle) -> Package:
        """Create uvx-compatible package structure."""

        # Generate pyproject.toml with uvx metadata
        pyproject = f"""
[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{bundle.name}"
version = "{bundle.version}"
description = "{bundle.description}"
requires-python = ">=3.9"
dependencies = {json.dumps(bundle.dependencies)}

[project.scripts]
{bundle.name} = "{bundle.name.replace('-', '_')}.__main__:main"

[tool.setuptools]
packages = ["src/{bundle.name.replace('-', '_')}"]
        """

        # Create __main__.py for direct uvx execution
        main_content = """
#!/usr/bin/env python3
import sys
from .cli import main

if __name__ == "__main__":
    sys.exit(main())
        """

        # Package structure
        package_dir = Path(tempfile.mkdtemp())
        src_dir = package_dir / "src" / bundle.name.replace("-", "_")
        src_dir.mkdir(parents=True)

        # Write package files
        (package_dir / "pyproject.toml").write_text(pyproject)
        (src_dir / "__main__.py").write_text(main_content)

        # Copy bundle content
        self._copy_bundle_files(bundle, src_dir)

        return Package(path=package_dir, metadata={
            "name": bundle.name,
            "version": bundle.version,
            "uvx_compatible": True
        })
```

## Deployment Architecture

### Local Development

```bash
# Install development version with editable mode
pip install -e .[dev]

# Run with debug logging
AMPLIHACK_DEBUG=1 amplihack bundle generate --verbose "my prompt"

# Use local templates
amplihack bundle generate --template-dir ./my-templates "my prompt"
```

### Production Deployment

```bash
# Install from PyPI
pip install amplihack-bundle-generator

# Or via uvx for zero-install
uvx --from amplihack-bundle-generator generate "create security scanner"

# Or directly from GitHub
uvx --from git+https://github.com/amplihack/bundle-generator generate "my prompt"
```

### CI/CD Integration

```yaml
# GitHub Actions workflow for automatic bundle generation
name: Generate Bundle
on:
  issues:
    types: [opened, labeled]
  workflow_dispatch:
    inputs:
      prompt:
        description: "Bundle generation prompt"
        required: true

jobs:
  generate:
    if: contains(github.event.issue.labels.*.name, 'bundle-request') || github.event_name == 'workflow_dispatch'
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install Bundle Generator
        run: |
          pip install amplihack-bundle-generator

      - name: Generate Bundle
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          PROMPT="${{ github.event.issue.body || github.event.inputs.prompt }}"
          amplihack bundle generate \
            --output ./generated-bundle \
            --publish github \
            --repo-prefix "bundle-" \
            "$PROMPT"

      - name: Comment on Issue
        if: github.event_name == 'issues'
        uses: actions/github-script@v6
        with:
          script: |
            const bundleUrl = process.env.BUNDLE_URL;
            await github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: `✅ Bundle generated successfully!\n\nExecute with:\n\`\`\`bash\nuvx --from ${bundleUrl} run\n\`\`\``
            });
```

---

_Document Version: 2.0_
_Last Updated: 2025-01-28_
_Author: Amplihack UltraThink Workflow - Enhanced Edition_
