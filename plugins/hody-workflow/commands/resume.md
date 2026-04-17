---
description: Resume an interrupted workflow. Respects persisted execution mode (auto/guided/manual). Override with 'auto', 'manual', or 'guided'.
argument-hint: "[optional: 'auto', 'manual', 'guided', 'skip <agent>', 'restart <agent>']"
---

# /hody-workflow:resume

Resume an interrupted feature workflow from where it left off.

## User Instructions

$ARGUMENTS

If the section above contains text, apply it as guidance for this resume:
- "auto" → override execution mode to `auto` (update state.json, auto-run all remaining agents)
- "manual" → override execution mode to `manual` (update state.json, pause between agents)
- "guided" → override execution mode to `guided` (update state.json, auto-run after spec confirmed)
- "skip <agent>" → mark that agent as skipped in state.json before computing next
- "restart <agent>" → clear that agent's checkpoint and start fresh
- "continue from <agent>" → jump directly to that agent instead of the default next
- "focus on <area>" → pass this as additional context to the next agent

If empty, resume normally using the execution mode persisted in state.json (default: `guided`).

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
Mode: [auto | guided | manual]
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

### If `spec_confirmed` is `true` → Execute Remaining Agents

The spec is confirmed — run remaining agents based on execution mode.

a. **Apply mode override**: If the user passed a mode argument (`auto`, `manual`, `guided`), update `execution_mode` in state.json. Otherwise, use the persisted mode (default: `guided`).

b. **Read the spec and log**: Read `.hody/knowledge/<spec_file>` for the confirmed spec and `.hody/knowledge/<log_file>` for work already done by previous agents.

c. **Identify remaining agents**: Find all agents that are not in `completed` or `skipped`.

d. **Run agents based on execution mode**: For each remaining agent in sequence:
   - Set it as `active` in state.json, add `agent_log` entry
   - If checkpoint exists for this agent, pass checkpoint data to the agent so it can resume from where it left off (include `partial_output`, `resume_hint`, and completed/pending items)
   - If no checkpoint, start the agent fresh
   - Activate the agent (it reads profile.yaml + KB + spec file)
   - When agent completes, update state.json
   - Show one-line status:
     ```
     ✅ backend completed — "Implemented 5 API endpoints" → Starting unit-tester...
     ```

   **Mode-specific behavior after each agent:**
   - **`auto` or `guided`**: **Immediately** proceed to next agent — do NOT pause.
   - **`manual`**: Pause and show a review prompt. Wait for user to respond with `continue`, `skip`, or `abort`.

e. **Complete workflow**: After all agents finish, set workflow status to `completed` and show the final summary.

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
Log:  .hody/knowledge/[log_file]

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
- **Key behavior**: Respects the `execution_mode` persisted in state.json. Override with `auto`, `guided`, or `manual` argument.
- If spec is confirmed → execute remaining agents per mode. If spec is pending → continue discovery.
- Workflow state (including execution mode) persists in `.hody/state.json` across sessions
- The knowledge base files modified by previous agents are available to the next agent automatically
- **Checkpoints**: When an agent is interrupted (context limit, disconnect, etc.), its checkpoint in `tracker.db` preserves exactly what work was done. On resume, the agent receives the checkpoint data so it can skip already-completed items and continue from `resume_hint`.
- Mode override updates state.json, so subsequent resumes will use the new mode
