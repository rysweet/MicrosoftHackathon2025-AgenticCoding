# Amplihack CLI

Enhanced command-line interface for Claude Code with Azure OpenAI integration support.

## Features

- **Agent Installation**: Install specialized AI agents to `~/.claude`
- **Proxy Integration**: Launch Claude with Azure OpenAI proxy for persistence
- **Smart Directory Detection**: Automatically finds `.claude` directories
- **System Prompt Enhancement**: Append custom prompts for specialized contexts
- **Cross-platform Support**: Works on Windows, macOS, and Linux

## Installation

```bash
# Clone the repository
git clone https://github.com/rysweet/MicrosoftHackathon2025-AgenticCoding
cd MicrosoftHackathon2025-AgenticCoding

# Install the package
pip install -e .
```

## Usage

### Install Agents

Install amplihack agents and tools to `~/.claude`:

```bash
amplihack install
```

### Launch Claude with Proxy

Launch Claude Code with Azure OpenAI proxy configuration:

```bash
# Basic launch (no proxy)
amplihack launch

# Launch with proxy configuration
amplihack launch --with-proxy-config /path/to/.env

# Launch with custom system prompt
amplihack launch --append-system-prompt /path/to/prompt.md

# Combined: proxy + system prompt
amplihack launch --with-proxy-config .env --append-system-prompt prompts/azure.md
```

### Uninstall Agents

Remove all amplihack components from `~/.claude`:

```bash
amplihack uninstall
```

## Proxy Configuration

Create a `.env` file for proxy configuration:

```env
# Required
ANTHROPIC_API_KEY=your-api-key

# Optional Azure configuration
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-azure-key
```

See `examples/proxy-config.env.example` for a complete template.

## How It Works

1. **Directory Detection**: Searches for `.claude` directory in current or parent directories
2. **Proxy Setup**:
   - Clones `claude-code-proxy` if not present
   - Copies your `.env` configuration
   - Starts proxy server on localhost:8080
3. **Environment Configuration**: Sets `ANTHROPIC_BASE_URL` to point to local proxy
4. **Claude Launch**: Starts Claude with `--dangerously-skip-permissions` flag
5. **Cleanup**: Automatically stops proxy when Claude exits

## Module Structure

```
src/amplihack/
├── __init__.py         # Main module entry
├── cli.py              # Enhanced CLI implementation
├── proxy/              # Proxy management
│   ├── manager.py      # Proxy lifecycle
│   ├── config.py       # Configuration parsing
│   └── env.py          # Environment setup
├── launcher/           # Claude launcher
│   ├── core.py         # Launch logic
│   └── detector.py     # Directory detection
├── utils/              # Utilities
│   ├── process.py      # Process management
│   └── paths.py        # Path resolution
└── prompts/            # System prompts
    └── azure_persistence.md
```

## Requirements

- Python 3.8+
- Git
- Node.js and npm (for proxy)
- Claude Code CLI installed

## Troubleshooting

### Proxy Won't Start

- Ensure Node.js and npm are installed
- Check that port 8080 is available
- Verify `.env` file has valid `ANTHROPIC_API_KEY`

### Claude Not Found

- Install Claude Code CLI: `npm install -g @anthropic-ai/claude-code`
- Ensure `claude` command is in your PATH

### Permission Issues

- The tool uses `--dangerously-skip-permissions` flag
- This bypasses Claude's normal permission prompts
- Only use with trusted proxy configurations

## Contributing

See the main repository README for contribution guidelines.
