# Complete EC2 Setup Instructions

Since you're connected to EC2 via Cursor Remote-SSH, follow these steps:

---

## **Quick Setup (Recommended)**

### **Option 1: Run the automated script**

In Cursor's terminal (which is connected to EC2), run:

```bash
cd /home/ubuntu/trading-tool
bash EC2_COMPLETE_SETUP.sh
```

This script will:
- ✅ Check/install dependencies
- ✅ Create secrets.env
- ✅ Run pre_deploy.py (if needed)
- ✅ Setup systemd service
- ✅ Start the bot
- ✅ Show status

---

### **Option 2: Manual setup (if script fails)**

Run these commands one by one in Cursor's terminal:

#### **Step 1: Navigate and activate venv**
```bash
cd /home/ubuntu/trading-tool
source venv/bin/activate
```

#### **Step 2: Verify dependencies**
```bash
python3 -c "import pandas, numpy, yfinance; print('✅ Dependencies OK')"
```

If it fails:
```bash
pip install pandas>=2.1.0 numpy>=1.26.0 pyarrow>=14.0.0 yfinance>=0.2.32 python-telegram-bot>=20.0 python-dotenv>=1.0.0 sqlalchemy>=2.0.0 requests pydantic>=2.5.0 aiohttp>=3.9.0
```

#### **Step 3: Verify secrets.env**
```bash
cat config/secrets.env
```

If missing or empty:
```bash
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
```

#### **Step 4: Run pre-deployment (if needed)**
```bash
# Check if database exists and has strategies
python3 -c "from src.utils.database import StrategyDatabase; db=StrategyDatabase(); print(len(db.get_top_strategies(min_confidence=50, min_trades=1, limit=1)))"
```

If returns 0 or error:
```bash
python3 scripts/pre_deploy.py
```
⏱️ Takes 10-30 minutes

#### **Step 5: Create systemd service**
```bash
sudo nano /etc/systemd/system/trading-bot.service
```

Paste:
```ini
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

[Install]
WantedBy=multi-user.target
```

Save: `Ctrl+X`, `Y`, `Enter`

#### **Step 6: Enable and start**
```bash
sudo systemctl daemon-reload
sudo systemctl enable trading-bot
sudo systemctl start trading-bot
```

#### **Step 7: Check status**
```bash
sudo systemctl status trading-bot
```

---

## **Verify Everything Works**

### **Check bot is running:**
```bash
sudo systemctl status trading-bot
```

Should show: `active (running)`

### **View logs:**
```bash
sudo journalctl -u trading-bot -f
```

### **Test in Telegram:**
1. Open Telegram
2. Find: @trading_47_bot
3. Send: `/start`
4. Send: `/signal`

---

## **Troubleshooting**

### Bot not starting:
```bash
# Check logs for errors
sudo journalctl -u trading-bot -n 50
```

### Dependencies missing:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Database missing:
```bash
python3 scripts/pre_deploy.py
```

---

**Start with Option 1 (automated script) - it's easiest!** 🚀

