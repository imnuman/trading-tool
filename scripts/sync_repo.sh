#!/bin/bash
# Repository Sync Helper Script
# Keeps local repo in sync with GitHub

set -e

cd "$(dirname "$0")/.."

echo "🔄 Syncing Trading Tool Repository..."
echo ""

# Check if we're on main branch
current_branch=$(git branch --show-current)
if [ "$current_branch" != "main" ]; then
    echo "⚠️  Warning: Not on main branch (currently on: $current_branch)"
    echo "   Consider switching: git checkout main"
    echo ""
fi

# Show current status
echo "📊 Current Status:"
git status --short
echo ""

# Check if there are uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "⚠️  You have uncommitted changes!"
    echo "   Please commit or stash them before syncing."
    echo ""
    read -p "Do you want to see what changed? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git status
    fi
    exit 1
fi

# Pull latest changes
echo "⬇️  Pulling latest changes from GitHub..."
git pull origin main

# Show recent commits
echo ""
echo "📝 Recent Commits (last 5):"
git log --oneline -5 --decorate

# Show files changed in last pull
echo ""
echo "📁 Files Changed (if any):"
git diff HEAD~1 HEAD --name-only 2>/dev/null || echo "   (No new changes)"

# Show current branch info
echo ""
echo "✅ Repository is up-to-date!"
echo "   Branch: $(git branch --show-current)"
echo "   Latest commit: $(git log -1 --oneline)"

