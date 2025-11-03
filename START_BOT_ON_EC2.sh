#!/bin/bash
# Start the Trading Bot on EC2
# Run this after pre_deploy.py completes

echo "🚀 Starting Trading Bot..."
echo ""

# Step 1: Stop bot if running
sudo systemctl stop trading-bot 2>/dev/null || true

# Step 2: Verify database has strategies
echo "📊 Checking database..."
STRATEGY_COUNT=$(python3 -c "from src.utils.database import StrategyDatabase; db=StrategyDatabase(); print(len(db.get_top_strategies(min_confidence=50, min_trades=1, limit=100)))" 2>/dev/null || echo "0")

if [ "$STRATEGY_COUNT" -lt 1 ]; then
    echo "❌ No strategies in database. Please run: python3 scripts/pre_deploy.py"
    exit 1
fi

echo "✅ Found $STRATEGY_COUNT strategies in database"
echo ""

# Step 3: Start the bot
echo "🚀 Starting bot service..."
sudo systemctl start trading-bot

# Step 4: Wait a moment
sleep 3

# Step 5: Check status
echo ""
echo "📊 Bot Status:"
sudo systemctl status trading-bot --no-pager -l | head -15

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ Bot started!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📋 Useful commands:"
echo "   View logs:     sudo journalctl -u trading-bot -f"
echo "   Check status:  sudo systemctl status trading-bot"
echo "   Restart:       sudo systemctl restart trading-bot"
echo ""
echo "🧪 Test in Telegram:"
echo "   1. Open Telegram"
echo "   2. Find: @trading_47_bot"
echo "   3. Send: /start"
echo "   4. Send: /signal"
echo ""

