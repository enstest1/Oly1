#!/usr/bin/env python3
"""
Oyl Corp Auto Clockin
"""

import os
import time
import subprocess
import requests
import sys
import json
import datetime
from dotenv import load_dotenv
load_dotenv()

print(f"DEBUG: MNEMONIC={os.environ.get('MNEMONIC')}")
print(f"DEBUG: SANDSHREW_PROJECT_ID={os.environ.get('SANDSHREW_PROJECT_ID')}")
if not os.environ.get('MNEMONIC'):
    print("WARNING: MNEMONIC not loaded from .env!")
if not os.environ.get('SANDSHREW_PROJECT_ID'):
    print("WARNING: SANDSHREW_PROJECT_ID not loaded from .env!")

BLOCK_API_URL = "https://blockstream.info/api/blocks/tip/height"
POLL_INTERVAL = 20
TX_COMMAND_TEMPLATE = "oyl alkane execute -data 2,21568,103 -p bitcoin -feeRate {}"
MAX_ATTEMPTS = 3
TARGET_BLOCK = 906485  # Next clock-in block
SEND_ON_BLOCK = TARGET_BLOCK - 1
DEPLOY_BLOCK = 897413
FEE_API_URL = "https://mempool.space/api/v1/fees/recommended"

def get_current_block_height():
    try:
        response = requests.get(BLOCK_API_URL, timeout=10)
        response.raise_for_status()
        return int(response.text.strip())
    except Exception as e:
        print(f"Error fetching block height: {e}")
        return None

def format_eta(minutes):
    return f"{minutes} minutes" if minutes < 60 else f"{minutes // 60}h {minutes % 60}m"

def get_dynamic_fee():
    try:
        response = requests.get(FEE_API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        base_fee = max(data.get("fastestFee", 10), data.get("halfHourFee", 10))
        fee = base_fee + 3
        print(f"Dynamic fee selected: {fee} (base: {base_fee} + buffer)")
        return fee
    except Exception as e:
        print(f"Error fetching fee: {e}")
        return 13

def send_transaction():
    fee_rate = get_dynamic_fee()
    tx_cmd = TX_COMMAND_TEMPLATE.format(fee_rate)
    for attempt in range(MAX_ATTEMPTS):
        try:
            print(f"Sending transaction (attempt {attempt+1}/{MAX_ATTEMPTS})...")
            result = subprocess.run(tx_cmd, shell=True, capture_output=True, text=True, check=True)
            print(f"Transaction result: {result.stdout}")
            if "txId" in result.stdout:
                import re
                match = re.search(r"txId['\"]?\s*[:=]\s*['\"]?([a-fA-F0-9]{64})", result.stdout)
                txid = match.group(1) if match else None
                print("Transaction sent successfully!")
                return True, txid
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}\n{e.stdout}\n{e.stderr}")
            if attempt < MAX_ATTEMPTS - 1:
                print("Retrying in 5 seconds...")
                time.sleep(5)
    print("Transaction failed after retries.")
    return False, None

def validate_environment():
    if not os.environ.get("SANDSHREW_PROJECT_ID"):
        print("ERROR: SANDSHREW_PROJECT_ID not set.")
        return False
    if not os.environ.get("MNEMONIC") and not os.path.exists(os.path.expanduser("~/.oyl/config.json")):
        print("WARNING: MNEMONIC not set or config not found.")
    return True

def calculate_next_clockin_block(current, start=DEPLOY_BLOCK):
    blocks_since = current - start
    blocks_until = 144 - (blocks_since % 144)
    return current if blocks_until == 144 else current + blocks_until

def send_discord_notification(message):
    webhook = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook:
        print("No webhook set.")
        return
    try:
        data = {"content": message}
        r = requests.post(webhook, data=json.dumps(data), headers={"Content-Type": "application/json"})
        if r.status_code in (200, 204):
            print("Discord notified.")
        else:
            print(f"Discord failed: {r.status_code} {r.text}")
    except Exception as e:
        print(f"Discord error: {e}")

def main():
    print("Starting Oyl Corp Auto Clockin...")
    if not validate_environment():
        sys.exit(1)

    global TARGET_BLOCK, SEND_ON_BLOCK
    current_height = get_current_block_height()
    if current_height is None:
        print("Failed to fetch block height.")
        sys.exit(1)

    while SEND_ON_BLOCK <= current_height:
        print(f"Missed {SEND_ON_BLOCK}. Advancing...")
        TARGET_BLOCK += 144
        SEND_ON_BLOCK = TARGET_BLOCK - 1

    while True:
        if TARGET_BLOCK == 0 or SEND_ON_BLOCK == 0:
            print("Invalid target/send blocks.")
            sys.exit(1)

        next_block = calculate_next_clockin_block(current_height)
        print(f"Current: {current_height} | Target: {TARGET_BLOCK} | Send on: {SEND_ON_BLOCK}")
        blocks_left = SEND_ON_BLOCK - current_height
        eta = format_eta(blocks_left * 10)

        send_discord_notification(
            f"⏰ Upcoming Oyl Corp clock-in!\nSend: {SEND_ON_BLOCK}\nTarget: {TARGET_BLOCK}\nETA: {eta}\nCurrent: {current_height}"
        )

        while True:
            time.sleep(POLL_INTERVAL)
            current_height = get_current_block_height()
            if current_height is None:
                continue

            print(f"Current block: {current_height} | Waiting for: {SEND_ON_BLOCK}")
            if current_height == SEND_ON_BLOCK:
                print("Target send block reached. Sending...")
                send_discord_notification(
                    f"🚀 Sending clock-in TX at {SEND_ON_BLOCK} for block {TARGET_BLOCK}!"
                )
                success, txid = send_transaction()
                if success:
                    send_discord_notification(
                        f"✅ SUCCESS!\nBlock: {TARGET_BLOCK}\nSent at: {SEND_ON_BLOCK}\ntxId: {txid or 'N/A'}"
                    )
                else:
                    send_discord_notification(
                        f"❌ FAILED!\nBlock: {TARGET_BLOCK}\nAttempted at: {SEND_ON_BLOCK}"
                    )
                TARGET_BLOCK += 144
                SEND_ON_BLOCK = TARGET_BLOCK - 1
                break
            if current_height > SEND_ON_BLOCK:
                print("Missed send window. Exiting.")
                send_discord_notification(
                    f"❌ MISSED CLOCK-IN!\nTarget: {TARGET_BLOCK}\nSend block passed: {SEND_ON_BLOCK}"
                )
                sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test-discord":
        send_discord_notification("🚀 Discord test message successful!")
        sys.exit(0)
    main()
