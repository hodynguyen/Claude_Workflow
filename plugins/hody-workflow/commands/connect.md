---
description: Configure MCP server integrations for the project. Connects agents to external tools like GitHub, Linear, and Jira. Auto-installs MCP server if all required fields are passed; otherwise prompts for missing values.
argument-hint: "[integration] [--api-token X --site Y --email Z ...] OR 'list' OR 'disable <name>'"
---

# /hody-workflow:connect

Configure MCP (Model Context Protocol) server integrations so agents can interact with external tools.

## User Instructions

$ARGUMENTS

Parse the section above as `<integration> [--field value ...]`:

- `jira`, `linear`, `github`, `graphify` → configure the named integration
- `list` (alias: `status`) → show currently configured integrations, don't add
- `disable <name>` (alias: `remove <name>`) → remove that integration from settings + profile.yaml
- Multiple integration names without flags (e.g. `linear jira`) → configure each interactively

**Auto-setup vs interactive flow:**

- If all required `--field` flags for the chosen integration are present, run setup non-interactively (no questions, just write settings + profile, then tell user to restart).
- If any required field is missing, list the missing fields with their guidance, then prompt the user one by one. Never proceed without valid values.
- Tokens and secrets entered interactively must NOT be echoed in the next reply or stored anywhere outside `.claude/settings.json`.

**Required fields per integration** (see `mcp_setup.py fields <name>` for canonical source):

| Integration | Required flags | Where to get the value |
|-------------|---------------|------------------------|
| `jira` | `--api-token`, `--site`, `--email` | Token: <https://id.atlassian.com/manage-profile/security/api-tokens>. Site: e.g. `https://your-org.atlassian.net`. Email: your Atlassian account email. |
| `linear` | `--api-key` | Linear → Settings → API → Personal API keys |
| `github` | `--token` (PAT) | <https://github.com/settings/tokens> (scopes: `repo`, `read:org`). Optional — `gh` CLI is the default route. |
| `graphify` | (none — automated) | Run setup script directly. |

If empty input, guide the user through available integrations interactively.

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

### Linear / Jira / GitHub Setup (auto-install)

These three integrations share the same setup flow via `mcp_setup.py`. The script writes `.claude/settings.json` (merging with existing servers) and flips `integrations.<name>: true` in `.hody/profile.yaml`.

**Step 1 — Check for required fields in $ARGUMENTS.**

Required field maps:

- `jira`: `--api-token`, `--site`, `--email`
- `linear`: `--api-key`
- `github`: `--token`

**Step 2 — If all required fields are provided, run non-interactively:**

```bash
python3 ${PLUGIN_ROOT}/skills/project-profile/scripts/mcp_setup.py jira \
  --cwd . \
  --api-token "<token>" \
  --site "<https://your-org.atlassian.net>" \
  --email "<email>"
```

Output is JSON describing what was written. After success, tell the user:

```
✅ jira MCP configured in .claude/settings.json
   profile.yaml updated: integrations.jira = true
   ⚠️  Restart Claude Code for the MCP server to load.
   Verify with /mcp after restart, or ask Claude to "list available Jira projects".
```

**Step 3 — If any field is missing, ask the user.** Display a guidance block first so they know exactly what to provide:

```
Jira MCP needs 3 fields. Please provide:

  --api-token   Atlassian API token
                Create at https://id.atlassian.com/manage-profile/security/api-tokens
  --site        Your Jira URL
                e.g. https://acme.atlassian.net  (no trailing slash)
  --email       Atlassian account email
                The email you log into Atlassian with

You provided: --api-token=*** (others missing)
Reply with the missing values, or re-run as:
  /hody-workflow:connect jira --api-token=... --site=... --email=...
```

For Linear / GitHub use the same pattern — list each missing field, the env var it maps to, and where to get the value. Use `mcp_setup.py fields <name>` to fetch the canonical field list as JSON if needed.

**Step 4 — When user replies with the missing values, run the setup script with the full set of args.**

**Disable / remove** an integration:

```bash
python3 ${PLUGIN_ROOT}/skills/project-profile/scripts/mcp_setup.py remove jira --cwd .
```

This drops the server entry from `.claude/settings.json` and sets `integrations.jira: false` in profile.yaml. Other servers in `mcpServers` are preserved.

**Status / list** of all integrations:

```bash
python3 ${PLUGIN_ROOT}/skills/project-profile/scripts/mcp_setup.py status --cwd .
```

Returns JSON of `configured_in_settings` and `profile_flag` per integration.

### Graphify Setup

Graphify turns the codebase into a queryable knowledge graph using tree-sitter AST extraction. Agents can then query call graphs, module boundaries, and coupling metrics via MCP tools.

Run the automated setup script:

```bash
python3 ${PLUGIN_ROOT}/skills/project-profile/scripts/graphify_setup.py --cwd .
```

The script handles all steps automatically:
1. Finds a suitable Python >= 3.10 interpreter
2. Installs `graphifyy` if missing (handles PEP 668 / externally-managed environments)
3. Builds the knowledge graph (AST extraction, no LLM) into `graphify-out/graph.json`
4. Configures the MCP server in `.claude/settings.json`
5. Adds `integrations.graphify: true` to `.hody/profile.yaml`
6. Adds `graphify-out/` to `.gitignore`

After the script completes, tell the user to restart Claude Code to activate the MCP server.

**Verify (after restart):** Ask Claude: "What MCP tools do you have from graphify?"

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
