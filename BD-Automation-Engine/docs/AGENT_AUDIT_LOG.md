# Agent Audit Log

All agent, subagent, workflow, and skill executions should be logged here using the standard format below.

---

## Log Format Template

```
## [YYYY-MM-DD HH:MM] [AGENT_TYPE] [STATUS: success|partial|failed]
- **Triggered by:** [user | automated | chained from <parent>]
- **Task summary:** [1-line description of what was requested]
- **Files modified:** [list or "none"]
- **Files created:** [list or "none"]
- **Files deleted:** [list or "none"]
- **Key findings:** [2-3 bullet summary of outcomes]
- **Memory updated:** [yes/no — if yes, what was added]
- **Docs refreshed:** [list of docs updated, or "none"]
- **Data stores changed:** [Qdrant collections, Neo4j nodes, Redis keys, or "none"]
- **Next recommended action:** [follow-up suggestion or "none"]
```

---

## Log Entries

<!-- Append new entries below this line, newest first -->
