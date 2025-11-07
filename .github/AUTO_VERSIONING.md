# Automatic Versioning System

## Overview

This repository uses automatic version bumping on every commit to the `main` branch using **CalVer (Calendar Versioning)** format: `YYYY.MM.MICRO`.

## How It Works

1. **Trigger**: Any push to `main` branch (except version bump commits, docs, tests)
2. **Version Format**: `YYYY.MM.MICRO`
   - `YYYY`: Current year (e.g., 2025)
   - `MM`: Current month (e.g., 11 for November)
   - `MICRO`: Auto-incrementing number within the month (resets to 1 each month)
3. **Actions**:
   - Bumps version in `pyproject.toml`
   - Commits the change
   - Creates a git tag (e.g., `v2025.11.1`)

## Version Examples

```
2025.11.1  → First version in November 2025
2025.11.2  → Second version in November 2025
2025.11.15 → Fifteenth version in November 2025
2025.12.1  → First version in December 2025 (MICRO resets)
```

## Why CalVer for This Project?

- **CLI Tool Focus**: Users care about "how recent" rather than API stability
- **Frequent Updates**: Handles high commit velocity naturally
- **Clear Temporal Context**: Easy to see when a version was released
- **No Semantic Debates**: No need to classify changes as major/minor/patch

## For Developers

### How Version Bumping Works

The system uses:

- **Script**: `.github/scripts/bump_version.py` - Bumps version in `pyproject.toml`
- **Workflow**: `.github/workflows/auto-version-bump.yml` - Automates the process
- **Protection**: Skips version bump commits to avoid infinite loops

### Testing Version Bump Locally

```bash
python .github/scripts/bump_version.py
git diff pyproject.toml
git checkout pyproject.toml  # Restore after testing
```

### Paths That Trigger Version Bumps

The workflow runs on commits that modify:

- Python source code (`src/**/*.py`)
- Configuration files (`pyproject.toml`, etc.)
- Core functionality

The workflow SKIPS commits that only modify:

- Documentation (`docs/**`, `**.md`)
- GitHub workflows (`.github/**`)
- Tests only (`tests/**`)

## Troubleshooting

### Version Bump Loop Detected

If you see "Version bump commit detected - skipping", this is normal. The workflow detected its own commit and skipped to avoid an infinite loop.

### Version Not Incrementing

Check if your commit modified ignored paths:

- Docs-only changes don't trigger version bumps
- Test-only changes don't trigger version bumps
- Workflow-only changes don't trigger version bumps

## Migration Notes

**Previous Version**: `0.1.7` (Semantic Versioning)
**New Version Format**: `2025.11.X` (Calendar Versioning)

The first auto-bump will transition from semantic versioning to CalVer format.
