"""
Telegram Bot Interface
Handles commands and automatic notifications for trading signals
Features:
- Manual commands: /signal, /chart, /stats, /status, /help
- Automatic signal notifications (configurable interval)
- Hourly market status updates
- Real-time OANDA data integration
"""

import asyncio
import logging
import os
from typing import Optional, List, Dict
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from datetime import datetime
import json

import pandas as pd
from src.ai.ensemble import EnsembleSignalGenerator
from src.utils.database import StrategyDatabase
from src.data.data_fetcher import DataFetcher
from src.risk.risk_manager import RiskManager
from src.ai.regime_detector import RegimeDetector

logger = logging.getLogger(__name__)


class TradingBot:
    """Telegram bot for trading signals with automatic notifications"""

    def __init__(self, bot_token: str):
        """
        Initialize Telegram bot

        Args:
            bot_token: Telegram bot token
        """
        self.bot_token = bot_token
        self.application = Application.builder().token(bot_token).build()
        self.db = StrategyDatabase()
        self.data_fetcher = DataFetcher(use_oanda=True)  # Enable OANDA real-time data
        self.ensemble: Optional[EnsembleSignalGenerator] = None
        self.regime_detector = RegimeDetector()

        # Default trading pairs in standard format (EUR/USD, not USD_EURUSD)
        self.default_pairs = os.getenv('DEFAULT_PAIRS', 'EUR/USD,GBP/USD,XAU/USD').split(',')

        # Auto-notification configuration
        self.enable_auto_signals = os.getenv('ENABLE_AUTO_SIGNALS', 'true').lower() == 'true'
        self.auto_signal_interval = int(os.getenv('AUTO_SIGNAL_INTERVAL', '1800'))  # 30 min default
        self.hourly_status_enabled = os.getenv('HOURLY_STATUS_ENABLED', 'true').lower() == 'true'
        self.hourly_status_interval = int(os.getenv('HOURLY_STATUS_INTERVAL', '3600'))  # 60 min

        # Get allowed users for notifications (optional security)
        allowed_users_str = os.getenv('TELEGRAM_ALLOWED_USERS', '')
        self.allowed_users = [int(uid.strip()) for uid in allowed_users_str.split(',') if uid.strip().isdigit()]

        # Background tasks
        self._auto_signal_task = None
        self._hourly_status_task = None
        self._notification_chat_id = None  # Will be set on first user interaction

        # Register command handlers
        self.application.add_handler(CommandHandler("signal", self.signal_command))
        self.application.add_handler(CommandHandler("chart", self.chart_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("start", self.start_command))

        # Initialize risk manager with news and correlation filters
        self.risk_manager = RiskManager(
            use_news_filter=True,
            use_correlation_filter=True
        )

        logger.info(f"🤖 Bot initialized")
        logger.info(f"📊 Default pairs: {', '.join(self.default_pairs)}")
        logger.info(f"🔔 Auto signals: {'ENABLED' if self.enable_auto_signals else 'DISABLED'} (every {self.auto_signal_interval}s)")
        logger.info(f"📈 Hourly status: {'ENABLED' if self.hourly_status_enabled else 'DISABLED'}")
    
    async def start(self):
        """Start the bot and background notification tasks"""
        logger.info("Starting Telegram bot...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        logger.info("✅ Telegram bot is running. Press Ctrl+C to stop.")

        # Start background notification tasks
        if self.enable_auto_signals:
            self._auto_signal_task = asyncio.create_task(self._auto_signal_loop())
            logger.info(f"🔔 Auto-signal notifications started (every {self.auto_signal_interval}s)")

        if self.hourly_status_enabled:
            self._hourly_status_task = asyncio.create_task(self._hourly_status_loop())
            logger.info(f"📊 Hourly status updates started (every {self.hourly_status_interval}s)")

        # Keep running
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info("Stopping bot...")
            # Cancel background tasks
            if self._auto_signal_task:
                self._auto_signal_task.cancel()
            if self._hourly_status_task:
                self._hourly_status_task.cancel()

            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        # Save chat ID for automatic notifications
        if self._notification_chat_id is None:
            self._notification_chat_id = update.effective_chat.id
            logger.info(f"📱 Notification chat ID set: {self._notification_chat_id}")

        welcome_message = """
🤖 *Trading Tool AI Bot*

Welcome! I'm your AI-powered trading assistant with real-time OANDA data.

*Manual Commands:*
/signal \[pair\] - Get high-confidence trading signal
/chart <pair> - Get chart analysis
/stats - View performance statistics
/status - Current market status for all pairs
/help - Show detailed help

*Automatic Features:*
🔔 Auto Signal Alerts (every 30 minutes)
📊 Hourly Market Status Updates

*Supported Pairs:*
EUR/USD, GBP/USD, USD/JPY, AUD/USD, USD/CHF, XAU/USD

Ready to provide signals with ≥80% confidence!
        """
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def signal_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /signal command with optional pair argument"""
        try:
            # Save chat ID for notifications
            if self._notification_chat_id is None:
                self._notification_chat_id = update.effective_chat.id

            if self.ensemble is None:
                await update.message.reply_text(
                    "⚠️ Ensemble not initialized. Please run pre-deployment first."
                )
                return

            # Get pair from arguments or use default
            pair = "EUR/USD"
            if context.args and len(context.args) > 0:
                pair = context.args[0].upper()
                # Normalize pair format
                if '/' not in pair:
                    # Handle formats like "EURUSD" -> "EUR/USD"
                    if len(pair) == 6:
                        pair = f"{pair[:3]}/{pair[3:]}"

            # Fetch real-time data from OANDA (or fallback to yfinance)
            await update.message.reply_text(f"📊 Fetching real-time data for {pair}...")

            data = self.data_fetcher.load_data(pair, period='7d', interval='1h')
            if data is None or data.empty:
                await update.message.reply_text(
                    f"⚠️ No data available for {pair}. Supported pairs:\n"
                    f"EUR/USD, GBP/USD, USD/JPY, AUD/USD, USD/CHF, XAU/USD"
                )
                return

            current_price = float(data['close'].iloc[-1])

            # Generate signal with proper pair name
            signal = self.ensemble.generate_signal(data, current_price, pair)
            
            if signal is None:
                await update.message.reply_text(
                    "❌ *No Trade*\n\n"
                    "Current market conditions do not meet the ≥80% confidence threshold. "
                    "Possible reasons:\n"
                    "• Strategies didn't reach consensus\n"
                    "• Market regime not suitable\n"
                    "• Timeframes not aligned\n"
                    "• Low confidence from ensemble",
                    parse_mode='Markdown'
                )
                return
            
            # Apply risk filters (news calendar, correlation)
            # Get existing positions from database (for correlation check)
            existing_positions = []  # TODO: Load from database when tracking implemented
            is_safe, reason = self.risk_manager.check_signal_safety(
                signal, data, existing_positions
            )
            
            if not is_safe:
                await update.message.reply_text(
                    f"❌ *No Trade - Risk Filter*\n\n"
                    f"Signal filtered by risk management:\n"
                    f"⚠️ {reason}\n\n"
                    f"Recommendation: Wait until conditions improve.",
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
        
        # Build additional info
        additional_info = []
        
        if signal.get('trend_aligned'):
            trend_info = signal.get('trend_info', {})
            additional_info.append(f"✓ Trend: {trend_info.get('alignment', 'N/A').upper()}")
            additional_info.append(f"✓ Timeframes: {trend_info.get('agreement', 'N/A')}")
        
        if signal.get('correlation_check', {}).get('passed'):
            additional_info.append("✓ Correlation check passed")
        
        additional_text = "\n".join(additional_info) if additional_info else "✓ All filters passed"
        
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

*Risk Checks:*
{additional_text}

*Time:* {signal['timestamp']}

⚠️ *For Human Execution Only*
This signal passed all filters and is ready for you to execute manually.
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

*Manual Commands:*

/signal \[pair\]
Get a high-confidence trading signal or "no trade" message.
Signals require ≥80% ensemble agreement and high confidence.
Example: `/signal EUR/USD` or `/signal` (uses EUR/USD default)

/chart <pair>
Get real-time chart analysis for a trading pair.
Example: `/chart EUR/USD`

/stats
View ensemble performance statistics:
• Win rates
• Sharpe ratios
• Top performing strategies

/status
Current market status for all monitored pairs.
Shows prices, regimes, and active signals.

/help
Show this help message

*Automatic Features:*
🔔 *Auto Signal Notifications*
The bot automatically checks all pairs every 30 minutes and sends notifications when high-confidence signals are detected.

📊 *Hourly Market Status*
Every hour, you'll receive a concise market overview showing prices, regimes, and active signals for all pairs.

*About Signals:*
Each signal includes:
• Direction (BUY/SELL)
• Entry zone (price range)
• Stop loss level
• Take profit level
• Confidence score (≥80%)
• Ensemble agreement (≥80%)
• Risk check results

*Supported Pairs:*
EUR/USD, GBP/USD, USD/JPY, AUD/USD, USD/CHF, XAU/USD (Gold)

⚠️ *Important:* All trades are for human execution only. This bot does NOT execute trades automatically.
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command - show market status for all pairs"""
        try:
            if self.ensemble is None:
                await update.message.reply_text("⚠️ Ensemble not initialized.")
                return

            await update.message.reply_text("📊 Fetching market status...")

            status_lines = ["📊 *Market Status*\n"]
            active_signals = 0

            for pair in self.default_pairs:
                try:
                    # Fetch real-time data
                    data = self.data_fetcher.load_data(pair, period='3d', interval='1h')
                    if data is None or data.empty:
                        continue

                    current_price = float(data['close'].iloc[-1])

                    # Detect regime
                    regime, confidence = self.regime_detector.detect_regime(data)
                    regime_emoji = "↗️" if regime == "trending" else "↔️" if regime == "ranging" else "📊"

                    # Check for signal
                    signal = self.ensemble.generate_signal(data, current_price, pair)

                    if signal:
                        active_signals += 1
                        direction_emoji = "📈" if signal['direction'] == 'buy' else "📉"
                        status_lines.append(
                            f"*{pair}*: {current_price:.4f} | {regime.title()} {regime_emoji} | "
                            f"{direction_emoji} {signal['direction'].upper()} ({signal['confidence']:.0f}%)"
                        )
                    else:
                        status_lines.append(
                            f"*{pair}*: {current_price:.4f} | {regime.title()} {regime_emoji} | ⚪ Monitoring"
                        )

                except Exception as e:
                    logger.error(f"Error checking {pair}: {e}")
                    status_lines.append(f"*{pair}*: ⚠️ Error fetching data")

            # Summary
            if active_signals > 0:
                status_lines.append(f"\n🟢 *{active_signals} Active Signal(s)*")
            else:
                status_lines.append(f"\n⚪ *No Active Signals* (monitoring)")

            status_lines.append(f"\n_Last updated: {datetime.now().strftime('%H:%M UTC')}_")

            await update.message.reply_text("\n".join(status_lines), parse_mode='Markdown')

        except Exception as e:
            logger.error(f"Error in status_command: {e}")
            await update.message.reply_text(f"❌ Error getting status: {str(e)}")

    async def _auto_signal_loop(self):
        """Background task: Check for signals automatically and notify"""
        logger.info("🔔 Auto-signal loop started")
        await asyncio.sleep(60)  # Wait 60s for bot to fully start

        while True:
            try:
                if self.ensemble is None or self._notification_chat_id is None:
                    await asyncio.sleep(self.auto_signal_interval)
                    continue

                logger.debug("🔍 Checking for signals...")

                for pair in self.default_pairs:
                    try:
                        # Fetch real-time data
                        data = self.data_fetcher.load_data(pair, period='7d', interval='1h')
                        if data is None or data.empty:
                            continue

                        current_price = float(data['close'].iloc[-1])

                        # Generate signal
                        signal = self.ensemble.generate_signal(data, current_price, pair)

                        if signal:
                            # Apply risk filters
                            existing_positions = []  # TODO: Load from database
                            is_safe, reason = self.risk_manager.check_signal_safety(
                                signal, data, existing_positions
                            )

                            if is_safe:
                                # Send notification
                                signal_message = "🔔 *Automatic Signal Alert*\n\n" + self._format_signal(signal)
                                await self.application.bot.send_message(
                                    chat_id=self._notification_chat_id,
                                    text=signal_message,
                                    parse_mode='Markdown'
                                )
                                logger.info(f"✅ Signal notification sent for {pair}")

                                # Save to database
                                self.db.save_signal(signal)

                    except Exception as e:
                        logger.error(f"Error checking signal for {pair}: {e}")

                # Wait for next check
                await asyncio.sleep(self.auto_signal_interval)

            except asyncio.CancelledError:
                logger.info("Auto-signal loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in auto-signal loop: {e}")
                await asyncio.sleep(self.auto_signal_interval)

    async def _hourly_status_loop(self):
        """Background task: Send hourly market status updates"""
        logger.info("📊 Hourly status loop started")
        await asyncio.sleep(120)  # Wait 120s for bot to fully start

        while True:
            try:
                if self.ensemble is None or self._notification_chat_id is None:
                    await asyncio.sleep(self.hourly_status_interval)
                    continue

                logger.debug("📊 Generating hourly status...")

                status_lines = ["📊 *Hourly Market Status*\n"]
                active_signals = 0

                for pair in self.default_pairs:
                    try:
                        data = self.data_fetcher.load_data(pair, period='3d', interval='1h')
                        if data is None or data.empty:
                            continue

                        current_price = float(data['close'].iloc[-1])
                        regime, _ = self.regime_detector.detect_regime(data)
                        regime_emoji = "↗️" if regime == "trending" else "↔️" if regime == "ranging" else "📊"

                        signal = self.ensemble.generate_signal(data, current_price, pair)

                        if signal:
                            active_signals += 1
                            direction_emoji = "📈" if signal['direction'] == 'buy' else "📉"
                            status_lines.append(
                                f"*{pair}*: {current_price:.4f} | {regime_emoji} | "
                                f"{direction_emoji} {signal['direction'].upper()} ({signal['confidence']:.0f}%)"
                            )
                        else:
                            status_lines.append(f"*{pair}*: {current_price:.4f} | {regime_emoji} | ⚪ Monitoring")

                    except Exception as e:
                        logger.debug(f"Error in status for {pair}: {e}")

                if active_signals > 0:
                    status_lines.append(f"\n🟢 {active_signals} Active Signal(s)")
                else:
                    status_lines.append(f"\n⚪ No Active Signals")

                next_update = datetime.now().hour + 1
                status_lines.append(f"\n_Next update: {next_update:02d}:00 UTC_")

                # Send status update
                await self.application.bot.send_message(
                    chat_id=self._notification_chat_id,
                    text="\n".join(status_lines),
                    parse_mode='Markdown'
                )
                logger.info("✅ Hourly status sent")

                await asyncio.sleep(self.hourly_status_interval)

            except asyncio.CancelledError:
                logger.info("Hourly status loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in hourly status loop: {e}")
                await asyncio.sleep(self.hourly_status_interval)

    def set_ensemble(self, ensemble: EnsembleSignalGenerator):
        """Set the ensemble generator"""
        self.ensemble = ensemble

