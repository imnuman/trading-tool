"""
Configuration Module
Centralized configuration management with validation
"""

import os
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)


class Config:
    """Application configuration with validation"""

    def __init__(self):
        """Initialize configuration from environment variables"""
        # Get project root directory
        self.PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()

        # Load environment variables
        env_path = self.PROJECT_ROOT / 'config' / 'secrets.env'
        if env_path.exists():
            load_dotenv(env_path)
        else:
            logger.warning(f"Config file not found: {env_path}")

        # Telegram Configuration
        self.TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
        allowed_users_str = os.getenv('TELEGRAM_ALLOWED_USERS', '')
        self.TELEGRAM_ALLOWED_USERS = [
            user_id.strip()
            for user_id in allowed_users_str.split(',')
            if user_id.strip()
        ]

        # Database Configuration
        self.DATABASE_PATH = Path(
            os.getenv('DATABASE_PATH', str(self.PROJECT_ROOT / 'data' / 'strategies.db'))
        )

        # Trading Configuration
        self.MIN_CONFIDENCE_THRESHOLD = float(os.getenv('MIN_CONFIDENCE_THRESHOLD', '80.0'))
        self.MIN_AGREEMENT_THRESHOLD = float(os.getenv('MIN_AGREEMENT_THRESHOLD', '0.80'))
        self.DEFAULT_PAIRS = os.getenv('DEFAULT_PAIRS', 'EUR/USD,GBP/USD,XAU/USD').split(',')

        # Signal Polling Configuration (for 24/7 notifications)
        self.ENABLE_AUTO_SIGNALS = os.getenv('ENABLE_AUTO_SIGNALS', 'false').lower() == 'true'
        self.AUTO_SIGNAL_INTERVAL = int(os.getenv('AUTO_SIGNAL_INTERVAL', '3600'))  # 1 hour default
        self.AUTO_SIGNAL_PAIRS = os.getenv('AUTO_SIGNAL_PAIRS', 'EUR/USD').split(',')

        # Learning Loop Configuration
        self.LEARNING_LOOP_INTERVAL = int(os.getenv('LEARNING_LOOP_INTERVAL', '3600'))  # 1 hour

        # Logging Configuration
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        self.LOG_FILE = Path(os.getenv('LOG_FILE', str(self.PROJECT_ROOT / 'logs' / 'trading_bot.log')))

        # Cache Configuration
        self.CACHE_DIR = Path(os.getenv('CACHE_DIR', str(self.PROJECT_ROOT / 'data' / 'cache')))

        # Validate configuration
        self.validate()

    def validate(self):
        """Validate critical configuration values"""
        errors = []

        if not self.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN is not set in config/secrets.env")

        if self.MIN_CONFIDENCE_THRESHOLD < 0 or self.MIN_CONFIDENCE_THRESHOLD > 100:
            errors.append(f"MIN_CONFIDENCE_THRESHOLD must be between 0 and 100, got {self.MIN_CONFIDENCE_THRESHOLD}")

        if self.MIN_AGREEMENT_THRESHOLD < 0 or self.MIN_AGREEMENT_THRESHOLD > 1:
            errors.append(f"MIN_AGREEMENT_THRESHOLD must be between 0 and 1, got {self.MIN_AGREEMENT_THRESHOLD}")

        if self.AUTO_SIGNAL_INTERVAL < 60:
            errors.append(f"AUTO_SIGNAL_INTERVAL must be at least 60 seconds, got {self.AUTO_SIGNAL_INTERVAL}")

        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {err}" for err in errors)
            raise ValueError(error_msg)

        logger.info("✅ Configuration validated successfully")

    def __repr__(self):
        """String representation (masks sensitive data)"""
        token_preview = f"{self.TELEGRAM_BOT_TOKEN[:10]}..." if self.TELEGRAM_BOT_TOKEN else "Not set"
        return f"""
Config(
    TELEGRAM_BOT_TOKEN={token_preview},
    ALLOWED_USERS={len(self.TELEGRAM_ALLOWED_USERS)} users,
    DATABASE_PATH={self.DATABASE_PATH},
    MIN_CONFIDENCE={self.MIN_CONFIDENCE_THRESHOLD}%,
    AUTO_SIGNALS={'enabled' if self.ENABLE_AUTO_SIGNALS else 'disabled'},
    LOG_LEVEL={self.LOG_LEVEL}
)
        """.strip()


# Global config instance
config = Config()
