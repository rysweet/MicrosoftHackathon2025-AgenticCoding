#!/usr/bin/env python3
"""
Bump version in pyproject.toml using CalVer (YYYY.MM.MICRO)

Auto-increments the micro version within the current month,
or resets to .1 when entering a new month.
"""

import sys
from datetime import datetime
from pathlib import Path


def load_toml(path):
    """Simple TOML parser for version line only"""
    try:
        lines = Path(path).read_text().splitlines()
    except FileNotFoundError:
        print("ERROR: pyproject.toml not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to read pyproject.toml: {e}", file=sys.stderr)
        sys.exit(1)

    for i, line in enumerate(lines):
        if line.strip().startswith("version ="):
            # Extract version: version = "0.1.7"
            try:
                version = line.split("=")[1].strip().strip("\"'")
                return lines, i, version
            except (IndexError, AttributeError):
                print(f"ERROR: Failed to parse version line: {line}", file=sys.stderr)
                sys.exit(1)

    print("ERROR: 'version =' line not found in pyproject.toml", file=sys.stderr)
    sys.exit(1)


def save_toml(path, lines):
    """Save TOML with preserved formatting"""
    try:
        Path(path).write_text("\n".join(lines) + "\n")
    except Exception as e:
        print(f"ERROR: Failed to write pyproject.toml: {e}", file=sys.stderr)
        sys.exit(1)


def bump_calver():
    """Bump version using CalVer format"""
    toml_path = Path("pyproject.toml")
    lines, version_line_idx, current = load_toml(toml_path)

    try:
        parts = current.split(".")
        if len(parts) == 3:
            year, month, micro = map(int, parts)
        else:
            # Fallback if current version isn't CalVer format
            year, month, micro = datetime.now().year, datetime.now().month, 0
    except (ValueError, IndexError):
        # Fallback for non-CalVer versions
        year, month, micro = datetime.now().year, datetime.now().month, 0

    now = datetime.now()
    current_year, current_month = now.year, now.month

    # If same year and month, increment micro; otherwise reset to .1
    if year == current_year and month == current_month:
        new_version = f"{year}.{month}.{micro + 1}"
    else:
        new_version = f"{current_year}.{current_month}.1"

    # Update version line
    lines[version_line_idx] = f'version = "{new_version}"'
    save_toml(toml_path, lines)

    print(new_version)
    return new_version


if __name__ == "__main__":
    try:
        bump_calver()
    except Exception as e:
        print(f"ERROR: Unexpected failure during version bump: {e}", file=sys.stderr)
        sys.exit(1)
