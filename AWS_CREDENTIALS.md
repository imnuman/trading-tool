# AWS Credentials Storage Guide

Best practices for storing AWS credentials securely.

---

## 🔐 **RECOMMENDED: AWS IAM Roles (Best Practice)**

**For EC2/Lightsail instances, use IAM roles instead of storing credentials.**

### Why IAM Roles?
- ✅ More secure (no credentials in files)
- ✅ Automatic credential rotation
- ✅ No risk of exposing credentials
- ✅ Easier to manage permissions

### Setup IAM Role for EC2:

1. **Create IAM Role:**
   - Go to: https://console.aws.amazon.com/iam/
   - Click "Roles" → "Create role"
   - Select "AWS service" → "EC2"
   - Click "Next"

2. **Attach Policies:**
   - For basic deployment: No special policies needed (if not using AWS services)
   - If using S3/CloudWatch: Attach relevant policies
   - Click "Next"

3. **Name Role:**
   - Name: `trading-tool-ec2-role`
   - Click "Create role"

4. **Attach to EC2 Instance:**
   - Go to EC2 Console → Instances
   - Select your instance
   - Actions → Security → Modify IAM role
   - Select the role you created
   - Click "Update IAM role"

**Result:** EC2 instance automatically has credentials - no need to store them!

---

## 📁 **OPTION 1: Standard AWS Credentials File (Recommended for Local)**

### Location:
```
~/.aws/credentials
```

### Format:
```ini
[default]
aws_access_key_id = AKIAIOSFODNN7EXAMPLE
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
region = us-east-1
```

### Setup:
```bash
# Create directory if it doesn't exist
mkdir -p ~/.aws

# Edit credentials file
nano ~/.aws/credentials

# Add your credentials (see format above)
```

### Permissions:
```bash
# Secure the file (owner read/write only)
chmod 600 ~/.aws/credentials
```

### Configuration File (Optional):
```
~/.aws/config
```

```ini
[default]
region = us-east-1
output = json
```

---

## 📁 **OPTION 2: Environment Variables (For Development)**

### On Local Machine:

**Linux/Mac:**
```bash
# Add to ~/.bashrc or ~/.zshrc
export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
export AWS_DEFAULT_REGION=us-east-1

# Reload shell
source ~/.bashrc
```

**Or create `.env` file (if using docker-compose):**
```bash
AWS_ACCESS_KEY_ID=your_key_here
AWS_SECRET_ACCESS_KEY=your_secret_here
AWS_DEFAULT_REGION=us-east-1
```

---

## 📁 **OPTION 3: config/secrets.env (NOT Recommended for AWS)**

**⚠️ Only use this if:**
- You're not using IAM roles
- You need AWS CLI access on the EC2 instance
- You're testing locally

### Add to `config/secrets.env`:

```bash
# AWS Credentials (Optional - use IAM roles instead!)
# Only add if you need AWS CLI access on EC2 instance
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_DEFAULT_REGION=us-east-1
```

**⚠️ Security Notes:**
- ✅ Already in `.gitignore` (won't be committed)
- ✅ But still accessible on the server
- ⚠️ Less secure than IAM roles

---

## 🎯 **RECOMMENDED SETUP BY SCENARIO**

### Scenario 1: EC2/Lightsail Deployment
**✅ Use IAM Roles** (no credentials needed!)

### Scenario 2: Local Development
**✅ Use `~/.aws/credentials`**

### Scenario 3: Docker/Container
**✅ Use environment variables or IAM roles**

### Scenario 4: Elastic Beanstalk
**✅ Use EB environment variables** (set via `eb setenv`)

---

## 🔍 **How to Get AWS Credentials**

### If You Need Access Keys:

1. **Go to IAM Console:**
   - https://console.aws.amazon.com/iam/
   - Click "Users" → Your username

2. **Create Access Key:**
   - Click "Security credentials" tab
   - Scroll to "Access keys"
   - Click "Create access key"
   - Choose use case (CLI access, etc.)
   - Click "Create access key"

3. **Save Credentials:**
   - **⚠️ Download immediately** - shown only once!
   - Access Key ID: `AKIA...`
   - Secret Access Key: `wJalr...`

---

## ✅ **VERIFICATION**

### Test AWS CLI Access:

```bash
# Install AWS CLI (if not installed)
pip install awscli

# Configure (if using credentials file)
aws configure

# Test access
aws sts get-caller-identity

# Should return:
# {
#     "UserId": "...",
#     "Account": "...",
#     "Arn": "arn:aws:iam::..."
# }
```

### Test from Python:

```bash
python3 -c "
import boto3
try:
    sts = boto3.client('sts')
    identity = sts.get_caller_identity()
    print('✅ AWS credentials working!')
    print(f'Account: {identity[\"Account\"]}')
    print(f'User/Role: {identity[\"Arn\"]}')
except Exception as e:
    print(f'❌ Error: {e}')
"
```

---

## 🔒 **SECURITY BEST PRACTICES**

### ✅ DO:
- Use IAM roles for EC2/Lightsail (preferred)
- Store credentials in `~/.aws/credentials` (local)
- Set file permissions: `chmod 600 ~/.aws/credentials`
- Use minimal required permissions
- Rotate credentials periodically

### ❌ DON'T:
- Commit credentials to git (already in `.gitignore`)
- Share credentials publicly
- Use root account credentials
- Store in code files
- Use same credentials across multiple projects

---

## 📝 **For Trading Tool Deployment**

### Recommended Approach:

**For EC2/Lightsail:**
1. ✅ Create IAM role (no special permissions needed for basic bot)
2. ✅ Attach role to instance
3. ✅ No credentials needed!

**For Local Testing (if needed):**
1. ✅ Install AWS CLI: `pip install awscli`
2. ✅ Configure: `aws configure`
3. ✅ Credentials stored in `~/.aws/credentials`

**For Elastic Beanstalk:**
1. ✅ Use `eb setenv` to set environment variables
2. ✅ No file storage needed

---

## 🎯 **QUICK REFERENCE**

| Location | Use Case | Security |
|----------|----------|----------|
| IAM Role | EC2/Lightsail | ⭐⭐⭐⭐⭐ Best |
| `~/.aws/credentials` | Local development | ⭐⭐⭐⭐ Good |
| Environment variables | Docker/Containers | ⭐⭐⭐⭐ Good |
| `config/secrets.env` | Local testing only | ⭐⭐⭐ OK |

---

## ⚠️ **IMPORTANT NOTES**

1. **For this trading bot:** You likely **don't need AWS credentials** unless:
   - You're using AWS services (S3, CloudWatch, etc.)
   - You're running AWS CLI commands on the instance
   - You're doing local development with AWS tools

2. **EC2/Lightsail deployment:** Use IAM roles - no credentials needed!

3. **Local testing:** Use `~/.aws/credentials` if you need AWS CLI access.

---

**Bottom Line:** For EC2/Lightsail deployment, **use IAM roles** and skip storing credentials entirely! 🎯

