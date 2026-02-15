# Hody Workflow - Development Proposal

> A project-aware, abstract development workflow plugin for Claude Code with 9 specialized AI agents.

For technical architecture details, see [ARCHITECTURE.md](./ARCHITECTURE.md).
For development roadmap, see [ROADMAP.md](./ROADMAP.md).
For usage instructions, see [USER_GUIDE.md](./USER_GUIDE.md).

---

## Table of Contents

- [1. Vision & Goals](#1-vision--goals)
- [2. Development Stack](#2-development-stack)
- [3. Workflow Usage In Practice](#3-workflow-usage-in-practice)
- [4. Distribution & Installation](#4-distribution--installation)
- [5. Step-by-step Build Guide](#5-step-by-step-build-guide)
- [6. Constraints & Risks](#6-constraints--risks)

---

## 1. Vision & Goals

### Problem

When working with Claude Code on real-world projects:

- Claude Code is a general-purpose AI with no specialized development workflow
- No domain-specific agents (FE, BE, testing, review...)
- Each new session, Claude must rediscover the project from scratch
- No process to ensure code quality before committing
- Knowledge is lost between sessions

### Solution

**Hody Workflow** is a Claude Code plugin that provides:

- **9 specialized agents** for each phase of development
- **Auto-detect project stack** — zero config when switching projects
- **Shared knowledge base** — knowledge accumulates and persists across sessions
- **Task-to-agents mapping** — automatically suggests the right agent for each task type
- **Abstract design** — one plugin works for any project, any tech stack

### Design Principles

1. **Project-aware, not project-specific**: Agent prompts are generic; behavior is specific thanks to the profile
2. **Composable, not rigid**: Users can call any agent directly; the workflow is just a recommended flow
3. **Accumulative knowledge**: Every agent reads AND writes to the knowledge base
4. **Zero config**: Auto-detect stack, no manual configuration required
5. **Works offline**: No external API dependency; MCP server is optional

---

## 2. Development Stack

### Languages & Tools

| Component | Language | Reason |
|-----------|----------|--------|
| Agent prompts | Markdown | Claude Code plugin format, no compilation needed |
| Skill docs | Markdown (YAML frontmatter) | Claude Code plugin format |
| `detect_stack.py` | Python 3 | Parse YAML/JSON/TOML, filesystem operations |
| `inject_project_context.py` | Python 3 | Read YAML, output JSON for Claude Code hook |
| Commands | Markdown | Claude Code plugin format |
| Hook config | JSON (`hooks.json`) | Claude Code plugin format |
| Project profile | YAML | Human-readable, easy to edit manually |
| Knowledge base | Markdown | Human-readable, versionable, Claude-friendly |

### Dependencies

```
Python 3.8+      ← already available on macOS/Linux
PyYAML            ← parse profile.yaml (or use built-in to avoid deps)
toml              ← parse Cargo.toml, pyproject.toml (Python 3.11+ has built-in)
```

Minimize external dependencies. Prefer Python stdlib. PyYAML is the only required dependency.

### Testing

```bash
# Run all 88 tests across 13 test files
python3 -m unittest discover -s test -v

# Tests cover:
# - Per-language detectors (node, go, python, rust, java, csharp, ruby, php)
# - Monorepo detection, DevOps, database, serializer
# - Auto-refresh logic, integrations preservation
# - Quality gate (security checks, file size, skip rules)
# - KB sync (validate, sync status)
# - Backward-compatible imports from detect_stack.py

# All tests use mock project structures (temp directories)
# to verify profile.yaml output correctness
```

---

## 3. Workflow Usage In Practice

### 3.1. First Time Setup

```bash
# User opens project and starts Claude Code
cd ~/projects/my-saas-app
claude

# Initialize hody workflow
User: /hody-workflow:init

# Claude Code runs:
# 1. detect_stack.py scans project
# 2. Creates .hody/profile.yaml
# 3. Creates .hody/knowledge/ with templates
# 4. Output: "Detected: React 18 + TypeScript + Fastify + PostgreSQL + GitHub Actions"

# From now on, every session auto-injects project context
```

### 3.2. Feature Development (full workflow)

```bash
User: "I need to implement user authentication with Google OAuth"

# Claude Code identifies: new feature → suggests full workflow

# ─── PHASE 1: THINK ───
# researcher agent activates
Claude (researcher): "Let me research Google OAuth best practices for React + Fastify stack..."
  → Investigates @react-oauth/google, passport-google-oauth20
  → Writes findings to .hody/knowledge/decisions.md

# architect agent activates
Claude (architect): "Based on the research, here's the auth flow design..."
  → Creates sequence diagram in .hody/knowledge/architecture.md
  → Defines API contracts in .hody/knowledge/api-contracts.md
  → Writes business rules (session timeout, refresh token) to business-rules.md

# ─── PHASE 2: BUILD ───
# backend agent activates
Claude (backend): "Implementing auth API according to defined contracts..."
  → POST /api/auth/google
  → GET /api/auth/me
  → POST /api/auth/refresh
  → Database migration: users table

# frontend agent activates
Claude (frontend): "Implementing login UI and OAuth flow..."
  → LoginPage component with Google OAuth button
  → AuthContext provider
  → Protected route wrapper

# ─── PHASE 3: VERIFY ───
# unit-tester agent activates
Claude (unit-tester): "Writing unit tests for auth modules..."
  → Test token validation edge cases
  → Test AuthContext behavior
  → Test API handler logic

# integration-tester agent activates
Claude (integration-tester): "Writing integration tests for auth flow..."
  → Test: Google OAuth → callback → token → profile
  → Test: expired token → refresh → new token
  → Test: invalid token → 401

# code-reviewer agent activates
Claude (code-reviewer): "Reviewing the entire auth implementation..."
  → Security: token storage, CSRF, XSS
  → Code quality: error handling, naming
  → Performance: database queries

# spec-verifier agent activates
Claude (spec-verifier): "Verifying implementation matches specs..."
  → Check API contracts match actual endpoints
  → Check business rules implemented correctly
  → Check edge cases covered

# ─── PHASE 4: SHIP ───
# devops agent activates (if needed)
Claude (devops): "Updating CI pipeline for auth..."
  → Add env vars for Google OAuth credentials
  → Update deployment config
```

### 3.3. Quick Tasks (no full workflow needed)

```bash
# Bug fix — only 2-3 agents needed
User: "Fix bug: login button doesn't redirect correctly after authentication"
  → architect (understand context from KB)
  → frontend (fix code)
  → unit-tester (verify fix)

# Code review — only 1 agent needed
User: "Review file server/auth/handler.ts"
  → code-reviewer

# Research — only 1 agent needed
User: "Research how to implement rate limiting for the API"
  → researcher
```

### 3.4. Calling agents directly

```bash
# Users can call any agent directly
User: "Use agent backend to implement a DELETE /api/users/:id endpoint"
User: "Use agent code-reviewer to review this PR"
User: "Use agent devops to setup monitoring"
```

---

## 4. Distribution & Installation

### 4.1. GitHub Repository

- **Repo name**: `Claude_Workflow`
- **URL**: `github.com/hodynguyen/Claude_Workflow`
- **Visibility**: Public (so other users can install)

### 4.2. Marketplace Registration

File `.claude-plugin/marketplace.json` at repo root:

```json
{
  "name": "hody",
  "owner": {
    "name": "Hody",
    "email": "your-email@example.com"
  },
  "plugins": [
    {
      "name": "hody-workflow",
      "source": "./plugins/hody-workflow"
    }
  ]
}
```

- `name: "hody"` — this is the marketplace name; users will reference it with `@hody`
- To add more plugins later (e.g., `hody-voice`, `hody-mcp`), just add entries to the `plugins` array

### 4.3. User Installation

```bash
# Step 1: Add marketplace
/plugin marketplace add hodynguyen/Claude_Workflow

# Step 2: Install plugin
/plugin install hody-workflow@hody

# Step 3: Restart Claude Code
# (plugins load at startup)

# Step 4: Init hody workflow in any project
cd ~/projects/my-app
claude
/hody-workflow:init
```

### 4.4. Update Plugin

When you push new code to GitHub:

```bash
# User updates plugin
/plugin marketplace update
/plugin update hody-workflow@hody
# Restart Claude Code
```

### 4.5. What to commit in the target project

When a user runs `/hody-workflow:init` in their project, it creates the `.hody/` directory:

```
.hody/
├── profile.yaml              ← SHOULD commit (team shares the profile)
└── knowledge/
    ├── architecture.md       ← SHOULD commit (shared knowledge)
    ├── decisions.md          ← SHOULD commit
    ├── api-contracts.md      ← SHOULD commit
    ├── business-rules.md     ← SHOULD commit
    ├── tech-debt.md          ← SHOULD commit
    └── runbook.md            ← SHOULD commit
```

Knowledge base SHOULD be committed — it's a team asset, not temp files.

---

## 5. Step-by-step Build Guide

Specific steps to build the hody-workflow plugin from scratch.

### Step 1: Create GitHub repo

```bash
mkdir hody-workflow
cd hody-workflow
git init

# Create .gitignore
cat > .gitignore << 'EOF'
__pycache__/
*.pyc
.pytest_cache/
.DS_Store
*.egg-info/
dist/
build/
EOF

# First commit
git add .gitignore
git commit -m "init: create repo"

# Create repo on GitHub and push
gh repo create hody-workflow --public --source=. --push
```

### Step 2: Create marketplace config

```bash
mkdir -p .claude-plugin
```

Create `.claude-plugin/marketplace.json`:
```json
{
  "name": "hody",
  "owner": {
    "name": "Hody",
    "email": "your-email@example.com"
  },
  "plugins": [
    {
      "name": "hody-workflow",
      "source": "./plugins/hody-workflow"
    }
  ]
}
```

### Step 3: Create plugin structure

```bash
# Plugin root
mkdir -p plugins/hody-workflow/.claude-plugin
mkdir -p plugins/hody-workflow/agents
mkdir -p plugins/hody-workflow/skills/project-profile/scripts
mkdir -p plugins/hody-workflow/skills/knowledge-base/templates
mkdir -p plugins/hody-workflow/hooks
mkdir -p plugins/hody-workflow/commands
mkdir -p plugins/hody-workflow/output-styles

# Test directory
mkdir -p test
```

Create `plugins/hody-workflow/.claude-plugin/plugin.json`:
```json
{
  "name": "hody-workflow",
  "description": "Project-aware development workflow with 9 specialized AI agents",
  "version": "0.1.0",
  "author": {
    "name": "Hody",
    "email": "your-email@example.com"
  },
  "license": "MIT",
  "keywords": [
    "workflow",
    "agents",
    "development",
    "code-review",
    "testing",
    "devops"
  ]
}
```

### Step 4: Write hooks.json

Create `plugins/hody-workflow/hooks/hooks.json`:
```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/inject_project_context.py",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

### Step 5: Write inject_project_context.py

Create `plugins/hody-workflow/hooks/inject_project_context.py`:
```python
#!/usr/bin/env python3
"""
SessionStart hook: reads .hody/profile.yaml and injects project context
into the system message so every agent knows the current tech stack.
"""
import json
import sys
import os

def main():
    try:
        input_data = json.load(sys.stdin)
        cwd = input_data.get("cwd", os.getcwd())

        profile_path = os.path.join(cwd, ".hody", "profile.yaml")
        if not os.path.isfile(profile_path):
            # No profile → skip
            print("{}")
            sys.exit(0)

        # Read profile (plain text, no PyYAML needed for simple inject)
        with open(profile_path, "r") as f:
            profile_content = f.read()

        # Inject into system message
        summary = f"[Hody Workflow] Project profile loaded from .hody/profile.yaml"
        output = {
            "systemMessage": summary
        }
        print(json.dumps(output))
        sys.exit(0)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(0)  # Don't block session if hook fails

if __name__ == "__main__":
    main()
```

```bash
chmod +x plugins/hody-workflow/hooks/inject_project_context.py
```

### Step 6: Write detect_stack.py

Create `plugins/hody-workflow/skills/project-profile/scripts/detect_stack.py`:
- Scan config files (package.json, go.mod, requirements.txt, pyproject.toml...)
- Output `.hody/profile.yaml`
- Start with top 5 stacks: Node/React, Node/Vue, Go, Python/Django, Python/FastAPI
- Expand gradually

```bash
chmod +x plugins/hody-workflow/skills/project-profile/scripts/detect_stack.py
```

### Step 7: Write SKILL.md for project-profile

Create `plugins/hody-workflow/skills/project-profile/SKILL.md`:
```markdown
---
name: project-profile
description: Use this skill when user asks to "detect project stack",
  "init hody", "setup hody workflow", or when you need to understand
  the current project's technology stack.
---

# Project Profile

Auto-detect project tech stack and create .hody/profile.yaml.

## Usage

Run the detection script:
\`\`\`bash
python3 ${SKILL_ROOT}/scripts/detect_stack.py --cwd .
\`\`\`

## Output
Creates `.hody/profile.yaml` with detected stack info.
```

### Step 8: Write first 3 agents (MVP)

Start with the 3 most important agents:

1. `plugins/hody-workflow/agents/architect.md`
2. `plugins/hody-workflow/agents/code-reviewer.md`
3. `plugins/hody-workflow/agents/unit-tester.md`

Each file follows the agent prompt template (see [ARCHITECTURE.md — Agent Prompt Template](./ARCHITECTURE.md#32-agent-prompt-template)).

### Step 9: Write /hody-workflow:init command

Create `plugins/hody-workflow/commands/init.md`:
```markdown
---
name: init
description: Initialize hody workflow for the current project
---

# /hody-workflow:init

Initialize hody workflow:

1. Run detect_stack.py to create .hody/profile.yaml
2. Create .hody/knowledge/ directory with template files
3. Show detected stack summary
```

### Step 10: Write knowledge base templates

Create files in `plugins/hody-workflow/skills/knowledge-base/templates/`:
- `architecture.md`
- `decisions.md`
- `api-contracts.md`
- `business-rules.md`
- `tech-debt.md`
- `runbook.md`

Each file contains the standard template (see [ARCHITECTURE.md — Knowledge Base Templates](./ARCHITECTURE.md#52-knowledge-base-templates)).

### Step 11: Write README.md

Create `README.md` (repo root) and `plugins/hody-workflow/README.md` (plugin docs):
- Overview
- Installation
- Quick start
- Agent descriptions
- Commands reference

### Step 12: Test locally

```bash
# Install plugin locally for testing
cd ~/projects/some-test-project
claude

# Add marketplace from local path (or from GitHub after pushing)
/plugin marketplace add hodynguyen/Claude_Workflow

# Install plugin
/plugin install hody-workflow@hody

# Restart Claude Code, then test
/hody-workflow:init
```

### Step 13: Push and publish

```bash
cd ~/path/to/hody-workflow
git add .
git commit -m "feat: initial hody-workflow plugin with 3 MVP agents"
git push origin main
```

From now on, anyone can install the plugin with:
```bash
/plugin marketplace add hodynguyen/Claude_Workflow
/plugin install hody-workflow@hody
```

---

## 6. Constraints & Risks

### Claude Code Plugin Constraints

| Constraint | Impact | Mitigation |
|-----------|--------|-----------|
| Agent prompts are static markdown | Cannot template dynamically | Agents read profile.yaml at runtime |
| Hooks timeout max 60s | detect_stack must be fast | Only scan config files, not the entire codebase |
| No persistent state beyond files | Session state lost on restart | Use `.hody/` directory on filesystem |
| Plugins only load at Claude Code startup | Plugin changes require restart | Use session hooks for dynamic behavior |

### Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| Profile detection is incorrect | Medium | Agent gets wrong context | Allow user to manually edit profile.yaml |
| Agent prompts too long | Medium | Uses too much context window | Keep prompts concise, use references |
| Knowledge base files conflict on merge | Low | Git conflicts | Use append-only format, clear sections |
| Claude Code plugin API changes | Low | Plugin breaks | Follow Claude Code changelog, maintain compatibility |

### Out of Scope (v1)

- IDE integration (VS Code extension)
- Real-time collaboration between multiple users
- Custom agent creation UI
- Agent marketplace (users share agents)
- Automatic agent selection (v1 uses manual + suggestion)
