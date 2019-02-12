"""Main entry for lmao-bot"""
# TODO: Use docstrings to clean up help menu

# Standard Python imports
import logging
import io
import inspect
import time
from datetime import datetime, timedelta
import socket
import os
import json
import random

# Pip imports
import asyncio
import discord
from discord.ext import commands
import aiohttp

# First-party imports
from modules import dblpy, fun
from utils import lbvars, lbutil, dbl, perms

# Renames the previous log file so there is a continuous record of log files
try:
    os.rename("logs/lmao.log", f"logs/lmao-{time.time()}.log")
except FileNotFoundError:
    pass

#Sets up logging here so we don't have to shoot ourselves
lbvars.LOGGER = logging.getLogger('discord')
lbvars.LOGGER.setLevel(logging.INFO)
FORMATTER = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
FILEHANDLER = logging.FileHandler(filename='logs/lmao.log', encoding='utf-8', mode='w')
FILEHANDLER.setFormatter(FORMATTER)
STREAMHANDLER = logging.StreamHandler()
STREAMHANDLER.setFormatter(FORMATTER)
lbvars.LOGGER.addHandler(STREAMHANDLER)
lbvars.LOGGER.addHandler(FILEHANDLER)

lbvars.LOGGER.info("lmao-bot is loading...")

def get_pre(bot, message):
    "Gets the prefix for the guild the message was sent it, otherwise returns lmao"
    try:
        prefix = lbvars.get_prefix(message.guild.id)
    except discord.ext.commands.errors.CommandInvokeError:
        prefix = "lmao"
    prefixes = lbutil.get_permutations(prefix) # Returns a list of strings that are prefixes
    return prefixes

def get_mentioned_or_pre(bot, message):
    prefixes = get_pre(bot, message)
    return commands.when_mentioned_or(*prefixes)(bot, message)

BOT = commands.AutoShardedBot(command_prefix=get_mentioned_or_pre, case_insensitive=True)
BOT.remove_command("help")

def starts_with_prefix(message):
    "Determines whether or not the current prefix was used in the message."
    if message.content.startswith(BOT.user.mention):
        return True
    prefixes = get_pre(BOT, message)
    for prefix in prefixes:
        if message.content.startswith(prefix):
            return True
    return False

def load_extensions(bot):
    """Loads all extensions found in the modules folder."""
    os.chdir(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) + "/modules")
    if __name__ == "__main__":
        for path in os.listdir():
            if os.path.isfile(path):
                module = os.path.splitext(path)[0]
                if module != "__init__":
                    try:
                        bot.load_extension(f"modules.{module}")
                        lbvars.LOGGER.info("%s sucessfully loaded.", module)
                    except Exception as Ex:
                        lbvars.LOGGER.info("%s could not be loaded because %s.", module, Ex)
    os.chdir("..")

load_extensions(BOT)
BOT.load_extension("events.onmemberjoin")
BOT.load_extension("events.onguildjoin")
BOT.load_extension("events.onmemberremove")
BOT.load_extension("events.onguildremove")
#BOT.load_extension("events.onvoicestateupdate") commented out, not sure if required by lavalink

def get_all_commands():
    """Returns all commands in the bot set by Discord.ext"""
    commands = []
    for command in BOT.commands:
        commands.append(command.name)
        for alias in command.aliases:
            commands.append(alias)
    return commands

lbvars.LOGGER.info("All extensions loaded.")

dblpy = BOT.cogs.get("DBL")

with io.open("../tokens/token.txt", "r") as token:
    bot_token = (token.read()).strip()
with io.open("../tokens/dbl.txt", "r") as token:
    dbl_token = (token.read()).strip()
lbvars.dbl_url = "https://discordbots.org/api/bots/459432854821142529/stats"
lbvars.dbl_headers = {"Authorization" : dbl_token}

bot_is_ready = False        # If bot is not ready, on_message event will not fire

async def check_reminders(late=False):
    """Check all reminders"""
    with io.open("../data/reminders.json") as f:
        reminders = json.load(f)
        for i in range(len(reminders["reminders"]) - 1, -1, -1):
            reminder = reminders["reminders"][i]
            if int(reminder["timestamp"]) <= round(time.time() / 60):
                late_msg = ""
                if late:
                    late_msg = "(If you are receiving this reminder late, the bot was likely offline when you should have received it.)"
                e = discord.Embed(title=f"🎗️ Reminder for {reminder['set_for']}", description=f"{reminder['message']}\n\n{late_msg}")
                e.set_footer(text=f"{reminder['time']} reminder set on {reminder['set_on']}.")
                try:
                    await BOT.get_user(reminder["author"]).send(embed=e)
                except AttributeError:
                    print(f"Error in getting user {reminder['author']}")
                reminders["reminders"].pop(i)
        new_reminders = json.dumps(reminders, indent=4)
        with io.open("../data/reminders.json", "w+", encoding="utf-8") as fo:
            fo.write(new_reminders)

async def check_dc():
    keys_to_delete = []
    for guild_id, dc_time in lbvars.dc_time.items():
        if round((datetime.now() - dc_time).total_seconds()) >= 0:
            try:
                channel = BOT.get_cog("Music").players[guild_id]._channel
                await channel.send("⏰ The voice channel has been inactive for 15 minutes. Now leaving...")
                BOT.get_cog("Music").players.pop(guild_id, 0)
                await BOT.get_guild(guild_id).voice_client.disconnect()
                # player.destroy(player._guild)
                # await player.send_np(finished=True, timeout=True)
                # await BOT.get_guild(guild_id).voice_client.disconnect()
            except KeyError:
                pass
            keys_to_delete.append(guild_id)
    for key in keys_to_delete:
        del lbvars.dc_time[key]

lbvars.LOGGER.info("Importing settings...")
lbvars.import_settings()
lbvars.LOGGER.info("All settings successfully imported.")

@BOT.event
async def on_ready():
    """Prints ready message in terminal"""
    lbvars.reset_guild_count()
    for guild in BOT.guilds:
        # lbvars.update_settings(guild.id, lbvars.GuildSettings(guild.id))
        new_guild = lbvars.init_settings(guild.id)
        guild_count = lbvars.increment_guild_count()
        keyword = "OLD: "
        if new_guild:
            "NEW: "
        lbvars.LOGGER.info(str("#{}. {}{}.".format(guild_count, keyword, guild.name)))
    voted = await dblpy.get_upvote_info()
    lbvars.LOGGER.info(f"{len(voted)} users have voted.")
    lbvars.LOGGER.info("Logged in as")
    lbvars.LOGGER.info(BOT.user.name)
    lbvars.LOGGER.info(str(BOT.user.id))
    lbvars.LOGGER.info(str(datetime.now()))
    lbvars.LOGGER.info("------")
    await BOT.change_presence(activity=discord.Game(name=f"lmao help | {len(BOT.guilds)} servers"))
    lbvars.set_start_time(time.time())
    global bot_is_ready
    bot_is_ready = True
    dbl_connector = aiohttp.TCPConnector(family=socket.AF_INET,verify_ssl=False,force_close=True)
    payload = {"server_count"  : len(BOT.guilds), "shard_count": len(BOT.shards)}
    async with aiohttp.ClientSession(connector=dbl_connector) as aioclient:
        async with aioclient.post(lbvars.dbl_url, data=payload, headers=lbvars.dbl_headers):
            dbl_connector.close()
            await aioclient.close()
    try:
        await check_reminders(late=True)
    except Exception as Ex:
        lbvars.LOGGER.warning("Error: %s", Ex)
    await asyncio.sleep(60 - round(time.time()) % 60)
    while(True):
        try:
            await check_reminders()
        except Exception as Ex:
            lbvars.LOGGER.warning("Reminder check error: %s", Ex)
        try:
            await check_dc()
        except Exception as Ex:
            lbvars.LOGGER.warning("Disconnection check error: %s", Ex)
        if not lbvars.custom_game:
            await BOT.change_presence(activity=discord.Game(name=f"lmao help | {len(BOT.guilds)} servers"))
        await asyncio.sleep(60)

@BOT.event
async def on_message(message):  # Event triggers when message is sent
    """Runs whenever a message is sent"""
    if not bot_is_ready:
        return

    # Prevent the bot from activating from other bots
    if message.author.bot:
        return

    guild = message.guild
    if guild is None:
        guild = message.channel
    guild_id = str(guild.id)

    prefix = lbvars.get_prefix(guild_id)
    msg_raw = message.content
    msg = msg_raw.lower()

    ctx = commands.Context(message=message, bot=BOT, prefix=prefix)

    async def replace_ass():    # Sends the ass substitution message
        await BOT.get_command("replaceass").invoke(ctx)
        lbvars.set_last_use_time(time.time())

    if message.guild is None:
        lbvars.LOGGER.info("DM from %s: %s", message.author, message.content)
        if message.author.id == 309480972707954688:
            await message.channel.send("Hey, babe, what's up? :smirk:")
        if "help" in message.content:
            await BOT.get_command("help").invoke(ctx)
        elif "lmao" in message.content or "lmfao" in message.content:
            await replace_ass()
        else:
            await BOT.get_command("info").invoke(ctx)
        lbvars.set_last_use_time(time.time())
        return

        # If used by bot's creator, displays last time a lmao-bot command was used
    if perms.is_lmao_developer(ctx.message) and message.content.lower().strip() == "last command used":
        current_time = time.time()
        await message.channel.send(f"The last command was used {lbutil.eng_time(current_time - lbvars.get_last_use_time())} ago.")

    # COMMANDS
    if starts_with_prefix(message): # Bot reacts to command prefix call
        if message.content.startswith(BOT.user.mention):
            prefix = BOT.user.mention
        else:
            prefix = lbvars.get_prefix(guild_id)
        msg_no_prefix = message.content[len(prefix):].strip()
        words = msg_no_prefix.split()
        cmd_name = ""
        if len(words) > 0:
            cmd_name = words[0]

        # lbvars.import_settings()

        if cmd_name.lower() in get_all_commands():
            await BOT.process_commands(message)
        else:
            try:
                await message.channel.send(perms.clean_everyone(ctx, lbvars.get_custom_cmd_list(message.guild.id)[cmd_name].strip()))
            except KeyError:
                if "lmao" in message.content.lower() or "lmfao" in message.content.lower():
                    await replace_ass()

        if not lbvars.get_no_command_invoked():
            lbvars.set_last_use_time(time.time())
        lbvars.set_no_command_invoked(False)

        lbvars.export_settings(guild_id)

    elif msg == "lmao help":
        await message.channel.send(f"Type `{prefix} help` to see the help menu.")
    elif msg == "lmao prefix":
        await message.channel.send(f"My command prefix for {message.guild.name} is currently `{prefix}`.")

    # GENERIC REPLY
    elif ("lmao" in msg or "lmfao" in msg): #generic ass substitution
        await replace_ass()
        lbvars.export_settings(guild_id)

    #FILTERS
    else:
        filters = lbvars.get_filter_list(guild_id)
        for key, value in filters.items():
            flags = value["flags"]
            if "chance" in flags:
                chance = lbutil.parse_chance(flags)
                x = random.randint(1, 100)
                if x > chance:
                    continue
            needle = key.lower()
            haystack = ctx.message.content.lower()
            if "casesensitive" in flags:
                needle = key
                haystack = ctx.message.content
            if "wholeword" in flags:
                haystack = haystack.split()
            contains_key = needle in haystack
            if contains_key:
                mention = f"{message.author.mention} "
                if "nomention" in flags:
                    mention = ""
                await ctx.send(perms.clean_everyone(ctx, f"{mention}{value['message']}"))
        lbvars.export_settings(guild_id)

    if guild_id in ["345655060740440064", "407274897350328345"] and ("pollard" in msg or "buh-bye" in msg or "buhbye" in msg or "buh bye" in msg):
        emoji_list = BOT.get_guild(345655060740440064).emojis
        for emoji in emoji_list:
            if emoji.name == "buhbye":
                buhbye = emoji
        try:
            await message.add_reaction(buhbye)
        except UnboundLocalError:
            pass
        except discord.errors.Forbidden:
            pass

BOT.run(bot_token)