import discord
from discord import app_commands
from discord.ext import commands
import os
import aiohttp

# --- CONFIGURATION ---
AUTHORIZED_USERS = [699055511667998750, 939735229747314729]

class StatusModal(discord.ui.Modal, title='Set Bot Status'):
    status_input = discord.ui.TextInput(
        label='New Status Text',
        placeholder='e.g. Managing Manitoba Ops',
        required=True,
        max_length=100
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.client.change_presence(activity=discord.Game(name=self.status_input.value))
        await interaction.response.send_message(f"✅ Status updated to: **{self.status_input.value}**", ephemeral=True)

class PellaBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix=">", intents=intents, help_command=None)

    async def on_ready(self):
        print(f"✅ Manitoba Global Ops Bot Online: {self.user}")

bot = PellaBot()

# --- THE SKELETON KEY SYNC ---
@bot.command(name="quicksync")
async def quicksync(ctx):
    if ctx.author.id not in AUTHORIZED_USERS: return
    await ctx.send("📡 Forcing Global Command Sync... Please wait.")
    try:
        synced = await bot.tree.sync()
        await ctx.send(f"✅ Success! {len(synced)} slash commands (including /botdash) are now registered globally. (May take a few mins to appear).")
    except Exception as e:
        await ctx.send(f"❌ Sync Error: {e}")

# --- THE SLASH COMMAND ---
@bot.tree.command(name="botdash", description="Manitoba Global Operations Bot Dashboard")
async def botdash(interaction: discord.Interaction):
    if interaction.user.id not in AUTHORIZED_USERS:
        return await interaction.response.send_message("❌ Access Denied: Unauthorized Developer.", ephemeral=True)

    payload = {
        "flags": 32768,
        "components": [
            {
                "type": 17,
                "components": [
                    {
                        "type": 9,
                        "components": [
                            {
                                "type": 10,
                                "content": "**Manitoba Global Operations Bot Dashboard**\nDevelopers can use the buttons and prompts below to edit core bot accessories.\n\n⚠️ **WARNING:** If you are not a Manitoba Engineer, use caution when using buttons below."
                            }
                        ],
                        "accessory": {
                            "type": 11,
                            "media": {
                                "url": "https://cdn.discordapp.com/attachments/1296716507803291661/1487159861119815850/MBGlobalOpsLogo.png"
                            }
                        }
                    },
                    {
                        "type": 14,
                        "spacing": 2
                    },
                    {
                        "type": 1,
                        "components": [
                            {
                                "style": 3,
                                "type": 2,
                                "label": "Set Custom Status",
                                "custom_id": "p_284757363318067206"
                            },
                            {
                                "style": 4,
                                "type": 2,
                                "label": "Sync Global Slash Commands",
                                "custom_id": "p_284757410839531528"
                            }
                        ]
                    }
                ]
            }
        ]
    }

    headers = {"Authorization": f"Bot {bot.http.token}", "Content-Type": "application/json"}
    url = f"https://discord.com/api/v10/interactions/{interaction.id}/{interaction.token}/callback"
    
    async with aiohttp.ClientSession() as session:
        await session.post(url, json={"type": 4, "data": payload}, headers=headers)

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component:
        cid = interaction.data.get("custom_id")
        
        if cid == "p_284757363318067206":
            if interaction.user.id not in AUTHORIZED_USERS: return
            await interaction.response.send_modal(StatusModal())
            
        elif cid == "p_284757410839531528":
            if interaction.user.id not in AUTHORIZED_USERS: return
            await interaction.response.defer(ephemeral=True)
            try:
                synced = await bot.tree.sync()
                await interaction.followup.send(f"✅ Global Sync Success: {len(synced)} commands updated.", ephemeral=True)
            except Exception as e:
                await interaction.followup.send(f"❌ Sync Error: {e}", ephemeral=True)

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send(f"🏓 Pong! Latency: {round(bot.latency * 1000)}ms")

TOKEN = os.getenv('BOT_TOKEN')
if TOKEN:
    bot.run(TOKEN)
