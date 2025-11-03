#!/bin/bash
# Complete EC2 Setup Script
# Run this on your EC2 instance via Cursor terminal

set -e  # Exit on error

echo "🚀 Completing Trading Tool Setup on EC2..."
echo ""

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Not in trading-tool directory. Please cd to /home/ubuntu/trading-tool first"
    exit 1
fi

echo "✅ Current directory: $(pwd)"
echo ""

# Step 1: Verify venv is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Step 2: Check dependencies
echo "📦 Checking dependencies..."
if ! python3 -c "import pandas" 2>/dev/null; then
    echo "⚠️  Installing minimal dependencies..."
    pip install pandas>=2.1.0 numpy>=1.26.0 pyarrow>=14.0.0 yfinance>=0.2.32 python-telegram-bot>=20.0 python-dotenv>=1.0.0 sqlalchemy>=2.0.0 requests pydantic>=2.5.0 aiohttp>=3.9.0
fi

# Step 3: Verify secrets.env exists
echo "📝 Checking secrets.env..."
if [ ! -f "config/secrets.env" ]; then
    echo "⚠️  Creating secrets.env..."
    mkdir -p config
    cat > config/secrets.env << 'EOF'
TELEGRAM_BOT_TOKEN=8425324139:AAGXmo2h3_4xTbkMW-TiASELOlWtMryN5ho
OANDA_API_KEY=45450d8926fe5c97a7e1867062bdb12f-1d815a45c5b08c7737de801882b104c0
OANDA_ACCOUNT_ID=101-002-37553196-001
OANDA_ENVIRONMENT=practice
DATABASE_PATH=./data/strategies.db
MIN_CONFIDENCE_THRESHOLD=80
MIN_ENSEMBLE_AGREEMENT=0.80
MAX_DRAWDOWN_THRESHOLD=0.20
EOF
    chmod 600 config/secrets.env
fi

# Step 4: Create data directory
echo "📁 Creating data directory..."
mkdir -p data

# Step 5: Check if pre_deploy needs to run
echo "📊 Checking database status..."
if [ ! -f "data/strategies.db" ] || [ $(python3 -c "from src.utils.database import StrategyDatabase; db=StrategyDatabase(); print(len(db.get_top_strategies(min_confidence=50, min_trades=1, limit=1)))" 2>/dev/null || echo "0") -lt 5 ]; then
    echo "⚠️  Database missing or has <5 strategies. Running pre_deploy.py..."
    echo "⏱️  This will take 10-30 minutes..."
    source venv/bin/activate
    python3 scripts/pre_deploy.py || {
        echo "⚠️  Pre-deploy had issues, but continuing..."
    }
else
    echo "✅ Database has strategies, skipping pre_deploy"
fi

# Step 6: Setup systemd service
echo ""
echo "⚙️  Setting up systemd service..."
SERVICE_FILE="/etc/systemd/system/trading-bot.service"

sudo tee $SERVICE_FILE > /dev/null << 'EOF'
[Unit]
Description=Trading Tool Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/trading-tool
Environment="PATH=/home/ubuntu/trading-tool/venv/bin"
ExecStart=/home/ubuntu/trading-tool/venv/bin/python3 main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Service file created"

# Step 7: Enable and start service
echo ""
echo "🚀 Enabling and starting bot..."
sudo systemctl daemon-reload
sudo systemctl enable trading-bot
sudo systemctl start trading-bot

# Step 8: Check status
echo ""
echo "📊 Checking bot status..."
sleep 2
sudo systemctl status trading-bot --no-pager -l || true

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ SETUP COMPLETE!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📋 Useful commands:"
echo "   View logs:     sudo journalctl -u trading-bot -f"
echo "   Check status:  sudo systemctl status trading-bot"
echo "   Restart bot:   sudo systemctl restart trading-bot"
echo "   Stop bot:      sudo systemctl stop trading-bot"
echo ""
echo "🧪 Test in Telegram:"
echo "   1. Open Telegram"
echo "   2. Find: @trading_47_bot"
echo "   3. Send: /start"
echo "   4. Send: /signal"
echo ""

