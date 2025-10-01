# Prerequisites

This document provides detailed installation instructions for all required tools across different platforms.

## Required Tools

The AmplihHack framework requires the following tools to be installed:

1. **Node.js** (v18 or higher) - Required for claude-trace
2. **npm** (comes with Node.js) - Package manager for Node.js
3. **uv** - Fast Python package installer and resolver
4. **git** - Version control system

## Quick Check

You can check if all prerequisites are installed by running:

```bash
amplihack
```

If any tools are missing, the framework will display detailed installation instructions.

## Platform-Specific Installation

### macOS

**Package Manager:** We recommend using [Homebrew](https://brew.sh/)

#### Install Homebrew (if not already installed)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### Install Required Tools

```bash
# Node.js and npm (installed together)
brew install node

# uv
brew install uv

# git
brew install git
```

#### Verify Installation

```bash
node --version   # Should show v18.x or higher
npm --version    # Should show 9.x or higher
uv --version     # Should show version info
git --version    # Should show 2.x or higher
```

---

### Linux

**Package Managers:** apt (Ubuntu/Debian), dnf (Fedora/RHEL), pacman (Arch)

#### Ubuntu/Debian

```bash
# Node.js and npm
sudo apt update
sudo apt install nodejs npm

# uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# git
sudo apt install git
```

#### Fedora/RHEL/CentOS

```bash
# Node.js and npm
sudo dnf install nodejs npm

# uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# git
sudo dnf install git
```

#### Arch Linux

```bash
# Node.js and npm
sudo pacman -S nodejs npm

# uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# git
sudo pacman -S git
```

#### Verify Installation

```bash
node --version   # Should show v18.x or higher
npm --version    # Should show 9.x or higher
uv --version     # Should show version info
git --version    # Should show 2.x or higher
```

---

### Windows Subsystem for Linux (WSL)

**Recommended:** Use the Linux installation instructions for your WSL distribution (usually Ubuntu)

WSL is detected automatically and will show appropriate Linux-based installation commands.

#### Ubuntu WSL

```bash
# Node.js and npm
sudo apt update
sudo apt install nodejs npm

# uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# git
sudo apt install git
```

#### After Installation

Restart your WSL terminal to ensure all tools are in your PATH:

```bash
# Close and reopen your WSL terminal, then verify:
node --version
npm --version
uv --version
git --version
```

---

### Windows (Native)

**Package Managers:** winget (recommended) or Chocolatey

#### Using winget (Windows 10 1709+)

```powershell
# Node.js and npm (installed together)
winget install OpenJS.NodeJS

# uv
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# git
winget install Git.Git
```

#### Using Chocolatey

```powershell
# Install Chocolatey first (if not installed):
# See https://chocolatey.org/install

# Node.js and npm
choco install nodejs

# uv
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# git
choco install git
```

#### Verify Installation

```powershell
node --version   # Should show v18.x or higher
npm --version    # Should show 9.x or higher
uv --version     # Should show version info
git --version    # Should show 2.x or higher
```

---

## Tool-Specific Documentation

### Node.js

**Purpose:** Runtime for claude-trace (enhanced debugging and tracing)

**Official Documentation:** https://nodejs.org/

**Minimum Version:** v18.0.0

**Alternative Installation Methods:**

- **nvm (Node Version Manager):** Recommended for managing multiple Node.js versions
  - macOS/Linux: https://github.com/nvm-sh/nvm
  - Windows: https://github.com/coreybutler/nvm-windows

### npm

**Purpose:** Package manager for installing claude-trace

**Official Documentation:** https://www.npmjs.com/

**Note:** npm is automatically installed with Node.js

**Verify npm Configuration:**

```bash
npm config get prefix  # Should show global installation directory
```

### uv

**Purpose:** Fast Python package installer and resolver

**Official Documentation:** https://docs.astral.sh/uv/

**Alternative Installation Methods:**

- **pip:** `pip install uv` (not recommended, slower)
- **cargo:** `cargo install uv` (if you have Rust toolchain)

**Configuration:**

```bash
# Optional: Configure uv cache location
export UV_CACHE_DIR=/path/to/cache

# Optional: Use specific Python version
uv python install 3.12
```

### git

**Purpose:** Version control and repository management

**Official Documentation:** https://git-scm.com/

**Minimum Version:** 2.0.0

**Configuration:**

```bash
# Set up your identity
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Verify configuration
git config --list
```

---

## Optional Tools

### claude-trace

**Purpose:** Enhanced debugging and traffic logging for Claude Code

**Installation:**

```bash
npm install -g @mariozechner/claude-trace
```

**Note:** AmplihHack can automatically install claude-trace if npm is available

**Documentation:** Part of claude-code ecosystem

**Usage:**

- Automatically used when `AMPLIHACK_USE_TRACE=1` (default)
- Disable with `AMPLIHACK_USE_TRACE=0`

---

## Troubleshooting

### "command not found" errors

**Problem:** Tool installed but not in PATH

**Solution:**

**macOS/Linux:**

```bash
# Check if tool is installed
which node npm uv git

# If missing from PATH, add to your shell profile:
# For bash:
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# For zsh:
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

**Windows:**

```powershell
# Add to PATH via System Settings:
# 1. Search for "Environment Variables"
# 2. Edit "Path" variable
# 3. Add tool installation directories
# 4. Restart PowerShell
```

### Permission errors during npm install

**Problem:** "permission denied" when installing npm packages globally

**Solution:**

**Option 1: Use a Node version manager (recommended)**

```bash
# Install nvm and use it to install Node.js
# This avoids permission issues
```

**Option 2: Fix npm permissions**

```bash
# Create a directory for global packages
mkdir ~/.npm-global

# Configure npm to use the new directory
npm config set prefix '~/.npm-global'

# Add to PATH
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.profile
source ~/.profile
```

**Option 3: Use sudo (not recommended)**

```bash
sudo npm install -g <package>
# Not recommended due to security implications
```

### uv installation fails

**Problem:** uv installer script fails or not found

**Solution:**

```bash
# Try alternative installation method
pip install uv

# Or if you have Rust:
cargo install uv

# Verify installation
uv --version
```

### Node.js version too old

**Problem:** Node.js version < 18

**Solution:**

**Using nvm:**

```bash
# Install latest LTS version
nvm install --lts
nvm use --lts
```

**Using package manager:**

```bash
# macOS
brew upgrade node

# Ubuntu/Debian - use NodeSource repository
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs

# Fedora
sudo dnf install nodejs

# Windows
winget upgrade OpenJS.NodeJS
```

---

## Verification Script

Run this script to verify all prerequisites:

```bash
#!/bin/bash

echo "Checking prerequisites..."
echo

# Check Node.js
if command -v node &> /dev/null; then
    echo "✓ Node.js: $(node --version)"
else
    echo "✗ Node.js: Not found"
fi

# Check npm
if command -v npm &> /dev/null; then
    echo "✓ npm: $(npm --version)"
else
    echo "✗ npm: Not found"
fi

# Check uv
if command -v uv &> /dev/null; then
    echo "✓ uv: $(uv --version)"
else
    echo "✗ uv: Not found"
fi

# Check git
if command -v git &> /dev/null; then
    echo "✓ git: $(git --version)"
else
    echo "✗ git: Not found"
fi

echo
echo "For installation instructions, see docs/PREREQUISITES.md"
```

---

## Next Steps

After installing all prerequisites:

1. **Verify installation:** Run `amplihack` to check all tools are detected
2. **Install claude-trace (optional):** Automatically installed on first use
3. **Configure git:** Set up your name and email
4. **Start using AmplihHack:** See README.md for usage instructions

---

## Support

If you encounter issues not covered in this guide:

1. Check the troubleshooting section above
2. Review the official documentation for each tool
3. Search for existing issues on GitHub
4. Create a new issue with:
   - Your platform and OS version
   - Command output showing the error
   - Steps you've already tried

---

**Last Updated:** 2025-10-01
