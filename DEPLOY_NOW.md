# 🚀 Deploy Trading Bot to AWS EC2 - Quick Start Guide

**AWS Account:** 980104576869
**Region:** us-east-1 (US East N. Virginia)
**User:** ncldev
**Status:** ✅ Ready to Deploy

---

## 📋 Pre-Deployment Checklist

✅ AWS credentials working
✅ Telegram bot configured
✅ OANDA API connected
✅ Database with 5 strategies loaded
✅ Region set to us-east-1

---

## 🎯 STEP 1: Launch EC2 Instance

### Option A: Using AWS Console (Recommended for First Time)

1. **Open EC2 Console:**
   ```
   https://console.aws.amazon.com/ec2/
   ```

2. **Verify Region:** Top-right corner should show "US East (N. Virginia) us-east-1"

3. **Click "Launch Instance"**

4. **Configure Instance:**

   | Setting | Value |
   |---------|-------|
   | **Name** | `trading-tool-bot` |
   | **AMI** | Ubuntu Server 22.04 LTS (Free tier eligible) |
   | **Instance Type** | `t2.micro` (Free tier) or `t3.micro` |
   | **Key Pair** | Create new: `trading-bot-key` (Download .pem file!) |
   | **Network** | Default VPC |
   | **Security Group** | Create new (see below) |
   | **Storage** | 8 GB gp3 (or 10 GB for more space) |

5. **Security Group Configuration:**
   - **Name:** `trading-bot-sg`
   - **Inbound Rules:**
     - Type: SSH, Port: 22, Source: My IP (Your current IP)
   - **Outbound Rules:**
     - All traffic (default)

6. **Click "Launch Instance"**

7. **Wait 2-3 minutes** for instance to start

8. **Get Instance IP:**
   - Go to EC2 Dashboard → Instances
   - Select your instance
   - Copy "Public IPv4 address" (e.g., 54.123.45.67)

### Option B: Using AWS CLI (Advanced)

```bash
# Create key pair
aws ec2 create-key-pair \
  --key-name trading-bot-key \
  --query 'KeyMaterial' \
  --output text > trading-bot-key.pem

chmod 400 trading-bot-key.pem

# Create security group
aws ec2 create-security-group \
  --group-name trading-bot-sg \
  --description "Security group for trading bot" \
  --region us-east-1

# Get your current IP
MY_IP=$(curl -s https://checkip.amazonaws.com)

# Allow SSH from your IP
aws ec2 authorize-security-group-ingress \
  --group-name trading-bot-sg \
  --protocol tcp \
  --port 22 \
  --cidr $MY_IP/32 \
  --region us-east-1

# Launch instance
aws ec2 run-instances \
  --image-id ami-0c7217cdde317cfec \
  --instance-type t2.micro \
  --key-name trading-bot-key \
  --security-groups trading-bot-sg \
  --region us-east-1 \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=trading-tool-bot}]' \
  --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":10,"VolumeType":"gp3"}}]'

# Get instance IP (wait 2 minutes first)
aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=trading-tool-bot" \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text \
  --region us-east-1
```

---

## 🔐 STEP 2: Connect to EC2 Instance

### 2.1 Prepare SSH Key

```bash
# Set correct permissions on your key file
chmod 400 trading-bot-key.pem

# Move to secure location (optional but recommended)
mkdir -p ~/.ssh/aws-keys
mv trading-bot-key.pem ~/.ssh/aws-keys/
```

### 2.2 Connect via SSH

```bash
# Replace <YOUR_EC2_IP> with your instance's public IP
ssh -i ~/.ssh/aws-keys/trading-bot-key.pem ubuntu@<YOUR_EC2_IP>

# Example:
# ssh -i ~/.ssh/aws-keys/trading-bot-key.pem ubuntu@54.123.45.67
```

**First time connecting?** Type `yes` when asked about host authenticity.

**Connection successful?** You should see:
```
ubuntu@ip-xxx-xxx-xxx-xxx:~$
```

---

## ⚙️ STEP 3: Setup on EC2 Instance

**ALL COMMANDS BELOW RUN ON THE EC2 INSTANCE**

### 3.1 Update System

```bash
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y python3.11 python3.11-venv python3-pip git htop
```

### 3.2 Clone Repository

```bash
cd ~
git clone https://github.com/imnuman/trading-tool.git
cd trading-tool
```

**OR** if you need to upload files from local machine:

```bash
# On your LOCAL machine (not EC2):
cd /home/user/trading-tool
scp -i ~/.ssh/aws-keys/trading-bot-key.pem -r . ubuntu@<YOUR_EC2_IP>:~/trading-tool/
```

### 3.3 Create Virtual Environment

```bash
cd ~/trading-tool
python3.11 -m venv venv
source venv/bin/activate

# Verify Python version
python --version  # Should show Python 3.11.x
```

### 3.4 Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt

# This takes 3-5 minutes
# You'll see packages being installed
```

**If you get errors with multitasking:**
```bash
pip install multitasking==0.0.11 --no-build-isolation
pip install -r requirements.txt
```

### 3.5 Create Directories

```bash
mkdir -p data logs data/cache
```

---

## 🔑 STEP 4: Configure Secrets

### 4.1 Create Configuration File

```bash
cd ~/trading-tool
nano config/secrets.env
```

### 4.2 Paste This Configuration

```bash
# =============================================================================
# PRODUCTION CONFIGURATION
# =============================================================================

# Telegram Bot
TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN_HERE
TELEGRAM_ALLOWED_USERS=YOUR_TELEGRAM_USER_ID_HERE

# 24/7 Automatic Signals
ENABLE_AUTO_SIGNALS=true
AUTO_SIGNAL_INTERVAL=3600
AUTO_SIGNAL_PAIRS=EUR/USD,GBP/USD,XAU/USD

# Trading Parameters
MIN_CONFIDENCE_THRESHOLD=80.0
MIN_AGREEMENT_THRESHOLD=0.80
DEFAULT_PAIRS=EUR/USD,GBP/USD,XAU/USD

# Database
DATABASE_PATH=./data/strategies.db

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/trading_bot.log

# Cache
CACHE_DIR=./data/cache

# OANDA API (if you have it)
OANDA_API_KEY=your_oanda_api_key_here
OANDA_ACCOUNT_ID=your_account_id_here
```

**Save and exit:** `Ctrl+O`, `Enter`, `Ctrl+X`

### 4.3 Get Your Telegram User ID

If you don't know your Telegram user ID:

1. Open Telegram
2. Search for `@userinfobot`
3. Start the bot and send `/start`
4. Copy your user ID
5. Add it to `TELEGRAM_ALLOWED_USERS` in the config above

---

## 📊 STEP 5: Generate Trading Strategies

**This is CRITICAL - don't skip this step!**

```bash
cd ~/trading-tool
source venv/bin/activate
python3 scripts/pre_deploy.py
```

**Expected output:**
```
[Step 1/4] Collecting historical data...
Fetched data for 6 pairs
[Step 2/4] Generating strategies...
Generated 1000 strategies
[Step 3/4] Backtesting strategies on TRAINING data...
Backtested 1000/1000 strategies...
[Step 4/4] Filtering strategies...
Filtered to 150 high-performing strategies
[Step 4b/4] Validating on TEST data...
Validation complete: 120/150 strategies passed

✅ Ready for Day 1 deployment!
```

**Duration:** 5-15 minutes depending on instance type

**If you already have a database with 5 strategies:**
```bash
# Option 1: Use existing database (upload it)
# On your local machine:
scp -i ~/.ssh/aws-keys/trading-bot-key.pem \
  data/strategies.db \
  ubuntu@<YOUR_EC2_IP>:~/trading-tool/data/

# Option 2: Generate new strategies (recommended for production)
# Run pre_deploy.py as shown above
```

### 5.1 Verify Database

```bash
ls -lh data/strategies.db
sqlite3 data/strategies.db "SELECT COUNT(*) FROM strategies;"
# Should show number > 0
```

---

## 🚀 STEP 6: Start the Bot (Manual Test)

### 6.1 Test Run First

```bash
cd ~/trading-tool
source venv/bin/activate
python3 main.py
```

**Expected output:**
```
2025-11-02 20:30:00 - root - INFO - Starting Trading Tool Telegram Bot...
2025-11-02 20:30:00 - root - INFO - Loading top strategies from database...
2025-11-02 20:30:00 - root - INFO - Loaded 120 strategies from database
2025-11-02 20:30:00 - root - INFO - Ensemble initialized with 50 strategies
2025-11-02 20:30:00 - root - INFO - ✅ Learning loop started in background
2025-11-02 20:30:00 - root - INFO - ✅ Bot initialized and ready!
2025-11-02 20:30:00 - root - INFO - Telegram bot is running. Press Ctrl+C to stop.
```

### 6.2 Test Telegram Bot

1. Open Telegram
2. Find your bot
3. Send `/start`

**Expected response:**
```
🤖 Trading Tool AI Bot

Welcome! I'm your AI-powered trading assistant.

Available Commands:
/signal - Get high-confidence trading signal
...
```

4. Try `/signal`
5. Try `/stats`

**If everything works, press `Ctrl+C` to stop the bot**

---

## 🔄 STEP 7: Setup systemd Service (24/7 Operation)

### 7.1 Edit Service File

```bash
cd ~/trading-tool
nano trading-bot.service
```

**Update these lines:**
```ini
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/trading-tool
ExecStart=/home/ubuntu/trading-tool/venv/bin/python3 /home/ubuntu/trading-tool/main.py
```

**Save:** `Ctrl+O`, `Enter`, `Ctrl+X`

### 7.2 Install Service

```bash
sudo cp trading-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable trading-bot
```

### 7.3 Start Service

```bash
sudo systemctl start trading-bot
```

### 7.4 Check Status

```bash
sudo systemctl status trading-bot
```

**Expected output:**
```
● trading-bot.service - Trading Tool - AI-Powered Forex Signal Bot
     Loaded: loaded (/etc/systemd/system/trading-bot.service; enabled)
     Active: active (running) since ...
```

**Press `q` to exit**

### 7.5 View Logs in Real-Time

```bash
# Option 1: System logs
sudo journalctl -u trading-bot -f

# Option 2: Application logs
tail -f ~/trading-tool/logs/trading_bot.log
```

**Press `Ctrl+C` to stop viewing logs**

---

## ✅ STEP 8: Verify Everything is Working

### 8.1 Check Bot is Running

```bash
sudo systemctl status trading-bot
```

### 8.2 Test Telegram Commands

1. `/start` - Welcome message
2. `/signal` - Get signal (or "No Trade")
3. `/chart EUR/USD` - Chart analysis
4. `/stats` - Performance statistics
5. `/help` - Help message

### 8.3 Check Resource Usage

```bash
# CPU and memory
htop

# Disk space
df -h

# Bot process
ps aux | grep python
```

### 8.4 Verify Auto-Signals (if enabled)

```bash
# Check logs for auto-signal polling
sudo journalctl -u trading-bot -f | grep -i "signal"

# You should see entries every hour if AUTO_SIGNALS enabled
```

---

## 🔧 STEP 9: Useful Commands

### Service Management

```bash
# Start bot
sudo systemctl start trading-bot

# Stop bot
sudo systemctl stop trading-bot

# Restart bot
sudo systemctl restart trading-bot

# View status
sudo systemctl status trading-bot

# View logs
sudo journalctl -u trading-bot -f

# View last 100 lines
sudo journalctl -u trading-bot -n 100
```

### Database Management

```bash
cd ~/trading-tool

# Count strategies
sqlite3 data/strategies.db "SELECT COUNT(*) FROM strategies;"

# View top 10 strategies
sqlite3 data/strategies.db "SELECT name, confidence_score, win_rate FROM backtest_results ORDER BY confidence_score DESC LIMIT 10;"

# View recent signals
sqlite3 data/strategies.db "SELECT * FROM signals ORDER BY timestamp DESC LIMIT 10;"

# Backup database
cp data/strategies.db data/strategies.db.backup-$(date +%Y%m%d)
```

### Log Management

```bash
# View recent logs
tail -100 logs/trading_bot.log

# Follow logs in real-time
tail -f logs/trading_bot.log

# Search for errors
grep -i error logs/trading_bot.log

# Clear old logs (optional)
> logs/trading_bot.log
```

### System Monitoring

```bash
# Resource usage
htop

# Memory
free -h

# Disk usage
df -h

# Check bot process
ps aux | grep python

# Network connections
netstat -tlnp | grep python
```

---

## 🛡️ STEP 10: Setup Automated Backups (Recommended)

### 10.1 Create S3 Bucket for Backups

```bash
# On your LOCAL machine (not EC2):
aws s3 mb s3://trading-bot-backups-980104576869 --region us-east-1
```

### 10.2 Create Backup Script on EC2

```bash
# On EC2 instance:
nano ~/trading-tool/scripts/backup.sh
```

**Paste this script:**

```bash
#!/bin/bash
# Backup script for trading bot

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/ubuntu/trading-tool/data"
S3_BUCKET="s3://trading-bot-backups-980104576869"

# Backup database
aws s3 cp $BACKUP_DIR/strategies.db \
  $S3_BUCKET/database/strategies-$DATE.db

# Backup logs (compressed)
tar -czf /tmp/logs-$DATE.tar.gz /home/ubuntu/trading-tool/logs
aws s3 cp /tmp/logs-$DATE.tar.gz \
  $S3_BUCKET/logs/logs-$DATE.tar.gz
rm /tmp/logs-$DATE.tar.gz

# Keep only last 30 days of backups
aws s3 ls $S3_BUCKET/database/ | \
  sort | head -n -30 | awk '{print $4}' | \
  xargs -I {} aws s3 rm $S3_BUCKET/database/{}

echo "Backup completed: $DATE"
```

**Make executable:**
```bash
chmod +x ~/trading-tool/scripts/backup.sh
```

### 10.3 Setup Daily Backups (Cron)

```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 2 AM):
0 2 * * * /home/ubuntu/trading-tool/scripts/backup.sh >> /home/ubuntu/trading-tool/logs/backup.log 2>&1
```

### 10.4 Test Backup

```bash
~/trading-tool/scripts/backup.sh

# Verify in S3
aws s3 ls s3://trading-bot-backups-980104576869/database/
```

---

## 📊 STEP 11: Setup CloudWatch Monitoring (Optional)

### 11.1 Install CloudWatch Agent

```bash
# On EC2 instance:
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb
```

### 11.2 Configure CloudWatch

```bash
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-config-wizard

# Follow prompts:
# - Instance (not ECS)
# - Standard metrics
# - Include disk and memory metrics
```

### 11.3 Start CloudWatch Agent

```bash
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -s \
  -c file:/opt/aws/amazon-cloudwatch-agent/bin/config.json
```

---

## 🚨 TROUBLESHOOTING

### Bot Won't Start

```bash
# Check logs for errors
sudo journalctl -u trading-bot -n 50

# Test manually
cd ~/trading-tool
source venv/bin/activate
python3 main.py
# Read error messages

# Common issues:
# 1. Missing TELEGRAM_BOT_TOKEN
nano config/secrets.env  # Verify token is set

# 2. No strategies in database
python3 scripts/pre_deploy.py

# 3. Permission issues
sudo chown -R ubuntu:ubuntu /home/ubuntu/trading-tool
```

### No Signals Being Generated

```bash
# Check if bot is running
sudo systemctl status trading-bot

# Check logs
tail -100 logs/trading_bot.log

# Test signal manually via Telegram
/signal

# Generate more strategies if needed
cd ~/trading-tool
source venv/bin/activate
python3 scripts/pre_deploy.py
```

### Out of Memory

```bash
# Check memory usage
free -h

# Add swap space
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Disk Full

```bash
# Check disk usage
df -h

# Clear old logs
sudo journalctl --vacuum-time=7d

# Clear cache
rm -rf ~/trading-tool/data/cache/*

# Archive old logs
tar -czf logs-archive-$(date +%Y%m%d).tar.gz logs/*.log
rm logs/*.log
```

### Can't Connect via SSH

```bash
# Verify instance is running
aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=trading-tool-bot" \
  --query 'Reservations[0].Instances[0].State.Name' \
  --region us-east-1

# Check security group allows your IP
aws ec2 describe-security-groups \
  --group-names trading-bot-sg \
  --region us-east-1

# Update security group with your current IP
MY_IP=$(curl -s https://checkip.amazonaws.com)
aws ec2 authorize-security-group-ingress \
  --group-name trading-bot-sg \
  --protocol tcp \
  --port 22 \
  --cidr $MY_IP/32 \
  --region us-east-1
```

---

## 📈 STEP 12: Monitor Performance

### Daily Checks

```bash
# 1. Check bot is running
sudo systemctl status trading-bot

# 2. Check resource usage
htop

# 3. View recent logs
tail -50 logs/trading_bot.log

# 4. Check signals generated today
sqlite3 data/strategies.db "SELECT COUNT(*) FROM signals WHERE date(timestamp) = date('now');"
```

### Weekly Checks

```bash
# 1. Review error logs
grep -i error logs/trading_bot.log | tail -50

# 2. Check disk space
df -h

# 3. Verify backups
aws s3 ls s3://trading-bot-backups-980104576869/database/ | tail -10

# 4. Review strategy performance
sqlite3 data/strategies.db "SELECT name, confidence_score, win_rate FROM backtest_results ORDER BY confidence_score DESC LIMIT 20;"
```

---

## 🎯 Success Criteria

Your deployment is successful when:

- ✅ Bot is running: `sudo systemctl status trading-bot` shows "active (running)"
- ✅ Telegram commands work: `/start`, `/signal`, `/stats` all respond
- ✅ Auto-signals enabled: Check config has `ENABLE_AUTO_SIGNALS=true`
- ✅ No crashes for 24+ hours: `sudo systemctl status trading-bot` shows long uptime
- ✅ Logs show activity: `tail logs/trading_bot.log` shows recent entries
- ✅ Resource usage normal: CPU < 50%, Memory < 1GB used

---

## 💰 Cost Tracking

### Monthly Cost Estimate (t2.micro Free Tier)

| Item | Cost |
|------|------|
| t2.micro EC2 (750 hrs/mo free) | $0 (first year) |
| EBS 8GB (30GB free) | $0 |
| Data transfer (15GB free) | $0 |
| S3 backups (~1GB) | ~$0.03 |
| **Total (Year 1)** | **~$0.03/month** |
| **Total (After Year 1)** | **~$8-10/month** |

### After Free Tier Expires (use t3.micro)

| Item | Cost |
|------|------|
| t3.micro EC2 | ~$7.50 |
| EBS 10GB | ~$0.80 |
| Data transfer | ~$0.50 |
| S3 backups | ~$0.03 |
| **Total** | **~$9/month** |

---

## 📞 Support

- **Documentation**: All .md files in repository
- **Logs**: `~/trading-tool/logs/trading_bot.log`
- **System Logs**: `sudo journalctl -u trading-bot -f`
- **GitHub Issues**: https://github.com/imnuman/trading-tool/issues

---

## 🎉 Congratulations!

Your trading bot is now running 24/7 on AWS!

**What happens next:**
- Bot checks for signals automatically every hour (if AUTO_SIGNALS enabled)
- You'll receive Telegram notifications when high-confidence signals appear
- All signals are filtered by: regime detection, trend alignment, risk management
- Bot restarts automatically if it crashes
- Backups run daily at 2 AM (if configured)

**Monitoring:**
- Check Telegram for notifications
- Review logs daily: `tail logs/trading_bot.log`
- Monitor costs in AWS Billing Dashboard

**Happy Trading! 📈💰**
