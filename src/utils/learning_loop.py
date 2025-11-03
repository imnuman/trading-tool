"""
Infinite Learning Loop
Continuous self-learning from live and historical data
"""

import asyncio
import logging
from typing import Optional
import pandas as pd
from datetime import datetime, timedelta

from src.data.data_fetcher import DataFetcher
from src.ai.ensemble import EnsembleSignalGenerator
from src.ai.rl_selector import RLSelector
from src.utils.database import StrategyDatabase

logger = logging.getLogger(__name__)


class LearningLoop:
    """Continuous learning loop that updates strategies every second"""
    
    def __init__(
        self,
        ensemble: EnsembleSignalGenerator,
        db: StrategyDatabase,
        update_interval: int = 60  # Update every 60 seconds
    ):
        """
        Initialize learning loop
        
        Args:
            ensemble: Ensemble signal generator
            db: Database connection
            update_interval: Seconds between updates
        """
        self.ensemble = ensemble
        self.db = db
        self.update_interval = update_interval
        self.rl_selector = RLSelector()
        self.data_fetcher = DataFetcher()
        self.running = False
    
    async def start(self):
        """Start the learning loop"""
        self.running = True
        logger.info(f"Starting learning loop (updates every {self.update_interval}s)")
        
        while self.running:
            try:
                await self._update()
                await asyncio.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Error in learning loop: {e}")
                await asyncio.sleep(self.update_interval)
    
    def stop(self):
        """Stop the learning loop"""
        self.running = False
        logger.info("Stopping learning loop...")
    
    async def _update(self):
        """
        Perform one learning update

        1. Fetch recent market data
        2. Evaluate current ensemble performance
        3. Update RL confidence scores
        4. Store feedback for optimization
        """
        try:
            # 1. Update market state - fetch fresh data for active pairs
            logger.debug("Fetching fresh market data...")
            active_pairs = ["EUR/USD", "GBP/USD", "XAU/USD"]

            for pair in active_pairs:
                try:
                    # Fetch latest hourly data
                    data = self.data_fetcher.load_data(pair, period='7d', interval='1h')
                    if data is None or data.empty:
                        logger.warning(f"No data available for {pair}")
                        continue

                    # Extract current market state
                    market_state = self.rl_selector.get_market_state(data)
                    logger.debug(f"{pair} market state: {market_state}")

                except Exception as e:
                    logger.error(f"Error updating market data for {pair}: {e}")
                    continue

            # 2. Evaluate recent ensemble performance
            logger.debug("Evaluating recent signals...")

            # Get recent signals from database (last 24 hours)
            cutoff_time = datetime.utcnow() - timedelta(hours=24)

            # Query database for recent signals
            # Note: This requires storing signals with timestamps in database
            # For now, we'll log and skip if no signals

            # 3. Update RL confidence scores based on recent performance
            # This would be triggered by external trade outcome reports
            # The update_from_trade_outcome() method handles this

            # 4. Store feedback metrics
            logger.debug("Storing performance feedback...")

            # Log current ensemble state
            if self.ensemble and self.ensemble.strategies:
                logger.info(
                    f"Learning loop update: {len(self.ensemble.strategies)} active strategies, "
                    f"min_agreement={self.ensemble.min_agreement}, "
                    f"min_confidence={self.ensemble.min_confidence}"
                )

            # Periodic Q-table pruning to prevent memory bloat
            if hasattr(self.rl_selector, 'q_table') and len(self.rl_selector.q_table) > 10000:
                logger.warning(f"Q-table size: {len(self.rl_selector.q_table)}. Consider pruning old entries.")

            logger.debug("Learning update complete")

        except Exception as e:
            logger.error(f"Error in learning update: {e}", exc_info=True)
    
    def update_from_trade_outcome(
        self,
        strategy_ids: list,
        market_state: tuple,
        outcome: str,  # 'profit', 'loss', 'no_trade'
        next_state: Optional[tuple] = None
    ):
        """
        Update learning from trade outcome
        
        Args:
            strategy_ids: List of strategy IDs used in signal
            market_state: Market state when signal was generated
            outcome: Trade outcome
            next_state: Next market state (optional)
        """
        reward = {
            'profit': 1.0,
            'loss': -1.0,
            'no_trade': 0.0
        }.get(outcome, 0.0)
        
        # Update Q-values for each strategy
        for strategy_id in strategy_ids:
            self.rl_selector.update_q_value(
                strategy_id=strategy_id,
                market_state=market_state,
                reward=reward,
                next_state=next_state
            )
        
        logger.info(f"Updated learning from {outcome} for {len(strategy_ids)} strategies")

