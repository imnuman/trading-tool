# OANDA API Setup Guide

Complete instructions for getting OANDA API access for real-time forex data.

---

## Step 1: Create OANDA Account

### Option A: Demo Account (Free - Recommended to Start)

1. **Visit OANDA Registration:**
   - Go to: https://www.oanda.com/us-en/trade/open-an-account/
   - Or direct: https://fxtrade.oanda.com/your_account/fxtrade/register/gate?utm_source=oandaapi&utm_medium=link&utm_campaign=devportaldocs_register

2. **Choose Account Type:**
   - Select **"Practice Account"** (Demo Account)
   - This gives you FREE API access with virtual money
   - Perfect for testing and development

3. **Fill Registration Form:**
   - Email address
   - Password (min 8 characters, 1 number, 1 letter)
   - Personal information (name, phone, address)
   - Country of residence
   - Accept terms and conditions

4. **Verify Email:**
   - Check your email inbox
   - Click verification link
   - Account will be activated

5. **Complete Profile:**
   - Answer trading experience questions
   - These are required but don't affect API access

**✅ Demo Account Benefits:**
- Free API access
- Live forex prices (real market data)
- Virtual money for testing
- No deposit required
- Same API as live account

### Option B: Live Account (If You Want to Trade Real Money)

1. **Follow same steps as Option A**
2. **Choose "Live Account" instead of "Practice Account"**
3. **Complete verification:**
   - Upload ID document
   - Proof of address
   - May take 1-3 business days

4. **Fund account:**
   - Minimum deposit: $0 (no minimum!)
   - But you need funds to actually trade
   - API works with any funded amount

**⚠️ Note:** For this trading bot, **Demo Account is recommended** unless you plan to auto-execute trades.

---

## Step 2: Get Your API Token

### 2.1. Log into OANDA Platform

1. Go to: https://fxtrade.oanda.com/
2. Log in with your account credentials
3. You'll see the trading platform dashboard

### 2.2. Navigate to API Settings

**Method 1: From Trading Platform**
1. Click on your **account name** (top right)
2. Select **"Manage API Access"** or **"API"**
3. If not visible, look for **"Settings"** → **"API"**

**Method 2: Direct Link**
- Go to: https://fxtrade.oanda.com/your_account/your_account/your_account/personal-access-tokens

### 2.3. Generate API Token

1. Click **"Generate New Token"** or **"Create API Token"**
2. **Token Name:** Give it a descriptive name
   - Example: "Trading Tool Bot" or "Python API Access"
3. **Permissions:** Select **"Read-only"** for data fetching
   - If you plan to execute trades later, you can create a separate token with "Trade" permissions
4. **Expiration:** 
   - For testing: 30-90 days
   - For production: Set longer or "Never expires"
5. Click **"Generate"** or **"Create"**

### 2.4. Save Your Token Immediately

**⚠️ CRITICAL:** The token is shown **ONCE**. Copy it immediately!

You'll see something like:
```
a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6
```

**Copy it now!** If you lose it, you'll need to generate a new one.

---

## Step 3: Get Your Account ID

1. **From Trading Platform:**
   - Log into OANDA platform
   - Your **Account ID** is displayed in the top-right corner
   - Format: Usually 7 digits (e.g., `101-004-1234567-001`)

2. **From API (if you have token):**
   ```bash
   curl https://api-fxpractice.oanda.com/v3/accounts \
     -H "Authorization: Bearer YOUR_API_TOKEN"
   ```
   This returns your account information including Account ID.

---

## Step 4: Configure Your Trading Tool

### 4.1. Add Credentials to secrets.env

Edit `config/secrets.env`:

```bash
# OANDA API Configuration
OANDA_API_KEY=your_api_token_here
OANDA_ACCOUNT_ID=your_account_id_here

# Use 'practice' for demo account, 'live' for live account
OANDA_ENVIRONMENT=practice
```

**Example:**
```bash
OANDA_API_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6
OANDA_ACCOUNT_ID=101-004-1234567-001
OANDA_ENVIRONMENT=practice
```

### 4.2. Test Your Connection

Run the test script:
```bash
python3 scripts/test_oanda_connection.py
```

Expected output:
```
✅ OANDA connection successful!
Account ID: 101-004-1234567-001
Account Balance: $10,000 (Demo)
```

---

## Step 5: API Endpoints

### Practice (Demo) Account:
- **REST API:** `https://api-fxpractice.oanda.com/v3/`
- **Streaming API:** `https://stream-fxpractice.oanda.com/v3/`

### Live Account:
- **REST API:** `https://api-fxtrade.oanda.com/v3/`
- **Streaming API:** `https://stream-fxtrade.oanda.com/v3/`

---

## API Rate Limits

### Free/Demo Accounts:
- **REST API:** 120 requests per second
- **Streaming:** Unlimited connections
- **Historical Data:** Unlimited
- **Real-time Prices:** Unlimited

**Note:** These limits are very generous - you won't hit them with normal usage.

---

## Supported Instruments (Forex Pairs)

OANDA supports all major forex pairs:
- EUR/USD, GBP/USD, USD/JPY, AUD/USD
- EUR/GBP, USD/CAD, USD/CHF, NZD/USD
- And 100+ more pairs

**Format:** `EUR_USD` (OANDA format uses underscore)

---

## Troubleshooting

### Error: "Invalid API Key"
- **Solution:** Make sure you copied the entire token (it's long!)
- Check for extra spaces or line breaks
- Regenerate token if needed

### Error: "Account ID not found"
- **Solution:** Make sure you're using correct Account ID
- Demo account ID format: `101-004-XXXXXXXX-001`
- Get it from OANDA platform (top-right corner)

### Error: "Invalid environment"
- **Solution:** Use `practice` for demo, `live` for live account
- Make sure it matches your account type

### Error: "Rate limit exceeded"
- **Solution:** You're making too many requests
- Add delays between requests (shouldn't happen with normal usage)

---

## Security Best Practices

1. **Never commit tokens to git:**
   - ✅ Already in `.gitignore` (secrets.env)
   - ❌ Never paste tokens in code or docs

2. **Use environment variables:**
   - Store tokens in `config/secrets.env` (not in code)

3. **Rotate tokens periodically:**
   - Generate new tokens every 90 days
   - Revoke old tokens

4. **Use read-only tokens for data fetching:**
   - Only create trade-enabled tokens if you plan to auto-execute

---

## Next Steps

After setting up OANDA:

1. ✅ Test connection (run test script)
2. ✅ Update `config/secrets.env` with credentials
3. ✅ Run `python3 scripts/pre_deploy.py` (will use OANDA for real-time data)
4. ✅ Start bot: `python3 main.py`
5. ✅ Bot will now use real-time OANDA prices!

---

## Helpful Links

- **OANDA Registration:** https://www.oanda.com/us-en/trade/open-an-account/
- **OANDA API Docs:** https://developer.oanda.com/rest-live-v20/introduction/
- **API Token Management:** https://fxtrade.oanda.com/your_account/your_account/your_account/personal-access-tokens
- **OANDA Support:** https://www.oanda.com/us-en/support/

---

**Ready to set up? Start with Step 1!** 🚀

