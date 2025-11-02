"""
Strategy Filtering System
Filters low-confidence strategies based on performance metrics
"""

import logging
from typing import List
from src.backtesting.backtest_engine import BacktestResult

logger = logging.getLogger(__name__)


class StrategyFilter:
    """Filters strategies based on performance criteria"""
    
    def __init__(
        self,
        min_sharpe: float = 0.5,
        max_drawdown: float = 0.25,
        min_trades: int = 10,
        min_win_rate: float = 0.50,
        min_profit_factor: float = 1.2,
        min_confidence: float = 60.0
    ):
        """
        Initialize strategy filter
        
        Args:
            min_sharpe: Minimum Sharpe ratio
            max_drawdown: Maximum acceptable drawdown
            min_trades: Minimum number of trades for statistical significance
            min_win_rate: Minimum win rate (0-1)
            min_profit_factor: Minimum profit factor
            min_confidence: Minimum confidence score (0-100)
        """
        self.min_sharpe = min_sharpe
        self.max_drawdown = max_drawdown
        self.min_trades = min_trades
        self.min_win_rate = min_win_rate
        self.min_profit_factor = min_profit_factor
        self.min_confidence = min_confidence
    
    def filter_strategies(self, results: List[BacktestResult]) -> List[BacktestResult]:
        """
        Filter strategies based on criteria
        
        Args:
            results: List of backtest results
        
        Returns:
            Filtered list of high-performing strategies
        """
        filtered = []
        
        for result in results:
            if self._passes_filter(result):
                filtered.append(result)
            else:
                logger.debug(
                    f"Filtered out strategy {result.strategy_id}: "
                    f"Sharpe={result.sharpe_ratio:.2f}, "
                    f"Drawdown={result.max_drawdown:.2f}, "
                    f"Trades={result.total_trades}, "
                    f"Confidence={result.confidence_score:.1f}"
                )
        
        logger.info(f"Filtered {len(results)} strategies down to {len(filtered)}")
        return filtered
    
    def _passes_filter(self, result: BacktestResult) -> bool:
        """Check if strategy passes all filter criteria"""
        checks = [
            result.sharpe_ratio >= self.min_sharpe,
            result.max_drawdown <= self.max_drawdown,
            result.total_trades >= self.min_trades,
            result.win_rate >= self.min_win_rate,
            result.profit_factor >= self.min_profit_factor,
            result.confidence_score >= self.min_confidence
        ]
        
        return all(checks)

