"""
Infinite Strategy Generator
Generates thousands to millions of strategies with technical indicators
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass
import json
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class Strategy:
    """Represents a trading strategy"""
    id: str
    name: str
    indicators: Dict[str, Any]
    timeframe: str
    session_filter: str  # 'London', 'NY', 'Both', 'Any'
    entry_conditions: Dict[str, Any]
    exit_conditions: Dict[str, Any]
    parameters: Dict[str, float]
    
    def to_dict(self) -> Dict:
        """Convert strategy to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'indicators': self.indicators,
            'timeframe': self.timeframe,
            'session_filter': self.session_filter,
            'entry_conditions': self.entry_conditions,
            'exit_conditions': self.exit_conditions,
            'parameters': self.parameters
        }


class StrategyGenerator:
    """Generates infinite trading strategies"""
    
    INDICATORS = [
        'ema', 'sma', 'rsi', 'macd', 'bollinger', 
        'atr', 'fibonacci', 'ichimoku', 'volume', 
        'support_resistance', 'stochastic', 'adx'
    ]
    
    TIMEFRAMES = ['1h', '4h', '1d']
    
    SESSIONS = ['London', 'NY', 'Both', 'Any']
    
    def __init__(self, max_strategies: int = 100000):
        """
        Initialize strategy generator
        
        Args:
            max_strategies: Maximum number of strategies to generate
        """
        self.max_strategies = max_strategies
        self.generated_strategies = []
        
    def generate_strategy(self, strategy_type: Optional[str] = None) -> Strategy:
        """
        Generate a single random strategy
        
        Args:
            strategy_type: Optional specific strategy type
        
        Returns:
            Strategy object
        """
        if strategy_type is None:
            strategy_type = np.random.choice([
                'ema_cross', 'rsi_reversal', 'macd_divergence',
                'bollinger_breakout', 'ichimoku_trend', 'support_resistance',
                'volume_breakout', 'atr_range', 'multi_indicator'
            ])
        
        strategy = self._create_strategy(strategy_type)
        return strategy
    
    def _create_strategy(self, strategy_type: str) -> Strategy:
        """Create a specific strategy type"""
        
        # Generate unique ID
        params = {
            'type': strategy_type,
            'seed': np.random.randint(0, 1000000)
        }
        strategy_id = self._generate_id(strategy_type, params)
        
        # Base parameters
        timeframe = np.random.choice(self.TIMEFRAMES)
        session_filter = np.random.choice(self.SESSIONS)
        
        # Strategy-specific generation
        if strategy_type == 'ema_cross':
            return self._create_ema_cross_strategy(strategy_id, timeframe, session_filter)
        elif strategy_type == 'rsi_reversal':
            return self._create_rsi_reversal_strategy(strategy_id, timeframe, session_filter)
        elif strategy_type == 'macd_divergence':
            return self._create_macd_strategy(strategy_id, timeframe, session_filter)
        elif strategy_type == 'bollinger_breakout':
            return self._create_bollinger_strategy(strategy_id, timeframe, session_filter)
        elif strategy_type == 'ichimoku_trend':
            return self._create_ichimoku_strategy(strategy_id, timeframe, session_filter)
        elif strategy_type == 'support_resistance':
            return self._create_sr_strategy(strategy_id, timeframe, session_filter)
        elif strategy_type == 'volume_breakout':
            return self._create_volume_strategy(strategy_id, timeframe, session_filter)
        elif strategy_type == 'atr_range':
            return self._create_atr_strategy(strategy_id, timeframe, session_filter)
        else:  # multi_indicator
            return self._create_multi_indicator_strategy(strategy_id, timeframe, session_filter)
    
    def _create_ema_cross_strategy(self, strategy_id: str, timeframe: str, session: str) -> Strategy:
        """EMA crossover strategy"""
        fast_period = np.random.randint(5, 25)
        slow_period = np.random.randint(30, 100)
        
        return Strategy(
            id=strategy_id,
            name=f"ema_cross_{fast_period}_{slow_period}",
            indicators={'ema_fast': fast_period, 'ema_slow': slow_period},
            timeframe=timeframe,
            session_filter=session,
            entry_conditions={
                'type': 'crossover',
                'fast_above_slow': True,
                'confirmation_bars': np.random.randint(1, 3)
            },
            exit_conditions={
                'opposite_cross': True,
                'stop_loss_pct': np.random.uniform(0.0015, 0.003),  # 15-30 pips for EURUSD
                'take_profit_pct': np.random.uniform(0.003, 0.006)  # 30-60 pips
            },
            parameters={
                'fast_ema': fast_period,
                'slow_ema': slow_period,
                'risk_reward_ratio': np.random.uniform(1.5, 3.0)
            }
        )
    
    def _create_rsi_reversal_strategy(self, strategy_id: str, timeframe: str, session: str) -> Strategy:
        """RSI reversal strategy"""
        rsi_period = np.random.randint(10, 20)
        oversold = np.random.uniform(25, 35)
        overbought = np.random.uniform(65, 75)
        
        return Strategy(
            id=strategy_id,
            name=f"rsi_reversal_{rsi_period}",
            indicators={'rsi': rsi_period},
            timeframe=timeframe,
            session_filter=session,
            entry_conditions={
                'type': 'reversal',
                'oversold_level': oversold,
                'overbought_level': overbought,
                'divergence': np.random.choice([True, False])
            },
            exit_conditions={
                'rsi_extreme': True,
                'stop_loss_pct': np.random.uniform(0.0015, 0.003),  # 15-30 pips
                'take_profit_pct': np.random.uniform(0.003, 0.006)  # 30-60 pips
            },
            parameters={
                'rsi_period': rsi_period,
                'oversold': oversold,
                'overbought': overbought,
                'risk_reward_ratio': np.random.uniform(1.5, 2.5)
            }
        )
    
    def _create_macd_strategy(self, strategy_id: str, timeframe: str, session: str) -> Strategy:
        """MACD strategy"""
        fast = np.random.randint(8, 15)
        slow = np.random.randint(20, 30)
        signal = np.random.randint(7, 12)
        
        return Strategy(
            id=strategy_id,
            name=f"macd_{fast}_{slow}_{signal}",
            indicators={'macd': {'fast': fast, 'slow': slow, 'signal': signal}},
            timeframe=timeframe,
            session_filter=session,
            entry_conditions={
                'type': 'macd_cross',
                'histogram_positive': True,
                'signal_line_cross': True
            },
            exit_conditions={
                'opposite_signal': True,
                'stop_loss_pct': np.random.uniform(0.0015, 0.003),  # 15-30 pips for EURUSD
                'take_profit_pct': np.random.uniform(0.003, 0.006)  # 30-60 pips
            },
            parameters={
                'macd_fast': fast,
                'macd_slow': slow,
                'macd_signal': signal,
                'risk_reward_ratio': np.random.uniform(1.5, 3.0)
            }
        )
    
    def _create_bollinger_strategy(self, strategy_id: str, timeframe: str, session: str) -> Strategy:
        """Bollinger Bands strategy"""
        period = np.random.randint(15, 25)
        std_dev = np.random.uniform(1.8, 2.2)
        
        return Strategy(
            id=strategy_id,
            name=f"bollinger_{period}_{std_dev:.1f}",
            indicators={'bollinger': {'period': period, 'std_dev': std_dev}},
            timeframe=timeframe,
            session_filter=session,
            entry_conditions={
                'type': 'breakout',
                'touch_lower_band': True,
                'price_reversion': np.random.choice([True, False])
            },
            exit_conditions={
                'touch_upper_band': True,
                'middle_band_cross': np.random.choice([True, False]),
                'stop_loss_pct': np.random.uniform(0.0015, 0.003),  # 15-30 pips for EURUSD
                'take_profit_pct': np.random.uniform(0.003, 0.006)  # 30-60 pips
            },
            parameters={
                'bb_period': period,
                'bb_std': std_dev,
                'risk_reward_ratio': np.random.uniform(1.5, 3.0)
            }
        )
    
    def _create_ichimoku_strategy(self, strategy_id: str, timeframe: str, session: str) -> Strategy:
        """Ichimoku strategy"""
        return Strategy(
            id=strategy_id,
            name=f"ichimoku_base",
            indicators={'ichimoku': {'tenkan': 9, 'kijun': 26, 'senkou': 52}},
            timeframe=timeframe,
            session_filter=session,
            entry_conditions={
                'type': 'ichimoku',
                'cloud_above': True,
                'price_above_cloud': True
            },
            exit_conditions={
                'cloud_below': True,
                'stop_loss_pct': np.random.uniform(0.0015, 0.003),  # 15-30 pips
                'take_profit_pct': np.random.uniform(0.003, 0.006)  # 30-60 pips
            },
            parameters={
                'risk_reward_ratio': np.random.uniform(1.5, 2.5)
            }
        )
    
    def _create_sr_strategy(self, strategy_id: str, timeframe: str, session: str) -> Strategy:
        """Support/Resistance strategy"""
        lookback = np.random.randint(20, 50)
        
        return Strategy(
            id=strategy_id,
            name=f"sr_{lookback}",
            indicators={'support_resistance': {'lookback': lookback}},
            timeframe=timeframe,
            session_filter=session,
            entry_conditions={
                'type': 'sr_bounce',
                'bounce_from_support': True,
                'bounce_from_resistance': True
            },
            exit_conditions={
                'break_sr': True,
                'stop_loss_pct': np.random.uniform(0.0015, 0.004),  # 15-40 pips
                'take_profit_pct': np.random.uniform(0.02, 0.06)
            },
            parameters={
                'sr_lookback': lookback,
                'risk_reward_ratio': np.random.uniform(1.5, 3.0)
            }
        )
    
    def _create_volume_strategy(self, strategy_id: str, timeframe: str, session: str) -> Strategy:
        """Volume breakout strategy"""
        volume_period = np.random.randint(10, 30)
        volume_multiplier = np.random.uniform(1.5, 3.0)
        
        return Strategy(
            id=strategy_id,
            name=f"volume_{volume_period}_{volume_multiplier:.1f}",
            indicators={'volume': {'period': volume_period, 'multiplier': volume_multiplier}},
            timeframe=timeframe,
            session_filter=session,
            entry_conditions={
                'type': 'volume_breakout',
                'volume_spike': True,
                'price_confirmation': True
            },
            exit_conditions={
                'volume_normalize': True,
                'stop_loss_pct': np.random.uniform(0.0015, 0.003),  # 15-30 pips for EURUSD
                'take_profit_pct': np.random.uniform(0.003, 0.006)  # 30-60 pips
            },
            parameters={
                'volume_period': volume_period,
                'volume_multiplier': volume_multiplier,
                'risk_reward_ratio': np.random.uniform(1.5, 3.0)
            }
        )
    
    def _create_atr_strategy(self, strategy_id: str, timeframe: str, session: str) -> Strategy:
        """ATR-based range strategy"""
        atr_period = np.random.randint(10, 20)
        atr_multiplier = np.random.uniform(1.5, 2.5)
        
        return Strategy(
            id=strategy_id,
            name=f"atr_{atr_period}_{atr_multiplier:.1f}",
            indicators={'atr': {'period': atr_period, 'multiplier': atr_multiplier}},
            timeframe=timeframe,
            session_filter=session,
            entry_conditions={
                'type': 'atr_range',
                'range_breakout': True
            },
            exit_conditions={
                'range_reversion': True,
                'stop_loss_atr': atr_multiplier,
                'take_profit_atr': atr_multiplier * np.random.uniform(1.5, 2.5)
            },
            parameters={
                'atr_period': atr_period,
                'atr_multiplier': atr_multiplier,
                'risk_reward_ratio': np.random.uniform(1.5, 3.0)
            }
        )
    
    def _create_multi_indicator_strategy(self, strategy_id: str, timeframe: str, session: str) -> Strategy:
        """Multi-indicator combination strategy"""
        num_indicators = np.random.randint(2, 4)
        selected = np.random.choice(['ema', 'rsi', 'macd', 'bollinger'], num_indicators, replace=False)
        
        indicators = {}
        for ind in selected:
            if ind == 'ema':
                indicators['ema'] = np.random.randint(10, 50)
            elif ind == 'rsi':
                indicators['rsi'] = np.random.randint(10, 20)
            elif ind == 'macd':
                indicators['macd'] = {'fast': 12, 'slow': 26, 'signal': 9}
            elif ind == 'bollinger':
                indicators['bollinger'] = {'period': 20, 'std_dev': 2.0}
        
        return Strategy(
            id=strategy_id,
            name=f"multi_{'_'.join(selected)}",
            indicators=indicators,
            timeframe=timeframe,
            session_filter=session,
            entry_conditions={
                'type': 'multi_indicator',
                'required_agreement': num_indicators - 1,
                'indicators': list(selected)
            },
            exit_conditions={
                'any_indicator_reverse': True,
                'stop_loss_pct': np.random.uniform(0.0015, 0.003),  # 15-30 pips for EURUSD
                'take_profit_pct': np.random.uniform(0.003, 0.006)  # 30-60 pips
            },
            parameters={
                'indicators': list(selected),
                'risk_reward_ratio': np.random.uniform(1.5, 3.0)
            }
        )
    
    def _generate_id(self, strategy_type: str, params: Dict) -> str:
        """Generate unique strategy ID"""
        param_str = json.dumps(params, sort_keys=True)
        hash_obj = hashlib.md5(f"{strategy_type}_{param_str}".encode())
        return f"{strategy_type}_{hash_obj.hexdigest()[:8]}"
    
    def generate_batch(self, num_strategies: int) -> List[Strategy]:
        """Generate a batch of strategies"""
        strategies = []
        
        for i in range(num_strategies):
            strategy = self.generate_strategy()
            strategies.append(strategy)
            
            if (i + 1) % 1000 == 0:
                logger.info(f"Generated {i + 1} strategies...")
        
        self.generated_strategies.extend(strategies)
        logger.info(f"Generated {len(strategies)} strategies")
        return strategies

