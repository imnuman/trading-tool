"""
Telegram Bot Interface
Handles /signal, /chart, /stats, /help commands
"""

import asyncio
import logging
from typing import Optional
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from datetime import datetime
import json

import pandas as pd
from src.ai.ensemble import EnsembleSignalGenerator
from src.utils.database import StrategyDatabase
from src.data.data_fetcher import DataFetcher

logger = logging.getLogger(__name__)


class TradingBot:
    """Telegram bot for trading signals"""
    
    def __init__(self, bot_token: str):
        """
        Initialize Telegram bot
        
        Args:
            bot_token: Telegram bot token
        """
        self.bot_token = bot_token
        self.application = Application.builder().token(bot_token).build()
        self.db = StrategyDatabase()
        self.data_fetcher = DataFetcher()
        self.ensemble: Optional[EnsembleSignalGenerator] = None
        
        # Register command handlers
        self.application.add_handler(CommandHandler("signal", self.signal_command))
        self.application.add_handler(CommandHandler("chart", self.chart_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("start", self.start_command))
    
    async def start(self):
        """Start the bot"""
        logger.info("Starting Telegram bot...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        logger.info("Telegram bot is running. Press Ctrl+C to stop.")
        
        # Keep running
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info("Stopping bot...")
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = """
🤖 *Trading Tool AI Bot*

Welcome! I'm your AI-powered trading assistant.

*Available Commands:*
/signal - Get high-confidence trading signal
/chart <pair> - Get chart analysis (USD, GBP, Gold)
/stats - View performance statistics
/help - Show detailed help

Ready to provide trading signals with ≥80% confidence!
        """
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def signal_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /signal command"""
        try:
            if self.ensemble is None:
                await update.message.reply_text(
                    "⚠️ Ensemble not initialized. Please run pre-deployment first."
                )
                return
            
            # Get current data
            # For now, use USD as default
            data = self.data_fetcher.load_data("USD_EURUSD")
            if data is None or data.empty:
                await update.message.reply_text(
                    "⚠️ No data available. Please run data collection first."
                )
                return
            
            current_price = float(data['close'].iloc[-1])
            
            # Generate signal
            signal = self.ensemble.generate_signal(data, current_price, "USD")
            
            if signal is None:
                await update.message.reply_text(
                    "❌ *No Trade*\n\n"
                    "Current market conditions do not meet the ≥80% confidence threshold. "
                    "The ensemble did not reach consensus for a high-probability trade.",
                    parse_mode='Markdown'
                )
                return
            
            # Format signal message
            signal_message = self._format_signal(signal)
            await update.message.reply_text(signal_message, parse_mode='Markdown')
            
            # Save signal to database
            self.db.save_signal(signal)
            
        except Exception as e:
            logger.error(f"Error in signal_command: {e}")
            await update.message.reply_text(f"❌ Error generating signal: {str(e)}")
    
    def _format_signal(self, signal: dict) -> str:
        """Format signal as Telegram message"""
        direction_emoji = "📈" if signal['direction'] == 'buy' else "📉"
        confidence_emoji = "🟢" if signal['confidence'] >= 85 else "🟡" if signal['confidence'] >= 80 else "🟠"
        
        message = f"""
{confidence_emoji} *Trading Signal*

*Pair:* {signal['pair']}
*Direction:* {direction_emoji} {signal['direction'].upper()}
*Confidence:* {signal['confidence']:.1f}%

*Entry Zone:* {signal['entry_zone'][0]:.5f} - {signal['entry_zone'][1]:.5f}
*Stop Loss:* {signal['stop_loss']:.5f}
*Take Profit:* {signal['take_profit']:.5f}

*Ensemble Agreement:* {signal['agreement']*100:.1f}%
*Strategies Used:* {len(signal['strategies_used'])}
*Time:* {signal['timestamp']}

⚠️ *For Human Execution Only*
This signal is ready for you to execute manually.
        """
        return message
    
    async def chart_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /chart command"""
        try:
            args = context.args
            
            if not args:
                await update.message.reply_text(
                    "Usage: /chart <pair>\n"
                    "Example: /chart USD\n"
                    "Available pairs: USD, GBP, Gold"
                )
                return
            
            pair = args[0].upper()
            
            # Load data
            data_key = f"{pair}_EURUSD" if pair == "USD" else f"{pair}_GBPUSD"
            data = self.data_fetcher.load_data(data_key)
            
            if data is None or data.empty:
                await update.message.reply_text(
                    f"⚠️ No data available for {pair}. Please run data collection first."
                )
                return
            
            # Generate analysis
            analysis = self._analyze_chart(data, pair)
            await update.message.reply_text(analysis, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in chart_command: {e}")
            await update.message.reply_text(f"❌ Error analyzing chart: {str(e)}")
    
    def _analyze_chart(self, data: pd.DataFrame, pair: str) -> str:
        """Analyze chart and return insights"""
        recent = data.tail(100)
        current_price = float(recent['close'].iloc[-1])
        
        # Calculate support/resistance
        high_price = float(recent['high'].max())
        low_price = float(recent['low'].min())
        
        # Trend analysis
        sma_short = recent['close'].rolling(10).mean().iloc[-1]
        sma_long = recent['close'].rolling(30).mean().iloc[-1]
        trend = "Bullish 📈" if sma_short > sma_long else "Bearish 📉"
        
        # Volatility
        volatility = float(recent['volatility'].iloc[-1]) * 100 if 'volatility' in recent.columns else 0
        
        message = f"""
📊 *Chart Analysis: {pair}*

*Current Price:* {current_price:.5f}
*Trend:* {trend}

*Support Level:* {low_price:.5f}
*Resistance Level:* {high_price:.5f}
*Volatility:* {volatility:.2f}%

*Recent Range:* {low_price:.5f} - {high_price:.5f}

*Last Updated:* {recent.index[-1]}
        """
        return message
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        try:
            # Get top strategies
            top_strategies = self.db.get_top_strategies(limit=10)
            
            if not top_strategies:
                await update.message.reply_text(
                    "⚠️ No strategies available. Please run pre-deployment first."
                )
                return
            
            # Calculate aggregate stats
            avg_win_rate = sum(s['win_rate'] for s in top_strategies) / len(top_strategies)
            avg_sharpe = sum(s['sharpe_ratio'] for s in top_strategies) / len(top_strategies)
            avg_confidence = sum(s['confidence_score'] for s in top_strategies) / len(top_strategies)
            
            message = f"""
📊 *Performance Statistics*

*Ensemble Performance:*
• Average Win Rate: {avg_win_rate*100:.1f}%
• Average Sharpe Ratio: {avg_sharpe:.2f}
• Average Confidence: {avg_confidence:.1f}%

*Top Strategies:*
            """
            
            for i, strat in enumerate(top_strategies[:5], 1):
                message += f"""
{i}. {strat['name']}
   • Confidence: {strat['confidence_score']:.1f}%
   • Win Rate: {strat['win_rate']*100:.1f}%
   • Sharpe: {strat['sharpe_ratio']:.2f}
                """
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in stats_command: {e}")
            await update.message.reply_text(f"❌ Error getting statistics: {str(e)}")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
📖 *Trading Tool Bot Help*

*Commands:*

/signal
Get a high-confidence trading signal or "no trade" message.
Signals require ≥80% ensemble agreement and high confidence.

/chart <pair>
Get live/historical chart analysis for a trading pair.
Available pairs: USD, GBP, Gold
Example: /chart USD

/stats
View ensemble performance statistics including:
• Win rates
• Sharpe ratios
• Top performing strategies

/help
Show this help message

*About Signals:*
Signals include:
• Entry zone
• Stop loss level
• Take profit level
• Confidence score
• Strategies used

⚠️ All trades are for human execution only.
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    def set_ensemble(self, ensemble: EnsembleSignalGenerator):
        """Set the ensemble generator"""
        self.ensemble = ensemble

