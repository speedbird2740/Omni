import json
import random
import re
import threading
from asyncio import sleep

import discord
import requests
from bs4 import BeautifulSoup as bs
from discord.ext import commands
from profanity_check import predict_prob

from files.backend.config_framework import listener, createconfig, loadconfig, saveconfig, gethash
from files.backend.webrequests import getdata

botdata = {}
slapgifs = []
fightgifs = []


class fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(description="Slap a user")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def slap(self, ctx, user: discord.Member):
        gif = slapgifs[random.randint(random.randint(0, len(slapgifs) - 2), len(slapgifs) - 1)]

        try:
            idhash = gethash(user.id)

            if idhash not in botdata["slapcount"]:
                saveconfig({
                    "slapcount.append": [idhash, 1]
                })
                await sleep(1)
            else:
                saveconfig({
                    "slapcount.add": [idhash, 1]
                })
        except:
            embed = discord.Embed(title="Slap")
            embed.set_thumbnail(url=gif)
            embed.add_field(name="Usage", value="```./slap @user```")

            await ctx.send(embed)
            return

        if not ctx.author.id == user.id:
            message = discord.Embed(title=f"{ctx.author.display_name} slaps {user.display_name}!",
                                    color=discord.Colour.dark_blue()).set_footer(
                text=f"This is {user.display_name}'s slap #{botdata['slapcount'][idhash]}!")
        else:
            message = discord.Embed(title=f"{ctx.author.display_name} slaps themselves!",
                                    color=discord.Colour.dark_blue()).set_footer(
                text=f"This is {user.display_name}'s slap #{botdata['slapcount'][idhash]}!")

        await ctx.send(embed=message.set_image(url=gif))

    @commands.command(description="Fight a user")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def fight(self, ctx, user: discord.Member):
        gif = fightgifs[random.randint(random.randint(0, len(fightgifs) - 2), len(fightgifs) - 1)]

        try:
            idhash = gethash(user.id)

            if not idhash in botdata["fightcount"]:
                saveconfig({
                    "fightcount.append": [idhash, 1]
                })
                await sleep(1)
            else:
                saveconfig({
                    "fightcount.add": [idhash, 1]
                })
        except Exception:
            embed = discord.Embed(title="Fight")
            embed.set_thumbnail(url=gif)
            embed.add_field(name="Usage", value="```./fight @valid_user```")

            await ctx.send(embed)
            return

        if not ctx.author.id == user.id:
            message = discord.Embed(title=f"{ctx.author.display_name} fights {user.display_name}!",
                                    color=discord.Colour.dark_blue()).set_footer(
                text=f"This is {user.name}'s fight #{botdata['fightcount'][idhash]}!")
        else:
            message = discord.Embed(title=f"{ctx.author.display_name} fights themselves!",
                                    color=discord.Colour.dark_blue()).set_footer(
                text=f"This is {user.name}'s fight #{botdata['fightcount'][idhash]}!")
        await ctx.send(embed=message.set_image(url=gif))

    @commands.command(description="Rate a anything an x/10")
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def rate(self, ctx):
        if len(ctx.message.content.split(" ")) > 1:
            item = ctx.message.content.replace("./rate ", "")
            itemhash = gethash(item)

            if itemhash in botdata["ratings"]:
                rating = botdata["ratings"][itemhash]
            else:
                ratingrange = [i for i in range(10)]
                rating = random.randint(random.randint(0, len(ratingrange) - 2), len(ratingrange) - 1)

                saveconfig({
                    "ratings.append": [itemhash, rating]
                })

            if predict_prob([item])[0] > 0.80:
                raise commands.errors.BadArgument(
                    "Your item has been flagged by my profanity module. Please try again.")

            await ctx.send(
                embed=discord.Embed(description=f"I rate {item} a {rating}/10!", color=discord.Colour.dark_blue()))
        else:
            embed = discord.Embed(title="Ratings", color=discord.Colour.dark_blue())
            embed.add_field(name="Usage", value="```./rate <item>```")
            await ctx.send(embed=embed)

    @commands.command(description="Dad jokes!")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def dadjoke(self, ctx):
        data = bs(requests.get("https://icanhazdadjoke.com/").text, "html.parser")
        data = str(data.select("p")[0])
        joke = re.findall('class="subtitle">.*</p>$', data)[0].replace('class="subtitle">', '').replace('</p>', '')

        await ctx.send(embed=discord.Embed(description=joke, color=discord.Colour.dark_blue()))

    @commands.command(description="Get general information about a country")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def country(self, ctx, value=None):
        query = ctx.message.content.replace("./country ", "")

        if value:
            data = json.loads(requests.get(f"https://restcountries.eu/rest/v2/name/{query}", timeout=4).text)

            country = data[0]
            embed = discord.Embed(title=country["name"], color=discord.Colour.dark_blue())
            timezones = ""
            currencies = ""
            languages = ""

            for timezone in country["timezones"]:
                timezones += f"{timezone}\n"

            for currency in country["currencies"]:
                name = currency["name"]
                code = currency["code"]
                symbol = currency["symbol"]
                currencies += f"{name} ({code}, {symbol})\n"

            for lang in country["languages"]:
                name = lang["name"]
                languages += f"{name}\n"

            embed.add_field(name="Capital", value=country["capital"])
            embed.add_field(name="Region/subregion", value=country["region"] + "/" + country["subregion"])
            embed.add_field(name="Population", value=country["population"])
            embed.add_field(name="Time zones", value=timezones)
            embed.add_field(name="Currencies", value=currencies)
            embed.add_field(name="Languages", value=languages)

        else:
            embed = discord.Embed(title="Country lookup", color=discord.Colour.dark_blue())
            embed.add_field(name="Usage", value="```./country <country>```")

        await ctx.send(embed=embed)


def syncdata():
    global botdata
    global slapgifs
    global fightgifs

    slapgifs, fightgifs, facts, nasalinks = getdata()

    global botdata

    host = listener(port=2)

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

    bot.add_cog(fun(bot))
    botdata = loadconfig()
    threading.Thread(target=syncdata).start()
