# Claude Code Hooks

This directory contains hooks that extend Claude Code's functionality.

## Available Hooks

### stop.py

- **Type**: Stop hook
- **Purpose**: Captures learnings and updates discoveries at session end
- **Always Active**: Yes

### stop_azure_continuation.py

- **Type**: Stop hook with DecisionControl
- **Purpose**: Prevents premature stopping when using Azure OpenAI models through the proxy
- **Auto-Activates**: When Azure OpenAI proxy is detected (via environment variables)
- **Decision Logic**:
  - Continues if uncompleted TODO items exist
  - Continues if continuation phrases are detected
  - Continues if multi-part user request appears unfulfilled
  - Otherwise allows normal stop

### session_start.py

- **Type**: Session start hook
- **Purpose**: Initializes session logging and context
- **Always Active**: Yes

### post_tool_use.py

- **Type**: Post tool use hook
- **Purpose**: Tracks tool usage metrics
- **Always Active**: Yes

## Hook Installation

Claude Code automatically discovers and loads hooks from this directory when:

1. The hooks are executable (chmod +x)
2. They follow the naming convention for their hook type
3. They are in the `.claude/tools/amplihack/hooks/` directory

## Testing Hooks

Each hook should have an accompanying test file:

- `test_stop_azure_continuation.py` - Tests the Azure continuation hook

Run tests with:

```bash
python3 .claude/tools/amplihack/hooks/test_stop_azure_continuation.py
```

## Environment Variables

The Azure continuation hook checks for:

- `ANTHROPIC_BASE_URL` - Set to localhost when proxy is active
- `CLAUDE_CODE_PROXY_LAUNCHER` - Indicates proxy launcher usage
- `AZURE_OPENAI_KEY` - Azure OpenAI credentials
- `OPENAI_BASE_URL` - Azure OpenAI endpoint

## Hook Development

When creating new hooks:

1. Use the existing hooks as templates
2. Include comprehensive error handling
3. Log to `.claude/runtime/logs/` for debugging
4. Default to non-intrusive behavior on errors
5. Create accompanying test files
6. Document the hook's purpose and activation conditions
