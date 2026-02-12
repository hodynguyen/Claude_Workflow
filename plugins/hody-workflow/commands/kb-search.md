---
description: Search the project knowledge base (.hody/knowledge/) for specific topics, keywords, or sections. Use when you need to find information across KB files.
---

# /hody-workflow:kb-search

Search the project's knowledge base for relevant information.

## Steps

1. **Check KB exists**: Verify `.hody/knowledge/` directory exists. If not, suggest running `/hody-workflow:init` first.

2. **Get search query**: Ask the user what they want to search for, or use the query they provided.

3. **Search across all KB files**: Read all `.md` files in `.hody/knowledge/` and search for the query.

Search each file in `.hody/knowledge/`:
- `architecture.md`
- `decisions.md`
- `api-contracts.md`
- `business-rules.md`
- `tech-debt.md`
- `runbook.md`

For each file, find:
- Matching section headers (## headings) that contain the keyword
- Paragraphs or list items containing the keyword
- Return surrounding context (the full section where the match was found)

4. **Present results**: Show results grouped by file, with the matching sections highlighted.

## Output Format

```
## Search results for: "<query>"

### architecture.md
> [matching section with context]

### api-contracts.md
> [matching section with context]

---
Found X matches across Y files.
```

If no matches found:
```
No matches found for "<query>" in the knowledge base.

Available KB files: architecture.md, decisions.md, api-contracts.md, business-rules.md, tech-debt.md, runbook.md
```

## Supported Search Modes

- **Keyword search**: Find all occurrences of a word/phrase across KB files
- **Section listing**: When query is "list" or "sections", show all ## headings from each file
- **File filter**: When query starts with "in:<filename>", search only that file (e.g., "in:architecture API")

## Notes

- Search is case-insensitive
- Returns full sections (from ## heading to next ## heading) for context
- Does not modify any knowledge base files
- Works with any custom .md files added to .hody/knowledge/
