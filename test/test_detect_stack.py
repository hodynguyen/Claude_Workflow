"""Tests for detect_stack.py using mock project structures."""
import json
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


class TestNodeProject(unittest.TestCase):
    def _make_package_json(self, tmpdir, deps=None, dev_deps=None):
        pkg = {"name": "test-app", "dependencies": deps or {}, "devDependencies": dev_deps or {}}
        with open(os.path.join(tmpdir, "package.json"), "w") as f:
            json.dump(pkg, f)

    def test_react_frontend(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_package_json(
                tmpdir,
                deps={"react": "^18.0.0", "react-dom": "^18.0.0"},
                dev_deps={"typescript": "^5.0.0", "vitest": "^1.0.0"},
            )
            profile = build_profile(tmpdir)
            self.assertEqual(profile["project"]["type"], "frontend")
            self.assertEqual(profile["frontend"]["framework"], "react")
            self.assertEqual(profile["frontend"]["language"], "typescript")
            self.assertEqual(profile["frontend"]["testing"], "vitest")

    def test_next_overrides_react(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_package_json(
                tmpdir,
                deps={"react": "^18.0.0", "next": "^14.0.0"},
            )
            profile = build_profile(tmpdir)
            self.assertEqual(profile["frontend"]["framework"], "next")

    def test_vue_frontend(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_package_json(tmpdir, deps={"vue": "^3.0.0"})
            profile = build_profile(tmpdir)
            self.assertEqual(profile["frontend"]["framework"], "vue")

    def test_express_backend(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_package_json(
                tmpdir,
                deps={"express": "^4.18.0", "@prisma/client": "^5.0.0"},
                dev_deps={"prisma": "^5.0.0"},
            )
            profile = build_profile(tmpdir)
            self.assertEqual(profile["project"]["type"], "backend")
            self.assertEqual(profile["backend"]["framework"], "express")
            self.assertEqual(profile["backend"]["orm"], "prisma")

    def test_fullstack(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_package_json(
                tmpdir,
                deps={"react": "^18.0.0", "fastify": "^4.0.0"},
            )
            profile = build_profile(tmpdir)
            self.assertEqual(profile["project"]["type"], "fullstack")
            self.assertEqual(profile["frontend"]["framework"], "react")
            self.assertEqual(profile["backend"]["framework"], "fastify")

    def test_state_management(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_package_json(tmpdir, deps={"react": "^18.0.0", "zustand": "^4.0.0"})
            profile = build_profile(tmpdir)
            self.assertEqual(profile["frontend"]["state"], "zustand")

    def test_styling_detection(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_package_json(
                tmpdir,
                deps={"react": "^18.0.0"},
                dev_deps={"tailwindcss": "^3.0.0"},
            )
            profile = build_profile(tmpdir)
            self.assertEqual(profile["frontend"]["styling"], "tailwind")

    def test_conventions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_package_json(
                tmpdir,
                deps={"react": "^18.0.0"},
                dev_deps={"eslint": "^8.0.0", "prettier": "^3.0.0"},
            )
            profile = build_profile(tmpdir)
            self.assertEqual(profile["conventions"]["linter"], "eslint")
            self.assertEqual(profile["conventions"]["formatter"], "prettier")


class TestGoProject(unittest.TestCase):
    def test_gin_backend(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "go.mod"), "w") as f:
                f.write("module github.com/test/api\n\nrequire github.com/gin-gonic/gin v1.9.1\n")
            profile = build_profile(tmpdir)
            self.assertEqual(profile["project"]["type"], "backend")
            self.assertEqual(profile["backend"]["language"], "go")
            self.assertEqual(profile["backend"]["framework"], "gin")
            self.assertEqual(profile["backend"]["testing"], "go-test")

    def test_echo_with_gorm(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "go.mod"), "w") as f:
                f.write("module test\n\nrequire (\n  github.com/labstack/echo v4\n  gorm.io/gorm v1.25\n)\n")
            profile = build_profile(tmpdir)
            self.assertEqual(profile["backend"]["framework"], "echo")
            self.assertEqual(profile["backend"]["orm"], "gorm")


class TestPythonProject(unittest.TestCase):
    def test_fastapi(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "requirements.txt"), "w") as f:
                f.write("fastapi==0.104.0\nsqlalchemy==2.0.0\npytest==7.4.0\n")
            profile = build_profile(tmpdir)
            self.assertEqual(profile["project"]["type"], "backend")
            self.assertEqual(profile["backend"]["language"], "python")
            self.assertEqual(profile["backend"]["framework"], "fastapi")
            self.assertEqual(profile["backend"]["orm"], "sqlalchemy")
            self.assertEqual(profile["backend"]["testing"], "pytest")

    def test_django(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "requirements.txt"), "w") as f:
                f.write("django==4.2.0\n")
            profile = build_profile(tmpdir)
            self.assertEqual(profile["backend"]["framework"], "django")
            self.assertEqual(profile["backend"]["orm"], "django-orm")


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


class TestToYaml(unittest.TestCase):
    def test_simple_dict(self):
        result = to_yaml({"key": "value"})
        self.assertEqual(result, "key: value")

    def test_nested_dict(self):
        result = to_yaml({"parent": {"child": "value"}})
        self.assertIn("parent:", result)
        self.assertIn("  child: value", result)

    def test_boolean(self):
        result = to_yaml({"flag": True})
        self.assertEqual(result, "flag: true")


if __name__ == "__main__":
    unittest.main()
