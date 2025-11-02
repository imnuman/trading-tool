"""
Correlation Management
Prevents opening correlated positions that amplify risk
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Set
import logging

logger = logging.getLogger(__name__)


class CorrelationManager:
    """
    Manages correlation between trading pairs to prevent duplicate exposure
    """
    
    # Currency correlation matrix (typical correlations)
    # Higher correlation = more similar movement
    CURRENCY_CORRELATIONS = {
        ('EURUSD', 'GBPUSD'): 0.75,  # Both vs USD, highly correlated
        ('EURUSD', 'AUDUSD'): 0.60,
        ('EURUSD', 'USDJPY'): -0.70,  # Inverse (EUR/USD up = USD/JPY down)
        ('GBPUSD', 'AUDUSD'): 0.65,
        ('GBPUSD', 'USDJPY'): -0.60,
        ('AUDUSD', 'USDJPY'): -0.55,
        ('GBPUSD', 'EURGBP'): -0.85,  # Inverse (GBP/USD vs EUR/GBP)
        ('EURUSD', 'EURGBP'): 0.90,   # High correlation
    }
    
    def __init__(
        self,
        correlation_threshold: float = 0.70,  # Maximum allowed correlation
        max_positions_per_currency: int = 1,  # Max positions per base/quote currency
        lookback_periods: int = 100  # Periods for dynamic correlation calculation
    ):
        """
        Initialize correlation manager
        
        Args:
            correlation_threshold: Maximum correlation allowed between positions
            max_positions_per_currency: Maximum positions per currency
            lookback_periods: Periods for calculating dynamic correlation
        """
        self.correlation_threshold = correlation_threshold
        self.max_positions_per_currency = max_positions_per_currency
        self.lookback_periods = lookback_periods
        self.active_positions: Set[str] = set()  # Set of active pair positions
    
    def calculate_correlation(
        self,
        pair1: str,
        pair2: str,
        data1: Optional[pd.DataFrame] = None,
        data2: Optional[pd.DataFrame] = None
    ) -> float:
        """
        Calculate correlation between two pairs
        
        Args:
            pair1: First trading pair
            pair2: Second trading pair
            data1: Price data for pair1 (optional, for dynamic calculation)
            data2: Price data for pair2 (optional, for dynamic calculation)
        
        Returns:
            Correlation coefficient (-1 to 1)
        """
        # Try dynamic calculation if data provided
        if data1 is not None and data2 is not None:
            try:
                # Calculate returns
                returns1 = data1['close'].pct_change().tail(self.lookback_periods)
                returns2 = data2['close'].pct_change().tail(self.lookback_periods)
                
                # Align indices
                common_idx = returns1.index.intersection(returns2.index)
                if len(common_idx) > 20:
                    returns1 = returns1.loc[common_idx]
                    returns2 = returns2.loc[common_idx]
                    
                    correlation = returns1.corr(returns2)
                    if not pd.isna(correlation):
                        return float(correlation)
            except Exception as e:
                logger.debug(f"Could not calculate dynamic correlation: {e}")
        
        # Fallback to static correlation matrix
        # Check direct correlation
        if (pair1, pair2) in self.CURRENCY_CORRELATIONS:
            return self.CURRENCY_CORRELATIONS[(pair1, pair2)]
        
        # Check reverse order
        if (pair2, pair1) in self.CURRENCY_CORRELATIONS:
            return self.CURRENCY_CORRELATIONS[(pair2, pair1)]
        
        # Calculate based on currency overlap
        return self._estimate_correlation_by_currency(pair1, pair2)
    
    def _estimate_correlation_by_currency(self, pair1: str, pair2: str) -> float:
        """
        Estimate correlation based on shared currencies
        
        Args:
            pair1: First pair (e.g., 'EURUSD')
            pair2: Second pair (e.g., 'GBPUSD')
        
        Returns:
            Estimated correlation
        """
        # Extract base and quote currencies
        def extract_currencies(pair: str) -> tuple:
            pair = pair.upper()
            currencies = ['EUR', 'GBP', 'USD', 'JPY', 'AUD', 'CAD', 'CHF', 'NZD']
            base = None
            quote = None
            
            for curr in currencies:
                if pair.startswith(curr):
                    base = curr
                    remaining = pair[len(curr):]
                    for curr2 in currencies:
                        if remaining.startswith(curr2):
                            quote = curr2
                            break
                    break
            
            return base, quote
        
        base1, quote1 = extract_currencies(pair1)
        base2, quote2 = extract_currencies(pair2)
        
        if not base1 or not quote1 or not base2 or not quote2:
            return 0.0  # Unknown pairs
        
        # Same quote currency = positive correlation
        if quote1 == quote2:
            # Same base = perfect correlation
            if base1 == base2:
                return 1.0
            # Different base, same quote = moderate positive
            return 0.60
        
        # Same base currency = negative correlation
        if base1 == base2:
            return -0.70
        
        # One pair's base is other's quote (inverse)
        if base1 == quote2 or base2 == quote1:
            return -0.65
        
        # No direct relationship
        return 0.20
    
    def check_correlation_conflict(
        self,
        new_pair: str,
        new_direction: str,
        existing_positions: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Check if new signal conflicts with existing positions
        
        Args:
            new_pair: New trading pair
            new_direction: Direction of new signal ('buy' or 'sell')
            existing_positions: List of existing position dictionaries
        
        Returns:
            Dictionary with conflict information
        """
        if existing_positions is None:
            existing_positions = []
        
        if not existing_positions:
            return {
                'has_conflict': False,
                'conflicting_pairs': [],
                'reason': None
            }
        
        conflicting_pairs = []
        max_correlation = 0.0
        
        for position in existing_positions:
            existing_pair = position.get('pair', '').upper()
            existing_direction = position.get('direction', '')
            
            # Skip if same pair (would be replacing position)
            if existing_pair == new_pair.upper():
                continue
            
            # Calculate correlation
            correlation = abs(self.calculate_correlation(new_pair, existing_pair))
            
            # Check if correlation exceeds threshold
            if correlation >= self.correlation_threshold:
                # Check if directions are same (both long USD or both short USD)
                # This amplifies risk
                
                # Extract base currencies
                new_base = self._get_base_currency(new_pair, new_direction)
                existing_base = self._get_base_currency(existing_pair, existing_direction)
                
                # If both buying same currency or both selling same currency
                if new_direction == existing_direction and new_base == existing_base:
                    conflicting_pairs.append({
                        'pair': existing_pair,
                        'direction': existing_direction,
                        'correlation': correlation,
                        'reason': f"Same direction on correlated pair ({correlation:.2f})"
                    })
                    max_correlation = max(max_correlation, correlation)
        
        # Check currency exposure limits
        currency_exposures = self._count_currency_exposures(existing_positions + [{
            'pair': new_pair,
            'direction': new_direction
        }])
        
        exceeded_limits = []
        for currency, count in currency_exposures.items():
            if count > self.max_positions_per_currency:
                exceeded_limits.append(currency)
        
        has_conflict = len(conflicting_pairs) > 0 or len(exceeded_limits) > 0
        
        reason = None
        if conflicting_pairs:
            reason = f"High correlation with existing positions ({max_correlation:.2f})"
        elif exceeded_limits:
            reason = f"Currency exposure limit exceeded: {', '.join(exceeded_limits)}"
        
        return {
            'has_conflict': has_conflict,
            'conflicting_pairs': conflicting_pairs,
            'exceeded_currency_limits': exceeded_limits,
            'max_correlation': max_correlation,
            'reason': reason
        }
    
    def _get_base_currency(self, pair: str, direction: str) -> Optional[str]:
        """
        Get base currency being bought/sold
        
        Args:
            pair: Trading pair (e.g., 'EURUSD')
            direction: 'buy' or 'sell'
        
        Returns:
            Base currency being bought
        """
        pair = pair.upper()
        currencies = ['EUR', 'GBP', 'USD', 'JPY', 'AUD', 'CAD', 'CHF', 'NZD']
        
        for curr in currencies:
            if pair.startswith(curr):
                if direction == 'buy':
                    return curr  # Buying base currency
                else:
                    # Selling base = buying quote
                    remaining = pair[len(curr):]
                    for curr2 in currencies:
                        if remaining.startswith(curr2):
                            return curr2
                    break
                break
        
        return None
    
    def _count_currency_exposures(self, positions: List[Dict]) -> Dict[str, int]:
        """
        Count positions per currency
        
        Args:
            positions: List of position dictionaries
        
        Returns:
            Dictionary mapping currency to position count
        """
        exposures = {}
        
        for position in positions:
            pair = position.get('pair', '').upper()
            direction = position.get('direction', '')
            base_currency = self._get_base_currency(pair, direction)
            
            if base_currency:
                exposures[base_currency] = exposures.get(base_currency, 0) + 1
        
        return exposures
    
    def filter_signal_by_correlation(
        self,
        signal: Dict,
        existing_positions: Optional[List[Dict]] = None
    ) -> Optional[Dict]:
        """
        Filter signal based on correlation with existing positions
        
        Args:
            signal: Trading signal dictionary
            existing_positions: List of existing positions
        
        Returns:
            Signal if no conflict, None if conflict detected
        """
        if existing_positions is None:
            existing_positions = []
        
        pair = signal.get('pair', '')
        direction = signal.get('direction', '')
        
        conflict = self.check_correlation_conflict(pair, direction, existing_positions)
        
        if conflict['has_conflict']:
            logger.info(
                f"Signal filtered by correlation: {conflict['reason']}. "
                f"Conflicting pairs: {[cp['pair'] for cp in conflict['conflicting_pairs']]}"
            )
            return None
        
        # Add correlation info to signal
        signal['correlation_check'] = {
            'passed': True,
            'max_correlation': conflict['max_correlation'],
            'existing_positions_count': len(existing_positions)
        }
        
        return signal

