"""
Walk-Forward Optimization
Prevents overfitting by testing strategies on unseen data
"""

import pandas as pd
import numpy as np
from typing import List, Tuple, Dict
import logging
from datetime import datetime, timedelta

from src.backtesting.backtest_engine import BacktestEngine, BacktestResult
from src.strategies.strategy_generator import Strategy

logger = logging.getLogger(__name__)


class WalkForwardOptimizer:
    """
    Walk-forward optimization splits data into training and validation periods
    Tests strategy on training data, validates on unseen validation data
    Rolls forward to test across multiple periods
    """
    
    def __init__(
        self,
        train_period_days: int = 365 * 2,  # 2 years training
        validation_period_days: int = 180,  # 6 months validation
        step_days: int = 90,  # Roll forward every 3 months
        min_periods: int = 3  # Minimum number of periods to validate
    ):
        """
        Initialize walk-forward optimizer
        
        Args:
            train_period_days: Length of training window in days
            validation_period_days: Length of validation window in days
            step_days: Days to step forward for each walk
            min_periods: Minimum number of validation periods required
        """
        self.train_period_days = train_period_days
        self.validation_period_days = validation_period_days
        self.step_days = step_days
        self.min_periods = min_periods
    
    def generate_windows(
        self, 
        data: pd.DataFrame
    ) -> List[Tuple[pd.DataFrame, pd.DataFrame, pd.Timestamp, pd.Timestamp]]:
        """
        Generate training and validation windows for walk-forward
        
        Args:
            data: Full historical dataframe with datetime index
        
        Returns:
            List of tuples: (train_data, validation_data, train_start, validation_end)
        """
        if data.empty or len(data) < (self.train_period_days + self.validation_period_days):
            logger.warning(f"Not enough data for walk-forward. Need at least "
                         f"{self.train_period_days + self.validation_period_days} days")
            return []
        
        windows = []
        data = data.sort_index()
        start_date = data.index[0]
        end_date = data.index[-1]
        
        current_train_start = start_date
        current_train_end = current_train_start + pd.Timedelta(days=self.train_period_days)
        current_validation_start = current_train_end
        current_validation_end = current_validation_start + pd.Timedelta(days=self.validation_period_days)
        
        period = 0
        while current_validation_end <= end_date:
            # Get data for this window
            train_data = data[
                (data.index >= current_train_start) & 
                (data.index < current_train_end)
            ].copy()
            
            validation_data = data[
                (data.index >= current_validation_start) & 
                (data.index < current_validation_end)
            ].copy()
            
            if len(train_data) > 100 and len(validation_data) > 20:  # Minimum data points
                windows.append((
                    train_data,
                    validation_data,
                    current_train_start,
                    current_validation_end
                ))
                period += 1
                logger.debug(
                    f"Period {period}: Train {current_train_start.date()} to "
                    f"{current_train_end.date()}, Validate {current_validation_start.date()} to "
                    f"{current_validation_end.date()}"
                )
            
            # Step forward
            current_train_start += pd.Timedelta(days=self.step_days)
            current_train_end = current_train_start + pd.Timedelta(days=self.train_period_days)
            current_validation_start = current_train_end
            current_validation_end = current_validation_start + pd.Timedelta(days=self.validation_period_days)
        
        logger.info(f"Generated {len(windows)} walk-forward periods")
        return windows
    
    def walk_forward_backtest(
        self,
        strategy: Strategy,
        data: pd.DataFrame
    ) -> Dict:
        """
        Run walk-forward backtest on a strategy
        
        Args:
            strategy: Strategy to test
            data: Full historical data
        
        Returns:
            Dictionary with walk-forward results
        """
        windows = self.generate_windows(data)
        
        if not windows:
            return {
                'strategy_id': strategy.id,
                'walk_forward_valid': False,
                'avg_train_win_rate': 0.0,
                'avg_validation_win_rate': 0.0,
                'win_rate_decay': 1.0,
                'periods': 0,
                'consistency_score': 0.0
            }
        
        train_results = []
        validation_results = []
        period_scores = []
        
        for train_data, validation_data, train_start, val_end in windows:
            # Backtest on training data
            train_engine = BacktestEngine(train_data)
            train_result = train_engine.backtest_strategy(strategy)
            train_results.append(train_result)
            
            # Backtest on validation data (unseen)
            val_engine = BacktestEngine(validation_data)
            val_result = val_engine.backtest_strategy(strategy)
            validation_results.append(val_result)
            
            # Calculate period score (validation performance relative to training)
            if train_result.total_trades > 0 and val_result.total_trades > 0:
                train_wr = train_result.win_rate
                val_wr = val_result.win_rate
                # Consistency: validation should be close to training
                consistency = 1.0 - abs(train_wr - val_wr)
                period_scores.append(consistency)
        
        if not train_results or not validation_results:
            return {
                'strategy_id': strategy.id,
                'walk_forward_valid': False,
                'avg_train_win_rate': 0.0,
                'avg_validation_win_rate': 0.0,
                'win_rate_decay': 1.0,
                'periods': 0,
                'consistency_score': 0.0
            }
        
        # Calculate aggregate metrics
        avg_train_wr = np.mean([r.win_rate for r in train_results if r.total_trades > 0])
        avg_val_wr = np.mean([r.win_rate for r in validation_results if r.total_trades > 0])
        
        # Win rate decay (how much validation underperforms training)
        if avg_train_wr > 0:
            win_rate_decay = avg_val_wr / avg_train_wr
        else:
            win_rate_decay = 0.0
        
        # Consistency score (how stable performance is across periods)
        consistency_score = np.mean(period_scores) if period_scores else 0.0
        
        # Validation criteria: Strategy is valid if:
        # 1. Validation win rate is within 15% of training (decay > 0.85)
        # 2. Consistency score > 0.7 (stable across periods)
        # 3. Minimum number of periods tested
        is_valid = (
            len(windows) >= self.min_periods and
            win_rate_decay >= 0.85 and
            consistency_score >= 0.70 and
            avg_val_wr >= 0.45  # Minimum acceptable validation win rate
        )
        
        result = {
            'strategy_id': strategy.id,
            'walk_forward_valid': is_valid,
            'avg_train_win_rate': avg_train_wr,
            'avg_validation_win_rate': avg_val_wr,
            'win_rate_decay': win_rate_decay,
            'periods': len(windows),
            'consistency_score': consistency_score,
            'train_sharpe': np.mean([r.sharpe_ratio for r in train_results]),
            'validation_sharpe': np.mean([r.sharpe_ratio for r in validation_results]),
            'train_max_dd': np.mean([r.max_drawdown for r in train_results]),
            'validation_max_dd': np.mean([r.max_drawdown for r in validation_results])
        }
        
        logger.info(
            f"Walk-forward for {strategy.id}: "
            f"Train WR={avg_train_wr:.2%}, Val WR={avg_val_wr:.2%}, "
            f"Decay={win_rate_decay:.2f}, Valid={is_valid}"
        )
        
        return result
    
    def filter_strategies_by_walk_forward(
        self,
        strategies: List[Strategy],
        data: pd.DataFrame,
        results: List[BacktestResult]
    ) -> Tuple[List[Strategy], List[BacktestResult], List[Dict]]:
        """
        Filter strategies using walk-forward validation
        
        Args:
            strategies: List of strategies
            data: Historical data
            results: Original backtest results
        
        Returns:
            Tuple of (filtered_strategies, filtered_results, walk_forward_metrics)
        """
        logger.info(f"Running walk-forward validation on {len(strategies)} strategies...")
        
        # Create mapping of strategy_id to result
        result_map = {r.strategy_id: r for r in results}
        
        walk_forward_metrics = []
        valid_strategies = []
        valid_results = []
        
        for i, strategy in enumerate(strategies):
            if (i + 1) % 100 == 0:
                logger.info(f"Walk-forward validated {i + 1}/{len(strategies)} strategies...")
            
            wf_result = self.walk_forward_backtest(strategy, data)
            walk_forward_metrics.append(wf_result)
            
            # Only keep strategies that pass walk-forward validation
            if wf_result['walk_forward_valid']:
                valid_strategies.append(strategy)
                if strategy.id in result_map:
                    valid_results.append(result_map[strategy.id])
        
        logger.info(
            f"Walk-forward filtered {len(strategies)} strategies down to {len(valid_strategies)} "
            f"({len(valid_strategies)/len(strategies)*100:.1f}% pass rate)"
        )
        
        return valid_strategies, valid_results, walk_forward_metrics

