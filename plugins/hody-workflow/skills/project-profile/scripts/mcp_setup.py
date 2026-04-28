"""
Configure MCP server entries for third-party integrations (Jira, GitHub,
Linear) in .claude/settings.json without manual JSON editing.

Each integration has a registered spec describing its required fields,
the MCP server command, and how to map fields to env vars. The CLI
accepts those fields as args, validates them, merges the resulting
server config into .claude/settings.json (preserving other entries),
and flips integrations.<name>: true in .hody/profile.yaml.

Usage:
  mcp_setup.py jira --api-token X --site Y --email Z
  mcp_setup.py linear --api-key X
  mcp_setup.py github --token X
  mcp_setup.py status
  mcp_setup.py remove jira
  mcp_setup.py fields jira       # describe required fields (for guides)
"""
import argparse
import json
import os
import re
import sys


# =====================================================================
# Integration specs
# =====================================================================

INTEGRATIONS = {
    "jira": {
        "fields": [
            {
                "name": "api-token",
                "env": "JIRA_API_TOKEN",
                "description": "Atlassian API token",
                "guide": "Create at https://id.atlassian.com/manage-profile/security/api-tokens",
            },
            {
                "name": "site",
                "env": "JIRA_BASE_URL",
                "description": "Your Jira site URL",
                "guide": "e.g. https://your-org.atlassian.net (no trailing slash)",
            },
            {
                "name": "email",
                "env": "JIRA_USER_EMAIL",
                "description": "Atlassian account email",
                "guide": "The email you log into Atlassian with",
            },
        ],
        "server": {
            "command": "npx",
            "args": ["-y", "@anthropic/mcp-server-atlassian"],
        },
    },
    "linear": {
        "fields": [
            {
                "name": "api-key",
                "env": "LINEAR_API_KEY",
                "description": "Linear API key",
                "guide": "Create at Linear → Settings → API → Personal API keys",
            },
        ],
        "server": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-linear"],
        },
    },
    "github": {
        "fields": [
            {
                "name": "token",
                "env": "GITHUB_PERSONAL_ACCESS_TOKEN",
                "description": "GitHub Personal Access Token",
                "guide": "Create at https://github.com/settings/tokens (scopes: repo, read:org)",
            },
        ],
        "server": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-github"],
        },
    },
}


# =====================================================================
# Settings.json read/write
# =====================================================================

def _settings_path(cwd):
    return os.path.join(cwd, ".claude", "settings.json")


def load_settings(cwd):
    path = _settings_path(cwd)
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_settings(cwd, settings):
    path = _settings_path(cwd)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")


def merge_mcp_server(settings, name, server_config):
    """Merge a server entry into settings.mcpServers without clobbering siblings."""
    if "mcpServers" not in settings or not isinstance(settings["mcpServers"], dict):
        settings["mcpServers"] = {}
    settings["mcpServers"][name] = server_config
    return settings


def remove_mcp_server(settings, name):
    """Drop a single server entry; return True if it existed."""
    servers = settings.get("mcpServers")
    if not isinstance(servers, dict) or name not in servers:
        return False
    del servers[name]
    return True


# =====================================================================
# profile.yaml integration flag
# =====================================================================

def update_profile_integration(cwd, name, enabled=True):
    """Flip integrations.<name>: <enabled> in .hody/profile.yaml.

    Mirrors the regex-based approach used by graphify_setup.py to avoid a
    full YAML round-trip.
    """
    path = os.path.join(cwd, ".hody", "profile.yaml")
    if not os.path.isfile(path):
        return False

    with open(path, "r") as f:
        content = f.read()

    target_value = "true" if enabled else "false"
    line_pattern = rf"^(\s*){re.escape(name)}:\s*\S+"

    # Case 1: line already set to target
    if re.search(rf"^\s*{re.escape(name)}:\s*{target_value}\s*$",
                 content, re.MULTILINE):
        return True

    # Case 2: line exists with different value -> rewrite
    new_content, count = re.subn(
        line_pattern,
        rf"\g<1>{name}: {target_value}",
        content,
        count=1,
        flags=re.MULTILINE,
    )
    if count > 0:
        with open(path, "w") as f:
            f.write(new_content)
        return True

    # Case 3: integrations section exists, missing this key
    if re.search(r"^integrations:\s*$", content, re.MULTILINE):
        new_content = re.sub(
            r"^(integrations:\s*\n)",
            rf"\1  {name}: {target_value}\n",
            content,
            count=1,
            flags=re.MULTILINE,
        )
        with open(path, "w") as f:
            f.write(new_content)
        return True

    # Case 4: no integrations section
    addition = f"\nintegrations:\n  {name}: {target_value}\n"
    with open(path, "a") as f:
        f.write(addition)
    return True


# =====================================================================
# Setup logic
# =====================================================================

def get_spec(name):
    if name not in INTEGRATIONS:
        raise ValueError(
            f"Unknown integration: {name}. "
            f"Choose from {sorted(INTEGRATIONS)}"
        )
    return INTEGRATIONS[name]


def describe_fields(name):
    """Return list of dicts describing required fields for guides/prompts."""
    return list(get_spec(name)["fields"])


def collect_missing(name, provided):
    """Return field specs whose values are missing or empty in `provided`."""
    fields = describe_fields(name)
    missing = []
    for f in fields:
        key = f["name"]
        if not provided.get(key):
            missing.append(f)
    return missing


def build_server_config(name, values):
    """Build the MCP server JSON entry from collected field values."""
    spec = get_spec(name)
    server = {
        "command": spec["server"]["command"],
        "args": list(spec["server"]["args"]),
    }
    env = {}
    for field in spec["fields"]:
        key = field["name"]
        if key not in values or values[key] in (None, ""):
            raise ValueError(f"Missing required field: --{key}")
        env[field["env"]] = values[key]
    if env:
        server["env"] = env
    return server


def configure(cwd, name, values):
    """Apply settings + profile updates for an integration. Returns summary."""
    spec = get_spec(name)
    missing = collect_missing(name, values)
    if missing:
        raise ValueError(
            "Missing required fields: "
            + ", ".join(f"--{f['name']}" for f in missing)
        )

    server_config = build_server_config(name, values)
    settings = load_settings(cwd)
    merge_mcp_server(settings, name, server_config)
    save_settings(cwd, settings)
    profile_updated = update_profile_integration(cwd, name, enabled=True)

    return {
        "integration": name,
        "settings_path": _settings_path(cwd),
        "profile_updated": profile_updated,
        "fields_used": [f["name"] for f in spec["fields"]],
        "restart_required": True,
    }


def remove(cwd, name):
    """Remove the MCP server entry and flip profile flag back to false."""
    get_spec(name)  # validate name
    settings = load_settings(cwd)
    removed = remove_mcp_server(settings, name)
    if removed:
        save_settings(cwd, settings)
    profile_updated = update_profile_integration(cwd, name, enabled=False)
    return {
        "integration": name,
        "removed_from_settings": removed,
        "profile_updated": profile_updated,
    }


def status(cwd):
    """Return current configuration state for all known integrations."""
    settings = load_settings(cwd)
    servers = settings.get("mcpServers", {}) or {}
    profile_path = os.path.join(cwd, ".hody", "profile.yaml")
    profile_text = ""
    if os.path.isfile(profile_path):
        with open(profile_path, "r") as f:
            profile_text = f.read()

    result = {}
    for name in INTEGRATIONS:
        in_settings = name in servers
        match = re.search(
            rf"^\s*{re.escape(name)}:\s*(true|false)\s*$",
            profile_text,
            re.MULTILINE,
        )
        profile_flag = match.group(1) if match else None
        result[name] = {
            "configured_in_settings": in_settings,
            "profile_flag": profile_flag,
        }
    return result


# =====================================================================
# CLI
# =====================================================================

def _add_field_args(parser, name):
    for field in describe_fields(name):
        parser.add_argument(
            f"--{field['name']}",
            dest=field["name"].replace("-", "_"),
            help=f"{field['description']} ({field['guide']})",
        )


def _values_from_namespace(ns, name):
    values = {}
    for field in describe_fields(name):
        attr = field["name"].replace("-", "_")
        values[field["name"]] = getattr(ns, attr, None)
    return values


def cmd_configure(args):
    values = _values_from_namespace(args, args.integration)
    result = configure(args.cwd, args.integration, values)
    print(json.dumps(result, indent=2))


def cmd_remove(args):
    result = remove(args.cwd, args.integration)
    print(json.dumps(result, indent=2))


def cmd_status(args):
    result = status(args.cwd)
    print(json.dumps(result, indent=2))


def cmd_fields(args):
    fields = describe_fields(args.integration)
    print(json.dumps(fields, indent=2))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cwd", default=os.getcwd(), help="Project root")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # Per-integration configure subcommands
    for name in INTEGRATIONS:
        p = sub.add_parser(name, help=f"Configure {name} MCP server")
        _add_field_args(p, name)
        p.set_defaults(func=cmd_configure, integration=name)

    p_remove = sub.add_parser("remove", help="Remove an integration")
    p_remove.add_argument("integration", choices=list(INTEGRATIONS))
    p_remove.set_defaults(func=cmd_remove)

    p_status = sub.add_parser("status", help="Show integration status")
    p_status.set_defaults(func=cmd_status)

    p_fields = sub.add_parser(
        "fields", help="Describe required fields (JSON for guides)"
    )
    p_fields.add_argument("integration", choices=list(INTEGRATIONS))
    p_fields.set_defaults(func=cmd_fields)

    args = parser.parse_args(argv)
    try:
        args.func(args)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
