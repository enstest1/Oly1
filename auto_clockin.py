import os
import time
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# Simulated wallet clock-in data (replace with real logic)
WALLETS = {
    1: {"clocked_in": 0, "streak": 0},
    2: {"clocked_in": 0, "streak": 0},
    3: {"clocked_in": 0, "streak": 0},
}

BLOCK_INTERVAL = 600  # 10 min/block (in seconds)
TARGET_BLOCK_OFFSET = 145  # Example: send on block +145

CURRENT_BLOCK = 906628  # Simulated value — replace with actual block fetch

def send_webhook_message(message):
    if WEBHOOK_URL:
        try:
            requests.post(WEBHOOK_URL, json={"content": message})
        except Exception as e:
            print("❌ Failed to send webhook:", e)

def get_current_block():
    # Replace this with actual chain query logic if available
    return CURRENT_BLOCK

def estimate_time(blocks_left):
    seconds = blocks_left * BLOCK_INTERVAL
    eta = datetime.utcnow() + timedelta(seconds=seconds)
    return eta.strftime('%Y-%m-%d %H:%M UTC')

def get_next_block_info():
    current = get_current_block()
    send_at = current + TARGET_BLOCK_OFFSET
    eta = estimate_time(send_at - current)
    return send_at, eta

def perform_clockin(wallet_id):
    # Replace this with actual transaction logic
    success = True  # simulate
    if success:
        WALLETS[wallet_id]["clocked_in"] += 1
        WALLETS[wallet_id]["streak"] += 1
        send_webhook_message(f"✅ Wallet #{wallet_id} clock-in successful! ✅\nStreak: {WALLETS[wallet_id]['streak']}")
    else:
        WALLETS[wallet_id]["streak"] = 0
        send_webhook_message(f"❌ Wallet #{wallet_id} clock-in FAILED!")

def start_clockin_loop():
    while True:
        current_block = get_current_block()
        target_block, eta = get_next_block_info()

        send_webhook_message(
            f"⏰ Upcoming Oyl Corp clock-in\n"
            f"Send block: `{target_block - 1}`\n"
            f"Target block: `{target_block}`\n"
            f"ETA: {eta}\n"
            f"Current block: {current_block}"
        )

        while get_current_block() < target_block - 1:
            time.sleep(60)  # Check every minute

        for wallet_id in WALLETS:
            perform_clockin(wallet_id)

        time.sleep(BLOCK_INTERVAL)

if __name__ == "__main__":
    send_webhook_message("🟢 Auto Clock-In Bot is running")
    start_clockin_loop()
