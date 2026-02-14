"""Tests for auto-refresh logic in inject_project_context.py and load_existing_integrations in detect_stack.py."""
import os
import sys
import tempfile
import time
import unittest

# Add hooks to path
HOOK_DIR = os.path.join(
    os.path.dirname(__file__),
    "..",
    "plugins",
    "hody-workflow",
    "hooks",
)
sys.path.insert(0, os.path.abspath(HOOK_DIR))

# Add detect_stack to path
SCRIPT_DIR = os.path.join(
    os.path.dirname(__file__),
    "..",
    "plugins",
    "hody-workflow",
    "skills",
    "project-profile",
    "scripts",
)
sys.path.insert(0, os.path.abspath(SCRIPT_DIR))

from inject_project_context import is_profile_stale, CONFIG_FILES
from detect_stack import load_existing_integrations


class TestIsProfileStale(unittest.TestCase):
    def _make_profile(self, tmpdir, content="project:\n  name: test\n"):
        hody_dir = os.path.join(tmpdir, ".hody")
        os.makedirs(hody_dir, exist_ok=True)
        profile_path = os.path.join(hody_dir, "profile.yaml")
        with open(profile_path, "w") as f:
            f.write(content)
        return profile_path

    def test_no_config_files_not_stale(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            profile_path = self._make_profile(tmpdir)
            self.assertFalse(is_profile_stale(tmpdir, profile_path))

    def test_older_config_not_stale(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create config file first
            pkg_path = os.path.join(tmpdir, "package.json")
            with open(pkg_path, "w") as f:
                f.write('{"name":"test"}')

            # Wait a moment, then create profile (newer)
            time.sleep(0.05)
            profile_path = self._make_profile(tmpdir)

            self.assertFalse(is_profile_stale(tmpdir, profile_path))

    def test_newer_config_is_stale(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create profile first
            profile_path = self._make_profile(tmpdir)

            # Wait a moment, then create config file (newer)
            time.sleep(0.05)
            pkg_path = os.path.join(tmpdir, "package.json")
            with open(pkg_path, "w") as f:
                f.write('{"name":"test","dependencies":{"react":"^18"}}')

            self.assertTrue(is_profile_stale(tmpdir, profile_path))

    def test_newer_gomod_is_stale(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            profile_path = self._make_profile(tmpdir)
            time.sleep(0.05)
            with open(os.path.join(tmpdir, "go.mod"), "w") as f:
                f.write("module example.com/app\n")
            self.assertTrue(is_profile_stale(tmpdir, profile_path))

    def test_newer_csproj_is_stale(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            profile_path = self._make_profile(tmpdir)
            time.sleep(0.05)
            with open(os.path.join(tmpdir, "MyApp.csproj"), "w") as f:
                f.write("<Project></Project>")
            self.assertTrue(is_profile_stale(tmpdir, profile_path))

    def test_newer_tf_file_is_stale(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            profile_path = self._make_profile(tmpdir)
            time.sleep(0.05)
            with open(os.path.join(tmpdir, "main.tf"), "w") as f:
                f.write('resource "aws_instance" "web" {}')
            self.assertTrue(is_profile_stale(tmpdir, profile_path))

    def test_newer_workflow_is_stale(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            profile_path = self._make_profile(tmpdir)
            time.sleep(0.05)
            wf_dir = os.path.join(tmpdir, ".github", "workflows")
            os.makedirs(wf_dir)
            with open(os.path.join(wf_dir, "ci.yml"), "w") as f:
                f.write("name: CI\n")
            self.assertTrue(is_profile_stale(tmpdir, profile_path))

    def test_missing_profile(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_path = os.path.join(tmpdir, ".hody", "profile.yaml")
            self.assertFalse(is_profile_stale(tmpdir, fake_path))


class TestLoadExistingIntegrations(unittest.TestCase):
    def _make_profile(self, tmpdir, content):
        hody_dir = os.path.join(tmpdir, ".hody")
        os.makedirs(hody_dir, exist_ok=True)
        with open(os.path.join(hody_dir, "profile.yaml"), "w") as f:
            f.write(content)

    def test_no_integrations(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_profile(tmpdir, "project:\n  name: test\n")
            result = load_existing_integrations(tmpdir)
            self.assertIsNone(result)

    def test_all_integrations(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_profile(tmpdir, (
                "project:\n  name: test\n"
                "integrations:\n"
                "  github: true\n"
                "  linear: true\n"
                "  jira: false\n"
            ))
            result = load_existing_integrations(tmpdir)
            self.assertEqual(result["github"], True)
            self.assertEqual(result["linear"], True)
            self.assertEqual(result["jira"], False)

    def test_partial_integrations(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_profile(tmpdir, (
                "project:\n  name: test\n"
                "integrations:\n"
                "  github: true\n"
                "conventions:\n"
                "  linter: eslint\n"
            ))
            result = load_existing_integrations(tmpdir)
            self.assertEqual(result["github"], True)
            self.assertNotIn("linter", result)

    def test_no_profile_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = load_existing_integrations(tmpdir)
            self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
