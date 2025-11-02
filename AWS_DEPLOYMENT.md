# AWS Deployment Guide - Trading Tool

**Complete guide for deploying your 24/7 AI-powered trading bot on AWS**

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Deployment Options](#deployment-options)
4. [Option 1: AWS EC2 (Recommended)](#option-1-aws-ec2-recommended)
5. [Option 2: AWS ECS with Fargate](#option-2-aws-ecs-with-fargate)
6. [Option 3: AWS Lambda (Not Recommended)](#option-3-aws-lambda-not-recommended)
7. [Configuration](#configuration)
8. [Monitoring & Logging](#monitoring--logging)
9. [Cost Estimation](#cost-estimation)
10. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                          AWS Cloud                               │
│                                                                   │
│  ┌─────────────────┐     ┌──────────────┐     ┌──────────────┐ │
│  │   EC2 Instance  │────▶│  CloudWatch  │────▶│   SNS/Email  │ │
│  │                 │     │   Logs &     │     │    Alerts    │ │
│  │  Trading Bot    │     │   Metrics    │     └──────────────┘ │
│  │  (Docker/systemd)│     └──────────────┘                      │
│  └────────┬────────┘                                            │
│           │                                                      │
│           ▼                                                      │
│  ┌──────────────────┐                                          │
│  │   EBS Volume     │                                          │
│  │  (Database &     │                                          │
│  │   Logs Storage)  │                                          │
│  └──────────────────┘                                          │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
         │
         ▼
  ┌─────────────┐
  │  Telegram   │
  │     API     │
  └─────────────┘
```

---

## Prerequisites

### 1. AWS Account
- Create an AWS account: https://aws.amazon.com/free
- Set up billing alerts
- Enable MFA for security

### 2. AWS CLI
```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure AWS CLI
aws configure
# Enter: AWS Access Key ID
# Enter: AWS Secret Access Key
# Enter: Default region (e.g., us-east-1)
# Enter: Default output format (json)
```

### 3. Telegram Bot Token
```bash
# Get your bot token from @BotFather on Telegram
# Get your user ID from @userinfobot
```

### 4. Local Testing Complete
```bash
# Ensure bot works locally before deploying
python3 scripts/pre_deploy.py  # Generate strategies
python3 main.py                 # Test bot
```

---

## Deployment Options

| Option | Best For | Cost/Month | Complexity | Uptime |
|--------|---------|-----------|------------|--------|
| **EC2 t3.small** | Production | ~$15-20 | Low | 99.9% |
| **ECS Fargate** | Auto-scaling | ~$20-30 | Medium | 99.95% |
| **Lambda** | Low-traffic | ~$5-10 | High | 99.95% |

---

## Option 1: AWS EC2 (Recommended)

### Step 1: Launch EC2 Instance

```bash
# Create key pair for SSH
aws ec2 create-key-pair \
  --key-name trading-bot-key \
  --query 'KeyMaterial' \
  --output text > trading-bot-key.pem

chmod 400 trading-bot-key.pem

# Create security group
aws ec2 create-security-group \
  --group-name trading-bot-sg \
  --description "Security group for trading bot"

# Allow SSH (from your IP only)
MY_IP=$(curl -s https://checkip.amazonaws.com)
aws ec2 authorize-security-group-ingress \
  --group-name trading-bot-sg \
  --protocol tcp \
  --port 22 \
  --cidr $MY_IP/32

# Allow outbound HTTPS for Telegram API
aws ec2 authorize-security-group-egress \
  --group-name trading-bot-sg \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0

# Launch EC2 instance (Ubuntu 22.04 LTS)
# Recommended: t3.small (2 vCPU, 2GB RAM)
aws ec2 run-instances \
  --image-id ami-0c7217cdde317cfec \
  --instance-type t3.small \
  --key-name trading-bot-key \
  --security-groups trading-bot-sg \
  --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":20,"VolumeType":"gp3"}}]' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=TradingBot}]'
```

### Step 2: Connect and Setup Instance

```bash
# Get instance public IP
INSTANCE_IP=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=TradingBot" \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)

# SSH into instance
ssh -i trading-bot-key.pem ubuntu@$INSTANCE_IP

# On EC2 instance - Install dependencies
sudo apt-get update
sudo apt-get install -y \
  python3.11 \
  python3.11-venv \
  python3-pip \
  git \
  htop

# Create project directory
mkdir -p ~/trading-tool
cd ~/trading-tool
```

### Step 3: Deploy Application

```bash
# On EC2 instance - Clone repository or upload files
# Option A: Using git
git clone https://github.com/yourusername/trading-tool.git .

# Option B: Upload from local machine
# On your local machine:
scp -i trading-bot-key.pem -r /home/user/trading-tool/* ubuntu@$INSTANCE_IP:~/trading-tool/

# Back on EC2 instance - Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create config file
nano config/secrets.env
# Paste your configuration (see Configuration section below)

# Create logs directory
mkdir -p logs data/cache
```

### Step 4: Run Pre-Deployment

```bash
# Generate strategies (takes 10-30 minutes)
python3 scripts/pre_deploy.py

# Verify database created
ls -lh data/strategies.db
```

### Step 5: Setup systemd Service

```bash
# Copy service file
sudo cp trading-bot.service /etc/systemd/system/

# Edit service file with correct paths
sudo nano /etc/systemd/system/trading-bot.service
# Update: User=ubuntu
# Update: WorkingDirectory=/home/ubuntu/trading-tool
# Update: ExecStart=/home/ubuntu/trading-tool/venv/bin/python3 /home/ubuntu/trading-tool/main.py

# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable trading-bot

# Start service
sudo systemctl start trading-bot

# Check status
sudo systemctl status trading-bot

# View logs in real-time
sudo journalctl -u trading-bot -f
```

### Step 6: Verify Bot is Running

```bash
# Check if bot is responding
# Send /start to your Telegram bot

# Check logs
tail -f logs/trading_bot.log

# Check resource usage
htop

# Check database
sqlite3 data/strategies.db "SELECT COUNT(*) FROM strategies;"
```

---

## Option 2: AWS ECS with Fargate

### Step 1: Create ECR Repository

```bash
# Create container registry
aws ecr create-repository --repository-name trading-bot

# Get registry URL
ECR_URL=$(aws ecr describe-repositories \
  --repository-names trading-bot \
  --query 'repositories[0].repositoryUri' \
  --output text)

# Login to ECR
aws ecr get-login-password | docker login \
  --username AWS \
  --password-stdin $ECR_URL
```

### Step 2: Build and Push Docker Image

```bash
# On your local machine
cd /home/user/trading-tool

# Build Docker image
docker build -t trading-bot:latest .

# Tag for ECR
docker tag trading-bot:latest $ECR_URL:latest

# Push to ECR
docker push $ECR_URL:latest
```

### Step 3: Create ECS Cluster

```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name trading-bot-cluster

# Create task execution role
aws iam create-role \
  --role-name ecsTaskExecutionRole \
  --assume-role-policy-document file://ecs-task-trust-policy.json

# Attach policies
aws iam attach-role-policy \
  --role-name ecsTaskExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
```

### Step 4: Create Task Definition

Create `task-definition.json`:
```json
{
  "family": "trading-bot",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::YOUR_ACCOUNT_ID:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "trading-bot",
      "image": "YOUR_ECR_URL:latest",
      "essential": true,
      "environment": [
        {"name": "TELEGRAM_BOT_TOKEN", "value": "YOUR_TOKEN"},
        {"name": "ENABLE_AUTO_SIGNALS", "value": "true"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/trading-bot",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

Register task:
```bash
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

### Step 5: Create Service

```bash
# Create service
aws ecs create-service \
  --cluster trading-bot-cluster \
  --service-name trading-bot-service \
  --task-definition trading-bot \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

---

## Option 3: AWS Lambda (Not Recommended)

**Why not recommended:**
- 15-minute timeout limit (conflicts with 24/7 polling)
- Cold start delays
- Complex state management
- Not suitable for long-running processes

**Alternative approach:**
- Use Lambda for scheduled signal checks (EventBridge trigger every hour)
- Store state in DynamoDB
- Use Step Functions for orchestration

---

## Configuration

### secrets.env for Production

```bash
# =============================================================================
# PRODUCTION CONFIGURATION
# =============================================================================

# Telegram
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_ALLOWED_USERS=123456789

# 24/7 Auto Signals
ENABLE_AUTO_SIGNALS=true
AUTO_SIGNAL_INTERVAL=3600
AUTO_SIGNAL_PAIRS=EUR/USD,GBP/USD,XAU/USD

# Trading
MIN_CONFIDENCE_THRESHOLD=80.0
MIN_AGREEMENT_THRESHOLD=0.80
DEFAULT_PAIRS=EUR/USD,GBP/USD,XAU/USD

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/trading_bot.log

# Paths
DATABASE_PATH=./data/strategies.db
CACHE_DIR=./data/cache
```

---

## Monitoring & Logging

### CloudWatch Setup

```bash
# Install CloudWatch agent on EC2
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb

# Configure agent
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-config-wizard

# Monitor logs
aws logs tail /aws/ec2/trading-bot --follow
```

### Key Metrics to Monitor

1. **Bot Uptime**: CloudWatch custom metric
2. **Signal Generation Rate**: Signals per hour
3. **Memory Usage**: Should stay < 1.5GB
4. **CPU Usage**: Should stay < 50%
5. **Error Rate**: Errors per hour

### Set Up Alerts

```bash
# Create SNS topic for alerts
aws sns create-topic --name trading-bot-alerts

# Subscribe email
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:123456789:trading-bot-alerts \
  --protocol email \
  --notification-endpoint your-email@example.com

# Create CloudWatch alarm
aws cloudwatch put-metric-alarm \
  --alarm-name trading-bot-high-cpu \
  --alarm-description "Alert when CPU > 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions arn:aws:sns:us-east-1:123456789:trading-bot-alerts
```

---

## Cost Estimation

### EC2 Deployment (Recommended)

| Resource | Specification | Monthly Cost |
|----------|--------------|--------------|
| EC2 t3.small | 2 vCPU, 2GB RAM | $15.18 |
| EBS gp3 | 20GB storage | $1.60 |
| Data Transfer | ~10GB/month | $0.90 |
| CloudWatch | Basic monitoring | Free |
| **Total** | | **~$18/month** |

### ECS Fargate

| Resource | Specification | Monthly Cost |
|----------|--------------|--------------|
| Fargate task | 1 vCPU, 2GB RAM | $29.55 |
| Data Transfer | ~10GB/month | $0.90 |
| CloudWatch | Logs | $5.00 |
| **Total** | | **~$35/month** |

### Cost Optimization Tips

1. **Use Reserved Instances**: Save 30-50% for 1-year commitment
2. **Stop during non-trading hours**: Save 50% if not needed 24/7
3. **Use Spot Instances**: Save up to 90% (but risk interruption)
4. **Compress logs**: Reduce CloudWatch costs
5. **Use S3 for backups**: Cheaper than EBS snapshots

---

## Backup Strategy

### Automated Daily Backups

Create backup script:
```bash
#!/bin/bash
# /home/ubuntu/trading-tool/scripts/backup.sh

DATE=$(date +%Y%m%d)
S3_BUCKET="your-backup-bucket"

# Backup database
aws s3 cp /home/ubuntu/trading-tool/data/strategies.db \
  s3://$S3_BUCKET/backups/strategies-$DATE.db

# Backup logs
tar -czf /tmp/logs-$DATE.tar.gz /home/ubuntu/trading-tool/logs
aws s3 cp /tmp/logs-$DATE.tar.gz \
  s3://$S3_BUCKET/backups/logs-$DATE.tar.gz
rm /tmp/logs-$DATE.tar.gz

# Keep only 30 days of backups
aws s3 ls s3://$S3_BUCKET/backups/ | \
  sort | head -n -30 | awk '{print $4}' | \
  xargs -I {} aws s3 rm s3://$S3_BUCKET/backups/{}
```

Add to crontab:
```bash
crontab -e
# Add line:
0 2 * * * /home/ubuntu/trading-tool/scripts/backup.sh >> /home/ubuntu/trading-tool/logs/backup.log 2>&1
```

---

## Troubleshooting

### Bot Won't Start

```bash
# Check logs
sudo journalctl -u trading-bot -n 50

# Check if port is in use
sudo netstat -tlnp | grep python

# Check permissions
ls -la /home/ubuntu/trading-tool/data

# Test manually
cd /home/ubuntu/trading-tool
source venv/bin/activate
python3 main.py
```

### Bot Crashes Frequently

```bash
# Check memory usage
free -h

# Check disk space
df -h

# Check for OOM kills
sudo dmesg | grep -i kill

# Increase swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Not Receiving Signals

```bash
# Check bot is running
sudo systemctl status trading-bot

# Check Telegram connection
curl -s "https://api.telegram.org/bot<YOUR_TOKEN>/getMe"

# Check signal generation
tail -f logs/trading_bot.log | grep signal

# Test signal manually via Telegram
/signal
```

### Database Locked

```bash
# Check if database file exists
ls -lh data/strategies.db

# Check for write permissions
ls -la data/

# Kill any locked processes
sudo lsof data/strategies.db
sudo kill -9 <PID>
```

---

## Security Best Practices

1. **Use IAM roles**: Never hardcode AWS credentials
2. **Rotate bot token**: Change Telegram token every 90 days
3. **Enable MFA**: On AWS account
4. **Restrict SSH**: Only from your IP
5. **Use secrets manager**: For production credentials
6. **Enable CloudTrail**: Audit all API calls
7. **Regular updates**: Keep system and packages updated

```bash
# Auto-update security patches
sudo apt-get install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

## Next Steps

After deployment:

1. **Monitor for 24-48 hours**: Watch logs and metrics
2. **Test auto-signals**: Verify notifications arrive
3. **Set up alerts**: Email/SMS for critical errors
4. **Document**: Note any custom configuration
5. **Backup**: Verify backups are working
6. **Optimize**: Adjust thresholds based on performance

---

## Support

- Issues: https://github.com/yourusername/trading-tool/issues
- Documentation: /home/user/trading-tool/TESTING.md
- Status: /home/user/trading-tool/STATUS.md

---

**Happy Trading! 🚀**
