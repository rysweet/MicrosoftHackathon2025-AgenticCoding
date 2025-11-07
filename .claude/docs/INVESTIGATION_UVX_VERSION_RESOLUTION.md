# Investigation: uvx Version Resolution and Caching Behavior

**Investigation Date**: 2025-11-07
**Investigator**: Integration Agent
**Subject**: How uvx determines when a new package version is available

## Executive Summary

uvx (the uv tool runner) uses a sophisticated caching strategy that prioritizes performance while respecting HTTP caching headers. The tool does NOT automatically check for new versions on every invocation - instead, it uses a cached environment after the first run and only checks for updates when explicitly requested.

## Key Findings

### 1. Version Resolution Process

**First Invocation Behavior:**
- On the first run, uvx resolves and fetches the latest available version from PyPI (or configured package index)
- Creates a virtual environment in the uv cache directory
- Installs the tool and its dependencies
- Caches the entire environment for future use

**Subsequent Invocations:**
- uvx reuses the cached environment without checking for updates
- No network requests are made to check for newer versions
- This behavior persists indefinitely unless explicitly overridden

### 2. Package Index and Version Discovery

**PyPI Integration:**
- uvx queries PyPI using the PEP 503 Simple Repository API
- Package metadata is fetched using HTTP requests
- uv uses HTTP range requests to fetch only the metadata (a few kilobytes) rather than downloading entire wheel files
- This is significantly more efficient than pip's approach of downloading complete wheels

**Version Information Sources:**
- Primary: PyPI (or configured package index)
- Git repositories: For git+ dependencies (cached by commit hash)
- Direct URLs: For URL dependencies (cached by URL with HTTP validation)
- Local paths: For editable/local dependencies (cached by modification time)

### 3. Caching Mechanism

**Cache Location:**
- Unix/Linux: `$XDG_CACHE_HOME/uv` or `$HOME/.cache/uv`
- Windows: `%LOCALAPPDATA%\uv\cache`
- Tools directory: `~/.local/share/uv/tools` (customizable via `UV_TOOL_DIR`)

**Cache Structure:**
- Tool environments are stored as isolated virtual environments
- Each tool gets its own directory (e.g., `tools/<tool-name>`)
- Environments include the tool package and all its dependencies
- Treated as disposable (can be removed and recreated automatically)

**What Gets Cached:**
- Registry dependencies (PyPI): Respected HTTP caching headers
- Direct URL dependencies: Cached by URL with HTTP validation
- Git dependencies: Cached by resolved commit hash
- Local dependencies: Cached by last-modified time

**Cache Duration:**
- Package metadata: 10 minutes (max-age=600 from PyPI headers)
- Wheels and source distributions: Indefinite (max-age=365000000, immutable)
- Tool environments: Persist until explicitly cleared or invalidated

### 4. Cache Invalidation Triggers

**Automatic Invalidation:**
- None - uvx does not automatically check for updates

**Manual Invalidation Methods:**

1. **Explicit version specification:**
   ```bash
   uvx ruff@0.6.0      # Run specific version
   uvx ruff@latest     # Force fetch latest version
   ```

2. **Cache refresh flags:**
   ```bash
   uvx --refresh ruff                    # Revalidate all dependencies
   uvx --refresh-package ruff ruff       # Revalidate specific package
   ```

3. **Cache cleaning:**
   ```bash
   uv cache clean           # Remove all cache entries
   uv cache clean ruff      # Remove cache for specific package
   uv cache prune           # Remove unused cache entries
   ```

4. **Isolated execution:**
   ```bash
   uvx --isolated ruff      # Ignore installed versions (doesn't refresh cache)
   uvx --no-cache ruff      # Bypass cache entirely
   ```

5. **Force latest check:**
   ```bash
   uvx --latest ruff        # Check for newer version, use cache if latest
   ```

### 5. Version Download Triggers

**New version downloads occur when:**
1. Tool is run for the first time (no cache exists)
2. `@latest` suffix is used and a newer version exists
3. Specific version is requested that differs from cached version
4. Cache is manually cleared and tool is run again
5. `--refresh` or `--refresh-package` flags are used
6. `--no-cache` flag forces bypass of cache

**Network requests are made to:**
- Fetch package metadata from PyPI (respecting 10-minute cache)
- Download wheel or source distribution files
- Validate HTTP caching headers for direct URL dependencies
- Fetch git repository data for git+ dependencies

### 6. Interaction with Installed Tools

**Priority hierarchy:**
1. `uv tool install` creates persistent installations
2. Once installed, uvx uses the installed version by default
3. Installed tools take precedence over cached ephemeral environments
4. To use a different version, specify explicitly with `@version` syntax

**Difference between uvx and uv tool install:**
- **uvx (uv tool run)**: Ephemeral, cached, disposable environments
- **uv tool install**: Persistent installations in tools directory
- Installed tools are NOT automatically updated

## HTTP Caching Details

**PyPI HTTP Headers:**
- Package metadata: `max-age=600` (10 minutes)
- Artifacts (wheels/sdists): `max-age=365000000, immutable`

**uv's HTTP Behavior:**
- Respects cache-control headers from package indexes
- Uses conditional requests for validation
- Employs HTTP range requests for efficient metadata fetching
- Cache is thread-safe and supports concurrent operations

**Customizing Cache Control:**
```toml
# In uv configuration
[tool.uv.index]
api = "max-age=600"  # Metadata cache duration
files = "max-age=365000000, immutable"  # Artifact cache
```

**Force revalidation:**
```toml
[tool.uv.index]
api = "no-cache"  # Always revalidate (not recommended)
```

## Performance Optimization

**Why uvx is fast:**
1. Caches entire tool environments after first run
2. No network requests on subsequent invocations
3. HTTP range requests fetch only metadata (not full wheels)
4. Respects HTTP caching headers (10-minute metadata cache)
5. Thread-safe, concurrent cache operations
6. Append-only cache structure for reliability

**Trade-offs:**
- Performance vs. Freshness: Prioritizes speed over automatic updates
- User must explicitly request updates with `@latest` or cache refresh
- May run outdated tool versions without user awareness

## Practical Implications

### For Users

**To ensure latest version:**
```bash
# Always get the latest version
uvx ruff@latest

# Or periodically clear cache
uv cache clean ruff
```

**To pin to specific version:**
```bash
# Run specific version
uvx ruff@0.6.0

# Or use --exclude-newer to limit by date
uvx --exclude-newer 2025-01-01 ruff
```

**To check what's cached:**
```bash
uv cache dir          # Show cache directory
ls $(uv cache dir)    # List cached items
```

### For CI/CD

**Recommendations:**
1. Use explicit versions for reproducibility: `uvx tool@1.2.3`
2. Consider `--no-cache` for always-fresh installations
3. Use `--exclude-newer` with specific dates for lockfile-like behavior
4. Cache the uv cache directory between CI runs for performance

### For Development

**Best practices:**
1. Use `uv tool install` for tools you use regularly
2. Use `uvx` for one-off tool executions or experiments
3. Periodically run `uv cache prune` to clean unused entries
4. Use `@latest` when you need the newest version explicitly

## Known Issues and Limitations

**Version Locking:**
- No built-in lock file mechanism for tools (unlike projects)
- Workaround: Use `--exclude-newer` with specific dates
- Feature request exists for better version locking

**Cache Refresh Ambiguity:**
- No clear documentation on when cache "spontaneously" refreshes
- Users report unexpected reinstallations
- Behavior appears non-deterministic in some edge cases

**Git Dependencies:**
- Some users report uv installing old cached versions even with new hash
- May require explicit cache clearing

**OS Upgrades:**
- Interpreter cache needs invalidation after OS version changes
- Fixed in recent versions by including OS version in cache key

## Related Commands and Options

**Version Management:**
```bash
uvx tool@version              # Specific version
uvx tool@latest               # Latest version
uvx --refresh tool            # Revalidate all dependencies
uvx --refresh-package tool    # Revalidate specific package
uvx --latest tool             # Check for newer, use cache if latest
```

**Cache Management:**
```bash
uv cache dir                  # Show cache location
uv cache clean                # Clear all cache
uv cache clean <package>      # Clear package cache
uv cache prune                # Remove unused entries
```

**Isolation:**
```bash
uvx --isolated tool           # Ignore installed versions
uvx --no-cache tool           # Bypass cache entirely
```

**Version Constraints:**
```bash
uvx --exclude-newer DATE tool # Limit by release date
uvx --from package tool       # Specify providing package
```

## References

**Official Documentation:**
- Tools Guide: https://docs.astral.sh/uv/concepts/tools/
- Caching: https://docs.astral.sh/uv/concepts/cache/
- Package Indexes: https://docs.astral.sh/uv/concepts/indexes/

**Key Design Decisions:**
1. Performance over automatic freshness
2. Explicit version control by users
3. HTTP standard compliance (caching headers)
4. Efficient network usage (range requests)
5. Thread-safe concurrent operations

## Conclusion

uvx uses a performance-first caching strategy where:
1. The latest version is fetched on first run
2. Cached environments are reused indefinitely
3. Updates require explicit user action (`@latest`, `--refresh`, cache clearing)
4. HTTP caching headers are respected (10-minute metadata cache)
5. Package indexes (PyPI) are queried only when necessary

This design prioritizes speed and efficiency over automatic freshness, placing the responsibility for version management on the user. For reproducible environments, explicit version specifications or date-based constraints are recommended.
