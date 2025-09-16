# extract-requirements

Extract functional requirements from a codebase, focusing on WHAT the software does rather than HOW it implements it.

## Usage

```
/extract-requirements <project-path> [options]
```

## Options

- `--output <file>` - Output file path (default: requirements.md)
- `--format <type>` - Output format: markdown, json, yaml (default: markdown)

## Examples

### Basic extraction
```
/extract-requirements ./my-project
```

### Specify output file
```
/extract-requirements ./my-project --output requirements.md
```

### JSON output for programmatic use
```
/extract-requirements ./my-project --format json --output requirements.json
```

## Description

This command provides clear instructions to Claude for analyzing a codebase and extracting functional requirements. It embraces Claude's intelligence rather than trying to orchestrate every detail through complex code.

### Philosophy

**"Code for structure, AI for intelligence"**

The tool follows ruthless simplicity:
- **130 lines of Python** instead of 700+
- **No complex orchestration** - Claude handles the analysis
- **No state management** - Claude manages the process
- **No SDK dependencies** - Direct, clear instructions

### How It Works

1. **Validates** the project path exists
2. **Formats** clear instructions for Claude
3. **Delegates** the actual analysis to Claude's intelligence
4. **Trusts** Claude to organize and extract requirements naturally

### What Claude Analyzes

When invoked, Claude will:
1. Explore the project structure to understand the codebase
2. Identify major functional modules and components
3. Extract what each module does (functionality, not implementation)
4. Organize requirements by functional category
5. Generate properly formatted requirements document

### Requirements Format

Generated requirements follow standard format:
```markdown
## Category: Feature Name

### REQ-MOD-001: Requirement Title
**Priority:** High/Medium/Low
**Category:** API/Data/UI/etc
**Description:** The system shall [action] [object] [condition/context]
**Evidence:** Brief rationale or code reference
```

### Focus Areas

Claude will focus on:
- User-facing functionality
- Business logic and rules
- Data processing and transformations
- API endpoints and interfaces
- Integration points
- Security and access control
- Performance-critical operations

### What's Excluded

Claude will avoid:
- Implementation details
- Technology stack specifics
- Code structure descriptions
- How things are coded

## Implementation

This simplified tool is located at:
`.claude/tools/requirement_extractor/`

To run it:
```bash
cd .claude/tools
python -m requirement_extractor <project-path> --output <file>
```

The tool is radically simplified from previous versions:
- **Before:** 700+ lines across 8 files with complex orchestration
- **After:** 130 lines total (just 2 files) that trust Claude's intelligence

## Why This Approach is Better

1. **Trusts Claude's Intelligence** - Claude can handle file discovery and analysis without micromanagement
2. **Ruthlessly Simple** - Follows the principle of minimal code for maximum capability
3. **Flexible** - Claude adapts to each codebase naturally
4. **Maintainable** - Less code means fewer bugs and easier updates
5. **Transparent** - Clear instructions that users can understand

## Performance

- Claude analyzes the entire codebase holistically
- No artificial module boundaries or chunking
- Natural organization based on actual code structure
- Complete analysis in a single pass when possible

This approach embodies the Amplifier philosophy: amplify Claude's capabilities, don't constrain them with unnecessary complexity.