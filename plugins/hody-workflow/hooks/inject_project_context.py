#!/usr/bin/env python3
"""
SessionStart hook: reads .hody/profile.yaml and injects project context
into the system message so all agents know the current tech stack.

Auto-refresh: if any config file is newer than profile.yaml, re-runs
detect_stack.py before injecting context.
"""
import json
import subprocess
import sys
import os


# Config files that trigger a profile refresh when modified
CONFIG_FILES = [
    "package.json",
    "go.mod",
    "requirements.txt",
    "pyproject.toml",
    "Pipfile",
    "setup.py",
    "Cargo.toml",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "Gemfile",
    "composer.json",
    "nx.json",
    "turbo.json",
    "lerna.json",
    "pnpm-workspace.yaml",
    "global.json",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    ".gitlab-ci.yml",
    "Jenkinsfile",
]


def is_profile_stale(cwd, profile_path):
    """Check if any config file is newer than profile.yaml."""
    try:
        profile_mtime = os.path.getmtime(profile_path)
    except OSError:
        return False

    for fname in CONFIG_FILES:
        fpath = os.path.join(cwd, fname)
        try:
            if os.path.getmtime(fpath) > profile_mtime:
                return True
        except OSError:
            continue

    # Check for .csproj and .sln files (glob pattern)
    try:
        for f in os.listdir(cwd):
            if f.endswith((".csproj", ".sln", ".tf")):
                if os.path.getmtime(os.path.join(cwd, f)) > profile_mtime:
                    return True
    except OSError:
        pass

    # Check .github/workflows/ directory
    workflows_dir = os.path.join(cwd, ".github", "workflows")
    try:
        if os.path.isdir(workflows_dir):
            for f in os.listdir(workflows_dir):
                fpath = os.path.join(workflows_dir, f)
                if os.path.getmtime(fpath) > profile_mtime:
                    return True
    except OSError:
        pass

    return False


def refresh_profile(cwd):
    """Re-run detect_stack.py to update profile.yaml."""
    # Derive detect_stack.py path from this script's location
    hook_dir = os.path.dirname(os.path.abspath(__file__))
    plugin_root = os.path.dirname(hook_dir)
    detect_script = os.path.join(
        plugin_root, "skills", "project-profile", "scripts", "detect_stack.py"
    )

    if not os.path.isfile(detect_script):
        return False

    try:
        subprocess.run(
            [sys.executable, detect_script, "--cwd", cwd],
            timeout=15,
            capture_output=True,
        )
        return True
    except (subprocess.TimeoutExpired, OSError):
        return False


def main():
    try:
        input_data = json.load(sys.stdin)
        cwd = input_data.get("cwd", os.getcwd())

        profile_path = os.path.join(cwd, ".hody", "profile.yaml")
        if not os.path.isfile(profile_path):
            print("{}")
            sys.exit(0)

        # Auto-refresh if config files changed (skip with HODY_SKIP_REFRESH=1)
        if not os.environ.get("HODY_SKIP_REFRESH"):
            if is_profile_stale(cwd, profile_path):
                refresh_profile(cwd)

        with open(profile_path, "r") as f:
            profile_content = f.read()

        # Extract key info for a concise summary
        lines = profile_content.strip().splitlines()
        summary_parts = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("name:"):
                summary_parts.append(stripped)
            elif stripped.startswith("framework:"):
                summary_parts.append(stripped)
            elif stripped.startswith("language:"):
                summary_parts.append(stripped)
            elif stripped.startswith("database:"):
                summary_parts.append(stripped)
            elif stripped.startswith("ci:"):
                summary_parts.append(stripped)

        summary = " | ".join(summary_parts) if summary_parts else "profile loaded"

        system_msg = f"[Hody Workflow] Project: {summary}. Full profile at .hody/profile.yaml"

        # Inject active workflow state if present
        state_path = os.path.join(cwd, ".hody", "state.json")
        if os.path.isfile(state_path):
            try:
                with open(state_path, "r") as sf:
                    state = json.load(sf)
                if state.get("status") == "in_progress":
                    feature = state.get("feature", "unknown")
                    # Find next agent
                    next_info = None
                    for phase in state.get("phase_order", []):
                        p = state.get("phases", {}).get(phase, {})
                        for agent in p.get("agents", []):
                            if (agent not in p.get("completed", [])
                                    and agent not in p.get("skipped", [])):
                                next_info = (phase, agent)
                                break
                        if next_info:
                            break
                    if next_info:
                        system_msg += (
                            f" | Active workflow: '{feature}'"
                            f" — next: {next_info[1]} ({next_info[0]} phase)"
                            f". Use /hody-workflow:resume to continue."
                        )
                    else:
                        system_msg += (
                            f" | Active workflow: '{feature}'"
                            f" — all agents done, ready to complete."
                        )
            except (json.JSONDecodeError, KeyError):
                pass  # Don't block on corrupt state file

        output = {"systemMessage": system_msg}
        print(json.dumps(output))
        sys.exit(0)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(0)  # Don't block session on hook error


if __name__ == "__main__":
    main()
