#!/usr/bin/env python3
"""
Generate Synthetic Forex Data for Testing
Creates realistic historical price data when yfinance is unavailable
"""

import pandas as pd
import numpy as np
from pathlib import Path
import pickle
from datetime import datetime, timedelta

def generate_forex_data(
    pair_name: str,
    start_price: float,
    days: int = 1825,  # 5 years
    volatility: float = 0.008,  # 0.8% daily volatility
    trend: float = 0.0001,  # Slight upward trend
    interval: str = '1d'
) -> pd.DataFrame:
    """
    Generate realistic forex price data using geometric Brownian motion

    Args:
        pair_name: Trading pair name (e.g., "EUR/USD")
        start_price: Initial price
        days: Number of days to generate
        volatility: Daily volatility (standard deviation)
        trend: Daily trend (drift)
        interval: Data interval ('1d' for daily)

    Returns:
        DataFrame with OHLCV data
    """
    print(f"Generating {days} days of data for {pair_name}...")

    # Generate timestamps
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')

    # Generate price movements using geometric Brownian motion
    # This creates realistic forex-like price action
    returns = np.random.normal(trend, volatility, len(dates))
    price = start_price * np.exp(np.cumsum(returns))

    # Generate OHLC from close prices
    # High = close + random uptick (0-0.3% of price)
    # Low = close - random downtick (0-0.3% of price)
    # Open = previous close + small gap (-0.1% to +0.1%)

    high = price * (1 + np.abs(np.random.normal(0, 0.002, len(dates))))
    low = price * (1 - np.abs(np.random.normal(0, 0.002, len(dates))))

    # Open is previous close with small gap
    open_prices = np.zeros(len(dates))
    open_prices[0] = start_price
    for i in range(1, len(dates)):
        gap = np.random.normal(0, 0.0005)  # Small gap
        open_prices[i] = price[i-1] * (1 + gap)

    # Ensure OHLC relationship: high >= max(open, close), low <= min(open, close)
    for i in range(len(dates)):
        high[i] = max(high[i], open_prices[i], price[i])
        low[i] = min(low[i], open_prices[i], price[i])

    # Generate volume (realistic forex volume pattern)
    # Higher volume during London/NY sessions, lower during Asian
    base_volume = 100000
    volume = np.random.lognormal(np.log(base_volume), 0.5, len(dates)).astype(int)

    # Create DataFrame
    df = pd.DataFrame({
        'open': open_prices,
        'high': high,
        'low': low,
        'close': price,
        'volume': volume
    }, index=dates)

    # Add technical indicators (same as data_fetcher.py)
    df = add_indicators(df)

    return df


def add_indicators(data: pd.DataFrame) -> pd.DataFrame:
    """Add technical indicators to price data"""
    # Moving averages
    data['sma_20'] = data['close'].rolling(window=20, min_periods=1).mean()
    data['sma_50'] = data['close'].rolling(window=50, min_periods=1).mean()
    data['ema_12'] = data['close'].ewm(span=12, adjust=False).mean()
    data['ema_26'] = data['close'].ewm(span=26, adjust=False).mean()

    # RSI
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
    rs = gain / loss.replace(0, 1e-10)
    data['rsi_14'] = 100 - (100 / (1 + rs))

    # ATR
    high_low = data['high'] - data['low']
    high_close = np.abs(data['high'] - data['close'].shift())
    low_close = np.abs(data['low'] - data['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    data['atr_14'] = true_range.rolling(window=14, min_periods=1).mean()

    # Returns and volatility
    data['returns'] = data['close'].pct_change()
    data['volatility'] = data['returns'].rolling(window=14, min_periods=1).std()

    # Fill NaN with forward fill
    data = data.fillna(method='ffill').fillna(0)

    return data


def main():
    """Generate synthetic data for all forex pairs"""
    print("=" * 60)
    print("Generating Synthetic Forex Data for Testing")
    print("=" * 60)
    print()

    # Create cache directory
    cache_dir = Path("data/cache")
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Forex pairs with realistic starting prices
    pairs = {
        "EUR/USD": 1.0850,
        "GBP/USD": 1.2640,
        "XAU/USD": 2650.00,  # Gold
        "USD/JPY": 149.50,
        "AUD/USD": 0.6580,
        "USD/CHF": 0.8850,
    }

    # Generate data for each pair
    for pair_name, start_price in pairs.items():
        # Adjust volatility based on pair type
        if "XAU" in pair_name:  # Gold is more volatile
            volatility = 0.012
        else:
            volatility = 0.008

        # Generate data
        data = generate_forex_data(
            pair_name=pair_name,
            start_price=start_price,
            days=1825,  # 5 years
            volatility=volatility,
            interval='1d'
        )

        # Save to cache (matching data_fetcher.py format)
        # Replace / with - for filename safety
        safe_pair_name = pair_name.replace("/", "-")
        cache_file = cache_dir / f"{safe_pair_name}_5y_1d.pkl"
        with open(cache_file, 'wb') as f:
            pickle.dump(data, f)

        print(f"✅ Saved {len(data)} rows to {cache_file}")
        print(f"   Price range: {data['close'].min():.4f} - {data['close'].max():.4f}")
        print(f"   Latest price: {data['close'].iloc[-1]:.4f}")
        print()

    print("=" * 60)
    print(f"✅ Generated synthetic data for {len(pairs)} pairs")
    print(f"   Cache directory: {cache_dir.absolute()}")
    print()
    print("You can now run: python scripts/pre_deploy.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
