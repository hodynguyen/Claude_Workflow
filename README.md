# Hody Workflow

> A project-aware development workflow plugin for Claude Code with specialized AI agents.

Full design spec: [HODY_WORKFLOW_PROPOSAL.md](./HODY_WORKFLOW_PROPOSAL.md)

---

## Features

- **Auto stack detection** — scans `package.json`, `go.mod`, `requirements.txt`, `Dockerfile`, CI configs, etc.
- **Knowledge base** — 6 persistent markdown files (architecture, decisions, api-contracts, business-rules, tech-debt, runbook) that accumulate project context across sessions
- **Specialized agents** — architect, code-reviewer, unit-tester (3 more groups coming in Phase 2)
- **SessionStart hook** — automatically injects your project's tech stack into every Claude Code session

---

## Installation

### 1. Add marketplace

```
/plugin marketplace add hodynguyen/claude-workflow
```

### 2. Install plugin

```
/plugin install hody-workflow@hody
```

### 3. Restart Claude Code

Plugins load at startup — restart is required after install.

---

## Usage

### Initialize in any project

```bash
cd ~/projects/my-app
claude

# Inside Claude Code:
/hody:init
```

This will:
1. Run `detect_stack.py` to scan your project files
2. Generate `.hody/profile.yaml` with detected stack info
3. Create `.hody/knowledge/` with 6 template files
4. Display a summary of detected technologies

### Generated structure

```
my-app/
└── .hody/
    ├── profile.yaml              # Tech stack (auto-generated)
    └── knowledge/
        ├── architecture.md       # System design
        ├── decisions.md          # ADRs (Architecture Decision Records)
        ├── api-contracts.md      # API specs between FE/BE
        ├── business-rules.md     # Business logic
        ├── tech-debt.md          # Known issues, TODOs
        └── runbook.md            # Deploy, debug, operate
```

> **Tip:** Commit `.hody/` to git — it's team knowledge, not temp files.

### Call agents

```
# Code review
"Use agent code-reviewer to review the auth module"

# Architecture design
"Use agent architect to design the payment system"

# Unit tests
"Use agent unit-tester to write tests for src/utils/validator.ts"
```

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
| Node.js + React/Vue/Next/Nuxt | `package.json` dependencies |
| Go + Gin/Echo/Fiber | `go.mod` |
| Python + Django/FastAPI/Flask | `requirements.txt`, `pyproject.toml` |
| Docker | `Dockerfile`, `docker-compose.yml` |
| CI/CD | `.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile` |
| Infrastructure | `*.tf` (Terraform), `pulumi/` |

More stacks (Rust, Java, C#, Ruby, PHP) coming in Phase 3.

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
| 8 | `/hody:init` command | Done |
| 9 | 3 MVP agents (architect, code-reviewer, unit-tester) | Done |
| 10 | Unit tests (20 tests) | Done |

### Phase 2: Full Agent Suite — Not started

- 6 remaining agents (researcher, frontend, backend, spec-verifier, integration-tester, devops)
- `/hody:start-feature` and `/hody:status` commands
- Output styles (review-report, test-report, design-doc)

### Phase 3-4

See [Development Roadmap](./HODY_WORKFLOW_PROPOSAL.md#10-development-roadmap) in the proposal.

---

## Project Structure

```
claude-workflow/
├── .claude-plugin/
│   └── marketplace.json              # Marketplace: name "hody"
├── plugins/
│   └── hody-workflow/
│       ├── .claude-plugin/
│       │   └── plugin.json           # Plugin metadata
│       ├── agents/
│       │   ├── architect.md          # System design agent
│       │   ├── code-reviewer.md      # Code review agent
│       │   └── unit-tester.md        # Unit testing agent
│       ├── skills/
│       │   ├── project-profile/
│       │   │   ├── SKILL.md
│       │   │   └── scripts/detect_stack.py
│       │   └── knowledge-base/
│       │       └── templates/        # 6 KB template files
│       ├── hooks/
│       │   ├── hooks.json            # SessionStart hook config
│       │   └── inject_project_context.py
│       └── commands/
│           └── init.md               # /hody:init command
├── test/
│   └── test_detect_stack.py          # 20 unit tests
├── CLAUDE.md                         # Instructions for Claude Code
└── HODY_WORKFLOW_PROPOSAL.md         # Full design spec (Vietnamese)
```

---

## License

MIT
