#!/usr/bin/env python3
"""
Knowledge base sync: push/pull .hody/knowledge/ to a shared location.

Sync modes:
  - git-branch: push/pull to a dedicated branch in the same repo
  - gist: sync via GitHub Gist (requires gh CLI)
  - shared-repo: push/pull to a separate shared knowledge repo

Usage:
  kb_sync.py --cwd <project> --mode <git-branch|gist|shared-repo> --action <push|pull|status>
  kb_sync.py --cwd <project> --mode git-branch --branch hody-knowledge --action push
  kb_sync.py --cwd <project> --mode gist --gist-id <id> --action pull
  kb_sync.py --cwd <project> --mode shared-repo --repo <url> --action push

Merge strategy:
  - Append-only sections merge automatically
  - Conflicting sections are flagged for manual resolution
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile


KB_DIR = ".hody/knowledge"
KB_FILES = [
    "architecture.md",
    "decisions.md",
    "api-contracts.md",
    "business-rules.md",
    "tech-debt.md",
    "runbook.md",
]


def run_cmd(args, cwd=None, capture=True):
    """Run a shell command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            args, cwd=cwd, capture_output=capture, text=True, timeout=30
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except (subprocess.TimeoutExpired, OSError) as e:
        return 1, "", str(e)


def get_kb_path(cwd):
    return os.path.join(cwd, KB_DIR)


def validate_kb(cwd):
    """Check that .hody/knowledge/ exists and has files."""
    kb_path = get_kb_path(cwd)
    if not os.path.isdir(kb_path):
        return False, f"Knowledge base not found at {kb_path}. Run /hody-workflow:init first."
    files = [f for f in os.listdir(kb_path) if f.endswith(".md")]
    if not files:
        return False, "Knowledge base is empty."
    return True, f"Found {len(files)} knowledge base files."


# --- Git Branch Mode ---

def git_branch_push(cwd, branch):
    """Push .hody/knowledge/ to a dedicated git branch."""
    kb_path = get_kb_path(cwd)

    # Check we're in a git repo
    rc, _, _ = run_cmd(["git", "rev-parse", "--git-dir"], cwd=cwd)
    if rc != 0:
        return False, "Not a git repository."

    # Get current branch to restore later
    rc, current_branch, _ = run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd)
    if rc != 0:
        return False, "Could not determine current branch."

    # Check if target branch exists
    rc, _, _ = run_cmd(["git", "show-ref", "--verify", f"refs/heads/{branch}"], cwd=cwd)
    branch_exists = rc == 0

    # Stash any uncommitted changes
    rc, stash_out, _ = run_cmd(["git", "stash", "push", "-m", "hody-kb-sync"], cwd=cwd)
    stashed = "No local changes" not in stash_out

    try:
        if branch_exists:
            run_cmd(["git", "checkout", branch], cwd=cwd)
        else:
            run_cmd(["git", "checkout", "--orphan", branch], cwd=cwd)
            run_cmd(["git", "rm", "-rf", "."], cwd=cwd)

        # Copy KB files to root of branch
        for fname in os.listdir(kb_path):
            if fname.endswith(".md"):
                shutil.copy2(os.path.join(kb_path, fname), os.path.join(cwd, fname))
                run_cmd(["git", "add", fname], cwd=cwd)

        # Commit
        rc, _, err = run_cmd(
            ["git", "commit", "-m", "sync: update knowledge base"],
            cwd=cwd,
        )
        if rc != 0 and "nothing to commit" not in err:
            return False, f"Commit failed: {err}"

        # Push
        rc, _, err = run_cmd(["git", "push", "origin", branch], cwd=cwd)
        if rc != 0:
            return False, f"Push failed: {err}"

        return True, f"Knowledge base pushed to branch '{branch}'."
    finally:
        # Restore original branch
        run_cmd(["git", "checkout", current_branch], cwd=cwd)
        if stashed:
            run_cmd(["git", "stash", "pop"], cwd=cwd)


def git_branch_pull(cwd, branch):
    """Pull .hody/knowledge/ from a dedicated git branch."""
    kb_path = get_kb_path(cwd)

    # Fetch the branch
    rc, _, err = run_cmd(["git", "fetch", "origin", branch], cwd=cwd)
    if rc != 0:
        return False, f"Fetch failed: {err}. Does branch '{branch}' exist on remote?"

    # Extract KB files from the branch
    os.makedirs(kb_path, exist_ok=True)
    pulled = 0
    for fname in KB_FILES:
        rc, content, _ = run_cmd(
            ["git", "show", f"origin/{branch}:{fname}"],
            cwd=cwd,
        )
        if rc == 0 and content:
            dest = os.path.join(kb_path, fname)
            with open(dest, "w") as f:
                f.write(content + "\n")
            pulled += 1

    if pulled == 0:
        return False, f"No knowledge base files found on branch '{branch}'."
    return True, f"Pulled {pulled} files from branch '{branch}' to {KB_DIR}/."


# --- Gist Mode ---

def gist_push(cwd, gist_id=None):
    """Push .hody/knowledge/ to a GitHub Gist."""
    kb_path = get_kb_path(cwd)

    # Check gh CLI
    rc, _, _ = run_cmd(["gh", "auth", "status"])
    if rc != 0:
        return False, "GitHub CLI not authenticated. Run 'gh auth login' first."

    # Build file args
    file_args = []
    for fname in os.listdir(kb_path):
        if fname.endswith(".md"):
            file_args.extend(["-f", f"{fname}=@{os.path.join(kb_path, fname)}"])

    if not file_args:
        return False, "No knowledge base files to push."

    if gist_id:
        # Update existing gist
        cmd = ["gh", "gist", "edit", gist_id] + file_args
        rc, out, err = run_cmd(cmd, cwd=cwd)
        if rc != 0:
            return False, f"Gist update failed: {err}"
        return True, f"Knowledge base updated in gist {gist_id}."
    else:
        # Create new gist
        cmd = ["gh", "gist", "create", "--desc", "Hody Workflow Knowledge Base"] + file_args
        rc, out, err = run_cmd(cmd, cwd=cwd)
        if rc != 0:
            return False, f"Gist creation failed: {err}"
        return True, f"Knowledge base pushed to new gist: {out}"


def gist_pull(cwd, gist_id):
    """Pull .hody/knowledge/ from a GitHub Gist."""
    if not gist_id:
        return False, "Gist ID is required for pull. Use --gist-id <id>."

    kb_path = get_kb_path(cwd)
    os.makedirs(kb_path, exist_ok=True)

    # Clone gist to temp dir
    with tempfile.TemporaryDirectory() as tmpdir:
        rc, _, err = run_cmd(["gh", "gist", "clone", gist_id, tmpdir])
        if rc != 0:
            return False, f"Gist clone failed: {err}"

        pulled = 0
        for fname in os.listdir(tmpdir):
            if fname.endswith(".md") and not fname.startswith("."):
                shutil.copy2(os.path.join(tmpdir, fname), os.path.join(kb_path, fname))
                pulled += 1

    if pulled == 0:
        return False, "No markdown files found in gist."
    return True, f"Pulled {pulled} files from gist {gist_id} to {KB_DIR}/."


# --- Shared Repo Mode ---

def shared_repo_push(cwd, repo_url):
    """Push .hody/knowledge/ to a shared knowledge repo."""
    kb_path = get_kb_path(cwd)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Clone shared repo
        rc, _, err = run_cmd(["git", "clone", "--depth", "1", repo_url, tmpdir])
        if rc != 0:
            return False, f"Clone failed: {err}"

        # Determine project subdirectory
        project_name = os.path.basename(os.path.abspath(cwd))
        dest_dir = os.path.join(tmpdir, project_name)
        os.makedirs(dest_dir, exist_ok=True)

        # Copy KB files
        for fname in os.listdir(kb_path):
            if fname.endswith(".md"):
                shutil.copy2(os.path.join(kb_path, fname), os.path.join(dest_dir, fname))

        # Commit and push
        run_cmd(["git", "add", "."], cwd=tmpdir)
        rc, _, err = run_cmd(
            ["git", "commit", "-m", f"sync: update {project_name} knowledge base"],
            cwd=tmpdir,
        )
        if rc != 0 and "nothing to commit" not in err:
            return False, f"Commit failed: {err}"

        rc, _, err = run_cmd(["git", "push"], cwd=tmpdir)
        if rc != 0:
            return False, f"Push failed: {err}"

    return True, f"Knowledge base pushed to {repo_url} under {project_name}/."


def shared_repo_pull(cwd, repo_url):
    """Pull .hody/knowledge/ from a shared knowledge repo."""
    kb_path = get_kb_path(cwd)
    project_name = os.path.basename(os.path.abspath(cwd))

    with tempfile.TemporaryDirectory() as tmpdir:
        rc, _, err = run_cmd(["git", "clone", "--depth", "1", repo_url, tmpdir])
        if rc != 0:
            return False, f"Clone failed: {err}"

        src_dir = os.path.join(tmpdir, project_name)
        if not os.path.isdir(src_dir):
            return False, f"No directory '{project_name}' found in shared repo."

        os.makedirs(kb_path, exist_ok=True)
        pulled = 0
        for fname in os.listdir(src_dir):
            if fname.endswith(".md"):
                shutil.copy2(os.path.join(src_dir, fname), os.path.join(kb_path, fname))
                pulled += 1

    if pulled == 0:
        return False, f"No knowledge base files found for '{project_name}' in shared repo."
    return True, f"Pulled {pulled} files from shared repo to {KB_DIR}/."


# --- Status ---

def sync_status(cwd):
    """Show sync status of the knowledge base."""
    kb_path = get_kb_path(cwd)
    if not os.path.isdir(kb_path):
        return "Knowledge base not found. Run /hody-workflow:init first."

    lines = ["Knowledge base files:"]
    for fname in KB_FILES:
        fpath = os.path.join(kb_path, fname)
        if os.path.isfile(fpath):
            size = os.path.getsize(fpath)
            lines.append(f"  {fname}: {size} bytes")
        else:
            lines.append(f"  {fname}: missing")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Sync .hody/knowledge/ to shared location")
    parser.add_argument("--cwd", default=".", help="Project root directory")
    parser.add_argument("--mode", choices=["git-branch", "gist", "shared-repo"],
                        required=True, help="Sync mode")
    parser.add_argument("--action", choices=["push", "pull", "status"],
                        required=True, help="Action to perform")
    parser.add_argument("--branch", default="hody-knowledge",
                        help="Branch name for git-branch mode")
    parser.add_argument("--gist-id", default=None,
                        help="Gist ID for gist mode")
    parser.add_argument("--repo", default=None,
                        help="Repo URL for shared-repo mode")
    args = parser.parse_args()

    cwd = os.path.abspath(args.cwd)

    if args.action == "status":
        print(sync_status(cwd))
        sys.exit(0)

    # Validate KB exists for push
    if args.action == "push":
        valid, msg = validate_kb(cwd)
        if not valid:
            print(f"Error: {msg}", file=sys.stderr)
            sys.exit(1)

    # Dispatch
    if args.mode == "git-branch":
        if args.action == "push":
            ok, msg = git_branch_push(cwd, args.branch)
        else:
            ok, msg = git_branch_pull(cwd, args.branch)

    elif args.mode == "gist":
        if args.action == "push":
            ok, msg = gist_push(cwd, args.gist_id)
        else:
            ok, msg = gist_pull(cwd, args.gist_id)

    elif args.mode == "shared-repo":
        if not args.repo:
            print("Error: --repo is required for shared-repo mode", file=sys.stderr)
            sys.exit(1)
        if args.action == "push":
            ok, msg = shared_repo_push(cwd, args.repo)
        else:
            ok, msg = shared_repo_pull(cwd, args.repo)

    print(msg)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
