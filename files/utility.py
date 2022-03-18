import json
import random
import threading
from asyncio import sleep

import discord
import requests
from better_profanity import profanity
from discord.ext import commands
from discord.ext.commands import HelpCommand as dhelp

from files.backend.config_framework import gethash, saveconfig, loadconfig, listener, processdeltas

searchcache = {}
botdata = {}
credentials = {}


class utility(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(description="Look for images on the internet")
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def image(self, ctx):
        global searchcache

        if len(ctx.message.content.split(" ")) > 1:
            links = []
            query = ctx.message.content.replace(f"{credentials['prefix']}image ", "").replace(" ", "+")
            hash = gethash(query.lower())

            if profanity.contains_profanity(query):
                raise commands.errors.BadArgument(
                    "Your query has been flagged by my profanity module. Please try again.")

            if hash in searchcache:
                links = searchcache[hash]

                try:
                    index = random.randint(random.randint(0, len(links) - 2), len(links) - 1)
                    msg = discord.Embed(color=discord.Colour.dark_blue()).set_image(
                        url=links[index])
                    msg.set_footer(text=f"{len(links)} images (cached)")
                except:
                    msg = discord.Embed(description=":x: no pictures found", color=discord.Colour.red())

            else:
                img_srv = credentials["img_srv"]

                if img_srv["service"] == 1:
                    params = {
                        "key": img_srv["api_key"],
                        "cx": img_srv["client_cx"],
                        "q": query,
                        "searchType": "image",
                        "safe": "active"
                    }

                    data = requests.get(f"https://www.googleapis.com/customsearch/v1", params=params).json()

                    for item in data["items"]:
                        links.append(item["link"])

                elif img_srv["service"] == 2:
                    headers = {"Ocp-Apim-Subscription-Key": img_srv["api_key"]}
                    params = {
                        "q": query,
                        "safeSearch": "strict",
                        "count": "25"
                    }

                    data = requests.get(f"https://api.bing.microsoft.com/v7.0/images/search", headers=headers, params=params).json()
                    images = data["value"]

                    for image in images:
                        links.append(image["contentUrl"])

                searchcache[hash] = links

                try:
                    index = random.randint(random.randint(0, len(links) - 2), len(links) - 1)
                    msg = discord.Embed(color=discord.Colour.dark_blue()).set_image(
                        url=links[index])
                    msg.set_footer(text=f"{len(links)} images")
                except:
                    msg = discord.Embed(description=":x: no pictures found", color=discord.Colour.red())

            await ctx.send(embed=msg)
            await sleep(43200)

            if hash in searchcache:
                del searchcache[hash]
        else:
            embed = discord.Embed(title="Image lookup", color=discord.Colour.dark_blue())
            embed.add_field(name="Usage", value=f"```{credentials['prefix']}image <query>```")

            await ctx.send(embed=embed)

    @commands.command(description="Set an afk message. I will notify other users that you are afk when they ping you")
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def afk(self, ctx):
        args = ctx.message.content.split(" ")
        afkconfig = ["bind", "unbind"]

        if len(args) > 1 and not args[1] in afkconfig:
            afkmsg = ctx.message.content.replace(f"{credentials['prefix']}afk ", "")
            afkmsg = dhelp().remove_mentions(afkmsg)
            memberidhash = gethash(ctx.author.id)

            saveconfig({
                "afkmembers.append": [memberidhash, afkmsg]
            })
            await ctx.send(f"I've set your afk: {afkmsg}")

        elif len(args) > 1 and args[1] in afkconfig:
            if ctx.author.guild_permissions.manage_messages:
                hash = gethash(ctx.channel.id)
                if args[1] == "bind":
                    saveconfig({
                        f"guild.{gethash(ctx.guild.id)}config.noafkchannels.remove": hash
                    })
                    await ctx.channel.send(f"AFK messages enabled in {ctx.channel.mention}")
                elif args[1] == "unbind":
                    saveconfig({
                        f"guild.{gethash(ctx.guild.id)}.config.noafkchannels.append": hash
                    })
                    await ctx.channel.send(f"AFK messages disabled in {ctx.channel.mention}")

            else:
                await ctx.send(":x: You do not have enough permissions to use that parameter")

        elif len(args) == 1:
            afkmsg = "afk"
            memberidhash = gethash(ctx.author.id)
            saveconfig({
                "afkmembers.append": [memberidhash, afkmsg]
            })

            await ctx.send(f"I've set your afk: {afkmsg}")


def syncdata():
    global botdata

    host = listener(port=2005)

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

    bot.add_cog(utility(bot))
    botdata = loadconfig()
    credentials = json.load(open("data/credentials.json"))
    threading.Thread(target=syncdata).start()

