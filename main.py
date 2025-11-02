#!/usr/bin/env python3
"""
Main entry point for Trading Tool
Telegram-interfaced AI trading system
"""

import asyncio
import logging
from dotenv import load_dotenv
import os
import json

from src.telegram.bot import TradingBot
from src.ai.ensemble import EnsembleSignalGenerator
from src.strategies.strategy_generator import Strategy
from src.utils.database import StrategyDatabase
from src.utils.learning_loop import LearningLoop

# Load environment variables
load_dotenv('config/secrets.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def initialize_ensemble(db: StrategyDatabase) -> EnsembleSignalGenerator:
    """Initialize ensemble from database"""
    logger.info("Loading top strategies from database...")
    # Lower thresholds to match actual strategy performance
    # Can be adjusted based on your requirements
    top_strategies_data = db.get_top_strategies(min_confidence=50.0, min_trades=1, limit=100)
    
    if not top_strategies_data:
        logger.warning("No strategies found in database. Please run pre_deploy.py first.")
        return None
    
    logger.info(f"Loaded {len(top_strategies_data)} strategies from database")
    
    # Convert database entries back to Strategy objects
    strategies = []
    for strat_data in top_strategies_data[:50]:  # Use top 50 for ensemble
        strategy = Strategy(
            id=strat_data['id'],
            name=strat_data['name'],
            indicators=strat_data['indicators'],
            timeframe=strat_data['timeframe'],
            session_filter=strat_data['session_filter'],
            entry_conditions=strat_data['entry_conditions'],
            exit_conditions=strat_data['exit_conditions'],
            parameters=strat_data['parameters']
        )
        strategies.append(strategy)
    
    ensemble = EnsembleSignalGenerator(
        strategies=strategies,
        min_agreement=0.80,
        min_confidence=80.0
    )
    
    logger.info(f"Ensemble initialized with {len(strategies)} strategies")
    return ensemble


async def main():
    """Main function to start the Telegram bot"""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN not found in config/secrets.env")
        logger.error("Please create config/secrets.env and add your Telegram bot token")
        return
    
    logger.info("Starting Trading Tool Telegram Bot...")
    
    # Initialize database and ensemble
    db = StrategyDatabase()
    ensemble = initialize_ensemble(db)
    
    if ensemble is None:
        logger.error("Failed to initialize ensemble. Cannot start bot.")
        logger.error("Please run: python scripts/pre_deploy.py")
        return
    
    # Initialize and start bot
    bot = TradingBot(bot_token)
    bot.set_ensemble(ensemble)

    # Initialize learning loop (optional - runs in background)
    learning_loop = LearningLoop(
        ensemble=ensemble,
        db=db,
        update_interval=3600  # Update every hour
    )

    # Start learning loop in background
    learning_task = asyncio.create_task(learning_loop.start())
    logger.info("✅ Learning loop started in background")

    logger.info("✅ Bot initialized and ready!")

    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        learning_loop.stop()
        await learning_task


if __name__ == "__main__":
    asyncio.run(main())

