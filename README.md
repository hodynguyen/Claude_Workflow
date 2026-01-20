# Hody Workflow

> A project-aware development workflow plugin for Claude Code with 9 specialized AI agents.

Full design spec: [HODY_WORKFLOW_PROPOSAL.md](./HODY_WORKFLOW_PROPOSAL.md)

---

## Development Progress

### Phase 1: Foundation (MVP)

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Repo setup + .gitignore | Done | |
| 2 | Marketplace config (`.claude-plugin/marketplace.json`) | Done | Marketplace name: `hody` |
| 3 | Plugin structure + `plugin.json` v0.1.0 | Done | |
| 4 | SessionStart hook (`inject_project_context.py`) | Done | Reads `.hody/profile.yaml`, injects into system message |
| 5 | `detect_stack.py` (project-profile skill) | **TODO** | Auto-detect tech stack from project files |
| 6 | Knowledge base templates (6 files) | **TODO** | architecture, decisions, api-contracts, business-rules, tech-debt, runbook |
| 7 | `SKILL.md` for project-profile | **TODO** | Skill documentation for Claude Code |
| 8 | `/hody:init` command | **TODO** | Runs detect_stack + creates `.hody/` directory |
| 9 | 3 MVP agents: architect, code-reviewer, unit-tester | **TODO** | First 3 of 9 agents |
| 10 | Basic tests for `detect_stack.py` | **TODO** | pytest with mock project structures |

### Phase 2-4

See [Development Roadmap](./HODY_WORKFLOW_PROPOSAL.md#10-development-roadmap) in the proposal.

---

## Can I Use It Now?

**Not yet.** The plugin skeleton is in place but the core features are not implemented:

- No `detect_stack.py` → cannot auto-detect your project stack
- No `/hody:init` command → cannot initialize `.hody/` directory
- No agents → no specialized AI workflows
- The SessionStart hook works but does nothing useful until `.hody/profile.yaml` exists

**What works now:** You can install the plugin and verify that Claude Code recognizes it. The hook will silently skip if no profile is found.

---

## Installation (for testing)

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

### 4. Verify installation

Start a new Claude Code session. If the plugin loaded correctly, you should see it listed when you check installed plugins.

---

## Usage (once MVP is complete)

### Initialize in any project

```bash
cd ~/projects/my-app
claude

# Inside Claude Code:
/hody:init
```

This will:
1. Run `detect_stack.py` to scan your project files (package.json, go.mod, requirements.txt, etc.)
2. Generate `.hody/profile.yaml` with detected stack info
3. Create `.hody/knowledge/` with template files

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

---

## Project Structure

```
claude-workflow/
├── .claude-plugin/
│   └── marketplace.json            # Marketplace: name "hody"
├── plugins/
│   └── hody-workflow/
│       ├── .claude-plugin/
│       │   └── plugin.json         # Plugin metadata (v0.1.0)
│       ├── agents/                 # 9 specialized agents (TODO)
│       ├── skills/
│       │   ├── project-profile/    # Auto-detect tech stack (TODO)
│       │   └── knowledge-base/     # KB templates (TODO)
│       ├── hooks/
│       │   ├── hooks.json          # SessionStart hook config
│       │   └── inject_project_context.py
│       └── commands/               # /hody:init, etc. (TODO)
├── test/                           # Tests (TODO)
├── CLAUDE.md                       # Instructions for Claude Code
└── HODY_WORKFLOW_PROPOSAL.md       # Full design spec (Vietnamese)
```

---

## License

MIT
