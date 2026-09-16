import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from check_skill_updates import check, git, GitError


class SkillUpdateTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="yontology-update-")
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
                        GIT_AUTHOR_NAME="Test", GIT_AUTHOR_EMAIL="test@example.com",
                        GIT_COMMITTER_NAME="Test", GIT_COMMITTER_EMAIL="test@example.com")
        self.environment = patch.dict(os.environ, self.env)
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.remote = self.base / "remote.git"
        self.author = self.base / "author"
        self.local = self.base / "checkout with spaces"
        self.run_git(self.base, "init", "--bare", "--initial-branch=main", str(self.remote))
        self.run_git(self.base, "clone", str(self.remote), str(self.author))
        p = self.author / "skills/demo/SKILL.md"
        p.parent.mkdir(parents=True)
        p.write_text("version one\n")
        (self.author / ".gitignore").write_text(".env\n")
        scripts = self.author / "scripts"
        scripts.mkdir()
        shutil.copy2(ROOT / "scripts/check_skill_updates.py", scripts)
        self.commit(self.author)
        self.run_git(self.author, "push", "origin", "main")
        self.run_git(self.base, "clone", str(self.remote), str(self.local))
        self.skill = self.local / "skills/demo/SKILL.md"

    def run_git(self, root, *args):
        return subprocess.check_output(["git", "-C", str(root), *args], env=self.env,
                                       stderr=subprocess.PIPE, text=True).strip()

    def commit(self, root):
        self.run_git(root, "add", "-A")
        self.run_git(root, "commit", "-m", "test: update fixture")

    def publish(self):
        (self.author / "skills/demo/SKILL.md").write_text("version two\n")
        self.commit(self.author)
        self.run_git(self.author, "push", "origin", "main")

    def test_current_does_not_create_commit(self):
        before = self.run_git(self.local, "rev-parse", "HEAD")
        result = check(self.local, self.skill)
        self.assertEqual(result["status"], "up_to_date")
        self.assertEqual(result["local_commit"], before)
        self.assertFalse(result["reload_required"])

    def test_update_through_symlink_and_preserve_env(self):
        link = self.base / "installed"
        link.symlink_to(self.skill.parent, target_is_directory=True)
        settings = self.local / ".env"
        settings.write_text('YONTOLOGY_NOTES_DIR="/my/notes"\n')
        self.publish()
        result = check(self.local, link / "SKILL.md")
        self.assertEqual(result["status"], "updated")
        self.assertTrue(result["reload_required"])
        self.assertEqual((link / "SKILL.md").read_text(), "version two\n")
        self.assertEqual(settings.read_text(), 'YONTOLOGY_NOTES_DIR="/my/notes"\n')

    def test_dirty_and_untracked_files_are_preserved(self):
        self.publish()
        for p in [self.skill, self.local / "local-notes.md"]:
            with self.subTest(path=p):
                original = p.read_bytes() if p.exists() else None
                p.write_text("my edits\n")
                result = check(self.local, self.skill)
                self.assertEqual(result["reason"], "local_changes")
                self.assertEqual(p.read_text(), "my edits\n")
                if original is None:
                    p.unlink()
                else:
                    p.write_bytes(original)

    def test_development_branch_and_detached_head_are_not_switched(self):
        self.publish()
        self.run_git(self.local, "switch", "-c", "feat/local-work")
        self.assertEqual(check(self.local, self.skill)["reason"], "not_on_main")
        self.assertEqual(self.run_git(self.local, "branch", "--show-current"), "feat/local-work")
        self.run_git(self.local, "checkout", "--detach")
        self.assertEqual(check(self.local, self.skill)["reason"], "not_on_main")

    def test_ahead_and_divergence_never_discard_local_commits(self):
        (self.local / "extra.md").write_text("local work\n")
        self.commit(self.local)
        before = self.run_git(self.local, "rev-parse", "HEAD")
        self.assertEqual(check(self.local, self.skill)["reason"], "local_commits")
        self.publish()
        self.assertEqual(check(self.local, self.skill)["reason"], "diverged_history")
        self.assertEqual(self.run_git(self.local, "rev-parse", "HEAD"), before)

    def test_failed_fetch_does_not_claim_cached_ref_is_current(self):
        self.run_git(self.local, "remote", "set-url", "origin", str(self.base / "missing.git"))
        result = check(self.local, self.skill)
        self.assertEqual(result["status"], "unverified")
        self.assertNotIn("remote_commit", result)
        self.assertEqual(self.skill.read_text(), "version one\n")

    def test_ignored_env_collision_aborts_without_overwrite(self):
        (self.local / ".env").write_text("private configuration\n")
        (self.author / ".env").write_text("remote configuration\n")
        self.run_git(self.author, "add", "-f", ".env")
        self.commit(self.author)
        self.run_git(self.author, "push", "origin", "main")
        before = self.run_git(self.local, "rev-parse", "HEAD")
        self.assertEqual(check(self.local, self.skill)["reason"], "fast_forward_failed")
        self.assertEqual((self.local / ".env").read_text(), "private configuration\n")
        self.assertEqual(self.run_git(self.local, "rev-parse", "HEAD"), before)

    def test_concurrent_check_returns_without_updating(self):
        self.publish()
        with (self.local / ".git/yontology-update.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertEqual(check(self.local, self.skill)["reason"], "update_in_progress")
        self.assertEqual(self.skill.read_text(), "version one\n")

    def test_removed_skill_is_reported_for_agent_to_stop(self):
        (self.author / "skills/demo/SKILL.md").unlink()
        self.commit(self.author)
        self.run_git(self.author, "push", "origin", "main")
        result = check(self.local, self.skill)
        self.assertEqual(result["status"], "updated")
        self.assertFalse(result["skill_available"])

    def test_copied_skill_outside_checkout_is_not_updated(self):
        copied = self.base / "SKILL.md"
        copied.write_text("separate copy")
        result = check(self.local, copied)
        self.assertEqual(result["reason"], "skill_not_in_checkout")

    def test_cli_uses_own_checkout_from_unrelated_cwd(self):
        self.publish()
        output = subprocess.check_output(
            [sys.executable, str(self.local / "scripts/check_skill_updates.py"), "--skill", str(self.skill)],
            cwd=self.base, env=self.env, text=True,
        )
        self.assertEqual(json.loads(output)["status"], "updated")

    def test_timeout_is_bounded_and_handled(self):
        with patch("check_skill_updates.subprocess.run", side_effect=subprocess.TimeoutExpired("git", 30)):
            with self.assertRaises(GitError):
                git(self.local, "fetch", "origin")


if __name__ == "__main__":
    unittest.main()
