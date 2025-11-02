"""
Risk Management and Safeguards
Volatility checks, liquidity filters, dynamic TP/SL adjustment
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, List
import logging
from datetime import datetime
from src.data.economic_calendar import EconomicCalendar
from src.risk.correlation_manager import CorrelationManager

logger = logging.getLogger(__name__)


class RiskManager:
    """Manages risk and applies safeguards"""
    
    def __init__(
        self,
        max_volatility_percentile: float = 0.95,
        min_liquidity_hours: list = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
        slippage_adjustment: float = 0.0002,
        spread_adjustment: float = 0.0001,
        use_news_filter: bool = True,
        use_correlation_filter: bool = True
    ):
        """
        Initialize risk manager
        
        Args:
            max_volatility_percentile: Maximum volatility percentile to allow trading
            min_liquidity_hours: Hours with acceptable liquidity
            slippage_adjustment: Slippage percentage to add to TP/SL
            spread_adjustment: Spread to add to TP/SL
            use_news_filter: Enable economic calendar filtering
            use_correlation_filter: Enable correlation management
        """
        self.max_volatility_percentile = max_volatility_percentile
        self.min_liquidity_hours = min_liquidity_hours
        self.slippage_adjustment = slippage_adjustment
        self.spread_adjustment = spread_adjustment
        
        # Initialize filters
        self.use_news_filter = use_news_filter
        self.use_correlation_filter = use_correlation_filter
        self.economic_calendar = EconomicCalendar() if use_news_filter else None
        self.correlation_manager = CorrelationManager() if use_correlation_filter else None
    
    def check_signal_safety(
        self, 
        signal: Dict, 
        data: pd.DataFrame,
        existing_positions: Optional[List[Dict]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if signal is safe to execute
        
        Args:
            signal: Signal dictionary
            data: Historical price data
            existing_positions: List of existing positions for correlation check
        
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
        
        # Check economic calendar (news filter)
        if self.use_news_filter and self.economic_calendar:
            is_allowed, reason = self.economic_calendar.is_trading_allowed()
            if not is_allowed:
                return False, reason
        
        # Check correlation with existing positions
        if self.use_correlation_filter and self.correlation_manager:
            conflict = self.correlation_manager.check_correlation_conflict(
                signal.get('pair', ''),
                signal.get('direction', ''),
                existing_positions or []
            )
            if conflict['has_conflict']:
                return False, conflict['reason']
        
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

