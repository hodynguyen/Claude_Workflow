# Hody Workflow

> A project-aware development workflow plugin for Claude Code with 9 specialized AI agents.

**Version**: v0.5.0 — All 6 phases complete

**Documentation**: [User Guide](./docs/USER_GUIDE.md) | [Architecture](./docs/ARCHITECTURE.md) | [Proposal](./docs/PROPOSAL.md) | [Roadmap](./docs/ROADMAP.md)

---

## Features

- **Auto stack detection** — scans `package.json`, `go.mod`, `requirements.txt`, `Cargo.toml`, `pom.xml`, `.csproj`, `Gemfile`, `composer.json`, monorepo configs, and more
- **Monorepo support** — detects Nx, Turborepo, Lerna, pnpm workspaces and builds per-workspace profiles
- **Knowledge base** — 6 persistent markdown files with YAML frontmatter, `_index.json` indexing, and auto-archival
- **9 specialized agents** across 4 groups: THINK (researcher, architect), BUILD (frontend, backend), VERIFY (code-reviewer, spec-verifier, unit-tester, integration-tester), SHIP (devops)
- **Workflow state machine** — `.hody/state.json` tracks feature progress across sessions with `/resume`
- **Agent contracts** — 6 typed handoff schemas for validated inter-agent communication
- **Configurable quality gate** — `.hody/quality-rules.yaml` with custom patterns, severity levels, debug detection
- **CI feedback loop** — poll CI status, parse test failures, auto-create tech-debt entries
- **Team roles** — `.hody/team.yaml` with role-based agent access control (lead, developer, reviewer, junior)
- **Health dashboard** — `/hody-workflow:health` aggregates KB completeness, tech debt, workflow stats, recommendations
- **MCP integrations** — connect to GitHub, Linear, and Jira for issue tracking and project management
- **SessionStart hook** — automatically injects your project's tech stack into every Claude Code session

---

## Installation

### 1. Add marketplace

```
/plugin marketplace add hodynguyen/Claude_Workflow
```

### 2. Install plugin

```
/plugin install hody-workflow@hody
```

You'll be prompted to choose a scope:

| Scope | When to use |
|-------|-------------|
| **User** | Personal use — available across all your projects |
| **Project** | Team use — committed to git, teammates get it automatically |
| **Local** | Testing — only you, only this project, gitignored |

### 3. Restart Claude Code

Plugins load at startup — restart is required after install.

---

## Usage

### Initialize in any project

```bash
cd ~/projects/my-app
claude

# Inside Claude Code:
/hody-workflow:init
```

This will:
1. Run `detect_stack.py` to scan your project files
2. Generate `.hody/profile.yaml` with detected stack info
3. Create `.hody/knowledge/` with 6 files (YAML frontmatter + `_index.json`)
4. Populate knowledge base with real project data (architecture, API routes, runbook commands, tech stack ADR)
5. Display a summary of detected technologies and populated knowledge

### Generated structure

```
my-app/
└── .hody/
    ├── profile.yaml              # Tech stack (auto-generated)
    ├── state.json                # Workflow state (created by /start-feature)
    ├── quality-rules.yaml        # Quality gate config (optional)
    ├── team.yaml                 # Team roles & permissions (optional)
    └── knowledge/
        ├── architecture.md       # System overview (auto-populated)
        ├── decisions.md          # ADR-001: tech stack (auto-populated)
        ├── api-contracts.md      # Detected API endpoints (auto-populated)
        ├── business-rules.md     # Business logic (template)
        ├── tech-debt.md          # Known issues (template)
        ├── runbook.md            # Dev commands (auto-populated)
        ├── _index.json           # Tag/agent/section index (auto-generated)
        └── archive/              # Auto-archived old sections
```

> **Tip:** Commit `.hody/` to git — it's team knowledge, not temp files.

### Commands

| Command | Description |
|---------|-------------|
| `/hody-workflow:init` | Detect stack, create profile + populate knowledge base |
| `/hody-workflow:start-feature` | Start guided feature development workflow |
| `/hody-workflow:status` | View profile + KB summary + workflow progress |
| `/hody-workflow:resume` | Resume an interrupted workflow from last checkpoint |
| `/hody-workflow:refresh` | Re-detect stack, update profile.yaml (`--deep` for dependency analysis) |
| `/hody-workflow:kb-search` | Search knowledge base (keyword, tag, agent, status) |
| `/hody-workflow:connect` | Configure MCP integrations (GitHub, Linear, Jira) |
| `/hody-workflow:ci-report` | Generate CI-compatible test reports |
| `/hody-workflow:sync` | Sync knowledge base with team |
| `/hody-workflow:update-kb` | Rescan codebase and refresh knowledge base |
| `/hody-workflow:health` | Project health dashboard with metrics and recommendations |

### Agents

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

### Supported stacks

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

### Updating the plugin

When a new version is released:

```
/plugin marketplace update
/plugin update hody-workflow@hody
# Then restart Claude Code
```

---

## Project Structure

```
Claude_Workflow/
├── .claude-plugin/
│   └── marketplace.json              # Marketplace: name "hody"
├── plugins/
│   └── hody-workflow/
│       ├── .claude-plugin/
│       │   └── plugin.json           # Plugin metadata (v0.5.0)
│       ├── agents/                   # 9 specialized agents
│       │   ├── contracts/            # 6 agent handoff contracts (.yaml)
│       │   ├── architect.md
│       │   ├── researcher.md
│       │   ├── frontend.md
│       │   ├── backend.md
│       │   ├── code-reviewer.md
│       │   ├── spec-verifier.md
│       │   ├── unit-tester.md
│       │   ├── integration-tester.md
│       │   └── devops.md
│       ├── output-styles/            # 4 output templates
│       │   ├── review-report.md
│       │   ├── test-report.md
│       │   ├── design-doc.md
│       │   └── ci-report.md
│       ├── skills/
│       │   ├── project-profile/
│       │   │   ├── SKILL.md
│       │   │   └── scripts/
│       │   │       ├── detect_stack.py       # CLI wrapper
│       │   │       ├── state.py              # Workflow state machine
│       │   │       ├── kb_index.py           # KB index builder
│       │   │       ├── kb_archive.py         # KB auto-archival
│       │   │       ├── contracts.py          # Agent I/O contract validator
│       │   │       ├── quality_rules.py      # Configurable quality rules
│       │   │       ├── ci_monitor.py         # CI feedback loop
│       │   │       ├── team.py               # Team roles & permissions
│       │   │       ├── health.py             # Project health dashboard
│       │   │       └── detectors/            # Modular detection (20 modules)
│       │   └── knowledge-base/
│       │       ├── scripts/
│       │       │   └── kb_sync.py
│       │       └── templates/        # 6 KB template files
│       ├── hooks/
│       │   ├── hooks.json
│       │   ├── inject_project_context.py     # SessionStart + auto-refresh
│       │   └── quality_gate.py               # Pre-commit quality gate (v2)
│       └── commands/                 # 11 commands
│           ├── init.md
│           ├── start-feature.md
│           ├── status.md
│           ├── resume.md
│           ├── refresh.md
│           ├── kb-search.md
│           ├── connect.md
│           ├── ci-report.md
│           ├── sync.md
│           ├── update-kb.md
│           └── health.md
├── test/                             # 309 tests across 25 files
├── docs/
│   ├── PROPOSAL.md
│   ├── ARCHITECTURE.md
│   ├── ROADMAP.md
│   └── USER_GUIDE.md
├── CLAUDE.md
└── README.md
```

---

## Development

```bash
# Run all tests
python3 -m unittest discover -s test -v

# 309 tests covering: per-language detectors, monorepo, devops,
# serializer, quality gate, KB sync, auto-refresh, workflow state,
# KB index/archive, deep analysis, contracts, quality rules,
# CI monitor, team roles, health dashboard
```

---

## License

MIT
