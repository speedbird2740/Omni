import threading

import discord
from discord.ext import commands

from files.backend.config_framework import listener, createconfig, loadconfig, saveconfig, gethash

botdata = {}


class configuration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(description="Edit general configuration for this server")
    @commands.cooldown(1, 4, commands.BucketType.guild)
    async def config(self, ctx):
        args = ctx.message.content.split(" ")

        if len(args) > 1:
            setting = args[1]
            hash = gethash(ctx.guild.id)
            guildconfig = botdata[hash]["config"]

            if setting == "show":
                if not guildconfig["botenabled"]:
                    botstatus = "No"
                else:
                    botstatus = "Yes"

                if not guildconfig["someoneping"]:
                    pingstatus = "No"
                else:
                    pingstatus = "Yes"

                if not guildconfig["greetings"]:
                    replystatus = "No"
                else:
                    replystatus = "Yes"

                if guildconfig["filterprofanity"]:
                    profanityfilter = "Yes"
                else:
                    profanityfilter = "No"

                if guildconfig["deleteprofanity"]:
                    deleteprofanity = "Yes"
                else:
                    deleteprofanity = "No"

                embed = discord.Embed(title="General configuration", color=discord.Colour.dark_blue())
                embed.add_field(name="Bot enabled", value=botstatus)
                embed.add_field(name="@someone enabled", value=pingstatus)
                embed.add_field(name="Greetings enabled", value=replystatus)
                embed.add_field(name="Profanity filter enabled", value=profanityfilter)
                embed.add_field(name="Delete profanity", value=deleteprofanity)

                await ctx.send(embed=embed)

            else:
                if ctx.author.guild_permissions.manage_messages:
                    value = args[2]

                    if setting == "someoneping":
                        if value == "disable":
                            saveconfig({
                                f"guild.{hash}.config.someoneping": False
                            })
                            await ctx.send("@someone ping disabled for this server!")
                        elif value == "enable":
                            saveconfig({
                                f"guild.{hash}.config.someoneping": True
                            })
                            await ctx.send("@someone ping enabled for this server!")

                    elif setting == "bot":
                        if value == "disable":
                            saveconfig({
                                f"guild.{hash}.config.botenabled": False
                            })
                            await ctx.send("Bot disabled for this server!")
                        elif value == "enable":
                            saveconfig({
                                f"guild.{hash}.config.botenabled": True
                            })
                            await ctx.send("Bot enabled for this server!")

                    elif setting == "greetings":
                        if value == "disable":
                            saveconfig({
                                f"guild.{hash}.config.greetings": False
                            })
                            await ctx.send("Greetings disabled for this server!")
                        elif value == "enable":
                            saveconfig({
                                f"guild.{hash}.config.greetings": True
                            })
                            await ctx.send("Greetings enabled for this server!")

                    elif setting == "filterprofanity":
                        if value == "disable":
                            saveconfig({
                                f"guild.{hash}.config.filterprofanity": False
                            })
                            await ctx.send("Profanity filter disabled for this server!")
                        elif value == "enable":
                            saveconfig({
                                f"guild.{hash}.config.filterprofanity": True
                            })
                            await ctx.send("Profanity filter enabled for this server!")

                    elif setting == "deleteprofanity":
                        if value == "disable":
                            saveconfig({
                                f"guild.{hash}.config.deleteprofanity": False
                            })
                            await ctx.send("Automatic deletion of profanity disabled for this server!")
                        elif value == "enable":
                            saveconfig({
                                f"guild.{hash}.config.deleteprofanity": True
                            })
                            await ctx.send("Automatic deletion of profanity enabled for this server!")
                else:
                    raise commands.errors.MissingPermissions(missing_perms=["manage messages"])

        else:
            embed = discord.Embed(title="Configuration", color=discord.Colour.dark_blue()).set_footer(
                text="You can also bind or unbind afk messages using ./afk bind/unbind")
            embed.add_field(name="Enable or disable me", value="```./config bot enable/disable```", inline=False)
            embed.add_field(name="Enable or disable @someone",
                            value="```./config someoneping enable/disable```", inline=False)
            embed.add_field(name="Enable or disable greetings",
                            value="```./config greetings enable/disable```", inline=False)
            embed.add_field(name="Enable or disable profanity filter",
                            value="```./config filterprofanity enable/disable```", inline=False)
            embed.add_field(name="Enable or disable automatic deletion of profanity",
                            value="```./config deleteprofanity enable/disable```", inline=False)
            embed.add_field(name="Show general configuration",
                            value="```./config show```")
            await ctx.send(embed=embed)


def syncdata():
    global botdata

    host = listener(port=1)

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
            pass


def setup(bot: commands.Bot):
    global botdata

    bot.add_cog(configuration(bot))
    botdata = loadconfig()
    threading.Thread(target=syncdata).start()
