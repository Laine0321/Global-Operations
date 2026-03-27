import discord
from discord import app_commands
from discord.ext import commands
import os
import aiohttp
import time

# --- CONFIGURATION ---
AUTHORIZED_USERS = [699055511667998750, 939735229747314729]
AUTHORIZED_ROLES = [1414310559423266936, 1394546258911166474, 1402422421050495026]
LOG_CHANNEL_ID = 1487200618845311016
LOGO_URL = "https://cdn.discordapp.com/attachments/1296716507803291661/1487159861119815850/MBGlobalOpsLogo.png"

# Department Channel IDs
CHANNELS = {
    "fire": 1403424467992186940,
    "wps": 1394549831904657539,
    "rcmp": 1382585364140527626
}

# Custom Capital Alphabet Mapping
CUSTOM_CAPS = {
    'A': '𝖠', 'B': '𝖡', 'C': '𝖢', 'D': '𝖣', 'E': '𝖤', 'F': '𝖥', 'G': '𝖦', 'H': '𝖧',
    'I': '𝖨', 'J': '𝖩', 'K': '𝖪', 'L': '𝖫', 'M': '𝖬', 'N': '𝖭', 'O': '𝖮', 'P': '𝖯',
    'Q': '𝖰', 'R': '𝖱', 'S': '𝖲', 'T': '𝖳', 'U': '𝖴', 'V': '𝖵', 'W': '𝖶', 'X': '𝖷',
    'Y': '𝖸', 'Z': '𝖹'
}

def transform_name(name: str):
    return "".join(CUSTOM_CAPS.get(char, char) for char in name)

async def send_mgo_log(bot, command_name, department, user_id, extra_info="None"):
    """Sends the custom JSON component log to the logging channel with V2 Flag fix."""
    timestamp = f"<t:{int(time.time())}:f>"
    content_body = (
        f"**MGO Action Log**\n"
        f"**{command_name}** used in **{department}** by <@{user_id}>\n\n"
        f"{extra_info}\n\n"
        f"-# Manitoba Global Operations - {timestamp}"
    )

    # EXACT payload for Discord's NEW Components V2 architecture
    payload = {
        "flags": 32768, # IS_COMPONENTS_V2 Flag
        "components": [
            {
                "type": 17, # Container
                "components": [
                    {
                        "type": 9, # Section
                        "components": [
                            {
                                "type": 10, # Text Display
                                "content": content_body
                            }
                        ],
                        "accessory": {
                            "type": 11, # Thumbnail
                            "media": {"url": LOGO_URL}
                        }
                    }
                ]
            }
        ]
    }

    headers = {
        "Authorization": f"Bot {bot.http.token}",
        "Content-Type": "application/json"
    }
    
    url = f"https://discord.com/api/v10/channels/{LOG_CHANNEL_ID}/messages"
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                print(f"❌ Log failed with status {resp.status}: {error_text}")

class StatusModal(discord.ui.Modal, title='Set Bot Status'):
    status_input = discord.ui.TextInput(label='New Status Text', required=True, max_length=100)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.client.change_presence(activity=discord.Game(name=self.status_input.value))
        await interaction.response.send_message(f"✅ Status updated.", ephemeral=True)
        await send_mgo_log(interaction.client, "Status Update", "Global", interaction.user.id, f"New Status: {self.status_input.value}")

class PellaBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix=">", intents=intents, help_command=None)

    async def on_ready(self):
        print(f"✅ MGO Bot Online: {self.user}")

bot = PellaBot()

@bot.command(name="quicksync")
async def quicksync(ctx):
    if ctx.author.id not in AUTHORIZED_USERS: return
    synced = await bot.tree.sync()
    await ctx.send(f"✅ Synced {len(synced)} commands.")

@bot.tree.command(name="rename-channel", description="Rename a channel using the custom MB alphabet")
async def rename_channel(interaction: discord.Interaction, channel: discord.abc.GuildChannel, new_name: str):
    user_role_ids = [role.id for role in interaction.user.roles]
    if not any(role_id in AUTHORIZED_ROLES for role_id in user_role_ids) and interaction.user.id not in AUTHORIZED_USERS:
        return await interaction.response.send_message("❌ Unauthorized.", ephemeral=True)

    transformed = transform_name(new_name)
    old_name = channel.name
    try:
        await channel.edit(name=transformed)
        await interaction.response.send_message(f"✅ Renamed to **#{transformed}**", ephemeral=True)
        await send_mgo_log(bot, "/rename-channel", interaction.guild.name, interaction.user.id, f"Old: #{old_name} | New: #{transformed}")
    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

@bot.tree.command(name="announce", description="Announce a message to specific departments")
@app_commands.choices(department=[
    app_commands.Choice(name="Fire Operations", value="fire"),
    app_commands.Choice(name="Law Enforcement", value="leo"),
    app_commands.Choice(name="All Departments", value="all")
])
async def announce(interaction: discord.Interaction, message: str, department: str):
    if interaction.user.id not in AUTHORIZED_USERS:
        return await interaction.response.send_message("❌ Unauthorized.", ephemeral=True)
    
    await interaction.response.defer(ephemeral=True)
    target_ids = []
    if department == "fire": target_ids = [CHANNELS["fire"]]
    elif department == "leo": target_ids = [CHANNELS["wps"], CHANNELS["rcmp"]]
    elif department == "all": target_ids = list(CHANNELS.values())

    success_count = 0
    for cid in target_ids:
        channel = bot.get_channel(cid)
        if channel:
            try:
                await channel.send(content=message)
                success_count += 1
            except: pass

    await interaction.followup.send(f"✅ Sent to {success_count} channels.", ephemeral=True)
    await send_mgo_log(bot, "/announce", department.upper(), interaction.user.id, f"Message: {message}")

@bot.tree.command(name="botdash", description="Manitoba Global Operations Bot Dashboard")
async def botdash(interaction: discord.Interaction):
    if interaction.user.id not in AUTHORIZED_USERS:
        return await interaction.response.send_message("❌ Access Denied.", ephemeral=True)

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
                                "content": "**Manitoba Global Operations Bot Dashboard**\nDevelopers can use the buttons and prompts below to edit core bot accessories."
                            }
                        ],
                        "accessory": {"type": 11, "media": {"url": LOGO_URL}}
                    },
                    {"type": 14, "spacing": 2},
                    {
                        "type": 1,
                        "components": [
                            {"style": 3, "type": 2, "label": "Set Custom Status", "custom_id": "p_284757363318067206"},
                            {"style": 4, "type": 2, "label": "Sync Global Slash Commands", "custom_id": "p_284757410839531528"}
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
    await send_mgo_log(bot, "/botdash", "Admin", interaction.user.id, "Dashboard accessed.")

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
            synced = await bot.tree.sync()
            await interaction.followup.send(f"✅ Global Sync Complete.", ephemeral=True)
            await send_mgo_log(bot, "Global Sync", "System", interaction.user.id, f"Commands Synced: {len(synced)}")

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send(f"🏓 Pong! {round(bot.latency * 1000)}ms")

TOKEN = os.getenv('BOT_TOKEN')
bot.run(TOKEN)
