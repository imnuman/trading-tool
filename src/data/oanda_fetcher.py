"""
OANDA Real-Time Data Fetcher
Fetches live forex prices from OANDA API
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import logging
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv('config/secrets.env')


class OANDAFetcher:
    """
    Fetches real-time and historical data from OANDA API
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        account_id: Optional[str] = None,
        environment: str = 'practice'
    ):
        """
        Initialize OANDA fetcher
        
        Args:
            api_key: OANDA API token (defaults to env var)
            account_id: OANDA account ID (defaults to env var)
            environment: 'practice' for demo, 'live' for live account
        """
        self.api_key = api_key or os.getenv('OANDA_API_KEY')
        self.account_id = account_id or os.getenv('OANDA_ACCOUNT_ID')
        self.environment = environment or os.getenv('OANDA_ENVIRONMENT', 'practice')
        
        # Validate API key
        if not self.api_key or self.api_key.lower() in ['optional', 'your_token_here', '']:
            raise ValueError(
                "OANDA_API_KEY not found or invalid. "
                "Please set it in config/secrets.env with your actual OANDA API token."
            )
        
        # Validate Account ID
        if not self.account_id or self.account_id.lower() in ['optional', 'your_account_id_here', '']:
            raise ValueError(
                "OANDA_ACCOUNT_ID not found or invalid. "
                "Please set it in config/secrets.env with your actual OANDA Account ID. "
                "You can find it in the OANDA platform (top-right corner) or by calling the accounts endpoint."
            )
        
        # Set API endpoints based on environment
        if self.environment == 'live':
            self.base_url = 'https://api-fxtrade.oanda.com/v3'
            self.stream_url = 'https://stream-fxtrade.oanda.com/v3'
        else:
            self.base_url = 'https://api-fxpractice.oanda.com/v3'
            self.stream_url = 'https://stream-fxpractice.oanda.com/v3'
        
        # Headers for API requests
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        # OANDA instrument naming (use underscores)
        self.instrument_mapping = {
            'EURUSD': 'EUR_USD',
            'GBPUSD': 'GBP_USD',
            'USDJPY': 'USD_JPY',
            'AUDUSD': 'AUD_USD',
            'USDCHF': 'USD_CHF',
            'NZDUSD': 'NZD_USD',
            'EURGBP': 'EUR_GBP',
            'EURAUD': 'EUR_AUD',
            'EURJPY': 'EUR_JPY',
            'GBPJPY': 'GBP_JPY',
        }
    
    def _convert_pair_to_oanda(self, pair: str) -> str:
        """
        Convert pair name to OANDA format
        
        Args:
            pair: Pair name (e.g., 'EURUSD', 'USD_EURUSD')
        
        Returns:
            OANDA format (e.g., 'EUR_USD')
        """
        # Remove common prefixes/suffixes
        pair = pair.upper().replace('USD_', '').replace('_', '')
        
        # Check if already in mapping
        if pair in self.instrument_mapping:
            return self.instrument_mapping[pair]
        
        # Try to extract currencies (e.g., 'EURUSD' -> 'EUR_USD')
        if len(pair) == 6:
            base = pair[:3]
            quote = pair[3:]
            return f"{base}_{quote}"
        
        # Default: return as is
        return pair.replace('USD', 'USD').replace('_', '_')
    
    def get_account_info(self) -> Dict:
        """
        Get account information
        
        Returns:
            Dictionary with account details
        """
        try:
            url = f'{self.base_url}/accounts/{self.account_id}'
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                logger.error(f"Bad Request (400). Check that Account ID '{self.account_id}' is correct.")
                logger.error("Get your Account ID from OANDA platform (top-right corner) or accounts endpoint.")
            else:
                logger.error(f"HTTP Error {e.response.status_code}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error fetching account info: {e}")
            return {}
    
    def get_current_price(self, instrument: str) -> Optional[Dict]:
        """
        Get current (live) price for an instrument
        
        Args:
            instrument: Instrument name (e.g., 'EUR_USD')
        
        Returns:
            Dictionary with bid/ask prices and timestamp
        """
        try:
            instrument = self._convert_pair_to_oanda(instrument)
            url = f'{self.base_url}/accounts/{self.account_id}/pricing'
            params = {'instruments': instrument}
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'prices' in data and len(data['prices']) > 0:
                price_data = data['prices'][0]
                return {
                    'instrument': instrument,
                    'bid': float(price_data.get('bids', [{}])[0].get('price', 0)),
                    'ask': float(price_data.get('asks', [{}])[0].get('price', 0)),
                    'mid': (float(price_data.get('bids', [{}])[0].get('price', 0)) + 
                           float(price_data.get('asks', [{}])[0].get('price', 0))) / 2,
                    'spread': (float(price_data.get('asks', [{}])[0].get('price', 0)) - 
                              float(price_data.get('bids', [{}])[0].get('price', 0))),
                    'time': price_data.get('time', ''),
                    'tradeable': price_data.get('tradeable', False)
                }
        except Exception as e:
            logger.error(f"Error fetching current price for {instrument}: {e}")
            return None
    
    def get_historical_data(
        self,
        instrument: str,
        count: int = 500,
        granularity: str = 'H1',
        from_time: Optional[datetime] = None,
        to_time: Optional[datetime] = None
    ) -> Optional[pd.DataFrame]:
        """
        Get historical OHLC data from OANDA
        
        Args:
            instrument: Instrument name (e.g., 'EUR_USD')
            count: Number of candles to fetch (max 5000)
            granularity: Timeframe (S5, S10, S15, S30, M1, M2, M4, M5, M10, M15, M30, H1, H2, H3, H4, H6, H8, H12, D, W, M)
            from_time: Start time (optional)
            to_time: End time (optional)
        
        Returns:
            DataFrame with OHLCV data
        """
        try:
            instrument = self._convert_pair_to_oanda(instrument)
            url = f'{self.base_url}/instruments/{instrument}/candles'
            
            params = {
                'granularity': granularity,
                'count': min(count, 5000)  # OANDA max is 5000
            }
            
            if from_time:
                params['from'] = from_time.strftime('%Y-%m-%dT%H:%M:%S.000000000Z')
            if to_time:
                params['to'] = to_time.strftime('%Y-%m-%dT%H:%M:%S.000000000Z')
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'candles' not in data or len(data['candles']) == 0:
                logger.warning(f"No candles returned for {instrument}")
                return None
            
            # Convert to DataFrame
            candles = []
            for candle in data['candles']:
                if candle.get('complete', False):  # Only use complete candles
                    candles.append({
                        'time': pd.to_datetime(candle['time']),
                        'open': float(candle['mid']['o']),
                        'high': float(candle['mid']['h']),
                        'low': float(candle['mid']['l']),
                        'close': float(candle['mid']['c']),
                        'volume': int(candle.get('volume', 0))
                    })
            
            if not candles:
                return None
            
            df = pd.DataFrame(candles)
            df.set_index('time', inplace=True)
            
            # Add technical indicators
            df = self._add_technical_indicators(df)
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {instrument}: {e}")
            return None
    
    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators to DataFrame"""
        # Calculate returns
        df['returns'] = df['close'].pct_change()
        
        # Volatility (rolling 20-period std)
        df['volatility'] = df['returns'].rolling(window=20).std()
        
        # Simple Moving Averages
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        
        # Exponential Moving Averages
        df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
        df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()
        
        # ATR (Average True Range)
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['atr'] = true_range.rolling(window=14).mean()
        
        # RSI (Relative Strength Index)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        return df
    
    def get_multiple_prices(self, instruments: List[str]) -> Dict[str, Dict]:
        """
        Get current prices for multiple instruments
        
        Args:
            instruments: List of instrument names
        
        Returns:
            Dictionary mapping instrument to price data
        """
        try:
            # Convert all instruments to OANDA format
            oanda_instruments = [self._convert_pair_to_oanda(inst) for inst in instruments]
            instruments_str = ','.join(oanda_instruments)
            
            url = f'{self.base_url}/accounts/{self.account_id}/pricing'
            params = {'instruments': instruments_str}
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            prices = {}
            if 'prices' in data:
                for price_data in data['prices']:
                    instrument = price_data.get('instrument', '')
                    prices[instrument] = {
                        'bid': float(price_data.get('bids', [{}])[0].get('price', 0)),
                        'ask': float(price_data.get('asks', [{}])[0].get('price', 0)),
                        'mid': (float(price_data.get('bids', [{}])[0].get('price', 0)) + 
                               float(price_data.get('asks', [{}])[0].get('price', 0))) / 2,
                        'spread': (float(price_data.get('asks', [{}])[0].get('price', 0)) - 
                                  float(price_data.get('bids', [{}])[0].get('price', 0))),
                        'time': price_data.get('time', ''),
                        'tradeable': price_data.get('tradeable', False)
                    }
            
            return prices
            
        except Exception as e:
            logger.error(f"Error fetching multiple prices: {e}")
            return {}
    
    def test_connection(self) -> bool:
        """
        Test API connection
        
        Returns:
            True if connection successful
        """
        try:
            account_info = self.get_account_info()
            if account_info and 'account' in account_info:
                logger.info(f"✅ OANDA connection successful!")
                logger.info(f"   Account ID: {account_info['account'].get('id', 'N/A')}")
                logger.info(f"   Account Balance: {account_info['account'].get('balance', 'N/A')}")
                logger.info(f"   Environment: {self.environment}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ OANDA connection failed: {e}")
            return False

