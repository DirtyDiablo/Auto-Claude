# Agentic Engineering Playbook
## A Portable Framework for Agent-First Software Development

> Based on Peter Steinberger's 15 Agentic Engineering Principles (Lex Fridman #491), battle-tested on a 23-phase federal BD intelligence platform (Python/FastAPI/React/Supabase monorepo).

---

## Table of Contents

1. [The 15 Principles](#the-15-principles)
2. [Codebase Architecture for Agents](#codebase-architecture-for-agents)
3. [The File System: What to Create](#the-file-system-what-to-create)
4. [Agent Navigation Design](#agent-navigation-design)
5. [Prompting Methodology](#prompting-methodology)
6. [Multi-Agent Workflow](#multi-agent-workflow)
7. [Post-Build Reflection System](#post-build-reflection-system)
8. [Code Review with Agents](#code-review-with-agents)
9. [The Agent Toolkit (Makefile + CLI)](#the-agent-toolkit)
10. [Skills & Superpowers System](#skills--superpowers-system)
11. [Git Workflow](#git-workflow)
12. [Anti-Patterns to Avoid](#anti-patterns-to-avoid)
13. [Applying to a New Project (Checklist)](#applying-to-a-new-project)

---

## The 15 Principles

| # | Principle | What It Means in Practice |
|---|-----------|--------------------------|
| 1 | **Empathize with your agent** | They start from nothing every session. Guide them. |
| 2 | **Guide, don't dictate** | Provide context, let agent find solutions |
| 3 | **Accept imperfection** | Like managing a team — code won't be exactly yours |
| 4 | **Short prompts > long prompts** | Once you have skill, brevity wins |
| 5 | **Voice input is legitimate** | Speak your prompts — speed matters |
| 6 | **Conversational workflow** | Discuss first, build second |
| 7 | **Post-build reflection** | Always ask "what would you change?" |
| 8 | **Multiple agents in parallel** | Different tasks, different terminals |
| 9 | **Never revert, always forward** | Agents can fix issues faster than reverting |
| 10 | **Design for agent navigation** | Not human aesthetics — agent discoverability |
| 11 | **Don't over-automate** | Keep the human creative touch |
| 12 | **Play constantly** | Skill compounds with practice |
| 13 | **Read agent questions** | They reveal knowledge gaps in your codebase |
| 14 | **Refactor cheaply** | Agents make refactoring fast — do it after every feature |
| 15 | **Keep it fun** | "Hard to compete against someone who's just there to have fun" |

---

## Codebase Architecture for Agents

### The Core Insight

> "Consider how the agent sees your codebase. They start a new session and know nothing about your project. You gotta help those agents a little bit."

Your codebase should be **agent-navigation-first**. An agent starting a fresh session should orient itself in under 30 seconds. This means:

1. **One bootstrap file** (CLAUDE.md) that tells the agent everything it needs to start
2. **Layered documentation** — quick-scan at top, deep dives linked below
3. **Self-documenting tooling** — `make help` shows all commands
4. **Self-diagnostic capability** — `make diagnose` catches config issues
5. **Consistent patterns** — same structure everywhere so agents build intuition

### Don't Fight the Agent's Naming

> "Don't fight the name they pick, because it's most likely in the weights. Next time they search, they'll look for that name."

Design your codebase so agents can do their best work, not so it reads perfectly to you. If the agent picks a name that's in the training weights, keep it — future agents will find it faster.

---

## The File System: What to Create

Every project should have these files, adapted to your stack:

### `CLAUDE.md` — The Session Bootstrap (MOST IMPORTANT)

This is the single file an agent reads to orient. It should contain:

```markdown
# [Project Name]

## Mission
[1-2 sentences: what this project does and why]

## You Are Here
- **Project:** [name]
- **Stack:** [languages, frameworks, databases]
- **State:** [current phase/status]
- **Commands:** `make help` for all targets, `make diagnose` for health
- **Philosophy:** `SOUL.md`
- **Reading order:** `docs/INDEX.md`

## Agent Self-Orientation
Starting a fresh session? Here's how to orient:
1. This file (CLAUDE.md) = session bootstrap
2. `SOUL.md` = project philosophy and constraints
3. `docs/INDEX.md` = reading order for deeper understanding
4. Each module/lib has a README.md with quick reference
5. `make help` = all available CLI commands
6. `make diagnose` = system health check
7. When stuck: read the source code — the answers are there
8. After building: ask "what would I refactor?" and "do we have enough tests?"

## Self-Debugging Protocol
When something fails:
1. Read the error message and the source file it references
2. Check docs/operations/DEBUGGING.md for known issues
3. Run `make diagnose` for system health
4. If DB-related: check connection config
5. If test failure: run tests with verbose/short output
6. If import error: check your test/import configuration

## Architecture
[Directory tree showing project structure — keep it scannable]

## Key Conventions
[Bulleted list of patterns agents MUST follow:
 - naming conventions
 - where models live
 - how database access works
 - import patterns
 - etc.]

## Development
[How to install, lint, test, run the project — copy-paste commands]

## Post-Build Checklist (After Every Feature)
After completing any feature, bug fix, or refactor:
1. "Now that you built it, what would you have done differently?"
2. "What can we refactor?" — identify pain points from building
3. "Do we have enough tests?" — find untested corner cases
4. "Write documentation — what file name, where does it fit?"
5. Run `make refactor-audit` to check tech debt count
6. Add discovered issues to docs/REFACTOR-BACKLOG.md
7. Run `make test` to verify nothing broke
```

**Guidelines:**
- Keep it under 400 lines — agents need to scan it fast
- Front-load the most critical info (mission, architecture, conventions)
- Every section should answer: "What does an agent need to know RIGHT NOW?"
- Update it every time you add major features or change patterns

### `SOUL.md` — Project Identity & Philosophy

Not personality roleplay — **project identity and engineering philosophy**:

```markdown
# [Project Name] — Soul

## Identity
[What this project IS, at its core. 2-3 sentences.]

## Philosophy
- [Core engineering principles — 5-10 bullets]
- Always move forward — never revert, fix instead
- Refactor after every feature — keep the codebase navigable
- Agents are first-class citizens — design for their navigation
- Fun matters — this project should be enjoyable to work on

## Constraints
- [Hard technical limits — database, platform, language version]
- [Architectural decisions that can't be changed easily]

## If You're an Agent Reading This
- You start each session fresh. That's okay.
- Read CLAUDE.md for conventions, this file for philosophy.
- Run `make help` to see what you can do.
- When stuck, read the source code — the answers are usually there.
- After building, ask yourself: "What would I refactor?"
- Your work will be reviewed. Write code you'd be proud of.
```

### `.cursorrules` — Agent Navigation Hints

Works with Cursor, Claude Code, and other agent-aware editors:

```markdown
# [Project Name] — Agent Navigation

## Reading Order
1. CLAUDE.md — Session bootstrap (conventions, models, patterns, commands)
2. SOUL.md — Project philosophy and constraints
3. docs/INDEX.md — Deep-dive reading order
4. [module]/README.md — Quick reference per module

## Available Commands
- `make help` — List all Makefile targets
- `make diagnose` — Check system health
- `make test` — Run all tests
- `make lint` — Run linter
- `make search q="pattern"` — Search codebase

## Key Conventions
[3-5 most important rules agents must follow]

## Self-Debugging
[Condensed version of the debugging protocol]

## Post-Build Reflection
[The 5-step checklist]
```

### `docs/INDEX.md` — Documentation Reading Order

```markdown
# Documentation Index

## Start Here
| Document | Audience | Description |
|----------|----------|-------------|
| CLAUDE.md | AI Agents | Session bootstrap — read FIRST |
| ARCHITECTURE.md | Everyone | System architecture diagrams |
| Getting Started | New Devs | Setup and quick start |

## Architecture
[Links to C4 diagrams, ADRs, etc.]

## Component Deep Dives
[Links to per-module documentation]

## Operations
[Runbook, debugging guide, production audit]

## For AI Agents — Reading Order
1. CLAUDE.md — conventions and patterns
2. ARCHITECTURE.md — visual overview
3. ADRs — why decisions were made (prevents re-litigation)
4. Relevant component doc — deep dive for your current task
5. Debugging guide — known gotchas
```

### `docs/REFACTOR-BACKLOG.md` — Living Tech Debt Tracker

```markdown
# Refactoring Backlog
Auto-maintained by post-build reflection. Items discovered during development.

## Priority: High
| Area | Issue | Discovered | Context |
|------|-------|-----------|---------|

## Priority: Medium
| Area | Issue | Discovered | Context |
|------|-------|-----------|---------|

## Priority: Low
| Area | Issue | Discovered | Context |
|------|-------|-----------|---------|

## Completed
| Area | Issue | Resolved | How |
|------|-------|---------|-----|
```

### Module-Level `README.md` Files

Every library, service, or major module gets a 10-15 line README:

```markdown
# [module-name]
[One-line description of what this module does.]

## Quick Reference
- [Key file]: [what it contains]
- [Key file]: [what it contains]
- Deep dive: [link to detailed doc]

## Testing
[How to run tests for this module specifically]
```

---

## Agent Navigation Design

### The 30-Second Orientation Test

An agent should be able to answer these questions within 30 seconds of starting:

1. What does this project do?
2. What's the tech stack?
3. Where do I find the code for X?
4. What commands can I run?
5. What patterns must I follow?

If any of these take longer than 30 seconds, your documentation needs work.

### Layered Information Architecture

```
Layer 0: CLAUDE.md          — Everything to start working (< 30s)
Layer 1: SOUL.md            — Why things are the way they are (< 1min)
Layer 2: docs/INDEX.md      — Where to find deep information
Layer 3: Component docs     — Detailed module documentation
Layer 4: Source code         — The ultimate source of truth
```

Agents should rarely need to go past Layer 2 for routine work.

---

## Prompting Methodology

### The Skill Progression Curve (The Agentic Trap)

| Level | Style | Example |
|-------|-------|---------|
| **Beginner** | Short, naive prompts | "Please fix this" |
| **Intermediate (THE TRAP)** | Over-engineered: 8 agents, complex orchestration, library of slash commands | "Execute workflow-7b with sub-agents A,B,C in parallel mode..." |
| **Elite / Zen** | Back to short, conversational | "Hey, look at these files and then do these changes" |

**Key insight:** The middle stage is "the agentic trap." The best practitioners return to simplicity with deep understanding.

### Conversational Prompting

Approach it like a **discussion with a very capable engineer** who sometimes needs help:

| Trigger Phrase | Effect |
|---------------|--------|
| **"Discuss"** | Prevents building, keeps agent in conversation mode |
| **"Give me options"** | Exploratory mode |
| **"Don't write code yet"** | Explicit hold |
| **"Okay, build"** | Green light to execute |
| **"Do you have any questions for me?"** | Surfaces knowledge gaps |
| **"Read more code to answer your own questions"** | Redirects when agent asks questions the codebase can answer |

### The "Read More Code" Technique

When the agent asks questions:
1. Scan the questions quickly
2. If answerable by reading the codebase: **"Read more code to answer your own questions"**
3. Only answer questions the agent truly can't figure out from context
4. The questions themselves reveal where your documentation has gaps

---

## Multi-Agent Workflow

### Running 4-10 Agents Simultaneously

Different agents for different tasks:
- **One** building a larger feature
- **One** exploring an uncertain idea
- **Two-three** fixing bugs
- **Others** writing documentation (always part of feature work)

### Terminal Setup

- Multiple terminals side-by-side
- Each terminal: Agent interface at top + actual terminal at bottom
- Bottom terminal prevents prompting in the wrong project
- Keep it simple — no elaborate orchestration

### Key Rules

- Each agent gets one clear task
- Independent tasks can run in parallel
- Dependent tasks must be sequenced
- When an agent finishes, review its work before starting the next task on that terminal
- Documentation is always part of the feature — not a separate task

---

## Post-Build Reflection System

This is the **most impactful practice** from the Steinberger method. After EVERY feature, bug fix, or refactor:

### The 7-Step Checklist

1. **"Now that you built it, what would you have done differently?"**
   - The agent has context from building — use it
   - Often reveals architectural insights you'd miss

2. **"What can we refactor?"**
   - Agents discover pain points during building
   - They'll identify coupling, duplication, unclear interfaces

3. **"Do we have enough tests?"**
   - Agent identifies untested corner cases
   - Often catches edge cases you didn't think of

4. **"Write documentation — what file name, where does it fit?"**
   - Agent suggests where docs belong in your structure
   - Keeps documentation as a natural part of development

5. **Run `make refactor-audit`** to check tech debt count
   - Grep for TODO/FIXME/HACK/XXX markers
   - Track whether debt is growing or shrinking

6. **Add discovered issues to `docs/REFACTOR-BACKLOG.md`**
   - Living document of improvement opportunities
   - Categorized by priority

7. **Run `make test`** to verify nothing broke

### Why This Works

> "Refactors are cheap now. Even though you might break some other PRs, nothing really matters anymore. Agents will just figure things out."

Agents make refactoring nearly free. But you have to **ask for it** — they won't volunteer improvements unless prompted.

---

## Code Review with Agents

### The 5-Step PR Review Process

1. **"Review this PR"** — Agent produces initial review
2. **"Do you understand the intent of the PR?"** — Not implementation, but the *problem* being solved
3. **"Is this the most optimal way to do it?"** — Agent usually says no
4. **"What would be a better way? Have you looked at [specific parts]?"** — Point agent to relevant code it hasn't seen
5. **"Could we make that even better with a larger refactor?"** — Decision: refactor now or save for later?

### Reviewing Agent-Generated Code

- **Always review database-touching code** — this is where bugs hide
- Don't bother reading Tailwind/CSS alignment — boring, low-risk
- Use a diff viewer for important changes
- Look at the *structure* of changes, not every line

---

## The Agent Toolkit

### Makefile (Every Project Needs This)

A self-documenting Makefile with `## comment` pattern for `make help`:

```makefile
.PHONY: help test test-fast lint format diagnose health search refactor-audit

help:           ## Show all available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-18s %s\n", $$1, $$2}'

test:           ## Run all tests
	[your test command]

test-fast:      ## Run tests excluding integration/slow tests
	[your fast test command]

lint:           ## Run linter
	[your lint command]

format:         ## Run formatter
	[your format command]

diagnose:       ## Check system health (DB, env, services)
	[your diagnostic script]

health:         ## Quick health check (services only)
	@curl -sf http://localhost:PORT/health && echo "service: OK" || echo "service: DOWN"

search:         ## Search codebase (usage: make search q="pattern")
	@rg "$(q)" src/ --glob '!node_modules'

refactor-audit: ## Find TODOs, FIXMEs, and tech debt markers
	@rg "(TODO|FIXME|HACK|XXX)" src/ --glob '!*.md' -c || echo "Clean!"
```

### Why CLIs > MCPs

> "Screw MCPs. Every MCP would be better as a CLI."

| MCPs | CLIs |
|------|------|
| Requires specific syntax in training | Models naturally good at Unix commands |
| Not composable | Composable with pipes, jq, scripts |
| Full blob → context pollution | Agent can filter, only get what it needs |
| Most are poorly made | Standard Unix tooling patterns |

**Exception:** Stateful tools (like Playwright/browser automation) can justify MCPs.

### Self-Diagnostic Script

Every project should have a `diagnose` command that checks:
- Language/runtime version
- Required environment variables are set
- Database/service connectivity
- Migration status (current vs head)
- Service port availability
- Dependency health
- Test count and pass rate

Output should be structured text that agents can parse — not fancy formatting.

---

## Skills & Superpowers System

### What Are Skills?

Skills are on-demand context packages that load domain expertise into an agent session. Instead of polluting the context window permanently, skills are loaded when needed.

### Core Workflow Skills (Use on EVERY Task)

| Skill | When |
|-------|------|
| **concise-planning** | Start every task with a plan |
| **lint-and-validate** | After writing code |
| **verification-before-completion** | Before claiming done |
| **commit** | When committing |

### Domain Skills (Match to Your Stack)

| Domain | Skills to Load |
|--------|---------------|
| Python | python-pro, python-patterns, async-python-patterns |
| Database/SQL | postgres-best-practices, sql-optimization-patterns |
| API Development | fastapi-pro, api-design-principles, api-security |
| Frontend | react-best-practices, tailwind-patterns |
| Testing | python-testing-patterns, test-driven-development |
| AI/LLM | rag-engineer, prompt-engineering, llm-app-patterns |
| Infrastructure | docker-expert, deployment-procedures |
| Architecture | architecture, monorepo-architect |

### Superpowers (Meta-Skills for Process)

| Superpower | When to Use |
|-----------|-------------|
| **brainstorming** | Before any creative work — features, components, modifications |
| **writing-plans** | When you have specs for multi-step work |
| **subagent-driven-development** | Executing plans with independent parallel tasks |
| **systematic-debugging** | Any bug, test failure, or unexpected behavior |
| **test-driven-development** | Before writing implementation code |
| **verification-before-completion** | Before claiming work is done |
| **requesting-code-review** | After completing features |
| **finishing-a-development-branch** | When ready to merge |

### The Skill Invocation Rule

**Before writing ANY code or response:**
1. Analyze the prompt — identify the task domain
2. Select 2-5 relevant skills
3. Invoke them BEFORE generating implementation
4. Follow the skill guidance during implementation

This is non-negotiable. Skills contain domain expertise that directly improves code quality.

---

## Git Workflow

### Steinberger's Approach (Adapted)

- **Never revert** — always move forward. Ask the agent to fix instead of rolling back.
- **Conventional commits** — `feat:`, `fix:`, `refactor:`, `docs:`, `test:`
- **Feature branches** for larger work, but keep them short-lived
- **Local CI** — run tests locally before pushing
- **Main should always be shippable**

### Commit Message Pattern

```
feat: [short description of what changed]

[Optional body explaining WHY, not WHAT]

Co-Authored-By: [Agent] <noreply@anthropic.com>
```

### Branch Strategy Options

| Strategy | Best For |
|----------|---------|
| **Commit to main** | Solo developer, high confidence, good test suite |
| **Feature branches** | Team projects, complex features, needs review |
| **Trunk-based** | Fast iteration, feature flags for incomplete work |

---

## Anti-Patterns to Avoid

### The Agentic Trap
- Building elaborate multi-agent orchestration systems
- Libraries of 18 slash commands
- Custom sub-agent workflows that add complexity without value
- **Fix:** Return to short, conversational prompts

### Context Pollution
- Loading everything into the agent's context permanently
- Giant CLAUDE.md files (> 400 lines)
- MCPs that return full blobs
- **Fix:** Layered docs, on-demand skills, CLI tools that agents filter themselves

### Not Empathizing
- Blaming the agent for poor results when your codebase is disorganized
- Not providing orientation files
- Expecting agents to "just know" your patterns
- **Fix:** CLAUDE.md + SOUL.md + module READMEs + make help

### Never Reflecting
- Shipping features without asking "what would you refactor?"
- Accumulating tech debt without tracking it
- Not asking about test coverage after building
- **Fix:** The 7-step post-build checklist

### Over-Automating
- Trying to remove all human judgment
- Complex orchestrators that miss style, love, and human touch
- **Fix:** Keep the human in the loop. You're the architect, agents are the builders.

---

## Applying to a New Project

### Day 1 Checklist

- [ ] Create `CLAUDE.md` with mission, architecture, conventions, commands
- [ ] Create `SOUL.md` with identity, philosophy, constraints, agent guidance
- [ ] Create `.cursorrules` with navigation hints
- [ ] Create `Makefile` with help, test, lint, format, diagnose, search, refactor-audit
- [ ] Create `docs/INDEX.md` linking all documentation
- [ ] Create `docs/REFACTOR-BACKLOG.md` (empty template)
- [ ] Create a README.md for each major module/lib/service
- [ ] Create a diagnostic script (`scripts/diagnose.py` or equivalent)
- [ ] Verify `make help` shows all commands
- [ ] Verify `make diagnose` runs without errors
- [ ] Run the 30-second orientation test — can you answer the 5 questions?

### Week 1 Habits

- [ ] After every feature: run the 7-step post-build reflection
- [ ] Update REFACTOR-BACKLOG.md with discovered issues
- [ ] When agents ask questions, note which ones reveal doc gaps — fix the docs
- [ ] Use "discuss" before "build" — conversation-first workflow
- [ ] Practice short prompts — resist the urge to over-specify

### Ongoing Practices

- [ ] Keep CLAUDE.md under 400 lines — prune ruthlessly
- [ ] Update module READMEs when they change significantly
- [ ] Review and prioritize the refactoring backlog weekly
- [ ] When stuck, step back: "Where's the mistake in my guidance?"
- [ ] Play constantly — experiment with new patterns and workflows

---

## Quick Reference Card

```
ORIENT:     Read CLAUDE.md → SOUL.md → docs/INDEX.md
COMMANDS:   make help | make diagnose | make test | make search q="..."
REFLECT:    "What would you change?" → "What to refactor?" → "Enough tests?"
REVIEW:     Understand intent → Optimal approach? → Larger refactor?
PROMPT:     Discuss → Options → Build → Reflect
DEBUG:      Error msg → Known issues doc → make diagnose → source code
TRACK:      make refactor-audit → docs/REFACTOR-BACKLOG.md
```

---

*Framework extracted from 23-phase PTS BD Intelligence Platform build (2025-2026).*
*Based on Peter Steinberger's Agentic Engineering Principles (Lex Fridman #491).*
