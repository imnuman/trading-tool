#!/usr/bin/env python3
"""
Test OANDA API Connection
Quick script to verify OANDA credentials are working
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from src.data.oanda_fetcher import OANDAFetcher
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Test OANDA connection"""
    load_dotenv('config/secrets.env')
    
    try:
        # Initialize OANDA fetcher
        fetcher = OANDAFetcher()
        
        # Test connection
        logger.info("Testing OANDA API connection...")
        if not fetcher.test_connection():
            logger.error("Connection test failed!")
            return False
        
        # Test getting current price
        logger.info("\nTesting price fetch...")
        price = fetcher.get_current_price('EURUSD')
        if price:
            logger.info(f"✅ Current EUR/USD Price:")
            logger.info(f"   Bid: {price['bid']:.5f}")
            logger.info(f"   Ask: {price['ask']:.5f}")
            logger.info(f"   Mid: {price['mid']:.5f}")
            logger.info(f"   Spread: {price['spread']:.5f}")
            logger.info(f"   Tradeable: {price['tradeable']}")
        else:
            logger.error("Failed to fetch price")
            return False
        
        # Test historical data
        logger.info("\nTesting historical data fetch...")
        hist_data = fetcher.get_historical_data('EURUSD', count=100, granularity='H1')
        if hist_data is not None and len(hist_data) > 0:
            logger.info(f"✅ Fetched {len(hist_data)} historical candles")
            logger.info(f"   Latest close: {hist_data['close'].iloc[-1]:.5f}")
            logger.info(f"   Date range: {hist_data.index[0]} to {hist_data.index[-1]}")
        else:
            logger.error("Failed to fetch historical data")
            return False
        
        logger.info("\n✅ All tests passed! OANDA integration is working.")
        return True
        
    except ValueError as e:
        logger.error(f"❌ Configuration error: {e}")
        logger.error("\n📝 Setup Instructions:")
        logger.error("1. Follow OANDA_SETUP.md to create an account and get API token")
        logger.error("2. Edit config/secrets.env and add your credentials:")
        logger.error("   OANDA_API_KEY=your_actual_token_here")
        logger.error("   OANDA_ACCOUNT_ID=your_actual_account_id_here")
        logger.error("   OANDA_ENVIRONMENT=practice")
        logger.error("\n💡 Quick Steps:")
        logger.error("   - Go to: https://www.oanda.com/us-en/trade/open-an-account/")
        logger.error("   - Create a Practice Account (free)")
        logger.error("   - Generate API token from Settings → API")
        logger.error("   - Copy Account ID from platform (top-right corner)")
        return False
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

