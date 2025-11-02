"""
Data Fetcher Module
Fetches historical and real-time price data for trading pairs
"""

import pandas as pd
import numpy as np
import yfinance as yf
from typing import Dict, Optional
import logging
from pathlib import Path
import pickle

logger = logging.getLogger(__name__)


class DataFetcher:
    """Fetches and manages market data"""

    def __init__(self, cache_dir: str = "data/cache"):
        """
        Initialize data fetcher

        Args:
            cache_dir: Directory to cache downloaded data
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Define trading pairs in standard format with their Yahoo Finance tickers
        # Format: "EUR/USD" -> Yahoo Finance ticker
        self.pair_mappings = {
            "EUR/USD": "EURUSD=X",
            "GBP/USD": "GBPUSD=X",
            "XAU/USD": "GC=F",  # Gold futures
            "USD/JPY": "USDJPY=X",
            "AUD/USD": "AUDUSD=X",
            "USD/CHF": "USDCHF=X",
        }

        # Backward compatibility mapping (old format -> new format)
        self.legacy_mappings = {
            "USD_EURUSD": "EUR/USD",
            "GBP_GBPUSD": "GBP/USD",
            "Gold_XAUUSD": "XAU/USD",
            "JPY_USDJPY": "USD/JPY",
            "AUD_AUDUSD": "AUD/USD",
            "CHF_USDCHF": "USD/CHF",
        }

    def fetch_all_pairs(
        self,
        period: str = '5y',
        interval: str = '1d'
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch historical data for all trading pairs

        Args:
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)

        Returns:
            Dictionary of {pair_name: DataFrame with OHLCV data}
        """
        logger.info(f"Fetching data for {len(self.pair_mappings)} pairs (period={period}, interval={interval})")

        all_data = {}

        for pair_name, ticker in self.pair_mappings.items():
            try:
                logger.info(f"Fetching {pair_name} ({ticker})...")

                # Check cache first
                cache_file = self.cache_dir / f"{pair_name}_{period}_{interval}.pkl"
                if cache_file.exists():
                    logger.info(f"Loading {pair_name} from cache")
                    with open(cache_file, 'rb') as f:
                        data = pickle.load(f)
                else:
                    # Fetch from yfinance
                    data = yf.download(
                        ticker,
                        period=period,
                        interval=interval,
                        progress=False,
                        auto_adjust=True
                    )

                    if data.empty:
                        logger.warning(f"No data received for {pair_name}")
                        continue

                    # Ensure column names are lowercase
                    data.columns = [col.lower() for col in data.columns]

                    # Add calculated indicators
                    data = self._add_indicators(data)

                    # Cache the data
                    with open(cache_file, 'wb') as f:
                        pickle.dump(data, f)

                    logger.info(f"Fetched {len(data)} rows for {pair_name}")

                all_data[pair_name] = data

            except Exception as e:
                logger.error(f"Error fetching {pair_name}: {e}")
                continue

        logger.info(f"Successfully fetched data for {len(all_data)}/{len(self.pair_mappings)} pairs")
        return all_data

    def load_data(
        self,
        pair_name: str,
        period: str = '60d',
        interval: str = '1h'
    ) -> Optional[pd.DataFrame]:
        """
        Load data for a specific pair

        Args:
            pair_name: Trading pair name (e.g., "EUR/USD" or legacy "USD_EURUSD")
            period: Time period to fetch
            interval: Data interval

        Returns:
            DataFrame with OHLCV data or None if fetch fails
        """
        # Handle legacy format for backward compatibility
        if pair_name in self.legacy_mappings:
            pair_name = self.legacy_mappings[pair_name]
            logger.debug(f"Converted legacy pair format to: {pair_name}")

        if pair_name not in self.pair_mappings:
            logger.error(f"Unknown pair: {pair_name}. Available pairs: {list(self.pair_mappings.keys())}")
            return None

        ticker = self.pair_mappings[pair_name]

        try:
            logger.info(f"Loading {pair_name} ({ticker}) - {period} @ {interval}")

            # Fetch from yfinance
            data = yf.download(
                ticker,
                period=period,
                interval=interval,
                progress=False,
                auto_adjust=True
            )

            if data.empty:
                logger.warning(f"No data received for {pair_name}")
                return None

            # Ensure column names are lowercase
            data.columns = [col.lower() for col in data.columns]

            # Add calculated indicators
            data = self._add_indicators(data)

            logger.info(f"Loaded {len(data)} rows for {pair_name}")
            return data

        except Exception as e:
            logger.error(f"Error loading {pair_name}: {e}")
            return None

    def get_latest_price(self, pair_name: str) -> Optional[float]:
        """
        Get the latest price for a trading pair

        Args:
            pair_name: Trading pair name

        Returns:
            Latest close price or None
        """
        data = self.load_data(pair_name, period='1d', interval='1m')
        if data is not None and not data.empty:
            return float(data['close'].iloc[-1])
        return None

    def get_available_pairs(self) -> list:
        """
        Get list of available trading pairs

        Returns:
            List of pair names in standard format (e.g., ["EUR/USD", "GBP/USD"])
        """
        return list(self.pair_mappings.keys())

    def _add_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Add technical indicators to OHLC data

        Args:
            data: OHLC DataFrame

        Returns:
            DataFrame with added indicators
        """
        if data.empty:
            return data

        df = data.copy()

        # Add volatility (ATR-like calculation)
        df['high_low'] = df['high'] - df['low']
        df['high_close'] = abs(df['high'] - df['close'].shift(1))
        df['low_close'] = abs(df['low'] - df['close'].shift(1))
        df['volatility'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
        df['volatility'] = df['volatility'].rolling(window=14).mean()

        # Add simple moving averages
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()

        # Add EMA
        df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
        df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()

        # Add RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        # Clean up temporary columns
        df.drop(['high_low', 'high_close', 'low_close'], axis=1, inplace=True, errors='ignore')

        return df

    def clear_cache(self):
        """Clear all cached data"""
        logger.info("Clearing data cache...")
        for cache_file in self.cache_dir.glob("*.pkl"):
            cache_file.unlink()
        logger.info("Cache cleared")
