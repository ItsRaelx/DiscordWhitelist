import os
import re
import requests
import discord
import sqlite3
import asyncio
from discord.ext import commands
from mcrcon import MCRcon
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
ROLE_ID = int(os.getenv('ROLE_ID'))

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.message_content = True

bot = commands.Bot(command_prefix=None, intents=intents, help_command=None)

conn = sqlite3.connect('users.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (discord_id INTEGER, minecraft_username TEXT, PRIMARY KEY (discord_id, minecraft_username))''')
conn.commit()

RCON_IP = os.getenv('RCON_IP')
RCON_PORT = int(os.getenv('RCON_PORT'))
RCON_PASSWORD = os.getenv('RCON_PASSWORD')

async def add_user_to_database(discord_id: int, minecraft_username: str):
    c.execute("INSERT OR IGNORE INTO users (discord_id, minecraft_username) VALUES (?, ?)", (discord_id, minecraft_username))
    conn.commit()
    await update_presence()

async def remove_user_from_database(discord_id: int, minecraft_username: str):
    c.execute("DELETE FROM users WHERE discord_id=? AND minecraft_username=?", (discord_id, minecraft_username))
    conn.commit()
    await update_presence()

async def user_has_added_to_database(discord_id: int):
    c.execute("SELECT * FROM users WHERE discord_id=?", (discord_id,))
    if c.fetchone() is not None:
        return True
    else:
        return False
    
# Check if Minecraft username is already in the database
async def minecraft_username_exists_in_database(minecraft_username: str):
    c.execute("SELECT * FROM users WHERE minecraft_username=?", (minecraft_username,))
    if c.fetchone() is not None:
        return True
    else:
        return False
    
async def update_presence():
    count = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching,
        name=f"{count} users in the whitelist"
    ))

async def add_user_to_whitelist(username: str):
    try:
        loop = asyncio.get_event_loop()
        with MCRcon(RCON_IP, RCON_PASSWORD, RCON_PORT) as mcr:
            response = await loop.run_in_executor(None, mcr.command, f'whitelist add {username}')
        return response
    except Exception as e:
        print(e)
        return None
    
async def remove_user_from_whitelist(minecraft_username: str):
    try:
        loop = asyncio.get_event_loop()
        with MCRcon(os.environ['RCON_IP'], os.environ['RCON_PASSWORD'], int(os.environ['RCON_PORT'])) as mcr:
            response = await loop.run_in_executor(None, mcr.command, f'whitelist remove {minecraft_username}')
        return response
    except Exception as e:
        print(e)
        return None
   
async def process_remove_user(message, minecraft_username, discord_user_id=None):
    rcon_response = await remove_user_from_whitelist(minecraft_username)
    if rcon_response is not None:
        embed = discord.Embed(
            title=f"{minecraft_username} został usunięty z whitelisty!",
            description=f"{message.author.mention} usunął `{minecraft_username}` z whitelisty.",
            color=0xFF0000
        )
        if discord_user_id:
            await remove_user_from_database(discord_user_id, minecraft_username)
        await message.channel.send(embed=embed, reference=message)
    else:
        await message.channel.send(f"An error occurred while removing `{minecraft_username}` from the whitelist.", reference=message)

def check_minecraft_premium(username: str):
    mojang_api_url = f'https://api.mojang.com/users/profiles/minecraft/{username}'
    response = requests.get(mojang_api_url)

    if response.status_code == 200:
        data = response.json()
        return True, data['id']
    else:
        return False, None


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    await update_presence()

@bot.event
async def on_message(message):
    if message.author == bot.user or message.channel.id != CHANNEL_ID:
        return
    
    has_role = False
    do_delete = True
    
    # Check if the user has the admin role
    for role in message.author.roles:
        if role.id == ROLE_ID:
            has_role = True

    # Check if the message contains a valid Minecraft username
    if re.match(r"^[a-zA-Z0-9_]{3,16}$", message.content) and (not await user_has_added_to_database(message.author.id) or has_role) and not await minecraft_username_exists_in_database(message.content.strip()):
        minecraft_username = message.content.strip()
        is_premium, uuid = check_minecraft_premium(minecraft_username)

        if is_premium:
            rcon_response = await add_user_to_whitelist(minecraft_username)
            if rcon_response is not None:
                embed = discord.Embed(
                    title=f"{minecraft_username} został dodany do whitelist!",
                    description=f"{message.author.mention} dodał `{minecraft_username}` do whitelisty.",
                    color=0x00FF00
                )
                embed.set_thumbnail(url=f'https://mc-heads.net/head/{uuid}')
                await message.channel.send(embed=embed, reference=message)

                await add_user_to_database(message.author.id, minecraft_username)
                do_delete = False
            else:
                await message.channel.send(f"An error occurred while adding `{minecraft_username}` to the whitelist.", reference=message)
                do_delete = False

    # Check if the message is a remove user command with a mention or a username
    remove_command = re.search(r"^!((<@!?(\d+)>)|([a-zA-Z0-9_]{3,16}))$", message.content)
    if remove_command:
        mentioned_user = remove_command.group(3)
        minecraft_username = remove_command.group(4)

        if mentioned_user:
            if message.author.id == int(mentioned_user) or has_role:
                c.execute("SELECT minecraft_username FROM users WHERE discord_id=?", (int(mentioned_user),))
                usernames = c.fetchall()
                for username in usernames:
                    do_delete = False
                    await process_remove_user(message, username[0], discord_user_id=int(mentioned_user))

        elif minecraft_username:
            c.execute("SELECT discord_id FROM users WHERE minecraft_username=?", (minecraft_username,))
            user_data = c.fetchone()

            if has_role and user_data:
                do_delete = False
                await process_remove_user(message, minecraft_username, discord_user_id=user_data[0])
            elif user_data and user_data[0] == message.author.id:
                do_delete = False
                await process_remove_user(message, minecraft_username, discord_user_id=message.author.id)
            elif not user_data:
                do_delete = False
                await message.channel.send(f"`{minecraft_username}` is not in the whitelist.", reference=message)

    if do_delete:
        await message.delete()

bot.run(TOKEN)
