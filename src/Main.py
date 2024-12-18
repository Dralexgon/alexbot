import discord
from discord import app_commands
from discord.ext import commands

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

todoChannel = 0#write id here

@bot.event
async def on_ready():
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} commands")
    print("Ready!")

@bot.tree.command(
    name="add",
    description="Add an item to the list",
)
async def move_token(interaction: discord.Interaction, item: str):
    await interaction.response.send_message(f"Added {item} to the list")
    #get last message
    channel = await bot.fetch_channel(todoChannel)
    messages = await channel.history(limit=1).flatten()
    lastMessage = messages[0]
    #edit last message
    await lastMessage.edit(content=lastMessage.content + f"\n- {item}")

#Token
tokenError = "Write your token in a .env file (token=your_token or see the example.env file)"
found = False
try:
    for line in open(r".env", "r").readlines():
        if line.split("=")[0] == "TOKEN":
            bot.run(line.split("=")[1])
            found = True
            break
    if not found: print(tokenError)
except FileNotFoundError:
    print(tokenError)