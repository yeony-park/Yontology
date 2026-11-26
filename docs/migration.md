# Migration (agent harness branch)

1. Back up local configuration; use a stable checkout of this branch. Preserve the existing notes path and all user notes. Run the path resolver, then the existing installer to register new skills. If switching branches from a main-based install, the installer points to the same checkout; separate checkouts need separate install destinations or manual link migration.
2. Session Analyzer has been retired. If its installed symlink is now dangling, inspect it and remove only that link manually. Do not delete session data or another installation. History Insight remains.
3. Initialize Agent Memory using the explicit command below; the script creates missing directories and templates only.
4. Inspect `python3 scripts/render_hooks.py codex` or `python3 scripts/render_hooks.py claude`. Merge the printed entries into your existing provider hook configuration, preserving all other entries; use the provider's current documented user/project hook location and trust/restart workflow. Do not duplicate Deep Inside if already installed. Hook fragments use the local checkout's absolute path. On another host regenerate them there. For Claude installations that do not discover ~/.agents/skills use the existing installer with --dest ~/.claude/skills after reviewing conflicts.
5. Create/verify Paseo profiles on each host. Do not assume display labels are model IDs. Test using non-sensitive fixtures before live deployment.

```bash
python3 scripts/yontology_paths.py
python3 scripts/install_skills.py
python3 scripts/agent_memory.py init
python3 scripts/render_hooks.py codex
python3 scripts/render_hooks.py claude
```

Existing learning skills are deliberately unchanged; future refactors and Notion migration are separate.
