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
import requests
from cryptography.fernet import Fernet
from discord.ext import commands


credentials = json.load(open("data/credentials.json"))


intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix=credentials["prefix"], intents=intents, help_command=None)

bot.owner_id = credentials["owner_id"]
api_key = credentials["api_key"]

version = "12.2"
pingcooldown = []
updatesuccess = True


def backgroundtasks():
    count = 0

    while True:
        bot.loop.create_task(bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.playing, name=f"v{version} | {credentials['prefix']}changelog"),
            status=discord.Status.idle))
        time.sleep(28800 if count < 1 else 60)
        bot.loop.create_task(bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.playing, name="DM to contact staff"),
            status=discord.Status.idle))

        count += 1
        time.sleep(60)


def syncdata():
    global botdata

    host = listener(port=2001)

    while True:
        try:
            conn = host.accept()
            data = conn.recv()

            if data == "close":
                host.close()
                break

            botdata = processdeltas(deltas=data, config=botdata)
        except:
            traceback.print_exc()


@bot.event
async def on_ready():
    global botdata
    global updatesuccess

    print("Bot online")

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
            channel = bot.get_channel(credentials["log_channel"])
            error = "".join(traceback.format_exception(type(error), error, error.__traceback__))
            await channel.send(f"```python\n{error}```")


class restricted(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def admin(self, ctx, module, value=None):
        global botdata

        if ctx.author.id == credentials["owner_id"]:
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
                    await ctx.send("Bot enabled globally!")
                elif value == "restart":
                    open("bot log.txt", "w").write(str(ctx.channel.id))

                    await ctx.send("Restarting...")

                    subprocess.Popen([sys.executable, "main.py"])
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
                        "global": ["someoneping", True]
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
                    id = args[-1]
                    idhash = gethash(args[-1])

                if value == "add":
                    saveconfig({
                        "blacklist.append": idhash
                    })
                    await ctx.send(
                        embed=discord.Embed(description=f"Added <@!{id}> to the blacklist. They cannot use the bot now",
                                            color=discord.Colour.dark_blue()))
                elif value == "remove":
                    saveconfig({
                        "blacklist.remove": idhash
                    })
                    await ctx.send(embed=discord.Embed(
                        description=f"Removed <@!{id}> from the blacklist. They can use the bot now",
                        color=discord.Colour.dark_blue()))
                elif value == "reset":
                    saveconfig({
                        "blacklist.clear": None
                    })
                    await ctx.send("Successfully cleared blacklist!")

            elif module == "afk":
                if value == "reset":
                    saveconfig({
                        "afkmembers": {}
                    })
                    await ctx.send("Successfully cleared afk list!")

            elif module == "settings":
                if value == "reset":
                    msg = await ctx.send("Processing...")

                    saveconfig({
                        "createconfig": None
                    })
                    await sleep(0.5)

                    for guild in self.bot.guilds:
                        guildidhash = gethash(guild.id)
                        saveconfig({
                            f"guild.{guildidhash}.createconfig": None
                        })

                    await msg.edit("Successfully reset all settings!")

            elif module == "exec":
                code = ctx.message.content.replace(f"{credentials['prefix']}admin exec ```py\n", "").replace("```", "")
                exec(code)
        else:
            await ctx.send(embed=discord.Embed(
                description="Only the developer behind this bot can use this command."
                            " If you are a server admin or moderator, make sure you have the manage messages"
                            f" permission and use `{credentials['prefix']}config` instead", color=discord.Colour.red()))

    @commands.command()
    async def update(self, ctx):
        if ctx.author.id == credentials["owner_id"]:
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
                                p = subprocess.Popen([sys.executable, "temp/setup.py"], stdout=subprocess.PIPE)
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

                                    if modified:
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

                        p = subprocess.Popen([sys.executable, "main.py"])

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

                            subprocess.Popen([sys.executable, "main.py"])

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
                    subprocess.Popen([sys.executable, "main.py"])
                    sys.exit()


if __name__ == "__main__":
    from files.backend.config_framework import listener, saveconfig, gethash, loadconfig, processdeltas

    botdata = loadconfig()

    bot.add_cog(restricted(bot))
    bot.load_extension("files.backend.events")
    bot.load_extension("files.configuration")
    bot.load_extension("files.moderation")
    bot.load_extension("files.fun")
    bot.load_extension("files.space")
    bot.load_extension("files.utility")
    bot.load_extension("files.miscellaneous")
    threading.Thread(target=syncdata).start()

    bot.run(api_key)
