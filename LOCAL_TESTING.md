# Local Testing Guide

Step-by-step guide to test the Trading Tool locally before AWS deployment.

---

## 🧪 **Quick Test Sequence**

### Step 1: Verify Prerequisites ✅

```bash
# Check Python version
python3 --version  # Should be 3.9+

# Check virtual environment
source venv/bin/activate

# Verify dependencies
pip list | grep -E "(pandas|telegram|yfinance|numpy)"
```

---

### Step 2: Test Database & Strategies ✅

```bash
# Check strategies in database
python3 -c "
from src.utils.database import StrategyDatabase
db = StrategyDatabase()
strategies = db.get_top_strategies(min_confidence=50.0, min_trades=1, limit=100)
print(f'✅ Found {len(strategies)} strategies')
if strategies:
    print(f'Top strategy: {strategies[0][\"name\"]}')
    print(f'Confidence: {strategies[0][\"confidence_score\"]:.1f}%')
"
```

**Expected:** Shows strategies count and top strategy details.

---

### Step 3: Test OANDA Connection ✅

```bash
python3 scripts/test_oanda_connection.py
```

**Expected:** 
- ✅ Connection successful
- ✅ Price fetch working
- ✅ Historical data working

---

### Step 4: Test Telegram Connection ✅

```bash
python3 -c "
from telegram import Bot
from dotenv import load_dotenv
import os
import asyncio

load_dotenv('config/secrets.env')
token = os.getenv('TELEGRAM_BOT_TOKEN')
bot = Bot(token)
info = asyncio.run(bot.get_me())
print(f'✅ Bot connected: @{info.username}')
"
```

**Expected:** Shows bot username.

---

### Step 5: Test Ensemble Initialization ✅

```bash
python3 -c "
from src.ai.ensemble import EnsembleSignalGenerator
from src.utils.database import StrategyDatabase
from src.strategies.strategy_generator import Strategy

db = StrategyDatabase()
strategies_data = db.get_top_strategies(min_confidence=50.0, min_trades=1, limit=50)

strategies = []
for s in strategies_data[:10]:  # Test with top 10
    strategies.append(Strategy(
        id=s['id'],
        name=s['name'],
        indicators=s['indicators'],
        timeframe=s['timeframe'],
        session_filter=s['session_filter'],
        entry_conditions=s['entry_conditions'],
        exit_conditions=s['exit_conditions'],
        parameters=s['parameters']
    ))

ensemble = EnsembleSignalGenerator(strategies=strategies, min_agreement=0.80, min_confidence=80.0)
print(f'✅ Ensemble initialized with {len(strategies)} strategies')
"
```

**Expected:** Ensemble creates successfully.

---

### Step 6: Test Data Fetching ✅

```bash
python3 -c "
from src.data.data_fetcher import DataFetcher
import pandas as pd

fetcher = DataFetcher()
print('Testing data fetching...')

# Test OANDA (if configured)
data = fetcher.load_data('USD_EURUSD', period='7d', interval='1h')
if data is not None:
    print(f'✅ Loaded {len(data)} rows from OANDA')
    print(f'Latest price: {data[\"close\"].iloc[-1]:.5f}')
else:
    print('⚠️  OANDA data not available, trying yfinance...')
    data = fetcher.load_data('USD_EURUSD', period='7d', interval='1h')
    if data is not None:
        print(f'✅ Loaded {len(data)} rows from yfinance')
"
```

**Expected:** Data loaded successfully (from OANDA or yfinance).

---

### Step 7: Test Signal Generation (Dry Run) ✅

```bash
python3 -c "
from src.data.data_fetcher import DataFetcher
from src.ai.ensemble import EnsembleSignalGenerator
from src.utils.database import StrategyDatabase
from src.strategies.strategy_generator import Strategy

# Load ensemble
db = StrategyDatabase()
strategies_data = db.get_top_strategies(min_confidence=50.0, min_trades=1, limit=50)
strategies = []
for s in strategies_data[:10]:
    strategies.append(Strategy(
        id=s['id'], name=s['name'], indicators=s['indicators'],
        timeframe=s['timeframe'], session_filter=s['session_filter'],
        entry_conditions=s['entry_conditions'],
        exit_conditions=s['exit_conditions'], parameters=s['parameters']
    ))

ensemble = EnsembleSignalGenerator(strategies=strategies, min_agreement=0.80, min_confidence=80.0)

# Get data
fetcher = DataFetcher()
data = fetcher.load_data('USD_EURUSD', period='30d', interval='1h')

if data is not None and len(data) > 0:
    current_price = float(data['close'].iloc[-1])
    signal = ensemble.generate_signal(data, current_price, 'EURUSD')
    
    if signal:
        print('✅ Signal generated!')
        print(f'Direction: {signal[\"direction\"]}')
        print(f'Confidence: {signal[\"confidence\"]:.1f}%')
        print(f'Agreement: {signal[\"agreement\"]*100:.1f}%')
    else:
        print('⚠️  No signal (normal - requires ≥80% agreement)')
else:
    print('❌ Could not load data')
"
```

**Expected:** Either generates signal or returns "No signal" (both are valid).

---

### Step 8: Start Bot (Interactive Test) 🚀

```bash
# Start the bot (will run until Ctrl+C)
python3 main.py
```

**Expected Output:**
```
INFO - Starting Trading Tool Telegram Bot...
INFO - Loading top strategies from database...
INFO - Loaded X strategies from database
INFO - Ensemble initialized with X strategies
INFO - ✅ Bot initialized and ready!
INFO - 📊 Learning loop will update strategies every 5 minutes
INFO - Telegram bot is running. Press Ctrl+C to stop.
```

**Then test in Telegram:**
1. Open Telegram
2. Find your bot: @trading_47_bot
3. Send `/start` - should show welcome message
4. Send `/signal` - should show signal or "No Trade"
5. Send `/chart USD` - should show chart analysis
6. Send `/stats` - should show performance stats
7. Send `/help` - should show help message

---

### Step 9: Extended Test (Optional) ⏱️

Keep bot running for 10-15 minutes to verify:
- No crashes
- Commands respond correctly
- Learning loop runs without errors

```bash
# In one terminal
python3 main.py

# In another terminal, watch logs
tail -f logs/*.log  # If logging to file
# Or just watch console output
```

---

## 🔍 **Troubleshooting**

### Issue: "No strategies found in database"
**Fix:**
```bash
python3 scripts/pre_deploy.py
```

### Issue: "Telegram bot not responding"
**Check:**
- Token is correct in `config/secrets.env`
- Bot is running (`python3 main.py`)
- Network connection is working
- Bot was started with `/start` in Telegram

### Issue: "OANDA connection failed"
**Check:**
- Credentials in `config/secrets.env`
- Run: `python3 scripts/test_oanda_connection.py`
- Falls back to yfinance if OANDA fails (acceptable)

### Issue: "Always getting 'No Trade'"
**This is normal!** The system is conservative:
- Requires ≥80% ensemble agreement
- Regime filters remove incompatible strategies
- Trend filters require alignment
- News filter blocks during events

**Expected:** 60-80% of requests return "No Trade" - this is correct behavior!

---

## ✅ **Success Criteria**

Your local test is successful if:

- [x] Bot starts without errors
- [x] Connects to Telegram
- [x] `/start` command works
- [x] `/signal` returns either signal or "No Trade" (both valid)
- [x] `/chart` command works
- [x] `/stats` shows statistics
- [x] No crashes for 10+ minutes
- [x] Learning loop runs without errors

---

## 📊 **Expected Behavior**

### Normal "No Trade" Responses:
```
❌ No Trade

Current market conditions do not meet the ≥80% confidence threshold.
Possible reasons:
• Strategies didn't reach consensus
• Market regime not suitable
• Timeframes not aligned
• Low confidence from ensemble
```

This is **expected and correct** - the system is selective!

### When Signal is Generated:
```
🟢 Trading Signal

Pair: EURUSD
Direction: 📈 BUY
Confidence: 85.3%
...
```

Rare but good - means all conditions met!

---

## 🎯 **Next Steps After Local Testing**

Once local tests pass:

1. ✅ Generate more strategies (optional):
   ```bash
   python3 scripts/pre_deploy.py
   ```

2. ✅ Deploy to AWS:
   - Follow `AWS_DEPLOYMENT.md`
   - Use same credentials
   - Bot will work identically

3. ✅ Monitor on AWS:
   - Check logs
   - Test commands
   - Monitor for 24 hours

---

**Ready to start testing? Run Step 8 to start the bot!** 🚀

