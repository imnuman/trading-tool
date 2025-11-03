# Pre-Deployment Checklist

Complete checklist of everything needed before deploying to AWS.

---

## ✅ **COMPLETED (Code & Features)**

- [x] Core infrastructure (data fetcher, strategy generator, backtest engine)
- [x] AI features (regime detection, trend filter, multi-timeframe)
- [x] Risk management (news calendar, correlation manager)
- [x] Telegram bot interface
- [x] OANDA API integration
- [x] AWS deployment guide
- [x] Train/test split (prevents overfitting)
- [x] Learning loop framework

---

## 🔶 **CONFIGURATION (Must Complete Before Deploy)**

### 1. **OANDA API Credentials** ⚠️ REQUIRED

**Status:** ❓ Not configured yet

**Action:**
1. Create OANDA Practice Account: https://www.oanda.com/us-en/trade/open-an-account/
2. Generate API token from Settings → API
3. Get Account ID from platform (top-right corner)
4. Update `config/secrets.env`:
   ```bash
   OANDA_API_KEY=your_actual_token_here
   OANDA_ACCOUNT_ID=your_account_id_here
   OANDA_ENVIRONMENT=practice
   ```
5. Test: `python3 scripts/test_oanda_connection.py`

**Time:** ~10 minutes  
**Cost:** FREE (Practice Account)

---

### 2. **Telegram Bot Token** ⚠️ REQUIRED

**Status:** ✅ Likely configured (you mentioned bot is working)

**Verify:**
```bash
# Check if token is set
grep TELEGRAM_BOT_TOKEN config/secrets.env

# Test bot (if running locally)
python3 main.py
```

**If not configured:**
1. Message @BotFather on Telegram
2. Use `/newbot` command
3. Copy token
4. Add to `config/secrets.env`:
   ```bash
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   ```

---

### 3. **Run Pre-Deployment Script** ⚠️ REQUIRED

**Status:** ❓ Not run yet

**Action:**
```bash
# Activate venv
source venv/bin/activate

# Run pre-deployment (generates strategies)
python3 scripts/pre_deploy.py
```

**What it does:**
- Fetches historical data (from OANDA or yfinance)
- Generates 1,000+ strategies
- Backtests on training data (80% of data)
- Validates on test data (20% of data)
- Filters strategies (keeps only high performers)
- Saves to `data/strategies.db`

**Time:** 10-30 minutes  
**Expected output:**
- ✅ Strategies generated: 1000
- ✅ Strategies backtested (train): 1000
- ✅ Strategies validated (test): 100-300
- ✅ Top validated strategies selected: 100-200

**⚠️ IMPORTANT:** Must complete before deploying bot!

---

## 🧪 **TESTING (Do Locally First)**

### 4. **Local Testing** ⚠️ RECOMMENDED

**Test 1: Import Verification**
```bash
python3 -c "
from src.data.data_fetcher import DataFetcher
from src.ai.ensemble import EnsembleSignalGenerator
from src.risk.risk_manager import RiskManager
print('✅ All imports successful')
"
```

**Test 2: OANDA Connection**
```bash
python3 scripts/test_oanda_connection.py
```

**Expected:** ✅ All tests passed!

**Test 3: Database Verification**
```bash
python3 -c "
from src.utils.database import StrategyDatabase
db = StrategyDatabase()
strategies = db.get_top_strategies(min_confidence=50.0, min_trades=1, limit=10)
print(f'✅ Found {len(strategies)} strategies in database')
"
```

**Expected:** ✅ Found X strategies (X > 0)

**Test 4: Bot Startup (Quick Test)**
```bash
# Start bot (will stop on Ctrl+C)
timeout 15 python3 main.py || true
```

**Expected:**
- ✅ Loads strategies from database
- ✅ Initializes ensemble
- ✅ Connects to Telegram
- ✅ Bot starts polling

---

## 📊 **DATA VERIFICATION**

### 5. **Verify Data Files** ⚠️ CHECK

**Check if data exists:**
```bash
ls -lh data/*.db
ls -lh data/cache/
```

**Expected:**
- `data/strategies.db` exists (after pre_deploy.py)
- Cache files may exist (historical data)

**If missing:**
- Run `python3 scripts/pre_deploy.py` again

---

## 🔐 **SECURITY CHECK**

### 6. **Secrets File** ⚠️ VERIFY

**Check `config/secrets.env`:**
```bash
# Verify file exists and has correct permissions
ls -l config/secrets.env

# Should show: -rw------- (readable by owner only)
chmod 600 config/secrets.env
```

**Verify contents (don't show in logs!):**
```bash
# Check format (not actual values)
grep -E "^(TELEGRAM_BOT_TOKEN|OANDA_API_KEY|OANDA_ACCOUNT_ID)=" config/secrets.env

# Should NOT contain: optional, your_token_here, etc.
# Should contain: actual tokens/IDs
```

**Make sure:**
- ✅ File is not committed to git (check `.gitignore`)
- ✅ Contains real credentials (not placeholders)
- ✅ Has correct permissions (600)

---

## 📁 **FILE VERIFICATION**

### 7. **Required Files** ✅ CHECK

**Verify all critical files exist:**
```bash
# Core files
test -f main.py && echo "✅ main.py"
test -f requirements.txt && echo "✅ requirements.txt"
test -f config/secrets.env && echo "✅ config/secrets.env"
test -f scripts/pre_deploy.py && echo "✅ pre_deploy.py"

# Data directory
test -d data && echo "✅ data/ directory"
test -d src && echo "✅ src/ directory"
```

---

## 🚀 **DEPLOYMENT PREPARATION**

### 8. **Git Status** ✅ CHECK

**Ensure code is committed:**
```bash
git status

# Should show: "nothing to commit, working tree clean"
# If not, commit changes:
git add -A
git commit -m "Final changes before deployment"
git push origin main
```

---

### 9. **Dependencies** ✅ VERIFY

**Check if all dependencies are in requirements.txt:**
```bash
# Verify key dependencies
grep -E "(pandas|numpy|python-telegram-bot|yfinance|requests)" requirements.txt

# Install locally to test
pip install -r requirements.txt
```

---

### 10. **AWS Account Setup** ⚠️ READY

**Status:** ✅ You mentioned you have AWS account

**Before deploying:**
- [ ] AWS account active
- [ ] AWS credentials ready (or will use IAM roles)
- [ ] Decided on instance type (EC2 t2.micro or Lightsail $3.50)
- [ ] Have SSH key pair ready (for EC2/Lightsail)

**Optional but recommended:**
- [ ] Set up AWS billing alerts
- [ ] Enable CloudWatch (optional monitoring)

---

## 📝 **PRE-DEPLOYMENT TESTING SUMMARY**

**Run this complete test:**

```bash
#!/bin/bash
# complete_pre_deployment_test.sh

echo "🧪 Running Pre-Deployment Tests..."

# Test 1: Imports
echo "1. Testing imports..."
python3 -c "
from src.data.data_fetcher import DataFetcher
from src.ai.ensemble import EnsembleSignalGenerator
print('✅ Imports OK')
" || exit 1

# Test 2: OANDA (if configured)
echo "2. Testing OANDA connection..."
if grep -q "OANDA_API_KEY" config/secrets.env && ! grep -q "optional\|your_token" config/secrets.env; then
    python3 scripts/test_oanda_connection.py || echo "⚠️  OANDA test failed (may need credentials)"
else
    echo "⚠️  OANDA not configured (optional)"
fi

# Test 3: Database
echo "3. Testing database..."
python3 -c "
from src.utils.database import StrategyDatabase
db = StrategyDatabase()
strategies = db.get_top_strategies(min_confidence=50.0, min_trades=1, limit=1)
if len(strategies) > 0:
    print(f'✅ Database OK ({len(strategies)}+ strategies)')
else:
    print('⚠️  No strategies in database - run pre_deploy.py')
    exit(1)
" || exit 1

# Test 4: Secrets
echo "4. Checking secrets..."
if [ ! -f config/secrets.env ]; then
    echo "❌ config/secrets.env not found!"
    exit 1
fi

if grep -q "your_token\|optional\|your_" config/secrets.env; then
    echo "⚠️  Secrets may contain placeholder values"
else
    echo "✅ Secrets file OK"
fi

# Test 5: Git
echo "5. Checking git status..."
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  Uncommitted changes detected"
else
    echo "✅ Git clean"
fi

echo ""
echo "✅ Pre-deployment tests complete!"
echo ""
echo "Next steps:"
echo "1. ✅ Run: python3 scripts/pre_deploy.py (if not done)"
echo "2. ✅ Verify OANDA credentials (if using)"
echo "3. ✅ Follow AWS_DEPLOYMENT.md to deploy"
```

---

## 🎯 **DEPLOYMENT READINESS SCORECARD**

### Must Have (Blockers):
- [ ] ✅ OANDA credentials configured (or skip if using yfinance only)
- [ ] ✅ Telegram bot token configured
- [ ] ✅ Pre-deployment script run successfully
- [ ] ✅ Strategies in database (`data/strategies.db` exists)
- [ ] ✅ Local testing passed (bot starts, imports work)
- [ ] ✅ Git code pushed to GitHub

### Should Have (Recommended):
- [ ] ✅ OANDA connection tested
- [ ] ✅ Database verified (has strategies)
- [ ] ✅ Secrets file permissions correct (600)
- [ ] ✅ All dependencies installed locally

### Nice to Have (Optional):
- [ ] ✅ AWS credentials ready
- [ ] ✅ Monitoring setup planned
- [ ] ✅ Backup strategy planned

---

## ⚡ **QUICK DEPLOYMENT READINESS CHECK**

**Run this command to see what's missing:**

```bash
echo "📋 Deployment Readiness:"
echo ""

# Check secrets
if [ -f config/secrets.env ]; then
    if grep -q "your_token\|optional" config/secrets.env; then
        echo "❌ Secrets: Contains placeholders"
    else
        echo "✅ Secrets: Configured"
    fi
else
    echo "❌ Secrets: File missing"
fi

# Check database
if [ -f data/strategies.db ]; then
    count=$(python3 -c "from src.utils.database import StrategyDatabase; db=StrategyDatabase(); print(len(db.get_top_strategies(min_confidence=50, min_trades=1, limit=100)))" 2>/dev/null || echo "0")
    if [ "$count" -gt 0 ]; then
        echo "✅ Database: Has $count strategies"
    else
        echo "❌ Database: Empty or error"
    fi
else
    echo "❌ Database: Not found (run pre_deploy.py)"
fi

# Check git
if [ -z "$(git status --porcelain)" ]; then
    echo "✅ Git: Clean"
else
    echo "⚠️  Git: Uncommitted changes"
fi

echo ""
echo "📝 Next: Run 'python3 scripts/pre_deploy.py' if database is missing"
```

---

## 🚨 **COMMON ISSUES & FIXES**

### Issue: "No strategies in database"
**Fix:** Run `python3 scripts/pre_deploy.py`

### Issue: "OANDA connection failed"
**Fix:** 
1. Check credentials in `config/secrets.env`
2. Verify API token is correct (very long string)
3. Verify Account ID format (e.g., `101-004-1234567-001`)
4. Run `python3 scripts/test_oanda_connection.py` for details

### Issue: "Telegram bot token invalid"
**Fix:**
1. Get token from @BotFather
2. Update `config/secrets.env`
3. Test: `python3 -c "from telegram import Bot; Bot('your_token').get_me()"`

### Issue: "Import errors"
**Fix:**
```bash
source venv/bin/activate
pip install -r requirements.txt --upgrade
```

---

## ✅ **FINAL CHECKLIST BEFORE AWS DEPLOYMENT**

Before you start AWS deployment, confirm:

- [ ] ✅ `python3 scripts/pre_deploy.py` completed successfully
- [ ] ✅ `data/strategies.db` exists and has strategies
- [ ] ✅ `config/secrets.env` has real credentials (not placeholders)
- [ ] ✅ Bot tested locally (starts without errors)
- [ ] ✅ Code pushed to GitHub
- [ ] ✅ OANDA connection tested (if using OANDA)
- [ ] ✅ All imports work locally

**Once all checked, you're ready for AWS deployment!**

Follow `AWS_DEPLOYMENT.md` for deployment steps.

---

## 📊 **ESTIMATED TIME**

- **OANDA Setup:** ~10 minutes
- **Pre-Deployment Script:** 10-30 minutes
- **Local Testing:** 5-10 minutes
- **AWS Deployment:** 20-30 minutes

**Total:** ~45-80 minutes to go from zero to deployed

---

**Status:** Ready to check items off! ✅

