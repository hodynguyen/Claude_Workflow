"""
Knowledge Base auto-archival for Hody Workflow.

When a KB file exceeds a line threshold (default 500), moves older
sections to `.hody/knowledge/archive/`. Sections are identified by
## headings with optional frontmatter dates for ordering.
"""
import os
import re
import shutil
from datetime import datetime, timezone


DEFAULT_THRESHOLD = 500


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _split_into_sections(content):
    """Split markdown content into sections by ## headings.

    Returns list of (heading, text) tuples. The first tuple may have
    heading=None for content before the first ## heading (preamble).
    """
    lines = content.splitlines(keepends=True)
    sections = []
    current_heading = None
    current_lines = []

    for line in lines:
        match = re.match(r"^##\s+(.+)", line)
        if match:
            # Save previous section
            if current_heading is not None or current_lines:
                sections.append((current_heading, "".join(current_lines)))
            current_heading = match.group(1).strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    # Don't forget last section
    if current_heading is not None or current_lines:
        sections.append((current_heading, "".join(current_lines)))

    return sections


def _extract_date_from_section(text):
    """Try to extract a date from section content for ordering.

    Looks for frontmatter 'created:' or '**Date**:' patterns.
    Returns date string or None.
    """
    # Check for created: in frontmatter-like content
    match = re.search(r"(?:created|date|\*\*Date\*\*):\s*(\d{4}-\d{2}-\d{2})", text)
    if match:
        return match.group(1)
    return None


def check_file_needs_archival(filepath, threshold=DEFAULT_THRESHOLD):
    """Check if a KB file exceeds the line threshold.

    Returns (needs_archival, total_lines).
    """
    try:
        with open(filepath, "r") as f:
            lines = f.readlines()
        return len(lines) > threshold, len(lines)
    except OSError:
        return False, 0


def archive_file(filepath, archive_dir=None, threshold=DEFAULT_THRESHOLD, keep_sections=3):
    """Archive older sections from a KB file that exceeds the threshold.

    Keeps the preamble (content before first ## heading) and the most recent
    `keep_sections` sections. Moves older sections to archive/.

    Args:
        filepath: Path to the KB .md file.
        archive_dir: Archive directory. Defaults to sibling archive/ dir.
        threshold: Line count threshold to trigger archival.
        keep_sections: Number of recent sections to keep in the main file.

    Returns:
        dict with 'archived_sections', 'archive_file', 'remaining_lines'
        or None if no archival was needed.
    """
    needs_archival, total_lines = check_file_needs_archival(filepath, threshold)
    if not needs_archival:
        return None

    with open(filepath, "r") as f:
        content = f.read()

    sections = _split_into_sections(content)
    if len(sections) <= keep_sections + 1:  # +1 for preamble
        return None  # Not enough sections to archive

    # Separate preamble from content sections
    preamble = None
    content_sections = []
    for heading, text in sections:
        if heading is None:
            preamble = text
        else:
            content_sections.append((heading, text))

    if len(content_sections) <= keep_sections:
        return None

    # Sort sections by date if possible, otherwise keep original order
    # Older sections (earlier in file or earlier dates) get archived
    sections_to_archive = content_sections[:-keep_sections]
    sections_to_keep = content_sections[-keep_sections:]

    # Set up archive directory
    if archive_dir is None:
        archive_dir = os.path.join(os.path.dirname(filepath), "archive")
    os.makedirs(archive_dir, exist_ok=True)

    # Write archived sections
    filename = os.path.basename(filepath)
    name_base = os.path.splitext(filename)[0]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    archive_filename = f"{name_base}-archive-{timestamp}.md"
    archive_path = os.path.join(archive_dir, archive_filename)

    archive_content = f"# Archived sections from {filename}\n"
    archive_content += f"# Archived at: {_now()}\n\n"
    for heading, text in sections_to_archive:
        archive_content += text
        if not text.endswith("\n"):
            archive_content += "\n"

    with open(archive_path, "w") as f:
        f.write(archive_content)

    # Rewrite main file with preamble + kept sections
    new_content = ""
    if preamble:
        new_content += preamble
        if not preamble.endswith("\n"):
            new_content += "\n"

    for heading, text in sections_to_keep:
        new_content += text
        if not text.endswith("\n"):
            new_content += "\n"

    with open(filepath, "w") as f:
        f.write(new_content)

    return {
        "archived_sections": len(sections_to_archive),
        "archive_file": archive_path,
        "remaining_lines": len(new_content.splitlines()),
    }


def check_all_kb_files(kb_dir, threshold=DEFAULT_THRESHOLD):
    """Check all KB files and archive any that exceed the threshold.

    Returns list of archive results (one per file that was archived).
    """
    results = []
    if not os.path.isdir(kb_dir):
        return results

    archive_dir = os.path.join(kb_dir, "archive")

    for fname in sorted(os.listdir(kb_dir)):
        if not fname.endswith(".md"):
            continue
        fpath = os.path.join(kb_dir, fname)
        if not os.path.isfile(fpath):
            continue

        result = archive_file(fpath, archive_dir=archive_dir, threshold=threshold)
        if result:
            result["source_file"] = fname
            results.append(result)

    return results
