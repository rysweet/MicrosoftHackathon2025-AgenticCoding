# Reflection → PR Creation System Tests

Comprehensive test suite for the reflection automation system that detects patterns in development sessions and automatically creates improvement PRs.

## Test Structure

### 🧪 Unit Tests (60% of coverage)

**test_transcript_reading.py**

- Message parsing accuracy
- Transcript path handling
- Pattern detection with real data
- Large transcript performance
- Error handling and recovery

**test_priority_scoring.py**

- User frustration scoring (critical priority)
- Security pattern prioritization
- Threshold enforcement logic
- Automation worthiness determination
- Complexity estimation

**test_automation_guard.py**

- Daily PR limits enforcement
- Cooldown period protection
- Duplicate prevention
- Configuration loading
- Emergency stop mechanisms

### 🔗 Integration Tests (30% of coverage)

**test_stop_hook_automation.py**

- Reflection triggers automation
- Stop hook workflow integration
- Basic continuation priority
- Async context handling
- End-to-end automation flow

### 🛡️ Safety Tests (10% of coverage)

**test_safety_mechanisms.py**

- Rate limiting prevents spam
- Circuit breaker activation/recovery
- Quality threshold enforcement
- Resource protection limits
- Concurrent workflow management

## Mock Infrastructure

**test_mocks.py**

- MockGitHubAPI: Simulates GitHub operations
- MockGitHubCLI: Mocks `gh` CLI commands
- MockSessionData: Generates realistic test data
- MockFileSystem: File system simulation

## Running Tests

### Quick Start

```bash
# Run all tests
python tests/run_reflection_tests.py

# Run specific suite
python tests/run_reflection_tests.py unit
python tests/run_reflection_tests.py safety

# With coverage
python tests/run_reflection_tests.py --coverage

# Verbose output
python tests/run_reflection_tests.py --verbose
```

### Using pytest directly

```bash
# All tests
pytest tests/

# Specific test file
pytest tests/test_transcript_reading.py -v

# With markers
pytest -m "unit" tests/
pytest -m "safety" tests/

# Coverage report
pytest --cov=.claude.tools --cov-report=html tests/
```

## Test Categories

### Critical Path Tests ✅

- Message parsing and pattern detection
- Automation trigger logic
- Safety mechanism enforcement
- GitHub API integration

### Edge Case Tests 🔍

- Empty/malformed input handling
- Network failure simulation
- Resource exhaustion scenarios
- Concurrent access safety

### Performance Tests ⚡

- Large session handling
- Memory usage protection
- Timeout enforcement
- Rate limiting effectiveness

## Safety Validation

### Rate Limiting

- Maximum 5 automations per day
- 1-hour cooldown between triggers
- Burst protection (max 2 per 10 minutes)

### Circuit Breakers

- Workflow failure tracking
- Automatic disable after 3 consecutive failures
- Recovery after success threshold

### Quality Thresholds

- Minimum pattern severity: medium
- Minimum pattern count: 2 for automation
- Security review required for error patterns

## Mock Data Scenarios

### Simple Session

- Basic user-assistant interaction
- Minimal tool usage
- No automation triggers

### Repeated Tool Usage

- 8+ repeated bash/read operations
- Should trigger "tooling" automation
- Medium-high priority

### Error Patterns

- Multiple error indicators
- Authentication/permission failures
- Should trigger "error_handling" automation
- High priority, security review required

### User Frustration

- Frustration indicators in messages
- "doesn't work", "broken", "confused"
- Should trigger "workflow" automation
- Critical priority (highest)

### Long Sessions

- 100+ message exchanges
- Should trigger "pattern" automation
- Medium priority

## CI/CD Integration

### GitHub Actions

```yaml
- name: Run Reflection Tests
  run: |
    python tests/run_reflection_tests.py --coverage
    python tests/run_reflection_tests.py --report-format html
```

### Test Reports

- JSON reports for CI integration
- HTML reports for human review
- Coverage analysis with line-by-line details
- Performance metrics and duration tracking

## Configuration

### Environment Variables

- `CLAUDE_REFLECTION_MODE=1`: Disable reflection (prevents infinite loops)
- `GITHUB_ACTIONS=true`: Enable CI-specific behavior
- `TEST_TIMEOUT=300`: Test timeout in seconds

### Test Configuration

- `pytest.ini`: pytest configuration
- `conftest.py`: shared fixtures and setup
- `test_mocks.py`: mock infrastructure

## Best Practices

### Test Design

- Each test has single responsibility
- Clear arrange-act-assert structure
- Realistic test data scenarios
- Comprehensive error handling

### Safety First

- All automation tests use mocks
- No actual GitHub API calls
- Rate limiting always tested
- Circuit breakers validated

### Performance

- Tests complete under 5 minutes
- Memory usage monitored
- Large data handling tested
- Timeout protection enforced

## Troubleshooting

### Common Issues

**Import Errors**

```bash
# Ensure project root in Python path
export PYTHONPATH=/path/to/project:$PYTHONPATH
```

**GitHub CLI Tests Failing**

```bash
# Check if gh CLI is available (optional)
gh --version
```

**Coverage Not Working**

```bash
# Install coverage tools
pip install pytest-cov coverage
```

### Debug Mode

```bash
# Run single test with debug output
pytest tests/test_transcript_reading.py::TestTranscriptReading::test_pattern_detection_with_real_data -v -s --tb=long
```

## Metrics and Reporting

### Success Criteria

- All critical path tests pass
- Safety mechanisms validated
- 80%+ code coverage on core components
- Performance under acceptable limits

### Quality Gates

- Zero tolerance for safety mechanism failures
- All error handling paths tested
- Mock infrastructure comprehensive
- Documentation up to date

---

This test suite ensures the reflection → PR creation system is robust, safe, and reliable before deployment.
