# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **Hody Workflow** plugin for Claude Code — a project-aware development workflow system with 9 specialized AI agents. All 4 phases are complete (MVP, Full Agent Suite, Intelligence, Ecosystem). The full specification is in `HODY_WORKFLOW_PROPOSAL.md`.

The plugin provides:
- Auto-detection of project tech stacks (generates `.hody/profile.yaml`)
- A shared knowledge base (`.hody/knowledge/`) that is auto-populated on init and accumulates across sessions
- 9 specialized agents across 4 groups: THINK (researcher, architect), BUILD (frontend, backend), VERIFY (code-reviewer, spec-verifier, unit-tester, integration-tester), SHIP (devops)
- 9 commands: `/hody-workflow:init`, `/hody-workflow:start-feature`, `/hody-workflow:status`, `/hody-workflow:refresh`, `/hody-workflow:kb-search`, `/hody-workflow:connect`, `/hody-workflow:ci-report`, `/hody-workflow:sync`, `/hody-workflow:update-kb`
- 4 output styles: review-report, test-report, design-doc, ci-report

## Architecture

### Three-Layer Design

1. **Project Profile** (foundation) — `detect_stack.py` scans config files (package.json, go.mod, requirements.txt, Cargo.toml, pom.xml, etc.) and outputs `.hody/profile.yaml` with detected language, framework, testing, CI/CD, and infra details
2. **Knowledge Base** (accumulative) — Markdown files in `.hody/knowledge/` (architecture, decisions/ADRs, api-contracts, business-rules, tech-debt, runbook). Auto-populated during init, then agents both read and write to accumulate context
3. **Specialized Agents** — 9 agents with static Markdown prompts that adapt behavior by reading the profile at runtime

### Data Flow
```
User request → [SessionStart hook] injects profile → Agent loads profile.yaml + knowledge base → Agent performs work → Agent writes new knowledge → Output
```

### Plugin Structure
```
plugins/hody-workflow/
├── .claude-plugin/plugin.json     # Plugin metadata
├── agents/                        # 9 agent prompt files (.md)
├── output-styles/                 # 4 output templates (review-report, test-report, design-doc, ci-report)
├── skills/
│   ├── project-profile/
│   │   ├── scripts/
│   │   │   ├── detect_stack.py    # Thin CLI wrapper (backward-compatible)
│   │   │   └── detectors/         # Modular detection package (16 modules)
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
│   │   │       └── serializer.py  # YAML output + CLI entry point
│   │   └── SKILL.md
│   └── knowledge-base/templates/  # 6 KB template files
├── hooks/
│   ├── hooks.json                 # SessionStart hook registration
│   ├── inject_project_context.py  # Reads profile, injects into system message
│   └── quality_gate.py            # Pre-commit quality gate
└── commands/                      # 9 commands: init, start-feature, status, refresh, kb-search, connect, ci-report, sync, update-kb
```

## Development Stack

- **Agent prompts, skills, commands**: Markdown
- **Scripts** (detect_stack, hooks): Python 3 (stdlib preferred, PyYAML is the only external dependency)
- **Config**: JSON (hooks.json, plugin.json, marketplace.json), YAML (profile output)
- **No build step** — plugins are distributed as-is

## Testing

```bash
# Run all tests (88 tests across 13 test files)
python3 -m unittest discover -s test -v

# Tests cover: per-language detectors, monorepo, devops, serializer, quality gate, KB sync, auto-refresh
# Uses mock project structures (temp directories) to verify profile.yaml output correctness
```

## Key Constraints

- Agent prompts are static Markdown — no dynamic templating; agents read `profile.yaml` at runtime instead
- Hook scripts must complete within 60s timeout
- No persistent state except filesystem (`.hody/` directory)
- Plugins only load at Claude Code startup — changes require restart
- `detect_stack.py` should only scan config files, not the full codebase (for speed)

## Development Roadmap

- **Phase 1 (MVP)**: Complete — detect_stack for top 5 stacks, 3 core agents, knowledge base templates, /hody-workflow:init
- **Phase 2 (Full Agent Suite)**: Complete — 9 agents, 3 commands, 3 output styles, extended stack detection (Rust, Java/Kotlin, Angular, Svelte), KB auto-populate on init
- **Phase 3 (Intelligence)**: Complete — C#/Ruby/PHP stack detection, monorepo support (nx/turborepo/lerna/pnpm), auto-update profile (/refresh), KB search (/kb-search), agent collaboration patterns
- **Phase 4 (Ecosystem)**: Complete — MCP integration with GitHub/Linear/Jira (`/hody-workflow:connect`), pre-commit quality gate (`quality_gate.py`), CI test report (`/hody-workflow:ci-report`), team KB sync (`/hody-workflow:sync`), agent MCP tool access, auto-profile refresh hook, KB update (`/hody-workflow:update-kb`). Refactored `detect_stack.py` into modular `detectors/` package (16 modules, SRP). 88 tests total.

## Language Note

Most docs and code are in English. The `USAGE_GUIDE.md` and `PROGRESS.md` are in Vietnamese (internal/personal docs). Code, configs, and agent prompts should be written in English.
