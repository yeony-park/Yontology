#!/usr/bin/env python3
"""Check origin/main and fast-forward a clean main checkout before using a skill.

JSON statuses: up_to_date/updated (exit 0), skipped (exit 2), unverified (exit 3).
No checkout switching, stashing, resetting, pushing, or installation is performed.
"""

import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


class GitError(Exception):
    pass


def git(root, *args, allow_false=False):
    environment = dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never")
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args], capture_output=True, text=True,
            env=environment, timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GitError("git_unavailable_or_timed_out") from exc
    if result.returncode and not (allow_false and result.returncode == 1):
        # Do not expose credential-bearing remote URLs or helper output.
        raise GitError("git_command_failed")
    return result.stdout.strip(), result.returncode


def check(root, skill=None):
    root = Path(root).resolve()
    result = {"checkout": str(root), "target": "origin/main", "reload_required": False}

    def finish(status, reason=None, **extra):
        return dict(result, status=status, **({"reason": reason} if reason else {}), **extra)

    try:
        actual, _ = git(root, "rev-parse", "--show-toplevel")
        if Path(actual).resolve() != root:
            return finish("skipped", "not_checkout_root")
        if skill is not None:
            skill = Path(skill).expanduser().resolve()
            relative = skill.relative_to(root)
            if (len(relative.parts) != 3 or relative.parts[0] != "skills"
                    or relative.name != "SKILL.md" or not skill.is_file()):
                return finish("skipped", "skill_not_in_checkout")
            git(root, "ls-files", "--error-unmatch", "--", str(relative))
            result["skill_path"] = str(skill)
        git_dir, _ = git(root, "rev-parse", "--absolute-git-dir")
        with (Path(git_dir) / "yontology-update.lock").open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return finish("skipped", "update_in_progress")
            branch, _ = git(root, "symbolic-ref", "--quiet", "--short", "HEAD", allow_false=True)
            result["branch"] = branch or None
            local, _ = git(root, "rev-parse", "HEAD")
            result["local_commit"] = local
            if branch != "main":
                return finish("skipped", "not_on_main")
            dirty, _ = git(root, "status", "--porcelain", "--untracked-files=normal")
            if dirty:
                return finish("skipped", "local_changes")
            for marker in ("MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-merge", "rebase-apply"):
                if (Path(git_dir) / marker).exists():
                    return finish("skipped", "git_operation_in_progress")
            try:
                git(root, "fetch", "--no-tags", "--no-recurse-submodules", "origin",
                    "refs/heads/main:refs/remotes/origin/main")
            except GitError:
                return finish("unverified", "fetch_failed_or_timed_out")
            remote, _ = git(root, "rev-parse", "refs/remotes/origin/main")
            result["remote_commit"] = remote
            # Fetch may take time. Recheck before touching the worktree.
            now, _ = git(root, "rev-parse", "HEAD")
            branch_now, _ = git(root, "symbolic-ref", "--quiet", "--short", "HEAD", allow_false=True)
            dirty, _ = git(root, "status", "--porcelain", "--untracked-files=normal")
            if now != local or branch_now != branch or dirty:
                return finish("skipped", "checkout_changed_during_check")
            if local == remote:
                return finish("up_to_date")
            _, behind = git(root, "merge-base", "--is-ancestor", local, remote, allow_false=True)
            if behind:
                _, ahead = git(root, "merge-base", "--is-ancestor", remote, local, allow_false=True)
                return finish("skipped", "local_commits" if not ahead else "diverged_history")
            try:
                # Suppress merge hooks and autostash; protect ignored local .env.
                git(root, "-c", "core.hooksPath=/dev/null", "-c", "merge.autostash=false",
                    "merge", "--ff-only", "--no-edit", "--no-overwrite-ignore", remote)
            except GitError:
                return finish("skipped", "fast_forward_failed")
            current, _ = git(root, "rev-parse", "HEAD")
            result["local_commit"] = current
            if current != remote:
                return finish("unverified", "head_changed_after_update", reload_required=True)
            if skill is not None and not skill.is_file():
                return finish("updated", "skill_removed", previous_commit=local,
                              reload_required=True, skill_available=False)
            return finish("updated", previous_commit=local, reload_required=True)
    except ValueError:
        return finish("skipped", "skill_not_in_checkout")
    except (GitError, OSError):
        return finish("unverified", "git_or_filesystem_error")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", type=Path, help="Invoked SKILL.md, including an installed symlink path")
    args = parser.parse_args()
    result = check(ROOT, args.skill)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return {"up_to_date": 0, "updated": 0, "skipped": 2, "unverified": 3}[result["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
