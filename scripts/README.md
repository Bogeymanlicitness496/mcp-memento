# Scripts Directory

This directory contains the unified release and deployment tooling for MCP Memento.

## robot.py — Primary Release Script

```bash
python scripts/robot.py <command> [options]
```

---

## Development Workflow

```
rebuild  →  fix / test  →  rebuild  →  ...  →  bump [X.Y.Z]  →  promote  →  publish
```

### Inner loop (fast, no git)

```bash
python scripts/robot.py rebuild
```

Rebuilds everything needed to test the current code in Zed — no git interaction:

1. Compiles the Rust stub binary for the current platform and copies it into the Zed extension work dir
2. Builds the Python wheel (`dist/mcp_memento-*.whl`)
3. Deletes the Zed venv marker so the stub reinstalls from the local wheel on next startup
4. Prints next steps (Zed reload command + pip install command for local testing)

After `rebuild`, reload the extension in Zed:

```
Ctrl+Shift+P → "zed: extensions" → Reload mcp-memento
```

### Dev snapshot (commit + local tag)

```bash
# Auto-increment patch version (X.Y.Z → X.Y.Z+1)
python scripts/robot.py bump

# Explicit version
python scripts/robot.py bump 0.3.0
```

Freezes the current state as a numbered dev version:

1. Bumps version in all manifests
2. Scaffolds a `CHANGELOG.md` placeholder entry
3. Builds the wheel
4. Commits to `dev` and pushes
5. Creates a local-only tag `vX.Y.Z` (CI is **not** triggered)
6. Builds stub + uploads to the rolling `dev-latest` pre-release on GitHub
7. Installs the wheel into the Zed extension venv (same as `rebuild` step 3–4)

Use `bump` when you want a named checkpoint before moving on.

### Promote to official release

```bash
python scripts/robot.py promote
```

Promotes the current `pyproject.toml` version to an official release (interactive):

1. Verifies `CHANGELOG.md` has a filled-in entry for the current version
2. Runs the test suite
3. Pushes tag `vX.Y.Z` to origin (triggers CI stub cross-compile for all 5 platforms)
4. Merges `dev → main`
5. Uploads local stub binaries to the GitHub Release

> **Before running promote**, write the release notes manually in `CHANGELOG.md`:
> ```
> * YYYY-MM-DD: vX.Y.Z - <title> (Hannibal)
>   * change one
>   * change two
> ```
> `promote` will abort if the entry is missing or still contains placeholder text.

### Publish to PyPI

```bash
python scripts/robot.py publish

# TestPyPI first (recommended)
python scripts/robot.py publish -t
python scripts/robot.py publish
```

Uploads `dist/*` to PyPI. If the release tag was not yet on the remote,
it is pushed first (triggering CI).

---

## All Commands

### `rebuild`

Fast dev rebuild: stub + wheel + Zed venv. **No git interaction.**

```bash
python scripts/robot.py rebuild
python scripts/robot.py rebuild --dry-run
```

### `bump [X.Y.Z]`

Dev snapshot: bump versions, commit, local tag, build stub + upload to
`dev-latest`, build wheel, install into Zed venv.

```bash
python scripts/robot.py bump              # auto-increment patch (Z+1)
python scripts/robot.py bump 0.3.0        # explicit version
python scripts/robot.py bump --skip-tests
python scripts/robot.py bump --dry-run
```

### `promote`

Promote to official release: verify CHANGELOG, run tests, push tag,
merge dev→main, upload stubs. Always interactive.

```bash
python scripts/robot.py promote
python scripts/robot.py promote --skip-tests
python scripts/robot.py promote --dry-run
```

### `publish`

Upload `dist/*` to PyPI or TestPyPI.

```bash
python scripts/robot.py publish
python scripts/robot.py publish -t        # TestPyPI
python scripts/robot.py publish --dry-run
```

### `build`

Build sdist + wheel only. No version bump, no git operations.

```bash
python scripts/robot.py build
```

### `build-zed-stub`

Build the Rust stub binary for the current platform, copy it into
`integrations/zed/stub/bin/` and into the Zed work dir, then commit and push.

Use this when you modify `stub/src/main.rs` without doing a full `bump`.

```bash
python scripts/robot.py build-zed-stub
```

### `ext-binaries [--version X.Y.Z]`

Download CI-built stub binaries from the GitHub Release `vX.Y.Z` and commit
them into `integrations/zed/stub/bin/`. Run after CI finishes following a
`promote`.

```bash
python scripts/robot.py ext-binaries
python scripts/robot.py ext-binaries --version 0.3.0
```

### `upload-stubs [--version X.Y.Z]`

Create the GitHub Release (if missing) and upload local stub binaries from
`stub/bin/`. Manual fallback if the CI upload step failed during `promote`.

```bash
python scripts/robot.py upload-stubs
```

### `dev-install`

Invalidate the Zed venv marker so the stub reinstalls from
`MEMENTO_LOCAL_WHEEL` on next Zed startup. Prints the Zed settings snippet
and the pip install command.

Called automatically by `rebuild` — only run manually if needed.

```bash
python scripts/robot.py dev-install
```

### `status`

Print the current version from every manifest file.

```bash
python scripts/robot.py status
```

---

## Options Reference

| Option            | Applies to                        | Description                           |
|-------------------|-----------------------------------|---------------------------------------|
| `--dry-run`       | all                               | Preview all actions without executing |
| `--skip-tests`    | `bump`, `promote`                 | Skip pytest                           |
| `--version X.Y.Z` | `ext-binaries`, `upload-stubs`   | Override version                      |
| `--test` / `-t`   | `publish`                         | Upload to TestPyPI instead of PyPI    |
| `--yes` / `-y`    | `ext-binaries`                    | Auto-confirm prompts                  |

---

## What `bump` Modifies

| File | Change |
|------|--------|
| `pyproject.toml` | `version` field |
| `src/memento/__init__.py` | `__version__` |
| `integrations/zed/Cargo.toml` | `[package] version` |
| `integrations/zed/extension.toml` | `version` |
| `integrations/zed/src/lib.rs` | `STUB_EXT_RELEASE` constant |
| `README.md` | Version badge |
| `CHANGELOG.md` | Placeholder entry scaffolded (if not present) |

---

## Zed Extension: How the Stub and Wheel Are Resolved

### Stub binary (`memento-stub`)

The Zed WASM extension resolves the stub binary with a bundle-first strategy:

1. `stub/bin/<asset>` relative to the Zed extension work dir (placed by `rebuild` or `bump`)
2. A previously downloaded binary cached in the work dir
3. Download from the GitHub Release (`dev-latest` on dev channel, `vX.Y.Z` on prod)

`rebuild` always copies the freshly built binary to the work dir, so reinstalling
the extension always picks up the latest local build via path 1.

### Python package (`mcp-memento`)

The stub creates a `venv/` in the work dir and installs the package:

- If `<work_dir>/local_wheel.txt` exists → installs from the `.whl` path it contains
- Otherwise → `pip install --upgrade mcp-memento` from PyPI

`rebuild` writes `local_wheel.txt` automatically. The file is never present in
production installs (marketplace or PyPI users are unaffected).

The venv is rebuilt whenever the marker file (`venv/memento_version.txt`) is
missing or stale. `rebuild` deletes this marker on every run, forcing a reinstall
from the local wheel on next Zed startup. No Zed settings changes required.

---

## Stub Platforms (CI cross-compile)

| Platform | Asset filename |
|----------|---------------|
| Windows x86-64 | `memento-stub-x86_64-pc-windows-msvc.exe` |
| macOS Intel | `memento-stub-x86_64-apple-darwin` |
| macOS Apple Silicon | `memento-stub-aarch64-apple-darwin` |
| Linux x86-64 | `memento-stub-x86_64-unknown-linux-gnu` |
| Linux ARM64 | `memento-stub-aarch64-unknown-linux-gnu` |

Cross-compilation is triggered automatically by pushing the tag `vX.Y.Z` (done
by `promote`). The CI workflow is `.github/workflows/zed-stub-release.yml`.

---

## Prerequisites

```bash
# Python build + publish tools
pip install build twine

# GitHub CLI (for stub upload/download and dev-latest pre-release management)
gh auth login
```

---

## Related Documentation

- **[docs/dev/README.md](../docs/dev/README.md)** — Full developer guide
- **[CHANGELOG.md](../CHANGELOG.md)** — Release history
- **[README.md](../README.md)** — Project overview and quick start