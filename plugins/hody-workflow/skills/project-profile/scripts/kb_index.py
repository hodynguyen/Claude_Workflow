"""
Knowledge Base index builder for Hody Workflow.

Parses YAML frontmatter from KB markdown files and builds
`.hody/knowledge/_index.json` for fast tag/date/agent searching.

The index is a generated cache — it can always be rebuilt from the .md files.
"""
import json
import os
import re
from datetime import datetime, timezone


def parse_frontmatter(content):
    """Parse YAML frontmatter from markdown content.

    Returns (frontmatter_dict, body) tuple.
    If no frontmatter found, returns (None, content).
    """
    # Match --- delimited frontmatter at the start of content
    match = re.match(r"^---\s*\n(.*?)---\s*\n?(.*)", content, re.DOTALL)
    if not match:
        return None, content

    fm_text = match.group(1)
    body = match.group(2)

    # Simple YAML-like parsing (stdlib only, no PyYAML dependency)
    fm = {}
    for line in fm_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()

        # Parse list values: [item1, item2, item3]
        if value.startswith("[") and value.endswith("]"):
            items = value[1:-1]
            fm[key] = [i.strip().strip("\"'") for i in items.split(",") if i.strip()]
        # Parse null
        elif value.lower() in ("null", "~", ""):
            fm[key] = None
        # Parse booleans
        elif value.lower() in ("true", "yes"):
            fm[key] = True
        elif value.lower() in ("false", "no"):
            fm[key] = False
        else:
            # Strip quotes
            fm[key] = value.strip("\"'")

    return fm, body


def extract_sections(content):
    """Extract ## heading sections from markdown content.

    Returns list of dicts with 'heading', 'level', 'line_number', 'line_count'.
    """
    sections = []
    lines = content.splitlines()

    for i, line in enumerate(lines):
        match = re.match(r"^(#{1,4})\s+(.+)", line)
        if match:
            sections.append({
                "heading": match.group(2).strip(),
                "level": len(match.group(1)),
                "line_number": i + 1,
            })

    # Calculate line counts
    for i, section in enumerate(sections):
        if i + 1 < len(sections):
            section["line_count"] = sections[i + 1]["line_number"] - section["line_number"]
        else:
            section["line_count"] = len(lines) - section["line_number"] + 1

    return sections


def build_file_entry(filepath):
    """Build an index entry for a single KB file.

    Returns dict with file metadata, frontmatter fields, and sections.
    """
    try:
        with open(filepath, "r") as f:
            content = f.read()
    except OSError:
        return None

    filename = os.path.basename(filepath)
    fm, body = parse_frontmatter(content)
    sections = extract_sections(body if fm else content)
    total_lines = len(content.splitlines())

    entry = {
        "file": filename,
        "total_lines": total_lines,
        "has_frontmatter": fm is not None,
        "tags": [],
        "author_agent": None,
        "created": None,
        "status": "active",
        "supersedes": None,
        "sections": [
            {"heading": s["heading"], "level": s["level"], "line": s["line_number"]}
            for s in sections
        ],
    }

    if fm:
        entry["tags"] = fm.get("tags", []) or []
        entry["author_agent"] = fm.get("author_agent")
        entry["created"] = fm.get("created")
        entry["status"] = fm.get("status", "active")
        entry["supersedes"] = fm.get("supersedes")

    return entry


def build_index(kb_dir):
    """Build the full index from all .md files in the KB directory.

    Returns the index dict. Skips _index.json and archive/ directory.
    """
    entries = []

    if not os.path.isdir(kb_dir):
        return {"version": 1, "built_at": _now(), "entries": []}

    for fname in sorted(os.listdir(kb_dir)):
        if not fname.endswith(".md"):
            continue
        fpath = os.path.join(kb_dir, fname)
        if not os.path.isfile(fpath):
            continue
        entry = build_file_entry(fpath)
        if entry:
            entries.append(entry)

    return {
        "version": 1,
        "built_at": _now(),
        "entries": entries,
    }


def write_index(kb_dir):
    """Build and write _index.json to the KB directory.

    Returns the index dict.
    """
    index = build_index(kb_dir)
    index_path = os.path.join(kb_dir, "_index.json")
    os.makedirs(kb_dir, exist_ok=True)
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)
    return index


def load_index(kb_dir):
    """Load _index.json from KB directory. Returns None if not found."""
    index_path = os.path.join(kb_dir, "_index.json")
    if not os.path.isfile(index_path):
        return None
    with open(index_path, "r") as f:
        return json.load(f)


def search_index(index, tag=None, agent=None, status=None):
    """Search the index by tag, author_agent, or status.

    Returns list of matching entries.
    """
    if index is None:
        return []

    results = []
    for entry in index.get("entries", []):
        if tag and tag.lower() not in [t.lower() for t in entry.get("tags", [])]:
            continue
        if agent and entry.get("author_agent") != agent:
            continue
        if status and entry.get("status") != status:
            continue
        results.append(entry)

    return results


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
