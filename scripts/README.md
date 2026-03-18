# Scripts Directory

This directory contains the unified release and deployment tooling for MCP Memento.

## 📦 deploy.py — Primary Release Script

Single entry point for all release and deployment operations.

```bash
python scripts/deploy.py <command> [options]
```

---

## Commands

### `bump X.Y.Z`
Full release cycle: run tests, bump versions across all manifests, update
`CHANGELOG.md` and `README.md` badges, build wheel, commit, tag, push,
merge `dev → main`, and upload stub binaries to the GitHub release.

```bash
# Preview without side effects
python scripts/deploy.py bump 0.3.0 --dry-run

# Execute the full release
python scripts/deploy.py bump 0.3.0 --yes
```

### `build`
Build `sdist` + wheel only, no version bump or git operations.

Temporarily patches `README.md` for PyPI compatibility before building:
- Converts relative markdown links to absolute GitHub URLs.
- Injects a compact "📋 Recent Changes" table (last 4 releases from `CHANGELOG.md`)
  before the License section.

The original `README.md` is restored immediately after the build.

```bash
python scripts/deploy.py build
```

### `publish`
Upload `dist/*` to TestPyPI or PyPI using `twine`.

```bash
python scripts/deploy.py publish --target testpypi
python scripts/deploy.py publish --target pypi
```

### `ext-binaries`
Download the CI-built stub binaries from the GitHub Release `vX.Y.Z` and
commit them into `integrations/zed/stub/bin/`.

Use this after the CI workflow has finished building all 5 platform binaries.

```bash
python scripts/deploy.py ext-binaries
python scripts/deploy.py ext-binaries --version 0.3.0   # explicit version
```

> Alias `zed-binaries` is kept for backward compatibility.

### `status`
Print the current version string from every manifest file.

```bash
python scripts/deploy.py status
```

---

## Options

| Option | Applies to | Description |
|---|---|---|
| `--dry-run` | all | Preview all actions without executing |
| `--skip-tests` | `bump` | Skip pytest before release |
| `--skip-merge` | `bump` | Do not merge `dev → main` |
| `--yes` / `-y` | `bump`, `ext-binaries` | Auto-confirm all prompts |
| `--version X.Y.Z` | `ext-binaries` | Override Python version |

---

## Typical Release Flow

```bash
# 1. Dry run — verify everything looks correct
python scripts/deploy.py bump 0.3.0 --dry-run

# 2. Full release (bumps, builds, tags, pushes, uploads stub binaries)
python scripts/deploy.py bump 0.3.0 --yes

# 3. Monitor CI (cross-compiles stub for all 5 platforms)
gh run list --repo annibale-x/mcp-memento --limit 5

# 4. Optional: pull fresh CI-built binaries into repo and commit
python scripts/deploy.py ext-binaries

# 5. Publish to PyPI
python scripts/deploy.py publish --target pypi
```

---

## Files Modified by `bump`

| File | What changes |
|---|---|
| `pyproject.toml` | `version` field |
| `src/memento/__init__.py` | `__version__` |
| `integrations/zed/Cargo.toml` | `[package] version` |
| `integrations/zed/extension.toml` | `version` |
| `integrations/zed/src/lib.rs` | `STUB_EXT_RELEASE` constant |
| `README.md` | Version badge |
| `CHANGELOG.md` | New entry prepended |

---

## Zed Extension Stub Binaries

The stub binaries in `integrations/zed/stub/bin/` are pre-compiled native
launchers for each platform. They are:

1. Bundled in the repository for zero-download installs (dev extensions).
2. Uploaded as assets to the GitHub release `vX.Y.Z` by `deploy.py bump`.
3. Re-built by GitHub Actions CI (`.github/workflows/zed-stub-release.yml`)
   on every push of a `vX.Y.Z` tag, for all 5 targets:

| Platform | Asset |
|---|---|
| Windows x86-64 | `memento-stub-x86_64-pc-windows-msvc.exe` |
| macOS Intel | `memento-stub-x86_64-apple-darwin` |
| macOS Apple Silicon | `memento-stub-aarch64-apple-darwin` |
| Linux x86-64 | `memento-stub-x86_64-unknown-linux-gnu` |
| Linux ARM64 | `memento-stub-aarch64-unknown-linux-gnu` |

---

## Directory Structure

```
scripts/
├── README.md    ← This file
└── deploy.py    ← Unified release & deploy script
```

---

## Prerequisites

```bash
# Python build tools
pip install build twine

# GitHub CLI (for stub binary upload / download)
gh auth login
```

---

## Related Documentation

- **[docs/dev/DEV.md](../docs/dev/DEV.md)** — Full developer guide
- **[CHANGELOG.md](../CHANGELOG.md)** — Release history
- **[Main README](../README.md)** — Project overview and quick start