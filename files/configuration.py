import json
import threading

import discord
from discord.ext import commands

from files.backend.config_framework import listener, loadconfig, saveconfig, gethash, processdeltas

botdata = {}
credentials = {}


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
                if guildconfig["botenabled"]:
                    botstatus = "Yes"
                else:
                    botstatus = "No"

                if guildconfig["someoneping"]:
                    pingstatus = "Yes"
                else:
                    pingstatus = "No"

                if guildconfig["greetings"]:
                    replystatus = "Yes"
                else:
                    replystatus = "No"

                if guildconfig["filterprofanity"]:
                    profanityfilter = "Yes"
                else:
                    profanityfilter = "No"

                if guildconfig["deleteprofanity"]:
                    deleteprofanity = "Yes"
                else:
                    deleteprofanity = "No"

                if guildconfig["log_channel"] is None:
                    log_channel = "Guild System Channel"
                else:
                    log_channel = self.bot.get_channel(guildconfig["log_channel"]).mention

                embed = discord.Embed(title="General configuration", color=discord.Colour.dark_blue())
                embed.add_field(name="Bot enabled", value=botstatus)
                embed.add_field(name="@someone enabled", value=pingstatus)
                embed.add_field(name="Greetings enabled", value=replystatus)
                embed.add_field(name="Profanity filter enabled", value=profanityfilter)
                embed.add_field(name="Delete profanity", value=deleteprofanity)
                embed.add_field(name="Bot messages channel", value=log_channel)

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

                    elif setting == "logchannel":
                        if value == "default":
                            saveconfig({
                                f"guild.{hash}.config.log_channel": None
                            })

                            await ctx.send("Bot messages channel set to guild system channel!")
                        else:
                            channel = await commands.TextChannelConverter().convert(ctx, value)

                            saveconfig({
                                f"guild.{hash}.config.log_channel": channel.id
                            })

                            await ctx.send(f"Bot messages channel set to {channel.mention}!")

                else:
                    raise commands.errors.MissingPermissions(missing_perms=["manage messages"])

        else:
            embed = discord.Embed(title="Configuration", color=discord.Colour.dark_blue()).set_footer(
                text=f"You can also bind or unbind afk messages using {credentials['prefix']}afk bind/unbind")
            embed.add_field(name="Enable or disable me", value=f"```{credentials['prefix']}config bot enable/disable```", inline=False)
            embed.add_field(name="Enable or disable @someone",
                            value=f"```{credentials['prefix']}config someoneping enable/disable```", inline=False)
            embed.add_field(name="Enable or disable greetings",
                            value=f"```{credentials['prefix']}config greetings enable/disable```", inline=False)
            embed.add_field(name="Enable or disable profanity filter",
                            value=f"```{credentials['prefix']}config filterprofanity enable/disable```", inline=False)
            embed.add_field(name="Enable or disable automatic deletion of profanity",
                            value=f"```{credentials['prefix']}config deleteprofanity enable/disable```", inline=False)
            embed.add_field(name="Set bot messages channel",
                            value=f"```{credentials['prefix']}config logchannel <channel mention>```To set it to the guild system channel, use"
                                  f"```{credentials['prefix']}config logchannel default```")
            embed.add_field(name="Show general configuration",
                            value=f"```{credentials['prefix']}config show```")
            await ctx.send(embed=embed)


def syncdata():
    global botdata

    host = listener(port=2002)

    while True:
        try:
            conn = host.accept()
            data = conn.recv()

            if data == "close":
                host.close()
                break

            botdata = processdeltas(deltas=data, config=botdata)
        except:
            pass


def setup(bot: commands.Bot):
    global botdata
    global credentials

    bot.add_cog(configuration(bot))
    credentials = json.load(open("data/credentials.json"))
    botdata = loadconfig()
    threading.Thread(target=syncdata).start()
