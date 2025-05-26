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

# Configuration - CUSTOMIZE THESE VALUES
BLOCK_API_URL = "https://blockstream.info/api/blocks/tip/height"
POLL_INTERVAL = 20  # seconds - conservative polling to respect API rate limits (3 requests/minute)

# REQUIRED: The Oyl command to execute for the Clock-in game
# Format: "oyl alkane execute -data CONTRACT_ID,OPCODE -p bitcoin -feeRate FEE_RATE"
# Example for Clock-in game: "oyl alkane execute -data 2,21568,103 -p bitcoin -feeRate 7"
TX_COMMAND = "oyl alkane execute -data 2,21568,103 -p bitcoin -feeRate 7"

# Number of retry attempts for transaction submission
MAX_ATTEMPTS = 3

# Target block configuration - CUSTOMIZE THESE VALUES
TARGET_BLOCK = 0  # The block where you want your transaction to be confirmed
SEND_ON_BLOCK = 0  # Send on this block to get confirmed in the target block (typically TARGET_BLOCK - 1)

def get_current_block_height():
    """Fetch the current Bitcoin block height from Blockstream API"""
    try:
        response = requests.get(BLOCK_API_URL, timeout=10)
        response.raise_for_status()
        return int(response.text.strip())
    except Exception as e:
        print(f"Error fetching block height: {e}")
        return None

def send_transaction():
    """Send the transaction using Oyl CLI with retry logic"""
    for attempt in range(MAX_ATTEMPTS):
        try:
            print(f"Sending transaction (attempt {attempt+1}/{MAX_ATTEMPTS})...")
            result = subprocess.run(
                TX_COMMAND, 
                shell=True, 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            print(f"Transaction result: {result.stdout}")
            if "txId" in result.stdout:
                print("Transaction sent successfully!")
                return True
                
        except subprocess.CalledProcessError as e:
            print(f"Error sending transaction: {e}")
            print(f"Command output: {e.stdout}\n{e.stderr}")
            if attempt < MAX_ATTEMPTS - 1:
                print(f"Retrying in 5 seconds...")
                time.sleep(5)
    
    print(f"Failed to send transaction after {MAX_ATTEMPTS} attempts")
    return False

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

def calculate_next_clockin_block(current_height, start_block=2):
    """Calculate the next valid clock-in block based on the 144-block cycle"""
    # Clock-in blocks occur every 144 blocks from the start block
    blocks_since_start = current_height - start_block
    blocks_until_next = 144 - (blocks_since_start % 144)
    
    if blocks_until_next == 144:
        # Current block is a valid clock-in block
        return current_height
    else:
        # Next valid block is in the future
        return current_height + blocks_until_next

def main():
    print("Starting Oyl Corp Auto Clockin...")
    
    # Validate environment
    if not validate_environment():
        sys.exit(1)
    
    # Validate configuration
    if TARGET_BLOCK == 0 or SEND_ON_BLOCK == 0:
        print("ERROR: You must set TARGET_BLOCK and SEND_ON_BLOCK values in the script")
        print("Current values are set to 0, which is invalid")
        sys.exit(1)
    
    # Get initial block height
    current_height = get_current_block_height()
    if current_height is None:
        print("Failed to get initial block height. Exiting.")
        sys.exit(1)
        
    # Calculate the next valid clock-in block (for reference)
    next_clockin_block = calculate_next_clockin_block(current_height)
    
    print(f"Current block height: {current_height}")
    print(f"Next valid clock-in block: {next_clockin_block}")
    print(f"Target confirmation block: {TARGET_BLOCK}")
    print(f"Will send transaction on block: {SEND_ON_BLOCK}")
    
    # Check if target block is valid for clock-in
    blocks_since_start = TARGET_BLOCK - 2  # Assuming start_block = 2 for the Clock-in game
    if blocks_since_start % 144 != 0:
        print(f"WARNING: Block {TARGET_BLOCK} does not appear to be a valid clock-in block!")
        print(f"Valid clock-in blocks occur every 144 blocks from the start block.")
        print(f"Consider using block {next_clockin_block} instead.")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(0)
    
    blocks_remaining = SEND_ON_BLOCK - current_height
    if blocks_remaining < 0:
        print(f"Send block {SEND_ON_BLOCK} has already passed (current: {current_height}). Exiting.")
        sys.exit(1)
    
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
            success = send_transaction()
            print("Transaction sent. Shutting down.")
            sys.exit(0 if success else 1)
            
        # Check if we've missed the target block
        if current_height > SEND_ON_BLOCK:
            print(f"Target send block {SEND_ON_BLOCK} has passed (current: {current_height}). Exiting without sending transaction.")
            sys.exit(1)

if __name__ == "__main__":
    main()
