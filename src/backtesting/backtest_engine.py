"""
Pre-Simulation Backtesting Engine
Runs strategies on historical data and calculates performance metrics
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from src.strategies.strategy_generator import Strategy

logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    """Results from backtesting a strategy"""
    strategy_id: str
    strategy_name: str
    win_rate: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    max_drawdown: float
    sharpe_ratio: float
    risk_reward_ratio: float
    total_return: float
    average_win: float
    average_loss: float
    profit_factor: float
    confidence_score: float  # Composite score 0-100


class BacktestEngine:
    """Backtests strategies on historical data"""
    
    def __init__(self, data: pd.DataFrame, slippage: float = 0.0002, spread: float = 0.0001):
        """
        Initialize backtest engine
        
        Args:
            data: Historical OHLCV data
            slippage: Slippage percentage per trade
            spread: Spread cost per trade
        """
        self.data = data.copy()
        self.slippage = slippage
        self.spread = spread
        self._prepare_data()
    
    def _prepare_data(self):
        """Prepare data with technical indicators"""
        df = self.data.copy()
        
        # Calculate basic indicators that might be needed
        df['returns'] = df['close'].pct_change()
        df['volatility'] = df['returns'].rolling(window=20).std()
        
        self.data = df
    
    def backtest_strategy(self, strategy: Strategy) -> BacktestResult:
        """
        Backtest a single strategy
        
        Args:
            strategy: Strategy object to backtest
        
        Returns:
            BacktestResult with performance metrics
        """
        try:
            # Generate signals based on strategy
            signals = self._generate_signals(strategy)
            
            # Execute trades
            trades = self._execute_trades(signals, strategy)
            
            # Calculate metrics
            result = self._calculate_metrics(strategy, trades)
            
            return result
            
        except Exception as e:
            logger.error(f"Error backtesting strategy {strategy.id}: {e}")
            # Return empty result
            return BacktestResult(
                strategy_id=strategy.id,
                strategy_name=strategy.name,
                win_rate=0.0,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                max_drawdown=1.0,
                sharpe_ratio=0.0,
                risk_reward_ratio=0.0,
                total_return=-1.0,
                average_win=0.0,
                average_loss=0.0,
                profit_factor=0.0,
                confidence_score=0.0
            )
    
    def _generate_signals(self, strategy: Strategy) -> pd.DataFrame:
        """Generate trading signals based on strategy"""
        df = self.data.copy()
        df['signal'] = 0  # 0 = no trade, 1 = buy, -1 = sell
        df['entry_price'] = np.nan
        df['stop_loss'] = np.nan
        df['take_profit'] = np.nan
        
        # Apply strategy-specific logic
        strategy_type = strategy.entry_conditions.get('type', '')
        
        if 'ema_cross' in strategy_type or strategy.name.startswith('ema_cross'):
            df = self._apply_ema_strategy(df, strategy)
        elif 'rsi' in strategy_type or strategy.name.startswith('rsi'):
            df = self._apply_rsi_strategy(df, strategy)
        elif 'macd' in strategy_type or strategy.name.startswith('macd'):
            df = self._apply_macd_strategy(df, strategy)
        elif 'bollinger' in strategy_type or strategy.name.startswith('bollinger'):
            df = self._apply_bollinger_strategy(df, strategy)
        elif 'volume' in strategy_type or strategy.name.startswith('volume'):
            df = self._apply_volume_strategy(df, strategy)
        elif 'atr' in strategy_type or strategy.name.startswith('atr'):
            df = self._apply_atr_strategy(df, strategy)
        else:
            # Default: simple momentum
            df = self._apply_simple_strategy(df, strategy)
        
        return df
    
    def _apply_ema_strategy(self, df: pd.DataFrame, strategy: Strategy) -> pd.DataFrame:
        """Apply EMA crossover strategy"""
        fast_period = strategy.parameters.get('fast_ema', 20)
        slow_period = strategy.parameters.get('slow_ema', 50)
        
        df['ema_fast'] = df['close'].ewm(span=fast_period, adjust=False).mean()
        df['ema_slow'] = df['close'].ewm(span=slow_period, adjust=False).mean()
        
        # Buy signal: fast EMA crosses above slow EMA
        df.loc[df['ema_fast'] > df['ema_slow'], 'signal'] = 1
        df.loc[df['ema_fast'] < df['ema_slow'], 'signal'] = -1
        
        # Remove signals during consolidation
        signal_changes = df['signal'].diff().abs() > 0
        df.loc[~signal_changes, 'signal'] = 0
        
        # Set entry prices and stops
        df.loc[df['signal'] != 0, 'entry_price'] = df['close']
        stop_loss_pct = strategy.exit_conditions.get('stop_loss_pct', 0.02)
        take_profit_pct = strategy.exit_conditions.get('take_profit_pct', 0.04)
        
        df.loc[df['signal'] == 1, 'stop_loss'] = df['close'] * (1 - stop_loss_pct)
        df.loc[df['signal'] == 1, 'take_profit'] = df['close'] * (1 + take_profit_pct)
        df.loc[df['signal'] == -1, 'stop_loss'] = df['close'] * (1 + stop_loss_pct)
        df.loc[df['signal'] == -1, 'take_profit'] = df['close'] * (1 - take_profit_pct)
        
        return df
    
    def _apply_rsi_strategy(self, df: pd.DataFrame, strategy: Strategy) -> pd.DataFrame:
        """Apply RSI strategy"""
        rsi_period = strategy.parameters.get('rsi_period', 14)
        oversold = strategy.parameters.get('oversold', 30)
        overbought = strategy.parameters.get('overbought', 70)
        
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Buy when RSI oversold, sell when overbought
        df.loc[df['rsi'] < oversold, 'signal'] = 1
        df.loc[df['rsi'] > overbought, 'signal'] = -1
        
        stop_loss_pct = strategy.exit_conditions.get('stop_loss_pct', 0.02)
        take_profit_pct = strategy.exit_conditions.get('take_profit_pct', 0.04)
        
        df.loc[df['signal'] == 1, 'entry_price'] = df['close']
        df.loc[df['signal'] == 1, 'stop_loss'] = df['close'] * (1 - stop_loss_pct)
        df.loc[df['signal'] == 1, 'take_profit'] = df['close'] * (1 + take_profit_pct)
        df.loc[df['signal'] == -1, 'entry_price'] = df['close']
        df.loc[df['signal'] == -1, 'stop_loss'] = df['close'] * (1 + stop_loss_pct)
        df.loc[df['signal'] == -1, 'take_profit'] = df['close'] * (1 - take_profit_pct)
        
        return df
    
    def _apply_macd_strategy(self, df: pd.DataFrame, strategy: Strategy) -> pd.DataFrame:
        """Apply MACD strategy"""
        fast = strategy.parameters.get('macd_fast', 12)
        slow = strategy.parameters.get('macd_slow', 26)
        signal = strategy.parameters.get('macd_signal', 9)
        
        ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
        df['macd'] = ema_fast - ema_slow
        df['macd_signal'] = df['macd'].ewm(span=signal, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # Buy when MACD crosses above signal
        df.loc[(df['macd'] > df['macd_signal']) & (df['macd_hist'].shift() <= 0), 'signal'] = 1
        df.loc[(df['macd'] < df['macd_signal']) & (df['macd_hist'].shift() >= 0), 'signal'] = -1
        
        stop_loss_pct = strategy.exit_conditions.get('stop_loss_pct', 0.02)
        take_profit_pct = strategy.exit_conditions.get('take_profit_pct', 0.04)
        
        df.loc[df['signal'] != 0, 'entry_price'] = df['close']
        df.loc[df['signal'] == 1, 'stop_loss'] = df['close'] * (1 - stop_loss_pct)
        df.loc[df['signal'] == 1, 'take_profit'] = df['close'] * (1 + take_profit_pct)
        df.loc[df['signal'] == -1, 'stop_loss'] = df['close'] * (1 + stop_loss_pct)
        df.loc[df['signal'] == -1, 'take_profit'] = df['close'] * (1 - take_profit_pct)
        
        return df
    
    def _apply_bollinger_strategy(self, df: pd.DataFrame, strategy: Strategy) -> pd.DataFrame:
        """Apply Bollinger Bands strategy"""
        period = strategy.parameters.get('bb_period', 20)
        std_dev = strategy.parameters.get('bb_std', 2.0)
        
        df['bb_middle'] = df['close'].rolling(window=period).mean()
        df['bb_std'] = df['close'].rolling(window=period).std()
        df['bb_upper'] = df['bb_middle'] + (df['bb_std'] * std_dev)
        df['bb_lower'] = df['bb_middle'] - (df['bb_std'] * std_dev)
        
        # Buy when price touches lower band, sell at upper band
        df.loc[df['close'] <= df['bb_lower'], 'signal'] = 1
        df.loc[df['close'] >= df['bb_upper'], 'signal'] = -1
        
        stop_loss_pct = strategy.exit_conditions.get('stop_loss_pct', 0.02)
        take_profit_pct = strategy.exit_conditions.get('take_profit_pct', 0.04)
        
        df.loc[df['signal'] != 0, 'entry_price'] = df['close']
        df.loc[df['signal'] == 1, 'stop_loss'] = df['close'] * (1 - stop_loss_pct)
        df.loc[df['signal'] == 1, 'take_profit'] = df['bb_middle']  # Target middle band
        df.loc[df['signal'] == -1, 'stop_loss'] = df['close'] * (1 + stop_loss_pct)
        df.loc[df['signal'] == -1, 'take_profit'] = df['bb_middle']
        
        return df
    
    def _apply_volume_strategy(self, df: pd.DataFrame, strategy: Strategy) -> pd.DataFrame:
        """Apply volume breakout strategy"""
        period = strategy.parameters.get('volume_period', 20)
        multiplier = strategy.parameters.get('volume_multiplier', 2.0)
        
        df['volume_ma'] = df['volume'].rolling(window=period).mean()
        df['volume_spike'] = df['volume'] > (df['volume_ma'] * multiplier)
        
        # Buy on volume spike with price increase
        df.loc[df['volume_spike'] & (df['close'] > df['close'].shift()), 'signal'] = 1
        df.loc[df['volume_spike'] & (df['close'] < df['close'].shift()), 'signal'] = -1
        
        stop_loss_pct = strategy.exit_conditions.get('stop_loss_pct', 0.02)
        take_profit_pct = strategy.exit_conditions.get('take_profit_pct', 0.04)
        
        df.loc[df['signal'] != 0, 'entry_price'] = df['close']
        df.loc[df['signal'] == 1, 'stop_loss'] = df['close'] * (1 - stop_loss_pct)
        df.loc[df['signal'] == 1, 'take_profit'] = df['close'] * (1 + take_profit_pct)
        df.loc[df['signal'] == -1, 'stop_loss'] = df['close'] * (1 + stop_loss_pct)
        df.loc[df['signal'] == -1, 'take_profit'] = df['close'] * (1 - take_profit_pct)
        
        return df
    
    def _apply_atr_strategy(self, df: pd.DataFrame, strategy: Strategy) -> pd.DataFrame:
        """Apply ATR-based strategy"""
        atr_period = strategy.parameters.get('atr_period', 14)
        atr_multiplier = strategy.parameters.get('atr_multiplier', 2.0)
        
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = true_range.rolling(window=atr_period).mean()
        
        # Breakout strategy using ATR
        df['atr_upper'] = df['close'] + (df['atr'] * atr_multiplier)
        df['atr_lower'] = df['close'] - (df['atr'] * atr_multiplier)
        
        df.loc[df['close'] > df['atr_upper'], 'signal'] = 1
        df.loc[df['close'] < df['atr_lower'], 'signal'] = -1
        
        df.loc[df['signal'] != 0, 'entry_price'] = df['close']
        df.loc[df['signal'] == 1, 'stop_loss'] = df['close'] - (df['atr'] * atr_multiplier)
        df.loc[df['signal'] == 1, 'take_profit'] = df['close'] + (df['atr'] * atr_multiplier * 2)
        df.loc[df['signal'] == -1, 'stop_loss'] = df['close'] + (df['atr'] * atr_multiplier)
        df.loc[df['signal'] == -1, 'take_profit'] = df['close'] - (df['atr'] * atr_multiplier * 2)
        
        return df
    
    def _apply_simple_strategy(self, df: pd.DataFrame, strategy: Strategy) -> pd.DataFrame:
        """Apply simple momentum strategy as fallback"""
        # Simple moving average crossover
        df['sma_short'] = df['close'].rolling(window=10).mean()
        df['sma_long'] = df['close'].rolling(window=30).mean()
        
        df.loc[df['sma_short'] > df['sma_long'], 'signal'] = 1
        df.loc[df['sma_short'] < df['sma_long'], 'signal'] = -1
        
        stop_loss_pct = 0.02
        take_profit_pct = 0.04
        
        df.loc[df['signal'] != 0, 'entry_price'] = df['close']
        df.loc[df['signal'] == 1, 'stop_loss'] = df['close'] * (1 - stop_loss_pct)
        df.loc[df['signal'] == 1, 'take_profit'] = df['close'] * (1 + take_profit_pct)
        df.loc[df['signal'] == -1, 'stop_loss'] = df['close'] * (1 + stop_loss_pct)
        df.loc[df['signal'] == -1, 'take_profit'] = df['close'] * (1 - take_profit_pct)
        
        return df
    
    def _execute_trades(self, signals: pd.DataFrame, strategy: Strategy) -> List[Dict]:
        """Execute trades based on signals"""
        trades = []
        position = None
        
        for idx, row in signals.iterrows():
            if pd.isna(row['entry_price']) or row['signal'] == 0:
                continue
            
            # Close existing position if signal changes
            if position:
                if (position['direction'] == 'long' and row['signal'] == -1) or \
                   (position['direction'] == 'short' and row['signal'] == 1):
                    # Close position
                    exit_price = row['close']
                    pnl = self._calculate_pnl(position, exit_price)
                    position['exit_price'] = exit_price
                    position['exit_time'] = idx
                    position['pnl'] = pnl
                    position['pnl_pct'] = (pnl / position['entry_price']) * 100
                    trades.append(position)
                    position = None
            
            # Open new position
            if not position and row['signal'] != 0:
                direction = 'long' if row['signal'] == 1 else 'short'
                entry_price = row['entry_price']
                
                # Adjust for slippage and spread
                if direction == 'long':
                    entry_price = entry_price * (1 + self.slippage + self.spread)
                else:
                    entry_price = entry_price * (1 - self.slippage - self.spread)
                
                position = {
                    'entry_time': idx,
                    'entry_price': entry_price,
                    'direction': direction,
                    'stop_loss': row['stop_loss'],
                    'take_profit': row['take_profit'],
                    'strategy_id': strategy.id
                }
        
        # Close final position if exists
        if position:
            exit_price = signals.iloc[-1]['close']
            pnl = self._calculate_pnl(position, exit_price)
            position['exit_price'] = exit_price
            position['exit_time'] = signals.index[-1]
            position['pnl'] = pnl
            position['pnl_pct'] = (pnl / position['entry_price']) * 100
            trades.append(position)
        
        return trades
    
    def _calculate_pnl(self, position: Dict, exit_price: float) -> float:
        """Calculate profit/loss for a position"""
        if position['direction'] == 'long':
            # Adjust exit for slippage
            exit_price = exit_price * (1 - self.slippage - self.spread)
            pnl = exit_price - position['entry_price']
        else:
            exit_price = exit_price * (1 + self.slippage + self.spread)
            pnl = position['entry_price'] - exit_price
        
        # Check if stop loss or take profit was hit
        if position['direction'] == 'long':
            if exit_price <= position['stop_loss']:
                pnl = position['stop_loss'] - position['entry_price']
            elif exit_price >= position['take_profit']:
                pnl = position['take_profit'] - position['entry_price']
        else:
            if exit_price >= position['stop_loss']:
                pnl = position['entry_price'] - position['stop_loss']
            elif exit_price <= position['take_profit']:
                pnl = position['entry_price'] - position['take_profit']
        
        return pnl
    
    def _calculate_metrics(self, strategy: Strategy, trades: List[Dict]) -> BacktestResult:
        """Calculate performance metrics"""
        if not trades:
            return BacktestResult(
                strategy_id=strategy.id,
                strategy_name=strategy.name,
                win_rate=0.0,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                max_drawdown=1.0,
                sharpe_ratio=0.0,
                risk_reward_ratio=0.0,
                total_return=-1.0,
                average_win=0.0,
                average_loss=0.0,
                profit_factor=0.0,
                confidence_score=0.0
            )
        
        # Basic metrics
        total_trades = len(trades)
        winning_trades = [t for t in trades if t['pnl'] > 0]
        losing_trades = [t for t in trades if t['pnl'] < 0]
        
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        
        # Profit metrics
        total_return = sum(t['pnl'] for t in trades)
        average_win = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
        average_loss = np.mean([abs(t['pnl']) for t in losing_trades]) if losing_trades else 0
        
        # Risk-reward ratio
        if average_loss > 0:
            risk_reward_ratio = abs(average_win / average_loss)
        else:
            risk_reward_ratio = 0
        
        # Profit factor
        total_profit = sum(t['pnl'] for t in winning_trades) if winning_trades else 0
        total_loss = abs(sum(t['pnl'] for t in losing_trades)) if losing_trades else 0
        profit_factor = total_profit / total_loss if total_loss > 0 else 0
        
        # Drawdown calculation
        cumulative_returns = np.cumsum([t['pnl'] for t in trades])
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - running_max) / (running_max + 1e-10)
        max_drawdown = abs(np.min(drawdown)) if len(drawdown) > 0 else 1.0
        
        # Sharpe ratio (simplified)
        returns_series = [t['pnl'] for t in trades]
        if len(returns_series) > 1 and np.std(returns_series) > 0:
            sharpe_ratio = np.mean(returns_series) / np.std(returns_series) * np.sqrt(252)  # Annualized
        else:
            sharpe_ratio = 0.0
        
        # Confidence score (0-100)
        confidence_score = self._calculate_confidence_score(
            win_rate, sharpe_ratio, max_drawdown, profit_factor, total_trades
        )
        
        return BacktestResult(
            strategy_id=strategy.id,
            strategy_name=strategy.name,
            win_rate=win_rate,
            total_trades=total_trades,
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            risk_reward_ratio=risk_reward_ratio,
            total_return=total_return,
            average_win=average_win,
            average_loss=average_loss,
            profit_factor=profit_factor,
            confidence_score=confidence_score
        )
    
    def _calculate_confidence_score(
        self, 
        win_rate: float, 
        sharpe: float, 
        drawdown: float, 
        profit_factor: float,
        total_trades: int
    ) -> float:
        """Calculate composite confidence score (0-100)"""
        # Normalize components
        win_rate_score = min(win_rate * 100, 100)  # 0-100
        sharpe_score = min(max(sharpe * 10, 0), 100)  # Scale Sharpe
        drawdown_score = max(100 - (drawdown * 500), 0)  # Lower drawdown = higher score
        profit_factor_score = min(profit_factor * 25, 100)  # Scale profit factor
        trade_count_score = min(total_trades / 10, 100)  # More trades = better
        
        # Weighted average
        confidence = (
            win_rate_score * 0.3 +
            sharpe_score * 0.25 +
            drawdown_score * 0.2 +
            profit_factor_score * 0.15 +
            trade_count_score * 0.1
        )
        
        return max(0, min(confidence, 100))

