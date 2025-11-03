"""
Regime Detection
Detects market regime: Trending Up, Trending Down, Ranging, or Volatile
Filters strategies based on current market conditions
"""

import pandas as pd
import numpy as np
from typing import Dict, Literal, Tuple
import logging

logger = logging.getLogger(__name__)


class RegimeDetector:
    """
    Detects current market regime to match appropriate strategies
    """
    
    REGIME_TYPES = ['trending_up', 'trending_down', 'ranging', 'volatile']
    
    def __init__(
        self,
        adx_threshold: float = 25.0,  # ADX threshold for trend strength
        volatility_percentile: float = 0.75,  # Volatility threshold
        lookback_periods: int = 50  # Periods to analyze
    ):
        """
        Initialize regime detector
        
        Args:
            adx_threshold: ADX value above which market is trending
            volatility_percentile: Percentile above which market is volatile
            lookback_periods: Number of periods to analyze
        """
        self.adx_threshold = adx_threshold
        self.volatility_percentile = volatility_percentile
        self.lookback_periods = lookback_periods
    
    def detect_regime(self, data: pd.DataFrame) -> Tuple[Literal['trending_up', 'trending_down', 'ranging', 'volatile'], float]:
        """
        Detect current market regime
        
        Args:
            data: Price dataframe with OHLC data
        
        Returns:
            Tuple of (regime_type, confidence)
        """
        if data.empty or len(data) < self.lookback_periods:
            logger.warning("Not enough data for regime detection")
            return 'ranging', 0.5
        
        recent = data.tail(self.lookback_periods).copy()
        
        # Calculate ADX (Average Directional Index) for trend strength
        adx = self._calculate_adx(recent)
        
        # Calculate trend direction
        sma_short = recent['close'].rolling(window=20).mean()
        sma_long = recent['close'].rolling(window=50).mean()
        price_trend = sma_short.iloc[-1] - sma_long.iloc[-1]
        
        # Calculate volatility
        returns = recent['close'].pct_change()
        current_volatility = returns.tail(20).std()
        volatility_history = returns.rolling(window=50).std()
        volatility_dropped = volatility_history.dropna()
        if len(volatility_dropped) == 0:
            # Not enough data for regime detection
            return 'ranging', 0.5
        volatility_percentile = np.percentile(volatility_dropped, 75)
        
        # Detect regime
        if current_volatility > volatility_percentile * 1.5:
            # High volatility regime
            regime = 'volatile'
            confidence = min(1.0, (current_volatility / volatility_percentile) / 2.0)
        elif adx >= self.adx_threshold:
            # Strong trend detected
            if price_trend > 0:
                regime = 'trending_up'
                confidence = min(1.0, adx / 50.0)  # Normalize ADX
            else:
                regime = 'trending_down'
                confidence = min(1.0, adx / 50.0)
        else:
            # Weak trend = ranging market
            regime = 'ranging'
            # Confidence based on how weak the trend is
            confidence = 1.0 - (adx / self.adx_threshold)
            confidence = max(0.5, confidence)
        
        logger.debug(
            f"Regime detected: {regime} (confidence: {confidence:.2f}, "
            f"ADX: {adx:.2f}, Volatility: {current_volatility:.4f})"
        )
        
        return regime, confidence
    
    def _calculate_adx(self, data: pd.DataFrame, period: int = 14) -> float:
        """
        Calculate Average Directional Index (ADX)
        
        Args:
            data: OHLC dataframe
            period: ADX period
        
        Returns:
            ADX value
        """
        try:
            high = data['high']
            low = data['low']
            close = data['close']
            
            # Calculate True Range
            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())
            true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            
            # Calculate Directional Movement
            plus_dm = high.diff()
            minus_dm = -low.diff()
            
            plus_dm[plus_dm < 0] = 0
            minus_dm[minus_dm < 0] = 0
            
            # Smooth the values
            atr = true_range.rolling(window=period).mean()
            plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
            minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
            
            # Calculate DX and ADX
            dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
            adx = dx.rolling(window=period).mean()
            
            return float(adx.iloc[-1]) if not adx.empty else 20.0
            
        except Exception as e:
            logger.error(f"Error calculating ADX: {e}")
            return 20.0  # Default to weak trend
    
    def get_strategy_compatibility(
        self,
        strategy_type: str,
        regime: str
    ) -> float:
        """
        Get compatibility score between strategy type and regime
        
        Args:
            strategy_type: Strategy type (e.g., 'ema_cross', 'rsi_reversal')
            regime: Current market regime
        
        Returns:
            Compatibility score (0-1), where 1 = perfect match
        """
        # Strategy-regime compatibility matrix
        compatibility = {
            'trending_up': {
                'ema_cross': 1.0,
                'macd': 0.9,
                'ichimoku': 0.9,
                'atr_range': 0.3,
                'rsi_reversal': 0.4,
                'bollinger': 0.5,
                'volume_breakout': 0.8,
                'support_resistance': 0.6
            },
            'trending_down': {
                'ema_cross': 1.0,
                'macd': 0.9,
                'ichimoku': 0.9,
                'atr_range': 0.3,
                'rsi_reversal': 0.4,
                'bollinger': 0.5,
                'volume_breakout': 0.8,
                'support_resistance': 0.6
            },
            'ranging': {
                'ema_cross': 0.3,
                'macd': 0.2,
                'ichimoku': 0.2,
                'atr_range': 0.9,
                'rsi_reversal': 1.0,
                'bollinger': 1.0,
                'volume_breakout': 0.4,
                'support_resistance': 0.8
            },
            'volatile': {
                'ema_cross': 0.4,
                'macd': 0.3,
                'ichimoku': 0.3,
                'atr_range': 0.7,
                'rsi_reversal': 0.6,
                'bollinger': 0.7,
                'volume_breakout': 0.5,
                'support_resistance': 0.6
            }
        }
        
        # Extract strategy base type
        strategy_base = strategy_type.split('_')[0] if '_' in strategy_type else strategy_type
        
        # Get compatibility
        regime_map = compatibility.get(regime, {})
        score = regime_map.get(strategy_base, 0.5)  # Default to neutral
        
        return score
    
    def filter_strategies_by_regime(
        self,
        strategies: list,
        regime: str,
        min_compatibility: float = 0.6
    ) -> list:
        """
        Filter strategies based on regime compatibility
        
        Args:
            strategies: List of Strategy objects
            regime: Current market regime
            min_compatibility: Minimum compatibility score
        
        Returns:
            Filtered list of compatible strategies
        """
        compatible = []
        
        for strategy in strategies:
            strategy_type = strategy.entry_conditions.get('type', '')
            compatibility = self.get_strategy_compatibility(strategy_type, regime)
            
            if compatibility >= min_compatibility:
                compatible.append(strategy)
        
        logger.info(
            f"Regime filter: {len(compatible)}/{len(strategies)} strategies "
            f"compatible with {regime} regime (min compatibility: {min_compatibility})"
        )
        
        return compatible

