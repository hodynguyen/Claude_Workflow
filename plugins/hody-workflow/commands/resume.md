---
description: Resume an interrupted workflow from the last checkpoint.
argument-hint: "[optional: specific agent to resume or skip, e.g. 'skip code-reviewer']"
---

# /hody-workflow:resume

Resume an interrupted feature workflow from where it left off.

## User Instructions

$ARGUMENTS

If the section above contains text, apply it as guidance for this resume:
- "skip <agent>" → mark that agent as skipped in state.json before computing next
- "restart <agent>" → clear that agent's checkpoint and start fresh
- "continue from <agent>" → jump directly to that agent instead of the default next
- "focus on <area>" → pass this as additional context to the next agent

If empty, resume normally by finding the next unfinished agent.

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

4. **Check for agent checkpoints**: Before identifying the next agent, check if there are saved checkpoints from interrupted agents:

```bash
python3 ${PLUGIN_ROOT}/skills/project-profile/scripts/tracker.py checkpoint-list --workflow-id <workflow_id>
```

If a checkpoint exists for the next agent (or the currently active agent), display the checkpoint progress:

```
📌 Checkpoint found for [agent name]:
   Progress: [completed_items]/[total_items] items done
   Last updated: [updated_at]
   Resume from: [resume_hint]

   Completed items:
   - [item.id]: [item.summary]
   - [item.id]: [item.summary]

   Remaining:
   - [item.id] (pending)
```

5. **Identify next agent**: Determine the next unfinished, unskipped agent by iterating through `phase_order` and each phase's `agents` list. Skip agents that are in `completed` or `skipped`.

6. **Ask user to continue**: Present options:

```
Next: [agent name] ([phase] phase)
[If checkpoint exists: "Has checkpoint — will resume from: [resume_hint]"]

Options:
  1. Continue with [agent name] [from checkpoint if exists]
  2. Restart [agent name] from scratch (discard checkpoint)
  3. Skip [agent name] and move to next
  4. Abort workflow
```

7. **Execute chosen action**:
   - **Continue**: Update `state.json` — set the agent as `active` in its phase, add a new entry to `agent_log` with `started_at`. Then activate the agent. **If a checkpoint exists, pass the checkpoint data to the agent prompt so it can continue from where it left off** — include the `partial_output`, `resume_hint`, and the list of completed/pending items.
   - **Restart from scratch**: Clear the checkpoint first (`tracker.py checkpoint-clear --workflow-id <id> --agent <name>`), then start the agent fresh.
   - **Skip**: Update `state.json` — add agent to the phase's `skipped` list. Clear any checkpoint for this agent. Then show the next agent.
   - **Abort**: Update `state.json` — set `status` to `"aborted"`. Inform the user the workflow has been aborted.

## Notes

- This command is the counterpart to `/hody-workflow:start-feature` — start begins, resume continues
- Workflow state persists in `.hody/state.json` across sessions
- The knowledge base files modified by previous agents are available to the next agent automatically
- If all agents are completed, suggest running `/hody-workflow:start-feature` for a new workflow or completing the current one by setting `status` to `"completed"`
- **Checkpoints**: When an agent is interrupted (context limit, disconnect, etc.), its checkpoint in `tracker.db` preserves exactly what work was done. On resume, the agent receives the checkpoint data so it can skip already-completed items and continue from `resume_hint`. Agents should save checkpoints incrementally as they complete each unit of work.
