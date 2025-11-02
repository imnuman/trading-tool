"""
Ensemble Signal Generator
Top N strategies vote on buy/sell/no-trade with ≥80% agreement requirement
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging
from src.strategies.strategy_generator import Strategy
from src.backtesting.backtest_engine import BacktestEngine

logger = logging.getLogger(__name__)


class EnsembleSignalGenerator:
    """Generates signals from ensemble of strategies"""
    
    def __init__(
        self,
        strategies: List[Strategy],
        min_agreement: float = 0.80,
        min_confidence: float = 80.0
    ):
        """
        Initialize ensemble generator
        
        Args:
            strategies: List of strategies to use in ensemble
            min_agreement: Minimum agreement threshold (0-1)
            min_confidence: Minimum confidence score to generate signal
        """
        self.strategies = strategies
        self.min_agreement = min_agreement
        self.min_confidence = min_confidence
        self.strategy_weights = self._calculate_weights(strategies)
    
    def _calculate_weights(self, strategies: List[Strategy]) -> Dict[str, float]:
        """Calculate weights for each strategy based on performance"""
        # Equal weights for now - can be enhanced with RL weights
        weights = {}
        for strategy in strategies:
            weights[strategy.id] = 1.0 / len(strategies)
        return weights
    
    def generate_signal(
        self, 
        data: pd.DataFrame, 
        current_price: float,
        pair: str = "USD"
    ) -> Optional[Dict]:
        """
        Generate signal from ensemble
        
        Args:
            data: Historical price data
            current_price: Current market price
            pair: Trading pair name
        
        Returns:
            Signal dictionary or None if no high-confidence signal
        """
        # Get votes from each strategy
        votes = []
        strategy_signals = []
        
        for strategy in self.strategies:
            signal = self._get_strategy_signal(strategy, data, current_price)
            if signal:
                votes.append(signal['direction'])
                strategy_signals.append({
                    'strategy_id': strategy.id,
                    'direction': signal['direction'],
                    'confidence': signal.get('confidence', 50),
                    'entry': signal.get('entry', current_price),
                    'stop_loss': signal.get('stop_loss'),
                    'take_profit': signal.get('take_profit')
                })
        
        if not votes:
            return None
        
        # Calculate agreement
        buy_votes = sum(1 for v in votes if v == 'buy')
        sell_votes = sum(1 for v in votes if v == 'sell')
        total_votes = len(votes)
        
        buy_agreement = buy_votes / total_votes if total_votes > 0 else 0
        sell_agreement = sell_votes / total_votes if total_votes > 0 else 0
        
        # Determine direction
        direction = None
        agreement = 0
        
        if buy_agreement >= self.min_agreement:
            direction = 'buy'
            agreement = buy_agreement
        elif sell_agreement >= self.min_agreement:
            direction = 'sell'
            agreement = sell_agreement
        
        if direction is None:
            logger.debug(f"No signal: buy_agreement={buy_agreement:.2f}, sell_agreement={sell_agreement:.2f}")
            return None
        
        # Calculate weighted entry, stop loss, and take profit
        entry_zone, stop_loss, take_profit = self._calculate_levels(
            strategy_signals, direction, current_price
        )
        
        # Calculate overall confidence
        confidence = self._calculate_confidence(
            agreement, strategy_signals, direction
        )
        
        if confidence < self.min_confidence:
            logger.debug(f"Signal confidence {confidence:.1f} below threshold {self.min_confidence}")
            return None
        
        # Get strategy IDs used
        strategies_used = [s['strategy_id'] for s in strategy_signals 
                          if s['direction'] == direction]
        
        signal = {
            'pair': pair,
            'direction': direction,
            'entry_zone': entry_zone,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'confidence': confidence,
            'strategies_used': strategies_used,
            'agreement': agreement,
            'timestamp': pd.Timestamp.now().isoformat()
        }
        
        logger.info(
            f"Generated {direction} signal for {pair} with {confidence:.1f}% confidence "
            f"({agreement*100:.1f}% agreement from {len(strategies_used)} strategies)"
        )
        
        return signal
    
    def _get_strategy_signal(
        self, 
        strategy: Strategy, 
        data: pd.DataFrame, 
        current_price: float
    ) -> Optional[Dict]:
        """Get signal from a single strategy"""
        try:
            # Create temporary backtest engine for signal generation
            engine = BacktestEngine(data.tail(1000))  # Use recent data
            
            # Generate signals
            signals = engine._generate_signals(strategy)
            
            if signals.empty:
                return None
            
            # Get most recent signal
            recent_signals = signals[signals['signal'] != 0].tail(1)
            
            if recent_signals.empty:
                return None
            
            latest = recent_signals.iloc[-1]
            
            if pd.isna(latest['entry_price']):
                return None
            
            direction = 'buy' if latest['signal'] == 1 else 'sell'
            
            return {
                'direction': direction,
                'entry': latest['entry_price'],
                'stop_loss': latest['stop_loss'],
                'take_profit': latest['take_profit'],
                'confidence': 70.0  # Base confidence
            }
            
        except Exception as e:
            logger.error(f"Error getting signal from strategy {strategy.id}: {e}")
            return None
    
    def _calculate_levels(
        self, 
        strategy_signals: List[Dict], 
        direction: str,
        current_price: float
    ) -> Tuple[List[float], float, float]:
        """Calculate weighted entry zone, stop loss, and take profit"""
        matching_signals = [s for s in strategy_signals if s['direction'] == direction]
        
        if not matching_signals:
            return [current_price * 0.999, current_price * 1.001], current_price * 0.99, current_price * 1.01
        
        # Weighted average of levels
        entries = [s.get('entry', current_price) for s in matching_signals]
        stop_losses = [s.get('stop_loss') for s in matching_signals if s.get('stop_loss')]
        take_profits = [s.get('take_profit') for s in matching_signals if s.get('take_profit')]
        
        # Entry zone (±0.1% around weighted average)
        avg_entry = np.mean(entries)
        entry_zone = [
            avg_entry * (1 - 0.001),
            avg_entry * (1 + 0.001)
        ]
        
        # Stop loss and take profit
        stop_loss = np.mean(stop_losses) if stop_losses else (
            current_price * 0.98 if direction == 'buy' else current_price * 1.02
        )
        take_profit = np.mean(take_profits) if take_profits else (
            current_price * 1.04 if direction == 'buy' else current_price * 0.96
        )
        
        return entry_zone, stop_loss, take_profit
    
    def _calculate_confidence(
        self, 
        agreement: float, 
        strategy_signals: List[Dict],
        direction: str
    ) -> float:
        """Calculate overall signal confidence"""
        matching = [s for s in strategy_signals if s['direction'] == direction]
        
        if not matching:
            return 0.0
        
        # Base confidence from agreement
        base_confidence = agreement * 100
        
        # Average strategy confidence
        avg_strategy_confidence = np.mean([s.get('confidence', 50) for s in matching])
        
        # Weighted combination
        confidence = (base_confidence * 0.6) + (avg_strategy_confidence * 0.4)
        
        # Bonus for more strategies agreeing
        num_strategies_bonus = min(len(matching) * 2, 10)
        confidence += num_strategies_bonus
        
        return min(confidence, 100.0)

