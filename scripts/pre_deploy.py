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
    
    # CRITICAL: Split data into train/test (80/20) to prevent overfitting
    split_idx = int(len(main_data) * 0.8)
    train_data = main_data.iloc[:split_idx].copy()
    test_data = main_data.iloc[split_idx:].copy()
    
    logger.info(f"Data split: {len(train_data)} rows for training, {len(test_data)} rows for testing")
    logger.info(f"Train period: {train_data.index[0]} to {train_data.index[-1]}")
    logger.info(f"Test period: {test_data.index[0]} to {test_data.index[-1]}")
    
    # Step 2: Generate strategies
    logger.info("\n[Step 2/4] Generating strategies...")
    # Start with smaller batch for faster testing - increase to 10000+ for production
    num_strategies = 1000  # Start with 1k strategies for testing
    strategies = strategy_generator.generate_batch(num_strategies)
    logger.info(f"Generated {len(strategies)} strategies")
    
    # Step 3: Backtest all strategies on TRAINING DATA ONLY
    logger.info("\n[Step 3/4] Backtesting strategies on TRAINING data...")
    logger.info("⚠️  Using training data only - test data will be used for validation later")
    train_engine = BacktestEngine(train_data)
    results = []
    
    for i, strategy in enumerate(strategies):
        if (i + 1) % 100 == 0:
            logger.info(f"Backtested {i + 1}/{len(strategies)} strategies...")
        
        # Backtest on TRAINING data only
        result = train_engine.backtest_strategy(strategy)
        results.append(result)
        
        # Save strategy and result to database
        db.save_strategy(strategy)
        db.save_backtest_result(result)
    
    logger.info(f"Backtested {len(results)} strategies")
    
    # Step 4: Filter strategies based on TRAINING performance
    logger.info("\n[Step 4/4] Filtering strategies based on training performance...")
    filtered_results = strategy_filter.filter_strategies(results)
    
    logger.info(f"Filtered to {len(filtered_results)} high-performing strategies on training data")
    
    # Step 4b: VALIDATE on TEST data (out-of-sample)
    logger.info("\n[Step 4b/4] Validating filtered strategies on TEST data (out-of-sample)...")
    test_engine = BacktestEngine(test_data)
    test_results = []
    
    # Create mapping of strategy_id to strategy
    strategy_map = {s.id: s for s in strategies}
    
    # Get filtered strategy IDs
    filtered_ids = {r.strategy_id for r in filtered_results}
    
    # Test filtered strategies on unseen test data
    validated_results = []
    for result in filtered_results:
        if result.strategy_id in strategy_map:
            strategy = strategy_map[result.strategy_id]
            test_result = test_engine.backtest_strategy(strategy)
            
            # Compare training vs test performance
            train_wr = result.win_rate
            test_wr = test_result.win_rate
            decay = test_wr / train_wr if train_wr > 0 else 0
            
            logger.debug(
                f"Strategy {result.strategy_id[:20]}: "
                f"Train WR={train_wr:.2%}, Test WR={test_wr:.2%}, Decay={decay:.2f}"
            )
            
            # Only keep strategies where test performance is within 15% of training
            if decay >= 0.85:
                validated_results.append(result)
                test_results.append(test_result)
    
    logger.info(
        f"Validation complete: {len(validated_results)}/{len(filtered_results)} strategies "
        f"passed out-of-sample test (decay >= 0.85)"
    )
    
    # Get top strategies from VALIDATED results
    top_strategies = sorted(
        validated_results, 
        key=lambda x: x.confidence_score, 
        reverse=True
    )[:1000]  # Top 1000 strategies
    
    logger.info(f"Selected top {len(top_strategies)} VALIDATED strategies for ensemble")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Pre-Deployment Complete!")
    logger.info("=" * 60)
    logger.info(f"Data pairs collected: {len(all_data)}")
    logger.info(f"Strategies generated: {len(strategies)}")
    logger.info(f"Strategies backtested (train): {len(results)}")
    logger.info(f"Strategies filtered (train): {len(filtered_results)}")
    logger.info(f"Strategies validated (test): {len(validated_results)}")
    logger.info(f"Top validated strategies selected: {len(top_strategies)}")
    
    if top_strategies and test_results:
        avg_train_wr = sum(s.win_rate for s in top_strategies) / len(top_strategies)
        avg_test_wr = sum(t.win_rate for t in test_results[:len(top_strategies)]) / len(top_strategies)
        avg_confidence = sum(s.confidence_score for s in top_strategies) / len(top_strategies)
        
        logger.info(f"\n📊 PERFORMANCE METRICS:")
        logger.info(f"  Training Win Rate: {avg_train_wr*100:.1f}%")
        logger.info(f"  Test (Out-of-Sample) Win Rate: {avg_test_wr*100:.1f}%")
        logger.info(f"  Performance Decay: {(avg_test_wr/avg_train_wr if avg_train_wr > 0 else 0)*100:.1f}%")
        logger.info(f"  Average Confidence: {avg_confidence:.1f}%")
        
        if avg_test_wr / avg_train_wr < 0.85:
            logger.warning("⚠️  WARNING: Significant performance decay detected! System may be overfit.")
    
    logger.info("\n✅ Ready for Day 1 deployment!")


if __name__ == "__main__":
    main()

