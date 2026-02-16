---
description: Start a guided feature development workflow. Analyzes the feature type and recommends an agent sequence through THINK, BUILD, VERIFY, and SHIP phases.
---

# /hody-workflow:start-feature

Start a guided, multi-phase feature development workflow.

## Steps

1. **Check initialization**: Verify `.hody/profile.yaml` exists. If not, run `/hody-workflow:init` first.

2. **Gather feature description**: Ask the user to describe the feature they want to build. Ask clarifying questions if the description is vague.

3. **Classify feature type**: Based on the description, classify into one of these types:

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

4. **Recommend agent workflow**: Map the feature type to an agent sequence:

| Type | Agent Sequence |
|------|---------------|
| `new-feature` | researcher → architect → frontend + backend → unit-tester → integration-tester → code-reviewer → spec-verifier → devops |
| `bug-fix` | architect → frontend or backend → unit-tester → code-reviewer |
| `refactor` | code-reviewer (assess) → frontend or backend → unit-tester → code-reviewer (verify) |
| `api-endpoint` | architect → backend → integration-tester → code-reviewer |
| `ui-change` | frontend → unit-tester → code-reviewer |
| `tech-spike` | researcher → architect |
| `deployment` | devops |
| `hotfix` | frontend or backend → unit-tester → devops |

5. **Present the plan**: Show the user the recommended workflow with phases:

```
Feature: [user's description]
Type: [classified type]

Recommended workflow:
  THINK:  [agents]
  BUILD:  [agents]
  VERIFY: [agents]
  SHIP:   [agents]
```

6. **Ask for confirmation**: Let the user adjust the plan (skip agents, reorder, etc.)

7. **Create workflow state**: After the user confirms the plan, create `.hody/state.json` to persist the workflow. The file should have this structure:

```json
{
  "workflow_id": "feat-<slugified-description>-<YYYYMMDD>",
  "feature": "<user's feature description>",
  "type": "<classified type>",
  "status": "in_progress",
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

Only include phases that have agents assigned. This enables `/hody-workflow:resume` to pick up where the user left off.

8. **Start first phase**: Activate the first agent in the sequence. When starting an agent, set it as `active` in its phase and add an entry to `agent_log` with `started_at`. After each agent completes, update `state.json`: add the agent to `completed`, record `completed_at`, `output_summary`, and `kb_files_modified` in the log. Then prompt the user to continue to the next agent or adjust.

## Output

After presenting the plan:
- Show which agents will be used and in what order
- Indicate which phases are optional (e.g., SHIP phase for non-deployment features)
- Suggest starting with the first agent

## Notes

- The workflow is a recommendation, not a rigid sequence — users can skip or reorder agents
- Frontend and backend agents can run in parallel during the BUILD phase
- The SHIP phase (devops) is optional for most feature types
- Each agent will read the knowledge base, so context accumulates across phases
- If an agent writes to the knowledge base, subsequent agents benefit automatically
- Workflow state is persisted in `.hody/state.json` — use `/hody-workflow:resume` to continue an interrupted workflow
