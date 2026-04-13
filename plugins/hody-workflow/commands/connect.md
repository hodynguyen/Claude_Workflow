---
description: Configure MCP server integrations for the project. Connects agents to external tools like GitHub, Linear, and Jira.
argument-hint: "[optional: specific integration, e.g. 'github' or 'linear jira']"
---

# /hody-workflow:connect

Configure MCP (Model Context Protocol) server integrations so agents can interact with external tools.

## User Instructions

$ARGUMENTS

If the section above contains text, treat it as the target integration(s) to configure:
- Single name (e.g. "github") → configure only that integration
- Multiple names (e.g. "linear jira") → configure each
- "list" → list currently configured integrations, don't add new ones
- "disable <name>" → remove that integration from profile.yaml

If empty, guide the user through available integrations interactively.

## Steps

1. **Check initialization**: Verify `.hody/profile.yaml` exists. If not, tell the user to run `/hody-workflow:init` first.

2. **Show current integrations**: Read `.hody/profile.yaml` and check for an `integrations:` section. Display what's currently configured:

```
Current integrations:
  GitHub:  ✅ Connected (via gh CLI)
  Linear:  ⚠️  Not configured
  Jira:    ⚠️  Not configured
```

If no `integrations:` section exists, show all as "Not configured".

3. **Ask which integration to configure**: Present the available options:

| Integration | MCP Server | What agents can do |
|-------------|-----------|-------------------|
| **GitHub** | `@modelcontextprotocol/server-github` or `gh` CLI | Read issues/PRs, create PRs, post comments, read repo metadata |
| **Linear** | `@modelcontextprotocol/server-linear` | Read/create issues, link work to tickets, track project progress |
| **Jira** | MCP server for Jira (or Atlassian MCP) | Read/create issues, link work to tickets, read sprint info |
| **Graphify** | `graphify.serve` (Python MCP stdio) | Query code knowledge graph: call graphs, module boundaries, god nodes, blast radius |

4. **Configure the selected integration**:

### GitHub Setup

Check if `gh` CLI is installed and authenticated:

```bash
gh auth status
```

- If `gh` is authenticated → GitHub is ready, no MCP server needed (agents use `gh` CLI directly)
- If `gh` is not installed → suggest `brew install gh` (macOS) or see https://cli.github.com/
- If `gh` is not authenticated → suggest `gh auth login`

Alternatively, configure the GitHub MCP server for richer integration:

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "<token>"
      }
    }
  }
}
```

Tell the user to add this to their Claude Code MCP settings (`.claude/settings.json` or via `/mcp` command).

### Linear Setup

Configure the Linear MCP server:

```json
{
  "mcpServers": {
    "linear": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-linear"],
      "env": {
        "LINEAR_API_KEY": "<api-key>"
      }
    }
  }
}
```

Guide the user:
- Get API key from Linear → Settings → API → Personal API keys
- Add MCP config to Claude Code settings

### Jira Setup

Configure Jira MCP integration:

```json
{
  "mcpServers": {
    "jira": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-atlassian"],
      "env": {
        "JIRA_BASE_URL": "<https://your-org.atlassian.net>",
        "JIRA_API_TOKEN": "<api-token>",
        "JIRA_USER_EMAIL": "<email>"
      }
    }
  }
}
```

Guide the user:
- Get API token from https://id.atlassian.com/manage-profile/security/api-tokens
- Add MCP config to Claude Code settings

### Graphify Setup

Graphify turns the codebase into a queryable knowledge graph using tree-sitter AST extraction. Agents can then query call graphs, module boundaries, and coupling metrics via MCP tools.

**Step 1 — Check Python version:**

```bash
python3 --version
```

Graphify requires **Python >= 3.10**. If the version is lower, inform the user:

```
Graphify requires Python 3.10+. Your current version is 3.X.
Consider installing a newer Python via pyenv, Homebrew (brew install python@3.13), or your system package manager.
```

If Python version is sufficient, continue.

**Step 2 — Install Graphify:**

```bash
pip install graphifyy
```

Note: The PyPI package name is `graphifyy` (two y's), but the CLI command is `graphify`.

**Step 3 — Build the knowledge graph:**

The easiest way is to use Graphify's built-in Claude Code skill installer:

```bash
graphify claude install
```

This copies the Graphify skill to `~/.claude/skills/graphify/SKILL.md` and registers a PreToolUse hook. After restarting Claude Code, the user can run `/graphify` to build the graph.

Alternatively, the graph can be built via Python directly:

```bash
python3 -c "
from graphify.detect import detect
from graphify.extract import extract
from graphify.build import build
from networkx.readwrite import json_graph
from pathlib import Path
import json

result = detect(Path('.'))
code_files = [Path(f) for f in result['files']['code']]
ast = extract(code_files)
G = build([ast], directed=True)
data = json_graph.node_link_data(G)
data['links'] = data.pop('edges', data.get('links', []))
Path('graphify-out').mkdir(exist_ok=True)
with open('graphify-out/graph.json', 'w') as f:
    json.dump(data, f)
print(f'Graph built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges')
"
```

**Step 4 — Configure MCP server:**

Add to the project's `.claude/settings.json`:

```json
{
  "mcpServers": {
    "graphify": {
      "command": "python3",
      "args": ["-m", "graphify.serve", "graphify-out/graph.json"]
    }
  }
}
```

Tell the user to restart Claude Code after adding the MCP config.

**Step 5 — Add `graphify-out/` to `.gitignore`:**

Check if `graphify-out/` is already in `.gitignore`. If not, append it:

```bash
grep -q 'graphify-out' .gitignore 2>/dev/null || echo 'graphify-out/' >> .gitignore
```

**Step 6 — Verify:**

After restart, ask Claude: "What MCP tools do you have from graphify?"

Expected tools: `query_graph`, `get_node`, `get_neighbors`, `get_community`, `god_nodes`, `graph_stats`, `shortest_path`

5. **Update profile.yaml**: After configuration, add or update the `integrations:` section in `.hody/profile.yaml`:

```yaml
integrations:
  github: true       # gh CLI authenticated or MCP server configured
  linear: false
  jira: false
  graphify: false    # Graphify knowledge graph MCP server
```

6. **Verify connection**: For each configured integration, run a quick test:
   - **GitHub**: `gh repo view --json name` (verify repo access)
   - **Linear**: Use the Linear MCP tool to search for recent issues (e.g., list issues updated in the last 7 days). If results are returned, the connection is working.
   - **Jira**: Use the Jira MCP tool to list available projects. If projects are returned, the connection is working.
   - **Graphify**: Call the `graph_stats` MCP tool. If it returns node/edge counts, the knowledge graph is accessible.

   **Troubleshooting** — if verification fails:
   - Check that API tokens are valid and not expired
   - Verify permissions: Linear API key needs read/write scopes; Jira token needs project read access
   - Confirm network connectivity to the service (Linear API, your Atlassian instance)
   - Restart Claude Code after adding MCP server config (plugins load at startup)
   - Run `/mcp` to verify the MCP server appears in the active server list

7. **Show summary**: Display the final integration status and which agents benefit:

```
Integrations Updated
━━━━━━━━━━━━━━━━━━━

GitHub:  ✅ Connected (gh CLI, repo: org/my-app)
Linear:  ⚠️  Not configured
Jira:    ⚠️  Not configured

Agents with enhanced capabilities:
  → researcher: can read GitHub issues, discussions
  → architect: can link designs to issues/tickets, query module boundaries
  → code-reviewer: can post review comments on PRs, analyze blast radius via graph
  → devops: can create PRs, manage releases
  → integration-tester: can read test-related issues
  → backend: can query callers/dependencies before modifying code

Run /hody-workflow:connect again to add more integrations.
```

## Notes

- Integrations are optional — all agents work without them
- MCP servers run locally and connect via stdio — no data sent to third parties beyond the configured service
- Integration config is stored in `.hody/profile.yaml` (project-level) and Claude Code MCP settings (user-level)
- Run `/hody-workflow:connect` again to add or change integrations
- Agents check `integrations:` in profile.yaml at bootstrap to know which tools are available
