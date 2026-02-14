"""Tests for quality_gate.py hook."""
import json
import os
import sys
import tempfile
import unittest

# Add the hook to path
HOOK_DIR = os.path.join(
    os.path.dirname(__file__),
    "..",
    "plugins",
    "hody-workflow",
    "hooks",
)
sys.path.insert(0, os.path.abspath(HOOK_DIR))

from quality_gate import (
    check_file,
    should_skip,
    run_quality_gate,
    SECRET_PATTERNS,
    SECURITY_PATTERNS,
)


class TestShouldSkip(unittest.TestCase):
    def test_skip_lock_files(self):
        self.assertTrue(should_skip("package-lock.json.lock"))
        self.assertTrue(should_skip("yarn.lock"))
        self.assertTrue(should_skip("go.sum"))

    def test_skip_minified(self):
        self.assertTrue(should_skip("bundle.min.js"))
        self.assertTrue(should_skip("styles.min.css"))

    def test_skip_binary(self):
        self.assertTrue(should_skip("logo.png"))
        self.assertTrue(should_skip("font.woff2"))
        self.assertTrue(should_skip("icon.svg"))

    def test_skip_node_modules(self):
        self.assertTrue(should_skip("node_modules/lodash/index.js"))

    def test_skip_vendor(self):
        self.assertTrue(should_skip("vendor/autoload.php"))

    def test_skip_dist(self):
        self.assertTrue(should_skip("dist/bundle.js"))

    def test_dont_skip_source(self):
        self.assertFalse(should_skip("src/auth.ts"))
        self.assertFalse(should_skip("main.py"))
        self.assertFalse(should_skip("server/handler.go"))

    def test_skip_map_files(self):
        self.assertTrue(should_skip("bundle.js.map"))


class TestCheckFile(unittest.TestCase):
    def _write_file(self, tmpdir, filename, content):
        fpath = os.path.join(tmpdir, filename)
        os.makedirs(os.path.dirname(fpath), exist_ok=True)
        with open(fpath, "w") as f:
            f.write(content)
        return filename

    def test_clean_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fname = self._write_file(tmpdir, "clean.ts", "const x = 42;\nexport default x;\n")
            issues = check_file(tmpdir, fname)
            self.assertEqual(issues, [])

    def test_hardcoded_api_key(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fname = self._write_file(
                tmpdir, "config.ts",
                'const API_KEY = "abcdef1234567890abcdef";\n'
            )
            issues = check_file(tmpdir, fname)
            self.assertTrue(any("API key" in i for i in issues))

    def test_hardcoded_password(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fname = self._write_file(
                tmpdir, "db.py",
                'password = "supersecretpassword123"\n'
            )
            issues = check_file(tmpdir, fname)
            self.assertTrue(any("secret" in i.lower() or "password" in i.lower() for i in issues))

    def test_aws_key(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fname = self._write_file(
                tmpdir, "config.js",
                'const key = "AKIAIOSFODNN7EXAMPLE";\n'
            )
            issues = check_file(tmpdir, fname)
            self.assertTrue(any("AWS" in i for i in issues))

    def test_private_key(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fname = self._write_file(
                tmpdir, "key.pem",
                '-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBg...\n'
            )
            issues = check_file(tmpdir, fname)
            self.assertTrue(any("Private key" in i for i in issues))

    def test_eval_usage(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fname = self._write_file(
                tmpdir, "handler.js",
                'const result = eval(userInput);\n'
            )
            issues = check_file(tmpdir, fname)
            self.assertTrue(any("eval" in i for i in issues))

    def test_innerhtml(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fname = self._write_file(
                tmpdir, "component.js",
                'el.innerHTML = userContent;\n'
            )
            issues = check_file(tmpdir, fname)
            self.assertTrue(any("innerHTML" in i for i in issues))

    def test_security_skipped_in_test_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fname = self._write_file(
                tmpdir, "handler.test.js",
                'const result = eval("2+2");\n'
            )
            issues = check_file(tmpdir, fname)
            # Security patterns should be skipped in test files
            self.assertFalse(any("eval" in i for i in issues))

    def test_large_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fname = self._write_file(
                tmpdir, "big.json",
                "x" * (600 * 1024)
            )
            issues = check_file(tmpdir, fname)
            self.assertTrue(any("Large file" in i for i in issues))

    def test_nonexistent_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            issues = check_file(tmpdir, "nonexistent.ts")
            self.assertEqual(issues, [])


class TestRunQualityGate(unittest.TestCase):
    def test_no_hody_dir_passes(self):
        """Quality gate should pass when there are no staged files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # run_quality_gate calls get_staged_files which needs git
            # Without a git repo, staged files list is empty → pass
            passed, report = run_quality_gate(tmpdir)
            self.assertTrue(passed)
            self.assertIn("No staged files", report)


if __name__ == "__main__":
    unittest.main()
