# Claude-Trace Log Analysis System - Test Documentation

This document describes the comprehensive test suite for the Claude-trace log analysis system, designed using Test-Driven Development (TDD) principles.

## Overview

The test suite follows the testing pyramid principle:

- **60% Unit Tests**: Core functionality, individual components
- **30% Integration Tests**: Component interactions
- **10% E2E Tests**: Complete workflow validation

## Test Structure

```
tests/
├── test_claude_trace_analyzer.py      # Unit tests (60%)
├── test_claude_trace_integration.py   # Integration tests (30%)
├── test_claude_trace_e2e.py          # E2E tests (10%)
├── test_claude_trace_performance.py   # Performance & error cases
├── fixtures/
│   └── claude_trace_test_data.py      # Test data & mocking
├── conftest.py                        # Pytest configuration
└── README_CLAUDE_TRACE_TESTS.md      # This documentation
```

## Test Categories

### Unit Tests (`test_claude_trace_analyzer.py`)

**ClaudeTraceParser Tests**:

- ✅ Empty file handling
- ✅ Single/multiple JSONL entries
- ✅ Malformed JSON recovery
- ✅ File not found errors
- ✅ Large file memory efficiency
- ✅ Unicode and encoding support

**ImprovementAnalyzer Tests**:

- ✅ Code improvement pattern detection
- ✅ Error handling pattern analysis
- ✅ Workflow inefficiency identification
- ✅ Prompt optimization detection
- ✅ Empty/invalid input handling

**GitHubIssueManager Tests**:

- ✅ Issue deduplication by title/content
- ✅ Well-formatted issue creation
- ✅ Rate limiting handling
- ✅ Batch issue creation with deduplication

**Data Structure Tests**:

- ✅ AnalysisResult validation
- ✅ ImprovementPattern validation
- ✅ Confidence score bounds
- ✅ JSON serialization/deserialization

### Integration Tests (`test_claude_trace_integration.py`)

**Parser-Analyzer Integration**:

- ✅ Real trace data processing
- ✅ Pattern detection across file types
- ✅ Corrupted data handling
- ✅ Multi-pattern analysis

**Analyzer-GitHub Integration**:

- ✅ Issue creation from patterns
- ✅ Deduplication workflow
- ✅ API error handling
- ✅ Batch processing

**System Integration**:

- ✅ Multiple directory analysis
- ✅ Reflection system integration
- ✅ Concurrent analysis safety
- ✅ Performance with large datasets

### E2E Tests (`test_claude_trace_e2e.py`)

**Complete Workflow**:

- ✅ Trace discovery → analysis → issue creation
- ✅ Duplicate detection in real scenarios
- ✅ Rate limiting recovery
- ✅ No trace files handling

**Real-World Scenarios**:

- ✅ Large project performance
- ✅ CI/CD integration
- ✅ Error recovery
- ✅ Output validation

### Performance & Error Tests (`test_claude_trace_performance.py`)

**Performance Scenarios**:

- ✅ Large file processing (10K+ entries)
- ✅ Memory efficiency with streaming
- ✅ Concurrent analysis
- ✅ Pattern analysis scaling
- ✅ GitHub rate limiting

**Error Handling**:

- ✅ Malformed JSON recovery
- ✅ File system errors
- ✅ GitHub API failures
- ✅ Memory pressure
- ✅ Unicode/encoding issues
- ✅ Extreme data patterns

## Test Data & Mocking

### Realistic Test Data (`fixtures/claude_trace_test_data.py`)

**ClaudeTraceTestData**:

- Code improvement sessions
- Error handling scenarios
- Workflow inefficiencies
- Performance issues
- Testing improvements
- Malformed data patterns

**Mock Strategies**:

- GitHub API responses (success/failure/rate-limiting)
- File system operations
- Network timeouts
- Authentication errors

### Test Configuration (`conftest.py`)

**Fixtures**:

- `temp_directory`: Isolated test environment
- `sample_trace_files`: Realistic trace data
- `mock_github_success`: Successful GitHub operations
- `project_with_traces`: Multi-directory project structure

**Test Markers**:

- `@pytest.mark.unit`: Fast, isolated tests
- `@pytest.mark.integration`: Component interaction tests
- `@pytest.mark.e2e`: Full workflow tests
- `@pytest.mark.performance`: Performance tests
- `@pytest.mark.slow`: Tests that may take several seconds

## Running Tests

### Basic Usage

```bash
# Run all tests
pytest tests/

# Run by category
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m e2e           # E2E tests only

# Run specific test file
pytest tests/test_claude_trace_analyzer.py

# Run with coverage
pytest --cov=amplihack.analysis tests/
```

### Performance Testing

```bash
# Run performance tests
pytest -m performance

# Skip slow tests
pytest -m "not slow"

# Run with performance profiling
pytest --profile tests/test_claude_trace_performance.py
```

### TDD Workflow

```bash
# 1. Run failing tests (Red)
pytest tests/test_claude_trace_analyzer.py::TestClaudeTraceParser::test_parse_empty_file

# 2. Implement minimal code (Green)
# ... implement ClaudeTraceParser.parse_file() ...

# 3. Run test again (should pass)
pytest tests/test_claude_trace_analyzer.py::TestClaudeTraceParser::test_parse_empty_file

# 4. Refactor and repeat
```

## Expected Test Failures (TDD)

Since this is a TDD approach, many tests are designed to **fail initially** and guide implementation:

### Critical Components to Implement

1. **`amplihack.analysis.claude_trace_analyzer` module**:
   - `ClaudeTraceParser` class
   - `ImprovementAnalyzer` class
   - `GitHubIssueManager` class
   - `ClaudeTraceLogAnalyzer` class
   - `AnalysisResult` data class
   - `ImprovementPattern` data class

2. **Core Methods**:
   - `ClaudeTraceParser.parse_file()`
   - `ClaudeTraceParser.parse_file_lazy()`
   - `ImprovementAnalyzer.analyze_code_improvements()`
   - `ImprovementAnalyzer.analyze_error_patterns()`
   - `ImprovementAnalyzer.analyze_workflow_patterns()`
   - `GitHubIssueManager.create_issues_from_patterns()`
   - `GitHubIssueManager.is_duplicate_issue_by_pattern()`

## Test Coverage Goals

### Minimum Coverage Requirements

- **Overall**: 90%+ line coverage
- **Unit Tests**: 95%+ coverage of core logic
- **Integration**: 85%+ coverage of component interactions
- **E2E**: 80%+ coverage of complete workflows

### Critical Coverage Areas

1. **Happy Path**: All successful operations
2. **Error Cases**: All exception scenarios
3. **Edge Cases**: Boundary conditions, empty inputs
4. **Performance**: Large datasets, concurrent access
5. **Integration**: External API interactions

## Test Quality Standards

### Good Test Characteristics

- **Fast**: Unit tests < 100ms, integration < 1s
- **Isolated**: No dependencies between tests
- **Repeatable**: Consistent results
- **Self-Validating**: Clear pass/fail
- **Focused**: Single responsibility per test

### Test Patterns

```python
def test_specific_behavior():
    """Should do specific thing under specific conditions."""
    # Arrange: Set up test data
    input_data = create_test_data()

    # Act: Execute the operation
    result = system_under_test.operation(input_data)

    # Assert: Verify behavior
    assert result.expected_property == expected_value
    assert len(result.collection) == expected_count
```

## Mock Guidelines

### When to Mock

- **External APIs**: GitHub API calls
- **File System**: Large file operations
- **Network**: HTTP requests, timeouts
- **Time**: Date/time dependencies

### When NOT to Mock

- **Pure Functions**: Logic without side effects
- **Data Structures**: Internal data manipulation
- **Simple Operations**: Basic file I/O

## Continuous Integration

### CI Test Strategy

```yaml
# Example CI configuration
test_matrix:
  fast_feedback:
    - pytest -m "unit and not slow"

  comprehensive:
    - pytest -m "integration or e2e"
    - pytest --cov=amplihack.analysis

  performance:
    - pytest -m performance --timeout=300
```

## Contributing

### Adding New Tests

1. **Identify Gap**: Use coverage reports to find untested areas
2. **Write Failing Test**: Follow TDD - write test first
3. **Implement Feature**: Make test pass with minimal code
4. **Refactor**: Improve code while keeping tests green
5. **Update Documentation**: Add test to appropriate category

### Test Review Checklist

- [ ] Test has clear, descriptive name
- [ ] Test follows AAA pattern (Arrange, Act, Assert)
- [ ] Test is focused on single behavior
- [ ] Test uses appropriate mocks/fixtures
- [ ] Test handles edge cases
- [ ] Test is categorized correctly (unit/integration/e2e)

## Debugging Failed Tests

### Common Issues

1. **Import Errors**: Module not implemented yet (expected in TDD)
2. **Mock Failures**: Incorrect mock configuration
3. **Data Issues**: Test data doesn't match expectations
4. **Timing Issues**: Race conditions in concurrent tests
5. **Environment**: Missing dependencies or configuration

### Debug Commands

```bash
# Run with verbose output
pytest -v tests/test_claude_trace_analyzer.py

# Run with detailed failure info
pytest --tb=long tests/

# Run single test with debugging
pytest -s tests/test_claude_trace_analyzer.py::TestClaudeTraceParser::test_parse_empty_file

# Run with pdb on failure
pytest --pdb tests/
```

## Performance Benchmarks

### Expected Performance

| Operation        | Dataset Size | Max Time | Max Memory |
| ---------------- | ------------ | -------- | ---------- |
| Parse JSONL      | 1K entries   | 0.1s     | 10MB       |
| Parse JSONL      | 10K entries  | 1.0s     | 50MB       |
| Pattern Analysis | 1K entries   | 0.5s     | 20MB       |
| GitHub API       | 10 issues    | 5.0s     | 5MB        |
| E2E Workflow     | 5K entries   | 10.0s    | 100MB      |

### Performance Alerts

Tests will fail if performance degrades beyond acceptable thresholds:

- Parse time > 2x expected
- Memory usage > 3x expected
- GitHub operations > 10s timeout

## Security Considerations

### Test Security

- **No Real Secrets**: All GitHub tokens are mocked
- **Isolated Environment**: Tests run in temporary directories
- **Safe Data**: Test data contains no sensitive information
- **Clean Up**: Temporary files are automatically removed

### Security Tests

- Input validation for malicious JSON
- GitHub API authentication handling
- File path traversal prevention
- Memory exhaustion protection

---

This test suite provides comprehensive coverage for the Claude-trace log analysis system using TDD principles. The tests are designed to fail initially and guide implementation of a robust, well-tested system.
