# Collaboration Workflow Guide

## 🎯 Setup Overview

**West Side:** Claude AI (connected to GitHub repo)  
**East Side:** Cursor AI/Auto (working on local codebase)  
**Repository:** `git@github.com:imnuman/trading-tool.git`  
**Branch:** `main` (primary development branch)

---

## 🔄 How We Collaborate

### Workflow Pattern

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│  West Side  │ ────>   │   GitHub     │  <────  │  East Side  │
│  (Claude)   │  Push   │   (Remote)    │  Pull   │  (Cursor)   │
└─────────────┘         └──────────────┘         └─────────────┘
     │                         │                         │
     │                         │                         │
     └─────────────────────────┴─────────────────────────┘
                    (Always sync to GitHub)
```

### Key Principle: **GitHub as Single Source of Truth**

- **ALL changes** go through GitHub
- **BOTH sides** pull before starting work
- **BOTH sides** push when work is complete
- **NEVER** work directly on same files simultaneously

---

## 📋 Standard Workflow

### Step 1: **Before Starting Work (BOTH SIDES)**

```bash
# Always pull latest changes first
cd /home/numan/trading-tool
git pull origin main
```

**Why:** Ensures you have the latest code from the other side.

### Step 2: **During Work**

- Work on your assigned files/modules
- Test your changes locally
- Commit with clear messages

### Step 3: **After Completing Work**

```bash
# Check what changed
git status

# Stage changes
git add <files>

# Commit with descriptive message
git commit -m "Clear description of what was changed"

# Push to GitHub
git push origin main
```

### Step 4: **Notify Other Side**

- Leave notes in commit messages
- Update STATUS.md if needed
- Document breaking changes

---

## 🤝 Collaboration Best Practices

### 1. **Communication via Commits**

Use clear commit messages to communicate:

```bash
# Good commit message
git commit -m "West: Fixed economic calendar API integration
- Replaced mock data with Investing.com API
- Added error handling for API failures
- Updated risk manager to use new calendar"

# Another good example
git commit -m "East: Enhanced regime detection
- Improved ADX calculation accuracy
- Added support for volatile market regime
- Updated compatibility matrix"
```

### 2. **File Ownership Strategy**

**West Side (Claude) Focus:**
- API integrations (economic calendar, data sources)
- External service connections
- Production deployment scripts
- Advanced ML/RL implementations

**East Side (Cursor) Focus:**
- Core trading logic
- Backtesting engine
- Strategy generation
- Telegram bot interface
- Documentation

**Shared:**
- Main entry points (`main.py`)
- Configuration files
- Database schema
- Critical bug fixes (coordinate first!)

### 3. **Avoiding Conflicts**

**DO:**
- ✅ Pull before starting work
- ✅ Work on different files when possible
- ✅ Communicate via commit messages
- ✅ Break large changes into smaller commits
- ✅ Test before pushing

**DON'T:**
- ❌ Work on same file simultaneously
- ❌ Force push to main
- ❌ Commit without testing
- ❌ Skip pulling before work
- ❌ Push broken code

### 4. **Handling Conflicts (If They Occur)**

If you get merge conflicts:

```bash
# When git pull shows conflicts
git pull origin main

# If conflicts occur:
# 1. Open conflicted file(s)
# 2. Look for conflict markers: <<<<<<< HEAD
# 3. Choose which version to keep (or merge both)
# 4. Remove conflict markers
# 5. Stage and commit

git add <resolved-file>
git commit -m "Resolved merge conflict in <file>"
git push origin main
```

---

## 🔍 Keeping Repo Up-to-Date

### **Daily Workflow**

#### **Morning Check (Both Sides):**
```bash
git pull origin main
git log --oneline -5  # See what changed
```

#### **Before Major Work:**
```bash
git pull origin main
git status  # Check current state
```

#### **After Work Session:**
```bash
git add -A
git commit -m "Description of changes"
git push origin main
```

### **Automatic Sync Script**

Create a helper script:

```bash
#!/bin/bash
# sync_repo.sh - Keep repo in sync

cd /home/numan/trading-tool

echo "🔄 Syncing repository..."

# Pull latest changes
git pull origin main

# Show recent commits
echo ""
echo "📝 Recent commits:"
git log --oneline -5

# Show current status
echo ""
echo "📊 Current status:"
git status --short
```

**Usage:**
```bash
chmod +x scripts/sync_repo.sh
./scripts/sync_repo.sh
```

---

## 📝 Communication Protocol

### **When Starting Work on Shared File:**

1. Check if file is being worked on:
   ```bash
   git log --oneline --follow <file> | head -3
   ```

2. If recently changed, wait or coordinate

3. Leave a note in commit message:
   ```
   "Working on <file> - expect changes in next commit"
   ```

### **When Completing Work:**

1. Commit with clear message
2. Push immediately
3. Update relevant docs if needed

### **When Fixing Bugs:**

1. Create a quick fix
2. Test thoroughly
3. Commit with "FIX:" prefix
4. Push immediately
5. Notify: "Bug fixed in <file>"

---

## 🎯 Coordination Examples

### **Example 1: West Side Adding Feature**

**West Side:**
```bash
git pull origin main  # Get latest
# ... work on economic calendar API ...
git add src/data/economic_calendar.py
git commit -m "West: Integrate real economic calendar API
- Replaced mock data with Investing.com API
- Added authentication and rate limiting
- Enhanced event detection accuracy"
git push origin main
```

**East Side (Next Session):**
```bash
git pull origin main  # Get West's changes
# Now economic_calendar.py has real API!
# Can test with real data
```

### **Example 2: East Side Fixing Bug**

**East Side:**
```bash
git pull origin main
# ... fix stop loss calculation ...
git add src/strategies/strategy_generator.py
git commit -m "FIX: Stop loss calculation in strategy generator
- Fixed pip calculation for EURUSD
- Adjusted stop loss from 1% to 0.15%
- Affects all strategy types"
git push origin main
```

**West Side (Next Session):**
```bash
git pull origin main  # Get East's fix
# Now stop losses are correct!
```

### **Example 3: Both Sides Working on Different Files**

**West Side:**
- Working on: `src/data/economic_calendar.py` (API integration)
- No conflict with East

**East Side:**
- Working on: `src/ai/ensemble.py` (signal generation)
- No conflict with West

✅ **Safe to work in parallel!**

---

## 🔐 Conflict Prevention Strategy

### **File-Level Separation:**

| File | Primary Owner | Secondary |
|------|--------------|-----------|
| `src/data/economic_calendar.py` | West (API) | East (logic) |
| `src/data/data_fetcher.py` | East | West (enhancements) |
| `src/strategies/*` | East | West (optimization) |
| `src/ai/ensemble.py` | East | West (ML enhancements) |
| `src/telegram/bot.py` | East | West (features) |
| `scripts/pre_deploy.py` | East | West (optimization) |
| `main.py` | Shared | Coordinate changes |
| `requirements.txt` | Shared | Coordinate changes |

### **Module-Level Separation:**

- **West Side:** External integrations, APIs, deployment
- **East Side:** Core trading logic, algorithms, UI

---

## 🚨 Emergency Protocols

### **If Code is Broken:**

1. **Don't panic!**
2. Check recent commits:
   ```bash
   git log --oneline -10
   ```
3. Revert if needed:
   ```bash
   git revert <commit-hash>
   git push origin main
   ```
4. Communicate via commit message:
   ```
   "REVERT: Reverting commit <hash> - caused <issue>"
   ```

### **If Merge Conflict:**

1. **Don't force push!**
2. Pull and resolve:
   ```bash
   git pull origin main
   # Resolve conflicts manually
   git add <resolved-files>
   git commit -m "Resolved merge conflict"
   git push origin main
   ```

---

## 📊 Status Tracking

### **Daily Sync Check:**

Run this to see what's new:
```bash
# See commits from last 24 hours
git log --since="24 hours ago" --oneline

# See what files changed
git diff HEAD~5 HEAD --name-only
```

### **Weekly Review:**

```bash
# See all commits this week
git log --since="1 week ago" --oneline

# See contributors (both sides show as same user)
git shortlog -sn
```

---

## ✅ Quick Reference

### **Start of Day:**
```bash
git pull origin main
git status
```

### **During Work:**
- Work on assigned files
- Test changes
- Commit frequently

### **End of Session:**
```bash
git add -A
git commit -m "Clear description"
git push origin main
```

### **Before Major Changes:**
```bash
git pull origin main
# Check what others changed
git log --oneline -5
```

---

## 🎓 Best Practices Summary

1. **Always pull before work** → `git pull origin main`
2. **Commit often** → Small, frequent commits
3. **Clear messages** → Describe what and why
4. **Test before push** → Don't break the build
5. **Communicate via commits** → Let commit messages speak
6. **Respect file ownership** → Check before modifying
7. **Push when done** → Share your work immediately
8. **Pull when starting** → Get latest changes

---

## 🔗 Useful Commands

```bash
# See what changed
git log --oneline -10

# See who changed what
git blame <file>

# See file history
git log --follow -- <file>

# Undo last commit (keep changes)
git reset --soft HEAD~1

# See what's different from remote
git fetch
git diff main origin/main

# Sync everything
git pull origin main && git push origin main
```

---

## 📞 Coordination Signals

In commit messages, use prefixes:
- `West:` - Changes from West side
- `East:` - Changes from East side  
- `FIX:` - Bug fixes (urgent)
- `FEAT:` - New features
- `DOC:` - Documentation only
- `REFACTOR:` - Code restructuring
- `TEST:` - Test additions/updates

Example:
```
West: FEAT - Added real-time data streaming API
East: FIX - Corrected stop loss calculation
West: DOC - Updated deployment guide
```

---

This workflow keeps both sides in sync and prevents conflicts! 🚀

