# AWS Deployment Guide

Complete guide for deploying the Trading Tool to AWS.

---

## Prerequisites

- ✅ AWS Account (you mentioned you have one)
- ✅ OANDA API credentials (see `OANDA_SETUP.md`)
- ✅ Telegram Bot Token
- ✅ Code pushed to GitHub

---

## Option 1: AWS EC2 (Recommended for Full Control)

### Step 1: Launch EC2 Instance

1. **Go to AWS Console:**
   - Navigate to: https://console.aws.amazon.com/ec2/
   - Click "Launch Instance"

2. **Configure Instance:**
   - **Name:** trading-tool-bot
   - **AMI:** Ubuntu 22.04 LTS (free tier eligible)
   - **Instance Type:** `t2.micro` (free tier) or `t3.micro` (~$7/month)
   - **Key Pair:** Create new or use existing (save the `.pem` file!)

3. **Network Settings:**
   - Allow SSH (port 22) from your IP
   - Security Group: `default` or create new one

4. **Storage:**
   - 8 GB is enough (free tier: 30 GB)
   - **Volume Type:** gp3

5. **Review and Launch:**
   - Click "Launch Instance"

### Step 2: Connect to EC2 Instance

```bash
# On your local machine
chmod 400 your-key.pem
ssh -i your-key.pem ubuntu@<YOUR_EC2_IP>
```

**Get EC2 IP:**
- Go to EC2 Console → Instances
- Copy "Public IPv4 address"

### Step 3: Setup on EC2

Once connected via SSH:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.9+
sudo apt install python3 python3-pip python3-venv git -y

# Clone repository
git clone https://github.com/imnuman/trading-tool.git
cd trading-tool

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create secrets.env
nano config/secrets.env
```

Add your credentials:
```bash
TELEGRAM_BOT_TOKEN=your_token_here
OANDA_API_KEY=your_oanda_key_here
OANDA_ACCOUNT_ID=your_account_id_here
OANDA_ENVIRONMENT=practice
```

### Step 4: Run Pre-Deployment

```bash
# Still in venv
source venv/bin/activate

# Generate strategies
python3 scripts/pre_deploy.py
```

This will take 5-30 minutes depending on strategy count.

### Step 5: Setup as System Service (24/7 Operation)

Create systemd service:

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

## Option 2: AWS Lightsail (Easier Setup)

### Step 1: Create Lightsail Instance

1. **Go to Lightsail:**
   - https://lightsail.aws.amazon.com/
   - Click "Create instance"

2. **Choose:**
   - **Platform:** Linux/Unix
   - **Blueprint:** Ubuntu 22.04 LTS
   - **Instance Plan:** $3.50/month (1 GB RAM) or higher
   - **Name:** trading-tool

3. **Click "Create instance"**

### Step 2: Connect and Setup

Click "Connect using SSH" in Lightsail console, then:

```bash
# Same setup as EC2
git clone https://github.com/imnuman/trading-tool.git
cd trading-tool
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create secrets.env
nano config/secrets.env
# (Add credentials same as EC2)

# Run pre-deploy
python3 scripts/pre_deploy.py

# Setup systemd service (same as EC2)
sudo nano /etc/systemd/system/trading-bot.service
# (Copy service config from EC2 section)
sudo systemctl enable trading-bot
sudo systemctl start trading-bot
```

---

## Option 3: AWS Elastic Beanstalk (Managed)

### Step 1: Prepare Application

Create `Procfile`:
```bash
web: python3 main.py
```

Create `.ebextensions/python.config`:
```yaml
option_settings:
  aws:elasticbeanstalk:application:environment:
    PYTHONPATH: "/var/app/current:$PYTHONPATH"
```

### Step 2: Initialize Beanstalk

```bash
# Install EB CLI
pip install awsebcli

# Initialize
eb init -p python-3.9 trading-tool --region us-east-1

# Create environment
eb create trading-tool-env

# Set environment variables
eb setenv TELEGRAM_BOT_TOKEN=your_token \
          OANDA_API_KEY=your_key \
          OANDA_ACCOUNT_ID=your_id \
          OANDA_ENVIRONMENT=practice

# Deploy
eb deploy
```

---

## Environment Variables Setup

For all options, set these in `config/secrets.env`:

```bash
# Telegram
TELEGRAM_BOT_TOKEN=your_token_from_botfather

# OANDA (for real-time data)
OANDA_API_KEY=your_oanda_api_token
OANDA_ACCOUNT_ID=your_account_id
OANDA_ENVIRONMENT=practice  # or 'live'

# Optional: AWS credentials (if needed)
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_DEFAULT_REGION=us-east-1
```

---

## Running Pre-Deployment on AWS

Before starting the bot, generate strategies:

```bash
cd /home/ubuntu/trading-tool
source venv/bin/activate
python3 scripts/pre_deploy.py
```

**Expected output:**
- Fetches historical data (from OANDA or yfinance)
- Generates 1000+ strategies
- Backtests and filters
- Saves to `data/strategies.db`

**Time:** 5-30 minutes depending on strategy count

---

## Monitoring & Logs

### View Logs (Systemd Service):

```bash
# Real-time logs
sudo journalctl -u trading-bot -f

# Last 100 lines
sudo journalctl -u trading-bot -n 100

# Since boot
sudo journalctl -u trading-bot -b
```

### View Application Logs:

```bash
# If logging to file
tail -f logs/trading-tool.log

# Or check Python output
ps aux | grep python
```

### Monitor Resource Usage:

```bash
# CPU and memory
htop

# Disk space
df -h

# Network
netstat -tuln
```

---

## Auto-Restart on Reboot

If using systemd (EC2/Lightsail), the service auto-starts on reboot.

To verify:
```bash
sudo systemctl is-enabled trading-bot
# Should return: enabled
```

---

## Updating the Application

### Pull Latest Code:

```bash
cd /home/ubuntu/trading-tool
git pull origin main

# Restart service
sudo systemctl restart trading-bot
```

### Update Dependencies:

```bash
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart trading-bot
```

---

## Cost Estimation

### EC2 t2.micro (Free Tier):
- **First 12 months:** FREE (750 hours/month)
- **After:** ~$7-10/month

### EC2 t3.micro:
- **Cost:** ~$7-10/month

### Lightsail $3.50 plan:
- **Cost:** $3.50/month
- **Includes:** 1 GB RAM, 1 vCPU, 40 GB SSD

### Lightsail $5 plan:
- **Cost:** $5/month
- **Includes:** 2 GB RAM, 1 vCPU, 60 GB SSD

### Data Transfer:
- **First 100 GB/month:** Usually free
- **After:** ~$0.09/GB

**Total Estimated Cost:** $3.50 - $10/month

---

## Security Best Practices

1. **Keep secrets.env secure:**
   ```bash
   chmod 600 config/secrets.env
   ```

2. **Firewall (Security Groups):**
   - Only allow SSH from your IP
   - No public web ports needed

3. **Regular Updates:**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

4. **Use IAM roles** (advanced):
   - Attach IAM role to EC2 instance
   - Don't store AWS keys in code

---

## Troubleshooting

### Bot Not Starting:

```bash
# Check logs
sudo journalctl -u trading-bot -n 50

# Check if process is running
ps aux | grep python

# Test manually
cd /home/ubuntu/trading-tool
source venv/bin/activate
python3 main.py
```

### Out of Memory:

- Upgrade to larger instance (t3.small or Lightsail $10 plan)
- Reduce number of strategies in ensemble

### Connection Issues:

```bash
# Test OANDA connection
python3 scripts/test_oanda_connection.py

# Test Telegram
curl https://api.telegram.org/bot<TOKEN>/getMe
```

---

## Quick Deploy Script

Save as `deploy.sh`:

```bash
#!/bin/bash
set -e

echo "🚀 Deploying Trading Tool..."

# Pull latest
git pull origin main

# Activate venv
source venv/bin/activate

# Update dependencies
pip install -r requirements.txt --quiet

# Restart service
sudo systemctl restart trading-bot

echo "✅ Deployment complete!"
echo "View logs: sudo journalctl -u trading-bot -f"
```

Make executable:
```bash
chmod +x deploy.sh
```

Use:
```bash
./deploy.sh
```

---

## Next Steps After Deployment

1. ✅ Test bot in Telegram: `/signal`, `/chart`, `/stats`
2. ✅ Monitor logs for first 24 hours
3. ✅ Set up CloudWatch alarms (optional)
4. ✅ Schedule regular backups of `data/strategies.db`
5. ✅ Set up automated updates (git pull + restart)

---

**Ready to deploy? Start with Option 1 (EC2) for full control!** 🚀

