"""Tests for DevOps and database detection."""
import os
import sys
import tempfile
import unittest

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

from detectors.profile import build_profile


class TestDevOps(unittest.TestCase):
    def test_docker(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            open(os.path.join(tmpdir, "Dockerfile"), "w").close()
            profile = build_profile(tmpdir)
            self.assertEqual(profile["devops"]["containerize"], "docker")

    def test_github_actions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".github", "workflows"))
            profile = build_profile(tmpdir)
            self.assertEqual(profile["devops"]["ci"], "github-actions")

    def test_gitlab_ci(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            open(os.path.join(tmpdir, ".gitlab-ci.yml"), "w").close()
            profile = build_profile(tmpdir)
            self.assertEqual(profile["devops"]["ci"], "gitlab-ci")

    def test_database_from_env(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, ".env.example"), "w") as f:
                f.write("DATABASE_URL=postgresql://localhost:5432/mydb\n")
            with open(os.path.join(tmpdir, "requirements.txt"), "w") as f:
                f.write("fastapi==0.104.0\n")
            profile = build_profile(tmpdir)
            self.assertEqual(profile["backend"]["database"], "postgresql")


if __name__ == "__main__":
    unittest.main()
