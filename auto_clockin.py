#!/usr/bin/env python3
"""
Oyl Corp Auto Clockin

A utility script to automatically send transactions to the Oyl Corp Clock-in game 
at precisely timed Bitcoin block heights.

This script monitors the blockchain and sends your transaction at exactly the right time
to be included in a target block.
"""

import os
import time
import subprocess
import requests
import sys
import json
import datetime
# Automatically load environment variables from .env for 24/7/hosted use
from dotenv import load_dotenv
load_dotenv()

# Debug: Print loaded environment variables for troubleshooting
print(f"DEBUG: MNEMONIC={os.environ.get('MNEMONIC')}")
print(f"DEBUG: SANDSHREW_PROJECT_ID={os.environ.get('SANDSHREW_PROJECT_ID')}")
if not os.environ.get('MNEMONIC'):
    print("WARNING: MNEMONIC not loaded from .env!")
if not os.environ.get('SANDSHREW_PROJECT_ID'):
    print("WARNING: SANDSHREW_PROJECT_ID not loaded from .env!")

# Configuration - CUSTOMIZE THESE VALUES
BLOCK_API_URL = "https://blockstream.info/api/blocks/tip/height"
POLL_INTERVAL = 20  # seconds - conservative polling to respect API rate limits (3 requests/minute)

# REQUIRED: The Oyl command to execute for the Clock-in game
# Format: "oyl alkane execute -data CONTRACT_ID,OPCODE -p bitcoin -feeRate FEE_RATE"
# Example for Clock-in game: "oyl alkane execute -data 2,21568,103 -p bitcoin -feeRate 7"
TX_COMMAND = "oyl alkane execute -data 2,21568,103 -p bitcoin -feeRate 10"  # Increased fee rate for reliability

# Number of retry attempts for transaction submission
MAX_ATTEMPTS = 3

# Target block configuration - CUSTOMIZE THESE VALUES
TARGET_BLOCK = 904181  # Next valid clock-in block (verified via Ordiscan)
SEND_ON_BLOCK = 904180  # Send one block before target
DEPLOY_BLOCK = 897413  # Oyl Corp contract deploy block (see https://ordiscan.com/alkane/ClockInSystem/2:21568)

FEE_API_URL = "https://mempool.space/api/v1/fees/recommended"

def get_current_block_height():
    """Fetch the current Bitcoin block height from Blockstream API"""
    try:
        response = requests.get(BLOCK_API_URL, timeout=10)
        response.raise_for_status()
        return int(response.text.strip())
    except Exception as e:
        print(f"Error fetching block height: {e}")
        return None

def format_eta(minutes):
    if minutes < 60:
        return f"{minutes} minutes"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m"

def get_dynamic_fee():
    """Fetch the recommended fee from mempool.space and add a buffer."""
    try:
        response = requests.get(FEE_API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        # Use the higher of fastestFee (next block) and halfHourFee (upcoming block)
        base_fee = max(data.get("fastestFee", 10), data.get("halfHourFee", 10))
        fee = base_fee + 3  # Add 3 sats/vByte buffer
        print(f"Dynamic fee selected: {fee} (base: {base_fee}, +3 buffer)")
        return fee
    except Exception as e:
        print(f"Error fetching dynamic fee: {e}")
        return 13  # Fallback to a safe default

def send_transaction():
    """Send the transaction using Oyl CLI with retry logic. Returns (success, txId or None)"""
    fee_rate = get_dynamic_fee()
    # Build the TX_COMMAND dynamically with the new fee
    dynamic_tx_command = f"oyl alkane execute -data 2,21568,103 -p bitcoin -feeRate {fee_rate}"
    for attempt in range(MAX_ATTEMPTS):
        try:
            print(f"Sending transaction (attempt {attempt+1}/{MAX_ATTEMPTS})...")
            result = subprocess.run(
                dynamic_tx_command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                check=True
            )
            print(f"Transaction result: {result.stdout}")
            if "txId" in result.stdout:
                # Try to extract txId from output
                import re
                match = re.search(r"txId['\"]?\s*[:=]\s*['\"]?([a-fA-F0-9]{64})", result.stdout)
                txid = match.group(1) if match else None
                print("Transaction sent successfully!")
                return True, txid
        except subprocess.CalledProcessError as e:
            print(f"Error sending transaction: {e}")
            print(f"Command output: {e.stdout}\n{e.stderr}")
            if attempt < MAX_ATTEMPTS - 1:
                print(f"Retrying in 5 seconds...")
                time.sleep(5)
    print(f"Failed to send transaction after {MAX_ATTEMPTS} attempts")
    return False, None

def validate_environment():
    """Validate that required environment variables are set"""
    if not os.environ.get("SANDSHREW_PROJECT_ID"):
        print("ERROR: SANDSHREW_PROJECT_ID environment variable is not set.")
        print("Please set this in your .env file or export it directly:")
        print("export SANDSHREW_PROJECT_ID=\"your_project_id_here\"")
        return False
        
    if not os.environ.get("MNEMONIC") and not os.path.exists(os.path.expanduser("~/.oyl/config.json")):
        print("WARNING: MNEMONIC environment variable is not set and no Oyl config found.")
        print("You may need to set your mnemonic or configure Oyl:")
        print("export MNEMONIC=\"your twelve word mnemonic phrase goes here\"")
        print("This might still work if you've previously configured Oyl with 'oyl account setMnemonic'")
    
    return True

def calculate_next_clockin_block(current_height, start_block=DEPLOY_BLOCK):
    """Calculate the next valid clock-in block based on the 144-block cycle and contract deploy block"""
    # Clock-in blocks occur every 144 blocks from the deploy block
    blocks_since_start = current_height - start_block
    blocks_until_next = 144 - (blocks_since_start % 144)
    if blocks_until_next == 144:
        # Current block is a valid clock-in block
        return current_height
    else:
        # Next valid block is in the future
        return current_height + blocks_until_next

def send_discord_notification(message):
    """Send a message to Discord via webhook if configured."""
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("No DISCORD_WEBHOOK_URL set, skipping Discord notification.")
        return
    try:
        data = {"content": message}
        response = requests.post(webhook_url, data=json.dumps(data), headers={"Content-Type": "application/json"})
        if response.status_code == 204 or response.status_code == 200:
            print("Discord notification sent.")
        else:
            print(f"Failed to send Discord notification: {response.status_code} {response.text}")
    except Exception as e:
        print(f"Exception sending Discord notification: {e}")

def main():
    print("Starting Oyl Corp Auto Clockin...")
    
    # Validate environment
    if not validate_environment():
        sys.exit(1)
    
    global TARGET_BLOCK, SEND_ON_BLOCK
    # Get initial block height
    current_height = get_current_block_height()
    if current_height is None:
        print("Failed to get initial block height. Exiting.")
        sys.exit(1)
    # Auto-advance to the next valid future clock-in if missed
    while SEND_ON_BLOCK <= current_height:
        print(f"Missed send block {SEND_ON_BLOCK} (current: {current_height}). Advancing to next valid clock-in block.")
        TARGET_BLOCK += 144
        SEND_ON_BLOCK = TARGET_BLOCK - 1
    while True:
        # Validate configuration
        if TARGET_BLOCK == 0 or SEND_ON_BLOCK == 0:
            print("ERROR: You must set TARGET_BLOCK and SEND_ON_BLOCK values in the script")
            print("Current values are set to 0, which is invalid")
            sys.exit(1)
        
        # Calculate the next valid clock-in block (for reference)
        next_clockin_block = calculate_next_clockin_block(current_height)
        
        print(f"Current block height: {current_height}")
        print(f"Next valid clock-in block: {next_clockin_block}")
        print(f"Target confirmation block: {TARGET_BLOCK}")
        print(f"Will send transaction on block: {SEND_ON_BLOCK}")
        
        # Check if target block is valid for clock-in
        blocks_since_deploy = TARGET_BLOCK - DEPLOY_BLOCK  # Use deploy block for Oyl Corp
        if blocks_since_deploy % 144 != 0:
            print(f"WARNING: Block {TARGET_BLOCK} does not appear to be a valid clock-in block!")
            print(f"Valid clock-in blocks occur every 144 blocks from the deploy block ({DEPLOY_BLOCK}).")
            print(f"You should set TARGET_BLOCK to a valid clock-in block as shown on Ordiscan.")
            print(f"SEND_ON_BLOCK should be one block before TARGET_BLOCK (TARGET_BLOCK - 1).\n")
            print(f"Current config: TARGET_BLOCK={TARGET_BLOCK}, SEND_ON_BLOCK={SEND_ON_BLOCK}")
            print(f"If you are sure {TARGET_BLOCK} is correct (per Ordiscan), you can safely continue.")
            response = input("Continue anyway? (y/n): ")
            if response.lower() != 'y':
                sys.exit(0)
        
        blocks_remaining = SEND_ON_BLOCK - current_height
        eta_minutes = blocks_remaining * 10
        eta_str = format_eta(eta_minutes)
        # Notify before clock-in attempt
        send_discord_notification(
            f"⏰ Upcoming Oyl Corp clock-in #3!\nWill send transaction on block: {SEND_ON_BLOCK}\nTarget clock-in block: {TARGET_BLOCK}\nEstimated time until send: {eta_str} (assuming 10 min/block)\nCurrent block: {current_height}"
        )
        print(f"Waiting for block {SEND_ON_BLOCK}... ({blocks_remaining} blocks remaining)")
        print(f"This will take approximately {blocks_remaining * 10} minutes at normal block times")
        # Monitor until target block
        while True:
            time.sleep(POLL_INTERVAL)
            current_height = get_current_block_height()
            if current_height is None:
                print("Failed to get current block height. Retrying...")
                continue
            blocks_remaining = SEND_ON_BLOCK - current_height
            print(f"Current block: {current_height}, Target send block: {SEND_ON_BLOCK}, Blocks remaining: {blocks_remaining}")
            # Check if it's time to send the transaction
            if current_height == SEND_ON_BLOCK:
                print(f"Target block {SEND_ON_BLOCK} reached! Sending transaction now for confirmation in block {TARGET_BLOCK}...")
                send_discord_notification(
                    f"🚀 Sending Oyl Corp clock-in #3 transaction!\nSend block: {SEND_ON_BLOCK}\nTarget block: {TARGET_BLOCK}\nTime: {datetime.datetime.utcnow().isoformat()} UTC"
                )
                success, txid = send_transaction()
                if success:
                    send_discord_notification(
                        f"✅ Clock-in #3 SUCCESS!\nBlock: {TARGET_BLOCK}\nSent at block: {SEND_ON_BLOCK}\ntxId: {txid if txid else 'N/A'}"
                    )
                else:
                    send_discord_notification(
                        f"❌ Clock-in #3 FAILED!\nBlock: {TARGET_BLOCK}\nAttempted at block: {SEND_ON_BLOCK}"
                    )
                print("Transaction sent. Preparing for next clock-in.")
                # Auto-advance to next valid block
                TARGET_BLOCK += 144
                SEND_ON_BLOCK = TARGET_BLOCK - 1
                print(f"Next clock-in scheduled for block {TARGET_BLOCK} (send on {SEND_ON_BLOCK})")
                break  # Exit inner monitor loop, restart for next block
            # Check if we've missed the target block
            if current_height > SEND_ON_BLOCK:
                print(f"Target send block {SEND_ON_BLOCK} has passed (current: {current_height}). Exiting without sending transaction.")
                send_discord_notification(
                    f"❌ Missed clock-in #3!\nBlock: {TARGET_BLOCK}\nSend block {SEND_ON_BLOCK} already passed."
                )
                sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test-discord":
        send_discord_notification("🚀 Test notification: Oyl Corp Auto Clockin #3 Discord integration is working!")
        print("Test Discord notification sent. Exiting.")
        sys.exit(0)
    main()
