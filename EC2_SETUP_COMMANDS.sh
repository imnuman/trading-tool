#!/bin/bash
# EC2 Setup Commands - Run these on your EC2 instance
# Copy and paste each section one at a time

set -e  # Exit on error

echo "🚀 Starting Trading Tool Setup on EC2..."
echo ""

# Step 1: Update System
echo "📦 Step 1: Updating system..."
sudo apt update && sudo apt upgrade -y

# Step 2: Install Dependencies
echo ""
echo "📦 Step 2: Installing dependencies..."
sudo apt install python3 python3-pip python3-venv git -y

# Step 3: Clone Repository
echo ""
echo "📦 Step 3: Cloning repository..."
git clone https://github.com/imnuman/trading-tool.git
cd trading-tool

# Step 4: Setup Virtual Environment
echo ""
echo "📦 Step 4: Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Step 5: Install Python Dependencies
echo ""
echo "📦 Step 5: Installing Python packages (this may take a few minutes)..."
pip install --upgrade pip
pip install -r requirements.txt

# Step 6: Create secrets.env
echo ""
echo "📝 Step 6: Creating secrets.env..."
echo "⚠️  You need to edit config/secrets.env with your credentials"
echo ""
cat > config/secrets.env << 'EOF'
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=8425324139:AAGXmo2h3_4xTbkMW-TiASELOlWtMryN5ho

# OANDA API Configuration
OANDA_API_KEY=45450d8926fe5c97a7e1867062bdb12f-1d815a45c5b08c7737de801882b104c0
OANDA_ACCOUNT_ID=101-002-37553196-001
OANDA_ENVIRONMENT=practice

# Database
DATABASE_PATH=./data/strategies.db

# Trading Parameters
MIN_CONFIDENCE_THRESHOLD=80
MIN_ENSEMBLE_AGREEMENT=0.80
MAX_DRAWDOWN_THRESHOLD=0.20
EOF

chmod 600 config/secrets.env
echo "✅ secrets.env created"
echo ""
echo "📝 Your credentials have been added to config/secrets.env"
echo ""

# Step 7: Create data directory
echo "📦 Step 7: Creating data directory..."
mkdir -p data

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Run pre-deployment: python3 scripts/pre_deploy.py"
echo "2. Setup systemd service: sudo nano /etc/systemd/system/trading-bot.service"
echo "3. Start the bot: sudo systemctl start trading-bot"
echo ""
echo "See DEPLOY_NOW.md for full instructions."

