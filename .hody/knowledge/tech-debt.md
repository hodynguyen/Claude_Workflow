# Tech Debt

> To be filled as tech debt is identified during development.

## detect_stack.py detects "unknown" for plugin projects
- **Priority**: low
- **Area**: scripts
- **Description**: Running `detect_stack.py` on this repo itself returns `type: unknown` because there's no detection rule for Claude Code plugin projects
- **Impact**: Minor — this repo is the plugin source, not a target project. The detector is designed for app projects (React, Go, Python, etc.)
- **Suggested Fix**: Could add a detection rule for `.claude-plugin/plugin.json` → type: claude-code-plugin, but low value since this is an edge case

## No integration tests
- **Priority**: medium
- **Area**: testing
- **Description**: Only unit tests exist (47 tests for detect_stack.py). No integration tests that verify the full init flow (detect → create KB → populate)
- **Impact**: Changes to the init command or KB population logic are not automatically tested
- **Suggested Fix**: Add integration tests that run `/hody-workflow:init` on mock projects and verify the full output
