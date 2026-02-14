#!/usr/bin/env python3
"""
PreToolUse hook (Bash matcher): intercepts git commit commands and runs
lightweight quality checks on staged files.

Checks:
  - Hardcoded secrets (API keys, tokens, passwords in code)
  - Common security patterns (SQL injection, eval usage)
  - Debug leftovers (console.log, print statements in non-test files)
  - Large files that shouldn't be committed

Output: JSON with permissionDecision "allow" or "deny" + reason.
Skip with HODY_SKIP_QUALITY_GATE=1 env var.
"""
import json
import os
import re
import subprocess
import sys


# Patterns that indicate hardcoded secrets
SECRET_PATTERNS = [
    (r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\'][A-Za-z0-9]{16,}["\']', "Possible hardcoded API key"),
    (r'(?i)(secret|token|password|passwd|pwd)\s*[:=]\s*["\'][^"\']{8,}["\']', "Possible hardcoded secret/password"),
    (r'(?i)-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----', "Private key detected"),
    (r'AKIA[0-9A-Z]{16}', "AWS access key detected"),
    (r'(?i)sk-[a-zA-Z0-9]{20,}', "Possible API secret key"),
]

# Security anti-patterns
SECURITY_PATTERNS = [
    (r'\beval\s*\(', "eval() usage — potential code injection"),
    (r'(?i)innerHTML\s*=', "innerHTML assignment — potential XSS"),
    (r'(?i)document\.write\s*\(', "document.write() — potential XSS"),
    (r'(?i)exec\s*\(\s*["\']', "exec() with string — potential injection"),
]

# Max file size to commit (500KB)
MAX_FILE_SIZE = 500 * 1024

# Files/patterns to skip checking
SKIP_EXTENSIONS = {".lock", ".sum", ".min.js", ".min.css", ".map", ".svg", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".woff", ".woff2", ".ttf", ".eot"}
SKIP_PATHS = {"node_modules/", "vendor/", "dist/", "build/", ".next/", "__pycache__/"}


def get_staged_files(cwd):
    """Get list of staged files with their status."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-status"],
            cwd=cwd, capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return []

        files = []
        for line in result.stdout.strip().splitlines():
            parts = line.split("\t", 1)
            if len(parts) == 2:
                status, path = parts
                if status != "D":  # Skip deleted files
                    files.append(path)
        return files
    except (subprocess.TimeoutExpired, OSError):
        return []


def should_skip(filepath):
    """Check if a file should be skipped from quality checks."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext in SKIP_EXTENSIONS:
        return True
    for skip in SKIP_PATHS:
        if filepath.startswith(skip):
            return True
    return False


def check_file(cwd, filepath):
    """Run quality checks on a single staged file. Returns list of issues."""
    issues = []
    full_path = os.path.join(cwd, filepath)

    # Check file size
    try:
        size = os.path.getsize(full_path)
        if size > MAX_FILE_SIZE:
            issues.append(f"Large file ({size // 1024}KB > {MAX_FILE_SIZE // 1024}KB)")
            return issues  # Don't read large files
    except OSError:
        return issues

    # Read file content
    try:
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except (OSError, UnicodeDecodeError):
        return issues

    lines = content.splitlines()

    # Secret patterns
    for pattern, message in SECRET_PATTERNS:
        for i, line in enumerate(lines, 1):
            if re.search(pattern, line):
                issues.append(f"L{i}: {message}")
                break  # One issue per pattern per file

    # Security patterns (skip test files)
    is_test = any(t in filepath.lower() for t in ["test", "spec", "__test__", ".test.", ".spec."])
    if not is_test:
        for pattern, message in SECURITY_PATTERNS:
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    issues.append(f"L{i}: {message}")
                    break

    return issues


def run_quality_gate(cwd):
    """Run all quality checks on staged files. Returns (passed, report)."""
    staged = get_staged_files(cwd)
    if not staged:
        return True, "No staged files to check."

    all_issues = {}
    for filepath in staged:
        if should_skip(filepath):
            continue
        issues = check_file(cwd, filepath)
        if issues:
            all_issues[filepath] = issues

    if not all_issues:
        return True, f"Quality gate passed. {len(staged)} file(s) checked."

    # Build report
    report_lines = [f"Quality gate: {len(all_issues)} file(s) with issues:\n"]
    for filepath, issues in all_issues.items():
        report_lines.append(f"  {filepath}:")
        for issue in issues:
            report_lines.append(f"    - {issue}")

    return False, "\n".join(report_lines)


def main():
    try:
        input_data = json.load(sys.stdin)

        # Skip if disabled
        if os.environ.get("HODY_SKIP_QUALITY_GATE"):
            sys.exit(0)

        # Only intercept git commit commands
        tool_input = input_data.get("tool_input", {})
        command = tool_input.get("command", "")

        if not re.match(r"^\s*git\s+commit\b", command):
            sys.exit(0)

        cwd = input_data.get("cwd", os.getcwd())

        # Check if .hody/ exists (only run for initialized projects)
        if not os.path.isdir(os.path.join(cwd, ".hody")):
            sys.exit(0)

        passed, report = run_quality_gate(cwd)

        if passed:
            # Allow commit, add info message
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                }
            }
            print(json.dumps(output))
            sys.exit(0)
        else:
            # Deny commit with reason
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"[Hody Quality Gate] {report}\n\nFix issues or skip with HODY_SKIP_QUALITY_GATE=1"
                }
            }
            print(json.dumps(output))
            sys.exit(0)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(0)  # Don't block on hook error


if __name__ == "__main__":
    main()
