---
description: Show project health dashboard with KB completeness, tech debt, workflow stats, and recommendations.
---

# /hody-workflow:health

Show a comprehensive project health dashboard.

## Steps

1. **Check initialization**: Verify `.hody/` directory exists. If not, suggest running `/hody-workflow:init` first.

2. **Gather metrics**: Collect data from all sources:
   - Read `.hody/knowledge/` files → KB completeness
   - Parse `tech-debt.md` → tech debt count and priorities
   - Read `.hody/state.json` → workflow statistics
   - Read `.hody/profile.yaml` → dependency health (if deep analysis was run)

3. **Display dashboard**: Show formatted health report:

   ```
   Project Health -- {project name}
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   Knowledge Base:  ████████░░ 80% complete (5/6 files populated)
   Tech Debt:       3 open items (1 high, 2 medium) -- oldest: 14 days
   Dependencies:    2 outdated, 0 vulnerabilities
   Workflows:       5 started, 4 completed (80% completion rate)
   Agent Usage:     code-reviewer (12x), backend (8x), unit-tester (7x)
                    Warning: spec-verifier never used

   Recommendations:
     -> Address high-priority tech debt item: "Migrate auth library"
     -> Try spec-verifier agent to validate implementation
     -> Run /hody-workflow:refresh --deep to check dependencies
   ```

4. **Actionable suggestions**: Based on the data, recommend specific next steps.

## Notes

- This command is read-only — it does not modify any files
- It reads `.hody/profile.yaml`, `.hody/knowledge/`, and `.hody/state.json`
- Useful as a quick health check when starting a new session or before a release
