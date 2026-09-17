---
name: overview-project
description: Open a live local code map for the current repository, inspect file and symbol relationships, or export a standalone HTML snapshot with Overview Project.
---

Resolve this skill's real path, including symlinks. The tool root is two directories above this skill folder; its CLI is `cli/main.mjs`. Do not assume the user's working directory is the tool root.

Use Node 20+ and Python 3.9+ (for Python source analysis). Install the tool root's dependencies with `pnpm install --frozen-lockfile` if missing. Never run dependency installation in the analyzed project. `OVERVIEW_PYTHON` can select a Python executable matching the source syntax.

When Node is missing from PATH in Codex desktop, use `python3 <tool-root>/overview.py ...`; the launcher discovers the bundled Node runtime. For dependency installation in that environment, use the host's workspace-dependency paths for Node and pnpm.

For a live map, run `node <tool-root>/cli/main.mjs serve <target-project>` in a persistent terminal. It prints a loopback URL. Open that URL in the host's right browser panel when available; otherwise provide a clickable URL for an ordinary browser. If the port is occupied, use `--port 0` and open the printed URL. Do not terminate the user's existing process. Keep the server available during their work; it watches automatically. Stop the process when asked.

For an explicit one-time analysis use `scan`. For sharing use `export`; it prints the generated single HTML path. Exports contain symbol names, paths and source previews. Mention that content when handing off a shareable export; do not publish it automatically.

All generated state lives in `<target-project>/.overview-project/`. `tmp/snapshots/` is local analysis history, separate for every project checkout/user. The default retains 30 versions; `--keep N` changes retention. It is not Git version history. `history` lists retained versions. A repeated scan with unchanged content does not create a version.

The graph shows static references, not runtime ordering or executed test coverage. Dashed edges are inferred. Check diagnostics and limitations before describing a graph as complete. Do not infer cross-language HTTP connections or props/state dataflow from missing edges.
