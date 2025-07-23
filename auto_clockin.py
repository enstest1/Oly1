#!/usr/bin/env python3 """ Multi-wallet Oyl Clock-in System with Discord Handles 3 wallets, block countdown, time estimate, error output """

import os import time import subprocess import requests import sys import json import datetime import re from dotenv import load_dotenv from collections import defaultdict

load_dotenv()

BLOCK_API_URL = "https://blockstream.info/api/blocks/tip/height" FEE_API_URL = "https://mempool.space/api/v1/fees/recommended" POLL_INTERVAL = 10 MAX_ATTEMPTS = 3 DEPLOY_BLOCK = 897413 WALLET_COUNT = 3

WALLET_LABELS = { 1: "Oyl Wallet #1", 2: "Oyl Wallet #2", 3: "Oyl Wallet #3" } WALLET_STATS = defaultdict(lambda: {"total": 0, "streak": 0, "max_streak": 0})

wallets = {} for i in range(1, WALLET_COUNT + 1): mnemonic = os.getenv(f"MNEMONIC_{i}") sand_id = os.getenv(f"SANDSHREW_PROJECT_ID_{i}") if mnemonic and sand_id: wallets[i] = { "mnemonic": mnemonic, "sand": sand_id, "target_block": 906773 + (i - 1) * 2, }

def get_current_block_height(): try: r = requests.get(BLOCK_API_URL, timeout=10) r.raise_for_status() return int(r.text.strip()) except Exception as e: print(f"Block height error: {e}") return None

def get_dynamic_fee(): try: r = requests.get(FEE_API_URL, timeout=10) r.raise_for_status() data = r.json() return max(data.get("fastestFee", 10), data.get("halfHourFee", 10)) + 3 except: return 13

def send_discord_notification(msg): url = os.getenv("DISCORD_WEBHOOK_URL") if not url: return try: data = {"content": msg} r = requests.post(url, data=json.dumps(data), headers={"Content-Type": "application/json"}) except Exception as e: print(f"Discord error: {e}")

def send_transaction(wallet_num): fee = get_dynamic_fee() cmd = f"oyl alkane execute -data 2,21568,103 -p bitcoin -feeRate {fee}" for i in range(MAX_ATTEMPTS): try: print(f"Sending TX for wallet #{wallet_num}, attempt {i+1}") result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True) match = re.search(r"txId['"]?\s*[:=]\s*['"]?([a-fA-F0-9]{64})", result.stdout) return True, match.group(1) if match else None except subprocess.CalledProcessError as e: print(f"Attempt {i+1} failed:\n{e.stdout}\n{e.stderr}") if "oyl: not found" in e.stderr: send_discord_notification(f"❌ ERROR: oyl command not found for Wallet #{wallet_num}! Is it installed on Railway?") break time.sleep(5) return False, None

def calculate_next_clockin(current): delta = current - DEPLOY_BLOCK remain = 144 - (delta % 144) return current if remain == 144 else current + remain

def get_eta_info(current, target): blocks_remaining = target - current eta_minutes = blocks_remaining * 10 eta_time_utc = datetime.datetime.utcnow() + datetime.timedelta(minutes=eta_minutes) return blocks_remaining, eta_minutes, eta_time_utc.strftime("%H:%M UTC")

def main(): current = get_current_block_height() if current is None: return

for i in range(1, WALLET_COUNT + 1):
    if i not in wallets:
        continue
    w = wallets[i]
    target = w["target_block"]
    send_block = target - 1

    while send_block <= current:
        w["target_block"] += 144
        target = w["target_block"]
        send_block = target - 1

    blocks_left, eta_min, eta_time = get_eta_info(current, target)

    send_discord_notification(
        f"⏰ {WALLET_LABELS[i]}\nSend block: {send_block}\nTarget: {target}\nETA: ~{eta_min} min (~{eta_time})\n⏳ Blocks remaining: {send_block - current}\nCurrent block: {current}"
    )

while True:
    time.sleep(POLL_INTERVAL)
    current = get_current_block_height()
    if current is None:
        continue

    for i in range(1, WALLET_COUNT + 1):
        if i not in wallets:
            continue
        w = wallets[i]
        target = w["target_block"]
        send_block = target - 1

        if current == send_block:
            send_discord_notification(f"🚀 Sending Oyl Corp clock-in for {WALLET_LABELS[i]} (block {send_block})")
            success, txid = send_transaction(i)
            if success:
                WALLET_STATS[i]["total"] += 1
                WALLET_STATS[i]["streak"] += 1
                WALLET_STATS[i]["max_streak"] = max(WALLET_STATS[i]["max_streak"], WALLET_STATS[i]["streak"])
                send_discord_notification(f"{WALLET_LABELS[i]} ✅️⏰️🟧\ntxId: {txid or 'N/A'}")
            else:
                WALLET_STATS[i]["streak"] = 0
                send_discord_notification(f"{WALLET_LABELS[i]} ❌️⏰️")
            wallets[i]["target_block"] += 144

if name == "main": main()

