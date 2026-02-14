# Hody Workflow - Development Proposal

> A project-aware, abstract development workflow plugin for Claude Code with 9 specialized AI agents.

---

## Table of Contents

- [1. Vision & Goals](#1-vision--goals)
- [2. Architecture Overview](#2-architecture-overview)
- [3. Agent Design](#3-agent-design)
- [4. Plugin Structure](#4-plugin-structure)
- [5. Core Components Detail](#5-core-components-detail)
- [6. Development Stack](#6-development-stack)
- [7. Workflow Usage In Practice](#7-workflow-usage-in-practice)
- [8. Distribution & Installation](#8-distribution--installation)
- [9. Step-by-step Build Guide](#9-step-by-step-build-guide)
- [10. Development Roadmap](#10-development-roadmap)
- [11. Constraints & Risks](#11-constraints--risks)

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

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     HODY WORKFLOW PLUGIN                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  LAYER 1: PROJECT PROFILE (foundation)                          │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ .hody/profile.yaml                                         │ │
│  │ Auto-detect: language, framework, testing, CI/CD, infra    │ │
│  │ Runs once via /hody-workflow:init, shared across all agents         │ │
│  └────────────────────────────────────────────────────────────┘ │
│                             ↓ feeds into                         │
│  LAYER 2: KNOWLEDGE BASE (accumulative)                         │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ .hody/knowledge/                                           │ │
│  │ ├── architecture.md     (system design, diagrams)          │ │
│  │ ├── decisions.md        (ADRs - why we chose X over Y)    │ │
│  │ ├── api-contracts.md    (API specs between FE/BE)          │ │
│  │ ├── business-rules.md   (business logic, constraints)      │ │
│  │ ├── tech-debt.md        (known issues, TODOs)              │ │
│  │ └── runbook.md          (deploy, debug, operate)           │ │
│  └────────────────────────────────────────────────────────────┘ │
│                             ↓ feeds into                         │
│  LAYER 3: SPECIALIZED AGENTS (9 agents, 4 groups)              │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ ┌───────────┐ │
│  │  THINK   │ │  BUILD   │ │     VERIFY       │ │   SHIP    │ │
│  │researcher│ │ frontend │ │ code-reviewer     │ │  devops   │ │
│  │architect │ │ backend  │ │ spec-verifier     │ │           │ │
│  │          │ │          │ │ unit-tester       │ │           │ │
│  │          │ │          │ │ integration-tester│ │           │ │
│  └──────────┘ └──────────┘ └──────────────────┘ └───────────┘ │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  SUPPORTING COMPONENTS                                           │
│  ├── Skills: project-profile (auto-detect), knowledge-base       │
│  ├── Hooks: inject_project_context (SessionStart)                │
│  ├── Commands: /hody-workflow:init, start-feature, status,      │
│  │             refresh, kb-search                               │
│  └── Output Styles: review-report, test-report, design-doc      │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
User request
     ↓
[Hook: SessionStart] → inject project profile into system message
     ↓
Claude Code receives request → determines task type
     ↓
Loads appropriate agent (from agents/*.md)
     ↓
Agent reads:
  1. .hody/profile.yaml (current stack)
  2. .hody/knowledge/* (accumulated context)
     ↓
Agent performs work
     ↓
Agent writes new knowledge (if any) to .hody/knowledge/
     ↓
Output to user
```

---

## 3. Agent Design

### 3.1. Agent Summary

| # | Agent | Group | Expertise | Input | Output | Scope |
|---|-------|-------|-----------|-------|--------|-------|
| 1 | researcher | THINK | External tech docs, best practices | Profile + question | Tech summary → knowledge base | READ only |
| 2 | architect | THINK | System design, BA, flows, contracts | Requirements + KB | Architecture docs, ADRs, API contracts | READ + WRITE KB |
| 3 | frontend | BUILD | UI/UX following project's FE stack | FE profile + design docs | FE code | WRITE FE code |
| 4 | backend | BUILD | API, business logic, DB | BE profile + design docs | BE code | WRITE BE code |
| 5 | code-reviewer | VERIFY | Code quality, patterns, security, perf | Code changes | Review report | READ only |
| 6 | spec-verifier | VERIFY | Logic matches specs/business rules | Code + specs from KB | Verification report | READ only |
| 7 | unit-tester | VERIFY | Unit tests, mocking, edge cases | Code + profile testing | Unit tests | WRITE tests |
| 8 | integration-tester | VERIFY | API tests, E2E, business flows | Code + API contracts + KB | Integration/E2E tests | WRITE tests |
| 9 | devops | SHIP | CI/CD, deployment, infra | DevOps profile + arch docs | Pipeline configs, IaC | WRITE configs |

### 3.2. Agent Prompt Template

Each agent `.md` follows this structure:

```markdown
---
name: agent-name
description: When this agent should be activated (for Claude Code matching)
---

# Agent: [Role Name]

## Bootstrap (must run first)
1. Read `.hody/profile.yaml` → determine tech stack
2. Read `.hody/knowledge/[relevant-files]` → understand project context
3. Confirm work scope with user if needed

## Core Expertise
- [Domain-specific knowledge]
- Adapt behavior based on profile:
  - If profile.frontend.framework = "react" → apply React patterns
  - If profile.frontend.framework = "vue" → apply Vue patterns

## Responsibilities
- [What this agent specifically does]

## Constraints
- [What this agent specifically does NOT do]

## Output Format
- [Standard output format]

## Knowledge Base Update
- After completion, write new knowledge to `.hody/knowledge/[file]`
```

### 3.3. Task-to-Agents Mapping

```
┌─────────────────────┬───────────────────────────────────────────────────────┐
│ Task Type           │ Agents (in order)                                     │
├─────────────────────┼───────────────────────────────────────────────────────┤
│ New feature         │ researcher → architect → FE + BE (parallel)          │
│                     │ → unit-tester + integration-tester                    │
│                     │ → code-reviewer + spec-verifier → devops              │
├─────────────────────┼───────────────────────────────────────────────────────┤
│ Bug fix             │ architect (understand context) → FE or BE            │
│                     │ → unit-tester → code-reviewer                         │
├─────────────────────┼───────────────────────────────────────────────────────┤
│ Refactor            │ code-reviewer (identify) → FE or BE                  │
│                     │ → unit-tester → code-reviewer (verify)                │
├─────────────────────┼───────────────────────────────────────────────────────┤
│ New API endpoint    │ architect (contract) → backend                       │
│                     │ → integration-tester → code-reviewer                  │
├─────────────────────┼───────────────────────────────────────────────────────┤
│ UI change           │ frontend → unit-tester → code-reviewer                │
├─────────────────────┼───────────────────────────────────────────────────────┤
│ Tech spike          │ researcher → architect                                │
├─────────────────────┼───────────────────────────────────────────────────────┤
│ Deployment          │ devops                                                │
├─────────────────────┼───────────────────────────────────────────────────────┤
│ Production hotfix   │ BE or FE → unit-tester → devops                      │
├─────────────────────┼───────────────────────────────────────────────────────┤
│ Performance issue   │ researcher (profiling best practices) → backend       │
│                     │ → integration-tester (benchmark) → code-reviewer      │
├─────────────────────┼───────────────────────────────────────────────────────┤
│ Security audit      │ code-reviewer (security focus)                        │
│                     │ → backend (fix) → unit-tester                         │
└─────────────────────┴───────────────────────────────────────────────────────┘
```

---

## 4. Plugin Structure

```
hody-workflow/                          # Root = GitHub repo
├── .claude-plugin/
│   └── marketplace.json                # Marketplace registration
│
├── plugins/
│   └── hody-workflow/                  # Main plugin
│       ├── .claude-plugin/
│       │   └── plugin.json             # Plugin metadata
│       │
│       ├── agents/                     # 9 specialized agents
│       │   ├── researcher.md
│       │   ├── architect.md
│       │   ├── frontend.md
│       │   ├── backend.md
│       │   ├── code-reviewer.md
│       │   ├── spec-verifier.md
│       │   ├── unit-tester.md
│       │   ├── integration-tester.md
│       │   └── devops.md
│       │
│       ├── skills/
│       │   ├── project-profile/
│       │   │   ├── SKILL.md
│       │   │   └── scripts/
│       │   │       └── detect_stack.py
│       │   │
│       │   └── knowledge-base/
│       │       └── templates/
│       │           ├── architecture.md
│       │           ├── decisions.md
│       │           ├── api-contracts.md
│       │           ├── business-rules.md
│       │           ├── tech-debt.md
│       │           └── runbook.md
│       │
│       ├── hooks/
│       │   ├── hooks.json
│       │   └── inject_project_context.py
│       │
│       ├── commands/
│       │   ├── init.md
│       │   ├── start-feature.md
│       │   ├── status.md
│       │   ├── refresh.md
│       │   └── kb-search.md
│       │
│       ├── output-styles/
│       │   ├── review-report.md
│       │   ├── test-report.md
│       │   └── design-doc.md
│       │
│       └── README.md
│
├── test/
│   └── test_detect_stack.py
│
├── .gitignore
├── LICENSE
└── README.md                           # Repo-level docs
```

---

## 5. Core Components Detail

### 5.1. Project Profile (`detect_stack.py`)

Python script that auto-detects tech stack from project files:

```python
# Detection rules:
#
# package.json → Node.js project
#   dependencies.react → frontend: react
#   dependencies.vue → frontend: vue
#   dependencies.next → frontend: next (SSR)
#   dependencies.express → backend: express
#   dependencies.fastify → backend: fastify
#   devDependencies.jest → testing: jest
#   devDependencies.vitest → testing: vitest
#
# go.mod → Go project
#   github.com/gin-gonic/gin → backend: gin
#   github.com/labstack/echo → backend: echo
#
# requirements.txt / pyproject.toml → Python project
#   django → backend: django
#   fastapi → backend: fastapi
#   pytest → testing: pytest
#
# Dockerfile → containerize: docker
# .github/workflows/ → ci: github-actions
# .gitlab-ci.yml → ci: gitlab-ci
# Jenkinsfile → ci: jenkins
# *.tf → infra: terraform
# pulumi/ → infra: pulumi
```

**Output:** `.hody/profile.yaml`

```yaml
project:
  name: my-app                    # from package.json name or directory name
  type: fullstack                 # fullstack | frontend | backend | library | monorepo

frontend:
  framework: react                # react | vue | angular | svelte | next | nuxt
  language: typescript             # typescript | javascript
  state: zustand                  # redux | zustand | pinia | vuex | mobx
  styling: tailwind               # tailwind | css-modules | styled-components | scss
  testing: vitest                 # jest | vitest | cypress | playwright
  build: vite                     # vite | webpack | esbuild | turbopack
  dir: src/                       # FE source directory

backend:
  framework: fastify              # express | fastify | nest | gin | echo | django | fastapi
  language: typescript             # typescript | javascript | go | python | java | rust
  database: postgresql            # postgresql | mysql | mongodb | redis | sqlite
  orm: drizzle                    # prisma | drizzle | typeorm | gorm | sqlalchemy
  testing: vitest                 # jest | vitest | go-test | pytest
  dir: server/                    # BE source directory

devops:
  ci: github-actions              # github-actions | gitlab-ci | jenkins | circleci
  containerize: docker            # docker | podman | none
  deploy: aws-ecs                 # aws-ecs | kubernetes | vercel | netlify | fly-io
  infra: terraform                # terraform | pulumi | cdk | none
  monitoring: none                # datadog | grafana | newrelic | none

conventions:
  git_branch: feature/{description}
  commit_style: conventional      # conventional | angular | none
  pr_template: true               # detected from .github/PULL_REQUEST_TEMPLATE.md
  linter: eslint                  # eslint | biome | golangci-lint | ruff | none
  formatter: prettier             # prettier | biome | gofmt | black | none
```

### 5.2. Knowledge Base Templates

Each file in `.hody/knowledge/` has a standard structure:

**`architecture.md`**
```markdown
# Architecture

## System Overview
<!-- High-level system description -->

## Component Diagram
<!-- Main components and their relationships -->

## Data Flow
<!-- Primary data flows -->

## Tech Stack Rationale
<!-- Why this stack was chosen -->
```

**`decisions.md`**
```markdown
# Architecture Decision Records

## ADR-001: [Title]
- **Date**: YYYY-MM-DD
- **Status**: accepted | rejected | superseded
- **Context**: Problem to be solved
- **Decision**: Chosen approach
- **Alternatives**: Other options considered
- **Consequences**: Impact of the decision
```

**`api-contracts.md`**
```markdown
# API Contracts

## [Feature Name]

### POST /api/[endpoint]
- **Request**: { field: type }
- **Response**: { field: type }
- **Auth**: required | public
- **Notes**: Any special considerations
```

**`business-rules.md`**
```markdown
# Business Rules

## [Domain]

### Rule: [Name]
- **Description**: Rule description
- **Conditions**: When it applies
- **Actions**: What happens
- **Exceptions**: Edge cases
```

### 5.3. Hook: `inject_project_context.py`

Runs at `SessionStart`, reads `.hody/profile.yaml` and injects into the system message:

```python
# Pseudocode:
# 1. Read .hody/profile.yaml
# 2. Format into concise summary
# 3. Output: {"systemMessage": "Project: my-app | Stack: React + Fastify + PostgreSQL | ..."}
```

Purpose: every agent knows the project context AS SOON AS THE SESSION STARTS, without needing to read files.

### 5.4. Commands

**`/hody-workflow:init`** — Initialize hody workflow for the current project:
1. Run `detect_stack.py` → create `.hody/profile.yaml`
2. Create `.hody/knowledge/` with template files
3. Populate knowledge base with real project data (architecture, API routes, runbook commands, tech stack ADR)

**`/hody-workflow:start-feature`** — Start developing a new feature:
1. Ask user to describe the feature
2. Classify task type and suggest agents to use (based on task-to-agents mapping)
3. Begin THINK phase (researcher → architect)

**`/hody-workflow:status`** — View current status:
1. Profile summary
2. Knowledge base overview (filled vs empty sections)
3. Suggest the next agent to call

**`/hody-workflow:refresh`** — Re-detect project stack:
1. Re-run `detect_stack.py` to update `.hody/profile.yaml`
2. Useful when project dependencies or config files change

**`/hody-workflow:kb-search`** — Search the knowledge base:
1. Search across all `.hody/knowledge/*.md` files
2. Supports keyword search and section filtering
3. Returns matching snippets with context

---

## 6. Development Stack

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
# Unit tests for detect_stack.py
python -m pytest test/test_detect_stack.py

# Test with mock project structures
# Create temp directories simulating React project, Go project, Python project...
# Verify profile.yaml output is correct

# Integration test
# 1. Run /hody-workflow:init on a real project
# 2. Verify profile.yaml is accurate
# 3. Verify agents can read the profile
# 4. Verify knowledge base files are created
```

---

## 7. Workflow Usage In Practice

### 7.1. First Time Setup

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

### 7.2. Feature Development (full workflow)

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

### 7.3. Quick Tasks (no full workflow needed)

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

### 7.4. Calling agents directly

```bash
# Users can call any agent directly
User: "Use agent backend to implement a DELETE /api/users/:id endpoint"
User: "Use agent code-reviewer to review this PR"
User: "Use agent devops to setup monitoring"
```

---

## 8. Distribution & Installation

### 8.1. GitHub Repository

Create a new repo on your personal GitHub account:

- **Repo name**: `hody-workflow` (or your preferred name)
- **URL**: `github.com/<your-username>/hody-workflow`
- **Visibility**: Public (so other users can install) or Private (personal use only)

### 8.2. Marketplace Registration

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

- `name: "hody"` → this is the marketplace name; users will reference it with `@hody`
- To add more plugins later (e.g., `hody-voice`, `hody-mcp`), just add entries to the `plugins` array

### 8.3. User Installation

```bash
# Step 1: Add marketplace
/plugin marketplace add <your-username>/hody-workflow

# Step 2: Install plugin
/plugin install hody-workflow@hody

# Step 3: Restart Claude Code
# (plugins load at startup)

# Step 4: Init hody workflow in any project
cd ~/projects/my-app
claude
/hody-workflow:init
```

### 8.4. Update Plugin

When you push new code to GitHub:

```bash
# User updates plugin
/plugin update hody-workflow@hody

# Or reinstall
/plugin install hody-workflow@hody
```

### 8.5. What to commit in the target project

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

## 9. Step-by-step Build Guide

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

Each file follows the template from [Section 3.2](#32-agent-prompt-template).

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

Each file contains the standard template (see [Section 5.2](#52-knowledge-base-templates)).

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
/plugin marketplace add <your-username>/hody-workflow

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
/plugin marketplace add <your-username>/hody-workflow
/plugin install hody-workflow@hody
```

---

## 10. Development Roadmap

### Phase 1: Foundation (MVP) — Complete

**Goal**: Plugin works with 3 basic agents

- [x] Repo setup + marketplace.json + plugin.json
- [x] `detect_stack.py` — auto-detect top 5 popular stacks
- [x] `inject_project_context.py` — SessionStart hook
- [x] `hooks.json` — hook registration
- [x] `/hody-workflow:init` command
- [x] 3 agents: **architect**, **code-reviewer**, **unit-tester**
- [x] Knowledge base templates (6 files)
- [x] SKILL.md for project-profile
- [x] README.md
- [x] Basic tests for detect_stack.py (20 tests)

**Deliverable**: User can `/hody-workflow:init` → call 3 agents → agents are aware of project stack

### Phase 2: Full Agent Suite — Complete

**Goal**: All 9 agents, task-to-agents mapping

- [x] 6 remaining agents: researcher, frontend, backend, spec-verifier, integration-tester, devops
- [x] `/hody-workflow:start-feature` command (orchestrate workflow)
- [x] `/hody-workflow:status` command
- [x] Output styles (review-report, test-report, design-doc)
- [x] Extended stack detection (Rust, Java/Kotlin, Angular, Svelte — 31 tests)

**Deliverable**: Full development workflow running end-to-end

### Phase 3: Intelligence — Complete

**Goal**: Smarter detection, richer knowledge base, agent collaboration

| # | Task | Status | Description |
|---|------|--------|-------------|
| 1 | C#/.NET stack detection | Done | Detect `.csproj`, `.sln`, `global.json`; frameworks: ASP.NET Core, Blazor; ORM: Entity Framework; test: xUnit, NUnit, MSTest |
| 2 | Ruby stack detection | Done | Detect `Gemfile`, `Rakefile`; frameworks: Rails, Sinatra, Hanami; test: RSpec, Minitest |
| 3 | PHP stack detection | Done | Detect `composer.json`; frameworks: Laravel, Symfony, Magento; test: PHPUnit, Pest |
| 4 | Monorepo detection | Done | Detect `nx.json`, `turbo.json`, `lerna.json`, `pnpm-workspace.yaml`; identify workspace root vs sub-projects |
| 5 | Monorepo profile format | Done | Extend `profile.yaml` with `workspaces[]` — each sub-project has its own language, framework, testing |
| 6 | Auto-update profile | Done | `/hody-workflow:refresh` command or hook to detect config file changes → re-run `detect_stack.py` |
| 7 | Knowledge base search | Done | Skill/command to search across `.hody/knowledge/*.md` — supports keyword search and section filtering |
| 8 | Agent collaboration | Done | Delegation pattern — agents can recommend/invoke other agents (e.g., architect → researcher, code-reviewer → unit-tester) |
| 9 | Unit tests for new stacks | Done | Tests for C#, Ruby, PHP detection + monorepo detection (extend `test_detect_stack.py`) |
| 10 | Docs update | Done | Update README, USAGE_GUIDE with Phase 3 features upon completion |

**Technical Details**:

**New stack detection (Tasks 1-3)**: Extend `detect_stack.py` — add detection functions following the same pattern as Node.js/Go/Python/Rust/Java. Each stack detects: language, framework(s), testing tool(s), package manager.

**Monorepo (Tasks 4-5)**: `detect_stack.py` checks for monorepo markers at root. If detected, scans each workspace/package to create individual profiles. Output format:
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

**Auto-update profile (Task 6)**: Add `/hody-workflow:refresh` command — wrapper that re-runs `detect_stack.py`. Optionally add a SessionStart hook that checks config file modification times vs profile.yaml.

**Knowledge base search (Task 7)**: Skill reads all `.hody/knowledge/*.md` files, supports: keyword search (grep-like), list sections/headings, filter by file. Output as snippets with context.

**Agent collaboration (Task 8)**: Add `## Collaboration` section in agent prompts — defines when to suggest the user invoke another agent. No auto-invoke (Claude Code doesn't support it); instead, suggests via output message.

**Note**: "Detect more stacks (Rust, Java)" was completed in Phase 2 — Phase 3 only covers C#, Ruby, PHP.

**Deliverable**: Plugin detects 8+ stacks + monorepo, has knowledge base search, agents know how to delegate to each other

### Phase 4: Ecosystem

**Goal**: Integration with external tools

- [ ] MCP integration (GitHub, Linear, Jira)
- [ ] Pre-commit hooks (quality gates)
- [ ] CI integration (generate test reports)
- [ ] Team sharing (knowledge base sync)

---

## 11. Constraints & Risks

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

---

## Quick Reference

### Commands

| Command | Description |
|---------|-------------|
| `/hody-workflow:init` | Detect stack, create profile + populate knowledge base |
| `/hody-workflow:start-feature` | Start feature development workflow |
| `/hody-workflow:status` | View profile + KB summary + next steps |
| `/hody-workflow:refresh` | Re-detect stack, update profile.yaml |
| `/hody-workflow:kb-search` | Search across knowledge base files |

### Agents

| Agent | When to use |
|-------|-------------|
| researcher | Need to research tech, docs, best practices |
| architect | Need to design systems, flows, API contracts, business rules |
| frontend | Need to implement UI |
| backend | Need to implement API, business logic, DB |
| code-reviewer | Need to review code quality |
| spec-verifier | Need to verify code matches specs |
| unit-tester | Need to write unit tests |
| integration-tester | Need to write API/E2E tests |
| devops | Need CI/CD, deployment, infra |

### Files created in target project

| File | Description |
|------|-------------|
| `.hody/profile.yaml` | Project tech stack (auto-generated) |
| `.hody/knowledge/architecture.md` | System design |
| `.hody/knowledge/decisions.md` | Architecture Decision Records |
| `.hody/knowledge/api-contracts.md` | API specs |
| `.hody/knowledge/business-rules.md` | Business logic rules |
| `.hody/knowledge/tech-debt.md` | Known issues |
| `.hody/knowledge/runbook.md` | Operations guide |
