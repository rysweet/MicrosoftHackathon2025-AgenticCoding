# Claude-Trace Analysis System

A comprehensive system for analyzing claude-trace JSON logs to automatically identify improvements in code, prompts, and system fixes, then create GitHub issues for each distinct improvement.

## Features

### 🔍 **Multi-Domain Analysis**

- **Code Improvements**: Bug fixes, performance optimizations, security enhancements
- **Prompt Improvements**: Clarity, context, specificity enhancements
- **System Fixes**: Connection, memory, API reliability improvements

### 🛡️ **Security & Safety**

- Input validation with file size and entry count limits
- Path traversal protection
- Content sanitization before GitHub issue creation
- Rate limiting for API protection
- Comprehensive audit logging

### 🚫 **Deduplication Engine**

- **Content Similarity**: Advanced text similarity with technical keyword matching
- **Temporal Filtering**: Prevents duplicate issues within time windows
- **GitHub Integration**: Checks existing issues to prevent duplicates
- **Multi-layer Detection**: Conservative approach to minimize false positives

### 📋 **GitHub Integration**

- Template-based issue generation with proper formatting
- Automatic labeling based on improvement type and confidence
- Rate limiting (50 daily, 10 hourly by default)
- Comprehensive error handling and retry logic

## Architecture

The system follows a modular "bricks & studs" design with 5 core components:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   JSONL Parser  │───▶│ Pattern Extractor│───▶│ Deduplication   │
│                 │    │                  │    │    Engine       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐             │
│ Issue Generator │◀───│    Workflow      │◀────────────┘
│                 │    │  Orchestrator    │
└─────────────────┘    └──────────────────┘
```

### Component Responsibilities

1. **JSONL Parser**: Pure parsing with security validation, no side effects
2. **Pattern Extractor**: Specialized analyzers for each improvement domain
3. **Deduplication Engine**: Multi-layer duplicate prevention
4. **Issue Generator**: GitHub integration with templates and sanitization
5. **Workflow Orchestrator**: Main coordination and result compilation

## Installation

```bash
# Install in the existing amplihack system
cd /path/to/amplihack
# The system is already integrated into .claude/tools/amplihack/
```

## Configuration

### Environment Variables

```bash
# GitHub Integration
export GITHUB_TOKEN="your_github_token"
export GITHUB_REPO_OWNER="your_username"
export GITHUB_REPO_NAME="your_repo"

# Rate Limiting
export GITHUB_DAILY_LIMIT="50"
export GITHUB_HOURLY_LIMIT="10"

# Security Settings
export TRACE_MAX_FILE_SIZE_MB="100"
export TRACE_MAX_ENTRIES="10000"
export TRACE_ENABLE_SANITIZATION="true"

# Analysis Settings
export ANALYSIS_SIMILARITY_THRESHOLD="0.8"
export ANALYSIS_TEMPORAL_WINDOW="60"
export ANALYSIS_MIN_CONFIDENCE="0.5"
```

### Programmatic Configuration

```python
from claude_trace_analysis import TraceConfig

# Load from environment
config = TraceConfig.create_default()

# Override specific settings
config = TraceConfig({
    "github": {
        "token": "your_token",
        "repo_owner": "username",
        "repo_name": "repository"
    },
    "analysis": {
        "similarity_threshold": 0.85,
        "min_confidence_threshold": 0.7
    }
})

# Save configuration
config.save_to_file("trace_config.json")

# Load from file
config = TraceConfig.create_from_file("trace_config.json")
```

## Usage

### Basic Analysis

```python
from claude_trace_analysis import TraceAnalyzer

# Initialize analyzer
analyzer = TraceAnalyzer(
    github_token="your_token",
    repo_owner="username",
    repo_name="repository"
)

# Analyze single file
result = analyzer.analyze_single_file("trace.jsonl")

# Analyze multiple files
result = analyzer.analyze_trace_files([
    "trace1.jsonl",
    "trace2.jsonl",
    "trace3.jsonl"
])

# Analysis without creating issues (dry run)
result = analyzer.analyze_trace_files(
    ["trace.jsonl"],
    create_issues=False
)
```

### Result Analysis

```python
# Check analysis results
if result.success:
    print(f"Processed {result.files_processed} files")
    print(f"Found {result.patterns_identified} patterns")
    print(f"Created {result.issues_created} GitHub issues")
    print(f"Execution time: {result.execution_time_seconds:.2f}s")
else:
    print(f"Analysis failed: {result.error_message}")

# Get detailed results
details = result.detailed_results
print(f"Deduplication rate: {details['patterns']['deduplication_rate']:.2%}")
print(f"Issue creation success rate: {details['issues']['success_rate']:.2%}")

# Get component statistics
summary = analyzer.get_analysis_summary()
print(summary['component_statistics'])
```

### Integration with Existing Reflection System

```python
# In your existing reflection workflow
from claude.tools.amplihack.claude_trace_analysis import TraceAnalyzer

def analyze_claude_traces(trace_files):
    """Integrate claude-trace analysis into existing reflection system."""

    # Initialize analyzer with existing GitHub config
    analyzer = TraceAnalyzer(
        github_token=os.getenv('GITHUB_TOKEN'),
        repo_owner=os.getenv('GITHUB_REPO_OWNER'),
        repo_name=os.getenv('GITHUB_REPO_NAME')
    )

    # Run analysis
    result = analyzer.analyze_trace_files(trace_files)

    # Log results using existing logging system
    if result.success:
        log_improvement_analysis(result)
        return result.issues_created
    else:
        log_analysis_error(result.error_message)
        return 0
```

## Claude-Trace Log Format

The system expects claude-trace logs in JSONL format:

```jsonl
{"timestamp": "2024-01-01T12:00:00Z", "type": "completion", "data": {"prompt": "Fix bug", "completion": "Here's the fix", "code_before": "broken", "code_after": "fixed"}}
{"timestamp": "2024-01-01T12:01:00Z", "type": "error", "data": {"error_type": "timeout", "fix_applied": "Added retry logic", "success": true}}
```

### Supported Entry Types

- **completion**: Claude completions with improvement potential
- **error**: System errors with applied fixes
- **tool_use**: Tool usage patterns for optimization

### Pattern Detection Fields

The system looks for these fields to identify improvements:

**Code Improvements:**

- `code_before`, `code_after`: Before/after code comparison
- `fix_applied`: Description of fix applied
- `performance_gain`: Performance improvement metrics
- `security_fix`: Security vulnerability fixes

**Prompt Improvements:**

- `clarification_needed`: Indicates unclear prompts
- `improved_prompt`: Better version of prompt
- `context_missing`: Missing context indicators
- `specificity_needed`: Need for more specific prompts

**System Fixes:**

- `error_type`: Type of system error
- `resolution`: How the error was resolved
- `memory_usage_reduced`: Memory optimization results
- `api_stability_improved`: API reliability improvements

## Security Considerations

### Input Validation

- File size limits (100MB default)
- Entry count limits (10K per file default)
- Path traversal protection
- Schema validation for all entries

### Content Sanitization

All content is sanitized before creating GitHub issues:

- Removes API keys, tokens, passwords
- Redacts email addresses and internal IPs
- Replaces sensitive patterns with `[REDACTED]`

### Rate Limiting

- Daily limit: 50 GitHub issues (configurable)
- Hourly limit: 10 GitHub issues (configurable)
- Conservative error handling
- Graceful degradation when limits exceeded

## Performance

### Benchmarks

- **10K entries**: <5 seconds processing time
- **100MB files**: Handled within memory limits
- **Parallel processing**: Multiple analyzers run simultaneously
- **Memory efficient**: Streaming for large datasets

### Optimization Features

- Compiled regex patterns for performance
- Efficient similarity algorithms
- Batch processing capabilities
- Optional parallel execution

## Error Handling

The system uses comprehensive error handling:

```python
# All operations return structured results
result = analyzer.analyze_trace_files(files)

if not result.success:
    print(f"Error: {result.error_message}")
    print(f"Exception type: {result.detailed_results.get('exception_type')}")

    # System continues gracefully
    # Partial results may still be available
```

### Common Error Scenarios

- **File not found**: Continues with other files
- **Invalid JSON**: Skips malformed entries, continues processing
- **GitHub API errors**: Reports failure but continues analysis
- **Rate limiting**: Gracefully handles and reports limits
- **Network issues**: Conservative fallback behavior

## Testing

The system includes comprehensive test coverage:

```bash
# Run unit tests
python -m pytest claude_trace_analysis/tests/unit/ -v

# Run integration tests
python -m pytest claude_trace_analysis/tests/integration/ -v

# Run end-to-end tests
python -m pytest claude_trace_analysis/tests/e2e/ -v
```

### Test Categories

- **Unit Tests (60%)**: Individual component testing
- **Integration Tests (30%)**: Component interaction testing
- **End-to-End Tests (10%)**: Full workflow testing

## Contributing

### Adding New Pattern Types

1. **Extend Pattern Extractor**:

```python
class NewPatternAnalyzer(BaseAnalyzer):
    def analyze(self, entries):
        # Implementation
        return patterns
```

2. **Add Template**:

```python
IssueTemplate.register_template('new_pattern_type', template)
```

3. **Update Configuration**:

```python
# Add to AnalysisConfig
enable_new_pattern_analysis: bool = True
```

### Code Style

- Follow existing patterns and architecture
- Maintain "bricks & studs" modular design
- Include comprehensive error handling
- Add security considerations for new features
- Write tests following TDD approach

## Monitoring & Observability

### Built-in Metrics

- Pattern identification rates by type
- Deduplication effectiveness
- GitHub issue creation success rates
- Processing performance metrics
- Error rates and types

### Integration with Existing Systems

The system integrates with the existing amplihack reflection system:

```python
# Automatic integration with existing logs
from claude.tools.amplihack.reflection import reflection_analysis

# Claude-trace analysis runs as part of reflection
improvement_count = reflection_analysis.run_claude_trace_analysis()
```

## Troubleshooting

### Common Issues

**No patterns detected:**

- Check log format matches expected schema
- Verify improvement indicators are present
- Check confidence thresholds in configuration

**GitHub integration failing:**

- Verify token permissions (issues:write required)
- Check repository owner/name configuration
- Validate rate limits haven't been exceeded

**Performance issues:**

- Reduce batch size for large files
- Check file size limits
- Monitor memory usage during processing

**Duplicate issues being created:**

- Verify deduplication engine configuration
- Check temporal window settings
- Review existing issue checking

### Debug Mode

```python
# Enable verbose logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Get detailed component reports
summary = analyzer.get_analysis_summary()
print(summary['component_statistics'])
```

## License

This system is part of the amplihack project and follows the same licensing terms.

---

_This system was designed following the amplihack philosophy of ruthless simplicity, modular design, and zero-BS implementation._
