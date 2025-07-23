import os
import subprocess
import re
import time
import random
import discord
from discord.ext import commands
from datetime import datetime, timedelta

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

wallets = [
    {"mnemonic": os.getenv("MNEMONIC_1"), "sandshare": os.getenv("SANDSHARE_1")},
    {"mnemonic": os.getenv("MNEMONIC_2"), "sandshare": os.getenv("SANDSHARE_2")},
    {"mnemonic": os.getenv("MNEMONIC_3"), "sandshare": os.getenv("SANDSHARE_3")}
]

MAX_ATTEMPTS = 3
clockin_history = {0: [], 1: [], 2: []}

intents = discord.Intents.default()
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

def get_dynamic_fee():
    # Dummy function, replace with API call if needed
    return round(random.uniform(1.5, 2.5), 2)

def get_estimated_time():
    now = datetime.utcnow()
    hours = random.randint(10, 14)
    eta = now + timedelta(hours=hours)
    return eta.strftime("%I:%M %p UTC")

def send_discord_notification(message):
    async def inner():
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            await channel.send(message)
    bot.loop.create_task(inner())

def send_transaction(wallet_num):
    fee = get_dynamic_fee()
    cmd = f"oyl alkane execute --data 2,21568,103 -p bitcoin -feeRate {fee}"
    
    for i in range(MAX_ATTEMPTS):
        try:
            print(f"Sending TX for wallet #{wallet_num + 1}, attempt {i+1}")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
            match = re.search(r'txId[\'"]?\s*[:=]\s*[\'"]?([a-fA-F0-9]{64})', result.stdout)
            if match:
                clockin_history[wallet_num].append(True)
                send_discord_notification(f"Oly Wallet #{wallet_num + 1} ✅️⏰️🟧\nTX: `{match.group(1)}`")
                return True, match.group(1)
            else:
                clockin_history[wallet_num].append(False)
        except subprocess.CalledProcessError as e:
            print(f"Error in wallet #{wallet_num + 1}, attempt {i+1}: {e.stderr}")
            if "oyl: not found" in e.stderr:
                send_discord_notification(f"Oly Wallet #{wallet_num + 1} ❌️⏰️\n`oyl` command not found.")
                break
            time.sleep(5)
    
    send_discord_notification(f"Oly Wallet #{wallet_num + 1} ❌️⏰️\nClock-in failed after {MAX_ATTEMPTS} attempts.")
    clockin_history[wallet_num].append(False)
    return False, None

def get_blocks_remaining():
    return random.randint(5, 25)  # Replace with real query if available

def get_streak(wallet_num):
    history = clockin_history[wallet_num]
    current = 0
    max_streak = 0
    for h in history:
        if h:
            current += 1
            max_streak = max(max_streak, current)
        else:
            current = 0
    return len([x for x in history if x]), max_streak

@bot.event
async def on_ready():
    print(f"Bot is live as {bot.user}")
    for idx in range(len(wallets)):
        send_transaction(idx)

@bot.event
async def on_message(message):
    if message.channel.id != CHANNEL_ID or message.author == bot.user:
        return

    content = message.content.strip().lower()

    if content in ["block", "check", "⏰️"]:
        blocks = get_blocks_remaining()
        eta = get_estimated_time()
        await message.channel.send(f"⏰️ ~{blocks} blocks (~est. {eta}) until next mint.")

    elif content in ["#1", "#2", "#3"]:
        wallet_num = int(content[1]) - 1
        total, streak = get_streak(wallet_num)
        await message.channel.send(f"📊 Oly Wallet #{wallet_num + 1} — Clock-ins: `{total}` | Longest streak: `{streak}`")

bot.run(TOKEN)
