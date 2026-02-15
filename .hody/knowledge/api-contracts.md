# API Contracts

No API endpoints detected — this is a Claude Code plugin project, not a web application.

The plugin exposes functionality through:

## Commands (slash commands)

| Command | Description |
|---------|-------------|
| `/hody-workflow:init` | Detect stack, create profile + populate knowledge base |
| `/hody-workflow:start-feature` | Start guided feature development workflow |
| `/hody-workflow:status` | View profile + KB summary + next steps |
| `/hody-workflow:refresh` | Re-detect stack, update profile.yaml |
| `/hody-workflow:kb-search` | Search across knowledge base files |
| `/hody-workflow:connect` | Configure MCP server integrations (GitHub, Linear, Jira) |
| `/hody-workflow:ci-report` | Generate CI-compatible test report (GitHub Actions, JUnit XML, Markdown) |
| `/hody-workflow:sync` | Sync knowledge base with shared location for team collaboration |
| `/hody-workflow:update-kb` | Rescan codebase and update knowledge base files |

## Hooks

| Hook | Trigger | Script |
|------|---------|--------|
| SessionStart | Every new Claude Code session | `inject_project_context.py` — reads profile.yaml, injects into system message |
| PreCommit | Before git commit (quality gate) | `quality_gate.py` — runs code-reviewer checks on staged files |

## Scripts (CLI)

| Script | Usage |
|--------|-------|
| `detect_stack.py --cwd <path>` | Scan project files and generate `.hody/profile.yaml` |
| `quality_gate.py <file1> <file2> ...` | Run quality checks on specified files |
| `kb_sync.py --mode <git\|gist\|repo> --cwd <path>` | Sync knowledge base with shared location |
