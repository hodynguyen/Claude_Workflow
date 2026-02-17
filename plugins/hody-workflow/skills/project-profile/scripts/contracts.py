"""
Agent contract validator for Hody Workflow.

Reads contract YAML files from agents/contracts/ and validates
that the required KB files have been modified and required sections
exist in the agent's output or KB.

Validation is advisory by default — produces warnings, not errors.
"""
import os
import re


def _parse_yaml_simple(content):
    """Simple YAML parser for contract files (stdlib only).

    Handles top-level keys, string values, and lists of dicts.
    """
    result = {}
    current_key = None
    current_list = None

    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(line) - len(line.lstrip())

        # Top-level key
        if indent == 0 and ":" in stripped:
            key, _, value = stripped.partition(":")
            key = key.strip()
            value = value.strip()
            if value:
                result[key] = value
            else:
                result[key] = []
                current_key = key
                current_list = result[key]
            continue

        # List item under current key
        if current_key and stripped.startswith("- "):
            item_content = stripped[2:].strip()
            if ":" in item_content:
                # Dict item: parse key: value pairs
                item = {}
                k, _, v = item_content.partition(":")
                item[k.strip()] = v.strip().strip('"')
                current_list.append(item)
            else:
                current_list.append(item_content.strip('"'))
            continue

        # Continuation of dict item (indented under a list item)
        if current_list and indent >= 4 and ":" in stripped:
            k, _, v = stripped.partition(":")
            v = v.strip().strip('"')
            if current_list and isinstance(current_list[-1], dict):
                current_list[-1][k.strip()] = v

    return result


def load_contract(contract_path):
    """Load a contract YAML file.

    Returns parsed contract dict, or None if file doesn't exist.
    """
    if not os.path.isfile(contract_path):
        return None
    with open(contract_path, "r") as f:
        return _parse_yaml_simple(f.read())


def find_contract(contracts_dir, from_agent, to_agent):
    """Find a contract file for a given agent pair.

    Looks for: from-to.yaml, e.g. architect-to-backend.yaml
    """
    filename = f"{from_agent}-to-{to_agent}.yaml"
    path = os.path.join(contracts_dir, filename)
    if os.path.isfile(path):
        return load_contract(path)
    return None


def list_contracts(contracts_dir):
    """List all available contracts.

    Returns list of (from_agent, to_agent, contract) tuples.
    """
    contracts = []
    if not os.path.isdir(contracts_dir):
        return contracts

    for fname in sorted(os.listdir(contracts_dir)):
        if not fname.endswith(".yaml"):
            continue
        # Parse "from-to-to.yaml" pattern
        name = fname[:-5]  # strip .yaml
        match = re.match(r"^(.+?)-to-(.+)$", name)
        if match:
            from_agent = match.group(1)
            to_agent = match.group(2)
            contract = load_contract(os.path.join(contracts_dir, fname))
            if contract:
                contracts.append((from_agent, to_agent, contract))

    return contracts


def validate_handoff(contract, kb_dir, state=None):
    """Validate a contract against the current KB state.

    Checks:
    1. Required KB files exist and have been modified (not just template)
    2. Required sections exist in KB files (by heading search)

    Args:
        contract: Parsed contract dict.
        kb_dir: Path to .hody/knowledge/ directory.
        state: Optional workflow state dict (for agent_log checks).

    Returns:
        dict with 'passed', 'warnings', 'errors' keys.
        In advisory mode (default), all issues are warnings.
    """
    result = {"passed": True, "warnings": [], "errors": []}

    if not contract:
        return result

    # Check validation rules
    for rule in contract.get("validation", []):
        check_type = rule.get("check", "")
        message = rule.get("message", "Validation check failed")

        if check_type == "kb_file_modified":
            kb_file = rule.get("file", "")
            kb_path = os.path.join(kb_dir, kb_file)

            if not os.path.isfile(kb_path):
                result["warnings"].append(f"[Missing] {kb_file}: {message}")
                continue

            # Check if file has content beyond template
            with open(kb_path, "r") as f:
                content = f.read()

            # A file with only template markers (<!-- -->) or very short content
            # is considered unmodified
            lines = [l for l in content.splitlines()
                     if l.strip() and not l.strip().startswith("<!--")
                     and not l.strip().startswith("#")
                     and not l.strip().startswith("---")]
            if len(lines) < 3:
                result["warnings"].append(f"[Template only] {kb_file}: {message}")

    # Check required sections (advisory — check if KB mentions them)
    for section in contract.get("required_sections", []):
        section_name = section.get("name", "")
        if not section_name:
            continue

        # Search across all KB files for this section heading
        found = False
        if os.path.isdir(kb_dir):
            for fname in os.listdir(kb_dir):
                if not fname.endswith(".md"):
                    continue
                fpath = os.path.join(kb_dir, fname)
                with open(fpath, "r") as f:
                    content = f.read()
                if re.search(rf"##\s+.*{re.escape(section_name)}", content, re.IGNORECASE):
                    found = True
                    break

        if not found:
            fmt = section.get("format", "")
            result["warnings"].append(
                f"[Missing section] '{section_name}' not found in KB"
                + (f" (expected: {fmt})" if fmt else "")
            )

    if result["warnings"] or result["errors"]:
        result["passed"] = False

    return result


def get_contracts_for_agent(contracts_dir, agent_name):
    """Get all contracts where agent_name is the 'to' agent (receiving handoff).

    Returns list of (from_agent, contract) tuples.
    """
    incoming = []
    for from_agent, to_agent, contract in list_contracts(contracts_dir):
        if to_agent == agent_name:
            incoming.append((from_agent, contract))
    return incoming
