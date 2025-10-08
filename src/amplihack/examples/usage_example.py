#!/usr/bin/env python
"""Example usage of amplihack modules."""  # noqa

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from amplihack.launcher import ClaudeDirectoryDetector, ClaudeLauncher  # noqa
from amplihack.proxy import ProxyConfig  # noqa

# PathResolver removed in simplification


def example_proxy_configuration():
    """Example of setting up proxy configuration."""
    print("=== Proxy Configuration Example ===")  # noqa: T201 (print)

    # Create a proxy configuration
    config_path = Path("proxy-config.env.example")
    if config_path.exists():
        config = ProxyConfig(config_path)
        print(f"Loaded configuration from: {config_path}")  # noqa: T201 (print)
        print(f"API Key present: {bool(config.get('ANTHROPIC_API_KEY'))}")  # noqa: T201 (print)
        print(f"Valid configuration: {config.validate()}")  # noqa: T201 (print)
    else:
        print(f"No configuration file found at: {config_path}")  # noqa: T201 (print)


def example_directory_detection():
    """Example of detecting .claude directory."""
    print("\n=== Directory Detection Example ===")  # noqa: T201 (print)

    detector = ClaudeDirectoryDetector()
    claude_dir = detector.find_claude_directory()

    if claude_dir:
        print(f"Found .claude directory: {claude_dir}")  # noqa: T201 (print)
        project_root = detector.get_project_root(claude_dir)
        print(f"Project root: {project_root}")  # noqa: T201 (print)
    else:
        print("No .claude directory found in hierarchy")  # noqa: T201 (print)


def example_path_utilities():
    """Example of using path utilities."""
    print("\n=== Path Utilities Example ===")  # noqa: T201 (print)

    # Note: PathResolver removed in simplification, using FrameworkPathResolver instead
    from amplihack.utils.paths import FrameworkPathResolver  # noqa

    # Find framework root
    framework_root = FrameworkPathResolver.find_framework_root()
    if framework_root:
        print(f"Found framework root: {framework_root}")  # noqa: T201 (print)
    else:
        print("No .claude framework directory found")  # noqa: T201 (print)

    # Find preferences file
    prefs_file = FrameworkPathResolver.resolve_preferences_file()
    if prefs_file:
        print(f"Found preferences file: {prefs_file}")  # noqa: T201 (print)
    else:
        print("No USER_PREFERENCES.md found")  # noqa: T201 (print)

    # Check if running in UVX deployment
    is_uvx = FrameworkPathResolver.is_uvx_deployment()
    print(f"Running in UVX deployment: {is_uvx}")  # noqa: T201 (print)


def example_launcher_setup():
    """Example of setting up the launcher (without actually launching)."""
    print("\n=== Launcher Setup Example ===")  # noqa: T201 (print)

    # Create a launcher with no proxy (dry run)
    launcher = ClaudeLauncher()

    # Build command that would be executed
    command = launcher.build_claude_command()
    print(f"Would execute: {' '.join(command)}")  # noqa: T201 (print)

    # With system prompt
    prompt_path = Path("prompts/azure_persistence.md")
    if prompt_path.exists():
        launcher_with_prompt = ClaudeLauncher(append_system_prompt=prompt_path)
        command = launcher_with_prompt.build_claude_command()
        print(f"With prompt: {' '.join(command)}")  # noqa: T201 (print)


def main():
    """Run all examples."""
    print("Amplihack Module Usage Examples\n")  # noqa: T201 (print)

    examples = [
        example_proxy_configuration,
        example_directory_detection,
        example_path_utilities,
        example_launcher_setup,
    ]

    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"Error in {example.__name__}: {e}")  # noqa: T201 (print)

    print("\n" + "=" * 50)  # noqa: T201 (print)
    print("Examples completed. Use 'amplihack launch' to actually launch Claude.")  # noqa: T201 (print)


if __name__ == "__main__":
    main()
