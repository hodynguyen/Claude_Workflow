# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **Hody Workflow** plugin for Claude Code — a project-aware development workflow system with 9 specialized AI agents. Current version: v0.10.0. Full documentation is in `docs/` (PROPOSAL, ARCHITECTURE, ROADMAP, USER_GUIDE).

The plugin provides:
- Auto-detection of project tech stacks (generates `.hody/profile.yaml`)
- A shared knowledge base (`.hody/knowledge/`) that is auto-populated on init and accumulates across sessions
- 9 specialized agents across 4 groups: THINK (researcher, architect), BUILD (frontend, backend), VERIFY (code-reviewer, spec-verifier, unit-tester, integration-tester), SHIP (devops)
- 14 commands: `/hody-workflow:init`, `/hody-workflow:start-feature`, `/hody-workflow:status`, `/hody-workflow:refresh`, `/hody-workflow:kb-search`, `/hody-workflow:connect`, `/hody-workflow:ci-report`, `/hody-workflow:sync`, `/hody-workflow:update-kb`, `/hody-workflow:resume`, `/hody-workflow:health`, `/hody-workflow:track`, `/hody-workflow:history`, `/hody-workflow:rules`
- 4 output styles: review-report, test-report, design-doc, ci-report
- Configurable quality gate with `.hody/quality-rules.yaml`
- Project rules (`.hody/rules.yaml`) — user-authored coding conventions, architecture constraints, testing requirements that all agents follow
- Team roles & permissions via `.hody/team.yaml`
- Workflow state machine (`.hody/state.json`) with spec-driven development and 3 execution modes: `auto` (full auto, no interaction), `guided` (interactive discovery, auto execution), `manual` (pause between agents)
- Interaction tracker (`tracker.py`, `.hody/tracker.db`) with agent checkpoints for surviving context limit interruptions
- Graphify knowledge graph integration — AST-based code graph via MCP server, used by all 9 agents
- Structured KB with YAML frontmatter, `_index.json` indexing, and auto-archival
- `$ARGUMENTS` support in all commands for inline parameters

## Architecture

### Three-Layer Design

1. **Project Profile** (foundation) — `detect_stack.py` scans config files (package.json, go.mod, requirements.txt, Cargo.toml, pom.xml, etc.) and outputs `.hody/profile.yaml` with detected language, framework, testing, CI/CD, and infra details
2. **Knowledge Base** (accumulative) — Markdown files in `.hody/knowledge/` with YAML frontmatter (tags, date, author-agent, status). Auto-populated during init, then agents both read and write to accumulate context. `_index.json` enables tag/agent/status search. Auto-archival moves old sections to `archive/` when files exceed 500 lines
3. **Specialized Agents** — 9 agents with static Markdown prompts that adapt behavior by reading the profile at runtime

### Data Flow
```
User request → [SessionStart hook] injects profile → Agent loads profile.yaml + knowledge base → Agent performs work → Agent writes new knowledge → Output
```

### Plugin Structure
```
plugins/hody-workflow/
├── .claude-plugin/plugin.json     # Plugin metadata
├── agents/                        # 9 agent prompt files (.md) + contracts/
│   └── contracts/                 # 6 handoff contract YAML files
├── output-styles/                 # 4 output templates (review-report, test-report, design-doc, ci-report)
├── skills/
│   ├── project-profile/
│   │   ├── scripts/
│   │   │   ├── detect_stack.py    # Thin CLI wrapper (backward-compatible)
│   │   │   ├── state.py           # Workflow state machine (.hody/state.json)
│   │   │   ├── tracker.py         # SQLite interaction tracker + agent checkpoints
│   │   │   ├── tracker_schema.py  # Tracker DB schema definitions
│   │   │   ├── tracker_awareness.py # Tracker context injection
│   │   │   ├── rules.py           # Project rules engine (.hody/rules.yaml)
│   │   │   ├── kb_index.py        # KB index builder (_index.json)
│   │   │   ├── kb_archive.py      # KB auto-archival (archive/ dir)
│   │   │   ├── contracts.py       # Agent I/O contract validator
│   │   │   ├── quality_rules.py   # Configurable quality rule engine
│   │   │   ├── ci_monitor.py      # CI feedback loop (poll, parse, tech-debt)
│   │   │   ├── team.py            # Team roles & permissions
│   │   │   ├── health.py          # Project health dashboard
│   │   │   ├── graphify_setup.py  # Graphify knowledge graph setup
│   │   │   ├── graphify_diff.py   # Graph structural diff between builds
│   │   │   ├── graphify_kb_populate.py # KB auto-populate from graph data
│   │   │   └── detectors/         # Modular detection package (20 modules)
│   │   │       ├── __init__.py    # Re-exports public API
│   │   │       ├── utils.py       # read_json, read_lines
│   │   │       ├── node.py        # Node.js/TS detection
│   │   │       ├── go.py          # Go detection
│   │   │       ├── python_lang.py # Python detection
│   │   │       ├── rust.py        # Rust detection
│   │   │       ├── java.py        # Java/Kotlin detection
│   │   │       ├── csharp.py      # C#/.NET detection
│   │   │       ├── ruby.py        # Ruby detection
│   │   │       ├── php.py         # PHP detection
│   │   │       ├── devops.py      # CI/CD, Docker, infra
│   │   │       ├── monorepo.py    # Monorepo + workspace profiles
│   │   │       ├── database.py    # Database detection
│   │   │       ├── conventions.py # Linter, formatter, PR template
│   │   │       ├── integrations.py# Preserve integrations across re-detection
│   │   │       ├── profile.py     # Orchestrator — calls all detectors
│   │   │       ├── serializer.py  # YAML output + CLI entry point
│   │   │       ├── deep_analysis.py # Deep dependency analysis (opt-in)
│   │   │       ├── versions.py    # Semver parsing, conflict detection
│   │   │       └── directories.py # Directory structure analysis
│   │   └── SKILL.md
│   └── knowledge-base/templates/  # 6 KB template files
├── hooks/
│   ├── hooks.json                 # SessionStart hook registration
│   ├── inject_project_context.py  # Reads profile + workflow state + rules, injects into system message
│   └── quality_gate.py            # Pre-commit quality gate (v2: configurable rules)
└── commands/                      # 14 commands: init, start-feature, status, refresh, kb-search, connect, ci-report, sync, update-kb, resume, health, track, history, rules
```

## Development Stack

- **Agent prompts, skills, commands**: Markdown
- **Scripts** (detect_stack, hooks): Python 3 (stdlib preferred, PyYAML is the only external dependency)
- **Config**: JSON (hooks.json, plugin.json, marketplace.json), YAML (profile output)
- **No build step** — plugins are distributed as-is

## Testing

```bash
# Run all tests (553 tests across 30 test files)
python3 -m unittest discover -s test -v

# Tests cover: per-language detectors, monorepo, devops, serializer, quality gate, KB sync,
# auto-refresh, workflow state, KB index/archive, deep analysis, contracts, quality rules,
# CI monitor, team roles, health dashboard, tracker, graphify (setup/diff/kb-populate), rules
# Uses mock project structures (temp directories) to verify profile.yaml output correctness
```

## Key Constraints

- Agent prompts are static Markdown — no dynamic templating; agents read `profile.yaml` at runtime instead
- Hook scripts must complete within 60s timeout
- Persistent state via filesystem (`.hody/` directory) and SQLite (`tracker.db`) for interaction tracking
- Plugins only load at Claude Code startup — changes require restart
- `detect_stack.py` should only scan config files, not the full codebase (for speed). Use `--deep` for actual package manager analysis
- Agent contracts are advisory by default — produce warnings, not errors

## Development Roadmap

- **Phase 1 (MVP)**: Complete — detect_stack for top 5 stacks, 3 core agents, knowledge base templates, /hody-workflow:init
- **Phase 2 (Full Agent Suite)**: Complete — 9 agents, 3 commands, 3 output styles, extended stack detection (Rust, Java/Kotlin, Angular, Svelte), KB auto-populate on init
- **Phase 3 (Intelligence)**: Complete — C#/Ruby/PHP stack detection, monorepo support (nx/turborepo/lerna/pnpm), auto-update profile (/refresh), KB search (/kb-search), agent collaboration patterns
- **Phase 4 (Ecosystem)**: Complete — MCP integration with GitHub/Linear/Jira (`/hody-workflow:connect`), pre-commit quality gate (`quality_gate.py`), CI test report (`/hody-workflow:ci-report`), team KB sync (`/hody-workflow:sync`), agent MCP tool access, auto-profile refresh hook, KB update (`/hody-workflow:update-kb`). Refactored `detect_stack.py` into modular `detectors/` package.
- **Phase 5 (Deep Intelligence)**: Complete — Workflow state machine (`state.py`, `/hody-workflow:resume`). Structured KB with frontmatter, `_index.json`, auto-archival. Deep stack analysis (`--deep` flag, `deep_analysis.py`, `versions.py`). Agent I/O contracts (`agents/contracts/`, `contracts.py`).
- **Phase 6 (Enterprise Grade)**: Complete — Configurable quality gate v2 (`quality_rules.py`, `.hody/quality-rules.yaml`). CI feedback loop (`ci_monitor.py`, auto tech-debt entries). Team roles & permissions (`team.py`, `.hody/team.yaml`). Project health dashboard (`health.py`, `/hody-workflow:health`).
- **v0.6.x (Interaction Tracker)**: Complete — SQLite-based tracker (`tracker.py`, `.hody/tracker.db`) for persistent interaction tracking, agent checkpoints that survive context limit interruptions, `/hody-workflow:track` and `/hody-workflow:history` commands, `$ARGUMENTS` support in all 14 commands, per-feature work logs.
- **v0.7.0 (Spec-Driven Workflow)**: Complete — Discovery → Confirm → Auto-execute paradigm. Agents produce specs first, user confirms, then remaining agents auto-execute against confirmed spec.
- **v0.8.x (Graphify Integration)**: Complete — AST-based knowledge graph via tree-sitter (`graphify_setup.py`). MCP server with 7 graph query tools. All 9 agents graph-aware. Graph diff tracking between builds (`graphify_diff.py`). KB auto-populate from graph data (`graphify_kb_populate.py`). Graph metadata in KB index.
- **v0.9.0 (Project Rules)**: Complete — User-authored project rules (`.hody/rules.yaml`) with coding conventions, architecture constraints, testing requirements, workflow preferences. All 9 agents read rules at bootstrap. `/hody-workflow:rules` command. Hook injection of rules summary.
- **v0.10.0 (Execution Modes)**: Complete — Three workflow execution modes: `auto` (skip discovery, auto-confirm spec, run all agents), `guided` (interactive discovery, auto execution), `manual` (pause between agents). Mode persisted in state.json, respected by resume. 553 tests total.
