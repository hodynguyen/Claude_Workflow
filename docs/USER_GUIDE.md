# Hody Workflow - User Guide

> How to install, configure, and use the Hody Workflow plugin for Claude Code.

**Current status**: Phase 6 complete (v0.5.0) — 9 agents, 11 commands, 4 output styles, 6 agent contracts, 309 tests.

---

## Table of Contents

- [How the Plugin Works](#how-the-plugin-works)
- [Installation](#installation)
- [Getting Started](#getting-started)
- [Commands Reference](#commands-reference)
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
~/.claude/plugins/cache/hody/hody-workflow/0.5.x/ ← plugin cache (Claude Code reads from here)
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
4. Display summary

### Files created in your project

```
my-app/
└── .hody/
    ├── profile.yaml              ← Tech stack (auto-generated)
    ├── state.json                ← Workflow state (created by /start-feature)
    ├── quality-rules.yaml        ← Quality gate config (optional)
    ├── team.yaml                 ← Team roles & permissions (optional)
    └── knowledge/
        ├── architecture.md       ← System overview, components (auto-populated)
        ├── decisions.md          ← ADR-001: tech stack (auto-populated)
        ├── api-contracts.md      ← Detected API endpoints (auto-populated)
        ├── business-rules.md     ← Business logic (template — fill manually)
        ├── tech-debt.md          ← Known issues (template — fill manually)
        ├── runbook.md            ← Dev commands, deployment (auto-populated)
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

### `/hody-workflow:start-feature`

Describe your feature → plugin classifies it (new-feature, bug-fix, refactor, etc.) → recommends agent workflow → creates `.hody/state.json` to track progress:

```
THINK:  researcher → architect
BUILD:  frontend + backend (parallel)
VERIFY: unit-tester → integration-tester → code-reviewer → spec-verifier
SHIP:   devops
```

Workflow state persists across sessions. If you close the terminal, use `/hody-workflow:resume` to continue.

### `/hody-workflow:status`

Shows: stack summary, KB overview (filled vs empty sections), active workflow progress, suggested next steps.

### `/hody-workflow:resume`

Resume an interrupted workflow. Shows completed agents with summaries, identifies the next agent, and lets you continue, skip, or abort.

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

Configure MCP servers (GitHub, Linear, Jira). After connecting, agents can read/create PRs, issues, and comments. Supports search, read, create, and transition operations for all 3 platforms.

### `/hody-workflow:ci-report`

Generate CI-compatible test reports (GitHub Actions annotations, JUnit XML, Markdown summary).

### `/hody-workflow:sync`

Push/pull `.hody/knowledge/` to a shared location (git branch, Gist, shared repo) for team collaboration.

### `/hody-workflow:update-kb`

Rescan the codebase and update `.hody/knowledge/` files with the latest architecture, API routes, and runbook commands.

### `/hody-workflow:health`

Show a comprehensive project health dashboard aggregating:
- **Knowledge Base**: completeness percentage (populated vs template files)
- **Tech Debt**: open items count by priority (high/medium/low)
- **Workflows**: started/completed/aborted counts, completion rate, average agents per workflow
- **Agent Usage**: most-used agents, unused agents flagged
- **Dependencies**: outdated/vulnerable counts (if deep analysis was run)
- **Recommendations**: actionable suggestions based on health data

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
1. /hody-workflow:init                    ← Run once (detect + populate KB + build index)
2. /hody-workflow:connect                 ← Connect GitHub/Linear (optional, once)
3. /hody-workflow:start-feature           ← Guided workflow → creates state.json
4. THINK: researcher → architect          ← Research + design (state tracked)
5. BUILD: frontend + backend              ← Implement (state tracked)
6. --- close terminal, come back later ---
7. /hody-workflow:resume                  ← Resume from last checkpoint
8. VERIFY: testers + reviewers            ← Test + review (state tracked)
9. git commit → quality_gate.py           ← Configurable quality check before commit
10. SHIP: devops                          ← Deploy (optional)
11. /hody-workflow:ci-report              ← Generate test report for CI (optional)
12. /hody-workflow:health                 ← Check project health (optional)
13. Knowledge base accumulates            ← Context for future sessions
14. /hody-workflow:sync                   ← Share KB with team (optional)
```

---

## SessionStart Hook (automatic)

Every time you open a new Claude Code session in a project that has been initialized:
- Hook reads `.hody/profile.yaml`
- **Auto-refresh**: if config files (package.json, go.mod, etc.) are newer than profile.yaml → automatically re-detects
- Injects project context into the system message
- If `.hody/state.json` exists with an active workflow → injects workflow state (feature name, next agent)
- All agents automatically know the tech stack AND workflow state — no need to remind them

---

## Pre-commit Quality Gate

The `quality_gate.py` hook runs before every commit with configurable rules:
- **Secrets**: API keys, tokens, passwords, AWS keys, private keys + custom patterns
- **Security**: eval(), innerHTML, document.write(), exec() anti-patterns
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
