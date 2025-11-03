# Trading Tool - Application Overview

**AI-Powered 24/7 Forex Signal Suggestion Bot**

---

## 🎯 Purpose

This is a **signal-suggestion only** trading bot that provides high-confidence BUY/SELL recommendations for forex pairs. It does NOT execute trades automatically - all signals are for human review and manual execution.

---

## 📊 Accuracy & Performance Metrics

### Target Performance
- **Real-World Win Rate Target**: 65-72%
- **Backtest Win Rate Target**: 70-80% (with robust out-of-sample testing)
- **Minimum Confidence Threshold**: 80% (signals below this are not shown)
- **Ensemble Agreement Required**: ≥80% (strategies must agree)

### Current Performance (Based on Backtests)
From the strategy database, top strategies show:
- **Average Win Rate**: ~60-75% (varies by strategy)
- **Average Sharpe Ratio**: 1.2-2.5 (indicates good risk-adjusted returns)
- **Profit Factor**: 1.5-2.8 (shows profitable strategies)
- **Maximum Drawdown**: 15-25% (acceptable risk levels)

### Signal Quality Assurance
Every signal passes through **7 layers of filtering**:
1. **Ensemble Voting** (≥80% agreement among top 50 strategies)
2. **Confidence Threshold** (≥80% minimum)
3. **Regime Detection** (market state compatibility)
4. **Multi-Timeframe Confirmation** (1H + 4H + Daily alignment)
5. **Trend Filter** (trend alignment across timeframes)
6. **News Embargo** (blocks signals during high-impact news)
7. **Correlation Filter** (prevents over-exposure to correlated pairs)

---

## 🏗️ Architecture

### Core Components

#### 1. **Ensemble Signal Generator** (`src/ai/ensemble.py`)
- Manages 50 top-performing strategies
- Voting mechanism requires ≥80% agreement
- Regime-aware strategy filtering
- Multi-timeframe trend confirmation

#### 2. **Strategy Database** (`data/strategies.db`)
- Stores 100+ backtested strategies
- Tracks performance metrics (win rate, Sharpe, drawdown)
- Continuously updated by learning loop

#### 3. **Data Sources**
- **OANDA API** (Real-time forex prices) - **PRIMARY**
- **yfinance** (Historical data fallback)
- Supports: EUR/USD, GBP/USD, USD/JPY, AUD/USD, USD/CHF, XAU/USD

#### 4. **Risk Management** (`src/risk/risk_manager.py`)
- News calendar monitoring (blocks signals during high-impact news)
- Correlation filtering (max 2 correlated pairs simultaneously)
- Position sizing recommendations
- Stop-loss enforcement

#### 5. **Telegram Bot Interface** (`src/telegram/bot.py`)
- User commands for signals, charts, stats
- Automatic signal notifications (when high-confidence signals detected)
- Hourly market status updates
- Beautiful formatted messages with emojis

#### 6. **Continuous Learning Loop** (`src/utils/learning_loop.py`)
- Updates every 5 minutes
- Retrains strategies on new market data
- Prunes underperforming strategies
- Adapts to market regime changes

#### 7. **Drift Detection** (`src/utils/drift_detector.py`)
- Monitors strategy performance degradation
- Triggers alerts when win rate drops >15%
- Statistical tests for distribution changes
- Cooldown mechanism (24h between alerts)

---

## 🚀 Functionality

### Available Commands

#### `/start`
Welcome message and command overview

#### `/signal [pair]`
Get a high-confidence trading signal right now
- Example: `/signal EUR/USD`
- Returns: Direction, entry zone, stop-loss, take-profit, confidence
- Or "No Trade" if conditions not met

#### `/chart <pair>`
Get real-time chart analysis
- Example: `/chart EUR/USD`
- Shows: Current price, trend, support/resistance, volatility

#### `/stats`
View ensemble performance statistics
- Average win rate, Sharpe ratio
- Top 5 performing strategies
- Recent signal accuracy

#### `/status`
Get current market status for all pairs
- Shows which pairs have active signals
- Market regime for each pair
- Real-time prices from OANDA

#### `/help`
Detailed help and usage instructions

### Automatic Features

#### 🔔 **Automatic Signal Notifications**
- Runs every 30 minutes (configurable)
- Checks all pairs (EUR/USD, GBP/USD, XAU/USD, etc.)
- Sends notification ONLY when high-confidence signal detected
- Includes full signal details (entry, SL, TP)

#### 📈 **Hourly Market Status**
- Runs every 60 minutes
- Provides market overview for all pairs
- Shows current regime (trending/ranging/volatile)
- Lists real-time prices from OANDA
- No spam - concise status updates

---

## 🎯 Signal Generation Flow

```
1. Fetch Real-Time Data (OANDA API)
   ↓
2. Detect Market Regime (Trending/Ranging/Volatile)
   ↓
3. Filter Strategies by Regime Compatibility
   ↓
4. Get Votes from Top 50 Strategies
   ↓
5. Check Ensemble Agreement (≥80%?)
   ↓
6. Multi-Timeframe Confirmation (1H + 4H + Daily)
   ↓
7. Trend Alignment Check
   ↓
8. News Calendar Check (High-impact events?)
   ↓
9. Correlation Filter (Max 2 correlated pairs)
   ↓
10. Generate Signal OR "No Trade"
```

**Result**: Only 2-5 signals per day (high quality over quantity)

---

## 🔐 Data Sources & Real-Time Integration

### OANDA API (Primary - Real-Time)
- **Live Prices**: Bid/Ask spreads updated every second
- **Historical Data**: Up to 5000 candles per request
- **Instruments**: All major forex pairs + gold (XAU/USD)
- **Latency**: <100ms (suitable for intraday signals)
- **Environment**: Practice account (paper trading) or Live

### yfinance (Fallback - Historical)
- Used only if OANDA unavailable
- Daily/hourly data with ~15min delay
- Suitable for backtesting

### Data Fetcher Logic
```python
if OANDA_API_configured:
    data = fetch_from_oanda(pair, realtime=True)
else:
    data = fetch_from_yfinance(pair, historical=True)
```

---

## 📱 User Experience Features

### Beautiful Telegram Messages
- **Emojis**: 📈 📉 🟢 🟡 ⚠️ ✅ ❌ (visual clarity)
- **Markdown Formatting**: Bold, italics, code blocks
- **Structured Layout**: Easy to scan and understand
- **Risk Warnings**: Clear disclaimers for human execution

### Signal Format Example
```
🟢 Trading Signal

Pair: EUR/USD
Direction: 📈 BUY
Confidence: 85.2%

Entry Zone: 1.0850 - 1.0865
Stop Loss: 1.0835
Take Profit: 1.0920

Ensemble Agreement: 86.7%
Strategies Used: 43

Risk Checks:
✓ Trend: BULLISH ALIGNED
✓ Timeframes: 3/3 AGREEMENT
✓ Correlation check passed

Time: 2025-11-03 14:30:00 UTC

⚠️ For Human Execution Only
This signal passed all filters and is ready for manual execution.
```

### Market Status Format Example
```
📊 Hourly Market Status

EUR/USD: 1.0857 | Trending ↗️ | No Signal
GBP/USD: 1.2645 | Ranging ↔️ | BUY Signal (83%)
XAU/USD: 2745.30 | Volatile 📊 | No Signal

🟢 1 Active Signal
⚪ 2 Monitoring

Next update: 15:00 UTC
```

---

## ⚙️ Configuration

### Environment Variables (`config/secrets.env`)
```bash
# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_ALLOWED_USERS=123456789  # Your Telegram user ID

# OANDA Real-Time Data
OANDA_API_KEY=your_oanda_token
OANDA_ACCOUNT_ID=your_account_id
OANDA_ENVIRONMENT=practice  # or 'live'

# Auto Features
ENABLE_AUTO_SIGNALS=true
AUTO_SIGNAL_INTERVAL=1800  # 30 minutes
HOURLY_STATUS_ENABLED=true
HOURLY_STATUS_INTERVAL=3600  # 60 minutes

# Trading Parameters
MIN_CONFIDENCE_THRESHOLD=80.0
MIN_AGREEMENT_THRESHOLD=0.80
MAX_DRAWDOWN_THRESHOLD=0.20
```

---

## 🧪 Testing & Validation

### Backtesting Protocol
1. **Train/Test Split**: 80/20 (temporal split)
2. **Walk-Forward Validation**: Rolling windows
3. **Out-of-Sample Testing**: Final 20% never seen during training
4. **Slippage & Spreads**: 0.02% slippage + 0.01% spread (realistic)
5. **Minimum Trades**: 30+ trades per strategy for statistical significance

### Pre-Deployment Validation
```bash
python scripts/pre_deploy.py  # Generate and test 100 strategies
python scripts/test_oanda_connection.py  # Verify OANDA API
python main.py  # Start bot and verify commands
```

---

## 📈 Expected Usage Patterns

### Typical Day
- **06:00-10:00 UTC**: High activity (London open) - 1-2 signals
- **13:00-17:00 UTC**: Medium activity (NY open) - 1 signal
- **20:00-23:00 UTC**: Low activity (Asian session) - 0-1 signal

### Signal Frequency
- **Average**: 2-4 signals per day across all pairs
- **High Volatility Days**: 5-7 signals
- **Low Volatility Days**: 0-2 signals

### Notification Volume
- **Signal Notifications**: 2-4/day (only when high-confidence)
- **Hourly Status**: 24/day (concise market overview)
- **Drift Alerts**: 0-2/week (only when strategy degradation detected)

---

## 🚨 Risk Disclaimers

1. **No Auto-Trading**: All signals require manual execution
2. **Past Performance**: Backtest results do not guarantee future performance
3. **Market Risk**: Forex trading involves substantial risk of loss
4. **Position Sizing**: Never risk more than 1-2% per trade
5. **Stop-Loss**: Always use the provided stop-loss levels
6. **News Events**: Bot blocks signals during high-impact news, but manual caution advised

---

## 🔧 Maintenance & Monitoring

### What's Monitored
- **Strategy Win Rate**: Alerts if <50% over 30 days
- **Ensemble Agreement**: Tracks if strategies diverging
- **API Uptime**: OANDA connection health
- **Signal Accuracy**: Tracks if recommendations profitable

### What's Updated
- **Every 5 minutes**: Learning loop updates strategies
- **Every hour**: Drift detection checks performance
- **Daily**: Database cleanup and optimization

---

## 📚 Additional Resources

- **AWS Deployment**: See `AWS_DEPLOYMENT.md`
- **OANDA Setup**: See `OANDA_SETUP.md`
- **Local Testing**: See `LOCAL_TESTING.md`
- **Pre-Deployment Checklist**: See `PRE_DEPLOYMENT_CHECKLIST.md`

---

## 🎯 Key Takeaways

✅ **High Accuracy**: 65-72% real-world win rate target with ensemble voting
✅ **Real-Time Data**: OANDA API integration for live prices
✅ **7-Layer Filtering**: Multiple checks ensure signal quality
✅ **Automatic Notifications**: Smart alerts only when high-confidence signals
✅ **Hourly Status**: Market overview without spam
✅ **Beautiful UX**: Emoji-rich, well-formatted Telegram messages
✅ **No Auto-Execution**: All signals for human review and manual trading
✅ **24/7 Operation**: Continuous monitoring and learning

---

**Version**: 1.0.0
**Last Updated**: 2025-11-03
