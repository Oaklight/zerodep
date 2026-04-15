# CLI Tool

The `zerodep` CLI automates module discovery, dependency resolution, and file copying — like a lightweight `pip` for single-file modules.

## Installation

### Run Directly (no install)

```bash
# Download zerodep.py from the repo
curl -O https://raw.githubusercontent.com/Oaklight/zerodep/master/zerodep.py

# Use it immediately
python zerodep.py list
```

### Install via pip

```bash
pip install zerodep
zerodep list
```

## Commands

### `zerodep list`

List all available modules with version and description.

```bash
$ zerodep list
  Module      Version  Description
  ----------  -----    ----------------------------------------
  aes         0.1.0    Pure-Python AES encryption: ECB, CBC, CTR, and GCM modes
  dotenv      0.1.0    .env file parser and loader
  httpclient  0.1.0    Zero-dependency sync + async HTTP REST client
  scheduler   0.1.0    Zero-dependency in-process task scheduler with cron support
  sse         0.1.0    Zero-dependency SSE (Server-Sent Events) client
  ...

  20 modules available
```

### `zerodep info <module>`

Show module details including files, version, and dependency tree.

```bash
$ zerodep info sse
Module:      sse
Version:     0.1.0
Description: Zero-dependency SSE (Server-Sent Events) client
Files:       sse/sse.py
Dependencies: httpclient
  (transitive: httpclient)
```

### `zerodep add <module> [...]`

Copy module files into your project. Dependencies are resolved and fetched automatically.

```bash
# Copy scheduler.py to current directory
zerodep add scheduler

# Copy sse + its dependency httpclient to lib/
zerodep add sse -d lib/

# Copy multiple modules
zerodep add retry dotenv yaml

# Use subdirectory structure (sse/sse.py, httpclient/httpclient.py)
zerodep add sse --nested

# Skip dependencies — copy only the requested module
zerodep add sse --no-deps

# Skip confirmation prompt
zerodep add scheduler -y

# Overwrite existing files without prompting
zerodep add scheduler -f
```

**Confirmation prompt** — by default, `add` shows a plan and asks for confirmation:

```
Will copy:
  sse.py                    -> sse.py  [sse]
  httpclient.py             -> httpclient.py  [httpclient (dependency)]
Target: /home/user/my-project
Continue? [Y/n]
```

### `zerodep update <module> [...]`

Re-fetch and overwrite existing module files. Equivalent to `add --force --yes`.

```bash
zerodep update sse
```

### `zerodep outdated`

Check local zerodep files for upstream content changes. Compares the content hash of each local file against the manifest, ignoring metadata-only changes (version bumps).

```bash
$ zerodep outdated
Module  Local Ver  Latest Ver  Status
------  ---------  ----------  ----------
semver  0.3.0      0.4.0       up-to-date
yaml    0.3.0      0.4.0       outdated
```

- **up-to-date** — the file content is identical to upstream (metadata may differ)
- **outdated** — the file has substantive upstream changes

Only files found in the current directory are checked; modules not present locally are silently skipped.

### `zerodep version-check`

Check which modules have been modified since their declared version tag. Compares the content hash of each module's current source against the git tag corresponding to its declared version.

```bash
$ zerodep version-check
Module       Version  Status
-----------  -------  -----------------------------
aes          0.4.0    up-to-date
cache        0.2.0    up-to-date
config       0.3.0    modified (needs version bump)
yaml         0.3.0    up-to-date
...
```

This is a maintainer command — run it before releasing to ensure all modified modules have had their version bumped.

Use `--strict` to exit with code 1 when any module needs a bump (useful in CI):

```bash
$ zerodep version-check --strict
# exits 0 if all up-to-date, 1 if any module needs a bump
```

### `zerodep bump`

Auto-detect changed modules and bump their frontmatter versions. By default performs a patch bump; use `--minor` or `--major` for larger increments.

```bash
# Auto-detect and patch-bump all changed modules
$ zerodep bump
Module       Old    New
-----------  -----  -----
config       0.3.0  0.3.1
yaml         0.3.0  0.3.1

bumped 2 module(s) (patch)
regenerating manifest.json ...
Generated manifest.json with 34 modules

# Minor bump specific modules
$ zerodep bump --minor config yaml

# Major bump
$ zerodep bump --major config
```

After bumping, the manifest is automatically regenerated. This command is used by the [release workflow](https://github.com/Oaklight/zerodep/actions/workflows/release.yml) to bump versions before tagging.

### `zerodep new`

Scaffold a new module directory with template files.

```bash
# Create a new module with defaults (tier=simple, category=utility)
$ zerodep new mymodule

# Specify category and tier
$ zerodep new mymodule --category network --tier subsystem

# With dependencies
$ zerodep new mymodule --deps httpclient yaml
```

This creates:

```
mymodule/
├── mymodule.py               # module file with frontmatter and copyright
└── test_mymodule_correctness.py  # test file with basic scaffold
```

Available categories: `agent`, `data`, `network`, `text`, `search`, `config`, `cli`, `security`, `utility`.
Available tiers: `simple`, `medium`, `subsystem`.

### `zerodep dep-graph`

Show module dependency relationships. Without arguments, displays a table of all modules that participate in any dependency. With a module name, shows detailed dependency info including transitive impact.

```bash
# All modules with dependencies
$ zerodep dep-graph
Module       Depends on           Depended on by
-----------  -------------------  -------------------
config       dotenv, jsonc, yaml  (none)
frontmatter  yaml                 skills
yaml         (none)               config, frontmatter
...

# Single module detail
$ zerodep dep-graph yaml
Module: yaml (v0.3.0)
  Depends on: (none)
  Depended on by: config, frontmatter
  Transitively affects: config, frontmatter, skills
```

### `zerodep dep-check`

Auto-detect changed modules and run correctness tests for them and all their downstream dependents. This ensures that a change in one module does not break modules that depend on it.

```bash
# Auto-detect changed modules
$ zerodep dep-check

Changed modules: yaml
Affected downstream: config, frontmatter, skills
Total modules to test: 4

Module       Changed  Test  Detail
-----------  -------  ----  ------
config       no       pass
frontmatter  no       pass
skills       no       pass
yaml         yes      pass

4 passed

# Check specific modules
$ zerodep dep-check yaml config
```

Exits with code 1 if any test fails — suitable for CI pipelines and pre-release checks.

### `zerodep manifest`

Regenerate `manifest.json` from local module source files. This is a maintainer command — run it after adding or updating modules in the repository.

```bash
$ zerodep manifest
Generated manifest.json with 20 modules
Modules with dependencies:
  sse -> httpclient
  vcs -> diff
```

See [Manifest](manifest.md) for details on the manifest format.

### `zerodep version`

Print the CLI version.

```bash
$ zerodep version
zerodep 2026.4.11
```

## Global Options

| Option | Description |
|--------|-------------|
| `--offline` | Use only cached files, no network access |
| `--local` | Use local `manifest.json` instead of fetching from remote |

## Network Behavior

The CLI fetches files using a multi-source fallback chain:

```
GitHub raw → jsDelivr CDN → Fastly CDN → local cache
```

1. Try `raw.githubusercontent.com` first
2. Fall back to `cdn.jsdelivr.net` mirror
3. Fall back to `fastly.jsdelivr.net` mirror
4. If all fail, use locally cached copy (with a warning)
5. With `--offline`, skip network entirely and use cache only

Fetched files are cached at `~/.zerodep/cache/` for offline use.

## Dependency Resolution

When you `add` a module, the CLI performs topological dependency resolution:

```
zerodep add sse
→ reads manifest.json
→ sse depends on httpclient
→ resolves: [httpclient, sse]  (deps first)
→ copies both files
```

Use `--no-deps` to skip dependency resolution and copy only the explicitly requested module.

## Examples

### Quick Start

```bash
# Start a new project and pull in what you need
mkdir my-tool && cd my-tool
zerodep add yaml dotenv structlog
# Now you have yaml.py, dotenv.py, structlog.py — ready to import
```

### Vendoring into a Library

```bash
# Copy into a vendor/ directory with subdirectory structure
zerodep add retry httpclient -d vendor/ --nested
# Result: vendor/retry/retry.py, vendor/httpclient/httpclient.py
```

### Air-Gapped Environment

```bash
# On a connected machine — populate the cache
zerodep add scheduler yaml dotenv -y
# Files are cached at ~/.zerodep/cache/

# On the air-gapped machine — copy the cache, then:
zerodep add scheduler yaml dotenv --offline -y
```
