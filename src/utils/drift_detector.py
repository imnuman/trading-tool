"""
Drift Detection Module
Monitors strategy performance degradation and triggers alerts/retraining

Detects when live performance deviates significantly from baseline metrics.
Essential for 24/7 production operation.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from scipy import stats
import logging

logger = logging.getLogger(__name__)


class DriftDetector:
    """Detects performance drift in trading strategies"""

    def __init__(
        self,
        drift_threshold: float = 0.15,  # 15% performance degradation triggers alert
        min_trades_for_detection: int = 30,  # Minimum trades needed for statistical significance
        lookback_days: int = 30,  # Recent performance window
        alert_cooldown_hours: int = 24  # Minimum time between alerts for same strategy
    ):
        """
        Initialize drift detector

        Args:
            drift_threshold: Maximum acceptable performance degradation (0-1)
            min_trades_for_detection: Minimum trades needed for statistical test
            lookback_days: Days to consider for recent performance
            alert_cooldown_hours: Hours between repeated alerts
        """
        self.drift_threshold = drift_threshold
        self.min_trades_for_detection = min_trades_for_detection
        self.lookback_days = lookback_days
        self.alert_cooldown_hours = alert_cooldown_hours

        # Track when alerts were last sent
        self.last_alert_time: Dict[str, datetime] = {}

    def detect_performance_drift(
        self,
        strategy_id: str,
        recent_trades: List[Dict],
        baseline_metrics: Dict
    ) -> Tuple[bool, Dict]:
        """
        Detect if strategy performance has drifted from baseline

        Args:
            strategy_id: Strategy identifier
            recent_trades: List of recent trade outcomes
            baseline_metrics: Historical baseline metrics (from backtesting)

        Returns:
            Tuple of (has_drift, drift_report)
        """
        if len(recent_trades) < self.min_trades_for_detection:
            logger.debug(
                f"Strategy {strategy_id[:20]}: Insufficient trades for drift detection "
                f"({len(recent_trades)} < {self.min_trades_for_detection})"
            )
            return False, {'reason': 'insufficient_data', 'trades_count': len(recent_trades)}

        # Calculate recent metrics
        recent_metrics = self._calculate_metrics(recent_trades)

        # Check for win rate drift
        win_rate_drift = self._check_win_rate_drift(
            recent_metrics['win_rate'],
            baseline_metrics.get('win_rate', 0.5)
        )

        # Check for profit factor drift
        pf_drift = self._check_profit_factor_drift(
            recent_metrics['profit_factor'],
            baseline_metrics.get('profit_factor', 1.0)
        )

        # Check for Sharpe ratio drift
        sharpe_drift = self._check_sharpe_drift(
            recent_metrics['sharpe_ratio'],
            baseline_metrics.get('sharpe_ratio', 0.0)
        )

        # Statistical distribution test
        distribution_drift = self._check_distribution_drift(recent_trades, baseline_metrics)

        # Determine if drift has occurred
        has_drift = (
            win_rate_drift['has_drift'] or
            pf_drift['has_drift'] or
            sharpe_drift['has_drift'] or
            distribution_drift['has_drift']
        )

        drift_report = {
            'strategy_id': strategy_id,
            'timestamp': datetime.utcnow(),
            'recent_trades_count': len(recent_trades),
            'has_drift': has_drift,
            'win_rate': win_rate_drift,
            'profit_factor': pf_drift,
            'sharpe_ratio': sharpe_drift,
            'distribution': distribution_drift,
            'recent_metrics': recent_metrics,
            'baseline_metrics': baseline_metrics,
            'severity': self._calculate_severity(win_rate_drift, pf_drift, sharpe_drift, distribution_drift)
        }

        if has_drift:
            logger.warning(
                f"DRIFT DETECTED for strategy {strategy_id[:20]}: "
                f"WR={recent_metrics['win_rate']:.2%} (baseline={baseline_metrics.get('win_rate', 0):.2%}), "
                f"PF={recent_metrics['profit_factor']:.2f} (baseline={baseline_metrics.get('profit_factor', 0):.2f}), "
                f"Severity={drift_report['severity']}"
            )

        return has_drift, drift_report

    def _calculate_metrics(self, trades: List[Dict]) -> Dict:
        """Calculate performance metrics from trade list"""
        if not trades:
            return {
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0
            }

        # Extract outcomes
        outcomes = [trade.get('outcome', 0) for trade in trades]
        wins = [o for o in outcomes if o > 0]
        losses = [abs(o) for o in outcomes if o < 0]

        # Win rate
        win_rate = len(wins) / len(trades) if trades else 0.0

        # Profit factor
        total_profit = sum(wins) if wins else 0.0
        total_loss = sum(losses) if losses else 0.0
        profit_factor = total_profit / total_loss if total_loss > 0 else 0.0

        # Sharpe ratio (annualized, assuming daily trades)
        if len(outcomes) > 1:
            returns = np.array(outcomes)
            sharpe_ratio = (np.mean(returns) / np.std(returns)) * np.sqrt(252) if np.std(returns) > 0 else 0.0
        else:
            sharpe_ratio = 0.0

        # Max drawdown
        cumulative = np.cumsum(outcomes)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = running_max - cumulative
        max_drawdown = np.max(drawdown) if len(drawdown) > 0 else 0.0

        return {
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'avg_win': np.mean(wins) if wins else 0.0,
            'avg_loss': np.mean(losses) if losses else 0.0,
            'total_trades': len(trades)
        }

    def _check_win_rate_drift(self, recent_wr: float, baseline_wr: float) -> Dict:
        """Check if win rate has drifted significantly"""
        if baseline_wr == 0:
            return {'has_drift': False, 'reason': 'no_baseline'}

        degradation = (baseline_wr - recent_wr) / baseline_wr
        has_drift = degradation > self.drift_threshold

        return {
            'has_drift': has_drift,
            'recent': recent_wr,
            'baseline': baseline_wr,
            'degradation': degradation,
            'threshold': self.drift_threshold
        }

    def _check_profit_factor_drift(self, recent_pf: float, baseline_pf: float) -> Dict:
        """Check if profit factor has drifted significantly"""
        if baseline_pf == 0:
            return {'has_drift': False, 'reason': 'no_baseline'}

        degradation = (baseline_pf - recent_pf) / baseline_pf
        has_drift = degradation > self.drift_threshold

        return {
            'has_drift': has_drift,
            'recent': recent_pf,
            'baseline': baseline_pf,
            'degradation': degradation,
            'threshold': self.drift_threshold
        }

    def _check_sharpe_drift(self, recent_sharpe: float, baseline_sharpe: float) -> Dict:
        """Check if Sharpe ratio has drifted significantly"""
        if baseline_sharpe <= 0:
            return {'has_drift': False, 'reason': 'no_baseline'}

        degradation = (baseline_sharpe - recent_sharpe) / baseline_sharpe
        has_drift = degradation > self.drift_threshold

        return {
            'has_drift': has_drift,
            'recent': recent_sharpe,
            'baseline': baseline_sharpe,
            'degradation': degradation,
            'threshold': self.drift_threshold
        }

    def _check_distribution_drift(self, recent_trades: List[Dict], baseline_metrics: Dict) -> Dict:
        """
        Perform statistical test to detect if return distribution has changed
        Uses Kolmogorov-Smirnov test
        """
        if 'return_distribution' not in baseline_metrics:
            return {'has_drift': False, 'reason': 'no_baseline_distribution'}

        # Get recent returns
        recent_returns = [trade.get('outcome', 0) for trade in recent_trades]

        # Get baseline returns (if available)
        baseline_returns = baseline_metrics.get('return_distribution', [])

        if len(recent_returns) < 20 or len(baseline_returns) < 20:
            return {'has_drift': False, 'reason': 'insufficient_samples'}

        # Kolmogorov-Smirnov test
        statistic, p_value = stats.ks_2samp(recent_returns, baseline_returns)

        # Drift detected if p-value < 0.05 (distributions are significantly different)
        has_drift = p_value < 0.05

        return {
            'has_drift': has_drift,
            'test': 'Kolmogorov-Smirnov',
            'statistic': statistic,
            'p_value': p_value,
            'threshold': 0.05
        }

    def _calculate_severity(
        self,
        win_rate_drift: Dict,
        pf_drift: Dict,
        sharpe_drift: Dict,
        dist_drift: Dict
    ) -> str:
        """
        Calculate drift severity level

        Returns: 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'NONE'
        """
        drift_count = sum([
            win_rate_drift.get('has_drift', False),
            pf_drift.get('has_drift', False),
            sharpe_drift.get('has_drift', False),
            dist_drift.get('has_drift', False)
        ])

        # Check degradation magnitudes
        wr_deg = win_rate_drift.get('degradation', 0)
        pf_deg = pf_drift.get('degradation', 0)
        sharpe_deg = sharpe_drift.get('degradation', 0)

        max_degradation = max(wr_deg, pf_deg, sharpe_deg)

        if drift_count >= 3:
            return 'CRITICAL'
        elif drift_count == 2 or max_degradation > 0.30:
            return 'HIGH'
        elif drift_count == 1 or max_degradation > 0.20:
            return 'MEDIUM'
        elif max_degradation > 0:
            return 'LOW'
        else:
            return 'NONE'

    def should_send_alert(self, strategy_id: str) -> bool:
        """
        Check if enough time has passed since last alert for this strategy

        Args:
            strategy_id: Strategy identifier

        Returns:
            True if alert should be sent, False if in cooldown period
        """
        if strategy_id not in self.last_alert_time:
            return True

        time_since_last = datetime.utcnow() - self.last_alert_time[strategy_id]
        cooldown = timedelta(hours=self.alert_cooldown_hours)

        return time_since_last >= cooldown

    def mark_alert_sent(self, strategy_id: str):
        """Mark that alert was sent for this strategy"""
        self.last_alert_time[strategy_id] = datetime.utcnow()

    def get_drift_summary(self, drift_reports: List[Dict]) -> Dict:
        """
        Create summary of drift status across all strategies

        Args:
            drift_reports: List of drift reports from multiple strategies

        Returns:
            Summary dictionary
        """
        if not drift_reports:
            return {
                'total_strategies': 0,
                'drifted_strategies': 0,
                'critical_count': 0,
                'high_count': 0,
                'medium_count': 0,
                'low_count': 0
            }

        severity_counts = {
            'CRITICAL': 0,
            'HIGH': 0,
            'MEDIUM': 0,
            'LOW': 0,
            'NONE': 0
        }

        for report in drift_reports:
            severity = report.get('severity', 'NONE')
            severity_counts[severity] += 1

        drifted = sum(severity_counts[s] for s in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'])

        return {
            'total_strategies': len(drift_reports),
            'drifted_strategies': drifted,
            'drift_rate': drifted / len(drift_reports) if drift_reports else 0.0,
            'critical_count': severity_counts['CRITICAL'],
            'high_count': severity_counts['HIGH'],
            'medium_count': severity_counts['MEDIUM'],
            'low_count': severity_counts['LOW'],
            'healthy_count': severity_counts['NONE']
        }

    def recommend_action(self, drift_report: Dict) -> str:
        """
        Recommend action based on drift severity

        Args:
            drift_report: Drift report from detect_performance_drift()

        Returns:
            Recommended action string
        """
        severity = drift_report.get('severity', 'NONE')

        actions = {
            'CRITICAL': (
                "IMMEDIATE ACTION REQUIRED:\n"
                "1. Disable strategy immediately\n"
                "2. Review recent market conditions\n"
                "3. Retrain or replace strategy\n"
                "4. Investigate root cause of degradation"
            ),
            'HIGH': (
                "HIGH PRIORITY:\n"
                "1. Reduce position size by 50%\n"
                "2. Monitor closely for 24-48 hours\n"
                "3. Prepare backup strategy\n"
                "4. Schedule retraining if drift continues"
            ),
            'MEDIUM': (
                "MONITOR CLOSELY:\n"
                "1. Continue operation with caution\n"
                "2. Review next 10-20 trades\n"
                "3. Check for regime changes\n"
                "4. Consider retraining if pattern continues"
            ),
            'LOW': (
                "ADVISORY:\n"
                "1. Continue normal operation\n"
                "2. Log for future analysis\n"
                "3. Monitor weekly performance\n"
                "4. No immediate action required"
            ),
            'NONE': (
                "HEALTHY:\n"
                "Strategy performing within expected parameters"
            )
        }

        return actions.get(severity, "Unknown severity level")
