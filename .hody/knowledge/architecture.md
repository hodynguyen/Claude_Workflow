# Architecture

## System Overview

Hody Workflow is a Claude Code plugin that provides project-aware development workflows with 9 specialized AI agents. It auto-detects tech stacks, maintains a persistent knowledge base, and guides developers through THINK → BUILD → VERIFY → SHIP phases.

## Component Diagram

```
claude-workflow/
├── .claude-plugin/marketplace.json     → Marketplace registration (name: "hody")
├── plugins/hody-workflow/
│   ├── .claude-plugin/plugin.json      → Plugin metadata (version, author)
│   ├── agents/                         → 9 agent prompt files (.md)
│   │   ├── THINK: researcher, architect
│   │   ├── BUILD: frontend, backend
│   │   ├── VERIFY: code-reviewer, spec-verifier, unit-tester, integration-tester
│   │   └── SHIP: devops
│   ├── commands/                       → 5 slash commands
│   │   ├── init.md, start-feature.md, status.md, refresh.md, kb-search.md
│   ├── output-styles/                  → 3 output templates
│   │   ├── review-report.md, test-report.md, design-doc.md
│   ├── skills/
│   │   ├── project-profile/            → detect_stack.py + SKILL.md
│   │   └── knowledge-base/templates/   → 6 KB template files
│   └── hooks/
│       ├── hooks.json                  → SessionStart hook config
│       └── inject_project_context.py   → Injects profile into system message
└── test/
    └── test_detect_stack.py            → 47 unit tests
```

## Three-Layer Design

```
Layer 1: PROJECT PROFILE (foundation)
  .hody/profile.yaml — auto-detected tech stack
       ↓
Layer 2: KNOWLEDGE BASE (accumulative)
  .hody/knowledge/*.md — 6 files that grow over time
       ↓
Layer 3: SPECIALIZED AGENTS (9 agents, 4 groups)
  Static Markdown prompts that adapt via profile.yaml at runtime
```

## Data Flow

```
Session starts
  → [SessionStart hook] reads .hody/profile.yaml → injects into system message
  → User request → Claude Code determines task type
  → Loads appropriate agent (agents/*.md)
  → Agent reads profile.yaml + knowledge base
  → Agent performs work
  → Agent writes new knowledge to .hody/knowledge/
  → Output to user
```

## Tech Stack Rationale

- **Markdown**: Claude Code plugin format for agents, commands, skills — no compilation needed
- **Python 3 (stdlib)**: Scripts for stack detection and hook injection — portable, no build step
- **PyYAML**: Only external dependency — needed to parse/write profile.yaml
- **YAML for profile**: Human-readable, easy to edit manually if detection is wrong
- **JSON for config**: Required by Claude Code plugin format (hooks.json, plugin.json)
- **No build step**: Plugins distributed as-is, loaded by Claude Code at startup
