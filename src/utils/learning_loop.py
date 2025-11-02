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
        """Perform one learning update"""
        logger.debug("Running learning update...")
        
        # 1. Update market state
        # (In production, fetch live data here)
        # For now, use historical data
        
        # 2. Evaluate current ensemble performance
        # (Check recent signals and outcomes)
        
        # 3. Update RL confidence scores
        # (Based on recent performance)
        
        # 4. Store feedback for optimization
        # (Save performance metrics)
        
        logger.debug("Learning update complete")
    
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

