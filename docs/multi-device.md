# Multiple Mac / host setup

Use one stable local checkout of the public repository per OS user/host. Git main is the distribution source of truth for skills, scripts, templates, and policy. Develop is for changes; do not auto-deploy a development checkout. The central storage server remains the source of truth for private task state, notes, and raw materials. Neither Git nor OneDrive is the live task-memory store.

## First install

Git and Python 3.10+ must be available. Choose a persistent local location, not a shared network filesystem. Do not clone over an existing installation.

```bash
mkdir -p "$HOME/.local/share"
git clone --branch main https://github.com/yeony-park/Yontology.git "$HOME/.local/share/Yontology"
cd "$HOME/.local/share/Yontology"
python3 scripts/bootstrap.py
```

The first run creates .env only if absent, then stops. Review the paths for this host; for a central deployment point NOTES_DIR and RAW_DIR at the mounted authorized shares (see storage.md). Do not initialize a local replacement for an unavailable server. Then rerun:

```bash
python3 scripts/bootstrap.py --claude --prune-retired
```

--claude is optional and installs into YONTOLOGY_CLAUDE_DIR/skills as well as YONTOLOGY_SKILLS_DIR. Check for duplicate discovery in the provider; omit it when the default directory already suffices. --prune-retired removes only the known Session Analyzer symlink if it points to this checkout's removed skill, never a real directory or another checkout. Existing unrelated or conflicting skills are not overwritten; setup stops on conflict. Multiple destinations are processed separately, not as a transaction. Existing installations can run bootstrap in their current stable checkout instead of moving it.

## Keeping each host current

Run at a safe task boundary, when no agent is actively reading this checkout:

```bash
cd "$HOME/.local/share/Yontology"
python3 scripts/bootstrap.py --update --claude --prune-retired
```

The existing guarded updater fetches origin/main, only fast-forwards clean main, and refuses divergent history, local modifications or protected ignored-file conflicts. It does not reset, stash, force or push. If the updater returns an error, installation stops. New skills are registered by the installer and existing symlinks resolve to the updated checkout. Restart Codex/Claude if they cache discovery. Update each Mac and any storage-server checkout separately. If the checkout predates bootstrap.py, use git pull --ff-only from clean main once first. No scheduled auto-update or update during an active task is enabled. Existing per-skill version checks remain; when updating an active shared checkout, avoid concurrent agents and do not blindly assume all skills are host-enforced.

## Machine-local items (not in Git)

- .env with actual mounted Vault and Documents paths, optional custom skill/provider directories.
- Provider account login, SSH keys, known_hosts, Tailscale identity, and actual Paseo profile IDs. Recreate/verify them for each host.
- Hook registration: generate the local fragment using render_hooks.py codex / claude, inspect the provider's current schema and merge without overwriting existing settings. Register Deep Inside only once. The hook points at this checkout, so code updates follow it; regenerate only if path/Python/hook schema changes. Provider support must be validated locally.
- Global agent instructions: review AGENTS.md and apply the relevant instructions to your provider's user-level config or each project's instructions without replacing existing rules. Repository-root AGENTS.md alone does not apply to arbitrary workspaces.
- Obsidian official connector skills are optional host installations; no automatic third-party installs.
- Central storage credentials and backup credentials never enter Git. Task writes are routed to the server; clients do not write checkpoints directly on SMB. Private/personal and shared roots remain separate.

For a new Mac, the one-time provider registration and mounts are still needed. This setup does not copy sessions, install a provider, configure the NAS, or grant access. It distributes behavior, not identity or private data.
