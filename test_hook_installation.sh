#!/bin/bash
# Comprehensive test suite for amplihack hook installation across all deployment scenarios
# Tests the fix for hook installation bug that handles all path formats

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Test function wrapper
run_test() {
    local test_name="$1"
    local test_function="$2"

    TESTS_RUN=$((TESTS_RUN + 1))
    log_info "Test $TESTS_RUN: $test_name"

    if $test_function; then
        log_success "$test_name"
    else
        log_error "$test_name"
    fi
    echo
}

# Setup test environment
setup_test_env() {
    # Create test directory
    TEST_DIR="/tmp/amplihack_hook_test_$$"
    BACKUP_DIR="/tmp/amplihack_backup_$$"

    mkdir -p "$TEST_DIR"
    mkdir -p "$BACKUP_DIR"

    # Backup existing Claude config if present
    if [ -d "$HOME/.claude" ]; then
        log_info "Backing up existing Claude config to $BACKUP_DIR"
        cp -r "$HOME/.claude" "$BACKUP_DIR/"
        HAS_BACKUP=true
    else
        HAS_BACKUP=false
    fi

    log_info "Test environment setup in $TEST_DIR"
}

# Cleanup test environment
cleanup_test_env() {
    # Restore backup if it exists
    if [ "$HAS_BACKUP" = true ]; then
        log_info "Restoring Claude config from backup"
        rm -rf "$HOME/.claude"
        cp -r "$BACKUP_DIR/.claude" "$HOME/"
    else
        # Clean up test installation
        rm -rf "$HOME/.claude"
    fi

    # Clean up temp directories
    rm -rf "$TEST_DIR"
    rm -rf "$BACKUP_DIR"

    log_info "Test environment cleaned up"
}

# Create test settings.json with different path formats
create_test_settings() {
    local path_format="$1"
    local settings_file="$2"

    case "$path_format" in
        "relative")
            cat > "$settings_file" << 'EOF'
{
  "hooks": {
    "SessionStart": [{"hooks": [{"type": "command", "command": ".claude/tools/amplihack/hooks/session_start.py", "timeout": 10000}]}],
    "Stop": [{"hooks": [{"type": "command", "command": ".claude/tools/amplihack/hooks/stop.py", "timeout": 30000}]}],
    "PostToolUse": [{"matcher": "*", "hooks": [{"type": "command", "command": ".claude/tools/amplihack/hooks/post_tool_use.py"}]}]
  }
}
EOF
            ;;
        "tilde")
            cat > "$settings_file" << 'EOF'
{
  "hooks": {
    "SessionStart": [{"hooks": [{"type": "command", "command": "~/.claude/tools/amplihack/hooks/session_start.py", "timeout": 10000}]}],
    "Stop": [{"hooks": [{"type": "command", "command": "~/.claude/tools/amplihack/hooks/stop.py", "timeout": 30000}]}],
    "PostToolUse": [{"matcher": "*", "hooks": [{"type": "command", "command": "~/.claude/tools/amplihack/hooks/post_tool_use.py"}]}]
  }
}
EOF
            ;;
        "absolute")
            cat > "$settings_file" << EOF
{
  "hooks": {
    "SessionStart": [{"hooks": [{"type": "command", "command": "$HOME/.claude/tools/amplihack/hooks/session_start.py", "timeout": 10000}]}],
    "Stop": [{"hooks": [{"type": "command", "command": "$HOME/.claude/tools/amplihack/hooks/stop.py", "timeout": 30000}]}],
    "PostToolUse": [{"matcher": "*", "hooks": [{"type": "command", "command": "$HOME/.claude/tools/amplihack/hooks/post_tool_use.py"}]}]
  }
}
EOF
            ;;
        "mixed")
            cat > "$settings_file" << EOF
{
  "hooks": {
    "SessionStart": [{"hooks": [{"type": "command", "command": ".claude/tools/amplihack/hooks/session_start.py", "timeout": 10000}]}],
    "Stop": [{"hooks": [{"type": "command", "command": "~/.claude/tools/amplihack/hooks/stop.py", "timeout": 30000}]}],
    "PostToolUse": [{"matcher": "*", "hooks": [{"type": "command", "command": "$HOME/.claude/tools/amplihack/hooks/post_tool_use.py"}]}]
  }
}
EOF
            ;;
        "none")
            cat > "$settings_file" << 'EOF'
{
  "permissions": {
    "allow": ["Bash", "TodoWrite"],
    "deny": []
  }
}
EOF
            ;;
    esac
}

# Verify hook paths in settings.json
verify_hook_paths() {
    local settings_file="$1"

    if [ ! -f "$settings_file" ]; then
        return 1
    fi

    # Count absolute paths
    local abs_paths=$(grep -c "\"$HOME/.claude/tools/amplihack/hooks/" "$settings_file" 2>/dev/null || echo "0")
    # Remove any newlines that might cause issues
    abs_paths=$(echo "$abs_paths" | tr -d '\n\r')

    # Should have exactly 3 absolute paths
    if [ "$abs_paths" -eq 3 ] 2>/dev/null; then
        return 0
    else
        log_warning "Expected 3 absolute paths, found '$abs_paths'"
        return 1
    fi
}

# Verify hook files exist
verify_hook_files() {
    local missing=0

    for hook in "session_start.py" "stop.py" "post_tool_use.py"; do
        if [ ! -f "$HOME/.claude/tools/amplihack/hooks/$hook" ]; then
            log_warning "Hook file missing: $hook"
            missing=$((missing + 1))
        fi
    done

    return $missing
}

# Test scenarios
test_relative_paths() {
    rm -rf "$HOME/.claude"
    mkdir -p "$HOME/.claude"

    create_test_settings "relative" "$HOME/.claude/settings.json"

    # Run install script
    cd "$TEST_DIR"
    AMPLIHACK_INSTALL_LOCATION="$(dirname "$0")" bash "$(dirname "$0")/.claude/tools/amplihack/install.sh" >/dev/null 2>&1

    verify_hook_paths "$HOME/.claude/settings.json" && verify_hook_files
}

test_tilde_paths() {
    rm -rf "$HOME/.claude"
    mkdir -p "$HOME/.claude"

    create_test_settings "tilde" "$HOME/.claude/settings.json"

    # Run install script
    cd "$TEST_DIR"
    AMPLIHACK_INSTALL_LOCATION="$(dirname "$0")" bash "$(dirname "$0")/.claude/tools/amplihack/install.sh" >/dev/null 2>&1

    verify_hook_paths "$HOME/.claude/settings.json" && verify_hook_files
}

test_absolute_paths() {
    rm -rf "$HOME/.claude"
    mkdir -p "$HOME/.claude"

    create_test_settings "absolute" "$HOME/.claude/settings.json"

    # Run install script
    cd "$TEST_DIR"
    AMPLIHACK_INSTALL_LOCATION="$(dirname "$0")" bash "$(dirname "$0")/.claude/tools/amplihack/install.sh" >/dev/null 2>&1

    verify_hook_paths "$HOME/.claude/settings.json" && verify_hook_files
}

test_mixed_paths() {
    rm -rf "$HOME/.claude"
    mkdir -p "$HOME/.claude"

    create_test_settings "mixed" "$HOME/.claude/settings.json"

    # Run install script
    cd "$TEST_DIR"
    AMPLIHACK_INSTALL_LOCATION="$(dirname "$0")" bash "$(dirname "$0")/.claude/tools/amplihack/install.sh" >/dev/null 2>&1

    verify_hook_paths "$HOME/.claude/settings.json" && verify_hook_files
}

test_no_existing_settings() {
    rm -rf "$HOME/.claude"

    # Run install script
    cd "$TEST_DIR"
    AMPLIHACK_INSTALL_LOCATION="$(dirname "$0")" bash "$(dirname "$0")/.claude/tools/amplihack/install.sh" >/dev/null 2>&1

    verify_hook_paths "$HOME/.claude/settings.json" && verify_hook_files
}

test_backup_creation() {
    rm -rf "$HOME/.claude"
    mkdir -p "$HOME/.claude"

    create_test_settings "relative" "$HOME/.claude/settings.json"

    # Run install script
    cd "$TEST_DIR"
    AMPLIHACK_INSTALL_LOCATION="$(dirname "$0")" bash "$(dirname "$0")/.claude/tools/amplihack/install.sh" >/dev/null 2>&1

    # Check if backup was created
    local backup_count=$(ls "$HOME/.claude"/settings.json.backup.* 2>/dev/null | wc -l)
    [ "$backup_count" -gt 0 ]
}

test_uvx_simulation() {
    # Simulate UVX deployment scenario where user runs install
    rm -rf "$HOME/.claude"
    mkdir -p "$HOME/.claude"

    # Create settings.json as if from UVX (relative paths)
    create_test_settings "relative" "$HOME/.claude/settings.json"

    # Run install script
    cd "$TEST_DIR"
    AMPLIHACK_INSTALL_LOCATION="$(dirname "$0")" bash "$(dirname "$0")/.claude/tools/amplihack/install.sh" >/dev/null 2>&1

    verify_hook_paths "$HOME/.claude/settings.json" && verify_hook_files
}

test_local_development() {
    # Simulate local development where settings.json already has absolute paths
    rm -rf "$HOME/.claude"
    mkdir -p "$HOME/.claude"

    create_test_settings "absolute" "$HOME/.claude/settings.json"

    # Run install script
    cd "$TEST_DIR"
    AMPLIHACK_INSTALL_LOCATION="$(dirname "$0")" bash "$(dirname "$0")/.claude/tools/amplihack/install.sh" >/dev/null 2>&1

    verify_hook_paths "$HOME/.claude/settings.json" && verify_hook_files
}

test_settings_persistence() {
    # Test that non-hook settings are preserved
    rm -rf "$HOME/.claude"
    mkdir -p "$HOME/.claude"

    cat > "$HOME/.claude/settings.json" << 'EOF'
{
  "permissions": {
    "allow": ["Bash", "TodoWrite", "CustomTool"],
    "deny": ["DangerousTool"],
    "defaultMode": "restrictive"
  },
  "customSetting": "preserved",
  "hooks": {
    "SessionStart": [{"hooks": [{"type": "command", "command": ".claude/tools/amplihack/hooks/session_start.py", "timeout": 10000}]}],
    "Stop": [{"hooks": [{"type": "command", "command": ".claude/tools/amplihack/hooks/stop.py", "timeout": 30000}]}],
    "PostToolUse": [{"matcher": "*", "hooks": [{"type": "command", "command": ".claude/tools/amplihack/hooks/post_tool_use.py"}]}]
  }
}
EOF

    # Run install script
    cd "$TEST_DIR"
    AMPLIHACK_INSTALL_LOCATION="$(dirname "$0")" bash "$(dirname "$0")/.claude/tools/amplihack/install.sh" >/dev/null 2>&1

    # Verify hooks were updated and other settings preserved
    if verify_hook_paths "$HOME/.claude/settings.json" && \
       grep -q '"customSetting": "preserved"' "$HOME/.claude/settings.json" && \
       grep -q '"defaultMode": "restrictive"' "$HOME/.claude/settings.json"; then
        return 0
    else
        return 1
    fi
}

# Main execution
main() {
    echo "🧪 Amplihack Hook Installation Test Suite"
    echo "=========================================="
    echo

    log_info "Setting up test environment..."
    setup_test_env

    # Run all tests
    run_test "Relative paths conversion" test_relative_paths
    run_test "Tilde paths conversion" test_tilde_paths
    run_test "Absolute paths handling" test_absolute_paths
    run_test "Mixed path formats" test_mixed_paths
    run_test "No existing settings.json" test_no_existing_settings
    run_test "Backup creation" test_backup_creation
    run_test "UVX deployment simulation" test_uvx_simulation
    run_test "Local development scenario" test_local_development
    run_test "Settings persistence" test_settings_persistence

    # Cleanup
    log_info "Cleaning up test environment..."
    cleanup_test_env

    # Results
    echo "=========================================="
    echo "📊 Test Results:"
    echo "   Total: $TESTS_RUN"
    echo "   Passed: $TESTS_PASSED"
    echo "   Failed: $TESTS_FAILED"

    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}✅ All tests passed!${NC}"
        exit 0
    else
        echo -e "${RED}❌ $TESTS_FAILED tests failed${NC}"
        exit 1
    fi
}

# Handle script interruption
trap cleanup_test_env EXIT

# Run main function
main "$@"
