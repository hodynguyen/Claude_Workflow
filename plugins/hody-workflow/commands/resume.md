---
description: Resume an interrupted workflow. If spec is confirmed, auto-runs remaining agents without stopping. If spec is pending, continues discovery.
argument-hint: "[optional: 'skip <agent>', 'restart <agent>', or 'manual' to pause between agents]"
---

# /hody-workflow:resume

Resume an interrupted feature workflow from where it left off.

## User Instructions

$ARGUMENTS

If the section above contains text, apply it as guidance for this resume:
- "skip <agent>" → mark that agent as skipped in state.json before computing next
- "restart <agent>" → clear that agent's checkpoint and start fresh
- "continue from <agent>" → jump directly to that agent instead of the default next
- "manual" → pause between each agent for user confirmation (override auto-execution)
- "focus on <area>" → pass this as additional context to the next agent

If empty, resume normally: auto-execute if spec is confirmed, or continue discovery if not.

## Steps

Before resuming, check tracker for additional context about this workflow and related items:

```bash
python3 ${PLUGIN_ROOT}/skills/project-profile/scripts/tracker.py context --cwd .
```

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
Spec: [✅ Confirmed | ⚠️ Pending — discovery incomplete]
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

4. **Check for agent checkpoints**: Check if there are saved checkpoints from interrupted agents:

```bash
python3 ${PLUGIN_ROOT}/skills/project-profile/scripts/tracker.py checkpoint-list --workflow-id <workflow_id> --cwd .
```

If a checkpoint exists for the next agent, display it:

```
📌 Checkpoint found for [agent name]:
   Progress: [completed_items]/[total_items] items done
   Last updated: [updated_at]
   Resume from: [resume_hint]
```

5. **Branch based on spec status**:

### If `spec_confirmed` is `false` or missing → Continue Discovery

The spec was not finalized before the session was interrupted. Continue the discovery process:

- Read any partial spec or notes from KB
- Re-read the feature description and type from state.json
- Resume asking clarifying questions from where discovery left off
- Once spec is confirmed, save it and proceed to auto-execution (same as start-feature Phase C)

### If `spec_confirmed` is `true` → Auto-Execute Remaining Agents

The spec is confirmed — run all remaining agents without stopping.

a. **Read the spec**: Read `.hody/knowledge/<spec_file>` to load the confirmed spec.

b. **Identify remaining agents**: Find all agents that are not in `completed` or `skipped`.

c. **Auto-run agents**: For each remaining agent in sequence:
   - Set it as `active` in state.json, add `agent_log` entry
   - If checkpoint exists for this agent, pass checkpoint data to the agent so it can resume from where it left off (include `partial_output`, `resume_hint`, and completed/pending items)
   - If no checkpoint, start the agent fresh
   - Activate the agent (it reads profile.yaml + KB + spec file)
   - When agent completes, update state.json
   - Show one-line status:
     ```
     ✅ backend completed — "Implemented 5 API endpoints" → Starting unit-tester...
     ```
   - **Immediately** proceed to next agent — do NOT pause to ask the user

   **Exception**: If user passed `manual` in arguments, pause between each agent and ask to continue.

d. **Complete workflow**: After all agents finish, set workflow status to `completed` and show the final summary.

### If all agents already completed

Inform the user and offer to complete the workflow:

```
All agents have completed their work.
Would you like to:
  1. Complete this workflow
  2. Re-run a specific agent
  3. Start a new feature with /hody-workflow:start-feature
```

## Output

### Final Summary (after all agents complete)
```
Workflow Complete
━━━━━━━━━━━━━━━━

Feature: [description]
Spec: .hody/knowledge/[spec_file]

Agent Results:
  ✅ researcher  — [summary]
  ✅ architect   — [summary]
  ✅ backend     — [summary]
  ✅ unit-tester — [summary]
  ✅ code-reviewer — [summary]

KB Files Updated:
  → architecture.md
  → api-contracts.md
  → decisions.md
```

## Notes

- This command is the counterpart to `/hody-workflow:start-feature` — start begins, resume continues
- **Key behavior**: If spec is confirmed, resume auto-executes all remaining agents. If spec is pending, resume continues the interactive discovery process.
- Workflow state persists in `.hody/state.json` across sessions
- The knowledge base files modified by previous agents are available to the next agent automatically
- **Checkpoints**: When an agent is interrupted (context limit, disconnect, etc.), its checkpoint in `tracker.db` preserves exactly what work was done. On resume, the agent receives the checkpoint data so it can skip already-completed items and continue from `resume_hint`.
- Use `manual` argument to override auto-execution and pause between agents
