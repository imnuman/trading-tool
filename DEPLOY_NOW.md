# Quick Deployment Guide - US East

## ✅ Pre-Flight Check

- [x] AWS credentials configured locally
- [x] AWS CLI installed
- [x] Region: us-east-1
- [x] Telegram bot token configured
- [x] OANDA credentials configured
- [x] Database has strategies

---

## 🚀 **Step 1: Launch EC2 Instance**

### Go to AWS Console:
1. Open: https://console.aws.amazon.com/ec2/
2. Make sure region is **US East (N. Virginia) - us-east-1** (top-right corner)
3. Click **"Launch Instance"**

### Configure Instance:

**Basic Settings:**
- **Name:** `trading-tool-bot`
- **AMI:** Ubuntu Server 22.04 LTS (Free tier eligible)
- **Instance Type:** `t2.micro` (Free tier) or `t3.micro` (~$7/month)
- **Key Pair:** 
  - Create new key pair OR
  - Use existing key pair
  - **⚠️ Save the `.pem` file if creating new!**

**Network Settings:**
- **VPC:** default
- **Subnet:** default
- **Auto-assign Public IP:** Enable
- **Security Group:** 
  - Allow SSH (port 22) from your IP
  - Or from anywhere (0.0.0.0/0) temporarily

**Configure Storage:**
- **Size:** 8 GB (free tier: 30 GB)
- **Volume Type:** gp3

**Review and Launch:**
- Click **"Launch Instance"**
- Wait for instance to start (1-2 minutes)

---

## 🔑 **Step 2: Create IAM Role (Optional but Recommended)**

1. Go to: https://console.aws.amazon.com/iam/
2. **Roles** → **Create role**
3. **AWS service** → **EC2** → Next
4. **Skip permissions** (no special policies needed) → Next
5. **Name:** `trading-tool-ec2-role`
6. **Create role**

### Attach to Instance:
1. Go back to EC2 Console → Instances
2. Select your instance
3. **Actions** → **Security** → **Modify IAM role**
4. Select `trading-tool-ec2-role`
5. **Update IAM role**

---

## 📝 **Step 3: Get Instance Details**

Note down:
- **Public IPv4 address:** (e.g., 54.123.45.67)
- **Instance ID:** (e.g., i-0abc123def456)

---

## 🔐 **Step 4: Connect to EC2**

```bash
# On your local machine
chmod 400 your-key.pem
ssh -i your-key.pem ubuntu@<YOUR_EC2_IP>
```

Replace `<YOUR_EC2_IP>` with the Public IPv4 address.

---

## ⚙️ **Step 5: Setup on EC2**

Once connected via SSH, run:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install python3 python3-pip python3-venv git -y

# Clone repository
git clone https://github.com/imnuman/trading-tool.git
cd trading-tool

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create secrets.env
nano config/secrets.env
```

**Add your credentials to `config/secrets.env`:**
```bash
TELEGRAM_BOT_TOKEN=8425324139:AAGXmo2h3_4xTbkMW-TiASELOlWtMryN5ho
OANDA_API_KEY=45450d8926fe5c97a7e1867062bdb12f-1d815a45c5b08c7737de801882b104c0
OANDA_ACCOUNT_ID=101-002-37553196-001
OANDA_ENVIRONMENT=practice
```

Save: `Ctrl+X`, then `Y`, then `Enter`

---

## 📊 **Step 6: Run Pre-Deployment**

```bash
# Still in venv
source venv/bin/activate

# Generate strategies
python3 scripts/pre_deploy.py
```

**Expected:** Takes 10-30 minutes, generates 1000+ strategies

---

## 🎯 **Step 7: Setup Systemd Service**

Create service file:

```bash
sudo nano /etc/systemd/system/trading-bot.service
```

Add:
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

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable trading-bot
sudo systemctl start trading-bot

# Check status
sudo systemctl status trading-bot

# View logs
sudo journalctl -u trading-bot -f
```

---

## ✅ **Step 8: Verify Deployment**

1. **Check bot is running:**
   ```bash
   sudo systemctl status trading-bot
   ```

2. **Test in Telegram:**
   - Find: @trading_47_bot
   - Send: `/start`
   - Send: `/signal`
   - Should respond!

3. **Monitor logs:**
   ```bash
   sudo journalctl -u trading-bot -f
   ```

---

## 🎉 **Done!**

Your bot is now running 24/7 on AWS!

**Useful Commands:**
```bash
# View logs
sudo journalctl -u trading-bot -f

# Restart bot
sudo systemctl restart trading-bot

# Stop bot
sudo systemctl stop trading-bot

# Update code
cd /home/ubuntu/trading-tool
git pull origin main
sudo systemctl restart trading-bot
```

---

## 💰 **Cost Estimate**

- **t2.micro (Free tier):** $0/month (first 12 months)
- **t3.micro:** ~$7-10/month
- **Data transfer:** Usually free (first 100 GB)

---

**Ready to start? Follow Step 1!** 🚀

