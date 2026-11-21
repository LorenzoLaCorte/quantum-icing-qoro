# Project notes for Claude

## Divi (qoro-divi) docs

This project uses Qoro's Divi SDK (`qoro-divi`, pinned in the notebooks). Don't answer Divi API questions from memory — the API changes between versions.

- Use the **Context7 MCP server** (configured in `.mcp.json`) with library ID `/qoroquantum/divi`:
  call `query-docs` directly with that ID (no need for `resolve-library-id`) and one focused question per call (e.g. "QAOA on a QUBO", "MonteCarloOptimizer params", "PartitioningProgramEnsemble").
- Web fallback: https://context7.com/qoroquantum/divi (append `/llms.txt?topic=<topic>` for plain text).
