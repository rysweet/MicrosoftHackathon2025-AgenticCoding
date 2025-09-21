# Stage 2 Reflection System

Converts session reflection insights into actionable pull requests and GitHub issues.

## Overview

The Stage 2 reflection system analyzes patterns from Stage 1 session analysis and automatically generates:

- Pull request proposals with implementation stubs
- GitHub issues for investigation tasks
- Comprehensive reflection reports
- Grouped improvements for related patterns

## Architecture

```
Session End
    ↓
Stage 1: Session Analysis (stop.py)
    - Extract metrics (tool usage, errors, duration)
    - Identify patterns and learnings
    - Save analysis JSON
    ↓
Stage 2: PR Generation (reflection_stage2.py)
    - Analyze Stage 1 output
    - Group related patterns
    - Generate PR/issue content from templates
    - Create implementation stubs
    - Generate comprehensive report
```

## Components

### 1. reflection_stage2.py

Main Stage 2 module with three key classes:

#### PatternToPRConverter

- Analyzes Stage 1 output for actionable patterns
- Groups related improvements
- Generates PR content from templates
- Creates implementation stubs for automation

#### PR Templates

Built-in templates for common patterns:

- `repeated_commands`: Automation script PRs
- `error_patterns`: Error handling improvements
- `user_frustration`: Architecture review issues
- `long_session`: Task decomposition guides
- `performance_bottleneck`: Optimization PRs
- `missing_tooling`: New tool proposals

#### ReflectionReportGenerator

- Combines Stage 1 and Stage 2 results
- Generates markdown reports
- Saves to `.claude/runtime/reports/`

### 2. Enhanced stop.py

Session stop hook with Stage 2 integration:

- Performs Stage 1 analysis
- Optionally triggers Stage 2
- Auto-triggers on significant patterns:
  - More than 5 errors
  - Session longer than 30 minutes
  - Any tool used more than 10 times

## Usage

### Command Line

```bash
# Analyze a Stage 1 file and generate proposals (dry run)
python reflection_stage2.py /path/to/stage1.json

# Generate proposals and create GitHub issues/PRs
python reflection_stage2.py /path/to/stage1.json --create-prs

# Generate comprehensive report
python reflection_stage2.py /path/to/stage1.json --report
```

### In Session Stop Hook

The stop hook automatically triggers Stage 2 when patterns warrant it:

```python
# Automatic triggers:
- Error count > 5
- Session duration > 30 minutes
- Any tool usage > 10 times
```

To force Stage 2:

```json
{
  "messages": [...],
  "enable_stage2": true,
  "create_prs": false  // Set true to actually create PRs
}
```

## Pattern Detection

### High Priority Patterns

**Repeated Commands** (>10 uses)

- Generates automation script PR
- Creates implementation stub
- Includes error handling template

**Error Patterns** (>5 errors)

- Creates investigation issue
- Proposes error handling improvements
- Includes recovery strategies

**User Frustration** (keyword detection)

- Creates architecture review issue
- Identifies pain points
- Proposes investigation plan

### Medium Priority Patterns

**Long Sessions** (>30 minutes)

- Generates task decomposition guide
- Identifies parallelization opportunities
- Creates checkpoint templates

**Performance Bottlenecks**

- Proposes optimization strategies
- Creates profiling plan
- Includes measurement criteria

## Generated Outputs

### 1. PR/Issue Proposals

Each proposal includes:

- Formatted title with context
- Detailed problem description
- Proposed solution with checklist
- Appropriate labels
- Priority classification

### 2. Implementation Stubs

For automation patterns, creates:

```python
.claude/tools/automation/auto_<tool_name>.py
- CLI interface
- Batch processing support
- Retry logic template
- Error handling structure
```

### 3. Comprehensive Report

Markdown report with:

- Session summary metrics
- Pattern analysis results
- Generated proposals list
- Created PRs/issues links
- Recommendations
- Next steps

## Configuration

### Thresholds

Edit in `reflection_stage2.py`:

```python
# Pattern detection thresholds
REPETITION_THRESHOLD = 5      # Min uses for repeated command
HIGH_REPETITION = 10          # High priority threshold
ERROR_THRESHOLD = 3            # Min errors for pattern
LONG_SESSION_MINUTES = 30      # Long session threshold
```

### Custom Templates

Add new templates in `PatternToPRConverter._init_templates()`:

```python
self.templates["new_pattern"] = {
    "title": "Template title with {variables}",
    "body": "Full PR body template",
    "labels": ["appropriate", "labels"]
}
```

## Testing

Run the test suite:

```bash
python test_reflection_stage2.py
```

Tests cover:

- Pattern analysis
- PR content generation
- Report generation
- End-to-end workflow

## Output Locations

- Stage 1 analysis: `.claude/runtime/analysis/session_*.json`
- Stage 2 results: `.claude/runtime/analysis/*_stage2.json`
- Reports: `.claude/runtime/reports/reflection_report_*.md`
- Logs: `.claude/runtime/logs/stop.log`

## Integration with CI/CD

The system can be integrated with CI/CD pipelines:

1. **Post-session hook**: Automatically analyze completed sessions
2. **Scheduled analysis**: Regular pattern review across sessions
3. **PR creation**: Auto-create improvement PRs for review
4. **Metrics tracking**: Monitor improvement implementation

## Best Practices

1. **Review before creating PRs**: Use dry-run mode first
2. **Group related patterns**: Reduces PR noise
3. **Prioritize high-impact**: Focus on high-priority patterns
4. **Track implementation**: Monitor PR completion rates
5. **Iterate on templates**: Refine based on team feedback

## Future Enhancements

Potential improvements:

- Machine learning for pattern detection
- Cross-session pattern aggregation
- Automatic PR assignment based on expertise
- Integration with project management tools
- Custom pattern definitions via configuration
