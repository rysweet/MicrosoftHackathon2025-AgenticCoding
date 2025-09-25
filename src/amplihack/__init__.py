import json
import os
import shutil
from pathlib import Path

HOME = str(Path.home())
CLAUDE_DIR = os.path.join(HOME, ".claude")
CLI_NAME = "amplihack_cli.py"
CLI_SRC = os.path.abspath(__file__)

MANIFEST_JSON = os.path.join(CLAUDE_DIR, "install", "amplihack-manifest.json")

# Essential directories that must be copied during installation
ESSENTIAL_DIRS = [
    "agents/amplihack",  # Specialized agents
    "commands/amplihack",  # Slash commands
    "tools/amplihack",  # Hooks and utilities
    "context",  # Philosophy, patterns, project info
    "workflow",  # DEFAULT_WORKFLOW.md
]

# Runtime directories that need to be created
RUNTIME_DIRS = [
    "runtime",
    "runtime/logs",
    "runtime/metrics",
    "runtime/security",
    "runtime/analysis",
]

# Settings.json template with proper hook configuration
SETTINGS_TEMPLATE = {
    "permissions": {
        "allow": ["Bash", "TodoWrite", "WebSearch", "WebFetch"],
        "deny": [],
        "defaultMode": "bypassPermissions",
        "additionalDirectories": [".claude", "Specs"],
    },
    "enableAllProjectMcpServers": False,
    "enabledMcpjsonServers": [],
    "hooks": {
        "SessionStart": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": "$HOME/.claude/tools/amplihack/hooks/session_start.py",
                        "timeout": 10000,
                    }
                ]
            }
        ],
        "Stop": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": "$HOME/.claude/tools/amplihack/hooks/stop.py",
                        "timeout": 30000,
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
                        "command": "$HOME/.claude/tools/amplihack/hooks/post_tool_use.py",
                    }
                ],
            }
        ],
        "PreCompact": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": "$HOME/.claude/tools/amplihack/hooks/pre_compact.py",
                        "timeout": 30000,
                    }
                ]
            }
        ],
    },
}


def ensure_dirs():
    os.makedirs(CLAUDE_DIR, exist_ok=True)


def copytree_manifest(repo_root, dst, rel_top=".claude"):
    """Copy all essential directories from repo to destination.

    Args:
        repo_root: Path to the repository root
        dst: Destination directory (usually ~/.claude)
        rel_top: Relative path to .claude directory in repo

    Returns:
        List of copied directory paths relative to dst
    """
    base = os.path.join(repo_root, rel_top)
    copied = []

    for dir_path in ESSENTIAL_DIRS:
        source_dir = os.path.join(base, dir_path)

        # Skip if source doesn't exist
        if not os.path.exists(source_dir):
            print(f"  ⚠️  Warning: {dir_path} not found in source, skipping")
            continue

        target_dir = os.path.join(dst, dir_path)

        # Create parent directories if needed
        os.makedirs(os.path.dirname(target_dir), exist_ok=True)

        # Remove existing target if it exists
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)

        # Copy the directory
        try:
            shutil.copytree(source_dir, target_dir)
            copied.append(dir_path)
            print(f"  ✅ Copied {dir_path}")
        except Exception as e:
            print(f"  ❌ Failed to copy {dir_path}: {e}")

    # Also copy settings.json if it exists and target doesn't have one
    settings_src = os.path.join(base, "settings.json")
    settings_dst = os.path.join(dst, "settings.json")

    if os.path.exists(settings_src) and not os.path.exists(settings_dst):
        try:
            shutil.copy2(settings_src, settings_dst)
            print("  ✅ Copied settings.json")
        except Exception as e:
            print(f"  ⚠️  Could not copy settings.json: {e}")

    return copied


def write_manifest(files, dirs):
    os.makedirs(os.path.dirname(MANIFEST_JSON), exist_ok=True)
    with open(MANIFEST_JSON, "w", encoding="utf-8") as f:
        json.dump({"files": files, "dirs": dirs}, f, indent=2)


def read_manifest():
    try:
        with open(MANIFEST_JSON, encoding="utf-8") as f:
            mf = json.load(f)
            return mf.get("files", []), mf.get("dirs", [])
    except Exception:
        return [], []


def get_all_files_and_dirs(root_dirs):
    all_files = []
    all_dirs = set()
    for d in root_dirs:
        if not os.path.exists(d):
            continue
        for r, dirs, files in os.walk(d):
            rel_dir = os.path.relpath(r, CLAUDE_DIR)
            all_dirs.add(rel_dir)
            for f in files:
                rel_path = os.path.relpath(os.path.join(r, f), CLAUDE_DIR)
                all_files.append(rel_path)
    return sorted(all_files), sorted(all_dirs)


def all_rel_dirs(base):
    result = set()
    for r, dirs, _files in os.walk(base):
        rel = os.path.relpath(r, CLAUDE_DIR)
        result.add(rel)
    return result


def ensure_settings_json():
    """Ensure settings.json exists with proper hook configuration."""
    settings_path = os.path.join(CLAUDE_DIR, "settings.json")

    # Load existing settings or use template
    if os.path.exists(settings_path):
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
            print("  📋 Found existing settings.json")

            # Back up existing settings
            import time

            backup_name = f"settings.json.backup.{int(time.time())}"
            backup_path = os.path.join(CLAUDE_DIR, backup_name)
            shutil.copy2(settings_path, backup_path)
            print(f"  💾 Backed up to {backup_name}")
        except Exception as e:
            print(f"  ⚠️  Could not read existing settings.json: {e}")
            print("  🔧 Creating new settings.json from template")
            settings = SETTINGS_TEMPLATE.copy()
    else:
        print("  🔧 Creating new settings.json")
        settings = SETTINGS_TEMPLATE.copy()

    # Update hook paths to use absolute paths
    hooks_updated = 0
    hooks_to_update = [
        ("SessionStart", "session_start.py"),
        ("Stop", "stop.py"),
        ("PostToolUse", "post_tool_use.py"),
        ("PreCompact", "pre_compact.py"),
    ]

    for hook_type, hook_file in hooks_to_update:
        if hook_type not in settings.get("hooks", {}):
            # Add missing hook configuration
            if "hooks" not in settings:
                settings["hooks"] = {}

            # Create hook config based on type
            if hook_type == "PostToolUse":
                settings["hooks"][hook_type] = [
                    {
                        "matcher": "*",
                        "hooks": [
                            {
                                "type": "command",
                                "command": os.path.join(
                                    HOME, ".claude", "tools", "amplihack", "hooks", hook_file
                                ),
                            }
                        ],
                    }
                ]
            else:
                timeout = 30000 if hook_type in ["Stop", "PreCompact"] else 10000
                settings["hooks"][hook_type] = [
                    {
                        "hooks": [
                            {
                                "type": "command",
                                "command": os.path.join(
                                    HOME, ".claude", "tools", "amplihack", "hooks", hook_file
                                ),
                                "timeout": timeout,
                            }
                        ]
                    }
                ]
            hooks_updated += 1
        else:
            # Update existing hook paths to absolute
            hook_configs = settings["hooks"][hook_type]
            for config in hook_configs:
                if "hooks" in config:
                    for hook in config["hooks"]:
                        if "command" in hook and "amplihack/hooks" in hook["command"]:
                            # Update to absolute path
                            old_cmd = hook["command"]
                            new_cmd = os.path.join(
                                HOME, ".claude", "tools", "amplihack", "hooks", hook_file
                            )
                            if old_cmd != new_cmd:
                                hook["command"] = new_cmd
                                hooks_updated += 1
                                print(f"  🔄 Updated {hook_type} hook path to absolute")

    # Ensure permissions are set correctly
    if "permissions" not in settings:
        settings["permissions"] = SETTINGS_TEMPLATE["permissions"].copy()
    else:
        # Ensure additionalDirectories includes .claude and Specs
        if "additionalDirectories" not in settings["permissions"]:
            settings["permissions"]["additionalDirectories"] = [".claude", "Specs"]
        else:
            for dir_name in [".claude", "Specs"]:
                if dir_name not in settings["permissions"]["additionalDirectories"]:
                    settings["permissions"]["additionalDirectories"].append(dir_name)

    # Write updated settings
    try:
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
        print(f"  ✅ Settings updated ({hooks_updated} hooks configured)")
        return True
    except Exception as e:
        print(f"  ❌ Failed to write settings.json: {e}")
        return False


def verify_hooks():
    """Verify that all hook files exist."""
    hooks_dir = os.path.join(CLAUDE_DIR, "tools", "amplihack", "hooks")
    hook_files = ["session_start.py", "stop.py", "post_tool_use.py", "pre_compact.py"]

    all_exist = True
    for hook_file in hook_files:
        hook_path = os.path.join(hooks_dir, hook_file)
        if os.path.exists(hook_path):
            print(f"  ✅ {hook_file} found")
        else:
            print(f"  ❌ {hook_file} missing")
            all_exist = False

    return all_exist


def create_runtime_dirs():
    """Create necessary runtime directories."""
    for dir_path in RUNTIME_DIRS:
        full_path = os.path.join(CLAUDE_DIR, dir_path)
        try:
            os.makedirs(full_path, exist_ok=True)
            if not os.path.exists(full_path):
                print(f"  ❌ Failed to create {dir_path}")
            else:
                print(f"  ✅ Runtime directory {dir_path} ready")
        except Exception as e:
            print(f"  ❌ Error creating {dir_path}: {e}")


def _local_install(repo_root):
    """
    Install amplihack files from the given repo_root directory.
    This provides a comprehensive installation that mirrors the shell script.
    """
    print("\n🚀 Starting amplihack installation...")
    print(f"   Source: {repo_root}")
    print(f"   Target: {CLAUDE_DIR}\n")

    # Step 1: Ensure base directory exists
    ensure_dirs()

    # Step 2: Track existing directories for manifest
    pre_dirs = all_rel_dirs(CLAUDE_DIR)

    # Step 3: Copy all essential directories
    print("📁 Copying essential directories:")
    copied_dirs = copytree_manifest(repo_root, CLAUDE_DIR)

    if not copied_dirs:
        print("\n❌ No directories were copied. Installation may be incomplete.")
        print("   Please check that the source repository is valid.\n")
        return

    # Step 4: Create runtime directories
    print("\n📂 Creating runtime directories:")
    create_runtime_dirs()

    # Step 5: Configure settings.json
    print("\n⚙️  Configuring settings.json:")
    settings_ok = ensure_settings_json()

    # Step 6: Verify hook files exist
    print("\n🔍 Verifying hook files:")
    hooks_ok = verify_hooks()

    # Step 7: Generate manifest for uninstall
    print("\n📝 Generating uninstall manifest:")

    # Build list of all directories to track
    all_essential = []
    for dir_path in ESSENTIAL_DIRS:
        full_path = os.path.join(CLAUDE_DIR, dir_path)
        if os.path.exists(full_path):
            all_essential.append(full_path)

    # Also track runtime dirs that were created
    for dir_path in RUNTIME_DIRS:
        full_path = os.path.join(CLAUDE_DIR, dir_path)
        if os.path.exists(full_path):
            all_essential.append(full_path)

    files, post_dirs = get_all_files_and_dirs(all_essential)
    new_dirs = sorted(set(post_dirs) - pre_dirs)
    write_manifest(files, new_dirs)
    print(f"   Manifest written to {MANIFEST_JSON}")

    # Step 8: Final summary
    print("\n" + "=" * 60)
    if settings_ok and hooks_ok and len(copied_dirs) > 0:
        print("✅ Amplihack installation completed successfully!")
        print(f"\n📍 Installed to: {CLAUDE_DIR}")
        print("\n📦 Components installed:")
        for dir_path in sorted(copied_dirs):
            print(f"   • {dir_path}")
        print("\n🎯 Features enabled:")
        print("   • Session start hook")
        print("   • Stop hook")
        print("   • Post-tool-use hook")
        print("   • Pre-compact hook")
        print("   • Runtime logging and metrics")
        print("\n💡 To uninstall: amplihack uninstall")
    else:
        print("⚠️  Installation completed with warnings")
        if not settings_ok:
            print("   • Settings.json configuration had issues")
        if not hooks_ok:
            print("   • Some hook files are missing")
        if len(copied_dirs) == 0:
            print("   • No directories were copied")
        print("\n💡 You may need to manually verify the installation")
    print("=" * 60 + "\n")


def uninstall():
    """Uninstall amplihack components from ~/.claude."""
    removed_any = False
    files, dirs = read_manifest()

    # Remove individual files from manifest
    removed_files = 0
    for f in files:
        target = os.path.join(CLAUDE_DIR, f)
        if os.path.isfile(target):
            try:
                os.remove(target)
                removed_files += 1
                removed_any = True
            except Exception as e:
                print(f"  ⚠️  Could not remove file {f}: {e}")

    # Remove directories from manifest (if any)
    for d in sorted(dirs, key=lambda x: -x.count(os.sep)):
        target = os.path.join(CLAUDE_DIR, d)
        if os.path.isdir(target):
            try:
                shutil.rmtree(target, ignore_errors=True)
                removed_any = True
            except Exception as e:
                print(f"  ⚠️  Could not remove directory {d}: {e}")

    # Always try to remove the main amplihack directories
    # This handles cases where the manifest might not track directories properly
    amplihack_dirs = [
        os.path.join(CLAUDE_DIR, "agents", "amplihack"),
        os.path.join(CLAUDE_DIR, "commands", "amplihack"),
        os.path.join(CLAUDE_DIR, "tools", "amplihack"),
        # Don't remove context, workflow, or runtime as they might be shared
    ]

    removed_dirs = 0
    for dir_path in amplihack_dirs:
        if os.path.exists(dir_path):
            try:
                shutil.rmtree(dir_path)
                removed_dirs += 1
                removed_any = True
            except Exception as e:
                print(f"  ⚠️  Could not remove {dir_path}: {e}")

    # Remove manifest file
    try:
        os.remove(MANIFEST_JSON)
    except Exception:
        pass

    # Report results
    if removed_any:
        print(f"✅ Uninstalled amplihack from {CLAUDE_DIR}")
        if removed_files > 0:
            print(f"   • Removed {removed_files} files")
        if removed_dirs > 0:
            print(f"   • Removed {removed_dirs} amplihack directories")
    else:
        print("Nothing to uninstall.")


def filecmp(f1, f2):
    try:
        if os.path.getsize(f1) != os.path.getsize(f2):
            return False
        with open(f1, "rb") as file1, open(f2, "rb") as file2:
            return file1.read() == file2.read()
    except Exception:
        return False


def main():
    # Import and use the enhanced CLI
    from .cli import main as cli_main

    return cli_main()
