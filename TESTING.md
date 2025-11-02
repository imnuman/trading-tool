# Testing Guide

## Quick Test Checklist

### 1. Test Imports ✅
```bash
cd /home/numan/trading-tool
source venv/bin/activate
python3 -c "
from src.data.data_fetcher import DataFetcher
from src.data.economic_calendar import EconomicCalendar
from src.ai.regime_detector import RegimeDetector
from src.ai.trend_filter import TrendFilter
from src.risk.correlation_manager import CorrelationManager
from src.risk.risk_manager import RiskManager
from src.ai.ensemble import EnsembleSignalGenerator
print('✅ All imports successful')
"
```

### 2. Test Pre-Deployment ✅
```bash
source venv/bin/activate
python3 scripts/pre_deploy.py
```

**Expected output:**
- Fetches data for 7 pairs
- Generates 1000 strategies
- Backtests on training data
- Validates on test data
- Filters and saves top strategies

### 3. Test Main Bot ✅
```bash
source venv/bin/activate
timeout 10 python3 main.py
```

**Expected output:**
- Loads strategies from database
- Initializes ensemble
- Connects to Telegram
- Bot starts polling

### 4. Test Telegram Commands

Once bot is running, test in Telegram:

1. `/start` - Should show welcome message
2. `/signal` - Should either show signal or "No Trade"
3. `/chart USD` - Should show chart analysis
4. `/stats` - Should show performance statistics
5. `/help` - Should show help message

## Common Issues & Fixes

### Issue: "No strategies found in database"
**Fix:** Run `python3 scripts/pre_deploy.py` first

### Issue: Import errors
**Fix:** Make sure virtual environment is activated:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: Economic calendar error
**Fix:** Already fixed - Tuple import added

### Issue: Bot token invalid
**Fix:** Check `config/secrets.env` has valid token from @BotFather

## End-to-End Test Flow

1. **Clean start:**
```bash
rm -rf data/*.db data/*.parquet
python3 scripts/pre_deploy.py
```

2. **Verify database:**
```bash
python3 -c "
from src.utils.database import StrategyDatabase
db = StrategyDatabase()
strategies = db.get_top_strategies(min_confidence=50.0, min_trades=1, limit=10)
print(f'Found {len(strategies)} strategies in database')
"
```

3. **Start bot:**
```bash
python3 main.py
```

4. **Test in Telegram:**
- Send `/signal`
- Check if signal is generated or filtered appropriately

## Performance Validation

After running pre_deploy.py, check:
- Training win rate vs Test win rate (should be within 15%)
- Number of validated strategies (should be > 0)
- If test WR < 85% of train WR, system may be overfit

## Production Readiness Checklist

- [ ] All imports work
- [ ] Pre-deployment completes successfully
- [ ] Bot connects to Telegram
- [ ] `/signal` command works
- [ ] Filters are functioning (regime, trend, news, correlation)
- [ ] Train/test split working (check for overfitting warning)
- [ ] Stop losses are correct (15-30 pips, not 100-300)
- [ ] Pair names are correct (EURUSD, not USD)

