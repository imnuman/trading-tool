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
from src.ai.regime_detector import RegimeDetector
from src.ai.trend_filter import TrendFilter
from src.data.data_fetcher import DataFetcher

logger = logging.getLogger(__name__)


class EnsembleSignalGenerator:
    """Generates signals from ensemble of strategies"""
    
    def __init__(
        self,
        strategies: List[Strategy],
        min_agreement: float = 0.80,
        min_confidence: float = 80.0,
        use_regime_filter: bool = True,
        use_trend_filter: bool = True
    ):
        """
        Initialize ensemble generator
        
        Args:
            strategies: List of strategies to use in ensemble
            min_agreement: Minimum agreement threshold (0-1)
            min_confidence: Minimum confidence score to generate signal
            use_regime_filter: Enable regime-based strategy filtering
            use_trend_filter: Enable multi-timeframe trend filtering
        """
        self.strategies = strategies
        self.min_agreement = min_agreement
        self.min_confidence = min_confidence
        self.strategy_weights = self._calculate_weights(strategies)
        
        # Initialize filters
        self.use_regime_filter = use_regime_filter
        self.use_trend_filter = use_trend_filter
        self.regime_detector = RegimeDetector() if use_regime_filter else None
        self.trend_filter = TrendFilter() if use_trend_filter else None
        self.data_fetcher = DataFetcher() if use_trend_filter else None
    
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
        pair: str = "EURUSD"
    ) -> Optional[Dict]:
        """
        Generate signal from ensemble with regime and trend filtering
        
        Args:
            data: Historical price data (1h timeframe)
            current_price: Current market price
            pair: Trading pair name
        
        Returns:
            Signal dictionary or None if no high-confidence signal
        """
        # Step 1: Detect market regime and filter strategies
        active_strategies = self.strategies
        
        if self.use_regime_filter and self.regime_detector:
            regime, regime_confidence = self.regime_detector.detect_regime(data)
            logger.info(f"Market regime: {regime} (confidence: {regime_confidence:.2f})")
            
            # Filter strategies by regime compatibility
            active_strategies = self.regime_detector.filter_strategies_by_regime(
                self.strategies,
                regime,
                min_compatibility=0.6
            )
            
            if not active_strategies:
                logger.info(f"No strategies compatible with {regime} regime")
                return None
        
        # Step 2: Get multi-timeframe data for trend analysis
        data_4h = None
        data_1d = None
        
        if self.use_trend_filter and self.trend_filter:
            # Resample 1h data to 4h and daily for trend analysis
            try:
                if len(data) > 100:
                    # Resample to 4h (take every 4th hour, or use OHLC resampling)
                    data_4h = data.copy()
                    if hasattr(data.index[0], 'hour'):
                        # Resample hourly to 4h
                        data_4h = data_4h.resample('4H', closed='left', label='left').agg({
                            'open': 'first',
                            'high': 'max',
                            'low': 'min',
                            'close': 'last',
                            'volume': 'sum'
                        }).dropna()
                    
                    # Resample to daily
                    data_1d = data.copy()
                    data_1d = data_1d.resample('D', closed='left', label='left').agg({
                        'open': 'first',
                        'high': 'max',
                        'low': 'min',
                        'close': 'last',
                        'volume': 'sum'
                    }).dropna()
                    
                    # Add back technical metrics for daily
                    if 'volatility' not in data_1d.columns:
                        data_1d['returns'] = data_1d['close'].pct_change()
                        data_1d['volatility'] = data_1d['returns'].rolling(window=20).std()
            except Exception as e:
                logger.debug(f"Could not resample data for multi-timeframe: {e}")
        
        # Step 3: Get votes from filtered strategies
        votes = []
        strategy_signals = []
        
        for strategy in active_strategies:
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
        
        # Step 4: Apply trend filter (multi-timeframe confirmation)
        if self.use_trend_filter and self.trend_filter:
            trend_alignment = self.trend_filter.check_multi_timeframe_trend(
                data_1h=data,
                data_4h=data_4h,
                data_1d=data_1d
            )
            
            # Filter signal based on trend alignment
            signal = self.trend_filter.filter_signal_by_trend(signal, trend_alignment)
            
            if signal is None:
                logger.info("Signal filtered by trend: timeframes not aligned or fighting trend")
                return None
        
        logger.info(
            f"Generated {direction} signal for {pair} with {signal['confidence']:.1f}% confidence "
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

