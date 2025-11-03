#!/bin/bash
# Quick deployment readiness check

echo "📋 Deployment Readiness Check"
echo "============================"
echo ""

# Check secrets
if [ -f config/secrets.env ]; then
    # More sophisticated check - verify actual values exist
    telegram=$(grep "^TELEGRAM_BOT_TOKEN=" config/secrets.env 2>/dev/null | cut -d'=' -f2- | tr -d '"' | tr -d "'")
    oanda_key=$(grep "^OANDA_API_KEY=" config/secrets.env 2>/dev/null | cut -d'=' -f2- | tr -d '"' | tr -d "'")
    
    if [ -z "$telegram" ] || echo "$telegram" | grep -qiE "(your_token|optional|your_|token_here)"; then
        echo "❌ Telegram Token: Not configured"
    elif [ ${#telegram} -lt 20 ]; then
        echo "⚠️  Telegram Token: Too short (may be invalid)"
    else
        echo "✅ Telegram Token: Configured (${#telegram} chars)"
    fi
    
    if [ -n "$oanda_key" ] && ! echo "$oanda_key" | grep -qiE "(your_|optional|token_here)"; then
        if [ ${#oanda_key} -gt 40 ]; then
            echo "✅ OANDA API Key: Configured (${#oanda_key} chars)"
        else
            echo "⚠️  OANDA API Key: May be invalid (too short)"
        fi
    else
        echo "⚠️  OANDA API Key: Not configured (optional)"
    fi
else
    echo "❌ Secrets: File missing (copy from secrets.env.example)"
fi

# Check database
if [ -f data/strategies.db ]; then
    count=$(python3 -c "from src.utils.database import StrategyDatabase; db=StrategyDatabase(); print(len(db.get_top_strategies(min_confidence=50, min_trades=1, limit=100)))" 2>/dev/null || echo "0")
    if [ "$count" -gt 0 ]; then
        echo "✅ Database: Has $count strategies"
    else
        echo "❌ Database: Empty or error (run pre_deploy.py)"
    fi
else
    echo "❌ Database: Not found (run pre_deploy.py)"
fi

# Check git
if [ -z "$(git status --porcelain 2>/dev/null)" ]; then
    echo "✅ Git: Clean"
else
    echo "⚠️  Git: Uncommitted changes"
fi

# Test connections
echo ""
echo "🔌 Connection Tests:"
python3 -c "
from telegram import Bot
from dotenv import load_dotenv
import os
import asyncio

load_dotenv('config/secrets.env')
token = os.getenv('TELEGRAM_BOT_TOKEN')

if token and len(token) > 20:
    try:
        bot = Bot(token)
        info = asyncio.run(bot.get_me())
        print('✅ Telegram: Connected (@' + info.username + ')')
    except:
        print('❌ Telegram: Connection failed')
else:
    print('❌ Telegram: Token missing or invalid')
" 2>/dev/null || echo "⚠️  Telegram: Could not test"

python3 -c "
from src.data.oanda_fetcher import OANDAFetcher
try:
    fetcher = OANDAFetcher()
    if fetcher.test_connection():
        print('✅ OANDA: Connected')
    else:
        print('⚠️  OANDA: Connection failed (optional)')
except:
    print('⚠️  OANDA: Not configured (optional)')
" 2>/dev/null || echo "⚠️  OANDA: Not configured (optional)"

echo ""
echo "📝 Next Steps:"
echo "1. If database missing: python3 scripts/pre_deploy.py"
echo "2. If secrets need setup: Edit config/secrets.env"
echo "3. If ready: Follow AWS_DEPLOYMENT.md"
