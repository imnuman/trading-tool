# 60-65% Win Rate Blueprint Implementation Guide

**Target**: Realistic 60-65% win rate with HIGH CONFIDENCE signals
**Focus**: Confidence level over win rate
**Timeline**: 25-30 weeks (~6 months)
**Cost**: ~$660 (Lambda Labs training + AWS)

---

## 📋 TABLE OF CONTENTS

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Implementation Phases](#implementation-phases)
4. [Technical Stack](#technical-stack)
5. [Success Criteria](#success-criteria)
6. [Timeline & Milestones](#timeline--milestones)

---

## OVERVIEW

### Why This Blueprint?

The current system achieves 76% win rate on synthetic data, but this is **unrealistic** for live trading. This blueprint focuses on:

✅ **HIGH CONFIDENCE signals** (65-80% confidence score)
✅ **Realistic 60-65% win rate** (achievable in live markets)
✅ **Proper transaction cost modeling** (3-7 pips realistic spreads)
✅ **Strict validation** (12-window walk-forward, Monte Carlo)
✅ **Professional-grade AI** (LSTM + Transformer + 15 PPO agents)

### Key Differences from Current System

| Component | Current System | Blueprint System |
|-----------|---------------|------------------|
| **Models** | Rule-based strategies + Q-learning | 3 LSTM + 1 Transformer + 15 PPO agents |
| **Features** | 15 basic features | 50 engineered features |
| **Data Sources** | OANDA + yfinance | OANDA + TrueFX + NewsAPI + FRED |
| **Win Rate Target** | 70-80% | 60-65% (realistic) |
| **Confidence Scoring** | Basic voting | Calibrated ensemble confidence |
| **Transaction Costs** | Simplified | Realistic (3-7 pips) |
| **Training** | Local machine | Lambda Labs 8xA100 GPUs |
| **Validation** | Basic walk-forward | 12-window strict + Monte Carlo |

---

## SYSTEM ARCHITECTURE

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA COLLECTION                          │
├─────────────────────────────────────────────────────────────────┤
│  OANDA (15yr) → TrueFX (ticks) → NewsAPI (sentiment) → FRED    │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                    FEATURE ENGINEERING (50)                     │
├─────────────────────────────────────────────────────────────────┤
│  20 Price + 20 Indicators + 5 Order Flow + 5 Time Context      │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                     NEURAL NETWORKS                             │
├─────────────────────────────────────────────────────────────────┤
│  LSTM (3 models) → Price direction [0-1]                       │
│  Transformer (1) → Trend alignment [-1, +1]                    │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                    RL AGENTS (15 PPO)                           │
├─────────────────────────────────────────────────────────────────┤
│  5 Conservative + 5 Balanced + 5 Specialists                   │
│  → Select Top 5 → Ensemble Confidence [0-1]                    │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                  CONFIDENCE SCORING                             │
├─────────────────────────────────────────────────────────────────┤
│  LSTM (30%) + Transformer (25%) + RL (35%) + Agreement (10%)   │
│  → Final Confidence: 65-100%                                    │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                   RISK MANAGEMENT                               │
├─────────────────────────────────────────────────────────────────┤
│  • Confidence-based sizing (0.5-1% risk)                       │
│  • Transaction costs (3-7 pips)                                │
│  • News filter, regime filter, correlation check               │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                    SIGNAL GENERATION                            │
├─────────────────────────────────────────────────────────────────┤
│  Every 2 minutes → Telegram notification                       │
│  Format: "BUY EUR/USD @ 1.0850 (Confidence: 78%)"             │
└─────────────────────────────────────────────────────────────────┘
```

---

## IMPLEMENTATION PHASES

### Phase 1: Repository Setup & Architecture (Week 1)

**Duration**: 1 week
**Status**: ✅ IN PROGRESS

#### Tasks:
- [x] Create CURRENT_STATE.md assessment
- [x] Create feature branch: `feature/60-65-blueprint-implementation`
- [x] Create directory structure
- [x] Create configuration files (training_config.yaml, data_config.yaml, risk_config.yaml)
- [ ] Create initial Python file templates
- [ ] Commit Phase 1 setup to GitHub

#### Deliverables:
- Complete directory structure
- Configuration files
- This blueprint document

---

### Phase 2: Data Infrastructure (Weeks 2-3)

**Duration**: 1.5 weeks
**Status**: ⏳ PENDING

#### 2.1 TrueFX Client (2 days)
```python
# data_sources/truefx_client.py
- Connect to TrueFX API (free, no key required)
- Fetch tick-level data for EUR/USD, GBP/USD
- Extract 5 order flow proxy features:
  * bid_ask_spread
  * tick_volume
  * price_momentum_ticks
  * order_flow_imbalance
  * liquidity_proxy
```

#### 2.2 NewsAPI Client (2 days)
```python
# data_sources/newsapi_client.py
- Connect to NewsAPI (100 req/day free tier)
- Query forex/gold/economic news
- FinBERT sentiment analysis
- Extract 4 sentiment features:
  * overall_sentiment [-1, 1]
  * sentiment_strength [0, 1]
  * news_volume (count)
  * sentiment_change
```

#### 2.3 FRED Client (1 day)
```python
# data_sources/fred_client.py
- Connect to FRED API (free)
- Fetch macro data (interest rates, CPI, GDP, unemployment)
- Extract 5 macro features:
  * interest_rate_differential
  * inflation_trend
  * gdp_growth_rate
  * unemployment_change
  * dollar_strength
```

#### 2.4 Data Manager (2 days)
```python
# data_sources/data_manager.py
- Orchestrate all data sources
- Handle synchronization & alignment
- Quality validation
- Caching & storage
```

#### 2.5 Enhanced OANDA Client (2 days)
```python
# Enhance existing src/data/oanda_fetcher.py
- Add batch historical fetching (15 years)
- Rate limiting & error handling
- Resume capability for interrupted downloads
```

#### Validation:
- [ ] Fetch 15 years OANDA data for 3 pairs
- [ ] Collect 1 year TrueFX tick data
- [ ] Fetch 10 years FRED macro data
- [ ] Test NewsAPI sentiment analysis
- [ ] Verify all data synchronized

---

### Phase 3: Feature Engineering (Week 4)

**Duration**: 1 week
**Status**: ⏳ PENDING

#### 3.1 Price Features (20 features)
```python
# features/price_features.py
- Returns (1d, 5d, 20d, log)
- OHLC ratios & ranges
- Price momentum & acceleration
- Candle patterns
- VWAP deviations
```

#### 3.2 Technical Indicators (20 features)
```python
# features/technical_features.py
- Moving averages (SMA 20/50/200, EMA 12/26/50)
- RSI (14, 21)
- MACD (line, signal, histogram)
- ATR (14, 21)
- Bollinger Bands (upper, lower, width)
- Stochastic (K, D)
- ADX, CCI
```

#### 3.3 Feature Pipeline (2 days)
```python
# features/feature_pipeline.py
- Combine all 50 features
- Validation (missing, infinite, outliers)
- Normalization (z-score)
- Distribution shift detection
```

#### Validation:
- [ ] Generate all 50 features for 15 years
- [ ] Check correlation matrix (remove >0.95)
- [ ] Validate no missing/infinite values
- [ ] Save processed features to parquet

---

### Phase 4: Neural Networks (Weeks 5-6)

**Duration**: 2 weeks
**Status**: ⏳ PENDING

#### 4.1 LSTM Models (1 week)
```python
# models/lstm_models.py
- 3 LSTM models (one per pair)
- Architecture: [64, 32] units, dropout 0.2
- Input: 60 candle lookback, 50 features
- Output: Price direction [0-1]
- Training: 100 epochs, early stopping
```

#### 4.2 Transformer Model (1 week)
```python
# models/transformer_model.py
- Single transformer for trend alignment
- Architecture: 4 heads, 3 layers, d_model=128
- Input: 100 candle lookback, 50 features
- Output: Trend score [-1, +1]
- Training: 80 epochs, early stopping
```

#### 4.3 Training Scripts
```python
# training/train_neural_networks.py
- Walk-forward data splitting
- Hyperparameter tuning
- Model checkpointing
- TensorBoard logging
```

#### Validation:
- [ ] Train LSTM on 9 months, test on 3 months
- [ ] Achieve >55% directional accuracy
- [ ] Train Transformer with MSE <0.1
- [ ] Save model checkpoints

---

### Phase 5: Reinforcement Learning (Weeks 7-8)

**Duration**: 2 weeks
**Status**: ⏳ PENDING

#### 5.1 Forex Trading Environment (3 days)
```python
# training/forex_trading_env.py
- OpenAI Gym environment
- Observation: 50 features
- Action: [HOLD, BUY, SELL]
- Reward: Risk-adjusted returns
- Episode: 1000 steps
```

#### 5.2 PPO Agents (5 days)
```python
# training/train_rl_agents.py
- 15 PPO agents (stable-baselines3)
  * 5 Conservative (low risk, 65-70% target)
  * 5 Balanced (medium risk, 60-65% target)
  * 5 Specialists (trend/range/volatility)
- Training: 8M steps per agent
- Parallel environments: 8
```

#### 5.3 Agent Selection (2 days)
```python
# models/rl_agents/agent_selector.py
- Evaluate all 15 agents on test data
- Select top 5 by Sharpe ratio
- Ensemble voting mechanism
- Confidence aggregation
```

#### Validation:
- [ ] All 15 agents complete training
- [ ] Select top 5 agents (Sharpe >1.5)
- [ ] Test ensemble achieves 60-65% win rate
- [ ] Confidence calibration within ±5%

---

### Phase 6: Lambda Labs Training (Week 9)

**Duration**: 20 hours
**Status**: ⏳ PENDING
**Cost**: $206 (8xA100)

#### Training Plan:
```
GPU Setup: Lambda Labs 8xA100 80GB
Duration: 20 hours
Parallel Jobs: 4 (3 LSTM + 1 Transformer)

Job 1: LSTM EUR/USD (5 hours)
Job 2: LSTM GBP/USD (5 hours)
Job 3: LSTM XAU/USD (5 hours)
Job 4: Transformer (5 hours)
Job 5-19: 15 PPO agents (15 hours, 1 hour each)

Total Time: ~20 hours
```

#### Steps:
1. Package code & data for Lambda Labs
2. Upload to Lambda Labs instance
3. Start parallel training jobs
4. Monitor via TensorBoard
5. Download trained models
6. Save to S3 & local storage

#### Validation:
- [ ] All models trained successfully
- [ ] LSTM accuracy >55% on test set
- [ ] Transformer MSE <0.1
- [ ] RL agents Sharpe >1.5

---

### Phase 7: Validation Framework (Weeks 10-11)

**Duration**: 1.5 weeks
**Status**: ⏳ PENDING

#### 7.1 Walk-Forward Validation (5 days)
```python
# backtesting/walk_forward_validation.py
- 12 windows (9 months train, 3 months test)
- Strict criteria (ALL windows must pass):
  * Test win rate: 58-65%
  * Train-test gap: <7%
  * Sharpe ratio: >1.5
  * Max drawdown: <20%
  * Profit factor: >1.8
  * Min trades: 30 per window
```

#### 7.2 Transaction Cost Backtesting (2 days)
```python
# backtesting/transaction_cost_backtest.py
- Apply realistic spreads:
  * EUR/USD: 3 pips
  * GBP/USD: 4 pips
  * XAU/USD: 7 pips
- Slippage: 1-3 pips
- Verify performance after costs
```

#### 7.3 Monte Carlo Simulation (3 days)
```python
# backtesting/monte_carlo.py
- 10,000 permutations of trade history
- Bootstrap resampling
- Calculate 95% confidence intervals for:
  * Win rate
  * Sharpe ratio
  * Max drawdown
  * Profit factor
```

#### Validation Criteria:
- [ ] Pass ALL 12 walk-forward windows
- [ ] Test win rate 58-65% (after costs)
- [ ] Monte Carlo: 95% CI for win rate [55-67%]
- [ ] Max drawdown <20% in all scenarios

---

### Phase 8: Inference System (Week 12)

**Duration**: 1 week
**Status**: ⏳ PENDING

#### 8.1 Unified Inference Service (3 days)
```python
# deployment/inference_service.py
- Load all models (LSTM, Transformer, RL agents)
- Real-time feature extraction
- Confidence scoring algorithm:
  * LSTM: 30%
  * Transformer: 25%
  * RL ensemble: 35%
  * Agreement: 10%
- Signal generation every 2 minutes
```

#### 8.2 Confidence Calibration (2 days)
```python
# deployment/confidence_calibrator.py
- Isotonic regression calibration
- Weekly recalibration
- Track confidence vs actual win rate
- Alert if drift >10%
```

#### 8.3 Integration with Telegram Bot (2 days)
```python
# Enhance src/telegram/bot.py
- Replace ensemble with inference service
- Add /won and /lost commands
- Format signals with confidence
- Real-time notifications
```

#### Validation:
- [ ] Inference generates signals in <2 minutes
- [ ] Confidence calibration error <5%
- [ ] Telegram bot sends formatted signals
- [ ] /won and /lost tracking works

---

### Phase 9: Risk Management Integration (Week 13)

**Duration**: 0.5 weeks
**Status**: ⏳ PENDING

#### 9.1 Position Sizing (1 day)
```python
# risk_management/position_sizer.py
- Confidence-based sizing:
  * 80-100%: 1% risk
  * 70-79%: 0.75% risk
  * 65-69%: 0.5% risk
  * <65%: No trade
```

#### 9.2 Risk Filters (2 days)
```python
# Enhance src/risk/risk_manager.py
- Transaction cost filtering
- News event blocking (30 min before/after)
- Regime-based adjustments
- Correlation limits
- Daily/weekly loss limits
```

#### Validation:
- [ ] Position sizing correct for all tiers
- [ ] Risk filters block signals properly
- [ ] Max drawdown <15% in backtest

---

### Phase 10: AWS Infrastructure (Week 14)

**Duration**: 1 week
**Status**: ⏳ PENDING

#### 10.1 S3 Model Storage (1 day)
```python
# aws/s3_manager.py
- Upload trained models to S3
- Version control (YYYYMMDD format)
- Download for inference
```

#### 10.2 Lambda Orchestration (2 days)
```python
# aws/lambda_functions/
- inference_lambda.py: Run inference every 2 min
- training_lambda.py: Monthly retraining
- monitoring_lambda.py: Performance checks
```

#### 10.3 EventBridge Scheduling (1 day)
```
- Inference: Every 2 minutes
- Hourly status: Every 1 hour
- Daily monitoring: 9 AM UTC
- Monthly retrain: 1st of month
```

#### 10.4 CloudWatch Monitoring (1 day)
```
- Log all signals
- Track win rate, drawdown
- Alert on performance degradation
```

**Note**: Can start with local deployment initially.

---

### Phase 11: Paper Trading (Weeks 15-22)

**Duration**: 8 weeks
**Status**: ⏳ PENDING

#### Week-by-Week Monitoring:
- Week 15-16: Track all signals, no execution
- Week 17-18: Verify confidence calibration
- Week 19-20: Monitor win rate (target 60-65%)
- Week 21-22: Validate risk management

#### Success Criteria:
- [ ] Win rate 58-65% over 8 weeks
- [ ] Confidence accuracy ±5%
- [ ] Max drawdown <15%
- [ ] Sharpe ratio >1.5
- [ ] Profit factor >1.8

#### Exit Criteria:
- IF win rate <55% for 2 consecutive weeks → STOP, retrain
- IF max drawdown >20% → STOP, review risk management
- IF confidence drift >10% → Recalibrate

---

### Phase 12: Micro Live Testing (Weeks 23-26)

**Duration**: 4 weeks
**Status**: ⏳ PENDING

#### Test Setup:
- Account size: $1,000 (micro account)
- Position size: 0.01 lots (micro)
- Max risk: $10 per trade (1%)

#### Week-by-Week:
- Week 23: 5 trades max
- Week 24: 10 trades max
- Week 25: 15 trades max
- Week 26: 20 trades max

#### Success Criteria:
- [ ] Win rate 58-65%
- [ ] No single loss >$20
- [ ] Total profit >$0 (break-even minimum)
- [ ] Max drawdown <$150 (15%)

#### Exit Criteria:
- IF win rate <55% → STOP
- IF drawdown >$200 (20%) → STOP

---

### Phase 13: Full Production (Week 27+)

**Duration**: Ongoing
**Status**: ⏳ PENDING

#### Production Deployment:
- Scale to $10,000 account
- Position sizes: 0.1-1.0 lots
- Max risk: 1% per trade ($100)
- Target: $200-500/month

#### Continuous Learning:
```python
# deployment/feedback_loop.py
- Track /won and /lost commands
- Weekly confidence recalibration
- Monthly model retraining
- Quarterly full revalidation
```

#### Monthly Retraining:
- Provider: Vast.ai (1xA100)
- Duration: 3 hours
- Cost: $45/month
- Schedule: 1st of every month

---

## TECHNICAL STACK

### Data & APIs
- **OANDA**: Real-time forex data (existing)
- **TrueFX**: Free tick data for order flow
- **NewsAPI**: News + sentiment (100 req/day free)
- **FRED**: Macro data (free)

### Machine Learning
- **TensorFlow/Keras**: LSTM + Transformer
- **Stable-Baselines3**: PPO agents
- **OpenAI Gym**: RL environment
- **Scikit-learn**: Feature engineering, calibration

### Cloud Infrastructure
- **Lambda Labs**: GPU training (8xA100, $10.30/hr)
- **Vast.ai**: Monthly retraining (1xA100, $1.50/hr)
- **AWS Lambda**: Orchestration
- **AWS S3**: Model storage
- **AWS EventBridge**: Scheduling
- **AWS CloudWatch**: Monitoring

### Development Tools
- **Python 3.11+**
- **Pandas, NumPy**: Data processing
- **TA-Lib**: Technical indicators
- **Plotly**: Visualization
- **TensorBoard**: Training monitoring
- **SQLite**: Results database
- **python-telegram-bot**: User interface

---

## SUCCESS CRITERIA

### Phase Completion Criteria

| Phase | Success Metric |
|-------|---------------|
| Data Infrastructure | Fetch 15yr data for 3 pairs |
| Feature Engineering | 50 features, no missing values |
| Neural Networks | LSTM >55% accuracy, Transformer MSE <0.1 |
| RL Agents | Top 5 agents with Sharpe >1.5 |
| Lambda Training | All models trained in 20 hours |
| Validation | Pass ALL 12 walk-forward windows |
| Inference | Generate signals in <2 minutes |
| Paper Trading | 60-65% win rate over 8 weeks |
| Live Testing | Profit >$0, drawdown <15% |

### Production Success (Month 7+)

**Minimum Acceptable**:
- Win rate: 58-65%
- Sharpe ratio: >1.5
- Max drawdown: <20%
- Profit factor: >1.8
- Monthly return: >2%

**Target Performance**:
- Win rate: 60-65%
- Sharpe ratio: >2.0
- Max drawdown: <15%
- Profit factor: >2.0
- Monthly return: 3-5%

---

## TIMELINE & MILESTONES

### Summary Timeline

| Week | Phase | Milestone |
|------|-------|-----------|
| 1 | Setup | Repository structure complete |
| 2-3 | Data | All data sources integrated |
| 4 | Features | 50 features engineered |
| 5-6 | Neural Nets | LSTM + Transformer trained locally |
| 7-8 | RL Agents | 15 PPO agents trained locally |
| 9 | Lambda Labs | All models retrained on 8xA100 |
| 10-11 | Validation | Pass 12-window walk-forward |
| 12 | Inference | Unified service deployed |
| 13 | Risk Mgmt | Position sizing integrated |
| 14 | AWS | Cloud infrastructure (optional) |
| 15-22 | Paper Trading | 8 weeks validation |
| 23-26 | Live Test | $1,000 micro account |
| 27+ | Production | $10,000 account |

**Total Duration**: 25-30 weeks (~6 months to production)

### Cost Summary

| Item | Cost |
|------|------|
| Lambda Labs (20hr, 8xA100) | $206 |
| Vast.ai monthly retrain (7 months) | $315 |
| AWS Lambda/S3 (7 months) | $140 |
| NewsAPI | Free |
| TrueFX | Free |
| FRED | Free |
| **TOTAL** | **~$661** |

---

## RISK MITIGATION

### Technical Risks

| Risk | Mitigation |
|------|-----------|
| Model overfitting | 12-window walk-forward, strict criteria |
| Transaction costs too high | Realistic 3-7 pip spreads in backtest |
| Confidence calibration drift | Weekly recalibration, 10% drift alert |
| Data quality issues | Validation pipeline, outlier detection |
| API rate limits | Caching, batch requests, free tiers |

### Performance Risks

| Risk | Mitigation |
|------|-----------|
| Win rate <55% in paper trading | Stop trading, retrain models |
| Drawdown >20% | Emergency stop, review risk management |
| Overly conservative signals | Adjust confidence threshold (65→60%) |
| Slippage worse than expected | Increase transaction costs in backtest |

---

## NEXT STEPS

### Immediate (Week 1):
1. ✅ Complete repository setup
2. ✅ Create configuration files
3. ✅ Document blueprint
4. ⏳ Commit Phase 1 to GitHub
5. ⏳ Begin Phase 2: Data Infrastructure

### This Week (Week 2-3):
1. Implement TrueFX client
2. Implement NewsAPI client
3. Implement FRED client
4. Create central DataManager
5. Fetch initial datasets

### This Month (Week 2-6):
1. Complete data infrastructure
2. Engineer all 50 features
3. Train LSTM models locally
4. Train Transformer model locally
5. Begin RL agent development

---

**Document Version**: 1.0
**Last Updated**: 2025-11-05
**Status**: Phase 1 In Progress
**Branch**: `feature/60-65-blueprint-implementation`

---

## APPENDIX

### Reusable Components from Current System

**High Reusability (70-90%)**:
- `src/data/oanda_fetcher.py` - needs enhancement for batch fetching
- `src/risk/risk_manager.py` - extend with new filters
- `src/risk/correlation_manager.py` - make dynamic
- `src/backtesting/backtest_engine.py` - add transaction costs
- `src/backtesting/walk_forward.py` - extend to 12 windows
- `src/telegram/bot.py` - add /won, /lost commands
- `src/utils/database.py` - extend schema
- `src/ai/regime_detector.py` - integrate into pipeline
- `src/ai/trend_filter.py` - integrate into pipeline

**Medium Reusability (30-60%)**:
- `src/ai/ensemble.py` - voting logic reusable
- `src/strategies/strategy_generator.py` - useful for comparison
- `src/utils/learning_loop.py` - logic reusable, needs PPO

**Low Reusability (0-30%)**:
- `src/ai/rl_selector.py` - Q-learning, needs PPO replacement
- Current strategies - Blueprint uses neural nets + RL

### References

- **Original Blueprint**: Step-by-step instructions from user
- **Current State**: CURRENT_STATE.md
- **Configuration**: config/*.yaml files
- **Pre-deployment Results**: PRE_DEPLOYMENT_RESULTS.md

---

*End of Blueprint Document*
