import json
import os
import subprocess
import sys
import threading
import time
import traceback
import zipfile
from asyncio import sleep

import discord
import psutil
import requests
from cryptography.fernet import Fernet
from discord.ext import commands

from files.backend.config_framework import listener, saveconfig, createconfig, gethash, loadconfig
from files.backend.webrequests import getdata

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='./', intents=intents, help_command=None)
bot.owner_id = "OWNER_ID"
pingcooldown = []

version = "12a1"
api_key_dev = "APIKEY"
api_key_stable = "APIKEY"
updatesuccess = True


def backgroundtasks(pid: int):
    count = 0

    while psutil.pid_exists(pid):
        bot.loop.create_task(bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.playing, name=f"v{version} | ./changelog"),
            status=discord.Status.idle))
        time.sleep(28800 if count < 1 else 60)
        bot.loop.create_task(bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.playing, name="DM to contact staff"),
            status=discord.Status.idle))

        count += 1
        time.sleep(60)


def syncdata():
    global botdata

    host = listener(port=7)

    while True:
        try:
            conn = host.accept()
            data = conn.recv()

            if data == "close":
                host.close()
                break

            for key in data.keys():
                token = key.split(".")
                value = data[key]

                if token[0] == "guild":
                    guildidhash = token[1]

                    if token[2] == "config":
                        guildconfig = botdata[guildidhash]["config"]
                        setting = token[3]

                        if not setting == "antiraid":
                            if type(guildconfig[setting]) == list:
                                action = token[4]

                                if action == "append":
                                    guildconfig[setting].append(value)

                                elif action == "remove":
                                    guildconfig[setting].remove(value)
                            else:
                                assert setting in guildconfig

                                guildconfig[setting] = value

                        elif setting == "antiraid":
                            raidconfig = guildconfig["antiraid"]
                            setting = token[4]

                            if type(raidconfig[setting]) == dict:
                                action = token[5]

                                if action == "append":
                                    name = value[0]
                                    config = value[1]

                                    raidconfig[setting][name] = config
                                elif action == "remove":
                                    name = value[0]

                                    del raidconfig[setting][name]

                                elif action == "reset":
                                    raidconfig[setting] = {}

                            elif type(raidconfig[setting]) == list and not setting == "rate":
                                action = token[5]

                                if action == "append":
                                    raidconfig[setting].append(value)

                                elif action == "remove":
                                    raidconfig[setting].remove(value)

                                elif action == "reset":
                                    raidconfig[setting] = []

                            elif type(raidconfig[setting]) == int:
                                action = token[5]

                                if action == "add":
                                    raidconfig[setting] += 1
                                elif action == "reset":
                                    raidconfig[setting] = 0

                            else:
                                assert setting in raidconfig

                                raidconfig[setting] = value

                    elif token[2] == "createconfig":
                        botdata[guildidhash] = createconfig("server")

                elif token[0] == "createconfig":
                    newconfig = createconfig("other")

                    for key in newconfig.keys():
                        botdata[key] = newconfig[key]

                elif type(botdata[token[0]]) == dict:
                    setting = token[0]
                    try:
                        action = token[1]
                    except:
                        action = None

                    if action == "append":
                        name = value[0]
                        config = value[1]

                        botdata[setting][name] = config
                    elif action == "remove":
                        name = value[0]

                        del botdata[setting][name]
                    elif action == "add":
                        name = value[0]
                        config = value[1]

                        botdata[setting][name] += config
                    else:
                        name = value[0]
                        config = value[1]

                        botdata[setting][name] = config

                elif type(botdata[token[0]]) == list:
                    setting = token[0]
                    try:
                        action = token[1]
                    except:
                        action = None

                    if action == "append":
                        botdata[setting].append(value)

                    elif action == "remove":
                        botdata[setting].remove(value)

                    else:
                        botdata[setting] = value

                elif type(botdata[token[0]]) == int:
                    setting = token[0]
                    action = token[1]

                    if action == "add":
                        botdata[setting] += 1
        except:
            traceback.print_exc()


@bot.event
async def on_ready():
    global botdata
    global updatesuccess

    print("Bot online")

    while len(botdata["log"]) > 10:
        del botdata["log"][0]

    if os.path.exists("bot log.txt"):
        try:
            val = open("bot log.txt", "r").read()
            await bot.get_channel(int(val)).send("Successfully restarted!")

            open("bot log.txt", "w").truncate()
        except:
            pass

    if os.path.exists("data/isupdate.json"):
        try:
            update = json.load(open("data/isupdate.json", "r"))
            open("data/isupdate.json", "w").truncate()

            if update:
                json.dump(True, open("data/updatesuccess.json", "w"))
                updatesuccess = True
        except:
            pass

        for id in botdata["modmailexempt"]:
            try:
                saveconfig({
                    "modmailexempt.remove": id
                })
            except:
                pass

        for id in botdata["pingcooldown"]:
            try:
                saveconfig({
                    "pingcooldown.remove": id
                })
            except:
                pass

        pid = os.getpid()
        threading.Thread(target=backgroundtasks, args=(pid,)).start()

@bot.event
async def on_message(msg):
    try:
        uidhash = gethash(msg.author.id)

        if msg.guild and uidhash not in botdata["blacklist"]:
            guildidhash = gethash(msg.guild.id)
            guildconfig = botdata[guildidhash]["config"]
            globalconfig = botdata["global"]

            if guildconfig["botenabled"] and globalconfig["botenabled"]:
                await bot.process_commands(msg)
    except Exception as error:
        if not type(error) == KeyError:
            channel = bot.get_channel("ERROR_CHANNEL")
            error = "".join(traceback.format_exception(type(error), error, error.__traceback__))
            await channel.send(f"```python\n{error}```")

            botdata[gethash(msg.guild.id)] = createconfig("server")


class restricted(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def admin(self, ctx, module, value=None):
        global botdata

        if ctx.author.id == bot.owner_id:
            if module == "bot":
                if value == "disable":
                    saveconfig({
                        "global": ["botenabled", False]
                    })
                    await self.bot.change_presence(status=discord.Status.do_not_disturb)
                    await ctx.send("Bot disabled globally!")
                elif value == "enable":
                    saveconfig({
                        "global": ["botenabled", True]
                    })
                    await self.bot.change_presence(status=discord.Status.idle,
                                                   activity=discord.Activity(type=discord.ActivityType.playing,
                                                                             name=f"v{version} | ./changelog"))
                    await ctx.send("Bot enabled globally!")
                elif value == "restart":
                    open("bot log.txt", "w").write(str(ctx.channel.id))

                    await ctx.send("Restarting...")

                    subprocess.Popen(["python", "main.py"])
                    saveconfig("close")
                    await sleep(5)
                    sys.exit()

            elif module == "someoneping":
                if value == "disable":
                    saveconfig({
                        "global": ["someoneping", False]
                    })
                    await ctx.send("@someone ping disabled globally!")
                elif value == "enable":
                    saveconfig({
                        "global": ["somepneping", True]
                    })
                    await ctx.send("@someone ping enabled globally!")

            elif module == "greetings":
                if value == "disable":
                    saveconfig({
                        "global": ["greetings", False]
                    })
                    await ctx.send("Greetings disabled globally!")
                elif value == "enable":
                    saveconfig({
                        "global": ["greetings", True]
                    })
                    await ctx.send("Greetings enabled globally!")

            elif module == "blacklist":  # This is broken
                args = ctx.message.content.split(" ")
                if not value == "reset":
                    blacklist = botdata["blacklist"]
                    id = args[-1]
                    idhash = gethash(args[-1])

                if value == "add":
                    botdata["blacklist"].append(idhash)
                    await ctx.send(
                        embed=discord.Embed(description=f"Added <@!{id}> to the blacklist. They cannot use the bot now",
                                            color=discord.Colour.dark_blue()))
                elif value == "remove":
                    botdata["blacklist"].remove(idhash)
                    await ctx.send(embed=discord.Embed(
                        description=f"Removed <@!{id}> from the blacklist. They can use the bot now",
                        color=discord.Colour.dark_blue()))
                elif value == "reset":
                    botdata["blacklist"].clear()
                    await ctx.send("Successfully cleared blacklist!")

            elif module == "afk":
                if value == "reset":
                    botdata["afkmembers"].clear()
                    await ctx.send("Successfully cleared afk list!")

            elif module == "settings":
                if value == "reset":
                    saveconfig({
                        "createconfig": None
                    })
                    await sleep(0.5)

                    for guild in self.bot.guilds:
                        guildidhash = gethash(guild.id)
                        saveconfig({
                            f"guild.{guildidhash}.createconfig": None
                        })

                    await ctx.send("Successfully reset all settings!")

                    await self.bot.change_presence(status=discord.Status.idle,
                                              activity=discord.Activity(type=discord.ActivityType.watching,
                                                                        name="settings have been reset"))
                    await sleep(3600)
                    await self.bot.change_presence(status=discord.Status.idle,
                                              activity=discord.Activity(type=discord.ActivityType.playing,
                                                                        name=f"v{version} | ./changelog"))

            elif module == "analytics":  # This is a retired function
                commandcount = botdata["commandscount"]
                errors = ""
                log = ""

                while len(botdata["log"]) > 15:
                    del botdata["log"][0]

                while len(botdata["errors"]) > 5:
                    del botdata["errors"][0]

                for error in botdata["errors"]:
                    errors += f"{error}\n"

                for event in botdata["log"]:
                    log += f"`{event}`\n"

                embed = discord.Embed(title="Analytics", color=discord.Colour.dark_blue())
                embed.add_field(name="Commands executed", value=commandcount)
                embed.add_field(name="Log", value=log, inline=False)
                embed.add_field(name="Errors", value=errors, inline=False)

                await ctx.send(embed=embed)

            elif module == "exec":
                code = ctx.message.content.replace("./admin exec ```py\n", "").replace("```", "")
                exec(code)
        else:
            await ctx.send(embed=discord.Embed(
                description="Only the developer behind this bot can use this command."
                            " If you are a server admin or moderator, make sure you have the manage messages"
                            " permission and use `./config` instead"))

    @commands.command()
    async def update(self, ctx):
        if ctx.author.id == bot.owner_id:
            args = ctx.message.content.split(" ")
            restart = False
            updatedcogs = []

            if len(args) > 1:
                if args[-1] == "generatekey":

                    key = Fernet.generate_key()
                    open("update.key", "wb").write(key)

                    file = discord.File("update.key")

                    await ctx.message.add_reaction("✅")
                    await self.bot.get_user(bot.owner_id).send("Here is your encryption key", file=file)

                elif args[-1] == "new":
                    embed = discord.Embed(title="Updating...",
                                          description="**Unpack update - 🔃\n"
                                                      "Run setup - ⏳\n"
                                                      "Install update - ⏳\n"
                                                      "Reload/restart - ⏳\n"
                                                      "Verification - ⏳**")
                    msg = await ctx.send(embed = embed)

                    url = ctx.message.attachments[0].url
                    update = bytes(requests.get(url).text, "utf-8")
                    key = open("update.key", "rb").read()
                    update = Fernet(key).decrypt(update)

                    if not os.path.exists("temp/"):
                        os.mkdir("temp/")

                    open("temp/update.temp", "wb").write(update)

                    with zipfile.ZipFile("temp/update.temp", "r") as pack:
                        files = pack.namelist()

                        if "setup.py" in files:
                            embed = discord.Embed(title="Updating...",
                                                  description="**Unpack update - ✅\n"
                                                              "Run setup - 🔃\n"
                                                              "Install update - ⏳\n"
                                                              "Reload/restart - ⏳\n"
                                                              "Verification - ⏳**")
                            await msg.edit(embed=embed)

                            with pack.open("setup.py") as setup:
                                update = setup.read()
                                open("temp/setup.py", "wb").write(update)
                                p = subprocess.Popen(["python", "temp/setup.py"], stdout=subprocess.PIPE)
                                result = p.wait(timeout=10)
                                time.sleep(0.5)

                                if result == 0:
                                    pass
                                else:
                                    await ctx.send(
                                        f"WARNING: Setup finished with exit code {result}"
                                        f"```fix\n{p.communicate()[0]}```Continue?")

                                    def check(msg):
                                        if msg.author.id == bot.owner_id:
                                            return True
                                        else:
                                            return False

                                    resp = await self.bot.wait_for(event="message", check=check, timeout=20)

                                    if resp.content.lower() == "yes":
                                        pass
                                    else:
                                        await ctx.send("Aborted")

                                        setup.close()
                                        pack.close()
                                        return

                        embed = discord.Embed(title="Updating...",
                                              description="**Unpack update - ✅\n"
                                                          "Run setup - ✅\n"
                                                          "Install update - 🔃\n"
                                                          "Reload/restart - ⏳\n"
                                                          "Verification - ⏳**")
                        await msg.edit(embed=embed)

                        for file in files:
                            with pack.open(file) as update:
                                modified = gethash(update.read()) != gethash(open(file, "rb").read())
                                if not file == "main.py" and not file == "setup.py":
                                    notcog = ("webrequests.py", "config_framework.py", "misc.py")

                                    if not any(file.endswith(name) for name in notcog) and modified:
                                        updatedcogs.append(file)
                                    elif modified:
                                        restart = True
                                        open(f"backup/{file}", "wb").write(open(file, "rb").read())
                                        open(file, "wb").write(update.read())

                                elif file == "main.py" and modified:
                                    restart = True
                                    open("backup/main.py", "wb").write(open("main.py", "rb").read())

                                    open("main.py", "wb").write(pack.open(file).read())

                        pack.close()

                    if restart:
                        saveconfig("close")
                        await sleep(5)

                        json.dump(False, open("data/updatesuccess.json", "w"))
                        json.dump(True, open("data/isupdate.json", "w"))

                        embed = discord.Embed(title="Updating...",
                                              description="**Unpack update - ✅\n"
                                                          "Run setup - ✅\n"
                                                          "Install update - ✅\n"
                                                          "Restart - 🔃\n"
                                                          "Verification - ⏳**")
                        await msg.edit(embed=embed)

                        p = subprocess.Popen(["python", "main.py"])

                        time.sleep(2)

                        embed = discord.Embed(title="Updating...",
                                              description="**Unpack update - ✅\n"
                                                          "Run setup - ✅\n"
                                                          "Install update - ✅\n"
                                                          "Restart - ✅\n"
                                                          "Verification - 🔃**")
                        await msg.edit(embed=embed)

                        for i in range(10):
                            try:
                                updatesuccess = json.load(open("data/updatesuccess.json", "r"))

                                if updatesuccess:
                                    time.sleep(1)
                                    break
                            except:
                                updatesuccess = False
                            time.sleep(1)

                        if updatesuccess:
                            embed = discord.Embed(title="Update successful",
                                                  description="**Unpack update - ✅\n"
                                                              "Run setup - ✅\n"
                                                              "Install update - ✅\n"
                                                              "Restart - ✅\n"
                                                              "Verification - ✅**")
                            await msg.edit(embed=embed)
                            sys.exit()

                        else:
                            await ctx.send("Verification timed out. Rolling back...")

                            try:
                                p.terminate()
                            except:
                                pass

                            if os.path.exists("main.py"):
                                os.remove("main.py")

                            for file in os.listdir("backup/files/"):
                                if file.endswith(".py"):
                                    update = open(f"backup/files/{file}", "rb").read()
                                    open(f"files/{file}", "wb").write(update)
                                elif file == "backend":
                                    for file in os.listdir(f"backup/files/{file}"):
                                        if file.endswith(".py"):
                                            open(f"files/backend/{file}", "wb").write(
                                                open(f"backup/files/backend/{file}", "rb").read())

                            update = open("backup/main.py", "rb").read()
                            open("main.py", "wb").write(update)

                            open("bot log.txt", "w").write(str(ctx.channel.id))

                            subprocess.Popen(["python", "main.py"])

                            sys.exit()

                    else:
                        await sleep(2)
                        embed = discord.Embed(title="Updating...",
                                              description="**Unpack update - ✅\n"
                                                          "Run setup - ✅\n"
                                                          "Install update - ✅\n"
                                                          "Reload - 🔃\n"
                                                          "Verification - not applicable**")
                        await msg.edit(embed=embed)

                        for file in updatedcogs:
                            bot.reload_extension(file)
                            await sleep(1)

                        embed = discord.Embed(title="Update successful",
                                              description="**Unpack update - ✅\n"
                                                          "Run setup - ✅\n"
                                                          "Install update - ✅\n"
                                                          "Reload - ✅\n"
                                                          "Verification - not applicable**")
                        await msg.edit(embed=embed)

                elif args[-1] == "rollback":
                    await ctx.send("Rolling back...")

                    if os.path.exists("main.py"):
                        os.remove("main.py")

                    for file in os.listdir("backup/files/"):
                        if file.endswith(".py"):
                            update = open(f"backup/files/{file}", "rb").read()
                            open(f"files/{file}", "wb").write(update)
                        elif file == "backend":
                            for file in os.listdir(f"backup/files/{file}"):
                                if file.endswith(".py"):
                                    open(f"files/backend/{file}", "wb").write(
                                        open(f"backup/files/backend/{file}", "rb").read())

                    update = open("backup/main.py", "rb").read()
                    open("main.py", "wb").write(update)

                    open("bot log.txt", "w").write(str(ctx.channel.id))

                    saveconfig("close")
                    await sleep(5)
                    subprocess.Popen(["python", "main.py"])
                    sys.exit()


if __name__ == "__main__":
    bot.add_cog(restricted(bot))
    bot.load_extension("files.backend.events")
    bot.load_extension("files.configuration")
    bot.load_extension("files.moderation")
    bot.load_extension("files.fun")
    bot.load_extension("files.space")
    bot.load_extension("files.utility")
    bot.load_extension("files.miscellaneous")
    threading.Thread(target=syncdata).start()

    botdata = loadconfig()
    bot.run(api_key_stable)
