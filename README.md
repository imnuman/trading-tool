# Trading Tool - AI-Powered Forex Signal Generator

A Telegram-interfaced AI trading system with infinite strategy learning, reinforcement learning-based signal generation, and continuous self-improvement.

## Features

- **Infinite Strategy Engine**: Pre-generates and backtests thousands of strategies on full historical data
- **Reinforcement Learning**: RL-based strategy selector adapts to market conditions
- **Ensemble Signals**: High-confidence signals with ≥80% ensemble agreement
- **Continuous Learning**: Self-improves every second from live and historical data
- **Telegram Interface**: Easy-to-use bot for signals, chart analysis, and stats
- **Risk Management**: Built-in safeguards for overfitting, volatility, and slippage

## Quick Start

1. **Run setup script**:
   ```bash
   ./setup.sh
   ```
   
   Or manually:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp config/secrets.env.example config/secrets.env
   # Edit config/secrets.env with your Telegram bot token
   ```

3. **Run pre-deployment (Day 0)**:
   ```bash
   source venv/bin/activate  # If not already activated
   python3 scripts/pre_deploy.py
   ```

4. **Start the Telegram bot (Day 1)**:
   ```bash
   source venv/bin/activate  # If not already activated
   python3 main.py
   ```

## Project Structure

```
trading-tool/
├── config/              # Configuration files
├── data/               # Historical data storage
├── src/
│   ├── data/           # Data fetching and preprocessing
│   ├── strategies/     # Strategy generation and management
│   ├── backtesting/    # Backtesting engine
│   ├── ai/             # RL and ensemble models
│   ├── telegram/       # Telegram bot interface
│   └── utils/          # Utility functions
├── scripts/            # Deployment and setup scripts
├── tests/              # Unit tests
└── main.py            # Main entry point
```

## Telegram Commands

- `/signal` - Get high-confidence trading signal or "no trade"
- `/chart <pair>` - Get live/historical chart analysis (USD, GBP, Gold)
- `/stats` - View ensemble performance statistics
- `/help` - Show command usage

## Risk Management

- Only generates signals with ≥80% ensemble consensus
- Avoids trading during extreme volatility or low liquidity
- Dynamic stop-loss/take-profit adjustments for slippage
- Walk-forward validation to prevent overfitting
- Market state awareness for current conditions

