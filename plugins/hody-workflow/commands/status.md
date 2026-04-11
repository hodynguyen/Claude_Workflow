---
description: Show current project status including detected tech stack, knowledge base overview, and suggested next steps.
argument-hint: "[optional: focus area, e.g. 'verbose' or 'kb only']"
---

# /hody-workflow:status

Show the current Hody Workflow status for this project.

## User Instructions

$ARGUMENTS

If the section above contains text, apply it as a filter or focus for the status output:
- "verbose" → show full profile.yaml, all KB files with line counts, full workflow state
- "kb only" → show only knowledge base status, skip tech stack and workflow
- "workflow only" → show only active workflow state and checkpoints
- "tracker" → include tracker.db stats (active items, recent sessions)

If empty, show the default status summary.

## Steps

1. **Check initialization**: Verify `.hody/profile.yaml` exists. If not, tell the user to run `/hody-workflow:init` first.

2. **Read profile**: Read `.hody/profile.yaml` and display a summary:

```
Project: [project name or directory]
Type: [fullstack | frontend | backend | library | unknown]

Stack:
  Frontend: [framework] + [language] (styling: [approach], testing: [framework])
  Backend:  [framework] + [language] (testing: [framework])
  DevOps:   [CI] + [containerization] + [infra]
```

Only show sections that exist in the profile (e.g., skip Frontend if no frontend detected).

3. **Check knowledge base**: For each file in `.hody/knowledge/`, check if it has content beyond the template header:

```
Knowledge Base:
  ✅ architecture.md    (last modified: [date])
  ✅ decisions.md        (3 ADRs)
  ✅ api-contracts.md    (5 endpoints)
  ⚠️  business-rules.md  (empty — template only)
  ⚠️  tech-debt.md       (empty — template only)
  ✅ runbook.md          (deployment guide)
```

Use ✅ for files with content and ⚠️ for files that are still just the template.

4. **Check active workflow**: If `.hody/state.json` exists and `status` is `"in_progress"`, display workflow progress:

```
Active Workflow:
  Feature: [description]
  Type: [type]
  Spec: [✅ Confirmed (spec-oauth2-login.md) | ⚠️ Pending — discovery incomplete]
  Mode: [Auto-execution | Discovery — waiting for spec confirmation]
  Progress: ██████░░░░ 3/8 agents (37%)

  THINK:  ✅ researcher → ✅ architect
  BUILD:  🔄 backend → ⬜ frontend
  VERIFY: ⬜ unit-tester → ⬜ code-reviewer
  SHIP:   ⬜ devops

  Next: Complete [current agent], then start [next agent]
  Resume: /hody-workflow:resume
```

Read `spec_confirmed` and `spec_file` from state.json:
- If `spec_confirmed` is `true` → show "Spec: ✅ Confirmed ([spec_file])" and "Mode: Auto-execution"
- If `spec_confirmed` is `false` or missing → show "Spec: ⚠️ Pending" and "Mode: Discovery"

Use these icons: ✅ completed, 🔄 active, ⏭️ skipped, ⬜ pending.

Calculate progress as `(completed + skipped) / total agents`. Build the progress bar with filled blocks (█) and empty blocks (░), 10 characters wide.

If no active workflow exists, skip this section.

5. **Check tracker state**: If `.hody/tracker.db` exists, show active tracked items:

```
Active Items:
  [HIGH] Task: "OAuth2 login" (in_progress, 3d)
  [MED]  Investigation: "Auth module" (paused, 2w)

Warnings:
  ⚠ Task "Payment refactor" paused 7 days — resume or abandon
```

Run to get tracker context:
```bash
python3 ${PLUGIN_ROOT}/skills/project-profile/scripts/tracker.py context --cwd .
```

Only show this section if tracker.db exists and has active items.

6. **Suggest next steps**: Based on the current state, suggest what the user could do next:

- If knowledge base files are empty → suggest using the architect agent to fill them
- If no tests exist → suggest using unit-tester or integration-tester
- If profile exists and KB is populated → suggest `/hody-workflow:start-feature` to begin a new feature
- If recent code changes exist → suggest using code-reviewer

## Output

Display all sections in a clean, readable format. Example:

```
🔧 Hody Workflow Status
━━━━━━━━━━━━━━━━━━━━━━

Project: my-app (fullstack)
Stack: React 18 + TypeScript | Fastify + TypeScript | Docker + GitHub Actions

Knowledge Base:
  ✅ architecture.md    — System design documented
  ✅ decisions.md        — 3 ADRs
  ✅ api-contracts.md    — 5 endpoints defined
  ⚠️  business-rules.md  — Empty
  ⚠️  tech-debt.md       — Empty
  ✅ runbook.md          — Deployment guide

Suggested next steps:
  → Define business rules (use architect agent)
  → Or start a new feature: /hody-workflow:start-feature
```

## Notes

- This command is read-only — it does not modify any files
- It reads `.hody/profile.yaml` and scans `.hody/knowledge/` directory
- Useful as a quick check when starting a new session
