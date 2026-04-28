# Hody Workflow - User Guide

> How to install, configure, and use the Hody Workflow plugin for Claude Code.

**Current status**: v0.12.0 — 9 agents, 14 commands, 4 output styles, 6 agent contracts, Graphify knowledge graph, project rules, interaction tracker, 3 execution modes, auto-track hook, MCP auto-setup for Jira/Linear/GitHub, 615 tests.

---

## Table of Contents

- [How the Plugin Works](#how-the-plugin-works)
- [Installation](#installation)
- [Getting Started](#getting-started)
- [Commands Reference](#commands-reference)
- [Project Rules](#project-rules)
- [Interaction Tracker](#interaction-tracker)
- [Graphify Knowledge Graph](#graphify-knowledge-graph)
- [Configurable Quality Gate](#configurable-quality-gate)
- [Team Roles & Permissions](#team-roles--permissions)
- [Agents Reference](#agents-reference)
- [Supported Stacks](#supported-stacks)
- [Complete Feature Workflow](#complete-feature-workflow)
- [SessionStart Hook (automatic)](#sessionstart-hook-automatic)
- [Pre-commit Quality Gate](#pre-commit-quality-gate)
- [For Plugin Developers (Distribution)](#for-plugin-developers-distribution)
- [Troubleshooting](#troubleshooting)

---

## How the Plugin Works

```
GitHub repo (hodynguyen/Claude_Workflow)
    ↓  /plugin marketplace add → git clone
~/.claude/plugins/marketplaces/hody/              ← cloned repo
    ↓  /plugin install → copy files
~/.claude/plugins/cache/hody/hody-workflow/0.9.x/ ← plugin cache (Claude Code reads from here)
    ↓  restart Claude Code
Plugin loaded: hooks, agents, skills, commands
```

Important notes:
- The plugin does **not auto-update** when the developer pushes new code
- Claude Code reads the plugin from **cache**, not directly from the marketplace clone
- You must **restart** Claude Code after each install/update to load the new plugin

---

## Installation

### For Users (Installing the Plugin)

#### First-time setup

```bash
# 1. Open Claude Code
claude

# 2. Add marketplace (only once)
/plugin marketplace add hodynguyen/Claude_Workflow

# 3. Install plugin
/plugin install hody-workflow@hody

# 4. Restart Claude Code
# Exit (Ctrl+C) then reopen
claude
```

#### Choose installation scope

| Scope | Stored in | Who can use it | Commit to git? |
|-------|-----------|----------------|----------------|
| **User** | `~/.claude/settings.json` | You, in all projects | No |
| **Project** | `.claude/settings.json` | Entire team who clones the repo | Yes |
| **Local** | `.claude/settings.local.json` | Only you, only this project | No (gitignored) |

- **Personal use** → choose User (plugin available in all projects)
- **Team sharing** → choose Project (commit `.claude/settings.json`, teammates get it automatically)
- **Testing/development** → choose Local (doesn't affect anyone)

Priority: Local > Project > User (higher scope overrides lower scope)

#### Updating to a new version

When the developer pushes new code:

```bash
# Open Claude Code
claude

# Run 2 commands:
/plugin marketplace update
/plugin update hody-workflow@hody

# Restart Claude Code
```

Or enable auto-update:
```
/plugin → Marketplaces → hody → Enable auto-update
```

---

## Getting Started

### Initialize in any project

```bash
cd ~/projects/my-app
claude

# Inside Claude Code:
/hody-workflow:init
```

This will:
1. Run `detect_stack.py` to scan project files → create `.hody/profile.yaml`
2. Create `.hody/knowledge/` with 6 files
3. **Populate knowledge base** — scan codebase and fill with real content:
   - `architecture.md` — directory structure, components, data flow, tech stack rationale
   - `api-contracts.md` — auto-detected API routes from code
   - `decisions.md` — ADR-001 documenting tech stack choices
   - `runbook.md` — dev commands from package.json, Makefile, docker-compose
   - `business-rules.md` + `tech-debt.md` — templates (fill manually)
4. Build KB index (`_index.json`)
5. Initialize tracker database (`.hody/tracker.db`)
6. Create project rules template (`.hody/rules.yaml`)
7. Optionally build Graphify knowledge graph (`/init --graph`)
8. Display summary

### Files created in your project

```
my-app/
└── .hody/
    ├── profile.yaml              ← Tech stack (auto-generated)
    ├── state.json                ← Workflow state (created by /start-feature)
    ├── tracker.db                ← Interaction tracker (local-only, gitignored)
    ├── rules.yaml                ← Project rules — coding, architecture, testing (user-authored)
    ├── quality-rules.yaml        ← Quality gate config (optional)
    ├── team.yaml                 ← Team roles & permissions (optional)
    └── knowledge/
        ├── architecture.md       ← System overview, components (auto-populated)
        ├── decisions.md          ← ADR-001: tech stack (auto-populated)
        ├── api-contracts.md      ← Detected API endpoints (auto-populated)
        ├── business-rules.md     ← Business logic (template — fill manually)
        ├── tech-debt.md          ← Known issues (template — fill manually)
        ├── runbook.md            ← Dev commands, deployment (auto-populated)
        ├── spec-*.md             ← Feature specs (created by /start-feature)
        ├── log-*.md              ← Per-feature work logs (created by /start-feature)
        ├── _index.json           ← Tag/agent/section index (auto-generated cache)
        └── archive/              ← Auto-archived old sections (when files > 500 lines)
```

> **Tip:** Commit `.hody/` to git — it's team knowledge, not temp files.

---

## Commands Reference

| Command | Description |
|---------|-------------|
| `/hody-workflow:init` | Detect stack, create profile + populate knowledge base |
| `/hody-workflow:start-feature` | Start guided feature development workflow |
| `/hody-workflow:status` | View profile + KB summary + workflow progress |
| `/hody-workflow:resume` | Resume an interrupted workflow from last checkpoint |
| `/hody-workflow:refresh` | Re-detect stack, update profile.yaml |
| `/hody-workflow:kb-search` | Search across knowledge base files (keyword, tag, agent) |
| `/hody-workflow:connect` | Configure MCP integrations (GitHub, Linear, Jira) |
| `/hody-workflow:ci-report` | Generate CI-compatible test reports |
| `/hody-workflow:sync` | Sync knowledge base with team |
| `/hody-workflow:update-kb` | Rescan codebase and refresh knowledge base |
| `/hody-workflow:health` | Project health dashboard with metrics and recommendations |
| `/hody-workflow:track` | Create, update, list tracked items (tasks, investigations, questions) |
| `/hody-workflow:history` | View interaction history and session timeline |
| `/hody-workflow:rules` | View, validate, or initialize project rules |

All commands support `$ARGUMENTS` — pass parameters inline (e.g., `/status verbose`, `/kb-search tag:auth`, `/rules init`).

### `/hody-workflow:start-feature`

Describe your feature → plugin classifies it (new-feature, bug-fix, refactor, etc.) → recommends agent workflow → creates `.hody/state.json` to track progress.

**Three execution modes:**

| Mode | Command | Behavior |
|------|---------|----------|
| Auto | `/start-feature --auto add OAuth login` | Skip discovery, auto-generate spec, run all agents end-to-end |
| Guided | `/start-feature add OAuth login` | Interactive discovery → confirm spec → auto-run agents |
| Manual | `/start-feature --manual add OAuth login` | Interactive discovery → confirm spec → pause between agents |

```
THINK:  researcher → architect
BUILD:  frontend + backend (parallel)
VERIFY: unit-tester → integration-tester → code-reviewer → spec-verifier
SHIP:   devops
```

Workflow state (including execution mode) persists across sessions. Use `/hody-workflow:resume` to continue.

### `/hody-workflow:status`

Shows: stack summary, KB overview (filled vs empty sections), active workflow progress, execution mode, suggested next steps.

### `/hody-workflow:resume`

Resume an interrupted workflow. Respects the persisted execution mode. Override with `auto`, `manual`, or `guided` argument. Shows completed agents with summaries, identifies the next agent.

### `/hody-workflow:refresh`

Re-detect stack when you add/remove dependencies, change framework, or restructure your project.

Add `--deep` to run full dependency analysis (dependency counts, outdated packages, security vulnerabilities). Requires the relevant package manager CLI (npm, pip, go, cargo).

### `/hody-workflow:kb-search`

Search across `.hody/knowledge/` files. Supports:
- **Keyword search**: find any word/phrase across all KB files
- **Tag search**: `tag:auth` — find files tagged with a topic
- **Agent search**: `agent:architect` — find entries by author agent
- **Status filter**: `status:active` or `status:superseded`

### `/hody-workflow:connect`

Configure MCP servers (GitHub, Linear, Jira). After connecting, agents can read/create PRs, issues, and comments.

**Auto-setup mode (v0.12.0+):** pass all required fields and the command writes `.claude/settings.json` + flips `integrations.<name>: true` in `profile.yaml` without asking. Restart Claude Code to activate.

```
/hody-workflow:connect jira --api-token=<token> --site=https://acme.atlassian.net --email=me@acme.com
/hody-workflow:connect linear --api-key=<key>
/hody-workflow:connect github --token=<pat>
```

**Interactive mode:** if any required field is missing, the command lists exactly what's needed and where to get each value, then prompts you. No copy-paste of JSON.

| Integration | Required flags | Where to get the value |
|------------|---------------|------------------------|
| `jira` | `--api-token`, `--site`, `--email` | Token: <https://id.atlassian.com/manage-profile/security/api-tokens>. Site: `https://your-org.atlassian.net`. Email: your Atlassian account. |
| `linear` | `--api-key` | Linear → Settings → API → Personal API keys |
| `github` | `--token` | <https://github.com/settings/tokens> (`repo`, `read:org`). Optional — `gh` CLI is the default route. |
| `graphify` | (none — runs an automated setup script) | — |

**Other actions:**

```
/hody-workflow:connect status        # show what's configured
/hody-workflow:connect disable jira  # remove MCP server entry + flip flag
```

Existing MCP servers in `.claude/settings.json` are preserved; only the target integration's entry is added/replaced/removed.

### `/hody-workflow:ci-report`

Generate CI-compatible test reports (GitHub Actions annotations, JUnit XML, Markdown summary).

### `/hody-workflow:sync`

Push/pull `.hody/knowledge/` to a shared location (git branch, Gist, shared repo) for team collaboration.

### `/hody-workflow:update-kb`

Rescan the codebase and update `.hody/knowledge/` files with the latest architecture, API routes, and runbook commands.

### `/hody-workflow:track`

Create, update, and list tracked items. Types: task, investigation, question. Priorities: high, medium, low.

```
/track create task "Implement OAuth2 login" --priority high
/track update <id> --status done
/track list --status active
```

### `/hody-workflow:history`

View interaction history. Shows tracked items, sessions, and activity timeline.

### `/hody-workflow:rules`

Manage project rules (`.hody/rules.yaml`):

```
/rules show       — display current rules with summary
/rules validate   — check YAML structure
/rules init       — create template with commented examples
/rules add coding:forbidden "Use camelCase for all variables"
```

### `/hody-workflow:health`

Show a comprehensive project health dashboard aggregating:
- **Knowledge Base**: completeness percentage (populated vs template files)
- **Tech Debt**: open items count by priority (high/medium/low)
- **Workflows**: started/completed/aborted counts, completion rate, average agents per workflow
- **Agent Usage**: most-used agents, unused agents flagged
- **Dependencies**: outdated/vulnerable counts (if deep analysis was run)
- **Recommendations**: actionable suggestions based on health data

---

## Project Rules

Define project-specific rules that all 9 agents follow. Create `.hody/rules.yaml`:

```yaml
version: "1"

coding:
  naming:
    - "Use camelCase for variables and functions"
    - "Use PascalCase for components"
  forbidden:
    - "Never use any as TypeScript type"

architecture:
  boundaries:
    - "Services must not import from controllers"
  constraints:
    - "Each module must have an index.ts barrel file"

testing:
  requirements:
    - "Every API endpoint needs integration tests"
  coverage:
    - "Minimum 80% line coverage for src/"

workflow:
  preferences:
    - "Always run code-reviewer before merging"

custom:
  - "All user-facing strings must support i18n"
```

- **Agents read rules at bootstrap** — each agent pays attention to relevant categories (e.g., code-reviewer checks `coding:` + `architecture:` + `testing:`)
- **Hook injection** — rules summary is injected into every session's system message
- **Separate from quality-rules.yaml** — `rules.yaml` is user-authored behavioral guidance; `quality-rules.yaml` is automated pre-commit checks

Run `/rules init` to create a template, then uncomment and customize rules for your project.

---

## Interaction Tracker

The tracker system (`.hody/tracker.db`) provides:

- **Item tracking**: Track tasks, investigations, and questions with priority and status
- **Agent checkpoints**: Agents save progress mid-work so context limit interruptions don't lose progress
- **Session history**: Timeline of all interactions
- **Per-feature work logs**: Each `/start-feature` workflow creates a dedicated log file tracking what each agent did

```
/track create task "Migrate to React 19" --priority high
/track list --status active
/history
```

The tracker database is local-only and should be gitignored. It's automatically created by `/init`.

### Auto-Track (v0.11.0)

`/start-feature` already creates a tracker item for each formal workflow, but most ad-hoc work (quick fixes, small refactors, conversations that turn into tasks) used to slip through. The auto-track hook closes that gap.

**How it works**:

1. Every user prompt passes through a `UserPromptSubmit` hook (`auto_track_hook.py`).
2. The heuristic detector (`auto_track.py`) classifies the prompt as task / bug-fix / investigation, or skips it.
3. If detected with confidence ≥ medium, the hook injects a one-line hint asking Claude to confirm with you and create a tracker item.
4. The hook never auto-creates items, never blocks input, and stays silent on questions, slash commands, and active workflows.

**Detection rules** (skip → no hint):

| Skip if | Example |
|---------|---------|
| Slash / shell / mention prefix | `/status`, `!ls`, `@agent` |
| Short prompt (< 15 chars) | `fix it`, `add` |
| English question word at start | `what`, `how`, `why`, `is`, `does`, `can`, ... |
| Vietnamese question phrase anywhere | `kiểu gì`, `thế nào`, `tại sao`, `hay chưa`, `có thể` |
| Trailing `?` | `something is wrong here?` |
| No imperative verb in first 6 words | `the production server has been down` |
| Active workflow exists in `state.json` | `/start-feature` already tracks it |

**Detected verbs** (first 6 words):

- English: `add, create, build, implement, write, generate, make, develop, update, change, modify, refactor, rewrite, improve, optimize, migrate, fix, patch, resolve, debug, remove, delete, drop, integrate, connect, deploy, release, ship, investigate, explore, research, ...`
- Vietnamese: `thêm, tạo, viết, làm, sửa, chỉnh, đổi, thay, xóa, bỏ, ...`

**Subtype classification**:

- `bug-fix` → prompt mentions `bug`, `error`, `exception`, `broken`, `crash`, `lỗi`, `không chạy`, ...
- `investigation` → prompt mentions `investigate`, `explore`, `research`, `tìm hiểu`, ...
- `feature` → default

**Disable globally** with `HODY_AUTO_TRACK=0`:

```bash
export HODY_AUTO_TRACK=0    # silence the hint for the current shell
```

---

## Graphify Knowledge Graph

Optional AST-based knowledge graph for structural code understanding. Powered by [graphifyy](https://pypi.org/project/graphifyy/) (tree-sitter).

### Setup

```
/init --graph
```

This builds `graphify-out/graph.json` and configures a Graphify MCP server. Restart Claude Code after setup.

### What agents can do with the graph

All 9 agents have access to Graphify MCP tools when configured:

| Tool | Usage |
|------|-------|
| `query_graph(question)` | Natural language query against code structure |
| `get_neighbors(label)` | Find all connected nodes (callers, callees, imports) |
| `get_community(label)` | Identify module boundaries and cohesive components |
| `shortest_path(source, target)` | Trace call chains between components |
| `god_nodes(top_n)` | Find high-coupling nodes (refactor candidates) |
| `graph_stats()` | Codebase shape: node/edge counts, module distribution |
| `get_node(label)` | Get detailed info about a specific node |

### Graph diff tracking

When rebuilding the graph (via `/refresh --graph`), the previous graph is saved as `graph.prev.json`. The `/status` command shows structural changes:

```
Graphify:
  curr: 1420 nodes, 1600 edges
  delta: +28 nodes / -0 nodes, +18 edges / -0 edges
  new god nodes: auth_validate (degree=42)
```

---

## Configurable Quality Gate

The quality gate now supports configurable rules via `.hody/quality-rules.yaml`:

```yaml
version: "1"
rules:
  secrets:
    enabled: true
    severity: error
    custom_patterns:
      - pattern: "STRIPE_[A-Z]+_KEY"
        message: "Stripe key detected"
  security:
    enabled: true
    severity: error
    ignore_paths: ["test/", "*.test.*"]
  debug_statements:
    enabled: true
    severity: warning
    languages:
      javascript: ["console.log", "debugger"]
      python: ["breakpoint()"]
      go: ["fmt.Println"]
  file_size:
    max_kb: 500
    severity: error
```

- **Severity levels**: `error` blocks commits, `warning` allows but prints issues
- **Custom patterns**: add project-specific secret patterns
- **Per-language debug detection**: based on file extension
- Falls back to built-in defaults when no config file exists

---

## Team Roles & Permissions

Define team roles in `.hody/team.yaml`:

```yaml
roles:
  lead:
    can_skip_agents: true
    agents: all
  developer:
    agents: [researcher, architect, frontend, backend, unit-tester]
    requires_review: true
  reviewer:
    agents: [code-reviewer, spec-verifier, integration-tester]
  junior:
    agents: [frontend, backend, unit-tester]
    requires_review: true
members:
  - github: "hodynguyen"
    role: lead
```

| Role | Agents | Can Skip | Review Required |
|------|--------|----------|-----------------|
| lead | all 9 | yes | no |
| developer | 5 | no | yes |
| reviewer | 3 | no | no |
| junior | 3 | no | yes + architect approval |

---

## Agents Reference

### 9 agents across 4 groups

| Group | Agent | Role |
|-------|-------|------|
| THINK | researcher | Research docs, best practices, library comparison |
| THINK | architect | System design, API contracts, ADRs |
| BUILD | frontend | UI components, state management, client-side logic |
| BUILD | backend | API endpoints, business logic, database operations |
| VERIFY | code-reviewer | Code quality, security, performance review |
| VERIFY | spec-verifier | Verify code matches specs and business rules |
| VERIFY | unit-tester | Unit tests for functions and components |
| VERIFY | integration-tester | API tests, E2E tests, business flow tests |
| SHIP | devops | CI/CD, Docker, infrastructure, deployment |

### Agent Contracts

When agents hand off work to each other, contracts in `agents/contracts/` define what the receiving agent should expect. At bootstrap, agents check if the previous agent provided the required sections in the KB. This is advisory — agents warn but don't block if something is missing.

| Contract | What it checks |
|----------|---------------|
| architect → backend | API endpoints, data models, architecture.md updated |
| architect → frontend | Component hierarchy, state management, API contracts |
| backend → unit-tester | Implementation files listed, test strategy, edge cases |
| code-reviewer → builder | Issues categorized, file:line references, suggested fixes |
| unit-tester → integration-tester | Coverage summary, integration boundaries |
| spec-verifier → code-reviewer | Spec compliance checklist, deviations flagged |

### Calling agents directly

```
# Research
"Use agent researcher to compare state management libraries"

# Architecture design
"Use agent architect to design the payment system"

# Frontend
"Use agent frontend to build the login page"

# Backend
"Use agent backend to implement the auth API"

# Code review
"Use agent code-reviewer to review the auth module"

# Verify specs
"Use agent spec-verifier to check if code matches API contracts"

# Unit tests
"Use agent unit-tester to write tests for src/utils/validator.ts"

# Integration tests
"Use agent integration-tester to test the auth flow"

# DevOps
"Use agent devops to set up GitHub Actions CI pipeline"
```

---

## Supported Stacks

| Stack | Detection source |
|-------|-----------------|
| Node.js + React/Vue/Angular/Svelte/SvelteKit/Next/Nuxt | `package.json` dependencies |
| Go + Gin/Echo/Fiber | `go.mod` |
| Python + Django/FastAPI/Flask | `requirements.txt`, `pyproject.toml` |
| Rust + Actix-web/Rocket/Axum | `Cargo.toml` |
| Java/Kotlin + Spring Boot/Quarkus/Micronaut | `pom.xml`, `build.gradle` |
| C#/.NET + ASP.NET Core/Blazor | `.csproj`, `.sln`, `global.json` |
| Ruby + Rails/Sinatra/Hanami | `Gemfile` |
| PHP + Laravel/Symfony/Magento | `composer.json` |
| Monorepo (Nx/Turborepo/Lerna/pnpm) | `nx.json`, `turbo.json`, `lerna.json`, `pnpm-workspace.yaml` |
| Docker | `Dockerfile`, `docker-compose.yml` |
| CI/CD | `.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile` |
| Infrastructure | `*.tf` (Terraform), `pulumi/` |

---

## Complete Feature Workflow

```
1. /hody-workflow:init                    ← Run once (detect + populate KB + tracker + rules template)
2. /hody-workflow:init --graph            ← Build Graphify knowledge graph (optional)
3. /hody-workflow:rules init              ← Customize project rules (optional)
4. /hody-workflow:connect                 ← Connect GitHub/Linear/Jira (optional, once)
5. /hody-workflow:start-feature           ← Guided workflow → creates state.json
6. THINK: researcher → architect          ← Discovery: research + spec (state tracked, checkpointed)
7. User confirms spec                     ← Spec-driven: review and confirm before BUILD
8. BUILD: frontend + backend              ← Auto-execute against confirmed spec
9. --- close terminal, come back later ---
10. /hody-workflow:resume                 ← Resume from last checkpoint (agent progress preserved)
11. VERIFY: testers + reviewers           ← Test + review (state tracked)
12. git commit → quality_gate.py          ← Configurable quality check before commit
13. SHIP: devops                          ← Deploy (optional)
14. /hody-workflow:ci-report              ← Generate test report for CI (optional)
15. /hody-workflow:health                 ← Check project health (optional)
16. Knowledge base accumulates            ← Context for future sessions
17. /hody-workflow:sync                   ← Share KB with team (optional)
```

---

## SessionStart Hook (automatic)

Every time you open a new Claude Code session in a project that has been initialized:
- Hook reads `.hody/profile.yaml`
- **Auto-refresh**: if config files (package.json, go.mod, etc.) are newer than profile.yaml → automatically re-detects
- Injects project context into the system message
- If `.hody/state.json` exists with an active workflow → injects workflow state (feature name, spec status, next agent)
- If `graphify-out/graph.json` exists → injects graph stats (node/edge counts)
- If `.hody/rules.yaml` exists → injects rules summary
- All agents automatically know the tech stack, workflow state, graph structure, AND project rules — no need to remind them

---

## Pre-commit Quality Gate

The `quality_gate.py` hook runs before every commit with configurable rules:
- **Secrets**: API keys, tokens, passwords, AWS keys, private keys + custom patterns
- **Security**: dangerous function calls, innerHTML, DOM injection, exec anti-patterns
- **Debug statements**: console.log (JS), breakpoint() (Python), fmt.Println (Go)
- **File size**: configurable limit (default 500KB)
- **Severity levels**: `error` blocks commit, `warning` allows but reports
- Skips binary files, node_modules, vendor, lock files
- Test files are exempt from security checks
- Configure via `.hody/quality-rules.yaml` (see Configurable Quality Gate section above)

---

## For Plugin Developers (Distribution)

### Requirements

- Public GitHub repo so users can clone: `hodynguyen/Claude_Workflow`
- Repo contains `.claude-plugin/marketplace.json` at root (already set up)
- Plugin lives in `plugins/hody-workflow/` with `.claude-plugin/plugin.json` (already set up)

### Release workflow

1. **Code & test** locally
2. **Bump version** in `plugins/hody-workflow/.claude-plugin/plugin.json`
3. **Commit & push** to GitHub
4. Done — users update with `/plugin marketplace update` + `/plugin update`

### Pre-push checklist

- [ ] Version bumped in `plugin.json` (if not a README-only change)
- [ ] Tests pass: `python3 -m unittest discover -s test -v`
- [ ] Commit message follows format: `<type>: <description>`
- [ ] No sensitive files committed (`.env`, credentials, `settings.local.json`)

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Plugin doesn't load after install | Restart Claude Code (exit + reopen) |
| Plugin is outdated after push | Run `/plugin marketplace update` then `/plugin update hody-workflow@hody` |
| `/hody-workflow:init` not found | Check if plugin is installed: `/plugin list` |
| Cache is broken | Delete cache: `rm -rf ~/.claude/plugins/cache/hody/hody-workflow/` then reinstall |
