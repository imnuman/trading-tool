#!/bin/bash
# Quick deployment readiness check

echo "📋 Deployment Readiness Check"
echo "============================"
echo ""

# Check secrets
if [ -f config/secrets.env ]; then
    if grep -qE "(your_token|optional|your_)" config/secrets.env 2>/dev/null; then
        echo "❌ Secrets: Contains placeholder values"
    else
        echo "✅ Secrets: Configured"
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

# Check OANDA (optional)
if grep -q "OANDA_API_KEY" config/secrets.env 2>/dev/null && ! grep -qE "(optional|your_)" config/secrets.env 2>/dev/null; then
    echo "✅ OANDA: Configured"
else
    echo "⚠️  OANDA: Not configured (optional, will use yfinance)"
fi

# Check Telegram
if grep -q "TELEGRAM_BOT_TOKEN" config/secrets.env 2>/dev/null && ! grep -qE "(your_token|optional)" config/secrets.env 2>/dev/null; then
    echo "✅ Telegram: Configured"
else
    echo "❌ Telegram: Not configured"
fi

echo ""
echo "📝 Next Steps:"
echo "1. If database missing: python3 scripts/pre_deploy.py"
echo "2. If secrets need setup: Edit config/secrets.env"
echo "3. If ready: Follow AWS_DEPLOYMENT.md"
