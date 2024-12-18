import discord
from discord.ext import tasks
from discord.ext import commands
import json
import os
import subprocess

# clone_process = subprocess.run(
#     ["ls"],
#     capture_output=True,
#     text=True
# )
# clone_output = clone_process.stdout + clone_process.stderr
# print(f"Cloned \"{clone_output}\"")
# exit()

DATA_FILE = "data.json"

#Bot

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())


#Todo list

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)

@bot.event
async def on_ready():
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} commands")
    git_pinger.start()
    print("Ready!")

@bot.tree.command(
    name="setup",
    description="Set the channel where the todo list will be",
)
async def set_todo_channel(interaction: discord.Interaction, todo_channel: discord.TextChannel, done_channel: discord.TextChannel):
    todo_message = await todo_channel.send("## Todo List ##")
    done_message = await done_channel.send("## Done List ##")
    data = load_data()
    data[str(interaction.guild_id)]["todo_channel"] = todo_channel.id
    data[str(interaction.guild_id)]["done_channel"] = done_channel.id
    data[str(interaction.guild_id)]["todo_message"] = todo_message.id
    data[str(interaction.guild_id)]["done_message"] = done_message.id
    save_data(data)
    await interaction.response.send_message("Setup complete")

@bot.tree.command(
    name="add",
    description="Add an item to the list",
)
async def add_list(interaction: discord.Interaction, item: str):
    data = load_data()
    if str(interaction.guild_id) not in data.keys():
        await interaction.response.send_message("You need to setup the channels first")
        return
    todo_channel = bot.get_channel(data[str(interaction.guild_id)]["todo_channel"])
    todo_message = await todo_channel.fetch_message(data[str(interaction.guild_id)]["todo_message"])
    
    await todo_message.edit(content=f"{todo_message.content}\n- {item}")
    await interaction.response.send_message(f"Added \"{item}\" to the list")

@bot.tree.command(
    name="remove",
    description="Remove an item from the list",
)
async def remove_list(interaction: discord.Interaction, item: str):
    data = load_data()
    if str(interaction.guild_id) not in data.keys():
        await interaction.response.send_message("You need to setup the channels first")
        return
    todo_channel = bot.get_channel(data[str(interaction.guild_id)]["todo_channel"])
    todo_message = await todo_channel.fetch_message(data[str(interaction.guild_id)]["todo_message"])

    lines = todo_message.content.split("\n")
    for i, line in enumerate(lines):
        if line == f"- {item}":
            lines.pop(i)
            await todo_message.edit(content="\n".join(lines))
            await interaction.response.send_message(f"Removed \"{item}\" from the list")
    await interaction.response.send_message(f"Item \"{item}\" not found")

@bot.tree.command(
    name="remove_index",
    description="Remove an item from the list by index",
)
async def remove_index_list(interaction: discord.Interaction, index: int):
    data = load_data()
    if str(interaction.guild_id) not in data.keys():
        await interaction.response.send_message("You need to setup the channels first")
        return
    todo_channel = bot.get_channel(data[str(interaction.guild_id)]["todo_channel"])
    todo_message = await todo_channel.fetch_message(data[str(interaction.guild_id)]["todo_message"])

    lines = todo_message.content.split("\n")
    if index < 0 or index >= len(lines):
        await interaction.response.send_message("Index out of bounds")
        return
    lines.pop(index)
    await todo_message.edit(content="\n".join(lines))
    await interaction.response.send_message(f"Removed item at index {index}")

@bot.tree.command(
    name="done",
    description="Mark an item as done",
)
async def done_list(interaction: discord.Interaction, item: str):
    data = load_data()
    if str(interaction.guild_id) not in data.keys():
        await interaction.response.send_message("You need to setup the channels first")
        return
    todo_channel = bot.get_channel(data[str(interaction.guild_id)]["todo_channel"])
    done_channel = bot.get_channel(data[str(interaction.guild_id)]["done_channel"])
    todo_message = await todo_channel.fetch_message(data[str(interaction.guild_id)]["todo_message"])
    done_message = await done_channel.fetch_message(data[str(interaction.guild_id)]["done_message"])

    lines = todo_message.content.split("\n")
    for i, line in enumerate(lines):
        if line == f"- {item}":
            lines.pop(i)
            break
    await todo_message.edit(content="\n".join(lines))
    await done_message.edit(content=f"{done_message.content}\n- ✅ {item} (by {interaction.user.mention})")
    await interaction.response.send_message(f"Marked \"{item}\" as done")


#Git pinger

@bot.tree.command(
    name="setup_git",
    description="Set the channel where the git pinger will be",
)
async def set_git_channel(interaction: discord.Interaction, git_channel: discord.TextChannel, git_repo: str):
    os.system(f"mkdir -p data/{interaction.guild_id}")
    clone_process = subprocess.run(
        ["git", "clone", git_repo, f"data/{interaction.guild_id}"],
        capture_output=True,
        text=True
    )
    clone_output = clone_process.stdout + clone_process.stderr
    data = load_data()
    data[str(interaction.guild_id)]["git_channel"] = git_channel.id
    save_data(data)
    if clone_process.returncode != 0:
        await interaction.response.send_message(f"Error cloning `{git_repo}`: ```{clone_output}```")
        return
    await git_channel.send(f"`{git_repo}` cloned")
    await interaction.response.send_message("Setup complete")

# Execute this fonction automatically every 5 minutes
# @tasks.loop(minutes=5)
@tasks.loop(seconds=10)
async def git_pinger():
    print("Pinging git")
    data = load_data()
    for guild_id, guild_data in data.items():
        if "git_channel" not in guild_data:
            continue
        git_channel = bot.get_channel(guild_data["git_channel"])
        pull_process = subprocess.run(
            ["git", "-C", f"data/{guild_id}", "pull"],
            capture_output=True,
            text=True
        )
        pull_output = pull_process.stdout + pull_process.stderr
        print("Pulled \"" + pull_output + "\"")
        if pull_output != "Already up to date.\n":
            await git_channel.send("```" + pull_output + "```")


#Token

tokenError = "Write your token in a .env file (token=your_token or see the .env.example file)"
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