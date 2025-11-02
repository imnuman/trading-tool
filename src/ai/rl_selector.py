"""
Reinforcement Learning Strategy Selector
Maps market state to strategy confidence
"""

import numpy as np
import pandas as pd
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class RLSelector:
    """
    Simplified RL selector for strategy confidence mapping
    In production, this would use stable-baselines3 or TensorFlow
    """
    
    def __init__(self):
        """Initialize RL selector"""
        self.q_table = {}  # State-action value table
        self.learning_rate = 0.1
        self.discount_factor = 0.95
        self.epsilon = 0.1  # Exploration rate
    
    def get_market_state(self, data: pd.DataFrame) -> tuple:
        """
        Extract market state features
        
        Returns:
            Tuple of state features
        """
        if data.empty or len(data) < 50:
            return (0, 0, 0, 0, 0)
        
        recent = data.tail(50)
        
        # Trend strength (0-1)
        sma_short = recent['close'].rolling(10).mean().iloc[-1]
        sma_long = recent['close'].rolling(30).mean().iloc[-1]
        trend_strength = abs(sma_short - sma_long) / sma_long
        
        # Volatility regime (0-1)
        volatility = recent['volatility'].iloc[-1] if 'volatility' in recent.columns else 0
        vol_percentile = np.percentile(recent['volatility'].tail(100) if len(recent) > 100 
                                       else recent['volatility'], 50)
        vol_regime = min(volatility / (vol_percentile + 1e-10), 2.0) / 2.0
        
        # ATR percentile (0-1)
        atr = recent['atr'].iloc[-1] if 'atr' in recent.columns else 0
        atr_percentile = np.percentile(recent['atr'].tail(100) if len(recent) > 100 
                                      else recent['atr'], 50)
        atr_pct = min(atr / (atr_percentile + 1e-10), 2.0) / 2.0
        
        # Session timing (0 or 1)
        hour = recent.index[-1].hour if hasattr(recent.index[-1], 'hour') else 12
        session = 1 if 8 <= hour <= 20 else 0
        
        # Recent momentum (0-1)
        returns = recent['returns'].tail(10) if 'returns' in recent.columns else pd.Series([0])
        momentum = abs(returns.mean())
        
        # Discretize state for Q-table
        state = (
            int(min(trend_strength * 10, 9)),
            int(min(vol_regime * 10, 9)),
            int(min(atr_pct * 10, 9)),
            session,
            int(min(momentum * 1000, 9))
        )
        
        return state
    
    def get_strategy_confidence(
        self, 
        strategy_id: str, 
        market_state: tuple,
        base_confidence: float
    ) -> float:
        """
        Get adjusted confidence for strategy based on market state
        
        Args:
            strategy_id: Strategy identifier
            market_state: Current market state tuple
            base_confidence: Base confidence from backtest
        
        Returns:
            Adjusted confidence score
        """
        # Get Q-value for this state-strategy pair
        key = (market_state, strategy_id)
        
        if key not in self.q_table:
            # Initialize with base confidence
            self.q_table[key] = base_confidence / 100.0
        
        # Get confidence from Q-table
        q_value = self.q_table[key]
        confidence = q_value * 100
        
        # Apply exploration
        if np.random.random() < self.epsilon:
            confidence = np.random.uniform(confidence * 0.8, min(confidence * 1.2, 100))
        
        return max(0, min(confidence, 100))
    
    def update_q_value(
        self,
        strategy_id: str,
        market_state: tuple,
        reward: float,
        next_state: tuple = None
    ):
        """
        Update Q-value based on reward
        
        Args:
            strategy_id: Strategy identifier
            market_state: Market state when action was taken
            reward: Reward signal (+1 for profit, -1 for loss, 0 for no trade)
            next_state: Next market state (optional)
        """
        key = (market_state, strategy_id)
        
        if key not in self.q_table:
            self.q_table[key] = 0.0
        
        current_q = self.q_table[key]
        
        # Simple Q-learning update
        if next_state:
            next_key = (next_state, strategy_id)
            next_q = self.q_table.get(next_key, 0.0)
            target = reward + self.discount_factor * next_q
        else:
            target = reward
        
        # Update Q-value
        new_q = current_q + self.learning_rate * (target - current_q)
        self.q_table[key] = new_q
        
        logger.debug(f"Updated Q-value for {strategy_id}: {current_q:.4f} -> {new_q:.4f}")

