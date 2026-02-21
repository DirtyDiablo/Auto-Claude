# WRAITH Heartbeat

## Periodic Checks

### On Session Start
1. Read `.openclaw/SOUL.md` for identity and context
2. Check `orchestrator.py` pipeline state: `outputs/pipeline_state.json`
3. Verify Engine 8 Knowledge API availability: `http://localhost:8100/health`
4. Check git branch is `claude/setup-auto-claude-IrK21`

### On Task Assignment
1. Identify which council member(s) should activate
2. Load relevant ClawhHub skills from `skills/` directory
3. Assess complexity: direct execution vs. sub-agent orchestration
4. Check for existing checkpoint: `outputs/pipeline_checkpoint.json`

### On Completion
1. Validate output through code review
2. Update memory if new patterns discovered
3. Run tests if code was modified: `pytest tests/ -v`
4. Commit with conventional format: `feat:`, `fix:`, `docs:`, `chore:`

## Health Indicators

| Check | Command | Expected |
|---|---|---|
| Knowledge API | `curl http://localhost:8100/health` | 200 OK |
| Qdrant collections | `curl http://localhost:8100/collections` | 8 collections |
| Git branch | `git branch --show-current` | `claude/setup-auto-claude-IrK21` |
| Python env | `python --version` | >= 3.9 |
| Dependencies | `pip check` | No conflicts |

## Memory Updates

After significant work sessions, update:
- `memory/MEMORY.md` — Key patterns and decisions
- `memory/debugging.md` — Solutions to recurring problems (if exists)
- `memory/patterns.md` — Confirmed architectural patterns (if exists)
