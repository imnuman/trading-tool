#!/bin/bash
# Quick setup script for Trading Tool

set -e  # Exit on error

echo "🚀 Setting up Trading Tool..."

# Check if python3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is not installed"
    exit 1
fi

# Check if python3-venv is installed (try to create venv, will fail gracefully)
echo "Checking for python3-venv..."
if ! python3 -m venv --help &> /dev/null; then
    echo "⚠️  Warning: python3-venv may not be installed"
    echo "If venv creation fails, install it with:"
    echo "  sudo apt install python3-venv"
    echo ""
fi

# Remove existing venv if it exists
if [ -d "venv" ]; then
    echo "Removing existing virtual environment..."
    rm -rf venv
fi

# Create virtual environment
echo "Creating virtual environment..."
if ! python3 -m venv venv; then
    echo "❌ Error: Failed to create virtual environment"
    echo "Please install python3-venv:"
    echo "  sudo apt install python3-venv"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
python3 -m pip install --upgrade pip --quiet

# Install dependencies
echo "Installing dependencies (this may take a few minutes)..."
pip install -r requirements.txt

# Create data directory
echo "Creating data directory..."
mkdir -p data

# Copy secrets template
if [ ! -f config/secrets.env ]; then
    echo "Creating secrets.env from template..."
    cp config/secrets.env.example config/secrets.env
    echo "⚠️  Please edit config/secrets.env and add your Telegram bot token!"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit config/secrets.env and add your TELEGRAM_BOT_TOKEN"
echo "2. Activate venv: source venv/bin/activate"
echo "3. Run: python3 scripts/pre_deploy.py (Day 0 - data collection and backtesting)"
echo "4. Run: python3 main.py (Day 1 - start Telegram bot)"
echo ""
echo "To activate the virtual environment later, run:"
echo "  source venv/bin/activate"

