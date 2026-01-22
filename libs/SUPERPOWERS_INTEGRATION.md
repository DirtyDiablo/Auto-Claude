# Superpowers Integration Plan for Auto-Claude

This document outlines how to integrate patterns from the [Superpowers](https://github.com/obra/superpowers) agentic skills framework into Auto-Claude.

## Overview

Superpowers provides composable "skills" that guide AI agents through structured development workflows. Many patterns align closely with Auto-Claude's existing architecture, making integration straightforward.

## Skill-to-Component Mapping

| Superpowers Skill | Auto-Claude Component | Integration Type |
|-------------------|----------------------|------------------|
| `brainstorming` | `spec_agents/gatherer.py` | Enhance prompt |
| `writing-plans` | `agents/planner.py` | Enhance prompt |
| `test-driven-development` | `agents/qa_reviewer.py`, `qa_fixer.py` | New capability |
| `systematic-debugging` | `agents/qa_fixer.py` | Enhance prompt |
| `dispatching-parallel-agents` | `agents/coder.py` | Already exists, refine |
| `subagent-driven-development` | Agent orchestration | Two-stage review pattern |
| `verification-before-completion` | `agents/qa_reviewer.py` | Enhance verification |
| `using-git-worktrees` | `cli/worktree.py` | Add safety checks |

## Priority 1: Immediate Value (High Impact, Low Effort)

### 1.1 Enhanced Verification (verification-before-completion)

**Current:** QA reviewer checks acceptance criteria
**Enhancement:** Add "Evidence before claims" mandate

**File:** `apps/backend/prompts/qa_reviewer.md`

Add section:
```markdown
## Verification Protocol

BEFORE claiming any test passes or requirement is met:

1. IDENTIFY: What command proves this claim?
2. RUN: Execute the command (fresh, complete)
3. READ: Full output, check exit code
4. VERIFY: Does output confirm the claim?

NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE

Never use "should pass", "looks correct", or "seems to work"
Always provide evidence: "[Ran: npm test] [Output: 47/47 pass]"
```

### 1.2 Systematic Debugging (systematic-debugging)

**Current:** QA fixer attempts fixes based on QA report
**Enhancement:** Add four-phase debugging protocol

**File:** `apps/backend/prompts/qa_fixer.md`

Add section:
```markdown
## Debugging Protocol

### Phase 1: Root Cause Investigation (MANDATORY BEFORE ANY FIX)
- Read error messages completely
- Reproduce the issue consistently
- Check recent changes (git diff)
- Trace data flow to find source

### Phase 2: Pattern Analysis
- Find working examples in codebase
- Identify differences between working and broken

### Phase 3: Hypothesis Testing
- Form single hypothesis: "X is the root cause because Y"
- Test with SMALLEST possible change
- One variable at a time

### Phase 4: Implementation
- Create failing test FIRST
- Implement single fix
- Verify fix works

RED FLAG: If 3+ fixes fail, question the architecture. Stop and report.
```

### 1.3 TDD Enforcement (test-driven-development)

**Current:** Tests run after implementation
**Enhancement:** Enforce RED-GREEN-REFACTOR cycle

**File:** `apps/backend/prompts/coder.md`

Add section:
```markdown
## Test-Driven Development

For every feature or fix:

1. **RED**: Write failing test first
   - Run test, confirm it FAILS
   - If test passes immediately, you're testing existing behavior

2. **GREEN**: Write minimal code to pass
   - Only enough to make test pass
   - No extra features

3. **REFACTOR**: Clean up (tests must stay green)

IRON LAW: No production code without a failing test first.
If you write code before the test, delete it and start over.
```

## Priority 2: Workflow Enhancements (Medium Effort)

### 2.1 Two-Stage Review (subagent-driven-development)

**Current:** Single QA review pass
**Enhancement:** Separate spec compliance from code quality

**New pattern for `agent.py` orchestration:**

```python
# After coder completes task:
# Stage 1: Spec Compliance Review
spec_review = run_spec_reviewer(task, implementation)
if not spec_review.compliant:
    run_fixer(spec_review.gaps)  # Fix missing requirements

# Stage 2: Code Quality Review
quality_review = run_quality_reviewer(implementation)
if quality_review.issues:
    run_fixer(quality_review.issues)  # Fix quality issues
```

**New prompts needed:**
- `prompts/spec_reviewer.md` - Checks implementation matches spec exactly
- `prompts/code_quality_reviewer.md` - Checks code quality, patterns, DRY

### 2.2 Enhanced Brainstorming (brainstorming)

**Current:** `spec_gatherer.py` collects requirements
**Enhancement:** Socratic questioning, one question at a time

**File:** `apps/backend/prompts/spec_gatherer.md`

Key additions:
- Ask ONE question per message (not multiple)
- Prefer multiple choice when possible
- Propose 2-3 approaches with trade-offs
- Present designs in 200-300 word sections, validate each

### 2.3 Worktree Safety (using-git-worktrees)

**Current:** `cli/worktree.py` creates worktrees
**Enhancement:** Add safety verification

**File:** `apps/backend/cli/worktree.py`

Add checks:
```python
def verify_worktree_safe(worktree_dir: str) -> bool:
    """Verify worktree directory is gitignored before creation."""
    result = subprocess.run(
        ["git", "check-ignore", "-q", worktree_dir],
        capture_output=True
    )
    return result.returncode == 0

def ensure_worktree_ignored(worktree_dir: str):
    """Add worktree dir to .gitignore if not already ignored."""
    if not verify_worktree_safe(worktree_dir):
        with open(".gitignore", "a") as f:
            f.write(f"\n{worktree_dir}/\n")
        # Commit the .gitignore change
```

## Priority 3: Advanced Patterns (Higher Effort)

### 3.1 Bite-Sized Task Granularity (writing-plans)

**Current:** Planner creates subtasks
**Enhancement:** Each step should be 2-5 minutes of work

Update `prompts/planner.md`:
```markdown
## Task Granularity

Each step is ONE action (2-5 minutes):
- "Write the failing test" - one step
- "Run it to verify it fails" - one step
- "Implement minimal code to pass" - one step
- "Run tests to verify" - one step
- "Commit" - one step

NOT: "Implement authentication with tests and commit"
```

### 3.2 Parallel Agent Dispatch (dispatching-parallel-agents)

**Current:** Coder can spawn subagents
**Enhancement:** Structured parallel dispatch for independent problems

Pattern for `agents/coder.py`:
```python
def handle_multiple_failures(failures: list[TestFailure]):
    """Dispatch parallel agents for independent failures."""

    # Group by independence
    independent_groups = group_by_domain(failures)

    if len(independent_groups) >= 3:
        # Dispatch parallel agents
        agents = []
        for group in independent_groups:
            agent = spawn_subagent(
                scope=f"Fix {group.domain}",
                constraints="Don't change other code",
                expected_output="Summary of root cause and fix"
            )
            agents.append(agent)

        # Wait and integrate
        results = await gather(*agents)
        verify_no_conflicts(results)
```

## Reference Location

Superpowers skills are available at: `libs/superpowers/skills/`

Key skill files to reference:
- `skills/test-driven-development/SKILL.md` - TDD methodology
- `skills/systematic-debugging/SKILL.md` - Debugging protocol
- `skills/verification-before-completion/SKILL.md` - Verification rules
- `skills/subagent-driven-development/SKILL.md` - Two-stage review
- `skills/brainstorming/SKILL.md` - Requirements gathering
- `skills/writing-plans/SKILL.md` - Plan structure

## Implementation Order

1. **Week 1:** Priority 1 items (prompt enhancements)
   - Add verification protocol to qa_reviewer.md
   - Add debugging protocol to qa_fixer.md
   - Add TDD section to coder.md

2. **Week 2:** Priority 2 items (workflow changes)
   - Implement two-stage review in agent orchestration
   - Enhance spec_gatherer.md with brainstorming patterns
   - Add worktree safety checks

3. **Week 3:** Priority 3 items (advanced patterns)
   - Refine task granularity in planner
   - Enhance parallel agent dispatch

## Notes

- Superpowers is NOT an MCP server - it's a Claude Code plugin
- Skills are designed as prompts/instructions, not APIs
- Adapt the patterns to Auto-Claude's Python codebase
- The skill files serve as reference documentation
