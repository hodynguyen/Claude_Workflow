#!/usr/bin/env python3
"""
Automated Graphify setup for any project.

Finds a suitable Python >= 3.10, installs graphifyy, builds the knowledge
graph, configures the MCP server, and updates profile.yaml + .gitignore.

Usage:
    python3 graphify_setup.py [--cwd <path>]
"""
import argparse
import json
import os
import re
import subprocess
import sys


# ---------------------------------------------------------------------------
# Step 1: Find Python >= 3.10
# ---------------------------------------------------------------------------

# Candidate interpreter names, highest version first.
_CANDIDATE_NAMES = [
    "python3.13",
    "python3.12",
    "python3.11",
    "python3.10",
]

# Extra directories to search (macOS Homebrew, /usr/local).
_EXTRA_DIRS = [
    "/opt/homebrew/bin",
    "/usr/local/bin",
]


def _which(name):
    """Return absolute path if *name* is on PATH, else None."""
    try:
        result = subprocess.run(
            ["which", name],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def _python_version(path):
    """Return (major, minor) for the interpreter at *path*, or None."""
    try:
        result = subprocess.run(
            [path, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        text = (result.stdout + result.stderr).strip()
        m = re.search(r"(\d+)\.(\d+)\.\d+", text)
        if m:
            return (int(m.group(1)), int(m.group(2)))
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def find_python(min_version=(3, 10)):
    """Return the path to the first Python interpreter >= *min_version*.

    Search order:
      1. Versioned names on PATH (python3.13 .. python3.10)
      2. Same names in common Homebrew / /usr/local dirs
      3. Fallback to ``python3`` if its version qualifies
    """
    # 1. Versioned names via which
    for name in _CANDIDATE_NAMES:
        path = _which(name)
        if path:
            ver = _python_version(path)
            if ver and ver >= min_version:
                return path

    # 2. Versioned names in extra directories
    for directory in _EXTRA_DIRS:
        for name in _CANDIDATE_NAMES:
            path = os.path.join(directory, name)
            if os.path.isfile(path) and os.access(path, os.X_OK):
                ver = _python_version(path)
                if ver and ver >= min_version:
                    return path

    # 3. Fallback to generic python3
    path = _which("python3")
    if path:
        ver = _python_version(path)
        if ver and ver >= min_version:
            return path

    return None


# ---------------------------------------------------------------------------
# Step 2: Ensure graphifyy is installed
# ---------------------------------------------------------------------------


def ensure_graphify(python_path):
    """Make sure ``import graphify`` works under *python_path*.

    Attempts pip install if the package is missing.  Returns True on
    success, False on failure (with a message printed to stderr).
    """
    if _can_import_graphify(python_path):
        return True

    # Try normal pip install
    print("Installing graphifyy...")
    rc = _pip_install(python_path, extra_flags=[])
    if rc == 0 and _can_import_graphify(python_path):
        return True

    # PEP 668 externally-managed fallback
    rc = _pip_install(python_path, extra_flags=["--break-system-packages"])
    if rc == 0 and _can_import_graphify(python_path):
        return True

    print(
        "ERROR: Could not install graphifyy.\n"
        "Please install it manually:\n"
        "  %s -m pip install graphifyy\n" % python_path,
        file=sys.stderr,
    )
    return False


def _can_import_graphify(python_path):
    try:
        result = subprocess.run(
            [python_path, "-c", "import graphify"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _pip_install(python_path, extra_flags):
    try:
        result = subprocess.run(
            [python_path, "-m", "pip", "install", "graphifyy", "-q"]
            + extra_flags,
            capture_output=True,
            text=True,
            timeout=120,
        )
        return result.returncode
    except (OSError, subprocess.TimeoutExpired):
        return 1


# ---------------------------------------------------------------------------
# Step 3: Build the knowledge graph
# ---------------------------------------------------------------------------

_BUILD_SCRIPT = """\
import json, sys
from pathlib import Path
from graphify.detect import detect
from graphify.extract import extract
from graphify.build import build
from networkx.readwrite import json_graph

cwd = Path(sys.argv[1])
result = detect(cwd)
code_files = [Path(f) for f in result['files']['code']]
ast = extract(code_files)
G = build([ast], directed=True)
data = json_graph.node_link_data(G)
# Ensure "links" key for graphify CLI compatibility
if 'edges' in data and 'links' not in data:
    data['links'] = data.pop('edges')
out = cwd / 'graphify-out'
out.mkdir(exist_ok=True)
with open(out / 'graph.json', 'w') as f:
    json.dump(data, f)
print(json.dumps({"nodes": G.number_of_nodes(), "edges": G.number_of_edges()}))
"""


def build_graph(python_path, cwd):
    """Build the Graphify knowledge graph.  Returns (nodes, edges) or None."""
    try:
        result = subprocess.run(
            [python_path, "-c", _BUILD_SCRIPT, cwd],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            print("ERROR: Graph build failed:\n" + result.stderr, file=sys.stderr)
            return None
        info = json.loads(result.stdout.strip())
        return info["nodes"], info["edges"]
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError, KeyError) as exc:
        print("ERROR: Graph build failed: %s" % exc, file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Step 4: Configure MCP server in .claude/settings.json
# ---------------------------------------------------------------------------


def update_claude_settings(cwd, python_path):
    """Add or update the graphify MCP server entry in .claude/settings.json."""
    settings_dir = os.path.join(cwd, ".claude")
    settings_path = os.path.join(settings_dir, "settings.json")

    settings = {}
    if os.path.isfile(settings_path):
        try:
            with open(settings_path, "r") as f:
                settings = json.load(f)
        except (json.JSONDecodeError, OSError):
            settings = {}

    if "mcpServers" not in settings:
        settings["mcpServers"] = {}

    settings["mcpServers"]["graphify"] = {
        "command": python_path,
        "args": ["-m", "graphify.serve", "graphify-out/graph.json"],
    }

    os.makedirs(settings_dir, exist_ok=True)
    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")

    print("MCP server configured in .claude/settings.json")


# ---------------------------------------------------------------------------
# Step 5: Update profile.yaml
# ---------------------------------------------------------------------------


def update_profile_yaml(cwd):
    """Ensure ``integrations.graphify: true`` in .hody/profile.yaml."""
    path = os.path.join(cwd, ".hody", "profile.yaml")
    if not os.path.isfile(path):
        print("WARNING: .hody/profile.yaml not found, skipping profile update.")
        return

    with open(path, "r") as f:
        content = f.read()

    # Case 1: graphify already set to true
    if re.search(r"^\s*graphify:\s*true\s*$", content, re.MULTILINE):
        print("Updated .hody/profile.yaml")
        return

    # Case 2: graphify line exists but set to false or other value
    new_content, count = re.subn(
        r"^(\s*)graphify:\s*\S+",
        r"\1graphify: true",
        content,
        count=1,
        flags=re.MULTILINE,
    )
    if count > 0:
        with open(path, "w") as f:
            f.write(new_content)
        print("Updated .hody/profile.yaml")
        return

    # Case 3: integrations section exists but no graphify line
    if re.search(r"^integrations:\s*$", content, re.MULTILINE):
        new_content = re.sub(
            r"^(integrations:\s*\n)",
            r"\1  graphify: true\n",
            content,
            count=1,
            flags=re.MULTILINE,
        )
        with open(path, "w") as f:
            f.write(new_content)
        print("Updated .hody/profile.yaml")
        return

    # Case 4: no integrations section at all
    addition = "\nintegrations:\n  graphify: true\n"
    with open(path, "a") as f:
        f.write(addition)
    print("Updated .hody/profile.yaml")


# ---------------------------------------------------------------------------
# Step 6: Update .gitignore
# ---------------------------------------------------------------------------


def update_gitignore(cwd):
    """Ensure ``graphify-out/`` is listed in .gitignore."""
    path = os.path.join(cwd, ".gitignore")

    if os.path.isfile(path):
        with open(path, "r") as f:
            content = f.read()
        if re.search(r"(^|\n)graphify-out/?(\s|$)", content):
            print("Updated .gitignore")
            return
        # Ensure trailing newline before appending
        if content and not content.endswith("\n"):
            content += "\n"
        with open(path, "w") as f:
            f.write(content + "graphify-out/\n")
    else:
        with open(path, "w") as f:
            f.write("graphify-out/\n")

    print("Updated .gitignore")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Automated Graphify setup")
    parser.add_argument("--cwd", default=".", help="Project root directory")
    args = parser.parse_args()

    cwd = os.path.abspath(args.cwd)
    if not os.path.isdir(cwd):
        print("ERROR: Directory does not exist: %s" % cwd, file=sys.stderr)
        sys.exit(1)

    # Step 1: Find Python >= 3.10
    print("Finding Python >= 3.10...")
    python_path = find_python()
    if not python_path:
        print(
            "ERROR: Python >= 3.10 not found.\n"
            "Install via pyenv, Homebrew (brew install python@3.13), "
            "or your system package manager.",
            file=sys.stderr,
        )
        sys.exit(1)
    print("Using: %s" % python_path)

    # Step 2: Ensure graphifyy is installed
    if not ensure_graphify(python_path):
        sys.exit(1)

    # Step 3: Build the knowledge graph
    print("Building knowledge graph...")
    result = build_graph(python_path, cwd)
    if result is None:
        sys.exit(1)
    nodes, edges = result
    print("Graph built: %d nodes, %d edges" % (nodes, edges))

    # Step 4: Configure MCP server
    update_claude_settings(cwd, python_path)

    # Step 5: Update profile.yaml
    update_profile_yaml(cwd)

    # Step 6: Update .gitignore
    update_gitignore(cwd)

    # Step 7: Summary
    print("")
    print("Graphify setup complete!")
    print("  Graph: %d nodes, %d edges" % (nodes, edges))
    print("  MCP: .claude/settings.json configured")
    print("  Profile: integrations.graphify = true")
    print("")
    print("WARNING: Restart Claude Code to activate the MCP server.")


if __name__ == "__main__":
    main()
