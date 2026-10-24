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
# Only one category
zerodep list --category serialization

# Machine-readable
zerodep list --json
```

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

### `zerodep search <term> [...]`

Search module names, descriptions, categories, tiers, and dependencies. All
terms must match, case-insensitively.

```bash
$ zerodep search http
  httpclient  0.6.1  Zero-dependency sync + async HTTP REST client
  httpserver  0.6.1  Zero-dependency async HTTP server with decorator-based routing
  sse         0.4.1  Zero-dependency SSE (Server-Sent Events) client and event encoder

  3 module(s) matched

# JSON for scripts
zerodep search http --json
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

# Do not write zerodep.lock.json
zerodep add scheduler --no-lock

# Show the plan without copying anything
zerodep add sse --dry-run
```

Every install is recorded in `zerodep.lock.json` next to the copied files (see
[Source pinning and the lock file](#source-pinning-and-the-lock-file)).

`add` refuses to overwrite a file whose content differs from what the lock
recorded, or — for an install made before the lock existed — from upstream.
`--force` replaces it anyway. Files pulled in as dependencies are recorded
with `"requested": false`.

**Confirmation prompt** — by default, `add` shows a plan and asks for confirmation:

```
Will copy:
  sse.py                    -> sse.py  [sse]
  httpclient.py             -> httpclient.py  [httpclient (dependency)]
Target: /home/user/my-project
Continue? [Y/n]
```

### `zerodep update <module> [...]`

Update installed modules to the current source ref. Each module is compared
against `zerodep.lock.json`, so a local edit is never overwritten silently.

```bash
# Update one module (dependencies that upstream added are pulled in)
zerodep update sse

# Update everything that needs attention
zerodep update --all

# Preview the changes without writing anything
zerodep update --all --diff

# CI gate: exit 1 if anything needs attention
zerodep update --all --check

# Overwrite locally modified or unverified modules
zerodep update sse --force

# Update without recording the result in the lock
zerodep update sse --no-lock

# Show what would be updated, without writing
zerodep update --all --dry-run
```

| State | Meaning | `update` without `--force` |
|-------|---------|----------------------------|
| `up-to-date` | installed content matches the lock and upstream | nothing to do |
| `outdated` | upstream changed, local file untouched | overwritten |
| `locally-modified` | local bytes differ from the lock | **skipped**, exit 1 |
| `conflict` | upstream changed *and* the file was edited | **skipped**, exit 1 |
| `missing` | a recorded file was deleted | reinstalled |
| `unverified` | no lock record and content differs from upstream | **skipped**, exit 1 |
| `upstream-removed` | the module is no longer published | **skipped**, warning |

Skipped modules make the command exit 1, so a CI job cannot mistake a refused
update for a successful one. `--diff` is read-only and still prints the diff
for skipped modules, so `--force` is a decision you can inspect first.

#### Migrating a lock-less install

Before this lock existed, installs had no baseline, and an older copy cannot
be told apart from an older copy that was also edited. Those files are
therefore reported as `unverified` and are not updated automatically — `add`
and `update` both refuse without `--force`. The one-time migration is:

```bash
zerodep status                  # see what is unverified
zerodep update sse --diff       # inspect the change per module
zerodep update sse --force      # adopt upstream content, record the lock
# or, accepting that every unverified module is rewritten:
zerodep update --all --force
```

After that the lock exists and later updates only replace files that still
match the recorded bytes.

### `zerodep status`

Show every installed module with its installed version, latest version, and
state (the same states as `update`).

```bash
$ zerodep status
Module      Installed  Latest  State
----------  ---------  ------  ----------------
httpclient  0.6.1      0.6.1   up-to-date
jsonx       1.0.0      1.0.2   outdated
yaml        0.3.1      0.3.1   locally-modified
```

```bash
zerodep status --json         # machine-readable rows plus a state count
zerodep status --exit-code    # exit 1 unless everything is up-to-date
```

`status` also warns about dependencies that are not installed. Modules placed
in the vendor directory by hand are listed too, even when the lock does not
mention them.

### `zerodep remove <module> [...]`

Delete the files of an installed module and update the lock. Dependencies that
were only pulled in for it are suggested for removal; dependencies the module
still needs are reported.

```bash
# Show what would be deleted
zerodep remove sse --dry-run

# Delete, skipping the prompt
zerodep remove sse -y

# Delete a module whose files were edited locally
zerodep remove sse --force

# Machine-readable result
zerodep remove sse -y --json
```

`remove` refuses to delete a tracked file whose bytes differ from the lock
unless `--force` is given, and warns when another installed module still
depends on what is being removed. `--json` requires `--yes` (or `--force`)
because it cannot prompt.

### `zerodep outdated`

List local zerodep files and how they compare with upstream. Uses the same
state vocabulary as `status`; with a lock it distinguishes an upstream change
from a local edit, and without one it reports any difference as `unverified`.

```bash
$ zerodep outdated
Module  Local Ver  Latest Ver  Status
------  ---------  ----------  ----------------
semver  0.3.0      0.4.0       unverified
yaml    0.3.1      0.3.1       up-to-date
```

- **up-to-date** — the content is identical to upstream (metadata may differ)
- **unverified** — no lock record, and the content differs from upstream; it
  may be old, edited, or both
- **outdated** / **locally-modified** / **conflict** / **missing** /
  **upstream-removed** — as documented under `update`

Use `--json` for machine-readable output and `--exit-code` to fail when any
module is not up to date. Only files in the target directory are considered.

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

### `zerodep release-check`

Run every check that must hold before a release is tagged: module versions
against their declared version tags, manifest freshness, CalVer consistency
between `pyproject.toml` and `zerodep.py`, that module sources import only the
stdlib and sibling modules, that frontmatter `deps` match the sibling imports,
that every benchmark with a reference library has a `bench-*` extra, that
every test file is wired into the Makefile, the generated docs module index
(when the docs worktrees are mounted) and a clean working tree. Any failure
exits with code 1.

The Release workflow calls this same command, so the local check and CI cannot
drift apart.

```bash
$ zerodep release-check
Check            Result  Detail
---------------  ------  ---------------------------------------------
module-versions  ok      49 modules match their declared versions
manifest         ok      manifest.json matches the source tree
project-version  ok      2026.10.23.1 is CalVer and matches zerodep.py
docs-index       ok      docs module index matches the manifest
working-tree     ok      no uncommitted tracked changes

release-check passed
```

Use `--allow-dirty` to skip the working-tree check while iterating.

Two opt-in checks delegate to the project's own tooling instead of
reimplementing it:

```bash
# Run the pre-commit hooks (ruff, ruff-format, ty, complexipy)
zerodep release-check --with-lint

# Run correctness tests for specific modules (comma-separated)
zerodep release-check --with-tests httpclient,httpserver

# Run every correctness test
zerodep release-check --with-tests
```

Use `--version X` to validate the version that will be tagged: it must be CalVer
(`YYYY.M.D` / `YYYY.M.D.N`) and no `vX` tag may exist yet. The Release workflow
passes the version it computed, so a manual dispatch with an arbitrary version
string fails here instead of producing a mislabelled tag.

The manifest check compares the fields that describe the source tree (`files`,
`version`, `content_hash`, `deps`, `tier`, `category`, `description`) and
ignores `generated` and each module's `last_updated`, which are commit
timestamps and change when history is squashed or rewritten. Note that
`docs-index` is skipped when the docs worktrees are not mounted, which is the
case in CI — the docs gate runs for maintainers locally.

### Which tree a catalog command operates on

Commands that read or rewrite module sources — `manifest`, `bump`, `new`,
`version-check`, `dep-graph`, `dep-check` and `release-check` — operate on a
catalog: a checkout containing `manifest.json`. They find it by walking up from
the current directory, and fall back to the directory holding the CLI when that
is itself a checkout.

So an installed CLI works inside a checkout without `python -m zerodep`:

```bash
cd ~/projects/zerodep
zerodep release-check        # inspects this checkout, not site-packages

cd httpclient
zerodep version-check        # still resolves to the checkout above
```

`manifest.json` is the marker because it *is* the catalog — a directory that
merely contains a `pyproject.toml` is some other project. The name alone is not
enough either, since browser extensions, PWAs and npm packages all ship one: a
candidate counts only if the file parses as a zerodep manifest and at least one
module it lists exists on disk. A stray copy above your project therefore never
captures a command that runs below it, which also means `zerodep manifest`
cannot rewrite someone else's `manifest.json`.

The one exception is a checkout that has no catalog yet: the CLI plus a
`pyproject.toml` naming `zerodep` counts, so `zerodep manifest` can create the
file it is asked for, whether it is invoked from inside the checkout or from
elsewhere. It still refuses to write an empty catalog.

Manifests written before `primary_file` existed (tags up to `v2026.10.23`) fall
back to the first entry in `files`, so checking out an old tag and running the
installed CLI still resolves to that checkout.

Outside a catalog the command refuses instead of guessing:

```
error: version-check inspects the zerodep source tree, but no directory above
/home/me/other-project holds a zerodep manifest.json and this CLI is not part of
a checkout (/usr/lib/python3/site-packages).
  Run it from a checkout: cd /path/to/zerodep && python -m zerodep version-check
```

Without that guard every directory in `site-packages` looks like a zerodep
module, which is exactly what the command used to report. If two catalogs are
in play — the CLI belongs to one checkout and you are standing in another — the
command names the tree it used before writing to it.

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

# Create from an existing Python file
$ zerodep new mymodule --from ~/projects/other/mymodule.py

# From existing file with category/tier override
$ zerodep new mymodule --from ./mymodule.py --category text --tier medium
```

When using `--from`, the command:

- Copies the source file into the new module directory
- Injects zerodep frontmatter if the file doesn't already have one (preserves shebang/encoding lines)
- Preserves existing frontmatter if present; `--category`, `--tier`, `--deps` can override
- Warns if third-party imports are detected (zerodep modules must use stdlib only)

Without `--from`, this creates an empty scaffold:

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
config       dotenv, jsonx, yaml  (none)
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
| `--local` | Use local `manifest.json` and module sources instead of fetching from remote |
| `--ref <ref>` | Install from a release tag, branch, or commit (default: the latest release, cached for one hour) |

Global options must appear before the subcommand: `zerodep --ref master add sse`.

## Network Behavior

The CLI fetches files from the resolved source ref (by default the latest
published release, not the moving `master` branch) using a multi-source
fallback chain:

```
GitHub raw → jsDelivr CDN → Fastly CDN → local cache
```

1. Try `raw.githubusercontent.com` first
2. Fall back to `cdn.jsdelivr.net` mirror
3. Fall back to `fastly.jsdelivr.net` mirror
4. If all fail, use locally cached copy (with a warning)
5. With `--offline`, skip network entirely and use cache only

Fetched files are cached at `~/.zerodep/cache/` for offline use, per ref.
Each file's content hash is checked against the manifest before anything is
written; a mismatch aborts the whole operation, so a partial install is never
left behind.

## Source pinning and the lock file

`zerodep add` writes `zerodep.lock.json` next to the installed modules. It
records the source repository and the exact ref the files came from, each
module's version and upstream content hash, the sha256 of every installed
file, and whether the module was requested explicitly or pulled in as a
dependency.

```json
{
  "lock_version": 1,
  "source": {"repo": "Oaklight/zerodep", "ref": "v2026.10.23"},
  "modules": {
    "sse": {
      "version": "0.4.1",
      "upstream_hash": "b7937446…",
      "requested": true,
      "files": {"sse.py": "3f216fb3…"}
    }
  }
}
```

Commit the lock file with the vendored modules. It is what lets `update`
distinguish "upstream moved" from "I edited this file", and it pins the ref
your project was actually installed from. Pass `--no-lock` to opt out.

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
