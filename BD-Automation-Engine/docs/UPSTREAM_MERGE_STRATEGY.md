# Upstream Merge Strategy for BD-Automation-Engine

This document outlines the strategy for merging upstream Auto Claude updates while preserving the BD-Automation-Engine customizations.

## Current Status

**Successfully Cherry-Picked (7 commits):**

| Commit | Description | Impact |
|--------|-------------|--------|
| f004a9c3 | Documentation updates | README, CONTRIBUTING.md, .gitignore - no code impact |
| 7adf881e | Windows fixes | pywin32 DLL fixes, UTF-8 encoding - critical for Windows |
| f8b27d8a | Auth/Security fixes | Profile manager, CodeQL - improved security |
| 959b0643 | Backend improvements | PYTHONPATH isolation, ultrathink (63999) - API compatibility |
| 548e3c1b | CI: PAT_TOKEN fix | Release workflow bypass branch protection |
| 91e5ecb3 | CI: yq manifest merging | macOS release builds |
| 34510b44 | CI: symlink handling | npm workspace compatibility |

**Your BD-Automation-Engine components are SAFE:**
- `BD-Automation-Engine/` folder - untouched
- `dashboard/` folder - untouched
- All SQLite databases - untouched
- All JSON data files - untouched
- All custom scripts - untouched

---

## Remaining Commits - Conflict Analysis

The following commits have conflicts that require manual resolution:

### 1. Terminal/UI Improvements (RECOMMENDED - Medium Effort)

**Commits:**
- `b2d2d7e9` - Terminal rename fix (only rename once)
- `dd2b8cfd` - Integration settings UI refactor
- `40fa1dc0` - v2.7.5 reauth warning modal
- `169df79f` - Multi-profile usage display

**What It Changes:**
- Settings UI components in `apps/frontend/src/renderer/components/settings/`
- Terminal store in `apps/frontend/src/renderer/stores/`
- i18n translation files
- Settings types

**Why It Conflicts:**
Our branch has older versions of these files. The upstream has refactored the settings structure.

**Your Data Safe?** YES - These are pure UI changes, no database or script impact.

**Resolution Strategy:**
```bash
# Option A: Accept upstream for these specific files
git checkout upstream/develop -- apps/frontend/src/renderer/components/settings/DevToolsSettings.tsx
git checkout upstream/develop -- apps/frontend/src/renderer/stores/terminal-store.ts

# Option B: Full merge of develop branch (more comprehensive but higher risk)
git merge upstream/develop
# Resolve conflicts, keeping BD-Automation-Engine/ intact
```

---

### 2. Kanban/Task Management (NOT RECOMMENDED - High Effort)

**Commits:**
- `5c5c4d38` - Task card improvements
- `2a8e1f29` - Kanban board refactor
- Various task-related UI fixes

**What It Changes:**
- Complete Kanban board rewrite
- Task store structure changes
- Multiple interconnected UI components

**Why It Conflicts:**
Massive structural changes to the task/Kanban system that touch 20+ files.

**Your Data Safe?** YES - But the merge is complex and error-prone.

**Resolution Strategy:**
Skip these for now. Your Kanban functionality works - upstream changes are mostly cosmetic.

---

### 3. GitHub PR Review Enhancements (OPTIONAL - Medium Effort)

**Commits:**
- `76a3e8f1` - PR review UI improvements
- `8d4c2e91` - Review comment threading
- `3f2a7b8c` - PR diff viewer enhancements

**What It Changes:**
- GitHub PR review components
- Review store and API calls
- Diff viewer rendering

**Why It Conflicts:**
Our branch has an older PR review implementation.

**Your Data Safe?** YES - GitHub integration is separate from BD-Automation-Engine.

**Resolution Strategy:**
Only merge if you actively use the GitHub PR review feature.

---

### 4. Major Feature Additions (DO NOT MERGE - Very High Effort)

**Commits affecting core architecture:**
- Model selector refactoring
- Spec runner rewrites
- Agent system changes

**Why Not To Merge:**
These fundamentally change how Auto Claude operates and would require extensive testing.

---

## Recommended Approach

### Phase 1: Current State (DONE)
You now have the most critical fixes:
- Windows compatibility
- Security improvements
- Backend API compatibility (ultrathink 63999)
- CI/CD workflow fixes

### Phase 2: Optional UI Updates
If you want the newer UI:

```bash
# Create a test branch first
git checkout -b test/upstream-ui

# Cherry-pick specific UI components one at a time
git cherry-pick --no-commit <commit>

# If conflicts are too complex, abort
git cherry-pick --abort

# If successful, commit
git add -A && git commit -m "feat: add upstream UI improvement"
```

### Phase 3: Full Sync (Future)
When you're ready for a complete sync:

1. **Backup your work:**
   ```bash
   git checkout -b backup/bd-engine-$(date +%Y%m%d)
   ```

2. **Create merge branch:**
   ```bash
   git checkout -b merge/upstream-full
   git merge upstream/develop
   ```

3. **Resolve conflicts systematically:**
   - Keep ALL files in `BD-Automation-Engine/`
   - Keep ALL files in `dashboard/`
   - Accept upstream for `apps/frontend/src/` (mostly)
   - Accept upstream for `apps/backend/` (mostly)
   - Review conflicts in shared config files carefully

4. **Test thoroughly before merging to main branch**

---

## Files That Must NEVER Be Overwritten

| Path | Reason |
|------|--------|
| `BD-Automation-Engine/*` | Your entire BD engine |
| `dashboard/*` | Your custom dashboard |
| `Engine7_BullhornETL/*` | Bullhorn ETL pipeline |
| `*.db` files | SQLite databases |
| `.env` | Your API keys and config |
| `outputs/*` | Generated data files |

---

## Commands Reference

```bash
# Check what's different
git diff upstream/develop -- apps/frontend/

# Check a specific file's history
git log --oneline upstream/develop -- path/to/file

# Preview a cherry-pick without committing
git cherry-pick --no-commit <sha>
git diff --cached  # See what would change
git reset HEAD     # Abort without committing

# Safely merge specific directories only
git checkout upstream/develop -- .github/  # Just CI files
git checkout upstream/develop -- apps/backend/prompts/  # Just prompts
```

---

## Summary

| Category | Status | Risk | Recommendation |
|----------|--------|------|----------------|
| Docs/CI/Windows/Backend | DONE | Low | Already merged |
| Terminal/UI | Skipped | Medium | Optional, test first |
| Kanban | Skipped | High | Not worth the effort |
| GitHub PR | Skipped | Medium | Only if you use it |
| Core Architecture | Skipped | Very High | Avoid |

Your BD-Automation-Engine is fully protected. All cherry-picked changes only affect the core Auto Claude UI/backend, not your custom engines, databases, or dashboard.
