---
description: Initialize hody workflow for the current project. Detects tech stack, creates knowledge base, and populates it with project context.
---

# /hody-workflow:init

Initialize Hody Workflow for the current project.

## Prerequisites — Root Directory Check

**CRITICAL**: Before doing anything, verify that `.hody/` will be created at the **project root directory** — the directory where the user launched Claude Code (the initial working directory of the session).

**How to determine the root directory**: Use the current working directory (`.`). Do NOT `cd` into a subdirectory or microservice before running init. If the project is a monorepo or multi-service repo (e.g., contains multiple `*-microservice/` or `*-service/` directories), `.hody/` MUST be placed at the top-level root, NOT inside any individual service.

**Validation**: Run `pwd` and confirm the output matches the project root. If the current directory is a subdirectory (e.g., `/project/24K/24k-email-microservice`), navigate back to the root (e.g., `/project/24K/`) before proceeding.

## Steps

1. **Detect tech stack**: Run the project-profile skill to scan the project and generate `.hody/profile.yaml`

```bash
python3 ${PLUGIN_ROOT}/skills/project-profile/scripts/detect_stack.py --cwd .
```

2. **Create knowledge base**: Copy template files to `.hody/knowledge/` if they don't already exist

Copy each template from `${PLUGIN_ROOT}/skills/knowledge-base/templates/` to `.hody/knowledge/`:
- `architecture.md`
- `decisions.md`
- `api-contracts.md`
- `business-rules.md`
- `tech-debt.md`
- `runbook.md`

Only copy files that don't already exist — never overwrite existing knowledge.

3. **Populate knowledge base**: Scan the project codebase and fill knowledge files with actual content. For each file below, read the relevant source files, then **replace the template placeholders** with real project data.

### 3a. architecture.md

Scan the project directory structure and source code to fill in:
- **System Overview**: Project type (from profile.yaml), main purpose (from README if exists), high-level description
- **Component Diagram**: List top-level directories and their roles (e.g., `src/components/` → UI components, `src/api/` → API handlers). Use a simple text diagram showing relationships
- **Data Flow**: Identify entry points (main files, route handlers, app bootstrap) and describe how a request/data flows through the system
- **Tech Stack Rationale**: From profile.yaml, document the detected stack choices (framework, language, DB, ORM, styling, testing, CI/CD)

Sources to scan: directory listing, README, main entry files, profile.yaml

### 3b. api-contracts.md

Search for existing API route definitions and document them:
- If Node.js (Express/Fastify/Nest): search for `app.get`, `app.post`, `router.`, `@Get`, `@Post` patterns
- If Python (FastAPI/Flask/Django): search for `@app.route`, `@router.`, `path(`, `urlpatterns`
- If Go (Gin/Echo/Fiber): search for `r.GET`, `r.POST`, `e.GET`, `app.Get` patterns

For each endpoint found, document: method, path, and brief description based on handler name. If no API routes are found, note "No API endpoints detected" and keep the template format for future use.

### 3c. decisions.md

Create ADR-001 documenting the initial tech stack detected from profile.yaml:
- **Title**: "Initial Tech Stack"
- **Status**: accepted
- **Context**: What was detected in the project
- **Decision**: Document each technology choice (language, framework, database, ORM, testing, CI/CD, styling)
- **Consequences**: What this means for development (e.g., "TypeScript chosen → strict typing required")

### 3d. runbook.md

Search for available commands and operational information:
- Read `scripts` section from `package.json` (if exists) → document dev, build, test, lint commands
- Check for `Makefile` → document available make targets
- Check for `docker-compose.yml` → document container start/stop commands
- Check for CI config (`.github/workflows/`) → note CI pipeline exists
- Check README for any deployment or setup instructions

Fill in: Deployment steps, common dev commands, how to run tests, how to start the project locally.

### 3e. business-rules.md and tech-debt.md

Leave these as templates — they cannot be reliably auto-detected from code. Note at the top: "To be filled by the team as business rules are defined" / "To be filled as tech debt is identified during development".

4. **Build KB index**: After populating knowledge files, build `.hody/knowledge/_index.json` by scanning all `.md` files in the knowledge directory. For each file, extract:
   - YAML frontmatter (tags, author_agent, created, status) if present
   - Section headings (## level)
   - Line count

   This index enables structured search via `/hody-workflow:kb-search` (tag, agent, status filters).

5. **Check KB file sizes**: If any KB file exceeds 500 lines, archive older sections to `.hody/knowledge/archive/`. Keep the 3 most recent sections in the main file, move the rest to an archive file named `<filename>-archive-<timestamp>.md`.

6. **Initialize tracker database** (REQUIRED — always run this step, even if `.hody/` already exists): Create or upgrade the interaction tracker database for persistent state tracking and agent checkpoints.

Run the tracker initialization:
```bash
python3 ${PLUGIN_ROOT}/skills/project-profile/scripts/tracker.py init --cwd .
```

This creates `.hody/tracker.db` (idempotent — safe to run multiple times). The database stores:
- Interaction tracking (tasks, investigations, questions)
- Agent checkpoints (progress that survives context limit interruptions)
- Session history

The database is local-only and should be added to `.gitignore`.

If the project already has a `.hody/state.json` from a previous workflow, also run migration:
```bash
python3 ${PLUGIN_ROOT}/skills/project-profile/scripts/tracker.py migrate --cwd .
```

7. **Show summary**: Display the detected stack and populated knowledge base

## Output

After running, show the user:
- Detected project type (fullstack, frontend, backend, etc.)
- Detected frameworks and languages
- Knowledge base status: which files were populated with content, which remain as templates
- Tracker database status: whether `.hody/tracker.db` was initialized (and whether state.json was migrated)
- Suggest next steps: "Use `/hody-workflow:start-feature` to begin a guided development workflow, or call agents directly (e.g., architect, code-reviewer, unit-tester)"

## Notes

- This command only needs to run once per project, but can be re-run safely
- `.hody/profile.yaml` can be re-generated by running this command again
- Knowledge base files are never overwritten — only missing files are created
- The populate step reads source files but does not modify any project code
- **Step 6 (tracker database) MUST always run**, even on re-init — `init_db` is idempotent and will add new tables (like `checkpoints`) if they don't exist yet. Without `tracker.db`, agent checkpoints cannot be saved and progress will be lost on interruption
- Recommend committing `.hody/` to git for team sharing (exclude `tracker.db` — it's local-only)
