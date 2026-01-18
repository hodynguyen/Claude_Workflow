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

Khi làm việc với Claude Code trên các dự án thực tế:

- Claude Code là general-purpose AI, không có workflow chuyên biệt cho development
- Không có agent chuyên sâu cho từng domain (FE, BE, testing, review...)
- Mỗi session mới, Claude phải khám phá lại project từ đầu
- Không có quy trình đảm bảo code quality trước khi commit
- Knowledge bị mất giữa các sessions

### Solution

**Hody Workflow** là một Claude Code plugin cung cấp:

- **9 specialized agents** cho từng phase của development
- **Auto-detect project stack** - zero config khi đổi project
- **Shared knowledge base** - knowledge tích lũy, persist qua sessions
- **Task-to-agents mapping** - tự động gợi ý agent phù hợp cho từng loại task
- **Abstract design** - 1 plugin hoạt động cho mọi project, mọi tech stack

### Design Principles

1. **Project-aware, not project-specific**: Agent prompts generic, behavior specific nhờ profile
2. **Composable, not rigid**: User gọi bất kỳ agent nào, workflow chỉ là recommended flow
3. **Accumulative knowledge**: Mỗi agent đọc VÀ ghi knowledge base
4. **Zero config**: Auto-detect stack, không yêu cầu user cấu hình manual
5. **Works offline**: Không phụ thuộc external API, MCP server optional

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
│  │ Chạy 1 lần qua /hody:init, mọi agent đọc chung           │ │
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
│  ├── Commands: /hody:init, /hody:start-feature, /hody:status    │
│  └── Output Styles: review-report, test-report, design-doc      │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
User request
     ↓
[Hook: SessionStart] → inject project profile vào system message
     ↓
Claude Code nhận request → xác định loại task
     ↓
Load agent phù hợp (từ agents/*.md)
     ↓
Agent đọc:
  1. .hody/profile.yaml (stack hiện tại)
  2. .hody/knowledge/* (context tích lũy)
     ↓
Agent thực hiện công việc
     ↓
Agent ghi lại knowledge mới (nếu có) vào .hody/knowledge/
     ↓
Output cho user
```

---

## 3. Agent Design

### 3.1. Agent Summary

| # | Agent | Group | Expertise | Input | Output | Scope |
|---|-------|-------|-----------|-------|--------|-------|
| 1 | researcher | THINK | External tech docs, best practices | Profile + câu hỏi | Tech summary → knowledge base | READ only |
| 2 | architect | THINK | System design, BA, flows, contracts | Requirements + KB | Architecture docs, ADRs, API contracts | READ + WRITE KB |
| 3 | frontend | BUILD | UI/UX theo stack FE của project | Profile FE + design docs | Code FE | WRITE code FE |
| 4 | backend | BUILD | API, business logic, DB | Profile BE + design docs | Code BE | WRITE code BE |
| 5 | code-reviewer | VERIFY | Code quality, patterns, security, perf | Code changes | Review report | READ only |
| 6 | spec-verifier | VERIFY | Logic khớp specs/business rules | Code + specs trong KB | Verification report | READ only |
| 7 | unit-tester | VERIFY | Unit tests, mocking, edge cases | Code + profile testing | Unit tests | WRITE tests |
| 8 | integration-tester | VERIFY | API tests, E2E, business flows | Code + API contracts + KB | Integration/E2E tests | WRITE tests |
| 9 | devops | SHIP | CI/CD, deployment, infra | Profile devops + arch docs | Pipeline configs, IaC | WRITE configs |

### 3.2. Agent Prompt Template

Mỗi agent `.md` theo cấu trúc sau:

```markdown
---
name: agent-name
description: Khi nào agent này được activate (cho Claude Code matching)
---

# Agent: [Role Name]

## Bootstrap (bắt buộc chạy đầu tiên)
1. Read `.hody/profile.yaml` → xác định tech stack
2. Read `.hody/knowledge/[relevant-files]` → hiểu project context
3. Xác nhận scope công việc với user nếu cần

## Core Expertise
- [Domain-specific knowledge]
- Adapt behavior theo profile:
  - Nếu profile.frontend.framework = "react" → apply React patterns
  - Nếu profile.frontend.framework = "vue" → apply Vue patterns

## Responsibilities
- [Cụ thể agent này làm gì]

## Constraints
- [Cụ thể agent này KHÔNG làm gì]

## Output Format
- [Format output chuẩn]

## Knowledge Base Update
- Sau khi hoàn thành, ghi knowledge mới vào `.hody/knowledge/[file]`
```

### 3.3. Task-to-Agents Mapping

```
┌─────────────────────┬───────────────────────────────────────────────────────┐
│ Task Type           │ Agents (theo thứ tự)                                  │
├─────────────────────┼───────────────────────────────────────────────────────┤
│ Feature mới         │ researcher → architect → FE + BE (parallel)          │
│                     │ → unit-tester + integration-tester                    │
│                     │ → code-reviewer + spec-verifier → devops              │
├─────────────────────┼───────────────────────────────────────────────────────┤
│ Bug fix             │ architect (understand context) → FE hoặc BE          │
│                     │ → unit-tester → code-reviewer                         │
├─────────────────────┼───────────────────────────────────────────────────────┤
│ Refactor            │ code-reviewer (identify) → FE hoặc BE               │
│                     │ → unit-tester → code-reviewer (verify)                │
├─────────────────────┼───────────────────────────────────────────────────────┤
│ API endpoint mới    │ architect (contract) → backend                       │
│                     │ → integration-tester → code-reviewer                  │
├─────────────────────┼───────────────────────────────────────────────────────┤
│ UI change           │ frontend → unit-tester → code-reviewer                │
├─────────────────────┼───────────────────────────────────────────────────────┤
│ Tech spike          │ researcher → architect                                │
├─────────────────────┼───────────────────────────────────────────────────────┤
│ Deployment          │ devops                                                │
├─────────────────────┼───────────────────────────────────────────────────────┤
│ Hotfix production   │ BE hoặc FE → unit-tester → devops                    │
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
│   └── hody-workflow/                  # Plugin chính
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
│       │       ├── SKILL.md
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
│       │   └── status.md
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

Script Python auto-detect tech stack từ project files:

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
  name: my-app                    # từ package.json name hoặc directory name
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

Mỗi file trong `.hody/knowledge/` có cấu trúc chuẩn:

**`architecture.md`**
```markdown
# Architecture

## System Overview
<!-- Mô tả tổng quan hệ thống -->

## Component Diagram
<!-- Các components chính và quan hệ -->

## Data Flow
<!-- Luồng dữ liệu chính -->

## Tech Stack Rationale
<!-- Tại sao chọn stack này -->
```

**`decisions.md`**
```markdown
# Architecture Decision Records

## ADR-001: [Title]
- **Date**: YYYY-MM-DD
- **Status**: accepted | rejected | superseded
- **Context**: Vấn đề cần giải quyết
- **Decision**: Quyết định đã chọn
- **Alternatives**: Các phương án khác đã xem xét
- **Consequences**: Hệ quả của quyết định
```

**`api-contracts.md`**
```markdown
# API Contracts

## [Feature Name]

### POST /api/[endpoint]
- **Request**: { field: type }
- **Response**: { field: type }
- **Auth**: required | public
- **Notes**: Đặc biệt gì
```

**`business-rules.md`**
```markdown
# Business Rules

## [Domain]

### Rule: [Name]
- **Description**: Mô tả rule
- **Conditions**: Khi nào apply
- **Actions**: Xảy ra gì
- **Exceptions**: Ngoại lệ
```

### 5.3. Hook: `inject_project_context.py`

Chạy ở `SessionStart`, đọc `.hody/profile.yaml` và inject vào system message:

```python
# Pseudocode:
# 1. Read .hody/profile.yaml
# 2. Format thành concise summary
# 3. Output: {"systemMessage": "Project: my-app | Stack: React + Fastify + PostgreSQL | ..."}
```

Mục đích: mọi agent đều biết project context NGAY KHI SESSION BẮT ĐẦU, không cần đọc file.

### 5.4. Commands

**`/hody:init`** - Khởi tạo hody workflow cho project hiện tại:
1. Chạy `detect_stack.py` → tạo `.hody/profile.yaml`
2. Tạo `.hody/knowledge/` với các template files
3. Add `.hody/` vào `.gitignore` nếu user muốn (hoặc commit nếu team dùng chung)

**`/hody:start-feature`** - Bắt đầu develop feature mới:
1. Hỏi user mô tả feature
2. Gợi ý agents cần dùng (dựa trên task-to-agents mapping)
3. Bắt đầu phase THINK (researcher → architect)

**`/hody:status`** - Xem trạng thái hiện tại:
1. Profile summary
2. Knowledge base overview
3. Gợi ý agent tiếp theo nên gọi

---

## 6. Development Stack

### Ngôn ngữ & Tools cần dùng

| Component | Ngôn ngữ | Lý do |
|-----------|---------|-------|
| Agent prompts | Markdown | Claude Code plugin format, không cần compile |
| Skill docs | Markdown (YAML frontmatter) | Claude Code plugin format |
| `detect_stack.py` | Python 3 | Parse YAML/JSON/TOML, filesystem operations |
| `inject_project_context.py` | Python 3 | Đọc YAML, output JSON cho Claude Code hook |
| Commands | Markdown | Claude Code plugin format |
| Hook config | JSON (`hooks.json`) | Claude Code plugin format |
| Project profile | YAML | Human-readable, dễ edit manual |
| Knowledge base | Markdown | Human-readable, versionable, Claude thân thiện |

### Dependencies

```
Python 3.8+      ← đã có sẵn trên macOS/Linux
PyYAML            ← parse profile.yaml (hoặc dùng built-in nếu tránh deps)
toml              ← parse Cargo.toml, pyproject.toml (Python 3.11+ có built-in)
```

Minimize external dependencies. Ưu tiên dùng Python stdlib. PyYAML là dependency duy nhất cần thiết.

### Testing

```bash
# Unit tests cho detect_stack.py
python -m pytest test/test_detect_stack.py

# Test với mock project structures
# Tạo temp directories giả lập React project, Go project, Python project...
# Verify profile.yaml output đúng

# Integration test
# 1. Chạy /hody:init trên project thật
# 2. Verify profile.yaml chính xác
# 3. Verify agents đọc được profile
# 4. Verify knowledge base files được tạo
```

---

## 7. Workflow Usage In Practice

### 7.1. First Time Setup

```bash
# User mở project và start Claude Code
cd ~/projects/my-saas-app
claude

# Khởi tạo hody workflow
User: /hody:init

# Claude Code chạy:
# 1. detect_stack.py scans project
# 2. Tạo .hody/profile.yaml
# 3. Tạo .hody/knowledge/ với templates
# 4. Output: "Detected: React 18 + TypeScript + Fastify + PostgreSQL + GitHub Actions"

# Từ giờ mọi session đều auto-inject project context
```

### 7.2. Feature Development (full workflow)

```bash
User: "Tôi cần implement chức năng user authentication với OAuth Google"

# Claude Code nhận diện: feature mới → gợi ý full workflow

# ─── PHASE 1: THINK ───
# researcher agent activate
Claude (researcher): "Để tôi research OAuth Google best practices cho stack React + Fastify..."
  → Tìm hiểu @react-oauth/google, passport-google-oauth20
  → Ghi findings vào .hody/knowledge/decisions.md

# architect agent activate
Claude (architect): "Dựa trên research, tôi thiết kế auth flow như sau..."
  → Tạo sequence diagram trong .hody/knowledge/architecture.md
  → Định nghĩa API contracts trong .hody/knowledge/api-contracts.md
  → Ghi business rules (session timeout, refresh token) vào business-rules.md

# ─── PHASE 2: BUILD ───
# backend agent activate
Claude (backend): "Implement auth API theo contracts đã define..."
  → POST /api/auth/google
  → GET /api/auth/me
  → POST /api/auth/refresh
  → Database migration: users table

# frontend agent activate
Claude (frontend): "Implement login UI và OAuth flow..."
  → LoginPage component với Google OAuth button
  → AuthContext provider
  → Protected route wrapper

# ─── PHASE 3: VERIFY ───
# unit-tester agent activate
Claude (unit-tester): "Viết unit tests cho auth modules..."
  → Test token validation edge cases
  → Test AuthContext behavior
  → Test API handler logic

# integration-tester agent activate
Claude (integration-tester): "Viết integration tests cho auth flow..."
  → Test: Google OAuth → callback → token → profile
  → Test: expired token → refresh → new token
  → Test: invalid token → 401

# code-reviewer agent activate
Claude (code-reviewer): "Review toàn bộ auth implementation..."
  → Security: token storage, CSRF, XSS
  → Code quality: error handling, naming
  → Performance: database queries

# spec-verifier agent activate
Claude (spec-verifier): "Verify implementation khớp với specs..."
  → Check API contracts match actual endpoints
  → Check business rules implemented correctly
  → Check edge cases covered

# ─── PHASE 4: SHIP ───
# devops agent activate (nếu cần)
Claude (devops): "Update CI pipeline cho auth..."
  → Thêm env vars cho Google OAuth credentials
  → Update deployment config
```

### 7.3. Quick Tasks (không cần full workflow)

```bash
# Bug fix - chỉ cần 2-3 agents
User: "Fix bug: login button không redirect đúng sau khi authenticate"
  → architect (hiểu context từ KB)
  → frontend (fix code)
  → unit-tester (verify fix)

# Code review - chỉ cần 1 agent
User: "Review file server/auth/handler.ts"
  → code-reviewer

# Research - chỉ cần 1 agent
User: "Tìm hiểu cách implement rate limiting cho API"
  → researcher
```

### 7.4. Gọi agent trực tiếp

```bash
# User có thể gọi bất kỳ agent nào trực tiếp
User: "Dùng agent backend để implement thêm endpoint DELETE /api/users/:id"
User: "Dùng agent code-reviewer để review PR này"
User: "Dùng agent devops để setup monitoring"
```

---

## 8. Distribution & Installation

### 8.1. GitHub Repository

Tạo repo mới trên GitHub account cá nhân:

- **Repo name**: `hody-workflow` (hoặc tên bạn chọn)
- **URL**: `github.com/<your-username>/hody-workflow`
- **Visibility**: Public (để user khác cài được) hoặc Private (chỉ mình dùng)

### 8.2. Marketplace Registration

File `.claude-plugin/marketplace.json` ở root repo:

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

- `name: "hody"` → đây là tên marketplace, user sẽ dùng `@hody` để reference
- Sau này muốn thêm plugin khác (vd: `hody-voice`, `hody-mcp`), chỉ cần thêm entry vào `plugins` array

### 8.3. User Installation

```bash
# Step 1: Add marketplace
/plugin marketplace add <your-username>/hody-workflow

# Step 2: Install plugin
/plugin install hody-workflow@hody

# Step 3: Restart Claude Code
# (plugins load khi khởi động)

# Step 4: Init hody workflow trong bất kỳ project nào
cd ~/projects/my-app
claude
/hody:init
```

### 8.4. Update Plugin

Khi bạn push code mới lên GitHub:

```bash
# User update plugin
/plugin update hody-workflow@hody

# Hoặc reinstall
/plugin install hody-workflow@hody
```

### 8.5. Cái gì nên Git trong target project

Khi user chạy `/hody:init` trong project của họ, sẽ tạo ra `.hody/` directory:

```
.hody/
├── profile.yaml              ← NÊN commit (team dùng chung profile)
└── knowledge/
    ├── architecture.md       ← NÊN commit (shared knowledge)
    ├── decisions.md          ← NÊN commit
    ├── api-contracts.md      ← NÊN commit
    ├── business-rules.md     ← NÊN commit
    ├── tech-debt.md          ← NÊN commit
    └── runbook.md            ← NÊN commit
```

Knowledge base SHOULD be committed - đây là tài sản của team, không phải temp files.

---

## 9. Step-by-step Build Guide

Các bước cụ thể để build hody-workflow plugin từ đầu.

### Step 1: Tạo GitHub repo

```bash
mkdir hody-workflow
cd hody-workflow
git init

# Tạo .gitignore
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

# Tạo repo trên GitHub và push
gh repo create hody-workflow --public --source=. --push
```

### Step 2: Tạo marketplace config

```bash
mkdir -p .claude-plugin
```

Tạo `.claude-plugin/marketplace.json`:
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

### Step 3: Tạo plugin structure

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

Tạo `plugins/hody-workflow/.claude-plugin/plugin.json`:
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

### Step 4: Viết hooks.json

Tạo `plugins/hody-workflow/hooks/hooks.json`:
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

### Step 5: Viết inject_project_context.py

Tạo `plugins/hody-workflow/hooks/inject_project_context.py`:
```python
#!/usr/bin/env python3
"""
SessionStart hook: đọc .hody/profile.yaml và inject project context
vào system message để mọi agent đều biết tech stack hiện tại.
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
            # Không có profile → skip
            print("{}")
            sys.exit(0)

        # Đọc profile (plain text, không cần PyYAML cho simple inject)
        with open(profile_path, "r") as f:
            profile_content = f.read()

        # Inject vào system message
        summary = f"[Hody Workflow] Project profile loaded from .hody/profile.yaml"
        output = {
            "systemMessage": summary
        }
        print(json.dumps(output))
        sys.exit(0)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(0)  # Không block session nếu hook lỗi

if __name__ == "__main__":
    main()
```

```bash
chmod +x plugins/hody-workflow/hooks/inject_project_context.py
```

### Step 6: Viết detect_stack.py

Tạo `plugins/hody-workflow/skills/project-profile/scripts/detect_stack.py`:
- Scan các config files (package.json, go.mod, requirements.txt, pyproject.toml...)
- Output `.hody/profile.yaml`
- Bắt đầu với top 5 stacks: Node/React, Node/Vue, Go, Python/Django, Python/FastAPI
- Mở rộng dần

```bash
chmod +x plugins/hody-workflow/skills/project-profile/scripts/detect_stack.py
```

### Step 7: Viết SKILL.md cho project-profile

Tạo `plugins/hody-workflow/skills/project-profile/SKILL.md`:
```markdown
---
name: project-profile
description: Use this skill when user asks to "detect project stack",
  "init hody", "setup hody workflow", or when you need to understand
  the current project's technology stack.
---

# Project Profile

Auto-detect project tech stack và tạo .hody/profile.yaml.

## Usage

Run the detection script:
\`\`\`bash
python3 ${SKILL_ROOT}/scripts/detect_stack.py --cwd .
\`\`\`

## Output
Creates `.hody/profile.yaml` with detected stack info.
```

### Step 8: Viết 3 agents đầu tiên (MVP)

Bắt đầu với 3 agents quan trọng nhất:

1. `plugins/hody-workflow/agents/architect.md`
2. `plugins/hody-workflow/agents/code-reviewer.md`
3. `plugins/hody-workflow/agents/unit-tester.md`

Mỗi file theo template ở [Section 3.2](#32-agent-prompt-template).

### Step 9: Viết command /hody:init

Tạo `plugins/hody-workflow/commands/init.md`:
```markdown
---
name: init
description: Initialize hody workflow for the current project
---

# /hody:init

Initialize hody workflow:

1. Run detect_stack.py to create .hody/profile.yaml
2. Create .hody/knowledge/ directory with template files
3. Show detected stack summary
```

### Step 10: Viết knowledge base templates

Tạo các files trong `plugins/hody-workflow/skills/knowledge-base/templates/`:
- `architecture.md`
- `decisions.md`
- `api-contracts.md`
- `business-rules.md`
- `tech-debt.md`
- `runbook.md`

Mỗi file chứa template chuẩn (xem [Section 5.2](#52-knowledge-base-templates)).

### Step 11: Viết README.md

Tạo `README.md` (repo root) và `plugins/hody-workflow/README.md` (plugin docs):
- Overview
- Installation
- Quick start
- Agent descriptions
- Commands reference

### Step 12: Test locally

```bash
# Cài plugin locally để test
cd ~/projects/some-test-project
claude

# Add marketplace từ local path (hoặc từ GitHub sau khi push)
/plugin marketplace add <your-username>/hody-workflow

# Install plugin
/plugin install hody-workflow@hody

# Restart Claude Code, rồi test
/hody:init
```

### Step 13: Push và publish

```bash
cd ~/path/to/hody-workflow
git add .
git commit -m "feat: initial hody-workflow plugin with 3 MVP agents"
git push origin main
```

Từ giờ bất kỳ ai cũng có thể cài plugin bằng:
```bash
/plugin marketplace add <your-username>/hody-workflow
/plugin install hody-workflow@hody
```

---

## 10. Development Roadmap

### Phase 1: Foundation (MVP)

**Goal**: Plugin hoạt động được với 3 agents cơ bản

- [ ] Repo setup + marketplace.json + plugin.json
- [ ] `detect_stack.py` - auto-detect top 5 popular stacks
- [ ] `inject_project_context.py` - SessionStart hook
- [ ] `hooks.json` - hook registration
- [ ] `/hody:init` command
- [ ] 3 agents: **architect**, **code-reviewer**, **unit-tester**
- [ ] Knowledge base templates (6 files)
- [ ] SKILL.md cho project-profile
- [ ] README.md
- [ ] Basic tests cho detect_stack.py

**Deliverable**: User có thể `/hody:init` → gọi 3 agents → agents aware project stack

### Phase 2: Full Agent Suite

**Goal**: Đủ 9 agents, task-to-agents mapping

- [ ] 6 agents còn lại: researcher, frontend, backend, spec-verifier, integration-tester, devops
- [ ] `/hody:start-feature` command (orchestrate workflow)
- [ ] `/hody:status` command
- [ ] Output styles (review-report, test-report, design-doc)
- [ ] Knowledge base management skill (SKILL.md)
- [ ] Detect thêm stacks (top 10)

**Deliverable**: Full development workflow chạy end-to-end

### Phase 3: Intelligence

**Goal**: Smarter detection, richer knowledge base

- [ ] Detect thêm stacks (Rust, Java, C#, Ruby, PHP...)
- [ ] Detect monorepo structures (nx, turborepo, lerna)
- [ ] Auto-update profile khi dependencies thay đổi
- [ ] Knowledge base search/query
- [ ] Agent collaboration patterns (agent gọi agent)

### Phase 4: Ecosystem

**Goal**: Tích hợp với tools bên ngoài

- [ ] MCP integration (GitHub, Linear, Jira)
- [ ] Pre-commit hooks (quality gates)
- [ ] CI integration (generate test reports)
- [ ] Team sharing (knowledge base sync)

---

## 11. Constraints & Risks

### Claude Code Plugin Constraints

| Constraint | Impact | Mitigation |
|-----------|--------|-----------|
| Agent prompts là static markdown | Không thể template dynamically | Agents đọc profile.yaml at runtime |
| Hooks timeout max 60s | detect_stack phải nhanh | Chỉ scan config files, không scan toàn bộ codebase |
| Không có persistent state ngoài files | Session state mất khi restart | Dùng `.hody/` directory trên filesystem |
| Plugin chỉ load khi Claude Code khởi động | Thay đổi plugin cần restart | Dùng session hooks cho dynamic behavior |

### Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| Profile detection sai | Medium | Agent nhận sai context | Cho phép user edit manual profile.yaml |
| Agent prompts quá dài | Medium | Tốn context window | Giữ prompts concise, dùng references |
| Knowledge base files conflict khi merge | Low | Git conflicts | Dùng append-only format, clear sections |
| Claude Code plugin API thay đổi | Low | Plugin hỏng | Follow Claude Code changelog, maintain compatibility |

### Out of Scope (v1)

- IDE integration (VS Code extension)
- Real-time collaboration giữa multiple users
- Custom agent creation UI
- Agent marketplace (user share agents)
- Automatic agent selection (v1 dùng manual + suggestion)

---

## Quick Reference

### Commands

| Command | Mô tả |
|---------|-------|
| `/hody:init` | Detect stack, tạo profile + knowledge base |
| `/hody:start-feature` | Bắt đầu feature development workflow |
| `/hody:status` | Xem profile + KB summary + next steps |

### Agents

| Agent | Gọi khi |
|-------|---------|
| researcher | Cần tìm hiểu tech, docs, best practices |
| architect | Cần design system, flows, API contracts, business rules |
| frontend | Cần implement UI |
| backend | Cần implement API, business logic, DB |
| code-reviewer | Cần review code quality |
| spec-verifier | Cần verify code đúng specs |
| unit-tester | Cần viết unit tests |
| integration-tester | Cần viết API/E2E tests |
| devops | Cần CI/CD, deployment, infra |

### Files tạo trong target project

| File | Mô tả |
|------|-------|
| `.hody/profile.yaml` | Project tech stack (auto-generated) |
| `.hody/knowledge/architecture.md` | System design |
| `.hody/knowledge/decisions.md` | Architecture Decision Records |
| `.hody/knowledge/api-contracts.md` | API specs |
| `.hody/knowledge/business-rules.md` | Business logic rules |
| `.hody/knowledge/tech-debt.md` | Known issues |
| `.hody/knowledge/runbook.md` | Operations guide |
