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
│   ├── commands/                       → 9 slash commands
│   │   ├── init.md, start-feature.md, status.md, refresh.md, kb-search.md
│   │   ├── connect.md, ci-report.md, sync.md, update-kb.md
│   ├── output-styles/                  → 4 output templates
│   │   ├── review-report.md, test-report.md, design-doc.md, ci-report.md
│   ├── skills/
│   │   ├── project-profile/
│   │   │   ├── SKILL.md
│   │   │   └── scripts/
│   │   │       ├── detect_stack.py     → Thin CLI wrapper (backward-compatible)
│   │   │       └── detectors/          → Modular detection package (18 modules)
│   │   │           ├── __init__.py, utils.py, profile.py, serializer.py
│   │   │           ├── node.py, go.py, python_lang.py, rust.py
│   │   │           ├── java.py, csharp.py, ruby.py, php.py
│   │   │           ├── devops.py, monorepo.py, database.py
│   │   │           ├── conventions.py, integrations.py, directories.py
│   │   └── knowledge-base/
│   │       ├── scripts/kb_sync.py      → Team KB sync script
│   │       └── templates/              → 6 KB template files
│   └── hooks/
│       ├── hooks.json                  → SessionStart hook config
│       ├── inject_project_context.py   → Injects profile into system message
│       └── quality_gate.py             → Pre-commit quality gate
└── test/                               → 110 unit tests across 17 test files
    ├── test_detect_stack.py            → Core detection tests
    ├── test_node_detector.py, test_go_detector.py, test_python_detector.py
    ├── test_rust_detector.py, test_java_detector.py, test_csharp_detector.py
    ├── test_ruby_detector.py, test_php_detector.py
    ├── test_monorepo.py, test_devops.py, test_conventions.py
    ├── test_directories.py, test_serializer.py
    ├── test_quality_gate.py, test_kb_sync.py, test_auto_refresh.py
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
