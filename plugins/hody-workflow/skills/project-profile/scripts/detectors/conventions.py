"""Detect project conventions."""
import os


def detect_conventions(cwd):
    """Detect project conventions."""
    conventions = {}

    if os.path.isfile(os.path.join(cwd, ".github", "PULL_REQUEST_TEMPLATE.md")):
        conventions["pr_template"] = True

    return conventions if conventions else None
