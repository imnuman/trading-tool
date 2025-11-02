#!/usr/bin/env python3
"""
Pre-Deployment Script (Day 0)
1. Collect full historical data
2. Generate infinite strategies
3. Pre-simulate backtests
4. Filter and store top strategies
"""

import sys
import os
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.data_fetcher import DataFetcher
from src.strategies.strategy_generator import StrategyGenerator
from src.strategies.strategy_filter import StrategyFilter
from src.backtesting.backtest_engine import BacktestEngine
from src.utils.database import StrategyDatabase

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main pre-deployment function"""
    logger.info("=" * 60)
    logger.info("Starting Pre-Deployment (Day 0)")
    logger.info("=" * 60)
    
    # Initialize components
    data_fetcher = DataFetcher()
    strategy_generator = StrategyGenerator(max_strategies=50000)  # Generate 50k strategies
    strategy_filter = StrategyFilter(
        min_sharpe=0.5,
        max_drawdown=0.25,
        min_trades=10,
        min_win_rate=0.50,
        min_profit_factor=1.2,
        min_confidence=60.0
    )
    db = StrategyDatabase()
    
    # Step 1: Collect historical data
    logger.info("\n[Step 1/4] Collecting historical data...")
    # Use daily data for 5y period (1h data limited to 730 days by yfinance)
    # For production, you might want to fetch 1h data separately for recent period
    all_data = data_fetcher.fetch_all_pairs(period='5y', interval='1d')
    
    if not all_data:
        logger.error("Failed to fetch data. Exiting.")
        return
    
    logger.info(f"Fetched data for {len(all_data)} pairs")
    
    # Use first dataset for strategy generation
    data_key = list(all_data.keys())[0]
    main_data = all_data[data_key]
    logger.info(f"Using {data_key} as main dataset ({len(main_data)} rows)")
    
    # Step 2: Generate strategies
    logger.info("\n[Step 2/4] Generating strategies...")
    # Start with smaller batch for faster testing - increase to 10000+ for production
    num_strategies = 1000  # Start with 1k strategies for testing
    strategies = strategy_generator.generate_batch(num_strategies)
    logger.info(f"Generated {len(strategies)} strategies")
    
    # Step 3: Backtest all strategies
    logger.info("\n[Step 3/4] Backtesting strategies...")
    backtest_engine = BacktestEngine(main_data)
    results = []
    
    for i, strategy in enumerate(strategies):
        if (i + 1) % 100 == 0:
            logger.info(f"Backtested {i + 1}/{len(strategies)} strategies...")
        
        result = backtest_engine.backtest_strategy(strategy)
        results.append(result)
        
        # Save strategy and result to database
        db.save_strategy(strategy)
        db.save_backtest_result(result)
    
    logger.info(f"Backtested {len(results)} strategies")
    
    # Step 4: Filter strategies
    logger.info("\n[Step 4/4] Filtering strategies...")
    filtered_results = strategy_filter.filter_strategies(results)
    
    logger.info(f"Filtered to {len(filtered_results)} high-performing strategies")
    
    # Get top strategies
    top_strategies = sorted(
        filtered_results, 
        key=lambda x: x.confidence_score, 
        reverse=True
    )[:1000]  # Top 1000 strategies
    
    logger.info(f"Selected top {len(top_strategies)} strategies for ensemble")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Pre-Deployment Complete!")
    logger.info("=" * 60)
    logger.info(f"Data pairs collected: {len(all_data)}")
    logger.info(f"Strategies generated: {len(strategies)}")
    logger.info(f"Strategies backtested: {len(results)}")
    logger.info(f"Strategies filtered: {len(filtered_results)}")
    logger.info(f"Top strategies selected: {len(top_strategies)}")
    
    if top_strategies:
        avg_confidence = sum(s.confidence_score for s in top_strategies) / len(top_strategies)
        avg_win_rate = sum(s.win_rate for s in top_strategies) / len(top_strategies)
        logger.info(f"Average confidence: {avg_confidence:.1f}%")
        logger.info(f"Average win rate: {avg_win_rate*100:.1f}%")
    
    logger.info("\n✅ Ready for Day 1 deployment!")


if __name__ == "__main__":
    main()

