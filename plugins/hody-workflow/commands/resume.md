---
description: Resume an interrupted workflow from the last checkpoint.
---

# /hody-workflow:resume

Resume an interrupted feature workflow from where it left off.

## Steps

Before resuming, check tracker for additional context about this workflow and related items:

```bash
python3 ${PLUGIN_ROOT}/skills/project-profile/scripts/tracker.py context --cwd .
```

This shows any warnings about stale items, related investigations, or other tracked items that may affect the current workflow.

1. **Check for active workflow**: Read `.hody/state.json`. If it doesn't exist or `status` is not `"in_progress"`, inform the user:

```
No active workflow found. Start one with /hody-workflow:start-feature
```

2. **Display workflow state**: Show the current workflow progress:

```
Resuming Workflow
━━━━━━━━━━━━━━━━
Feature: [feature description]
Type: [feature type]
Started: [created_at]

Progress: ██████░░░░ 3/8 agents (37%)

  THINK:  ✅ researcher → ✅ architect
  BUILD:  🔄 backend → ⬜ frontend
  VERIFY: ⬜ unit-tester → ⬜ code-reviewer
  SHIP:   ⬜ devops
```

Use these icons:
- ✅ completed
- 🔄 active (in progress)
- ⏭️ skipped
- ⬜ pending

3. **Show completed agent summaries**: For each completed agent in `agent_log`, show:

```
Completed work:
  ✅ researcher — "Researched OAuth2 vs JWT" (updated: decisions.md)
  ✅ architect — "Designed API contracts" (updated: architecture.md, api-contracts.md)
```

4. **Identify next agent**: Determine the next unfinished, unskipped agent by iterating through `phase_order` and each phase's `agents` list. Skip agents that are in `completed` or `skipped`.

5. **Ask user to continue**: Present options:

```
Next: [agent name] ([phase] phase)

Options:
  1. Continue with [agent name]
  2. Skip [agent name] and move to next
  3. Abort workflow
```

6. **Execute chosen action**:
   - **Continue**: Update `state.json` — set the agent as `active` in its phase, add a new entry to `agent_log` with `started_at`. Then activate the agent.
   - **Skip**: Update `state.json` — add agent to the phase's `skipped` list. Then show the next agent.
   - **Abort**: Update `state.json` — set `status` to `"aborted"`. Inform the user the workflow has been aborted.

## Notes

- This command is the counterpart to `/hody-workflow:start-feature` — start begins, resume continues
- Workflow state persists in `.hody/state.json` across sessions
- The knowledge base files modified by previous agents are available to the next agent automatically
- If all agents are completed, suggest running `/hody-workflow:start-feature` for a new workflow or completing the current one by setting `status` to `"completed"`
