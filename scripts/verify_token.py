#!/usr/bin/env python3
"""Quick script to verify Telegram bot token format"""

import os
import re
from dotenv import load_dotenv

load_dotenv('config/secrets.env')

token = os.getenv('TELEGRAM_BOT_TOKEN', '')

if not token:
    print("❌ TELEGRAM_BOT_TOKEN not found in config/secrets.env")
    exit(1)

# Telegram token format: numbers:alphanumeric (typically 10 digits:35 chars)
token_pattern = r'^\d+:[A-Za-z0-9_-]{30,}$'

if re.match(token_pattern, token):
    print("✅ Token format looks correct!")
    print(f"   Token starts with: {token[:15]}...")
    print(f"   Token length: {len(token)} characters")
    print("\n💡 To fully verify, try starting the bot:")
    print("   python3 main.py")
else:
    print("❌ Token format appears incorrect!")
    print("   Expected format: numbers:alphanumeric_string")
    print(f"   Your token: {token[:20]}...")
    print(f"   Length: {len(token)} characters")
    print("\n💡 Make sure:")
    print("   - No quotes around the token")
    print("   - No spaces around the = sign")
    print("   - Complete token copied from @BotFather")

