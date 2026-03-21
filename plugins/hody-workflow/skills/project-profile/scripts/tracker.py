"""
Core CRUD operations, queries, workflow sync, and CLI entry point
for the Interaction Tracking system.

Uses tracker_schema for database access, schema init, ID generation,
transition validation, and migration from state.json.
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone

# Handle both package and direct imports
try:
    from . import tracker_schema as schema
except ImportError:
    import tracker_schema as schema


# =====================================================================
# Terminal states per type (for completed_at logic)
# =====================================================================

TERMINAL_STATES = {
    "task":          {"completed", "abandoned"},
    "investigation": {"concluded", "abandoned"},
    "question":      {"answered"},
    "discussion":    {"resolved"},
    "maintenance":   {"completed", "abandoned"},
}

# Priority ordering for queries (higher number = higher priority)
PRIORITY_ORDER = {"high": 3, "medium": 2, "low": 1}


# =====================================================================
# Helpers
# =====================================================================

def _now():
    """Return current UTC timestamp as ISO string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _item_to_dict(conn, item_row):
    """Convert sqlite3.Row to dict, including tags, files, kb_refs."""
    d = dict(item_row)

    # Parse extra JSON
    if d.get("extra"):
        try:
            d["extra"] = json.loads(d["extra"])
        except (json.JSONDecodeError, TypeError):
            d["extra"] = {}
    else:
        d["extra"] = {}

    item_id = d["id"]

    # Fetch tags
    rows = conn.execute(
        "SELECT tag FROM item_tags WHERE item_id = ?", (item_id,)
    ).fetchall()
    d["tags"] = [r["tag"] for r in rows]

    # Fetch related files
    rows = conn.execute(
        "SELECT filepath FROM item_files WHERE item_id = ?", (item_id,)
    ).fetchall()
    d["related_files"] = [r["filepath"] for r in rows]

    # Fetch KB refs
    rows = conn.execute(
        "SELECT kb_ref FROM item_kb_refs WHERE item_id = ?", (item_id,)
    ).fetchall()
    d["kb_refs"] = [r["kb_ref"] for r in rows]

    return d


# =====================================================================
# Sessions
# =====================================================================

def ensure_session(cwd):
    """Create new session or return current one (same date).

    If a session for today already exists and has not been ended,
    returns that session ID. Otherwise creates a new session.

    Returns:
        session_id string (ses_YYYYMMDD_NNN).
    """
    schema.init_db(cwd)
    conn = schema.get_db(cwd)
    now = _now()
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    prefix = f"ses_{today}_"

    # Look for an open session today (no ended_at)
    row = conn.execute(
        "SELECT id FROM sessions WHERE id LIKE ? AND ended_at IS NULL",
        (f"{prefix}%",)
    ).fetchone()

    if row:
        session_id = row["id"]
        conn.close()
        return session_id

    # Create new session
    session_id = schema.generate_session_id(cwd)
    conn.execute(
        "INSERT INTO sessions (id, started_at) VALUES (?, ?)",
        (session_id, now)
    )
    conn.commit()
    conn.close()
    return session_id


def end_session(cwd, session_id, summary=""):
    """Mark session as ended."""
    conn = schema.get_db(cwd)
    now = _now()
    conn.execute(
        "UPDATE sessions SET ended_at = ?, summary = ? WHERE id = ?",
        (now, summary, session_id)
    )
    conn.commit()
    conn.close()


# =====================================================================
# Items: CRUD
# =====================================================================

def create_item(cwd, type, title, description="", priority="medium",
                tags=None, related_files=None, workflow_id=None, extra=None):
    """Create a new tracking item.

    Args:
        cwd: Project root directory.
        type: One of task, investigation, question, discussion, maintenance.
        title: Short title for the item.
        description: Longer description (optional).
        priority: high, medium, or low.
        tags: List of tag strings.
        related_files: List of file paths.
        workflow_id: Link to state.json workflow (for tasks).
        extra: Dict of type-specific metadata.

    Returns:
        Full item dict with generated id.
    """
    schema.init_db(cwd)
    session_id = ensure_session(cwd)
    conn = schema.get_db(cwd)
    now = _now()

    item_id = schema.generate_item_id()
    initial_status = schema.INITIAL_STATUS.get(type)
    if initial_status is None:
        conn.close()
        raise ValueError(f"Invalid item type: {type}")

    extra_json = json.dumps(extra or {})

    conn.execute(
        """INSERT INTO items
           (id, type, title, description, status, priority,
            created_at, updated_at, completed_at, session_id,
            workflow_id, notes, extra)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (item_id, type, title, description, initial_status, priority,
         now, now, None, session_id, workflow_id, "", extra_json)
    )

    # Log initial status
    conn.execute(
        """INSERT INTO status_log
           (item_id, from_status, to_status, changed_at, session_id, reason)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (item_id, None, initial_status, now, session_id, "Item created")
    )

    # Insert tags
    if tags:
        for tag in tags:
            conn.execute(
                "INSERT OR IGNORE INTO item_tags (item_id, tag) VALUES (?, ?)",
                (item_id, tag)
            )

    # Insert related files
    if related_files:
        for fp in related_files:
            conn.execute(
                "INSERT OR IGNORE INTO item_files (item_id, filepath) VALUES (?, ?)",
                (item_id, fp)
            )

    conn.commit()

    # Read back full item
    row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    result = _item_to_dict(conn, row)
    conn.close()
    return result


def get_item(cwd, item_id):
    """Get item by ID with tags, files, kb_refs included.

    Returns:
        Item dict or None if not found.
    """
    conn = schema.get_db(cwd)
    row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    if row is None:
        conn.close()
        return None
    result = _item_to_dict(conn, row)
    conn.close()
    return result


def update_item(cwd, item_id, title=None, description=None, priority=None,
                notes=None, extra=None):
    """Partial update of item metadata.

    For extra, merges with existing extra dict rather than replacing.

    Returns:
        Updated item dict.

    Raises:
        ValueError if item not found.
    """
    conn = schema.get_db(cwd)
    row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    if row is None:
        conn.close()
        raise ValueError(f"Item not found: {item_id}")

    now = _now()
    updates = []
    params = []

    if title is not None:
        updates.append("title = ?")
        params.append(title)

    if description is not None:
        updates.append("description = ?")
        params.append(description)

    if priority is not None:
        updates.append("priority = ?")
        params.append(priority)

    if notes is not None:
        updates.append("notes = ?")
        params.append(notes)

    if extra is not None:
        # Merge with existing
        existing_extra = {}
        if row["extra"]:
            try:
                existing_extra = json.loads(row["extra"])
            except (json.JSONDecodeError, TypeError):
                pass
        existing_extra.update(extra)
        updates.append("extra = ?")
        params.append(json.dumps(existing_extra))

    if updates:
        updates.append("updated_at = ?")
        params.append(now)
        params.append(item_id)
        conn.execute(
            f"UPDATE items SET {', '.join(updates)} WHERE id = ?",
            params
        )
        conn.commit()

    row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    result = _item_to_dict(conn, row)
    conn.close()
    return result


def transition_status(cwd, item_id, new_status, reason=""):
    """Validate and perform a status transition.

    Logs the transition to status_log. Sets completed_at for terminal states.

    Returns:
        Updated item dict.

    Raises:
        ValueError if item not found or transition is invalid.
    """
    conn = schema.get_db(cwd)
    row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    if row is None:
        conn.close()
        raise ValueError(f"Item not found: {item_id}")

    item_type = row["type"]
    current_status = row["status"]

    if not schema.validate_transition(item_type, current_status, new_status):
        conn.close()
        raise ValueError(
            f"Invalid transition for {item_type}: "
            f"{current_status} -> {new_status}"
        )

    now = _now()
    session_id = ensure_session(cwd)

    # Check if this is a terminal state
    terminal = TERMINAL_STATES.get(item_type, set())
    completed_at = now if new_status in terminal else None

    conn.execute(
        """UPDATE items
           SET status = ?, updated_at = ?, completed_at = ?
           WHERE id = ?""",
        (new_status, now, completed_at, item_id)
    )

    # Log transition
    conn.execute(
        """INSERT INTO status_log
           (item_id, from_status, to_status, changed_at, session_id, reason)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (item_id, current_status, new_status, now, session_id, reason)
    )

    conn.commit()

    row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    result = _item_to_dict(conn, row)
    conn.close()
    return result


# =====================================================================
# Items: Relations
# =====================================================================

def add_relation(cwd, from_id, to_id, relation):
    """Create a relation between two items."""
    conn = schema.get_db(cwd)
    now = _now()
    conn.execute(
        """INSERT OR IGNORE INTO item_relations
           (from_item_id, to_item_id, relation, created_at)
           VALUES (?, ?, ?, ?)""",
        (from_id, to_id, relation, now)
    )
    conn.commit()
    conn.close()


def add_tags(cwd, item_id, tags):
    """Add tags to an item. Idempotent."""
    conn = schema.get_db(cwd)
    for tag in tags:
        conn.execute(
            "INSERT OR IGNORE INTO item_tags (item_id, tag) VALUES (?, ?)",
            (item_id, tag)
        )
    conn.execute(
        "UPDATE items SET updated_at = ? WHERE id = ?",
        (_now(), item_id)
    )
    conn.commit()
    conn.close()


def add_related_files(cwd, item_id, files):
    """Add related files to an item. Idempotent."""
    conn = schema.get_db(cwd)
    for fp in files:
        conn.execute(
            "INSERT OR IGNORE INTO item_files (item_id, filepath) VALUES (?, ?)",
            (item_id, fp)
        )
    conn.execute(
        "UPDATE items SET updated_at = ? WHERE id = ?",
        (_now(), item_id)
    )
    conn.commit()
    conn.close()


def add_kb_ref(cwd, item_id, ref):
    """Add a knowledge base reference to an item. Idempotent."""
    conn = schema.get_db(cwd)
    conn.execute(
        "INSERT OR IGNORE INTO item_kb_refs (item_id, kb_ref) VALUES (?, ?)",
        (item_id, ref)
    )
    conn.execute(
        "UPDATE items SET updated_at = ? WHERE id = ?",
        (_now(), item_id)
    )
    conn.commit()
    conn.close()


# =====================================================================
# Queries
# =====================================================================

def _get_all_terminal_statuses():
    """Return a flat set of all terminal statuses across all types."""
    result = set()
    for statuses in TERMINAL_STATES.values():
        result.update(statuses)
    return result


def get_active_items(cwd, limit=10):
    """Get non-terminal status items, sorted by priority DESC, updated_at DESC.

    Returns:
        List of item dicts.
    """
    conn = schema.get_db(cwd)
    terminal = _get_all_terminal_statuses()
    placeholders = ",".join("?" for _ in terminal)

    rows = conn.execute(
        f"""SELECT * FROM items
            WHERE status NOT IN ({placeholders})
            ORDER BY
                CASE priority
                    WHEN 'high' THEN 3
                    WHEN 'medium' THEN 2
                    WHEN 'low' THEN 1
                END DESC,
                updated_at DESC
            LIMIT ?""",
        (*terminal, limit)
    ).fetchall()

    result = [_item_to_dict(conn, row) for row in rows]
    conn.close()
    return result


def get_incomplete(cwd):
    """Get all non-terminal items.

    Returns:
        List of item dicts.
    """
    conn = schema.get_db(cwd)
    terminal = _get_all_terminal_statuses()
    placeholders = ",".join("?" for _ in terminal)

    rows = conn.execute(
        f"""SELECT * FROM items
            WHERE status NOT IN ({placeholders})
            ORDER BY updated_at DESC""",
        tuple(terminal)
    ).fetchall()

    result = [_item_to_dict(conn, row) for row in rows]
    conn.close()
    return result


def search(cwd, type=None, status=None, tags=None, related_files=None,
           after=None, before=None, query=None, limit=20):
    """Multi-criteria AND search across items.

    All filters are combined with AND logic. Query does LIKE on
    title + description.

    Returns:
        List of item dicts matching all criteria.
    """
    conn = schema.get_db(cwd)
    conditions = []
    params = []

    if type is not None:
        conditions.append("i.type = ?")
        params.append(type)

    if status is not None:
        conditions.append("i.status = ?")
        params.append(status)

    if after is not None:
        conditions.append("i.created_at >= ?")
        params.append(after)

    if before is not None:
        conditions.append("i.created_at <= ?")
        params.append(before)

    if query is not None:
        conditions.append("(i.title LIKE ? OR i.description LIKE ?)")
        like_val = f"%{query}%"
        params.extend([like_val, like_val])

    if tags:
        for tag in tags:
            conditions.append(
                "EXISTS (SELECT 1 FROM item_tags t WHERE t.item_id = i.id AND t.tag = ?)"
            )
            params.append(tag)

    if related_files:
        for fp in related_files:
            conditions.append(
                "EXISTS (SELECT 1 FROM item_files f WHERE f.item_id = i.id AND f.filepath = ?)"
            )
            params.append(fp)

    where = " AND ".join(conditions) if conditions else "1=1"

    rows = conn.execute(
        f"""SELECT * FROM items i
            WHERE {where}
            ORDER BY updated_at DESC
            LIMIT ?""",
        (*params, limit)
    ).fetchall()

    result = [_item_to_dict(conn, row) for row in rows]
    conn.close()
    return result


def get_item_history(cwd, item_id):
    """Get all status_log entries for an item, ordered by time.

    Returns:
        List of status log dicts.
    """
    conn = schema.get_db(cwd)
    rows = conn.execute(
        """SELECT * FROM status_log
           WHERE item_id = ?
           ORDER BY changed_at ASC""",
        (item_id,)
    ).fetchall()
    result = [dict(r) for r in rows]
    conn.close()
    return result


# =====================================================================
# Workflow Sync
# =====================================================================

def sync_workflow_status(cwd, state=None):
    """Sync state.json status to tracker.db.

    Reads state.json if state is not provided. Finds the tracker item
    by workflow_id and updates its status to match the workflow status.
    """
    if state is None:
        try:
            from . import state as state_module
        except ImportError:
            try:
                import state as state_module
            except ImportError:
                return
        state = state_module.load_state(cwd)

    if state is None:
        return

    workflow_id = state.get("workflow_id")
    if not workflow_id:
        return

    try:
        conn = schema.get_db(cwd)
    except FileNotFoundError:
        return

    row = conn.execute(
        "SELECT * FROM items WHERE workflow_id = ?",
        (workflow_id,)
    ).fetchone()

    if row is None:
        conn.close()
        return

    # Map workflow status to tracker status
    new_status = schema._map_workflow_status(state.get("status", "in_progress"))
    current_status = row["status"]

    if new_status == current_status:
        conn.close()
        return

    item_type = row["type"]
    item_id = row["id"]
    now = _now()
    session_id = ensure_session(cwd)

    # Check if transition is valid; if not, skip silently
    if not schema.validate_transition(item_type, current_status, new_status):
        conn.close()
        return

    # Check terminal state
    terminal = TERMINAL_STATES.get(item_type, set())
    completed_at = now if new_status in terminal else None

    conn.execute(
        """UPDATE items
           SET status = ?, updated_at = ?, completed_at = ?
           WHERE id = ?""",
        (new_status, now, completed_at, item_id)
    )

    conn.execute(
        """INSERT INTO status_log
           (item_id, from_status, to_status, changed_at, session_id, reason)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (item_id, current_status, new_status, now, session_id,
         "Synced from state.json")
    )

    conn.commit()
    conn.close()


def migrate_from_state_json(cwd):
    """Import state.json into tracker.db.

    Delegates to tracker_schema.migrate_from_state_json().

    Returns:
        Created item dict or None if no state.json exists.
    """
    return schema.migrate_from_state_json(cwd)


# =====================================================================
# CLI Entry Point
# =====================================================================

def _output(data):
    """Print data as JSON to stdout."""
    print(json.dumps(data, indent=2, default=str))


def main():
    """CLI interface for tracker operations."""
    parser = argparse.ArgumentParser(
        description="Hody Workflow Interaction Tracker"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init
    subparsers.add_parser("init", help="Initialize tracker database")

    # create
    create_p = subparsers.add_parser("create", help="Create a new item")
    create_p.add_argument("--type", required=True,
                          choices=["task", "investigation", "question",
                                   "discussion", "maintenance"])
    create_p.add_argument("--title", required=True)
    create_p.add_argument("--description", default="")
    create_p.add_argument("--priority", default="medium",
                          choices=["high", "medium", "low"])
    create_p.add_argument("--tags", default=None,
                          help="Comma-separated tags")
    create_p.add_argument("--workflow-id", default=None)

    # update (status transition)
    update_p = subparsers.add_parser("update", help="Update item status")
    update_p.add_argument("id", help="Item ID")
    update_p.add_argument("--status", required=True, help="New status")
    update_p.add_argument("--reason", default="", help="Reason for transition")

    # note
    note_p = subparsers.add_parser("note", help="Add notes to an item")
    note_p.add_argument("id", help="Item ID")
    note_p.add_argument("text", help="Note text")

    # search
    search_p = subparsers.add_parser("search", help="Search items")
    search_p.add_argument("--type", default=None,
                          choices=["task", "investigation", "question",
                                   "discussion", "maintenance"])
    search_p.add_argument("--status", default=None)
    search_p.add_argument("--tags", default=None,
                          help="Comma-separated tags")
    search_p.add_argument("--query", default=None, help="Text search")
    search_p.add_argument("--limit", type=int, default=20)

    # list
    list_p = subparsers.add_parser("list", help="List items")
    list_p.add_argument("--active", action="store_true",
                        help="Show only active (non-terminal) items")
    list_p.add_argument("--all", action="store_true",
                        help="Show all items (no limit)")

    # history
    history_p = subparsers.add_parser("history", help="Show item history")
    history_p.add_argument("id", help="Item ID")

    # context
    subparsers.add_parser("context",
                          help="Show session context (placeholder)")

    # migrate
    subparsers.add_parser("migrate", help="Import state.json into tracker")

    args = parser.parse_args()
    cwd = os.getcwd()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "init":
        schema.init_db(cwd)
        session_id = ensure_session(cwd)
        _output({"status": "ok", "session_id": session_id})

    elif args.command == "create":
        tags = args.tags.split(",") if args.tags else None
        item = create_item(
            cwd,
            type=args.type,
            title=args.title,
            description=args.description,
            priority=args.priority,
            tags=tags,
            workflow_id=args.workflow_id,
        )
        _output(item)

    elif args.command == "update":
        item = transition_status(
            cwd,
            item_id=args.id,
            new_status=args.status,
            reason=args.reason,
        )
        _output(item)

    elif args.command == "note":
        item = update_item(cwd, item_id=args.id, notes=args.text)
        _output(item)

    elif args.command == "search":
        tags = args.tags.split(",") if args.tags else None
        results = search(
            cwd,
            type=args.type,
            status=args.status,
            tags=tags,
            query=args.query,
            limit=args.limit,
        )
        _output(results)

    elif args.command == "list":
        if args.active:
            results = get_active_items(cwd)
        elif args.all:
            results = search(cwd, limit=1000)
        else:
            results = get_active_items(cwd, limit=20)
        _output(results)

    elif args.command == "history":
        results = get_item_history(cwd, args.id)
        _output(results)

    elif args.command == "context":
        # Placeholder — will delegate to tracker_awareness module
        _output({
            "summary": "Context awareness not yet implemented",
            "active_items": get_active_items(cwd, limit=5),
            "warnings": [],
            "recent_completed": [],
        })

    elif args.command == "migrate":
        result = migrate_from_state_json(cwd)
        if result:
            _output(result)
        else:
            _output({"status": "no_state_json", "message": "No state.json found to migrate"})


if __name__ == "__main__":
    main()
