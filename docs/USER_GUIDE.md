# Hody Workflow - User Guide

> How to install, configure, and use the Hody Workflow plugin for Claude Code.

**Current status**: Phase 4 complete (v0.3.19) — 9 agents, 9 commands, 4 output styles, 88 tests.

---

## Table of Contents

- [How the Plugin Works](#how-the-plugin-works)
- [Installation](#installation)
- [Getting Started](#getting-started)
- [Commands Reference](#commands-reference)
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
~/.claude/plugins/cache/hody/hody-workflow/0.3.x/ ← plugin cache (Claude Code reads from here)
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
    └── knowledge/
        ├── architecture.md       ← System overview, components (auto-populated)
        ├── decisions.md          ← ADR-001: tech stack (auto-populated)
        ├── api-contracts.md      ← Detected API endpoints (auto-populated)
        ├── business-rules.md     ← Business logic (template — fill manually)
        ├── tech-debt.md          ← Known issues (template — fill manually)
        └── runbook.md            ← Dev commands, deployment (auto-populated)
```

> **Tip:** Commit `.hody/` to git — it's team knowledge, not temp files.

---

## Commands Reference

| Command | Description |
|---------|-------------|
| `/hody-workflow:init` | Detect stack, create profile + populate knowledge base |
| `/hody-workflow:start-feature` | Start guided feature development workflow |
| `/hody-workflow:status` | View profile + KB summary + suggested next steps |
| `/hody-workflow:refresh` | Re-detect stack, update profile.yaml |
| `/hody-workflow:kb-search` | Search across knowledge base files |
| `/hody-workflow:connect` | Configure MCP integrations (GitHub, Linear, Jira) |
| `/hody-workflow:ci-report` | Generate CI-compatible test reports |
| `/hody-workflow:sync` | Sync knowledge base with team |
| `/hody-workflow:update-kb` | Rescan codebase and refresh knowledge base |

### `/hody-workflow:start-feature`

Describe your feature → plugin classifies it (new-feature, bug-fix, refactor, etc.) → recommends agent workflow:

```
THINK:  researcher → architect
BUILD:  frontend + backend (parallel)
VERIFY: unit-tester → integration-tester → code-reviewer → spec-verifier
SHIP:   devops
```

### `/hody-workflow:status`

Shows: stack summary, KB overview (filled vs empty sections), suggested next steps.

### `/hody-workflow:refresh`

Re-detect stack when you add/remove dependencies, change framework, or restructure your project.

### `/hody-workflow:kb-search`

Search keywords and topics across `.hody/knowledge/` files.

### `/hody-workflow:connect`

Configure MCP servers (GitHub, Linear, Jira). After connecting, agents can read/create PRs, issues, and comments. Supports search, read, create, and transition operations for all 3 platforms.

### `/hody-workflow:ci-report`

Generate CI-compatible test reports (GitHub Actions annotations, JUnit XML, Markdown summary).

### `/hody-workflow:sync`

Push/pull `.hody/knowledge/` to a shared location (git branch, Gist, shared repo) for team collaboration.

### `/hody-workflow:update-kb`

Rescan the codebase and update `.hody/knowledge/` files with the latest architecture, API routes, and runbook commands.

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
1. /hody-workflow:init                    ← Run once (detect + populate KB)
2. /hody-workflow:connect                 ← Connect GitHub/Linear (optional, once)
3. /hody-workflow:start-feature           ← Guided workflow
4. THINK: researcher → architect          ← Research + design
5. BUILD: frontend + backend              ← Implement
6. VERIFY: testers + reviewers            ← Test + review
7. git commit → quality_gate.py           ← Auto security check before commit
8. SHIP: devops                           ← Deploy (optional)
9. /hody-workflow:ci-report               ← Generate test report for CI (optional)
10. Knowledge base accumulates             ← Context for future sessions
11. /hody-workflow:sync                   ← Share KB with team (optional)
```

---

## SessionStart Hook (automatic)

Every time you open a new Claude Code session in a project that has been initialized:
- Hook reads `.hody/profile.yaml`
- **Auto-refresh**: if config files (package.json, go.mod, etc.) are newer than profile.yaml → automatically re-detects
- Injects project context into the system message
- All agents automatically know the tech stack — no need to remind them

---

## Pre-commit Quality Gate

The `quality_gate.py` hook runs before every commit:
- Checks for security issues (API keys, secrets, hardcoded passwords)
- Checks file size limits
- Skips binary files, node_modules, vendor, lock files
- Test files are exempt from security checks

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
