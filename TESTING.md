# Trading Tool - Testing Guide

**System Status:** Ready for End-to-End Testing
**Last Updated:** 2025-11-02

---

## Quick Start Testing

### Prerequisites
```bash
# 1. Navigate to project directory
cd /home/user/trading-tool

# 2. Install dependencies (if not already installed)
pip3 install -r requirements.txt

# 3. Create Telegram bot token
# Visit @BotFather on Telegram and create a new bot
# Copy the token and create config/secrets.env:
echo "TELEGRAM_BOT_TOKEN=your_token_here" > config/secrets.env
```

---

## Phase 1: Pre-Deployment Testing (Day 0)

### Test 1.1: Data Fetching
```bash
python3 -c "
from src.data.data_fetcher import DataFetcher
df = DataFetcher()
data = df.fetch_all_pairs(period='5y', interval='1d')
print(f'✅ Fetched {len(data)} pairs')
for pair, df in data.items():
    print(f'  {pair}: {len(df)} rows')
"
```

**Expected Output:**
```
✅ Fetched 6 pairs
  USD_EURUSD: ~1250 rows
  GBP_GBPUSD: ~1250 rows
  Gold_XAUUSD: ~1250 rows
  ...
```

### Test 1.2: Component Imports
```bash
python3 -c "
from src.data.data_fetcher import DataFetcher
from src.data.economic_calendar import EconomicCalendar
from src.ai.ensemble import EnsembleSignalGenerator
from src.ai.regime_detector import RegimeDetector
from src.ai.trend_filter import TrendFilter
from src.risk.risk_manager import RiskManager
from src.risk.correlation_manager import CorrelationManager
from src.utils.learning_loop import LearningLoop
from src.ai.rl_selector import RLSelector
print('✅ All critical imports successful!')
"
```

**Expected Output:**
```
✅ All critical imports successful!
```

### Test 1.3: Run Pre-Deployment
```bash
python3 scripts/pre_deploy.py
```

**Expected Behavior:**
- Fetches 5 years of historical data
- Generates 1,000 strategies
- Backtests all strategies on training data
- Filters by performance metrics
- Validates on test data (out-of-sample)
- Stores top strategies in `data/strategies.db`

**Duration:** 5-30 minutes (depending on number of strategies)

**Expected Output (final summary):**
```
============================================================
Pre-Deployment Complete!
============================================================
Data pairs collected: 6
Strategies generated: 1000
Strategies backtested (train): 1000
Strategies filtered (train): 150-300
Strategies validated (test): 100-200
Top validated strategies selected: 100-200

📊 PERFORMANCE METRICS:
  Training Win Rate: 52-58%
  Test (Out-of-Sample) Win Rate: 48-55%
  Performance Decay: 85-95%
  Average Confidence: 60-75%

✅ Ready for Day 1 deployment!
```

---

## Phase 2: Bot Testing (Day 1)

### Test 2.1: Verify Telegram Token
```bash
python3 scripts/verify_token.py
```

**Expected Output:**
```
✅ Token is valid
Bot Name: YourBotName
Username: @YourBotUsername
```

### Test 2.2: Start Bot
```bash
python3 main.py
```

**Expected Output:**
```
2025-11-02 19:30:00 - root - INFO - Starting Trading Tool Telegram Bot...
2025-11-02 19:30:00 - root - INFO - Loading top strategies from database...
2025-11-02 19:30:00 - root - INFO - Loaded 150 strategies from database
2025-11-02 19:30:00 - root - INFO - Ensemble initialized with 50 strategies
2025-11-02 19:30:00 - root - INFO - ✅ Learning loop started in background
2025-11-02 19:30:00 - root - INFO - ✅ Bot initialized and ready!
2025-11-02 19:30:00 - root - INFO - Telegram bot is running. Press Ctrl+C to stop.
```

---

## Phase 3: End-to-End Testing

### Test 3.1: `/start` Command
Open Telegram and message your bot:
```
/start
```

**Expected Response:**
```
🤖 Trading Tool AI Bot

Welcome! I'm your AI-powered trading assistant.

Available Commands:
/signal - Get high-confidence trading signal
/chart <pair> - Get chart analysis (USD, GBP, Gold)
/stats - View performance statistics
/help - Show detailed help

Ready to provide trading signals with ≥80% confidence!
```

### Test 3.2: `/signal` Command
```
/signal
```

**Possible Responses:**

**A) High-Confidence Signal (when all conditions met):**
```
🟢 Trading Signal

Pair: EURUSD
Direction: 📈 BUY
Confidence: 85.3%

Entry Zone: 1.08450 - 1.08550
Stop Loss: 1.08200
Take Profit: 1.08900

Ensemble Agreement: 85.0%
Strategies Used: 42

Risk Checks:
✓ Trend: BULLISH
✓ Timeframes: 3/3
✓ Correlation check passed

⚠️ For human execution only
```

**B) No Trade (most common during testing):**
```
❌ No Trade

Current market conditions do not meet the ≥80% confidence threshold.
Possible reasons:
• Strategies didn't reach consensus
• Market regime not suitable
• Timeframes not aligned
• Low confidence from ensemble
```

**C) Risk Filter Block:**
```
❌ No Trade - Risk Filter

Signal filtered by risk management:
⚠️ High-impact news at 12:30 UTC

Recommendation: Wait until conditions improve.
```

### Test 3.3: `/chart` Command
```
/chart USD
```

**Expected Response:**
```
📊 Chart Analysis: USD

Current Price: 1.08562
Trend: Bullish 📈

Support Level: 1.07800
Resistance Level: 1.09200
Volatility: 0.85%

Recent Range: 1.07800 - 1.09200

Last Updated: 2025-11-02 19:30:00
```

### Test 3.4: `/stats` Command
```
/stats
```

**Expected Response:**
```
📊 Performance Statistics

Ensemble Performance:
• Average Win Rate: 54.2%
• Average Sharpe Ratio: 0.65
• Average Confidence: 68.5%

Top Strategies:

1. EMA_Crossover_1h_v42
   • Confidence: 72.3%
   • Win Rate: 58.1%
   • Sharpe: 0.82

2. RSI_Reversal_4h_v17
   • Confidence: 70.8%
   • Win Rate: 56.4%
   • Sharpe: 0.75

[... more strategies ...]
```

### Test 3.5: `/help` Command
```
/help
```

**Expected Response:**
```
📖 Trading Tool Bot Help

Commands:

/signal
Get a high-confidence trading signal or "no trade" message.
Signals require ≥80% ensemble agreement and high confidence.

/chart <pair>
Get live/historical chart analysis for a trading pair.
Available pairs: USD, GBP, Gold
Example: /chart USD

/stats
View ensemble performance statistics including:
• Win rates
• Sharpe ratios
• Top performing strategies

/help
Show this help message

About Signals:
Signals include:
• Entry zone
• Stop loss level
• Take profit level
• Confidence score
• Strategies used

⚠️ All trades are for human execution only.
```

---

## Phase 4: Filter Testing

### Test 4.1: Economic Calendar Filter
```bash
# Simulate testing during news time
python3 -c "
from src.data.economic_calendar import EconomicCalendar
cal = EconomicCalendar(buffer_minutes=30)
allowed, reason = cal.is_trading_allowed()
print(f'Trading allowed: {allowed}')
if not allowed:
    print(f'Reason: {reason}')
"
```

### Test 4.2: Regime Detection
```bash
python3 -c "
from src.data.data_fetcher import DataFetcher
from src.ai.regime_detector import RegimeDetector

df = DataFetcher()
data = df.load_data('USD_EURUSD', period='60d', interval='1h')
detector = RegimeDetector()
regime, confidence = detector.detect_regime(data)
print(f'Market Regime: {regime}')
print(f'Confidence: {confidence:.2f}')
"
```

**Expected Output:**
```
Market Regime: Trending Up
Confidence: 0.78
```

### Test 4.3: Trend Filter
```bash
python3 -c "
from src.data.data_fetcher import DataFetcher
from src.ai.trend_filter import TrendFilter

df = DataFetcher()
data_1h = df.load_data('USD_EURUSD', period='60d', interval='1h')
trend_filter = TrendFilter()
trend, alignment = trend_filter.analyze_multi_timeframe_trend(data_1h)
print(f'Trend: {trend}')
print(f'Alignment: {alignment}')
"
```

**Expected Output:**
```
Trend: bullish
Alignment: 3/3 aligned
```

---

## Troubleshooting

### Issue 1: "No strategies found in database"
**Cause:** Pre-deployment hasn't been run
**Solution:**
```bash
python3 scripts/pre_deploy.py
```

### Issue 2: "TELEGRAM_BOT_TOKEN not found"
**Cause:** Missing or incorrect secrets.env file
**Solution:**
```bash
# Create token file
cat > config/secrets.env << EOF
TELEGRAM_BOT_TOKEN=your_actual_token_here
EOF
```

### Issue 3: "No data available"
**Cause:** Data fetching failed or network issue
**Solution:**
```bash
# Test data fetching
python3 -c "
from src.data.data_fetcher import DataFetcher
df = DataFetcher()
df.clear_cache()  # Clear cache
data = df.load_data('USD_EURUSD')
print('Success!' if data is not None else 'Failed')
"
```

### Issue 4: Always getting "No Trade"
**Cause:** This is expected! The system is conservative
**Explanation:**
- ≥80% ensemble agreement is strict
- Regime filters remove incompatible strategies
- Trend filters require alignment
- Risk filters block unsafe conditions
- News calendar blocks during high-impact events

**Normal behavior:** 60-80% of signal requests return "No Trade"

### Issue 5: Import errors
**Cause:** Missing dependencies
**Solution:**
```bash
pip3 install -r requirements.txt
```

---

## Performance Benchmarks

### Pre-Deployment Speed
- 1,000 strategies: 5-10 minutes
- 10,000 strategies: 30-60 minutes
- 50,000 strategies: 2-4 hours

### Signal Generation Speed
- < 2 seconds (with all filters enabled)

### Memory Usage
- Bot idle: ~150-300 MB
- Pre-deployment: ~500 MB - 1 GB

---

## Success Criteria

✅ **System is working correctly if:**
- All imports succeed
- Pre-deployment completes without errors
- Bot starts and responds to commands
- `/signal` returns either a signal or "No Trade" (both are valid)
- Filters properly block unsafe trades
- Learning loop runs without crashes

❌ **System needs attention if:**
- Import errors occur
- Bot crashes on command
- Database errors appear
- Data fetching consistently fails

---

## Next Steps After Testing

1. ✅ All tests pass
2. Set up Telegram bot with @BotFather
3. Run pre_deploy.py with larger strategy count (10k-50k)
4. Monitor bot for 24-48 hours
5. Track signal quality and win rates
6. Adjust confidence thresholds if needed
7. Consider deploying to cloud server

---

## Monitoring Commands

```bash
# Check database size
ls -lh data/strategies.db

# Count strategies in database
sqlite3 data/strategies.db "SELECT COUNT(*) FROM strategies;"

# View top strategies
sqlite3 data/strategies.db "SELECT name, confidence_score, win_rate FROM backtest_results ORDER BY confidence_score DESC LIMIT 10;"

# Clear cache
python3 -c "from src.data.data_fetcher import DataFetcher; DataFetcher().clear_cache()"
```

---

**Happy Testing!** 🚀
