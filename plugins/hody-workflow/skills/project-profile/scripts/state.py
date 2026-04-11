"""
Workflow state machine for Hody Workflow.

Manages `.hody/state.json` — tracks active workflows with phases,
agents, timestamps, and an audit log.
"""
import json
import os
import re
from datetime import datetime, timezone


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
    slug = re.sub(r"[^a-z0-9]+", "-", feature.lower()).strip("-")
    slug = slug[:40]  # truncate long slugs
    date = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"feat-{slug}-{date}"


def init_workflow(cwd, feature, feature_type, phases, spec_confirmed=False, spec_file=None):
    """Create .hody/state.json with initial workflow state.

    Args:
        cwd: Project root directory.
        feature: Feature description string.
        feature_type: One of the feature types (new-feature, bug-fix, etc.).
        phases: Dict mapping phase names to agent lists, e.g.
                {"THINK": ["researcher", "architect"], "BUILD": ["backend"]}.
        spec_confirmed: Whether spec has been confirmed by the user.
        spec_file: KB filename for the confirmed spec (e.g. "spec-oauth2-login.md").

    Returns:
        The created state dict.
    """
    phase_order = [p for p in ["THINK", "BUILD", "VERIFY", "SHIP"] if p in phases]

    state = {
        "workflow_id": _make_workflow_id(feature),
        "feature": feature,
        "type": feature_type,
        "status": "in_progress",
        "spec_confirmed": spec_confirmed,
        "spec_file": spec_file,
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
    """Set status = 'completed', record end time. Clears all checkpoints."""
    state = load_state(cwd)
    if state is None:
        raise FileNotFoundError("No active workflow — .hody/state.json not found")

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
