# Hody Workflow

> A project-aware development workflow plugin for Claude Code with specialized AI agents.

**Documentation**: [User Guide](./docs/USER_GUIDE.md) | [Architecture](./docs/ARCHITECTURE.md) | [Proposal](./docs/PROPOSAL.md) | [Roadmap](./docs/ROADMAP.md)

---

## Features

- **Auto stack detection** — scans `package.json`, `go.mod`, `requirements.txt`, `Cargo.toml`, `pom.xml`, `.csproj`, `Gemfile`, `composer.json`, monorepo configs, and more
- **Monorepo support** — detects Nx, Turborepo, Lerna, pnpm workspaces and builds per-workspace profiles
- **Knowledge base** — 6 persistent markdown files (architecture, decisions, api-contracts, business-rules, tech-debt, runbook) that accumulate project context across sessions, with search support
- **9 specialized agents** across 4 groups with collaboration: THINK (researcher, architect), BUILD (frontend, backend), VERIFY (code-reviewer, spec-verifier, unit-tester, integration-tester), SHIP (devops)
- **Guided workflows** — `/hody-workflow:start-feature` maps your task to the right agent sequence
- **Output styles** — standardized templates for review reports, test reports, and design docs
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
3. Create `.hody/knowledge/` with 6 files
4. Populate knowledge base with real project data (architecture, API routes, runbook commands, tech stack ADR)
5. Display a summary of detected technologies and populated knowledge

### Generated structure

```
my-app/
└── .hody/
    ├── profile.yaml              # Tech stack (auto-generated)
    └── knowledge/
        ├── architecture.md       # System overview, components, data flow (auto-populated)
        ├── decisions.md          # ADR-001: initial tech stack (auto-populated)
        ├── api-contracts.md      # Detected API endpoints (auto-populated)
        ├── business-rules.md     # Business logic (template — fill manually)
        ├── tech-debt.md          # Known issues (template — fill manually)
        └── runbook.md            # Dev commands, deployment (auto-populated)
```

> **Tip:** Commit `.hody/` to git — it's team knowledge, not temp files.

### Start a feature workflow

```
/hody-workflow:start-feature
```

This classifies your task (new feature, bug fix, refactor, etc.) and recommends an agent sequence:

```
THINK:  researcher → architect
BUILD:  frontend + backend (parallel)
VERIFY: unit-tester → integration-tester → code-reviewer → spec-verifier
SHIP:   devops
```

### Call agents directly

```
# Code review
"Use agent code-reviewer to review the auth module"

# Architecture design
"Use agent architect to design the payment system"

# Unit tests
"Use agent unit-tester to write tests for src/utils/validator.ts"

# Research
"Use agent researcher to compare state management libraries"

# Check project status
/hody-workflow:status
```

### Available agents

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

### How it works

```
Session starts
  → [SessionStart hook] reads .hody/profile.yaml, injects into system message
  → Every agent automatically knows your tech stack
  → Agent reads .hody/knowledge/* for accumulated context
  → Agent does work + writes new knowledge back
```

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

## Development Progress

### Phase 1: Foundation (MVP) — Complete

| # | Task | Status |
|---|------|--------|
| 1 | Repo setup + .gitignore | Done |
| 2 | Marketplace config | Done |
| 3 | Plugin structure + `plugin.json` | Done |
| 4 | SessionStart hook | Done |
| 5 | `detect_stack.py` — auto stack detection | Done |
| 6 | Knowledge base templates (6 files) | Done |
| 7 | `SKILL.md` for project-profile | Done |
| 8 | `/hody-workflow:init` command | Done |
| 9 | 3 MVP agents (architect, code-reviewer, unit-tester) | Done |
| 10 | Unit tests (20 tests) | Done |

### Phase 2: Full Agent Suite — Complete

| # | Task | Status |
|---|------|--------|
| 1 | 6 remaining agents (researcher, frontend, backend, spec-verifier, integration-tester, devops) | Done |
| 2 | Output styles (review-report, test-report, design-doc) | Done |
| 3 | `/hody-workflow:start-feature` command | Done |
| 4 | `/hody-workflow:status` command | Done |
| 5 | Extended stack detection (Rust, Java/Kotlin, Angular, Svelte) | Done |
| 6 | Unit tests expanded (31 tests) | Done |

### Phase 3: Intelligence — Complete

| # | Task | Status |
|---|------|--------|
| 1 | C#/.NET stack detection (.csproj, .sln, ASP.NET, Entity Framework) | Done |
| 2 | Ruby stack detection (Gemfile, Rails, RSpec, Sinatra) | Done |
| 3 | PHP stack detection (composer.json, Laravel, Symfony, PHPUnit) | Done |
| 4 | Monorepo detection (nx, turborepo, lerna, pnpm-workspaces) | Done |
| 5 | Monorepo profile format (workspace-level profile.yaml) | Done |
| 6 | Auto-update profile (`/hody-workflow:refresh` command) | Done |
| 7 | Knowledge base search (`/hody-workflow:kb-search` command) | Done |
| 8 | Agent collaboration patterns (delegation) | Done |
| 9 | Unit tests for new stacks + monorepo (47 tests) | Done |
| 10 | Docs update | Done |

### Phase 4: Ecosystem — Complete

| # | Task | Status |
|---|------|--------|
| 1 | Auto-profile refresh hook (detect stale `profile.yaml` on session start) | Done |
| 2 | Pre-commit quality gate (`quality_gate.py` hook) | Done |
| 3 | CI test report generation (`ci-report` output style, `/hody-workflow:ci-report`) | Done |
| 4 | MCP GitHub integration (`/hody-workflow:connect`, agents read/create PRs & issues) | Done |
| 5 | Agent MCP tool access (`## MCP Tools` section in agent prompts) | Done |
| 6 | Team KB sync (`/hody-workflow:sync`, push/pull knowledge base) | Done |
| 7 | Unit tests for Phase 4 (88 total) | Done |
| 8 | MCP issue tracker integration (Linear, Jira workflows in agent prompts) | Done |
| 9 | Refactor `detect_stack.py` into modular `detectors/` package (SRP) | Done |
| 10 | Docs update | Done |

See the [Roadmap](./docs/ROADMAP.md) for technical details and future plans.

---

## Project Structure

```
Claude_Workflow/
├── .claude-plugin/
│   └── marketplace.json              # Marketplace: name "hody"
├── plugins/
│   └── hody-workflow/
│       ├── .claude-plugin/
│       │   └── plugin.json           # Plugin metadata
│       ├── agents/                   # 9 specialized agents
│       │   ├── architect.md          # THINK — system design
│       │   ├── researcher.md         # THINK — research & comparison
│       │   ├── frontend.md           # BUILD — UI implementation
│       │   ├── backend.md            # BUILD — API & business logic
│       │   ├── code-reviewer.md      # VERIFY — code quality
│       │   ├── spec-verifier.md      # VERIFY — spec compliance
│       │   ├── unit-tester.md        # VERIFY — unit tests
│       │   ├── integration-tester.md # VERIFY — API & E2E tests
│       │   └── devops.md             # SHIP — CI/CD & infra
│       ├── output-styles/            # Standardized output templates
│       │   ├── review-report.md
│       │   ├── test-report.md
│       │   ├── design-doc.md
│       │   └── ci-report.md
│       ├── skills/
│       │   ├── project-profile/
│       │   │   ├── SKILL.md
│       │   │   └── scripts/
│       │   │       ├── detect_stack.py       # CLI wrapper (backward-compatible)
│       │   │       └── detectors/            # Modular detection package (16 modules)
│       │   └── knowledge-base/
│       │       └── templates/        # 6 KB template files
│       ├── hooks/
│       │   ├── hooks.json            # SessionStart hook config
│       │   ├── inject_project_context.py
│       │   └── quality_gate.py       # Pre-commit quality gate
│       └── commands/
│           ├── init.md               # /hody-workflow:init
│           ├── start-feature.md      # /hody-workflow:start-feature
│           ├── status.md             # /hody-workflow:status
│           ├── refresh.md            # /hody-workflow:refresh
│           ├── kb-search.md          # /hody-workflow:kb-search
│           ├── connect.md            # /hody-workflow:connect
│           ├── ci-report.md          # /hody-workflow:ci-report
│           ├── sync.md              # /hody-workflow:sync
│           └── update-kb.md         # /hody-workflow:update-kb
├── test/                             # 88 unit tests across 13 files
│   ├── test_detect_stack.py          # Integration test (backward-compat imports)
│   ├── test_node_detector.py         # Node.js detector tests
│   ├── test_go_detector.py           # Go detector tests
│   ├── test_python_detector.py       # Python detector tests
│   ├── test_rust_detector.py         # Rust detector tests
│   ├── test_java_detector.py         # Java detector tests
│   ├── test_csharp_detector.py       # C# detector tests
│   ├── test_ruby_detector.py         # Ruby detector tests
│   ├── test_php_detector.py          # PHP detector tests
│   ├── test_devops.py                # DevOps + database tests
│   ├── test_monorepo.py              # Monorepo detection tests
│   ├── test_serializer.py            # YAML serializer tests
│   ├── test_auto_refresh.py          # Auto-refresh + integrations tests
│   ├── test_quality_gate.py          # Quality gate tests
│   └── test_kb_sync.py              # KB sync tests
├── docs/                             # Documentation
│   ├── PROPOSAL.md                   # Vision, goals, build guide
│   ├── ARCHITECTURE.md               # Technical architecture
│   ├── ROADMAP.md                    # All phases, task tracking
│   └── USER_GUIDE.md                # Installation, usage, commands
├── CLAUDE.md                         # Instructions for Claude Code
└── README.md                         # This file
```

---

## License

MIT
