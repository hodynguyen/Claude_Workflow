---
description: Start a guided feature development workflow. Analyzes the feature type and recommends an agent sequence through THINK, BUILD, VERIFY, and SHIP phases.
---

# /hody:start-feature

Start a guided, multi-phase feature development workflow.

## Steps

1. **Check initialization**: Verify `.hody/profile.yaml` exists. If not, run `/hody:init` first.

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

7. **Start first phase**: Activate the first agent in the sequence. After each agent completes, prompt the user to continue to the next agent or adjust.

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
