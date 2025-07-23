import discord
import asyncio
import os
from auto_clockin import start_clockin, get_streak_info, get_next_block_info
from discord.ext import commands

intents = discord.Intents.default()
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", ""))
WALLETS_ENABLED = [1, 2, 3]

@bot.event
async def on_ready():
    print(f"{bot.user} is online.")
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if channel:
        await channel.send(
            "🟢 **Oyl Clock Bot is online!**\n"
            "Listening for `#1`, `#2`, `block`, `⏰`\n"
            f"Wallets loaded: {', '.join(f'#{w}' for w in WALLETS_ENABLED)}"
        )

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content.strip().lower()

    if content in ("block", "⏰", "check"):
        blocks_left, eta = get_next_block_info()
        await message.channel.send(f"⏰ ~{blocks_left} blocks left (~est. {eta} UTC)")

    elif content.startswith("#") and content[1:].isdigit():
        wallet_num = int(content[1:])
        if wallet_num in WALLETS_ENABLED:
            count, streak = get_streak_info(wallet_num)
            await message.channel.send(
                f"📊 Oly Wallet #{wallet_num} — Clock-ins: `{count}` | Longest streak: `{streak}`"
            )

    await bot.process_commands(message)

def run_bot():
    token = os.getenv("DISCORD_BOT_TOKEN")
    bot.loop.create_task(start_clockin())
    bot.run(token)

if __name__ == "__main__":
    run_bot()
