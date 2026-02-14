# Runbook

## Development Setup

```bash
# Clone the repo
git clone git@github.com:hodynguyen/Claude_Workflow.git
cd Claude_Workflow

# No install step — no dependencies needed for development
# PyYAML is only needed at runtime in target projects
```

## Running Tests

```bash
# Run all 47 unit tests
python3 -m unittest test.test_detect_stack -v

# Tests use temp directories simulating various project types
# (React, Go, Python, Rust, Java, C#, Ruby, PHP, monorepo)
```

## Local Plugin Testing

```bash
# Install plugin locally for testing
claude
/plugin marketplace add hodynguyen/Claude_Workflow
/plugin install hody-workflow@hody
# Restart Claude Code after install

# Test in any project
cd ~/projects/some-project
claude
/hody-workflow:init
```

## Release Process

1. Code and test locally
2. Bump version in `plugins/hody-workflow/.claude-plugin/plugin.json`
3. Commit with conventional format: `<type>: <description>`
4. Push to `main` branch
5. Users update via `/plugin marketplace update` + `/plugin update hody-workflow@hody`

## Pre-push Checklist

- [ ] Version bumped in `plugin.json` (for non-README changes)
- [ ] Tests pass: `python3 -m unittest test.test_detect_stack -v`
- [ ] Commit message follows format: `<type>: <description>`
- [ ] No sensitive files committed (`.env`, credentials, `settings.local.json`)

## Common Issues

| Issue | Fix |
|-------|-----|
| Plugin not loading after install | Restart Claude Code |
| Plugin showing old version | Run `/plugin marketplace update` then `/plugin update hody-workflow@hody` |
| `/hody-workflow:init` not found | Check plugin installed: `/plugin list` |
| Cache corrupted | Delete cache: `rm -rf ~/.claude/plugins/cache/hody/hody-workflow/` then reinstall |
| `detect_stack.py` fails | Ensure Python 3.8+ available, check PyYAML installed in target project |
