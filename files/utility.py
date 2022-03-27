import json
import random
import threading
from asyncio import sleep

import discord
import requests
from better_profanity import profanity
from discord.ext import commands
from discord.ext.commands import HelpCommand as dhelp
from discord.ext.commands import has_permissions

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
                raise commands.errors.MissingPermissions(missing_perms=["manage_messages"])

        elif len(args) == 1:
            afkmsg = "afk"
            memberidhash = gethash(ctx.author.id)
            saveconfig({
                "afkmembers.append": [memberidhash, afkmsg]
            })

            await ctx.send(f"I've set your afk: {afkmsg}")

    @commands.command(description="Send an announcement in an embed")
    @has_permissions(mention_everyone=True)
    @commands.cooldown(2, 60, commands.BucketType.user)
    async def announce(self, ctx):
        content = ctx.message.content
        args = ctx.message.content.split("--")
        del args[0]

        if len(args) > 1 and "--t" in content and "--d" in content:
            for arg in args:
                if arg.startswith("t "):
                    arg = list(arg)
                    del arg[0]
                    del arg[0]

                    title = "".join(arg)
                elif arg.startswith("d "):
                    arg = list(arg)
                    del arg[0]
                    del arg[0]

                    description = "".join(arg)
                else:
                    raise commands.errors.BadArgument("Invalid parameters.")

            if title and description:
                if len(title) >= 256:
                    raise commands.errors.BadArgument(message="Title must be less than 256 characters.")
                elif len(description) >= 2048:
                    raise commands.errors.BadArgument(message="Description must be less than 2048 characters.")

                resp = await ctx.send("**This will ping everyone.** Are you sure you want to continue? (y/n)")

                def check(message: discord.Message):
                    if message.author.id == ctx.author.id:
                        return True
                    else:
                        return False

                confirmation = await self.bot.wait_for(event="message", check=check, timeout=10)

                if confirmation.content.lower() == "y":
                    await resp.delete()
                    await confirmation.delete()
                else:
                    await ctx.send("Announcement cancelled.")
                    return

                await ctx.message.delete()
                await ctx.send(ctx.message.guild.default_role, embed=discord.Embed(title=title, description=description,
                                                                                   color=discord.Colour.dark_blue()))
        else:
            embed = discord.Embed(title="Announcements", color=discord.Colour.dark_blue())
            embed.add_field(name="Usage",
                            value="Use `--t <title>` to set the title. Use `--d <description>` to set the description."
                                  "```./announce --t I figured it out! --d I figured out how to use this command!```")
            await ctx.send(embed=embed)

    @commands.command(description="Get positive affirmations to help you get through your day")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def affirmation(self, ctx):
        affirmation = json.loads(requests.get("https://www.affirmations.dev/").text)["affirmation"]
        await ctx.send(embed=discord.Embed(description=affirmation, color=discord.Colour.dark_blue()))


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


async def setup(bot: commands.Bot):
    global botdata
    global credentials

    await bot.add_cog(utility(bot))
    botdata = loadconfig()
    credentials = json.load(open("data/credentials.json"))
    threading.Thread(target=syncdata).start()

