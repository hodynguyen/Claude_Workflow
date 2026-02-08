---
description: Show current project status including detected tech stack, knowledge base overview, and suggested next steps.
---

# /hody-workflow:status

Show the current Hody Workflow status for this project.

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

4. **Suggest next steps**: Based on the current state, suggest what the user could do next:

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
