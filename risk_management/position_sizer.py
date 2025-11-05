"""
Confidence-Based Position Sizing

Position sizing rules:
- 80-100% confidence: 1% risk per trade
- 70-79% confidence: 0.75% risk per trade
- 65-69% confidence: 0.5% risk per trade
- <65% confidence: No trade
"""

from typing import Dict


class PositionSizer:
    """Calculate position sizes based on confidence and risk parameters"""

    def __init__(self, account_balance: float):
        """
        Initialize position sizer

        Args:
            account_balance: Current account balance
        """
        self.account_balance = account_balance

        # Confidence-based risk tiers
        self.risk_tiers = {
            (80, 100): 0.01,   # 1% risk
            (70, 79): 0.0075,  # 0.75% risk
            (65, 69): 0.005,   # 0.5% risk
        }

    def calculate_position_size(
        self,
        confidence: float,
        stop_loss_pips: float,
        pip_value: float
    ) -> float:
        """
        Calculate position size in lots

        Args:
            confidence: Signal confidence [0-1]
            stop_loss_pips: Stop loss distance in pips
            pip_value: Value of 1 pip for 1 lot

        Returns:
            Position size in lots (0 if confidence too low)
        """
        # TODO: Implement position sizing calculation
        pass

    def get_risk_percentage(self, confidence: float) -> float:
        """
        Get risk percentage for given confidence

        Args:
            confidence: Signal confidence [0-1]

        Returns:
            Risk percentage (0 if below threshold)
        """
        confidence_pct = confidence * 100

        for (lower, upper), risk_pct in self.risk_tiers.items():
            if lower <= confidence_pct <= upper:
                return risk_pct

        return 0.0  # Below minimum confidence
