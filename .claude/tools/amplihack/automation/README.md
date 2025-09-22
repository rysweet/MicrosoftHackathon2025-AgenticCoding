# Stage 2 Automation Engine

Bridges reflection insights to automated PR creation through intelligent pattern prioritization and workflow orchestration.

## Overview

The Stage 2 Automation Engine processes patterns detected during reflection analysis and automatically creates pull requests to address high-priority issues. It acts as the automation bridge between insight detection (Stage 1) and implementation (Stage 3).

## Architecture

```
Reflection Analysis (Stage 1)
         ↓
┌─────────────────────────┐
│  Stage2AutomationEngine │
├─────────────────────────┤
│  • Load insights        │
│  • Score patterns       │
│  • Check guards        │
│  • Execute workflow    │
└─────────────────────────┘
         ↓
    PR Creation (Stage 3)
```

## Components

### 1. Stage2AutomationEngine (`stage2_engine.py`)

Main orchestrator that:

- Processes reflection analysis files
- Coordinates scoring and guard checking
- Triggers improvement workflows
- Tracks automation history

```python
from .claude.tools.amplihack.automation import Stage2AutomationEngine

engine = Stage2AutomationEngine()
result = engine.process_reflection_insights(analysis_path)
```

### 2. PriorityScorer (`priority_scorer.py`)

Scores patterns based on:

- **Pattern type**: Security > User frustration > Errors > Performance
- **Severity**: Critical (2x) > High (1.5x) > Medium (1x) > Low (0.5x)
- **Frequency**: More occurrences = higher score
- **Scope**: System-wide > Module > Component > Edge case
- **Urgency indicators**: Blocking issues, critical path impacts

Score ranges:

- 150+: Critical priority (bypass cooldowns)
- 100-149: High priority
- 60-99: Medium priority
- 30-59: Low priority
- <30: No action

### 3. AutomationGuard (`automation_guard.py`)

Prevents runaway automation through:

- **Daily/weekly PR limits**: Default 3/day, 10/week
- **Cooldown periods**: 4 hours between automations
- **Score thresholds**: Minimum score 60 for automation
- **Pattern blacklist**: Never automate sensitive patterns
- **Failed attempt tracking**: Stop after 5 failures

### 4. Configuration (`automation_config.yaml`)

Customizable settings for:

- Priority weights
- Safety limits
- GitHub integration
- Workflow constraints
- Environment-specific overrides

## Usage

### Basic Integration

```python
# In stop hook or reflection pipeline
from .claude.tools.amplihack.automation import Stage2AutomationEngine

# Process reflection results
engine = Stage2AutomationEngine()
result = engine.process_reflection_insights(Path("analysis.json"))

if result.success:
    print(f"Created PR #{result.pr_number}")
else:
    print(f"Automation skipped: {result.message}")
```

### Manual Pattern Processing

```python
from .claude.tools.amplihack.automation import PriorityScorer, AutomationGuard

# Score patterns
scorer = PriorityScorer()
patterns = [{"type": "error_patterns", "severity": "high", "count": 5}]
scored = scorer.score_patterns(patterns)

# Check guards
guard = AutomationGuard()
should_automate, reason = guard.should_automate(scored[0][1].score)

if should_automate:
    # Trigger automation
    pass
```

### Configuration Override

```python
# Temporarily increase limits for batch processing
engine = Stage2AutomationEngine()
engine.guard.update_config({
    "max_prs_per_day": 10,
    "cooldown_hours": 0
})
```

## Safety Features

### Pattern Blacklist

Never automates:

- Database migrations
- Authentication changes
- Payment processing
- User data handling
- Deployment configurations

### Emergency Controls

```python
# Emergency stop all automation
guard = AutomationGuard()
guard.emergency_stop()

# Resume with default limits
guard.resume_automation()

# Check current status
status = guard.get_current_status()
```

### Failed Attempt Handling

After 5 failed attempts:

1. Automation pauses
2. Manual intervention required
3. Reset with `guard.reset_failed_attempts()`

## Workflow Integration

The engine integrates with:

1. **improvement-workflow agent**: Preferred method, uses specialized agent
2. **DEFAULT_WORKFLOW.md**: Direct execution of 13-step workflow
3. **GitHub CLI**: Creates issues and PRs via `gh` commands

## Testing

Run the test suite:

```bash
cd .claude/tools/amplihack/automation
python test_stage2_engine.py
```

Tests verify:

- Pattern scoring accuracy
- Guard enforcement
- PR creation logic
- Integration flow

## Monitoring

Track automation activity:

```python
engine = Stage2AutomationEngine()
status = engine.get_status()

print(f"Engine enabled: {status['engine_enabled']}")
print(f"Daily PRs remaining: {status['guard_status']['daily_prs_remaining']}")
print(f"Recent workflows: {status['recent_workflows']}")
```

## Files

```
.claude/tools/amplihack/automation/
├── __init__.py              # Public interface
├── stage2_engine.py         # Main orchestrator
├── priority_scorer.py       # Pattern scoring
├── automation_guard.py      # Safety limits
├── automation_config.yaml   # Configuration
├── test_stage2_engine.py    # Test suite
└── README.md               # This file
```

## Environment Variables

- `AUTOMATION_DISABLED=true`: Disable all automation
- `AUTOMATION_TEST_MODE=true`: Relax limits for testing

## Future Enhancements

- [ ] Machine learning for pattern priority adjustment
- [ ] Slack/email notifications for automation events
- [ ] Web dashboard for monitoring
- [ ] Parallel workflow execution
- [ ] PR quality scoring and feedback loop
