---
description: Rescan project codebase and update .hody/knowledge/ files with the latest architecture, APIs, and runbook commands.
---

# /hody-workflow:update-kb

Rescan the project codebase and intelligently update knowledge base files to reflect the current state.

## Important: Merge Strategy

**NEVER overwrite knowledge base files from scratch.** This command uses an intelligent merge approach:

1. Read the existing content of each KB file first
2. Identify which sections are auto-generated vs. manually written
3. Update only auto-generated sections; preserve all manual content
4. Append new findings to existing sections rather than replacing them
5. When removing outdated items, mark them as `(Deprecated)` rather than deleting

Manual sections to always preserve:
- Any content under headings containing "Manual", "Notes", "Rationale", "Context", or "Discussion"
- The `business-rules.md` file (entirely manual — skip unless adding a TODO scan section)
- ADR entries in `decisions.md` (never modify existing ADRs)

## Steps

### Step 1: Analyze Baseline

1. **Check initialization**: Verify `.hody/profile.yaml` and `.hody/knowledge/` exist. If not, tell the user to run `/hody-workflow:init` first.

2. **Read current state**:
   - Read `.hody/profile.yaml` to understand the tech stack
   - Read all `.hody/knowledge/*.md` files to understand the current baseline
   - Note the last-modified dates to understand staleness

3. **Identify stack-specific scan patterns** from the profile:
   - Node.js → scan `package.json` scripts, route patterns (`app.get`, `router.`, `@Get`, `@Post`)
   - Python → scan for `@app.route`, `@router.`, `path(`, FastAPI/Flask/Django patterns
   - Go → scan for `r.GET`, `e.GET`, `app.Get`, handler functions
   - Rust → scan for Actix/Axum route macros
   - Java/Kotlin → scan for `@RequestMapping`, `@GetMapping`, `@PostMapping`
   - C#/.NET → scan for `[HttpGet]`, `[HttpPost]`, `MapGet`, `MapPost`
   - Ruby → scan for `get '/'`, `resources :`, Rails route patterns
   - PHP → scan for Laravel routes, Symfony controllers

### Step 2: Update Architecture (architecture.md)

1. **Scan directory structure**: Run a directory tree (top 3 levels) and compare with the existing "Component Diagram" or "Directory Structure" section in `architecture.md`.

2. **Detect new modules**: Look for new top-level directories or significant new subdirectories that aren't documented.

3. **Update the architecture file**:
   - If the directory structure section exists, update it in-place with the current tree
   - If new significant modules were added (new directories with source files), append them to the component descriptions
   - Do NOT remove existing component descriptions — they may contain manual context

### Step 3: Update API Contracts (api-contracts.md)

1. **Scan for endpoints**: Based on the detected stack, search for route/endpoint definitions across the codebase.

2. **Compare with existing**: Read the current `api-contracts.md` and identify:
   - **New endpoints**: Found in code but not in the KB → append to the list
   - **Missing endpoints**: In the KB but no longer in code → mark as `(Deprecated)` with today's date
   - **Unchanged endpoints**: Leave as-is (preserve any manual descriptions)

3. **Update format**: For each new endpoint, document:
   ```
   ### METHOD /path
   - **Handler**: `functionName` in `file/path.ext`
   - **Description**: [inferred from handler name or brief code context]
   - **Added**: [today's date]
   ```

4. If no API endpoints exist in the project, skip this step.

### Step 4: Update Runbook (runbook.md)

1. **Scan for commands**:
   - `package.json` → read `scripts` section for dev/build/test/lint/start commands
   - `Makefile` → parse targets (lines matching `target_name:`)
   - `docker-compose.yml`/`docker-compose.yaml` → note available services
   - `Dockerfile` → note build/run commands
   - CI config (`.github/workflows/`, `.gitlab-ci.yml`) → note pipeline commands
   - `pyproject.toml` / `setup.py` → Python project commands
   - `Cargo.toml` → Rust build/test commands
   - `go.mod` → Go build/test patterns

2. **Compare with existing**: Identify new commands not yet documented, and commands that no longer exist.

3. **Update the runbook**:
   - Add new commands under the appropriate section (Development, Build, Test, Deploy)
   - Mark removed commands as `(Removed)` rather than deleting them
   - Preserve any manual operational notes, troubleshooting guides, or deployment procedures

### Step 5: Scan Tech Debt (tech-debt.md)

1. **Scan for code markers**: Search the codebase for these patterns:
   - `TODO:` or `TODO(`
   - `FIXME:` or `FIXME(`
   - `HACK:` or `HACK(`
   - `XXX:` or `XXX(`
   - `DEPRECATED:`

   Exclude: `node_modules/`, `vendor/`, `dist/`, `build/`, `.hody/`, lock files.

2. **Format findings**: Group by type and file:
   ```
   ### Detected Codebase TODOs
   > Auto-scanned on [today's date]. Re-run `/hody-workflow:update-kb` to refresh.

   | Type | File | Line | Description |
   |------|------|------|-------------|
   | TODO | src/auth.ts:42 | Implement token refresh |
   | FIXME | src/db.ts:18 | Connection pool leak |
   ```

3. **Merge into tech-debt.md**:
   - If a "Detected Codebase TODOs" section exists, replace it entirely (it's auto-generated)
   - If it doesn't exist, append it at the end of the file
   - NEVER modify other sections in tech-debt.md (manual entries, prioritization, etc.)

### Step 6: Summary

Display a change summary showing exactly what was updated.

## Output

After running, show the user:

```
📚 Knowledge Base Updated
━━━━━━━━━━━━━━━━━━━━━━━━

architecture.md:
  ✅ Updated directory structure (2 new modules added)
  — Component descriptions unchanged

api-contracts.md:
  ✅ Added 3 new endpoints (GET /users, POST /auth/login, DELETE /users/:id)
  ⚠️  Marked 1 endpoint as deprecated (GET /legacy/status)

runbook.md:
  ✅ Added 2 new scripts (lint:fix, db:migrate)
  — Deployment guide unchanged

tech-debt.md:
  ✅ Found 8 TODOs, 2 FIXMEs across 5 files
  — Manual debt entries preserved

business-rules.md:
  — Skipped (manual content only)

decisions.md:
  — Skipped (ADRs are manual entries)
```

If nothing changed: "Knowledge base is up to date — no changes detected."

## Notes

- This command modifies `.hody/knowledge/` files — review changes via `git diff` after running
- Safe to run repeatedly — uses merge strategy, not overwrite
- Does NOT modify `business-rules.md` content or existing ADRs in `decisions.md`
- Does NOT modify any project source code
- For first-time setup, use `/hody-workflow:init` instead
- Recommend committing KB changes to git for team visibility
