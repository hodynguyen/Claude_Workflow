"""Integration test for detect_stack.py — verifies backward-compatible imports and end-to-end build_profile."""
import os
import sys
import tempfile
import unittest

# Add the script to path
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

from detect_stack import build_profile, to_yaml


class TestEmptyProject(unittest.TestCase):
    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            profile = build_profile(tmpdir)
            self.assertEqual(profile["project"]["type"], "unknown")
            self.assertNotIn("frontend", profile)
            self.assertNotIn("backend", profile)


class TestBackwardCompatibleImports(unittest.TestCase):
    def test_build_profile_importable(self):
        self.assertTrue(callable(build_profile))

    def test_to_yaml_importable(self):
        self.assertTrue(callable(to_yaml))

    def test_load_existing_integrations_importable(self):
        from detect_stack import load_existing_integrations
        self.assertTrue(callable(load_existing_integrations))


if __name__ == "__main__":
    unittest.main()
