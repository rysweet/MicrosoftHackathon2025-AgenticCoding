# Amplihack Hook Installation Bug Fix

## Problem Summary

The amplihack hook installation system had a critical bug where the install
script couldn't update hook paths due to format mismatches between expected and
actual path formats in `settings.json`.

### Root Cause

- **Original settings.json**: Used absolute paths
  (`~/.claude/tools/amplihack/hooks/stop.py`)
- **Install script**: Expected relative paths
  (`.claude/tools/amplihack/hooks/stop.py`)
- **Result**: Silent failure - sed patterns didn't match, no updates occurred

## Solution Overview

### 1. Settings.json Fix ✅

**File**: `.claude/settings.json` **Change**: Converted to relative paths for
maximum compatibility

```json
// Before (absolute paths)
"command": "~/.claude/tools/amplihack/hooks/stop.py"

// After (relative paths)
"command": ".claude/tools/amplihack/hooks/stop.py"
```

**Benefits**:

- ✅ Works with UVX direct usage (relative to working directory)
- ✅ Compatible with install script transformations
- ✅ Maintains backward compatibility

### 2. Enhanced Install Script ✅

**File**: `.claude/tools/amplihack/install.sh` **Improvements**:

#### Comprehensive Path Format Support

- **Relative paths**: `.claude/tools/amplihack/hooks/*.py`
- **Tilde paths**: `~/.claude/tools/amplihack/hooks/*.py`
- **Absolute paths**: `/Users/username/.claude/tools/amplihack/hooks/*.py`
- **Mixed formats**: Handles combinations

#### Enhanced Feedback & Verification

- Path format detection and reporting
- Verification of successful updates (counts updated paths)
- Hook file existence verification
- Backup creation with timestamps
- Clear success/failure messages

#### Fallback Creation

- Creates complete settings.json if none exists
- Ensures all required hooks are configured
- Preserves existing non-hook settings

### 3. Comprehensive Testing ✅

**File**: `test_hook_installation.sh` **Coverage**: All deployment scenarios

## Deployment Scenarios Supported

### 1. UVX Direct Usage

**Scenario**: User runs `uvx amplihack` without /install

```bash
uvx amplihack launch
# Works immediately - hooks use relative paths
```

### 2. UVX + Install

**Scenario**: User runs /install after UVX deployment

```bash
uvx amplihack install
# Install script converts relative → absolute paths
# All path formats handled correctly
```

### 3. Local Development

**Scenario**: User clones repo and works locally

```bash
git clone repo && cd repo
# settings.json has relative paths, works directly
```

### 4. Local + Install

**Scenario**: User runs /install in local repo

```bash
git clone repo && cd repo
./claude/tools/amplihack/install.sh
# Install script handles path conversion
```

### 5. Transition/Migration

**Scenario**: Users with existing absolute paths

```bash
# Install script detects absolute paths
# Converts them to correct absolute format
# Preserves all functionality
```

## Migration Path for Existing Users

### Automatic Migration

The enhanced install script automatically handles migration:

1. **Detection**: Identifies current path format
2. **Conversion**: Updates to correct absolute paths
3. **Verification**: Confirms successful conversion
4. **Backup**: Creates timestamped backup

### Manual Migration (if needed)

If automatic migration fails:

```bash
# 1. Backup current settings
cp ~/.claude/settings.json ~/.claude/settings.json.backup

# 2. Re-run install
bash ~/.claude/tools/amplihack/install.sh

# 3. Verify hooks work
# Check that Claude Code session start triggers hooks correctly
```

### Verification Steps

After migration, verify:

1. **Hook files exist**:

   ```bash
   ls ~/.claude/tools/amplihack/hooks/
   # Should show: session_start.py, stop.py, post_tool_use.py
   ```

2. **Correct paths in settings.json**:

   ```bash
   grep "hooks" ~/.claude/settings.json
   # Should show absolute paths with your home directory
   ```

3. **Hooks execute**:
   - Start Claude Code session
   - Check for session startup messages
   - Verify hooks run on tool usage and session end

## Testing

### Run Comprehensive Tests

```bash
# Run full test suite
./test_hook_installation.sh

# Expected output:
# 🧪 Amplihack Hook Installation Test Suite
# [PASS] Relative paths conversion
# [PASS] Tilde paths conversion
# [PASS] Absolute paths handling
# [PASS] Mixed path formats
# [PASS] No existing settings.json
# [PASS] Backup creation
# [PASS] UVX deployment simulation
# [PASS] Local development scenario
# [PASS] Settings persistence
# ✅ All tests passed!
```

### Manual Testing

Test each deployment scenario:

1. **Clean installation**:

   ```bash
   rm -rf ~/.claude
   bash .claude/tools/amplihack/install.sh
   ```

2. **Existing settings update**:

   ```bash
   # With existing settings.json
   bash .claude/tools/amplihack/install.sh
   ```

3. **UVX simulation**:
   ```bash
   # Test relative path conversion
   echo '{"hooks": {"Stop": [{"hooks": [{"command": ".claude/tools/amplihack/hooks/stop.py"}]}]}}' > ~/.claude/settings.json
   bash .claude/tools/amplihack/install.sh
   ```

## Troubleshooting

### Issue: Install script reports "No hook paths updated"

**Cause**: Unexpected settings.json format **Solution**:

1. Check current format: `grep -A10 '"hooks"' ~/.claude/settings.json`
2. Manual update or create new settings.json
3. Re-run install script

### Issue: Hook files missing after install

**Cause**: Installation source issue **Solution**:

1. Verify installation source: `echo $AMPLIHACK_INSTALL_LOCATION`
2. Check repo access: `git ls-remote $AMPLIHACK_INSTALL_LOCATION`
3. Use local installation: `AMPLIHACK_INSTALL_LOCATION=. bash install.sh`

### Issue: Hooks not executing

**Cause**: Path resolution or permissions **Solution**:

1. Check paths: `ls -la ~/.claude/tools/amplihack/hooks/`
2. Test execution: `python ~/.claude/tools/amplihack/hooks/session_start.py`
3. Check permissions: `chmod +x ~/.claude/tools/amplihack/hooks/*.py`

## Technical Details

### Path Transformation Logic

```bash
# The install script applies these transformations:
".claude/tools/amplihack/hooks/stop.py" → "/Users/username/.claude/tools/amplihack/hooks/stop.py"
"~/.claude/tools/amplihack/hooks/stop.py" → "/Users/username/.claude/tools/amplihack/hooks/stop.py"
"/Users/username/.claude/tools/amplihack/hooks/stop.py" → "/Users/username/.claude/tools/amplihack/hooks/stop.py" (no change)
```

### Settings.json Structure

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/Users/username/.claude/tools/amplihack/hooks/session_start.py",
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
            "command": "/Users/username/.claude/tools/amplihack/hooks/stop.py",
            "timeout": 30000
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "/Users/username/.claude/tools/amplihack/hooks/post_tool_use.py"
          }
        ]
      }
    ]
  }
}
```

## Success Criteria

✅ **UVX Direct**: Works immediately without install ✅ **UVX + Install**:
Install script succeeds with clear feedback ✅ **Local Development**: Works
directly from repo ✅ **Local + Install**: Install script works correctly ✅
**Migration**: Existing users automatically migrated ✅ **Backward
Compatibility**: No breaking changes ✅ **Clear Feedback**: Users know what
happened ✅ **Comprehensive Testing**: All scenarios validated

## Files Modified

1. **`.claude/settings.json`** - Fixed relative paths
2. **`.claude/tools/amplihack/install.sh`** - Enhanced path handling
3. **`test_hook_installation.sh`** - Comprehensive test suite (new)
4. **`HOOK_INSTALLATION_FIX.md`** - This documentation (new)

This fix ensures amplihack hooks work correctly across all deployment scenarios
with clear feedback and automatic migration for existing users.
