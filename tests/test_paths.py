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
from yontology_paths import load_paths


class PathSettingsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="yontology-config-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.settings = self.root / ".env"

    def test_quoted_unicode_home_and_relative_paths(self):
        self.settings.write_text(
            'YONTOLOGY_NOTES_DIR="상대 경로/학습" # comment\n'
            'YONTOLOGY_SKILLS_DIR="~/skills with spaces"\n'
            'YONTOLOGY_CLAUDE_DIR="${HOME}/claude data"\n'
        )
        paths = load_paths(self.settings)
        self.assertEqual(paths["YONTOLOGY_NOTES_DIR"], ROOT / "상대 경로/학습")
        self.assertEqual(paths["YONTOLOGY_SKILLS_DIR"], Path.home() / "skills with spaces")
        self.assertEqual(paths["YONTOLOGY_CLAUDE_DIR"], Path.home() / "claude data")

    def test_environment_override_does_not_mutate_environment(self):
        self.settings.write_text('YONTOLOGY_NOTES_DIR="/from-file"\n')
        with patch.dict(os.environ, {"YONTOLOGY_NOTES_DIR": "/from-environment"}):
            before = dict(os.environ)
            self.assertEqual(load_paths(self.settings)["YONTOLOGY_NOTES_DIR"], Path("/from-environment"))
            self.assertEqual(dict(os.environ), before)

    def test_invalid_configuration_is_not_executed(self):
        marker = self.root / "must-not-exist"
        for value in ['""', '"${YONTOLOGY_MISSING_TEST_VARIABLE}"', f'"$(touch {marker})"']:
            with self.subTest(value=value):
                self.settings.write_text(f"YONTOLOGY_NOTES_DIR={value}\n")
                with self.assertRaises(ValueError):
                    load_paths(self.settings)
        self.assertFalse(marker.exists())

    def test_missing_env_uses_portable_defaults(self):
        paths = load_paths(self.settings)
        self.assertEqual(paths["YONTOLOGY_NOTES_DIR"], Path.home() / "Documents/Yontology/notes")
        self.assertEqual(paths["YONTOLOGY_SKILLS_DIR"], Path.home() / ".agents/skills")


class CheckoutIntegrationTests(unittest.TestCase):
    def test_two_machine_configs_and_installed_symlink_use_checkout_env(self):
        with tempfile.TemporaryDirectory(prefix="yontology-integration-") as temporary:
            base = Path(temporary)
            checkout = base / "checkout with spaces"
            helpers = [
                "scripts/yontology_paths.py", "scripts/install_skills.py",
                "skills/daily-learning-tutor/scripts/study_scheduler.py",
                "skills/history-insight/scripts/session_corpus.py",
                "skills/session-analyzer/scripts/normalize_trace.py",
            ]
            for name in helpers:
                target = checkout / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / name, target)
            for name in ["daily-learning-tutor", "history-insight", "session-analyzer"]:
                (checkout / "skills" / name / "SKILL.md").write_text(name)
            # A caller's unrelated .env must never override the checkout's configuration.
            (base / ".env").write_text('YONTOLOGY_NOTES_DIR="/wrong-location"\n')
            environment = {key: value for key, value in os.environ.items()
                           if not key.startswith("YONTOLOGY_")}

            def run(*args):
                return subprocess.check_output([sys.executable, *map(str, args)],
                                               cwd=base, env=environment, text=True)

            for machine in ["맥 A", "맥 B"]:
                paths = {key: base / machine / child for key, child in {
                    "YONTOLOGY_NOTES_DIR": "notes", "YONTOLOGY_SKILLS_DIR": "skills",
                    "YONTOLOGY_CLAUDE_DIR": "claude", "YONTOLOGY_CODEX_DIR": "codex",
                }.items()}
                (checkout / ".env").write_text("".join(f'{key}="{value}"\n' for key, value in paths.items()))
                actual = json.loads(run(checkout / "scripts/yontology_paths.py"))
                self.assertEqual(actual, {key: str(value) for key, value in paths.items()})
                run(checkout / "scripts/install_skills.py")
                run(checkout / "scripts/install_skills.py")
                scheduler = paths["YONTOLOGY_SKILLS_DIR"] / "daily-learning-tutor/scripts/study_scheduler.py"
                self.assertTrue(scheduler.parent.parent.is_symlink())
                run(scheduler, "init")
                state = paths["YONTOLOGY_NOTES_DIR"] / "learning-tutor/state.json"
                self.assertEqual(json.loads(state.read_text())["cards"], {})
                run(scheduler, "validate")
                override = base / machine / "explicit-state.json"
                run(scheduler, "init", "--state", override)
                self.assertTrue(override.is_file())
                for relative, function, expected in [
                    (helpers[3], "default_claude_projects", paths["YONTOLOGY_CLAUDE_DIR"] / "projects"),
                    (helpers[4], "codex_home", paths["YONTOLOGY_CODEX_DIR"]),
                ]:
                    code = f"import runpy; print(runpy.run_path({str(checkout / relative)!r})[{function!r}]())"
                    self.assertEqual(run("-c", code).strip(), str(expected))


if __name__ == "__main__":
    unittest.main()
