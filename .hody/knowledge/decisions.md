# Architecture Decision Records

## ADR-001: Initial Tech Stack
- **Date**: 2025-01-18
- **Status**: accepted
- **Context**: Building a Claude Code plugin for project-aware development workflows. Need languages for scripting, config formats for plugin metadata, and a way to store project profiles.
- **Decision**:
  - Python 3 (stdlib + PyYAML) for all scripts (detect_stack.py, inject_project_context.py)
  - Markdown for agent prompts, commands, skills (Claude Code plugin format)
  - YAML for project profile output (.hody/profile.yaml)
  - JSON for plugin config (plugin.json, hooks.json, marketplace.json)
  - unittest (stdlib) for testing
- **Alternatives**: Could have used Node.js/TypeScript for scripts, but Python is simpler for file parsing and available everywhere. Could have used JSON for profiles, but YAML is more human-readable.
- **Consequences**: No build step needed. Only external dependency is PyYAML. Scripts must work with Python 3.8+.

## ADR-002: Three-Layer Architecture
- **Date**: 2025-01-18
- **Status**: accepted
- **Context**: Agents need to be project-aware without dynamic templating (Claude Code constraint — agent prompts are static Markdown).
- **Decision**: Three layers: (1) Profile — auto-detected stack in YAML, (2) Knowledge Base — accumulative Markdown files, (3) Agents — static prompts that read profile at runtime.
- **Alternatives**: Dynamic prompt templating (not supported by Claude Code), single config file (insufficient for accumulated knowledge).
- **Consequences**: Agents must bootstrap by reading profile.yaml and knowledge files. Knowledge base grows over time across sessions.

## ADR-003: Agent Collaboration via Suggestion
- **Date**: 2025-02-12
- **Status**: accepted
- **Context**: Agents sometimes need to delegate work to other agents (e.g., code-reviewer suggests running unit-tester).
- **Decision**: Agents include a `## Collaboration` section that recommends the user invoke another agent. No auto-invocation — Claude Code doesn't support agent-to-agent calls.
- **Alternatives**: Auto-invoke via tool calls (not supported), chaining via commands (too complex).
- **Consequences**: User must manually follow agent suggestions. Workflow guidance via `/hody-workflow:start-feature` helps orchestrate the right sequence.
