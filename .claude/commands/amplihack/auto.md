# Auto Mode - Autonomous Agentic Loop

## Input Validation

@.claude/context/AGENT_INPUT_VALIDATION.md

## Usage

`/amplihack:auto <prompt>`

## Purpose

Execute an autonomous multi-turn agentic loop using the amplihack CLI's auto mode. This runs an iterative workflow (clarify → plan → execute → evaluate) that continues until the objective is complete or max iterations reached.

## What Auto Mode Does

The amplihack CLI auto mode:

1. **Turn 1: Clarify** - Restates objective and defines evaluation criteria
2. **Turn 2: Plan** - Breaks down into steps and identifies parallel opportunities
3. **Turns 3-9: Execute** - Implements, validates, evaluates, and adapts
4. **Turn 10: Complete** - Final evaluation and summary

Auto mode uses the same Claude CLI but orchestrates multiple turns automatically.

## When to Use

**Use /amplihack:auto for:**

- Complex multi-step implementations
- Tasks requiring iteration and refinement
- Problems where the path isn't immediately clear
- Work needing self-correction and adaptation

**Don't use for:**

- Simple single-step tasks
- Quick questions or information requests
- Code review only (use `/amplihack:analyze`)

## How to Invoke

# if you were called with /amplihack:auto

Use the Bash tool to run the amplihack CLI auto mode command:

```bash
amplihack claude --auto --max-turns 10 -- -p "$ARGUMENTS"
```

This will:

- Launch amplihack's auto mode using Claude
- Run up to 10 turns (default, adjustable with --max-turns)
- Pass the user's prompt via -p flag
- Execute the full agentic loop until objective is complete

## Notes

- Auto mode runs as a subprocess and streams output to console
- Progress is logged to `.claude/runtime/logs/auto_claude_*`
- User can interrupt at any time with Ctrl+C
- See `docs/AUTO_MODE.md` for comprehensive documentation
