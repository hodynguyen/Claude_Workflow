---
description: Configure MCP server integrations for the project. Connects agents to external tools like GitHub, Linear, and Jira.
---

# /hody-workflow:connect

Configure MCP (Model Context Protocol) server integrations so agents can interact with external tools.

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

5. **Update profile.yaml**: After configuration, add or update the `integrations:` section in `.hody/profile.yaml`:

```yaml
integrations:
  github: true       # gh CLI authenticated or MCP server configured
  linear: false
  jira: false
```

6. **Verify connection**: For each configured integration, run a quick test:
   - GitHub: `gh repo view --json name` (verify repo access)
   - Linear/Jira: check if MCP server responds

7. **Show summary**: Display the final integration status and which agents benefit:

```
Integrations Updated
━━━━━━━━━━━━━━━━━━━

GitHub:  ✅ Connected (gh CLI, repo: org/my-app)
Linear:  ⚠️  Not configured
Jira:    ⚠️  Not configured

Agents with enhanced capabilities:
  → researcher: can read GitHub issues, discussions
  → architect: can link designs to issues/tickets
  → code-reviewer: can post review comments on PRs
  → devops: can create PRs, manage releases
  → integration-tester: can read test-related issues

Run /hody-workflow:connect again to add more integrations.
```

## Notes

- Integrations are optional — all agents work without them
- MCP servers run locally and connect via stdio — no data sent to third parties beyond the configured service
- Integration config is stored in `.hody/profile.yaml` (project-level) and Claude Code MCP settings (user-level)
- Run `/hody-workflow:connect` again to add or change integrations
- Agents check `integrations:` in profile.yaml at bootstrap to know which tools are available
