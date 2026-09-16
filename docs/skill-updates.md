# Skill version check

This checkout's Git commit is its version. The update target is `origin/main`.
Installed symlinks follow the checkout; copied skills are not managed by this
mechanism. This is an agent workflow instruction, not a host-enforced startup hook.

## Before using a skill

Once per user request and Yontology checkout, before starting skill-specific
work, resolve the invoked `SKILL.md` through symlinks to locate the checkout.
Run its own helper, independent of the user's current project directory:

```bash
python3 <checkout>/scripts/check_skill_updates.py --skill <invoked-SKILL.md>
```

Respect the host's network and filesystem permissions. A sandbox denial needs
the host's normal approval flow; never switch tools to bypass it.

| JSON status | Action |
| --- | --- |
| `up_to_date` | Continue with the current skill. The reported commit matched the remote when fetched. |
| `updated` | Report the update briefly, then re-read the resolved skill and any references already loaded for this request. Do not rerun the preflight just because the file was re-read. |
| `skipped` | Report the reason once and continue with the local version, unless the user requires the latest version. Never describe it as verified current. |
| `unverified` | Explain that checking failed and use the local version with that limitation, unless the user requires the latest version. Do not retry indefinitely. |

If `skill_available` is false, stop this skill workflow and explain that the
update removed or relocated the skill. Do not keep executing cached instructions.
If the helper or checkout is missing, report an unmanaged installation; do not
update a different project or silently replace the user's files.

## Update boundaries

The helper only fast-forwards a clean `main` checkout. It skips local edits,
untracked files, development branches, detached HEAD, unfinished Git operations,
local-only commits, diverged history, and concurrent updater runs. Git commands
have a 30-second timeout and do not prompt for login. Raw Git error output is not
printed because it can contain credential-bearing URLs.

Updates never stash, reset, switch branches, create commits, or push. A merge
that would overwrite an ignored local file such as `.env` is refused. Merge
hooks and automatic stashing are disabled for this operation. A successful update
changes the shared checkout and therefore every skill linked to it.

New skill directories require `scripts/install_skills.py` to register new links;
the updater does not install or remove links. Installed skills on another Mac
need that Mac's checkout to be updated separately.

To opt out for a particular request or use an older checkout, the user can ask
to use the local version without updating. Never imply a latest-version check
was performed in that case.
