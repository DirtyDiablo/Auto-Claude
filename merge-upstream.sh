#!/usr/bin/env bash
set -euo pipefail

# ========================================
# Customized for your setup:
# - Your branch: claude/setup-auto-claude-IrK21
# - Upstream: upstream/develop (AndyMik90/Auto-Claude)
# ========================================

LOCAL_BRANCH="claude/setup-auto-claude-IrK21"
UPSTREAM_REMOTE="upstream"
UPSTREAM_BRANCH="develop"

TIMESTAMP=$(date +%s)
BACKUP_BRANCH="${LOCAL_BRANCH//\//-}-backup-${TIMESTAMP}"
MERGE_BRANCH="merge-temp-${TIMESTAMP}"
MERGE_TARGET="${UPSTREAM_REMOTE}/${UPSTREAM_BRANCH}"

echo "=============================================="
echo "Merge Upstream Script"
echo "=============================================="
echo "Local branch:  $LOCAL_BRANCH"
echo "Upstream:      $MERGE_TARGET"
echo "=============================================="
echo ""

# Ensure we're in the repo root
cd "$(git rev-parse --show-toplevel)"

# Fetch upstream
echo ">>> Fetching upstream..."
git fetch "$UPSTREAM_REMOTE" "$UPSTREAM_BRANCH"

# Make sure we're on the local branch
git checkout "$LOCAL_BRANCH"

# Create a backup of your branch
echo ""
echo ">>> Creating backup branch: $BACKUP_BRANCH"
git branch "$BACKUP_BRANCH"
echo "    Backup created."

# Create a temp branch from your branch to run the merge
echo ""
echo ">>> Creating temp merge branch: $MERGE_BRANCH"
git checkout -b "$MERGE_BRANCH"

echo ""
echo ">>> Attempting merge: ${MERGE_TARGET} into ${MERGE_BRANCH}"
echo ""

# Try merge but don't auto-commit so we can inspect conflicts
if git merge --no-commit --no-ff "$MERGE_TARGET"; then
    echo ""
    echo "=============================================="
    echo "SUCCESS: Merge completed cleanly!"
    echo "=============================================="
    git commit -m "Merge ${MERGE_TARGET} into ${LOCAL_BRANCH}" || true
    echo ""
    echo "To update your local branch with the merge:"
    echo "  git checkout ${LOCAL_BRANCH}"
    echo "  git merge ${MERGE_BRANCH}"
    echo ""
    echo "To push to your remote:"
    echo "  git push origin ${LOCAL_BRANCH}"
    exit 0
fi

# If we get here, there are conflicts
echo ""
echo "=============================================="
echo "CONFLICTS DETECTED"
echo "=============================================="
echo ""

echo ">>> Listing conflicted files..."
conflict_files=$(git diff --name-only --diff-filter=U)
echo "$conflict_files" | tee conflicts.txt
echo ""
echo "Wrote: conflicts.txt"

echo ""
echo ">>> Getting all upstream commits ahead of your branch..."
git --no-pager log --oneline "${LOCAL_BRANCH}..${MERGE_TARGET}" > upstream_commits.txt
echo "Wrote: upstream_commits.txt ($(wc -l < upstream_commits.txt) commits)"

echo ""
echo ">>> Finding upstream commits that touch the conflicted files..."
> problematic_commits.txt
for f in $conflict_files; do
    echo "" >> problematic_commits.txt
    echo "=== File: $f ===" >> problematic_commits.txt
    git --no-pager log --oneline "${MERGE_TARGET}" -- "$f" | head -10 >> problematic_commits.txt
done

echo "Wrote: problematic_commits.txt"

echo ""
echo "=============================================="
echo "OUTPUT FILES CREATED:"
echo "=============================================="
echo "  conflicts.txt              - Files with merge conflicts"
echo "  upstream_commits.txt       - All 193 upstream commits"
echo "  problematic_commits.txt    - Commits touching conflict files"
echo ""
echo "=============================================="
echo "OPTIONS:"
echo "=============================================="
echo ""
echo "1. ABORT (discard merge, return to original state):"
echo "   git merge --abort"
echo "   git checkout ${LOCAL_BRANCH}"
echo "   git branch -D ${MERGE_BRANCH}"
echo ""
echo "2. RESOLVE CONFLICTS and complete merge:"
echo "   - Open conflicted files and resolve conflicts"
echo "   - git add <resolved-files>"
echo "   - git commit -m 'Merge upstream/develop with conflict resolution'"
echo "   - git checkout ${LOCAL_BRANCH}"
echo "   - git merge ${MERGE_BRANCH}"
echo "   - git push origin ${LOCAL_BRANCH}"
echo ""
echo "3. ACCEPT ALL UPSTREAM CHANGES (loses your local changes):"
echo "   git checkout --theirs ."
echo "   git add ."
echo "   git commit -m 'Merge upstream/develop (accept upstream)'"
echo ""
echo "=============================================="
