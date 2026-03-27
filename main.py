
import discord
from discord.ext import commands
import os

class PellaBot(commands.Bot):
    def __init__(self):
        # Intents.all() ensures the bot can see messages starting with '>'
        intents = discord.Intents.all()
        super().__init__(command_prefix=">", intents=intents, help_command=None)

    async def on_ready(self):
        print(f"✅ Pella Bot Online: {self.user}")
        await self.change_presence(activity=discord.Game(name="Securely Hosted"))

bot = PellaBot()

@bot.command(name="ping")
async def ping(ctx):
    """Replies with Pong and the current latency."""
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! Latency: {latency}ms")

# --- SECURE TOKEN FETCH ---
# Pella will inject the 'BOT_TOKEN' from your environment variables
TOKEN = os.getenv('BOT_TOKEN')

if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ ERROR: 'BOT_TOKEN' not found in Environment Variables!")
