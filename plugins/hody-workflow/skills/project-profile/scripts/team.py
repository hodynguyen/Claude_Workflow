"""
Team roles and permissions for Hody Workflow.

Reads `.hody/team.yaml` for role definitions, member assignments,
and agent access control.
"""
import os
import re
import subprocess


# Built-in role definitions
DEFAULT_ROLES = {
    "lead": {
        "can_skip_agents": True,
        "can_modify_contracts": True,
        "agents": "all",
        "requires_review": False,
    },
    "developer": {
        "can_skip_agents": False,
        "can_modify_contracts": False,
        "agents": ["researcher", "architect", "frontend", "backend", "unit-tester"],
        "requires_review": True,
    },
    "reviewer": {
        "can_skip_agents": False,
        "can_modify_contracts": False,
        "agents": ["code-reviewer", "spec-verifier", "integration-tester"],
        "requires_review": False,
        "can_approve_merge": True,
    },
    "junior": {
        "can_skip_agents": False,
        "can_modify_contracts": False,
        "agents": ["frontend", "backend", "unit-tester"],
        "requires_review": True,
        "requires_architect_approval": True,
    },
}

ALL_AGENTS = [
    "researcher", "architect", "frontend", "backend",
    "code-reviewer", "spec-verifier", "unit-tester",
    "integration-tester", "devops",
]


def _parse_team_yaml(content):
    """Simple YAML parser for team config (stdlib only).

    Handles roles dict, members list, and nested properties.
    Returns a dict with 'roles' and 'members' keys.
    """
    result = {"roles": {}, "members": []}
    lines = content.split("\n")
    current_section = None
    current_role = None
    current_member = None
    current_agents_list = False

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip empty lines and comments
        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        # Top-level sections
        if not line.startswith(" ") and not line.startswith("\t"):
            if stripped == "roles:":
                current_section = "roles"
                current_role = None
                current_agents_list = False
            elif stripped == "members:":
                current_section = "members"
                current_role = None
                current_member = None
                current_agents_list = False
            else:
                current_section = None
            i += 1
            continue

        # Inside roles section
        if current_section == "roles":
            indent = len(line) - len(line.lstrip())
            if indent == 2 and stripped.endswith(":"):
                current_role = stripped[:-1]
                result["roles"][current_role] = {}
                current_agents_list = False
            elif current_role and indent == 4:
                if stripped.startswith("- ") and current_agents_list:
                    # Agent list item
                    agent = stripped[2:].strip().strip('"').strip("'")
                    result["roles"][current_role]["agents"].append(agent)
                elif ":" in stripped:
                    key, val = stripped.split(":", 1)
                    key = key.strip()
                    val = val.strip()
                    current_agents_list = False
                    if key == "agents":
                        if val == "" or val == "[]":
                            result["roles"][current_role]["agents"] = []
                            if val == "":
                                current_agents_list = True
                        elif val.startswith("["):
                            # Inline list: [a, b, c]
                            items = val.strip("[]").split(",")
                            result["roles"][current_role]["agents"] = [
                                item.strip().strip('"').strip("'")
                                for item in items if item.strip()
                            ]
                        elif val == "all":
                            result["roles"][current_role]["agents"] = "all"
                        else:
                            result["roles"][current_role]["agents"] = val
                    else:
                        result["roles"][current_role][key] = _parse_yaml_value(val)
            elif current_role and indent == 6 and current_agents_list:
                if stripped.startswith("- "):
                    agent = stripped[2:].strip().strip('"').strip("'")
                    result["roles"][current_role]["agents"].append(agent)

        # Inside members section
        elif current_section == "members":
            indent = len(line) - len(line.lstrip())
            if stripped.startswith("- "):
                # New member entry: - name: alice
                rest = stripped[2:]
                if ":" in rest:
                    key, val = rest.split(":", 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    current_member = {key: val}
                    result["members"].append(current_member)
                else:
                    current_member = None
            elif current_member and indent >= 4 and ":" in stripped:
                key, val = stripped.split(":", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                current_member[key] = _parse_yaml_value(val)

        i += 1

    return result


def _parse_yaml_value(val):
    """Parse a simple YAML scalar value."""
    if val.lower() == "true":
        return True
    if val.lower() == "false":
        return False
    if val.isdigit():
        return int(val)
    return val.strip('"').strip("'")


def load_team_config(cwd):
    """Load .hody/team.yaml. Returns parsed config or default if not found."""
    team_path = os.path.join(cwd, ".hody", "team.yaml")
    if not os.path.isfile(team_path):
        return {
            "roles": dict(DEFAULT_ROLES),
            "members": [],
        }
    try:
        with open(team_path, "r") as f:
            content = f.read()
        parsed = _parse_team_yaml(content)
        # Merge with defaults: default roles are base, custom roles override
        merged_roles = dict(DEFAULT_ROLES)
        for role_name, role_def in parsed.get("roles", {}).items():
            if role_name in merged_roles:
                merged_roles[role_name] = {**merged_roles[role_name], **role_def}
            else:
                merged_roles[role_name] = role_def
        return {
            "roles": merged_roles,
            "members": parsed.get("members", []),
        }
    except (IOError, OSError):
        return {
            "roles": dict(DEFAULT_ROLES),
            "members": [],
        }


def get_current_user(cwd):
    """Get current git user (from git config user.name or HODY_USER env var).

    Returns username string, or None if not determinable.
    """
    # Check env var first
    env_user = os.environ.get("HODY_USER")
    if env_user:
        return env_user

    # Try git config user.name
    try:
        result = subprocess.run(
            ["git", "config", "user.name"],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        pass

    return None


def get_user_role(config, username):
    """Look up a user's role from team config.

    Returns role name string, or "developer" as default.
    """
    if not username:
        return "developer"

    for member in config.get("members", []):
        member_name = member.get("name", "")
        if member_name == username:
            return member.get("role", "developer")

    return "developer"


def get_role_permissions(config, role_name):
    """Get permissions for a role.

    Returns dict with can_skip_agents, agents, requires_review, etc.
    Merges custom role definitions with defaults.
    """
    roles = config.get("roles", DEFAULT_ROLES)

    if role_name in roles:
        perms = dict(roles[role_name])
    elif role_name in DEFAULT_ROLES:
        perms = dict(DEFAULT_ROLES[role_name])
    else:
        # Unknown role, default to developer permissions
        perms = dict(DEFAULT_ROLES["developer"])

    # Ensure required keys exist
    perms.setdefault("can_skip_agents", False)
    perms.setdefault("can_modify_contracts", False)
    perms.setdefault("requires_review", True)
    perms.setdefault("agents", [])

    return perms


def can_use_agent(config, username, agent_name):
    """Check if a user can use a specific agent.

    Returns (allowed: bool, reason: str).
    """
    role_name = get_user_role(config, username)
    perms = get_role_permissions(config, role_name)
    agents = perms.get("agents", [])

    if agents == "all":
        return True, f"Role '{role_name}' has access to all agents."

    if isinstance(agents, list) and agent_name in agents:
        return True, f"Role '{role_name}' has access to agent '{agent_name}'."

    return False, (
        f"Role '{role_name}' does not have access to agent '{agent_name}'. "
        f"Allowed agents: {agents}"
    )


def check_workflow_permissions(config, username, action):
    """Check if user can perform a workflow action.

    Actions: "skip_agent", "abort_workflow", "modify_contract"
    Returns (allowed: bool, reason: str).
    """
    role_name = get_user_role(config, username)
    perms = get_role_permissions(config, role_name)

    if action == "skip_agent":
        if perms.get("can_skip_agents", False):
            return True, f"Role '{role_name}' can skip agents."
        return False, f"Role '{role_name}' cannot skip agents."

    if action == "modify_contract":
        if perms.get("can_modify_contracts", False):
            return True, f"Role '{role_name}' can modify contracts."
        return False, f"Role '{role_name}' cannot modify contracts."

    if action == "abort_workflow":
        # Leads can always abort; others cannot
        if perms.get("can_skip_agents", False):
            return True, f"Role '{role_name}' can abort workflows."
        return False, f"Role '{role_name}' cannot abort workflows."

    return False, f"Unknown action: {action}"


def generate_default_team_config():
    """Generate default team.yaml content as string."""
    return """# Team Roles & Permissions for Hody Workflow
# See docs for full configuration options.

roles:
  lead:
    can_skip_agents: true
    can_modify_contracts: true
    agents: all
    requires_review: false
  developer:
    can_skip_agents: false
    can_modify_contracts: false
    agents:
      - researcher
      - architect
      - frontend
      - backend
      - unit-tester
    requires_review: true
  reviewer:
    can_skip_agents: false
    can_modify_contracts: false
    agents:
      - code-reviewer
      - spec-verifier
      - integration-tester
    requires_review: false
    can_approve_merge: true
  junior:
    can_skip_agents: false
    can_modify_contracts: false
    agents:
      - frontend
      - backend
      - unit-tester
    requires_review: true
    requires_architect_approval: true

members:
  # - name: alice
  #   role: lead
  # - name: bob
  #   role: developer
"""


def get_team_summary(cwd):
    """Get team overview for status/health commands.

    Returns dict with roles, member_count, current_user, current_role.
    """
    config = load_team_config(cwd)
    username = get_current_user(cwd)
    role = get_user_role(config, username)
    roles = config.get("roles", {})

    return {
        "roles": list(roles.keys()),
        "member_count": len(config.get("members", [])),
        "current_user": username,
        "current_role": role,
    }
