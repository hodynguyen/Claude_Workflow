---
description: Start a spec-driven feature development workflow. Gathers requirements through discovery questions, confirms spec with user, then auto-runs all agents without interruption.
argument-hint: "[feature description and/or focus, e.g. 'add OAuth2 login, focus on security']"
---

# /hody-workflow:start-feature

Start a spec-driven, multi-phase feature development workflow.

## User Instructions

$ARGUMENTS

If the section above contains text, treat it as the user's initial feature description and/or additional guidance for this workflow. Use it to:
- Pre-fill step 2 (feature description) so you can skip asking if the description is clear enough
- Apply focus areas (e.g. "focus on security" → emphasize code-reviewer + spec-verifier)
- Narrow scope (e.g. "only backend" → skip frontend agent in BUILD)
- Override the default agent sequence if the user explicitly requests it

If empty, ask the user for the feature description normally as in step 2.

## Workflow Overview

This command follows a **spec-driven development** approach:

```
DISCOVERY → SPEC CONFIRMATION → AUTO-EXECUTION
     ↑              │
     └──────────────┘  (iterate until user confirms)
```

1. **Discovery**: Ask all clarifying questions upfront, discuss trade-offs with user
2. **Spec Confirmation**: Summarize everything into a clear spec, user confirms
3. **Auto-Execution**: Run all agents in sequence automatically — no stopping between agents

## Steps

### Phase A: Discovery

1. **Check initialization**: Verify `.hody/profile.yaml` exists. If not, run `/hody-workflow:init` first.

2. **Read project context**: Read `.hody/profile.yaml` and all `.hody/knowledge/` files to understand the current project state.

3. **Gather feature description**: If not provided in arguments, ask the user to describe the feature.

4. **Classify feature type**: Based on the description, classify into one of these types:

| Type | Description |
|------|-------------|
| `new-feature` | Entirely new functionality |
| `bug-fix` | Fix a reported bug |
| `refactor` | Restructure existing code without changing behavior |
| `api-endpoint` | New or modified API endpoint |
| `ui-change` | Frontend-only change |
| `tech-spike` | Research and prototyping |
| `deployment` | Infrastructure or deployment change |
| `hotfix` | Urgent production fix |

5. **Generate discovery questions**: Based on the feature type, tech stack (from profile.yaml), and existing knowledge base, compile a **single batch** of all questions that need clarification. Group them by category:

**For `new-feature` / `api-endpoint`:**
- **Architecture**: Where does this fit in the current system? New service or extend existing?
- **API Design**: What endpoints are needed? Request/response shapes? Auth requirements?
- **Data Model**: New tables/collections? Schema changes? Migrations needed?
- **Business Logic**: What are the core rules? Edge cases? Error scenarios?
- **Frontend** (if applicable): What UI components? User flow? State management approach?
- **Testing**: Coverage requirements? Integration test scenarios? E2E needed?
- **Deployment**: Feature flags? Rollback plan? Environment-specific config?

**For `bug-fix` / `hotfix`:**
- **Reproduction**: Steps to reproduce? Which environments?
- **Root Cause**: Known cause or needs investigation? Related recent changes?
- **Scope**: Which components are affected? Is it isolated or systemic?
- **Testing**: How to verify the fix? Regression tests needed?

**For `refactor`:**
- **Scope**: Which modules/files? What patterns to introduce/remove?
- **Behavior**: Must behavior stay identical? Any acceptable changes?
- **Testing**: Existing test coverage? Additional tests needed?
- **Migration**: Breaking API changes? Backward compatibility needed?

**For `tech-spike`:**
- **Goal**: What question are we trying to answer?
- **Constraints**: Time box? Must integrate with existing stack?
- **Output**: Prototype? Comparison doc? ADR?

Present ALL questions at once. Let the user answer in any order, partially, or all at once.

6. **Iterate until clear**: If answers are vague or raise new questions, ask follow-ups. But always batch questions — never ask one at a time. Continue until you have enough information to write a spec.

### Phase B: Spec Confirmation

7. **Write the spec**: Synthesize all discovery answers into a structured spec document. Present it to the user:

```
Feature Spec: [title]
━━━━━━━━━━━━━━━━━━━━

Type: [classified type]
Priority: [high/medium/low]

## Summary
[1-2 sentence description of what will be built]

## Requirements
- [Req 1]
- [Req 2]
- ...

## Technical Design
- Architecture: [approach]
- API Endpoints: [list with methods, paths, request/response]
- Data Model: [schema changes]
- Key Decisions: [trade-offs made during discovery]

## Out of Scope
- [What we explicitly won't do in this feature]

## Agent Workflow
  THINK:  [agents]
  BUILD:  [agents]
  VERIFY: [agents]
  SHIP:   [agents] (optional)

Estimated agents: [N] agents across [M] phases
```

8. **Get user confirmation**: Ask the user to confirm or request changes. The user may:
- Approve as-is → proceed to execution
- Request changes → update spec and re-present
- Add/remove agents → adjust the workflow
- Change scope → update requirements

Do NOT proceed to execution until the user explicitly confirms.

### Phase C: Auto-Execution

9. **Save spec to knowledge base**: Write the confirmed spec to `.hody/knowledge/spec-<slugified-feature>.md` with YAML frontmatter:

```markdown
---
tags: [spec, <feature-type>, <relevant-tags>]
date: <YYYY-MM-DD>
author-agent: start-feature
status: confirmed
---

# Spec: [feature title]

[Full spec content from step 7]
```

10. **Create workflow state and feature log**: Create `.hody/state.json`:

```json
{
  "workflow_id": "feat-<slugified-description>-<YYYYMMDD>",
  "feature": "<user's feature description>",
  "type": "<classified type>",
  "status": "in_progress",
  "spec_confirmed": true,
  "spec_file": "spec-<slugified-feature>.md",
  "log_file": "log-<slugified-feature>.md",
  "created_at": "<ISO 8601 UTC>",
  "updated_at": "<ISO 8601 UTC>",
  "phases": {
    "<PHASE>": {
      "agents": ["<agent1>", "<agent2>"],
      "completed": [],
      "active": null,
      "skipped": []
    }
  },
  "phase_order": ["THINK", "BUILD", "VERIFY", "SHIP"],
  "agent_log": []
}
```

Create the **feature log** file at `.hody/knowledge/log-<slugified-feature>.md`:

```markdown
---
tags: [log, <feature-type>]
date: <YYYY-MM-DD>
author-agent: start-feature
status: in_progress
---

# Feature Log: <feature title>

Type: <feature-type>
Started: <YYYY-MM-DD>

## Spec
-> spec-<slugified-feature>.md

## Agent Work
```

This log file is where each agent will append its detailed work record. It tracks:
- What each agent did (summary)
- Files created and modified in the codebase
- KB files updated
- Key decisions made

Also create a tracker item:

```bash
python3 ${PLUGIN_ROOT}/skills/project-profile/scripts/tracker.py create \
  --type task \
  --title "<feature description>" \
  --tags "<relevant tags>" \
  --priority medium \
  --cwd .
```

11. **Auto-run all agents**: Execute agents in sequence automatically. For each agent:
   - Set it as `active` in state.json, add `agent_log` entry
   - Activate the agent (it reads profile.yaml + KB + spec file + log file)
   - When agent completes:
     - Update state.json (completed, output_summary, kb_files_modified)
     - Agent appends its work record to the log file (files created/modified, KB updated, decisions)
   - **Immediately** proceed to next agent — do NOT pause to ask the user

   **Important**: Between agents, briefly show a one-line status update so the user can follow progress:
   ```
   ✅ researcher completed — "Researched OAuth2 providers" → Starting architect...
   ```

   **Parallel agents**: During BUILD phase, if both `frontend` and `backend` are present, run them in parallel.

12. **Complete workflow**: After all agents finish:
   - Finalize the feature log (append Summary section, update status to `completed`)
   - Set workflow status to `completed`
   - Show a final summary of all agent outputs
   - Update spec file status to `implemented`

## Agent Sequence by Feature Type

| Type | Agent Sequence |
|------|---------------|
| `new-feature` | researcher → architect → frontend + backend → unit-tester → integration-tester → code-reviewer → spec-verifier |
| `bug-fix` | architect → frontend or backend → unit-tester → code-reviewer |
| `refactor` | code-reviewer (assess) → frontend or backend → unit-tester → code-reviewer (verify) |
| `api-endpoint` | architect → backend → integration-tester → code-reviewer |
| `ui-change` | frontend → unit-tester → code-reviewer |
| `tech-spike` | researcher → architect |
| `deployment` | devops |
| `hotfix` | frontend or backend → unit-tester → devops |

## Output

### During Discovery
- Present all questions grouped by category
- Show the iterative spec as it develops

### During Execution
- One-line per agent completion
- Final summary with all outputs

### Final Summary
```
Workflow Complete
━━━━━━━━━━━━━━━━

Feature: [description]
Type: [type]
Duration: [time from start to finish]

Agent Results:
  ✅ researcher  — [summary]
  ✅ architect   — [summary]
  ✅ backend     — [summary]
  ✅ frontend    — [summary]
  ✅ unit-tester — [summary]
  ✅ code-reviewer — [summary]

KB Files Updated:
  → architecture.md
  → api-contracts.md
  → decisions.md

Spec: .hody/knowledge/spec-<feature>.md
Log:  .hody/knowledge/log-<feature>.md
```

## Notes

- **Discovery is interactive** — iterate with the user until spec is clear
- **Execution is automatic** — once spec is confirmed, agents run without interruption
- Frontend and backend agents can run in parallel during BUILD phase
- SHIP phase (devops) is included only for deployment/hotfix types
- Each agent reads the spec file + KB, so context flows naturally between agents
- If an agent is interrupted mid-execution, use `/hody-workflow:resume` to continue — it will auto-run remaining agents since spec is already confirmed
- Workflow state is persisted in `.hody/state.json`, spec in `.hody/knowledge/spec-*.md`, log in `.hody/knowledge/log-*.md`
- The feature log provides a complete audit trail of all work done — review it after workflow completes
