"""
Data Fetcher Module
Fetches historical and real-time price data for trading pairs
Supports both yfinance (free) and OANDA (real-time) data sources
"""

import pandas as pd
import numpy as np
import yfinance as yf
from typing import Dict, Optional
import logging
from pathlib import Path
import pickle
import os

logger = logging.getLogger(__name__)

# Try to import OANDA fetcher (optional)
try:
    from src.data.oanda_fetcher import OANDAFetcher
    OANDA_AVAILABLE = True
except ImportError:
    OANDA_AVAILABLE = False


class DataFetcher:
    """Fetches and manages market data"""

    def __init__(self, cache_dir: str = "data/cache", use_oanda: bool = True):
        """
        Initialize data fetcher

        Args:
            cache_dir: Directory to cache downloaded data
            use_oanda: Use OANDA API if available and configured (default: True)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.use_oanda = use_oanda

        # Initialize OANDA fetcher if available and configured
        self.oanda_fetcher = None
        if use_oanda and OANDA_AVAILABLE:
            try:
                self.oanda_fetcher = OANDAFetcher()
                # Test connection
                if self.oanda_fetcher.test_connection():
                    logger.info("✅ Using OANDA API for real-time data")
                else:
                    logger.warning("⚠️  OANDA configured but connection failed. Falling back to yfinance.")
                    self.oanda_fetcher = None
            except Exception as e:
                logger.warning(f"⚠️  OANDA not configured or unavailable: {e}. Using yfinance.")
                self.oanda_fetcher = None

        # Define trading pairs in standard format (EUR/USD) with their Yahoo Finance tickers (fallback)
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
        
        # OANDA instrument mapping
        self.oanda_pairs = {
            "USD_EURUSD": "EUR_USD",
            "GBP_GBPUSD": "GBP_USD",
            "JPY_USDJPY": "USD_JPY",
            "AUD_AUDUSD": "AUD_USD",
            "CHF_USDCHF": "USD_CHF",
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
                # Replace / with - for filename safety
                safe_pair_name = pair_name.replace("/", "-")
                cache_file = self.cache_dir / f"{safe_pair_name}_{period}_{interval}.pkl"
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

                    # Handle MultiIndex columns (yfinance sometimes returns tuples)
                    if isinstance(data.columns, pd.MultiIndex):
                        # Flatten MultiIndex: take the first level (usually the column name)
                        data.columns = [col[0] if isinstance(col, tuple) else col for col in data.columns]
                    
                    # Ensure column names are lowercase (handle both strings and tuples)
                    def normalize_col(col):
                        if isinstance(col, tuple):
                            return str(col[0]).lower() if len(col) > 0 else str(col).lower()
                        return str(col).lower()
                    
                    data.columns = [normalize_col(col) for col in data.columns]

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

    def get_realtime_price(self, pair_name: str) -> Optional[Dict]:
        """
        Get real-time price using OANDA (if available)
        
        Args:
            pair_name: Trading pair name
        
        Returns:
            Dictionary with bid/ask/mid prices or None
        """
        if self.oanda_fetcher and pair_name in self.oanda_pairs:
            oanda_pair = self.oanda_pairs[pair_name]
            return self.oanda_fetcher.get_current_price(oanda_pair)
        return None
    
    def load_data(
        self,
        pair_name: str,
        period: str = '60d',
        interval: str = '1h',
        use_oanda: Optional[bool] = None
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

        # Try OANDA first if available and pair is supported
        if (use_oanda is not False) and self.oanda_fetcher and pair_name in self.oanda_pairs:
            try:
                # Convert interval to OANDA granularity
                granularity_map = {
                    '1m': 'M1', '5m': 'M5', '15m': 'M15', '30m': 'M30',
                    '1h': 'H1', '4h': 'H4', '1d': 'D', '1w': 'W'
                }
                granularity = granularity_map.get(interval, 'H1')
                
                # Convert period to count (rough estimate)
                count = 500  # OANDA max is 5000, use 500 for reasonable response time
                
                logger.info(f"Loading {pair_name} from OANDA - {period} @ {interval}")
                data = self.oanda_fetcher.get_historical_data(
                    pair_name,
                    count=count,
                    granularity=granularity
                )
                
                if data is not None and not data.empty:
                    logger.info(f"✅ Loaded {len(data)} rows from OANDA")
                    return data
            except Exception as e:
                logger.warning(f"OANDA fetch failed for {pair_name}: {e}. Falling back to yfinance.")

        # Fallback to yfinance
        try:
            logger.info(f"Loading {pair_name} ({ticker}) from yfinance - {period} @ {interval}")

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

            # Handle MultiIndex columns (yfinance sometimes returns tuples)
            if isinstance(data.columns, pd.MultiIndex):
                # Flatten MultiIndex: take the first level (usually the column name)
                data.columns = [col[0] if isinstance(col, tuple) else col for col in data.columns]
            
            # Ensure column names are lowercase (handle both strings and tuples)
            def normalize_col(col):
                if isinstance(col, tuple):
                    return str(col[0]).lower() if len(col) > 0 else str(col).lower()
                return str(col).lower()
            
            data.columns = [normalize_col(col) for col in data.columns]

            # Add calculated indicators
            data = self._add_indicators(data)

            logger.info(f"Loaded {len(data)} rows for {pair_name}")
            return data

        except Exception as e:
            logger.error(f"Error loading {pair_name}: {e}")
            return None

    def get_latest_price(self, pair_name: str) -> Optional[float]:
        """
        Get the latest price for a trading pair (uses OANDA if available)

        Args:
            pair_name: Trading pair name

        Returns:
            Latest close price or None
        """
        # Try OANDA real-time price first
        if self.oanda_fetcher and pair_name in self.oanda_pairs:
            price_data = self.get_realtime_price(pair_name)
            if price_data:
                return price_data.get('mid')  # Use mid price
        
        # Fallback to yfinance
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
