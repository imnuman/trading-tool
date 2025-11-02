"""
Database module for storing strategies and backtest results
"""

import sqlite3
import json
import os
from typing import List, Dict, Optional
import logging
import numpy as np
from src.strategies.strategy_generator import Strategy
from src.backtesting.backtest_engine import BacktestResult

logger = logging.getLogger(__name__)


def _json_serialize(obj):
    """Convert numpy types to native Python types for JSON serialization"""
    if isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, dict):
        return {k: _json_serialize(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_json_serialize(item) for item in obj]
    return obj


class StrategyDatabase:
    """Database for storing strategies and results"""
    
    def __init__(self, db_path: str = './data/strategies.db'):
        """
        Initialize database
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Strategies table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS strategies (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                strategy_type TEXT,
                indicators TEXT,
                timeframe TEXT,
                session_filter TEXT,
                entry_conditions TEXT,
                exit_conditions TEXT,
                parameters TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Backtest results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backtest_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_id TEXT NOT NULL,
                win_rate REAL,
                total_trades INTEGER,
                winning_trades INTEGER,
                losing_trades INTEGER,
                max_drawdown REAL,
                sharpe_ratio REAL,
                risk_reward_ratio REAL,
                total_return REAL,
                average_win REAL,
                average_loss REAL,
                profit_factor REAL,
                confidence_score REAL,
                backtested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (strategy_id) REFERENCES strategies(id)
            )
        ''')
        
        # Live signals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pair TEXT,
                direction TEXT,
                entry_zone_min REAL,
                entry_zone_max REAL,
                stop_loss REAL,
                take_profit REAL,
                confidence REAL,
                strategies_used TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                executed INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")
    
    def save_strategy(self, strategy: Strategy):
        """Save strategy to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO strategies 
            (id, name, strategy_type, indicators, timeframe, session_filter, 
             entry_conditions, exit_conditions, parameters)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            strategy.id,
            strategy.name,
            strategy.entry_conditions.get('type', ''),
            json.dumps(_json_serialize(strategy.indicators)),
            strategy.timeframe,
            strategy.session_filter,
            json.dumps(_json_serialize(strategy.entry_conditions)),
            json.dumps(_json_serialize(strategy.exit_conditions)),
            json.dumps(_json_serialize(strategy.parameters))
        ))
        
        conn.commit()
        conn.close()
    
    def save_backtest_result(self, result: BacktestResult):
        """Save backtest result to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO backtest_results
            (strategy_id, win_rate, total_trades, winning_trades, losing_trades,
             max_drawdown, sharpe_ratio, risk_reward_ratio, total_return,
             average_win, average_loss, profit_factor, confidence_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            result.strategy_id,
            result.win_rate,
            result.total_trades,
            result.winning_trades,
            result.losing_trades,
            result.max_drawdown,
            result.sharpe_ratio,
            result.risk_reward_ratio,
            result.total_return,
            result.average_win,
            result.average_loss,
            result.profit_factor,
            result.confidence_score
        ))
        
        conn.commit()
        conn.close()
    
    def get_top_strategies(
        self, 
        min_confidence: float = 70.0,
        min_trades: int = 10,
        limit: int = 1000
    ) -> List[Dict]:
        """Get top performing strategies"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT s.*, br.confidence_score, br.win_rate, br.sharpe_ratio,
                   br.max_drawdown, br.total_trades
            FROM strategies s
            JOIN (
                SELECT strategy_id, 
                       MAX(backtested_at) as latest_backtest,
                       confidence_score, win_rate, sharpe_ratio, 
                       max_drawdown, total_trades
                FROM backtest_results
                GROUP BY strategy_id
            ) br ON s.id = br.strategy_id
            WHERE br.confidence_score >= ? 
            AND br.total_trades >= ?
            ORDER BY br.confidence_score DESC
            LIMIT ?
        ''', (min_confidence, min_trades, limit))
        
        results = cursor.fetchall()
        conn.close()
        
        strategies = []
        for row in results:
            strategies.append({
                'id': row[0],
                'name': row[1],
                'strategy_type': row[2],
                'indicators': json.loads(row[3]),
                'timeframe': row[4],
                'session_filter': row[5],
                'entry_conditions': json.loads(row[6]),
                'exit_conditions': json.loads(row[7]),
                'parameters': json.loads(row[8]),
                'confidence_score': row[9],
                'win_rate': row[10],
                'sharpe_ratio': row[11],
                'max_drawdown': row[12],
                'total_trades': row[13]
            })
        
        return strategies
    
    def save_signal(self, signal: Dict):
        """Save generated signal"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO signals
            (pair, direction, entry_zone_min, entry_zone_max, stop_loss, 
             take_profit, confidence, strategies_used)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            signal['pair'],
            signal['direction'],
            signal['entry_zone'][0],
            signal['entry_zone'][1],
            signal['stop_loss'],
            signal['take_profit'],
            signal['confidence'],
            json.dumps(signal.get('strategies_used', []))
        ))
        
        conn.commit()
        conn.close()

