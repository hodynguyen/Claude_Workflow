# Hody Workflow - Development Roadmap

> Single source of truth for all phase tracking and future plans.

**Current version**: v0.4.0

---

## Phase Summary

| Phase | Name | Status | Version |
|-------|------|--------|---------|
| 1 | Foundation (MVP) | Complete | v0.1.0 |
| 2 | Full Agent Suite | Complete | v0.2.0 |
| 3 | Intelligence | Complete | v0.3.6 |
| 4 | Ecosystem | Complete | v0.3.19 |
| 5 | Deep Intelligence | Complete | v0.4.0 |
| 6 | Enterprise Grade | Planned | v0.5.x |

---

## Phase 1: Foundation (MVP) — Complete

**Goal**: Plugin works with 3 basic agents

| # | Task | Status | Date | Description |
|---|------|--------|------|-------------|
| 1 | Repo setup + .gitignore | Done | 18/01 | `.gitignore`, `marketplace.json`, `plugin.json` |
| 2 | Marketplace config | Done | 18/01 | `.claude-plugin/marketplace.json` |
| 3 | Plugin structure + plugin.json | Done | 18/01 | v0.1.0 |
| 4 | SessionStart hook | Done | 18/01 | `inject_project_context.py` + `hooks.json` |
| 5 | README.md | Done | 20/01 | Progress + usage guide |
| 6 | Update author email | Done | 23/01 | marketplace.json + plugin.json |
| 7 | `detect_stack.py` | Done | 24/01 | Auto-detect top 5 popular stacks (Node.js, Go, Python + DevOps/conventions) |
| 8 | Knowledge base templates (6 files) | Done | 25/01 | architecture, decisions, api-contracts, business-rules, tech-debt, runbook |
| 9 | `SKILL.md` for project-profile | Done | 27/01 | Usage docs, detection sources, sample output |
| 10 | `/hody-workflow:init` command | Done | 29/01 | Detect stack + create KB + show summary |
| 11 | 3 MVP agents | Done | 31/01 | **architect**, **code-reviewer**, **unit-tester** |
| 12 | Unit tests | Done | 02/02 | 20 tests, found & fixed backend-only detection bug |

**Deliverable**: User can `/hody-workflow:init` → call 3 agents → agents are aware of project stack

---

## Phase 2: Full Agent Suite — Complete

**Goal**: All 9 agents, task-to-agents mapping

| # | Task | Status | Date | Description |
|---|------|--------|------|-------------|
| 1 | THINK + BUILD agents | Done | 09/02 | 3 new agents: researcher, frontend, backend |
| 2 | VERIFY + SHIP agents | Done | 09/02 | 3 new agents: spec-verifier, integration-tester, devops — all 9 agents complete |
| 3 | Output styles | Done | 09/02 | 3 templates: review-report, test-report, design-doc |
| 4 | `/hody-workflow:start-feature` command | Done | 09/02 | 8 feature types, agent workflow mapping |
| 5 | `/hody-workflow:status` command | Done | 09/02 | Profile + KB overview + suggestions |
| 6 | Extended stack detection | Done | 09/02 | Rust, Java/Kotlin, Angular, Svelte — 31 tests (up from 20) |
| 7 | Update README + bump version | Done | 09/02 | v0.2.0 |

**Deliverable**: Full development workflow running end-to-end

---

## Phase 3: Intelligence — Complete

**Goal**: Smarter detection, richer knowledge base, agent collaboration

| # | Task | Status | Date | Description |
|---|------|--------|------|-------------|
| 1 | C#/.NET stack detection | Done | 10/02 | Detect `.csproj`, `.sln`, `global.json`; frameworks: ASP.NET Core, Blazor; ORM: Entity Framework; test: xUnit, NUnit, MSTest |
| 2 | Ruby stack detection | Done | 10/02 | Detect `Gemfile`, `Rakefile`; frameworks: Rails, Sinatra, Hanami; test: RSpec, Minitest |
| 3 | PHP stack detection | Done | 10/02 | Detect `composer.json`; frameworks: Laravel, Symfony, Magento; test: PHPUnit, Pest |
| 4 | Monorepo detection | Done | 11/02 | Detect `nx.json`, `turbo.json`, `lerna.json`, `pnpm-workspace.yaml`; identify workspace root vs sub-projects |
| 5 | Monorepo profile format | Done | 11/02 | Extend `profile.yaml` with `workspaces[]` — each sub-project has its own language, framework, testing |
| 6 | Auto-update profile | Done | 11/02 | `/hody-workflow:refresh` command to re-run `detect_stack.py` |
| 7 | Knowledge base search | Done | 12/02 | `/hody-workflow:kb-search` — supports keyword search and section filtering |
| 8 | Agent collaboration | Done | 12/02 | `## Collaboration` section in all 9 agent prompts — delegation pattern |
| 9 | Unit tests for new stacks | Done | 13/02 | Tests for C#, Ruby, PHP detection + monorepo — 47 tests (up from 31) |
| 10 | Docs update | Done | 13/02 | Updated README, USAGE_GUIDE with Phase 3 features |

**Technical details**:

- **Monorepo profile format**: `detect_stack.py` checks for monorepo markers at root. If detected, scans each workspace/package to create individual profiles:
  ```yaml
  monorepo:
    tool: turborepo | nx | lerna | pnpm-workspaces
    workspaces:
      - path: packages/frontend
        language: TypeScript
        framework: React
      - path: packages/api
        language: Go
        framework: Gin
  ```
- **Agent collaboration**: Agents have `## Collaboration` section defining when to suggest another agent. No auto-invoke; agents suggest via output message.

**Deliverable**: Plugin detects 8+ stacks + monorepo, has knowledge base search, agents know how to delegate to each other

---

## Phase 4: Ecosystem — Complete

**Goal**: Integration with external tools, CI pipelines, and team collaboration

| # | Task | Status | Date | Description |
|---|------|--------|------|-------------|
| 1 | Auto-profile refresh hook | Done | 14/02 | Enhanced SessionStart hook to check config file modification times vs `profile.yaml`. Auto-re-runs detection if stale. |
| 2 | Pre-commit quality gate | Done | 14/02 | Hook script `quality_gate.py` (PreCommit). Checks security patterns, file size on staged files. Outputs pass/fail. |
| 3 | CI test report generation | Done | 14/02 | Output style `ci-report.md` + `/hody-workflow:ci-report` command. JUnit XML / GitHub Actions / Markdown. |
| 4 | MCP GitHub integration | Done | 14/02 | `/hody-workflow:connect` command. Agents can read issues/PRs, create PRs, post comments. |
| 5 | Preserve integrations | Done | 14/02 | `load_existing_integrations()` preserves user-configured integrations across profile re-detection. |
| 6 | Agent MCP tool access | Done | 14/02 | `## MCP Tools` section added to 5 agent prompts (researcher, architect, code-reviewer, devops, integration-tester). |
| 7 | Team KB sync | Done | 14/02 | `/hody-workflow:sync` command + `kb_sync.py` script. Push/pull `.hody/knowledge/` to shared location. |
| 8 | Unit tests for Phase 4 | Done | 14/02 | 85 tests (up from 47) covering quality gate, KB sync, auto-refresh, integrations. |
| 9 | Refactor detect_stack.py (SRP) | Done | 15/02 | Modularized from 820-line monolith into 16 SRP modules under `detectors/` package. |
| 10 | MCP issue tracker integration | Done | 15/02 | Enhanced 5 agent prompts with Linear/Jira workflows — search, read, create, transition issues. Updated `/connect` verification. |
| 11 | Docs update | Done | 15/02 | Updated README, USAGE_GUIDE, CLAUDE.md, PROGRESS.md, SKILL.md, PROPOSAL.md. |

**Technical details**:

- **Auto-profile refresh**: `inject_project_context.py` compares modification times of key config files against `.hody/profile.yaml`. If any config file is newer, auto-runs `detect_stack.py` before injecting context.
- **Pre-commit quality gate**: `quality_gate.py` checks security patterns (AWS keys, private keys, hardcoded passwords, API keys, eval/innerHTML usage). Skips binary files, node_modules, vendor, dist, lock files. Test files skip security checks.
- **Refactored detect_stack.py**: Modularized from 820-line monolith into 16 SRP modules under `detectors/` package. `detect_stack.py` remains as backward-compatible thin CLI wrapper.

**Deliverable**: Plugin integrates with GitHub/Linear/Jira via MCP, enforces quality gates pre-commit, generates CI-compatible test reports, supports team KB sync, and has modular detection architecture

---

## Phase 5: Deep Intelligence — Planned

**Goal**: Transform agents from prompt-driven tools into context-aware, stateful collaborators.

### Critical Limitation Analysis

Five structural limitations prevent the plugin from scaling beyond individual-developer, small-project usage:

1. **Scalability** — Flat Markdown KB breaks at scale. No structure, indexing, or size management. KB files grow unbounded; keyword search has no ranking; team sync creates merge conflicts.

2. **Intelligence** — Regex detection is shallow. All 16 detector modules use string/substring matching against config files. No version awareness, no transitive dependency analysis, no architectural pattern detection.

3. **Process Enforcement** — Workflow is recommendation-only. `/start-feature` suggests agent sequences but nothing tracks progress, enforces ordering, or persists state between sessions.

4. **Agent Orchestration** — No coordination between agents. "Collaboration" is advisory text only. No schema defining agent inputs/outputs, no validation at handoff, no parallel coordination.

5. **Ecosystem** — Shallow integrations. Quality gate is regex-only. CI integration is one-shot reporting. No feedback loops with external systems.

### Features

| # | Feature | Status | Description |
|---|---------|--------|-------------|
| 1 | Workflow State Machine | Done | `.hody/state.json` with phases, active agent, timestamps, audit log. New `state.py` module. `/hody-workflow:resume` command. |
| 2 | Structured Knowledge Base | Done | YAML frontmatter (tags, date, author-agent) on KB entries. `_index.json` for section-level indexing. Auto-archival for large KB files. |
| 3 | Deep Stack Analysis | Done | Parse actual dependency trees (`npm ls --json`, `pip list`, `go list`, `cargo metadata`). Version conflict detection, security audit. Opt-in via `--deep` flag. |
| 4 | Agent Input/Output Contracts | Done | Typed handoff schemas in `agents/contracts/*.yaml`. Validation at agent bootstrap. Advisory by default. 6 contracts defined. |

#### Feature 5.1: Workflow State Machine

**Problem solved**: No progress tracking, no session persistence.

**Solution**: Introduce `.hody/state.json` that tracks the active workflow, current phase, completed agents, timestamps, and outputs.

**State schema** (`.hody/state.json`):
```json
{
  "workflow_id": "feat-user-auth-20260215",
  "feature": "Add user authentication",
  "type": "new-feature",
  "status": "in_progress",
  "created_at": "2026-02-15T10:30:00Z",
  "updated_at": "2026-02-15T14:22:00Z",
  "phases": {
    "THINK": {
      "agents": ["researcher", "architect"],
      "completed": ["researcher"],
      "active": "architect",
      "skipped": []
    },
    "BUILD": {
      "agents": ["backend", "frontend"],
      "completed": [],
      "active": null,
      "skipped": []
    },
    "VERIFY": { "agents": ["unit-tester", "code-reviewer"], "completed": [], "active": null, "skipped": [] },
    "SHIP": { "agents": ["devops"], "completed": [], "active": null, "skipped": [] }
  },
  "agent_log": [
    {
      "agent": "researcher",
      "started_at": "2026-02-15T10:30:00Z",
      "completed_at": "2026-02-15T10:45:00Z",
      "output_summary": "Researched OAuth2 vs JWT approaches",
      "kb_files_modified": ["decisions.md"]
    }
  ]
}
```

**Implementation**:

| Component | File | Description |
|-----------|------|-------------|
| State manager | `skills/project-profile/scripts/state.py` | Create/read/update `.hody/state.json`; validate phase transitions |
| Hook integration | `hooks/inject_project_context.py` | Inject active workflow state alongside profile into agent context |
| Start-feature update | `commands/start-feature.md` | Create state on workflow start; write initial phases |
| Status update | `commands/status.md` | Read and display workflow progress (phase, active agent, completion %) |
| Resume command | `commands/resume.md` | New command — resume interrupted workflow from last checkpoint |

**Key design decisions**:
- State is a single JSON file (not a database) — keeps the "no dependencies" philosophy
- State transitions are validated: BUILD cannot start until at least one THINK agent completes
- Agent log provides audit trail without requiring external services
- `/hody-workflow:resume` reads state and re-injects context for the next agent

#### Feature 5.2: Structured Knowledge Base

**Problem solved**: Flat markdown doesn't scale.

**Solution**: Add YAML frontmatter to KB entries, section-level indexing, size-based auto-archival.

**KB entry format** (enhanced):
```markdown
---
tags: [authentication, oauth2, backend]
created: 2026-02-15
author_agent: architect
status: active
supersedes: null
---

## OAuth2 Implementation Decision

We chose OAuth2 with PKCE flow for the following reasons...
```

**Implementation**:

| Component | File | Description |
|-----------|------|-------------|
| KB index builder | `skills/project-profile/scripts/kb_index.py` | Parse frontmatter from all KB files; build `.hody/knowledge/_index.json` with tags, dates, sections |
| Enhanced kb-search | `commands/kb-search.md` | Search against `_index.json` first (tag/date/agent filter), then fall back to content search |
| Auto-archival | `skills/project-profile/scripts/kb_archive.py` | When a KB file exceeds 500 lines, move older sections (by date) to `.hody/knowledge/archive/` |
| KB write helper | Agent prompt updates | Agents instructed to include frontmatter when writing KB entries |
| Init update | `commands/init.md` | Generate `_index.json` during init; add frontmatter to templates |

**Key design decisions**:
- Frontmatter is optional — existing KB files without frontmatter still work (backward compatible)
- `_index.json` is a generated cache, not source of truth — can be rebuilt from `.md` files
- Archive threshold is configurable via `.hody/config.yaml` (future)
- Tags enable cross-file discovery: "find all decisions about authentication" across `decisions.md`, `architecture.md`, etc.

#### Feature 5.3: Deep Stack Analysis

**Problem solved**: Regex detection misses real architecture.

**Solution**: Run actual package manager commands to get dependency trees, parse versions, detect conflicts.

**Implementation**:

| Component | File | Description |
|-----------|------|-------------|
| Deep analyzer | `skills/project-profile/scripts/detectors/deep_analysis.py` | Run `npm ls --json`, `pip show`, `go list -m all`, `cargo tree` (when available) |
| Version parser | `skills/project-profile/scripts/detectors/versions.py` | Parse semver, detect major version conflicts, identify deprecated packages |
| Profile extension | `detectors/profile.py` | Add `deep_analysis` section to profile.yaml with dependency tree summary, conflicts, outdated packages |
| Opt-in flag | `commands/refresh.md` | `--deep` flag triggers deep analysis (default: fast regex-only, for speed) |

**Enhanced profile.yaml section**:
```yaml
deep_analysis:
  last_run: "2026-02-15T10:00:00Z"
  dependency_count: 142
  direct: 28
  transitive: 114
  conflicts:
    - package: "@types/react"
      installed: "17.0.2"
      required_by_peer: "18.0.0"
      severity: warning
  outdated:
    - package: "express"
      current: "4.18.2"
      latest: "5.0.1"
      breaking: true
  security:
    - package: "lodash"
      vulnerability: "CVE-2024-XXXX"
      severity: high
```

**Key design decisions**:
- Deep analysis is **opt-in** (`--deep` flag) because it runs shell commands and is slower
- Falls back gracefully if package manager CLI is not available
- Results are cached in profile.yaml — not re-run on every agent bootstrap
- Security vulnerability data comes from `npm audit --json` / `pip audit` / `cargo audit` when available

#### Feature 5.4: Agent Input/Output Contracts

**Problem solved**: No validation between agents.

**Solution**: Define typed handoff schemas for each agent pair; validate at agent bootstrap.

**Contract schema** (`agents/contracts/architect-to-backend.yaml`):
```yaml
contract: architect-to-backend
version: 1
required_sections:
  - name: "API Endpoints"
    format: "table or list with method, path, request/response types"
  - name: "Data Models"
    format: "entity definitions with fields and types"
  - name: "Architecture Decision"
    format: "chosen pattern with rationale"
optional_sections:
  - name: "Sequence Diagrams"
  - name: "Error Handling Strategy"
validation:
  - check: "kb_file_modified"
    file: "architecture.md"
    message: "Architect should update architecture.md before handing off to backend"
  - check: "kb_file_modified"
    file: "api-contracts.md"
    message: "Architect should define API contracts before backend implementation"
```

**Key contracts to define**:

| From | To | Key Requirements |
|------|----|-----------------|
| architect | backend | API endpoints defined, data models specified, architecture.md updated |
| architect | frontend | Component hierarchy, state management approach, API contract for frontend |
| backend | unit-tester | Implementation files listed, test strategy suggested, edge cases identified |
| code-reviewer | backend/frontend | Issues categorized (blocking/non-blocking), specific file:line references |
| unit-tester | integration-tester | Unit test coverage report, identified integration boundaries |
| spec-verifier | code-reviewer | Spec compliance checklist, deviations flagged |

**Deliverable**: Agents have persistent workflow state, structured & searchable KB, real dependency understanding, and validated inter-agent communication

---

## Phase 6: Enterprise Grade — Planned

**Goal**: Make the plugin viable for teams, CI pipelines, and production environments. Builds on Phase 5 foundations.

| # | Feature | Status | Description |
|---|---------|--------|-------------|
| 1 | Quality Gate v2 | Planned | Configurable rules in `.hody/quality-rules.yaml`. Coverage thresholds, dependency audit, severity levels (error/warning). |
| 2 | CI Feedback Loop | Planned | Poll CI status, parse test failures, auto-create tech-debt entries, suggest fixes. `ci_monitor.py` hook. |
| 3 | Team Roles & Permissions | Planned | Role definitions in `.hody/team.yaml` (lead, dev, reviewer). Agent access control, workflow enforcement per role. |
| 4 | Project Health Dashboard | Planned | `/hody-workflow:health` command. Aggregate KB completeness, test coverage trends, tech-debt count, agent usage stats. |

#### Feature 6.1: Quality Gate v2 — Configurable Rule Engine

**Solution**: Configurable quality rules in `.hody/quality-rules.yaml` with severity levels, custom patterns, and integration with language-specific linters.

```yaml
version: 1
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
      python: ["print(", "breakpoint()"]
      go: ["fmt.Println"]
  file_size:
    max_kb: 500
    severity: error
  coverage:
    enabled: false
    min_percentage: 80
    command: "npm run test:coverage -- --json"
  dependency_audit:
    enabled: false
    severity: warning
    command: "npm audit --json"
    fail_on: "high"
```

#### Feature 6.2: CI Feedback Loop

**Solution**: Poll CI status via MCP/GitHub API, parse test failures, auto-create tech-debt entries, suggest fixes.

**Workflow**:
```
Developer pushes → CI runs → CI monitor polls status → On failure:
  1. Parse failure details (which tests, what errors)
  2. Create tech-debt entry in KB
  3. Suggest fix based on error pattern
  4. Notify developer via status command
```

#### Feature 6.3: Team Roles & Permissions

**Solution**: Role definitions in `.hody/team.yaml`; agent access control based on roles.

```yaml
roles:
  lead:
    can_skip_agents: true
    can_modify_contracts: true
    agents: all
  developer:
    can_skip_agents: false
    agents: [researcher, architect, frontend, backend, unit-tester]
    requires_review: true
  reviewer:
    agents: [code-reviewer, spec-verifier, integration-tester]
    can_approve_merge: true
  junior:
    agents: [frontend, backend, unit-tester]
    requires_review: true
    requires_architect_approval: true
members:
  - github: "hodynguyen"
    role: lead
```

#### Feature 6.4: Project Health Dashboard

**Solution**: `/hody-workflow:health` command aggregating metrics from KB, state, profile, and git history.

```
Project Health — my-app
━━━━━━━━━━━━━━━━━━━━━━

Knowledge Base:  ████████░░ 80% complete (5/6 files populated)
Tech Debt:       3 open items (1 high, 2 medium) — oldest: 14 days
Test Coverage:   78% → 82% (↑4% this week)
Dependencies:    2 outdated, 0 vulnerabilities
Agent Usage:     code-reviewer (12x), backend (8x), unit-tester (7x)
                 ⚠ spec-verifier never used
Workflows:       5 started, 4 completed (80% completion rate)
                 Average: 3.2 agents per workflow

Recommendations:
  → Address high-priority tech debt item: "Migrate from express 4 to 5"
  → Try spec-verifier agent to validate implementation against requirements
  → Consider running deep stack analysis: /hody-workflow:refresh --deep
```

**Deliverable**: Production-ready plugin with configurable quality gates, CI feedback loops, team role management, and project health visibility

---

## Implementation Priority Matrix

| Priority | Feature | Phase | Effort | Impact | Dependencies |
|----------|---------|-------|--------|--------|-------------|
| **P0** | Workflow State Machine | 5.1 | Medium | High | None — foundational for all other features |
| **P0** | Structured KB | 5.2 | Medium | High | None — backward compatible |
| **P1** | Agent Contracts | 5.4 | Medium | Medium-High | Benefits from 5.1 (state tracking) |
| **P1** | Quality Gate v2 | 6.1 | Low-Medium | Medium | None |
| **P2** | Deep Stack Analysis | 5.3 | Medium | Medium | None — opt-in |
| **P2** | CI Feedback Loop | 6.2 | Medium | Medium | Benefits from 5.2 (KB structure for tech-debt) |
| **P3** | Team Roles | 6.3 | Medium | Medium | Requires 5.1 (state machine for enforcement) |
| **P3** | Health Dashboard | 6.4 | Low | Medium | Benefits from 5.1 + 5.2 (data sources) |

**Recommended implementation order**: 5.1 → 5.2 → 5.4 → 6.1 → 5.3 → 6.2 → 6.3 → 6.4
