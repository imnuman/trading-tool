"""
Trend Filter
Filters signals based on higher timeframe trends
Prevents trading against the major trend
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Literal
import logging

logger = logging.getLogger(__name__)


class TrendFilter:
    """
    Filters trades based on trend alignment across timeframes
    """
    
    def __init__(
        self,
        min_timeframe_alignment: int = 2,  # Require at least 2 timeframes to agree
        trend_strength_threshold: float = 0.6  # Minimum trend strength (0-1)
    ):
        """
        Initialize trend filter
        
        Args:
            min_timeframe_alignment: Minimum number of timeframes that must agree
            trend_strength_threshold: Minimum trend strength to consider valid
        """
        self.min_timeframe_alignment = min_timeframe_alignment
        self.trend_strength_threshold = trend_strength_threshold
    
    def detect_trend(
        self,
        data: pd.DataFrame,
        timeframe_name: str = "1h"
    ) -> Dict[str, float]:
        """
        Detect trend direction and strength
        
        Args:
            data: Price dataframe
            timeframe_name: Name of timeframe (for logging)
        
        Returns:
            Dictionary with trend info: {direction, strength, sma_short, sma_long}
        """
        if data.empty or len(data) < 50:
            return {
                'direction': 'neutral',
                'strength': 0.0,
                'sma_short': 0.0,
                'sma_long': 0.0
            }
        
        recent = data.tail(50).copy()
        
        # Calculate moving averages
        sma_short = recent['close'].rolling(window=10).mean()
        sma_long = recent['close'].rolling(window=30).mean()
        
        sma_short_val = sma_short.iloc[-1]
        sma_long_val = sma_long.iloc[-1]
        current_price = recent['close'].iloc[-1]
        
        # Determine direction
        if sma_short_val > sma_long_val and current_price > sma_short_val:
            direction = 'bullish'
            # Strength based on distance from MA
            strength = min(1.0, abs(sma_short_val - sma_long_val) / sma_long_val * 100)
        elif sma_short_val < sma_long_val and current_price < sma_short_val:
            direction = 'bearish'
            strength = min(1.0, abs(sma_short_val - sma_long_val) / sma_long_val * 100)
        else:
            direction = 'neutral'
            strength = 0.3  # Weak trend
        
        return {
            'direction': direction,
            'strength': strength,
            'sma_short': sma_short_val,
            'sma_long': sma_long_val,
            'timeframe': timeframe_name
        }
    
    def check_multi_timeframe_trend(
        self,
        data_1h: pd.DataFrame,
        data_4h: Optional[pd.DataFrame] = None,
        data_1d: Optional[pd.DataFrame] = None
    ) -> Dict:
        """
        Check trend alignment across multiple timeframes
        
        Args:
            data_1h: 1-hour timeframe data
            data_4h: 4-hour timeframe data (optional)
            data_1d: Daily timeframe data (optional)
        
        Returns:
            Dictionary with alignment results and recommendation
        """
        # Detect trends for each timeframe
        trends = {}
        
        trends['1h'] = self.detect_trend(data_1h, '1h')
        
        if data_4h is not None and not data_4h.empty:
            trends['4h'] = self.detect_trend(data_4h, '4h')
        
        if data_1d is not None and not data_1d.empty:
            trends['1d'] = self.detect_trend(data_1d, '1d')
        
        # Count bullish/bearish/neutral
        bullish_count = sum(1 for t in trends.values() if t['direction'] == 'bullish')
        bearish_count = sum(1 for t in trends.values() if t['direction'] == 'bearish')
        neutral_count = sum(1 for t in trends.values() if t['direction'] == 'neutral')
        
        total_timeframes = len(trends)
        
        # Determine overall alignment
        if bullish_count >= self.min_timeframe_alignment:
            alignment = 'bullish'
            alignment_strength = bullish_count / total_timeframes
        elif bearish_count >= self.min_timeframe_alignment:
            alignment = 'bearish'
            alignment_strength = bearish_count / total_timeframes
        else:
            alignment = 'neutral'
            alignment_strength = max(neutral_count, max(bullish_count, bearish_count)) / total_timeframes
        
        # Weight by timeframe importance (daily > 4h > 1h)
        weighted_score = 0.0
        if '1d' in trends:
            weight = 0.5
            if trends['1d']['direction'] == alignment:
                weighted_score += weight * trends['1d']['strength']
        if '4h' in trends:
            weight = 0.3
            if trends['4h']['direction'] == alignment:
                weighted_score += weight * trends['4h']['strength']
        if '1h' in trends:
            weight = 0.2
            if trends['1h']['direction'] == alignment:
                weighted_score += weight * trends['1h']['strength']
        
        is_aligned = (
            alignment != 'neutral' and
            alignment_strength >= (self.min_timeframe_alignment / total_timeframes) and
            weighted_score >= self.trend_strength_threshold
        )
        
        result = {
            'aligned': is_aligned,
            'alignment': alignment,
            'alignment_strength': alignment_strength,
            'weighted_score': weighted_score,
            'trends': trends,
            'bullish_count': bullish_count,
            'bearish_count': bearish_count,
            'neutral_count': neutral_count,
            'total_timeframes': total_timeframes
        }
        
        logger.info(
            f"Multi-timeframe trend: {alignment} ({bullish_count}B/{bearish_count}S/{neutral_count}N), "
            f"Aligned: {is_aligned}, Score: {weighted_score:.2f}"
        )
        
        return result
    
    def filter_signal_by_trend(
        self,
        signal: Dict,
        trend_alignment: Dict
    ) -> Optional[Dict]:
        """
        Filter signal based on trend alignment
        
        Args:
            signal: Trading signal dictionary
            trend_alignment: Result from check_multi_timeframe_trend
        
        Returns:
            Signal if aligned, None if not aligned
        """
        if not trend_alignment['aligned']:
            logger.info(f"Signal filtered: Trend not aligned ({trend_alignment['alignment']})")
            return None
        
        signal_direction = signal.get('direction')
        trend_direction = trend_alignment['alignment']
        
        # Check if signal direction matches trend
        if signal_direction == 'buy' and trend_direction == 'bearish':
            logger.info("Signal filtered: BUY signal but trend is BEARISH")
            return None
        
        if signal_direction == 'sell' and trend_direction == 'bullish':
            logger.info("Signal filtered: SELL signal but trend is BULLISH")
            return None
        
        # Adjust confidence based on trend strength
        trend_strength = trend_alignment['weighted_score']
        original_confidence = signal.get('confidence', 0.0)
        
        # Boost confidence if strong trend alignment
        if trend_strength > 0.8:
            confidence_boost = 5.0
        elif trend_strength > 0.6:
            confidence_boost = 3.0
        else:
            confidence_boost = 1.0
        
        signal['confidence'] = min(100.0, original_confidence + confidence_boost)
        signal['trend_aligned'] = True
        signal['trend_strength'] = trend_strength
        signal['trend_info'] = {
            'alignment': trend_direction,
            'timeframes': trend_alignment['total_timeframes'],
            'agreement': f"{trend_alignment['bullish_count'] if trend_direction == 'bullish' else trend_alignment['bearish_count']}/{trend_alignment['total_timeframes']}"
        }
        
        logger.info(
            f"Signal passed trend filter: {signal_direction} aligns with {trend_direction} trend "
            f"(confidence: {original_confidence:.1f}% → {signal['confidence']:.1f}%)"
        )
        
        return signal

