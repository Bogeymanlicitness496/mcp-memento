
---
name: bump command
description: How to bump the version in mcp-memento
type: feedback
---

Always edit dthe CHANGELOG and use `python robot.py bump` to bump the version in mcp-memento. Never manually edit version numbers in pyproject.toml, server.json, README.md, or CHANGELOG.md.

**Why:** The robot.py script handles all version bumps atomically and correctly (pyproject.toml, server.json, README badge, CHANGELOG). Manual bumps are error-prone and may miss files or steps.

**How to apply:** Whenever the user asks for a version bump / "fai bump" in mcp-memento, run `python robot.py bump` instead of editing files manually.


---
name: no co-authored-by in commits
description: Never add Co-Authored-By trailer to git commits
type: feedback
---

Never add "Co-Authored-By: Claude..." or any co-authorship trailer to git commit messages.

**Why:** The user explicitly doesn't want it. It pollutes commit history.

**How to apply:** Always commit with a plain message, no trailers whatsoever.
