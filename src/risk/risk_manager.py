"""
Risk Management and Safeguards
Volatility checks, liquidity filters, dynamic TP/SL adjustment
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class RiskManager:
    """Manages risk and applies safeguards"""
    
    def __init__(
        self,
        max_volatility_percentile: float = 0.95,
        min_liquidity_hours: list = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
        slippage_adjustment: float = 0.0002,
        spread_adjustment: float = 0.0001
    ):
        """
        Initialize risk manager
        
        Args:
            max_volatility_percentile: Maximum volatility percentile to allow trading
            min_liquidity_hours: Hours with acceptable liquidity
            slippage_adjustment: Slippage percentage to add to TP/SL
            spread_adjustment: Spread to add to TP/SL
        """
        self.max_volatility_percentile = max_volatility_percentile
        self.min_liquidity_hours = min_liquidity_hours
        self.slippage_adjustment = slippage_adjustment
        self.spread_adjustment = spread_adjustment
    
    def check_signal_safety(self, signal: Dict, data: pd.DataFrame) -> tuple[bool, Optional[str]]:
        """
        Check if signal is safe to execute
        
        Args:
            signal: Signal dictionary
            data: Historical price data
        
        Returns:
            Tuple of (is_safe, reason_if_not_safe)
        """
        # Check volatility
        if not self._check_volatility(data):
            return False, "Extreme volatility detected"
        
        # Check liquidity (session timing)
        if not self._check_liquidity(data):
            return False, "Low liquidity session"
        
        # Check if price levels are realistic
        if not self._check_price_levels(signal, data):
            return False, "Price levels outside acceptable range"
        
        return True, None
    
    def _check_volatility(self, data: pd.DataFrame) -> bool:
        """Check if volatility is acceptable"""
        if 'volatility' not in data.columns:
            return True  # Can't check, allow by default
        
        recent_volatility = data['volatility'].tail(100)
        volatility_percentile = np.percentile(recent_volatility, 95)
        current_volatility = recent_volatility.iloc[-1]
        
        # Reject if current volatility exceeds 95th percentile
        if current_volatility > volatility_percentile:
            logger.warning(f"High volatility detected: {current_volatility:.4f} > {volatility_percentile:.4f}")
            return False
        
        return True
    
    def _check_liquidity(self, data: pd.DataFrame) -> bool:
        """Check if current session has sufficient liquidity"""
        if data.empty:
            return True
        
        current_hour = data.index[-1].hour if hasattr(data.index[-1], 'hour') else pd.Timestamp.now().hour
        
        if current_hour not in self.min_liquidity_hours:
            logger.warning(f"Low liquidity session: hour {current_hour}")
            return False
        
        return True
    
    def _check_price_levels(self, signal: Dict, data: pd.DataFrame) -> bool:
        """Check if price levels are realistic"""
        if data.empty:
            return True
        
        current_price = float(data['close'].iloc[-1])
        recent_range = (float(data['high'].tail(50).max()), float(data['low'].tail(50).min()))
        
        # Check if stop loss and take profit are within reasonable range
        stop_loss = signal.get('stop_loss')
        take_profit = signal.get('take_profit')
        
        if stop_loss and take_profit:
            # Stop loss should not be too far from recent range
            range_size = recent_range[0] - recent_range[1]
            sl_distance = abs(current_price - stop_loss)
            tp_distance = abs(current_price - take_profit)
            
            # Reject if stop loss or take profit is more than 3x the recent range
            if sl_distance > range_size * 3 or tp_distance > range_size * 3:
                logger.warning("Price levels outside acceptable range")
                return False
        
        return True
    
    def adjust_levels_for_slippage(self, signal: Dict) -> Dict:
        """
        Adjust stop loss and take profit for slippage and spread
        
        Args:
            signal: Signal dictionary
        
        Returns:
            Signal with adjusted levels
        """
        adjusted = signal.copy()
        direction = signal['direction']
        entry_zone = signal['entry_zone']
        stop_loss = signal.get('stop_loss')
        take_profit = signal.get('take_profit')
        
        # Adjust entry zone
        if direction == 'buy':
            adjusted['entry_zone'] = [
                entry_zone[0] * (1 + self.slippage_adjustment + self.spread_adjustment),
                entry_zone[1] * (1 + self.slippage_adjustment + self.spread_adjustment)
            ]
            if stop_loss:
                adjusted['stop_loss'] = stop_loss * (1 - self.slippage_adjustment)
            if take_profit:
                adjusted['take_profit'] = take_profit * (1 + self.slippage_adjustment)
        else:  # sell
            adjusted['entry_zone'] = [
                entry_zone[0] * (1 - self.slippage_adjustment - self.spread_adjustment),
                entry_zone[1] * (1 - self.slippage_adjustment - self.spread_adjustment)
            ]
            if stop_loss:
                adjusted['stop_loss'] = stop_loss * (1 + self.slippage_adjustment)
            if take_profit:
                adjusted['take_profit'] = take_profit * (1 - self.slippage_adjustment)
        
        return adjusted

