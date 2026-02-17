---
description: Re-detect project tech stack and update .hody/profile.yaml. Use when dependencies or project structure have changed.
---

# /hody-workflow:refresh

Re-detect the project tech stack and update the existing profile.

## Steps

1. **Re-detect tech stack**: Run the project-profile skill to re-scan the project and regenerate `.hody/profile.yaml`

```bash
python3 ${PLUGIN_ROOT}/skills/project-profile/scripts/detect_stack.py --cwd .
```

If the user requests deep analysis (e.g., "refresh --deep", "deep analysis", "check dependencies"), add the `--deep` flag:

```bash
python3 ${PLUGIN_ROOT}/skills/project-profile/scripts/detect_stack.py --cwd . --deep
```

The `--deep` flag runs actual package manager commands (`npm ls`, `npm audit`, `pip list`, `go list`, `cargo metadata`) to get:
- Dependency counts (direct + transitive)
- Outdated packages with breaking change detection
- Security vulnerabilities

This is slower than the default regex-only detection but provides much richer data.

2. **Show diff**: Compare the new profile with the previous one and highlight what changed

Read the current `.hody/profile.yaml` before running detection, then compare with the new output. Show:
- New technologies detected
- Technologies no longer detected
- Framework or version changes

3. **Show summary**: Display the updated stack

## Output

After running, show the user:
- Updated project type and detected stack
- What changed since last detection (if anything)
- Suggest running `/hody-workflow:status` for a full overview

## Notes

- This command overwrites `.hody/profile.yaml` with fresh detection results
- Knowledge base files are NOT modified — only the profile is updated
- Run this after adding/removing major dependencies, changing frameworks, or restructuring the project
- The profile is also regenerated when running `/hody-workflow:init`
- Use `--deep` for dependency analysis — results are cached in profile.yaml under `deep_analysis`
- Deep analysis requires the relevant package manager CLI to be installed (npm, pip, go, cargo)
