# Amplihack Hook Installation Testing Guide

This document provides comprehensive testing procedures for the amplihack hook
installation fix, covering all deployment scenarios and validation checks.

## Overview

The fix addresses path resolution issues in hook installation across different
deployment scenarios:

1. **Fixed settings.json** - Now uses relative paths
   (`.claude/tools/amplihack/hooks/stop.py`)
2. **Enhanced install.sh** - Handles all path formats with verification
3. **Comprehensive testing** - Covers UVX, local dev, with/without /install
   scenarios

## Quick Start

### Automated Testing

Run the complete test suite:

```bash
./test_hook_installation.sh
```

This will automatically test all scenarios and provide a pass/fail report.

### Manual Testing

For step-by-step verification, follow the procedures below.

## Testing Scenarios

### Scenario 1: UVX Deployment without /install (Relative Paths)

**Description**: User deploys via UVX without running install script. Should
work with relative paths.

**Setup**:

```bash
# Backup existing config
cp -r ~/.claude ~/.claude.backup 2>/dev/null || true

# Clean slate
rm -rf ~/.claude

# Simulate UVX deployment - copy project to ~/.claude
mkdir -p ~/.claude
cp -r .claude/* ~/.claude/
```

**Expected Behavior**:

- Settings.json uses relative paths: `.claude/tools/amplihack/hooks/`
- Hooks execute correctly from ~/.claude location
- No absolute path conversions needed

**Validation**:

```bash
# Check path format
grep '\.claude/tools/amplihack/hooks/' ~/.claude/settings.json

# Verify hook files exist and are accessible
ls -la ~/.claude/tools/amplihack/hooks/
python3 -m py_compile ~/.claude/tools/amplihack/hooks/stop.py
```

**Pass Criteria**:

- ✅ settings.json contains relative paths
- ✅ All hook files exist at ~/.claude/tools/amplihack/hooks/
- ✅ Hook files have valid Python syntax
- ✅ hook_processor.py dependency accessible

---

### Scenario 2: UVX Deployment with /install (Absolute Paths)

**Description**: User deploys via UVX then runs `/install` to optimize for
global use.

**Setup**:

```bash
# Clean slate
rm -rf ~/.claude

# Simulate UVX deployment first
mkdir -p ~/.claude
cp -r .claude/* ~/.claude/

# Run install script
AMPLIHACK_INSTALL_LOCATION="$(pwd)" bash .claude/tools/amplihack/install.sh
```

**Expected Behavior**:

- Converts relative paths to absolute paths
- Creates backup of original settings.json
- Verifies all hook files exist after installation
- Shows conversion status messages

**Validation**:

```bash
# Check path conversion
grep "$HOME/.claude/tools/amplihack/hooks/" ~/.claude/settings.json

# Verify backup created
ls ~/.claude/settings.json.backup.*

# Test hook accessibility
python3 -c "import sys; sys.path.append('$HOME/.claude/tools/amplihack/hooks'); import hook_processor"
```

**Pass Criteria**:

- ✅ settings.json contains absolute paths
- ✅ Backup file created with timestamp
- ✅ Install script reports successful path conversion
- ✅ All 3 hook entries converted (session_start, stop, post_tool_use)

---

### Scenario 3: Local Development (Symlink)

**Description**: Developer working locally with symlinked ~/.claude directory.

**Setup**:

```bash
# Clean slate
rm -rf ~/.claude

# Create symlink for local development
ln -s "$(pwd)/.claude" ~/.claude
```

**Expected Behavior**:

- Works with relative paths through symlink
- No install script needed
- Direct access to project files

**Validation**:

```bash
# Verify symlink
ls -la ~/.claude

# Check hook accessibility through symlink
python3 -m py_compile ~/.claude/tools/amplihack/hooks/stop.py

# Verify settings.json path format
grep '\.claude/tools/amplihack/hooks/' ~/.claude/settings.json
```

**Pass Criteria**:

- ✅ ~/.claude is a symlink to project directory
- ✅ Hook files accessible through symlink
- ✅ Relative paths work correctly
- ✅ No path conversion needed

---

### Scenario 4: Local Development with /install

**Description**: Developer runs install script from local project directory.

**Setup**:

```bash
# Clean slate
rm -rf ~/.claude

# Run install script from project directory
AMPLIHACK_INSTALL_LOCATION="$(pwd)" bash .claude/tools/amplihack/install.sh
```

**Expected Behavior**:

- Creates copy (not symlink) in ~/.claude
- Converts to absolute paths for global operation
- Works independently of project location

**Validation**:

```bash
# Verify it's a copy, not symlink
[ ! -L ~/.claude ] && [ -d ~/.claude ]

# Check absolute paths
grep "$HOME/.claude/tools/amplihack/hooks/" ~/.claude/settings.json

# Verify independence from project
mv .claude .claude.tmp
python3 -m py_compile ~/.claude/tools/amplihack/hooks/stop.py
mv .claude.tmp .claude
```

**Pass Criteria**:

- ✅ ~/.claude is a directory (not symlink)
- ✅ Uses absolute paths
- ✅ Works independently of project location
- ✅ All hook files copied and functional

---

### Scenario 5: Migration from Old Configurations

**Description**: User has existing configuration with tilde or mixed path
formats.

**Setup**:

```bash
# Clean slate
rm -rf ~/.claude
mkdir -p ~/.claude

# Create old-style config with tilde paths
cat > ~/.claude/settings.json << 'EOF'
{
  "permissions": {
    "allow": ["Bash", "TodoWrite"],
    "customSetting": "preserve_me"
  },
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/tools/amplihack/hooks/session_start.py",
            "timeout": 10000
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/tools/amplihack/hooks/stop.py",
            "timeout": 30000
          }
        ]
      }
    ]
  }
}
EOF

# Copy hook files
cp -r .claude/tools ~/.claude/

# Run install script to migrate
AMPLIHACK_INSTALL_LOCATION="$(pwd)" bash .claude/tools/amplihack/install.sh
```

**Expected Behavior**:

- Converts tilde paths to absolute paths
- Preserves existing non-hook settings
- Creates backup before modification
- Reports migration status

**Validation**:

```bash
# Check path migration
grep "$HOME/.claude/tools/amplihack/hooks/" ~/.claude/settings.json

# Verify settings preservation
grep '"customSetting": "preserve_me"' ~/.claude/settings.json

# Check backup creation
ls ~/.claude/settings.json.backup.*
```

**Pass Criteria**:

- ✅ Tilde paths converted to absolute paths
- ✅ Non-hook settings preserved
- ✅ Backup created before changes
- ✅ Migration reported as successful

---

### Scenario 6: Fresh Installation

**Description**: No existing ~/.claude directory - complete fresh install.

**Setup**:

```bash
# Ensure clean state
rm -rf ~/.claude

# Run fresh installation
AMPLIHACK_INSTALL_LOCATION="$(pwd)" bash .claude/tools/amplihack/install.sh
```

**Expected Behavior**:

- Creates new ~/.claude directory
- Generates complete settings.json with hooks
- Uses absolute paths for global operation
- Reports successful installation

**Validation**:

```bash
# Verify directory created
[ -d ~/.claude ]

# Check settings.json creation
[ -f ~/.claude/settings.json ]

# Verify complete hook configuration
grep -c "\"$HOME/.claude/tools/amplihack/hooks/" ~/.claude/settings.json
# Should return 3 (session_start, stop, post_tool_use)

# Validate JSON structure
python3 -c "import json; print('Valid JSON' if json.load(open('$HOME/.claude/settings.json')) else 'Invalid')"
```

**Pass Criteria**:

- ✅ ~/.claude directory created
- ✅ Complete settings.json generated
- ✅ All 3 hooks configured with absolute paths
- ✅ Valid JSON structure
- ✅ All hook files present and functional

---

## Edge Cases and Error Conditions

### Test 1: Existing tmpamplihack Directory

**Test**:

```bash
mkdir -p ./tmpamplihack
bash .claude/tools/amplihack/install.sh
```

**Expected**: Should fail with error message and exit code 1

### Test 2: Invalid Repository URL

**Test**:

```bash
AMPLIHACK_INSTALL_LOCATION="https://invalid-repo-url.com" bash .claude/tools/amplihack/install.sh
```

**Expected**: Should fail with git clone error

### Test 3: Read-only settings.json

**Test**:

```bash
mkdir -p ~/.claude
touch ~/.claude/settings.json
chmod 444 ~/.claude/settings.json
bash .claude/tools/amplihack/install.sh
```

**Expected**: Should handle gracefully or report permission error

### Test 4: Missing Hook Files

**Test**:

```bash
# Create incomplete installation
mkdir -p ~/.claude/tools/amplihack/hooks
rm ~/.claude/tools/amplihack/hooks/stop.py
bash .claude/tools/amplihack/install.sh
```

**Expected**: Should report missing hook files

## Validation Checks

### JSON Validity

```bash
# Validate settings.json syntax
python3 -c "import json; json.load(open('$HOME/.claude/settings.json'))"
```

### Hook File Syntax

```bash
# Check each hook file for Python syntax errors
for hook in session_start.py stop.py post_tool_use.py; do
    python3 -m py_compile ~/.claude/tools/amplihack/hooks/$hook
done
```

### Path Resolution

```bash
# Test that hooks can import dependencies
python3 -c "
import sys
sys.path.append('$HOME/.claude/tools/amplihack/hooks')
try:
    import hook_processor
    print('✅ hook_processor import successful')
except ImportError as e:
    print(f'❌ hook_processor import failed: {e}')
"
```

### Hook Configuration Completeness

```bash
# Verify all required hooks are configured
required_hooks=("SessionStart" "Stop" "PostToolUse")
for hook in "${required_hooks[@]}"; do
    if grep -q "\"$hook\"" ~/.claude/settings.json; then
        echo "✅ $hook configured"
    else
        echo "❌ $hook missing"
    fi
done
```

## Cleanup Procedures

### After Each Test

```bash
# Restore from backup if exists
if [ -d ~/.claude.backup ]; then
    rm -rf ~/.claude
    mv ~/.claude.backup ~/.claude
else
    rm -rf ~/.claude
fi

# Clean up test artifacts
rm -rf ./tmpamplihack
```

### Complete Reset

```bash
# Nuclear option - complete reset
rm -rf ~/.claude
rm -rf ~/.claude.backup
rm -rf ./tmpamplihack

# Remove any test backup files
rm -f ~/.claude.*.backup
```

## Troubleshooting

### Common Issues

1. **"Permission denied" errors**
   - Check file permissions: `ls -la ~/.claude/`
   - Ensure write access: `chmod 755 ~/.claude/`

2. **"Hook not found" errors**
   - Verify file existence: `ls ~/.claude/tools/amplihack/hooks/`
   - Check path format in settings.json

3. **"Import error" in hooks**
   - Verify hook_processor.py exists
   - Check Python path resolution
   - Test manual import:
     `python3 -c "import sys; sys.path.append('~/.claude/tools/amplihack/hooks'); import hook_processor"`

4. **Settings.json corruption**
   - Validate JSON:
     `python3 -c "import json; json.load(open('~/.claude/settings.json'))"`
   - Restore from backup if available

### Debug Commands

```bash
# Show current hook configuration
grep -A 10 -B 2 "amplihack" ~/.claude/settings.json

# Test hook execution environment
python3 ~/.claude/tools/amplihack/hooks/stop.py --help 2>/dev/null || echo "Hook execution failed"

# Check file permissions
ls -la ~/.claude/tools/amplihack/hooks/

# Verify path resolution
echo "Relative path test:"
cd ~/.claude && ls tools/amplihack/hooks/

echo "Absolute path test:"
ls $HOME/.claude/tools/amplihack/hooks/
```

## Success Criteria Summary

A successful hook installation should meet ALL criteria:

### Critical Path Requirements

- ✅ All hook files exist and have valid Python syntax
- ✅ settings.json is valid JSON with correct hook configuration
- ✅ Path format matches deployment scenario (relative for UVX, absolute for
  /install)
- ✅ hook_processor.py dependency is accessible
- ✅ Install script completes without errors

### Edge Case Handling

- ✅ Graceful failure with existing tmpamplihack directory
- ✅ Proper error reporting for invalid repository URLs
- ✅ Backup creation before modifying existing settings
- ✅ Settings preservation during migration

### Deployment Scenario Coverage

- ✅ UVX deployment works with relative paths
- ✅ Install script converts paths correctly
- ✅ Local development supports both symlink and copy modes
- ✅ Migration preserves existing non-hook settings
- ✅ Fresh installation creates complete configuration

## Testing Pyramid Coverage

Following the testing pyramid principle:

- **60% Unit Tests**: Individual hook file validation, path resolution, JSON
  parsing
- **30% Integration Tests**: Install script execution, settings.json
  modification, file copying
- **10% E2E Tests**: Complete deployment scenarios, user workflow simulation

This comprehensive testing approach ensures the hook installation fix works
reliably across all deployment scenarios while maintaining the existing
functionality.
