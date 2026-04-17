"""
Workflow state machine for Hody Workflow.

Manages `.hody/state.json` — tracks active workflows with phases,
agents, timestamps, and an audit log.
"""
import json
import os
import re
from datetime import datetime, timezone

VALID_MODES = ("auto", "guided", "manual")


def _now():
    """Return current UTC timestamp as ISO string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _state_path(cwd):
    return os.path.join(cwd, ".hody", "state.json")


def _write_state(cwd, state):
    state["updated_at"] = _now()
    path = _state_path(cwd)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(state, f, indent=2)
    return state


def _make_workflow_id(feature):
    """Generate workflow ID from feature description + date."""
    date = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"feat-{_make_slug(feature)}-{date}"


def _make_slug(text):
    """Convert text to a URL-friendly slug."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40]


def init_workflow(cwd, feature, feature_type, phases, spec_confirmed=False,
                  spec_file=None, log_file=None, execution_mode="guided"):
    """Create .hody/state.json with initial workflow state.

    Args:
        cwd: Project root directory.
        feature: Feature description string.
        feature_type: One of the feature types (new-feature, bug-fix, etc.).
        phases: Dict mapping phase names to agent lists, e.g.
                {"THINK": ["researcher", "architect"], "BUILD": ["backend"]}.
        spec_confirmed: Whether spec has been confirmed by the user.
        spec_file: KB filename for the confirmed spec (e.g. "spec-oauth2-login.md").
        log_file: KB filename for the feature log (auto-generated if None).
        execution_mode: One of "auto", "guided", "manual".

    Returns:
        The created state dict.
    """
    if execution_mode not in VALID_MODES:
        raise ValueError(
            f"Invalid execution_mode: {execution_mode}. Must be one of {VALID_MODES}"
        )
    phase_order = [p for p in ["THINK", "BUILD", "VERIFY", "SHIP"] if p in phases]
    slug = _make_slug(feature)

    if log_file is None:
        log_file = f"log-{slug}.md"

    state = {
        "workflow_id": _make_workflow_id(feature),
        "feature": feature,
        "type": feature_type,
        "status": "in_progress",
        "execution_mode": execution_mode,
        "spec_confirmed": spec_confirmed,
        "spec_file": spec_file,
        "log_file": log_file,
        "created_at": _now(),
        "updated_at": _now(),
        "phases": {},
        "phase_order": phase_order,
        "agent_log": [],
    }

    for phase in phase_order:
        state["phases"][phase] = {
            "agents": list(phases[phase]),
            "completed": [],
            "active": None,
            "skipped": [],
        }

    return _write_state(cwd, state)


def load_state(cwd):
    """Read .hody/state.json, return None if doesn't exist."""
    path = _state_path(cwd)
    if not os.path.isfile(path):
        return None
    with open(path, "r") as f:
        return json.load(f)


def get_execution_mode(state):
    """Return execution mode, defaulting to 'guided' for legacy state files."""
    if state is None:
        return "guided"
    return state.get("execution_mode", "guided")


def set_execution_mode(cwd, mode):
    """Override execution mode for current workflow."""
    if mode not in VALID_MODES:
        raise ValueError(
            f"Invalid mode: {mode}. Must be one of {VALID_MODES}"
        )
    state = load_state(cwd)
    if state is None:
        raise FileNotFoundError("No active workflow — .hody/state.json not found")
    state["execution_mode"] = mode
    return _write_state(cwd, state)


def confirm_spec(cwd, spec_file):
    """Mark the spec as confirmed, enabling auto-execution.

    Args:
        cwd: Project root directory.
        spec_file: KB filename for the confirmed spec.

    Returns:
        The updated state dict.
    """
    state = load_state(cwd)
    if state is None:
        raise FileNotFoundError("No active workflow — .hody/state.json not found")

    state["spec_confirmed"] = True
    state["spec_file"] = spec_file
    return _write_state(cwd, state)


def _find_agent_phase(state, agent_name):
    """Find which phase an agent belongs to."""
    for phase in state["phase_order"]:
        if agent_name in state["phases"][phase]["agents"]:
            return phase
    return None


def _current_phase(state):
    """Return the current (first non-complete) phase name, or None."""
    for phase in state["phase_order"]:
        p = state["phases"][phase]
        remaining = set(p["agents"]) - set(p["completed"]) - set(p["skipped"])
        if remaining:
            return phase
    return None


def _phase_has_progress(state, phase):
    """Check if a phase has at least one completed or skipped agent."""
    p = state["phases"][phase]
    return len(p["completed"]) > 0 or len(p["skipped"]) == len(p["agents"])


def _load_checkpoint(cwd, workflow_id, agent_name):
    """Try to load a checkpoint for this agent. Returns dict or None."""
    try:
        from . import tracker as tracker_module
    except ImportError:
        try:
            import tracker as tracker_module
        except ImportError:
            return None
    try:
        return tracker_module.load_checkpoint(cwd, workflow_id, agent_name)
    except Exception:
        return None


def _clear_checkpoint(cwd, workflow_id, agent_name):
    """Try to clear the checkpoint for a completed agent."""
    try:
        from . import tracker as tracker_module
    except ImportError:
        try:
            import tracker as tracker_module
        except ImportError:
            return
    try:
        tracker_module.clear_checkpoint(cwd, workflow_id, agent_name)
    except Exception:
        pass


def start_agent(cwd, agent_name):
    """Set agent as active, log start time.

    Returns (updated_state, checkpoint_or_none). If a checkpoint exists
    for this agent, it is returned so the caller can resume from where
    the agent left off.
    """
    state = load_state(cwd)
    if state is None:
        raise FileNotFoundError("No active workflow — .hody/state.json not found")

    phase = _find_agent_phase(state, agent_name)
    if phase is None:
        raise ValueError(f"Agent '{agent_name}' not found in any workflow phase")

    # Advisory check: warn if earlier phases haven't started
    phase_idx = state["phase_order"].index(phase)
    warnings = []
    for earlier_phase in state["phase_order"][:phase_idx]:
        if not _phase_has_progress(state, earlier_phase):
            warnings.append(
                f"Warning: Starting '{agent_name}' in {phase} "
                f"before {earlier_phase} phase has any progress"
            )

    if warnings:
        for w in warnings:
            print(w)

    # Set active
    state["phases"][phase]["active"] = agent_name

    # Add log entry
    state["agent_log"].append({
        "agent": agent_name,
        "phase": phase,
        "started_at": _now(),
        "completed_at": None,
        "output_summary": "",
        "kb_files_modified": [],
    })

    updated_state = _write_state(cwd, state)

    # Check for existing checkpoint (agent was interrupted before)
    checkpoint = _load_checkpoint(cwd, state["workflow_id"], agent_name)

    return updated_state, checkpoint


def complete_agent(cwd, agent_name, output_summary="", kb_files_modified=None):
    """Mark agent as completed, log end time + summary.

    Clears the agent's checkpoint since work is done.
    """
    state = load_state(cwd)
    if state is None:
        raise FileNotFoundError("No active workflow — .hody/state.json not found")

    phase = _find_agent_phase(state, agent_name)
    if phase is None:
        raise ValueError(f"Agent '{agent_name}' not found in any workflow phase")

    p = state["phases"][phase]

    # Mark completed
    if agent_name not in p["completed"]:
        p["completed"].append(agent_name)

    # Clear active if this agent was active
    if p["active"] == agent_name:
        p["active"] = None

    # Update log entry
    for entry in reversed(state["agent_log"]):
        if entry["agent"] == agent_name and entry["completed_at"] is None:
            entry["completed_at"] = _now()
            entry["output_summary"] = output_summary
            entry["kb_files_modified"] = kb_files_modified or []
            break

    # Clear checkpoint — agent is done, no need to keep it
    _clear_checkpoint(cwd, state["workflow_id"], agent_name)

    return _write_state(cwd, state)


def skip_agent(cwd, agent_name):
    """Mark agent as skipped."""
    state = load_state(cwd)
    if state is None:
        raise FileNotFoundError("No active workflow — .hody/state.json not found")

    phase = _find_agent_phase(state, agent_name)
    if phase is None:
        raise ValueError(f"Agent '{agent_name}' not found in any workflow phase")

    p = state["phases"][phase]
    if agent_name not in p["skipped"]:
        p["skipped"].append(agent_name)

    # Clear active if this agent was active
    if p["active"] == agent_name:
        p["active"] = None

    return _write_state(cwd, state)


def _clear_all_checkpoints(cwd, workflow_id):
    """Clear all checkpoints for a workflow."""
    try:
        from . import tracker as tracker_module
    except ImportError:
        try:
            import tracker as tracker_module
        except ImportError:
            return
    try:
        tracker_module.clear_workflow_checkpoints(cwd, workflow_id)
    except Exception:
        pass


def complete_workflow(cwd):
    """Set status = 'completed', record end time.

    Clears all checkpoints and finalizes the feature log.
    """
    state = load_state(cwd)
    if state is None:
        raise FileNotFoundError("No active workflow — .hody/state.json not found")

    # Finalize log before changing status
    finalize_feature_log(cwd, state.get("log_file"))

    state["status"] = "completed"
    _clear_all_checkpoints(cwd, state["workflow_id"])
    return _write_state(cwd, state)


def abort_workflow(cwd):
    """Set status = 'aborted'. Clears all checkpoints."""
    state = load_state(cwd)
    if state is None:
        raise FileNotFoundError("No active workflow — .hody/state.json not found")

    state["status"] = "aborted"
    _clear_all_checkpoints(cwd, state["workflow_id"])
    return _write_state(cwd, state)


def _log_path(cwd, log_file):
    """Return absolute path to the feature log file in KB."""
    return os.path.join(cwd, ".hody", "knowledge", log_file)


def create_feature_log(cwd, feature, feature_type, spec_file=None, log_file=None):
    """Create the initial feature log file in the knowledge base.

    Args:
        cwd: Project root directory.
        feature: Feature description.
        feature_type: Classified feature type.
        spec_file: Spec filename if available.
        log_file: Log filename (reads from state.json if None).

    Returns:
        The log file path.
    """
    if log_file is None:
        state = load_state(cwd)
        if state is None:
            raise FileNotFoundError("No active workflow")
        log_file = state.get("log_file", f"log-{_make_slug(feature)}.md")

    path = _log_path(cwd, log_file)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    spec_ref = f"\n\n## Spec\n-> {spec_file}" if spec_file else ""

    content = (
        f"---\n"
        f"tags: [log, {feature_type}]\n"
        f"date: {today}\n"
        f"author-agent: start-feature\n"
        f"status: in_progress\n"
        f"---\n\n"
        f"# Feature Log: {feature}\n"
        f"\n"
        f"Type: {feature_type}\n"
        f"Started: {today}"
        f"{spec_ref}\n\n"
        f"## Agent Work\n"
    )

    with open(path, "w") as f:
        f.write(content)

    return path


def append_feature_log(cwd, agent_name, phase, summary,
                       files_created=None, files_modified=None,
                       kb_updated=None, decisions=None, log_file=None):
    """Append a structured agent entry to the feature log.

    Args:
        cwd: Project root directory.
        agent_name: Name of the agent (e.g. "backend").
        phase: Workflow phase (e.g. "BUILD").
        summary: Brief description of what the agent did.
        files_created: List of files the agent created.
        files_modified: List of files the agent modified.
        kb_updated: List of KB files updated.
        decisions: List of key decisions made.
        log_file: Log filename (reads from state.json if None).
    """
    if log_file is None:
        state = load_state(cwd)
        if state is None:
            return  # No workflow, skip silently
        log_file = state.get("log_file")
        if not log_file:
            return

    path = _log_path(cwd, log_file)
    if not os.path.isfile(path):
        return  # Log not created yet, skip silently

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [f"\n### {agent_name} ({phase}) — {today}\n"]
    lines.append(f"- {summary}\n")

    if files_created:
        lines.append("- Files created: " + ", ".join(f"`{f}`" for f in files_created) + "\n")
    if files_modified:
        lines.append("- Files modified: " + ", ".join(f"`{f}`" for f in files_modified) + "\n")
    if kb_updated:
        lines.append("- KB updated: " + ", ".join(kb_updated) + "\n")
    if decisions:
        for d in decisions:
            lines.append(f"- Decision: {d}\n")

    with open(path, "a") as f:
        f.writelines(lines)


def finalize_feature_log(cwd, log_file=None):
    """Append a final summary section to the feature log.

    Reads agent_log from state.json to build the summary.
    """
    state = load_state(cwd)
    if state is None:
        return

    if log_file is None:
        log_file = state.get("log_file")
    if not log_file:
        return

    path = _log_path(cwd, log_file)
    if not os.path.isfile(path):
        return

    # Build summary from agent_log
    lines = ["\n## Summary\n"]
    completed_count = 0
    for entry in state.get("agent_log", []):
        if entry.get("completed_at"):
            completed_count += 1
            agent = entry["agent"]
            phase = entry["phase"]
            summary = entry.get("output_summary", "")
            kb = entry.get("kb_files_modified", [])
            kb_str = f" (KB: {', '.join(kb)})" if kb else ""
            lines.append(f"- **{agent}** ({phase}): {summary}{kb_str}\n")

    lines.insert(1, f"\n{completed_count} agents completed.\n\n")

    # Update frontmatter status
    with open(path, "r") as f:
        content = f.read()

    content = content.replace("status: in_progress", "status: completed", 1)

    with open(path, "w") as f:
        f.write(content)

    with open(path, "a") as f:
        f.writelines(lines)


def get_next_agent(state):
    """Returns (phase, agent) for next unfinished agent, or None if done."""
    if state is None or state.get("status") != "in_progress":
        return None

    for phase in state["phase_order"]:
        p = state["phases"][phase]
        for agent in p["agents"]:
            if agent not in p["completed"] and agent not in p["skipped"]:
                return (phase, agent)

    return None
