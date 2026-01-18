# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **Hody Workflow** plugin for Claude Code — a project-aware development workflow system with 9 specialized AI agents. The project is currently in the **design/proposal phase** with the full specification in `HODY_WORKFLOW_PROPOSAL.md`.

The plugin provides:
- Auto-detection of project tech stacks (generates `.hody/profile.yaml`)
- A shared knowledge base (`.hody/knowledge/`) that persists across sessions
- 9 specialized agents across 4 groups: THINK (researcher, architect), BUILD (frontend, backend), VERIFY (code-reviewer, spec-verifier, unit-tester, integration-tester), SHIP (devops)

## Architecture

### Three-Layer Design

1. **Project Profile** (foundation) — `detect_stack.py` scans config files (package.json, go.mod, requirements.txt, etc.) and outputs `.hody/profile.yaml` with detected language, framework, testing, CI/CD, and infra details
2. **Knowledge Base** (accumulative) — Markdown files in `.hody/knowledge/` (architecture, decisions/ADRs, api-contracts, business-rules, tech-debt, runbook) that agents both read and write
3. **Specialized Agents** — 9 agents with static Markdown prompts that adapt behavior by reading the profile at runtime

### Data Flow
```
User request → [SessionStart hook] injects profile → Agent loads profile.yaml + knowledge base → Agent performs work → Agent writes new knowledge → Output
```

### Plugin Structure (target)
```
plugins/hody-workflow/
├── .claude-plugin/plugin.json     # Plugin metadata
├── agents/                        # 9 agent prompt files (.md)
├── skills/
│   ├── project-profile/scripts/detect_stack.py
│   └── knowledge-base/templates/  # 6 KB template files
├── hooks/
│   ├── hooks.json                 # SessionStart hook registration
│   └── inject_project_context.py  # Reads profile, injects into system message
└── commands/                      # /hody:init, /hody:start-feature, /hody:status
```

## Development Stack

- **Agent prompts, skills, commands**: Markdown
- **Scripts** (detect_stack, hooks): Python 3 (stdlib preferred, PyYAML is the only external dependency)
- **Config**: JSON (hooks.json, plugin.json, marketplace.json), YAML (profile output)
- **No build step** — plugins are distributed as-is

## Testing

```bash
# Unit tests for detect_stack.py
python3 -m pytest test/test_detect_stack.py

# Tests use mock project structures (temp directories simulating React, Go, Python projects)
# to verify profile.yaml output correctness
```

## Key Constraints

- Agent prompts are static Markdown — no dynamic templating; agents read `profile.yaml` at runtime instead
- Hook scripts must complete within 60s timeout
- No persistent state except filesystem (`.hody/` directory)
- Plugins only load at Claude Code startup — changes require restart
- `detect_stack.py` should only scan config files, not the full codebase (for speed)

## Development Roadmap

- **Phase 1 (MVP)**: Repo setup, detect_stack for top 5 stacks, 3 core agents (architect, code-reviewer, unit-tester), knowledge base templates, /hody:init command
- **Phase 2**: Remaining 6 agents, /hody:start-feature and /hody:status commands, output styles
- **Phase 3**: Broader stack detection, monorepo support, knowledge base search
- **Phase 4**: MCP integration (GitHub, Linear, Jira), CI integration, team KB sync

## Language Note

The proposal document (`HODY_WORKFLOW_PROPOSAL.md`) is written in Vietnamese. Code, configs, and agent prompts should be written in English.
