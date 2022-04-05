import datetime
import json
import random
import threading
import time
import traceback
from asyncio import sleep

import discord
from better_profanity import profanity
from discord.ext import commands

from files.backend.config_framework import loadconfig, saveconfig, listener, gethash, host, processdeltas

botdata = {}
credentials = {}
antiraidlog = {}
whitelist = (
    "dumb", "stupid", "idiot", "nerd", "wtf", "len", "crap", "lmao", "analy", "gae", "gay", "god", "stroke", "weed",
    "omg", "ugly")
ports = [7]
authkey = b"authkey"
pingcooldown = []


class events(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, ctx: discord.Message):
        global botdata

        try:
            if not ctx.author.bot:
                guildidhash = gethash(ctx.guild.id)
                uidhash = gethash(ctx.author.id)

                guildconfig = botdata[guildidhash]["config"]
                globalconfig = botdata["global"]

                if globalconfig["botenabled"] and guildconfig["botenabled"] and not uidhash in botdata[
                    "blacklist"]:
                    if "<@" in ctx.content and ctx.channel.id not in guildconfig["noafkchannels"] or ctx.reference:
                        memberpings = ctx.mentions
                        pings = []
                        temp = []
                        msg = ""

                        words = ctx.content.split(" ")

                        for ping in words:
                            if ping.startswith("<@"):
                                pings.append(ping)

                        for member in memberpings:
                            memberidhash = gethash(member.id)

                            if memberidhash in botdata[
                                "afkmembers"] and not memberidhash == uidhash and not memberidhash in temp:
                                temp.append(memberidhash)

                                await ctx.reply(f"{member.name} is afk: {botdata['afkmembers'][memberidhash]}")

                        for ping in pings:
                            try:
                                roleid = int(ping.replace("<@&", "").replace(">", ""))
                                role = ctx.guild.get_role(roleid)

                                for member in role.members:
                                    memberidhash = gethash(member.id)

                                    if memberidhash in botdata[
                                        "afkmembers"] and not memberidhash == uidhash and not memberidhash in temp:
                                        temp.append(memberidhash)

                                        await ctx.reply(f"{member.name} is afk: {botdata['afkmembers'][memberidhash]}")
                            except:
                                pass

                        if ctx.reference:
                            original = await ctx.channel.fetch_message(ctx.reference.message_id)
                            memberidhash = gethash(original.author.id)

                            if memberidhash in botdata[
                                "afkmembers"] and not memberidhash == uidhash and not memberidhash in temp:
                                member = self.bot.get_user(original.author.id)
                                temp.append(memberidhash)

                                await ctx.reply(f"{member.name} is afk: {botdata['afkmembers'][memberidhash]}")

                    if ctx.content.startswith("<@!BOT_ID>"):
                        await ctx.channel.send(
                            embed=discord.Embed(description=f"fMy prefix is `{credentials['prefix']}`",
                                                color=discord.Colour.dark_blue()))

                    if uidhash in botdata["afkmembers"]:
                        saveconfig({
                            "afkmembers.remove": [uidhash, None]
                        })

                        await ctx.reply(f"I removed your afk", delete_after=5)

                    if guildconfig["greetings"] == True and globalconfig["greetings"]:
                        if ctx.content.lower().startswith("hello") or ctx.content.lower().startswith("hi") or \
                                ctx.content.startswith("hey") and not ctx.author.bot and not "welcome" in \
                                                                                             ctx.channel.name.lower():
                            greetings = ["Hello", "Hi", "Greetings", "Hey", "Hiya"]

                            resp = greetings[random.randint(random.randint(0, len(greetings) - 2), len(greetings) - 1)]
                            await ctx.channel.send(resp + " " + ctx.author.mention + "!")

                    if "@someone" in ctx.content.lower() and globalconfig["someoneping"] \
                            and not ctx.author.bot and guildconfig["someoneping"]:
                        members = []
                        ping = True

                        for member in ctx.guild.members:
                            if not member.bot and not member == ctx.author:
                                members.append(member)

                        member = members[random.randint(random.randint(0, len(members) - 2), len(members) - 1)]

                        hash = gethash(ctx.author.id)

                        for user in pingcooldown:
                            args = user.split(":")
                            cooldowntime = round(time.perf_counter() - float(args[1]))

                            if cooldowntime < 30 and args[0] == hash and not ctx.author.bot:
                                cooldown = round(30 - cooldowntime, 1)
                                try:
                                    await ctx.reply(embed=discord.Embed(
                                        description=f":x: You are on cooldown. Try again in {cooldown}s",
                                        color=discord.Colour.red()), delete_after=5)
                                except Exception as error:
                                    traceback.print_exc()

                                ping = False
                            else:
                                pingcooldown.remove(user)

                        if ping:
                            await ctx.channel.send(member.mention)
                            pingcooldown.append(f"{hash}:{time.perf_counter()}")

                    if "@someone" in ctx.content.lower():
                        if not guildconfig["someoneping"]:

                            await ctx.channel.send(
                                embed=discord.Embed(description="@someone ping is disabled in this server",
                                                    color=discord.Colour.red()))

                        elif not globalconfig["someoneping"]:
                            await ctx.channel.send(embed=discord.Embed(description="@someone ping is disabled globally",
                                                                       color=discord.Colour.red()))

                    if guildconfig["filterprofanity"]:

                        for word in whitelist:
                            if "msg" in locals():
                                msg = msg.replace(word, "")
                            else:
                                msg = ctx.content.lower().replace(word, "")

                        has_profanity = profanity.contains_profanity(msg)

                        if has_profanity:

                            if guildconfig["deleteprofanity"]:
                                censored = profanity.censor(ctx.content, censor_char="\*")

                                embed = discord.Embed(title="Watch your language", color=discord.Colour.dark_blue())
                                embed.add_field(name="Filtered message", value=censored)
                                embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar)
                                try:
                                    await ctx.delete()
                                    await ctx.channel.send(ctx.author.mention, embed=embed)

                                except Exception as error:
                                    if "Missing Permissions" in str(error):
                                        await ctx.channel.send(ctx.author.mention, embed=embed.set_footer(
                                            text="I was unable to delete the message due to insufficient permissions."))
                            else:
                                embed = discord.Embed(title="Watch your language", color=discord.Colour.dark_blue())
                                await ctx.channel.send(ctx.author.mention, embed=embed)

                    if random.randint(0, 10000000) < 10:
                        await ctx.reply("🍕")

                elif not ctx.author.bot:
                    if ctx.author.id == self.bot.owner_id and guildconfig[
                        "botenabled"] is False \
                            and ctx.content.startswith({credentials['prefix']}):
                        await ctx.channel.send("Note: I am disabled in this server")
                        await self.bot.process_commands(ctx)

                    elif ctx.author.id == self.bot.owner_id and not globalconfig["botenabled"] \
                            and ctx.content.startswith({credentials['prefix']}):

                        await ctx.channel.send("Note: I am disabled globally")
                        await self.bot.process_commands(ctx)

                    elif ctx.author.id == self.bot.owner_id:
                        await self.bot.process_commands(ctx)

                    elif ctx.author.guild_permissions.manage_messages and globalconfig["botenabled"] and not \
                            gethash(ctx.author.id) in botdata["blacklist"]:
                        await self.bot.process_commands(ctx)

                    elif guildconfig["botenabled"] is False and ctx.content.startswith({credentials['prefix']}) and not \
                            gethash(ctx.author.id) in botdata["blacklist"]:
                        await ctx.channel.send(embed=discord.Embed(description="I am disabled in this server"))

                    elif ctx.content.startswith({credentials['prefix']}) and not globalconfig["botenabled"] \
                            and not gethash(ctx.author.id) in botdata["blacklist"]:
                        await ctx.channel.send(
                            embed=discord.Embed(description="I am disabled globally",
                                                color=discord.Colour.red()).set_footer(
                                text="Tip: my status will be do not disturb when I am disabled globally"))

        except Exception as error:
            if "private" in str(ctx.channel.type) and \
                    not gethash(ctx.author.id) in botdata["modmailexempt"] \
                    and not ctx.content.startswith({credentials['prefix']}) and not ctx.author.bot:
                guilds = []

                for guild in self.bot.guilds:
                    if guild.get_member(ctx.author.id):
                        guilds.append(guild)

                if len(guilds) < 2 and not len(guilds) == 0:
                    guildidhash = gethash(guilds[0].id)
                    guildconfig = botdata[guildidhash]["config"]

                    if type(guildconfig["modmailchannel"]) == int:
                        channel = self.bot.get_channel(guildconfig["modmailchannel"])
                        embed = discord.Embed(title="New message",
                                              description=profanity.censor(ctx.content, censor_char="\*"),
                                              color=discord.Colour.dark_blue())
                        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar)
                        embed.set_footer(text=str(ctx.author.id))

                        await channel.send(embed=embed)
                        await sleep(1)
                        await ctx.author.send("Message forwarded to staff.")

                    else:
                        await ctx.author.send("The server you're trying to contact has not set up modmail yet.")

                elif len(guilds) >= 2:
                    count = 0
                    _guilds = {}
                    msg = ""

                    for guild in guilds:
                        count += 1
                        _guilds[count] = guild

                    for guild in _guilds.keys():
                        msg += f"`{guild}` - {_guilds[guild].name}\n"

                    embed = discord.Embed(title="Which server are you trying to DM?", description=msg,
                                          color=discord.Colour.dark_blue())
                    embed.set_footer(text="Only send the number your server corresponds to, not the server name.")

                    saveconfig({
                        "modmailexempt.append": gethash(ctx.author.id)
                    })
                    await ctx.author.send(embed=embed)

                    def check(msg):
                        if ctx.author.id == msg.author.id:
                            return True
                        else:
                            return False

                    try:
                        msg = await self.bot.wait_for(event="message", check=check, timeout=20)
                    except:
                        saveconfig({
                            "modmailexempt.remove": gethash(ctx.author.id)
                        })

                    try:
                        if int(msg.content) in _guilds:
                            saveconfig({
                                "modmailexempt.remove": gethash(ctx.author.id)
                            })
                            guild = _guilds[int(msg.content)]
                            guildidhash = gethash(guild.id)
                            guildconfig = botdata[guildidhash]["config"]

                            if type(guildconfig["modmailchannel"]) == int:
                                channel = self.bot.get_channel(guildconfig["modmailchannel"])
                                embed = discord.Embed(title="New message",
                                                      description=profanity.censor(ctx.content, censor_char="\*"),
                                                      color=discord.Colour.dark_blue())
                                embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar)
                                embed.set_footer(text=str(ctx.author.id))

                                await channel.send(embed=embed)
                                await sleep(1)
                                await ctx.author.send("Message forwarded to staff.")
                            else:
                                await ctx.author.send("The server you're trying to contact has not set up modmail yet.")

                        else:
                            saveconfig({
                                "modmailexempt.remove": gethash(ctx.author.id)
                            })
                            await ctx.author.send(
                                "That server is not in listed. Please try again and make sure to"
                                " **only send the number that corresponds to the server**")
                    except:
                        saveconfig({
                            "modmailexempt.remove": gethash(ctx.author.id)
                        })

            elif not str(ctx.channel.type) == "private" and not ctx.author.id in botdata["modmailexempt"]:
                date = datetime.datetime.now().strftime(r"%m/%d/%Y %H:%M:%S")
                botdata["errors"].append(f"`on_message` event on `{date}` ```fix\n{error}```")

                if type(error) == KeyError:
                    if ctx.guild:
                        hash = gethash(ctx.guild.id)
                        saveconfig({
                            f"guild.{hash}.createconfig": None
                        })

                        await ctx.channel.send(
                            "**(Getting this message when adding me is a known bug. Bot should still work properly)**"
                            "Missing or corrupted settings and data detected for this sever. They have been reset."
                            " We appologize for any inconvenience.")
                        await self.bot.process_commands(ctx)

                    return

                channel = self.bot.get_channel(credentials["log_channel"])
                error = "".join(traceback.format_exception(type(error), error, error.__traceback__))
                await channel.send(f"```python\n{error}```")

            if ctx.author.id == self.bot.owner_id:
                await self.bot.process_commands(ctx)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        global botdata

        guildidhash = gethash(member.guild.id)
        guilddata = botdata[guildidhash]
        raidconfig = guilddata["config"]["antiraid"]

        if type(guilddata["config"]["log_channel"]) == int:
            channel = self.bot.get_channel(guilddata["config"]["log_channel"])

        else:
            channel = member.guild.system_channel

        if raidconfig["enabled"]:
            embed = discord.Embed(title=f"You've been automatically kicked or banned from {member.guild.name}",
                                  color=discord.Colour.gold())
            embed.add_field(name="Why?", value=f"There are several reasons why you may have been kicked or banned:\n\n"
                                               f"**-** Anti-raid has been triggered.\n"
                                               f"**-** Your username has profane, offensive,"
                                               f" or hateful language.\n"
                                               f"**-** Your username, or parts of your username, are "
                                               f"blacklisted by {member.guild.name}.")
            embed.add_field(name="What can I do?", value="You can:\n\n"
                                                         "**-** Remove profane, hateful, or offensive language"
                                                         " from your username.\n"
                                                         "**-** Contact the moderators of"
                                                         f" {member.guild.name}.\n"
                                                         f"**-** Try again later.")

            if raidconfig["underraid"]:
                if raidconfig["mode"] == "active":
                    await sleep(0.4)

                    if raidconfig["action"] == "kick":
                        action = "kicked"
                    else:
                        action = "banned"

                    try:
                        saveconfig({
                            f"guild.{guildidhash}.config.antiraid.count.add": None
                        })

                        if raidconfig["count"] > 3:
                            await sleep(0.4)
                        await member.send(embed=embed)
                    except:
                        pass
                    finally:
                        await sleep(0.5)

                    try:
                        if raidconfig["action"] == "kick":
                            await member.kick(reason="Automatic action carried out (anti-raid triggered)")
                        else:
                            await member.ban(reason="Automatic action carried out (anti-raid triggered)")

                    except:
                        await sleep(1)
                        await channel.send(f"Could not {raidconfig['action']} {member.mention}!")

                else:
                    raidconfig["underraid"] = False
                    saveconfig({
                        f"guild.{guildidhash}.config.antiraid.underraid": False
                    })

                return

            if guilddata["config"]["antiraid"]["banprofanenicks"] \
                    and profanity.contains_profanity(member.display_name):
                await sleep(0.2)

                action = "kicked"

                try:
                    await member.send(embed=embed)
                except:
                    pass
                finally:
                    await sleep(0.5)

                try:
                    await member.kick(reason="Profane nickname")
                    await sleep(1)

                    await channel.send(f"kick {member.mention}: profane nickname")
                except:
                    await sleep(1)
                    await channel.send(f"Could not kick {member.mention}!")

            elif len(guilddata["config"]["antiraid"]["blacklist"]) > 0 \
                    and any(name in member.display_name.lower() for name in guilddata["config"]["antiraid"]["blacklist"]):
                await sleep(0.2)

                try:
                    await member.send(embed=embed)
                except:
                    pass
                finally:
                    await sleep(0.5)

                try:
                    if raidconfig["action"] == "kick":
                        await member.kick(reason="Blacklisted nickname")
                    elif raidconfig["action"] == "ban":
                        await member.ban(reason="Blacklisted nickname")
                        await sleep(1)

                        await channel.send(f"{raidconfig['action']} {member.mention}: blacklisted nickname")

                except Exception as error:
                    await sleep(1)
                    await channel.send(f"Could not {raidconfig['action']} {member.mention}!")

            temp = 0
            msg = ""

            if guildidhash not in antiraidlog:
                antiraidlog[guildidhash] = []

            antiraidlog[guildidhash].append({"id": member.id, "time": time.perf_counter()})
            membercount = raidconfig["rate"][0]
            log = []

            if len(antiraidlog[guildidhash]) >= membercount:
                for i in range(1, membercount + 1):
                    log.append(antiraidlog[guildidhash][-i])

                for event in log:
                    if "lastevent" in locals():
                        temp2 = lastevent["time"] - event["time"]
                        temp += temp2
                        lastevent = event
                    else:
                        lastevent = event

                if raidconfig["rate"][1] > temp > 0:
                    raidconfig["underraid"] = True
                    saveconfig({
                        f"guild.{guildidhash}.config.antiraid.underraid": True
                    })

                    for role in member.guild.roles:
                        if role.permissions.kick_members and not role.managed:
                            msg += role.mention
                            msg += " "

                    msg += f"Anti-raid has been triggered! To disable it, use `{credentials['prefix']}antiraid end`"

                    await channel.send(msg)
                    await sleep(1)

                    if raidconfig["mode"] == "active":
                        for event in log:
                            try:
                                _member = member.guild.get_member(event["id"])
                                await _member.kick(reason="Automatic action carried out (anti-raid triggered)")
                            except:
                                pass
                            finally:
                                await sleep(1)

                    if raidconfig["raiseverification"]:
                        if not member.guild.verification_level == discord.VerificationLevel.high \
                                or not member.guild.verification_level == discord.VerificationLevel.very_high:
                            try:
                                await member.guild.edit(verification_level=discord.VerificationLevel.high)
                            except:
                                pass
                            finally:
                                await sleep(0.4)

                    if raidconfig["revokeinvites"]:
                        for invite in await member.guild.invites():
                            try:
                                await invite.delete(reason="Automatic action carried out (anti-raid triggered)")
                            except:
                                pass
                            finally:
                                await sleep(0.5)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        global botdata

        hash = gethash(guild.id)
        saveconfig({
            f"guild.{hash}.createconfig": None
        })

        msg = discord.Embed(title="Thanks for adding me!",
                            description=f"I am {credentials['name']}. Here are some of my features. "
                                        f"For more information, see `{credentials['prefix']}help`",
                            color=discord.Colour.dark_blue())
        msg.add_field(name="Utility",
                      value=f"**-** Image lookup (`{credentials['prefix']}image`)\n"
                            f"**-** AFK status (`{credentials['prefix']}afk`)\n"
                            f"**-** Announcements (`{credentials['prefix']}announce`)")
        msg.add_field(name="Moderation",
                      value=f"**-** Modmail (`{credentials['prefix']}modmail`)\n"
                            f"**-** Anti-raid (`{credentials['prefix']}antiraid`)\n"
                            f"**-** Profanity filter (`{credentials['prefix']}config`)\n"
                            f"**-** Server audit (`{credentials['prefix']}audit`)")
        msg.add_field(name="Miscellaneous",
                      value=f"**-** SpaceX information (`{credentials['prefix']}spacex`)\n"
                            f"**-** NASA astronomy picture of the day (`{credentials['prefix']}apod`)\n"
                            f"**-** @someone ping\n")

        await sleep(5)

        try:
            await guild.system_channel.send(embed=msg)
        except:
            for channel in guild.channels:
                try:
                    await channel.send(embed=msg)
                    break
                except:
                    await sleep(1)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        strerror = str(error)
        red = discord.Colour.red()
        yellow = discord.Colour.gold()

        if isinstance(error, commands.errors.CommandOnCooldown):
            await ctx.reply(embed=discord.Embed(description=f":warning: {error}", color=yellow), delete_after=5,
                            mention_author=False)

        elif isinstance(error, commands.errors.MissingPermissions):
            await ctx.reply(embed=discord.Embed(description=f":x: {strerror}", color=red), delete_after=5,
                            mention_author=False)
        elif isinstance(error, commands.errors.CommandNotFound):
            await self.bot.get_cog("miscellaneous").help(ctx=ctx)
        elif isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.reply(embed=discord.Embed(description=f":x: {strerror}", color=red), delete_after=5,
                            mention_author=False)
        elif isinstance(error, commands.errors.BadArgument):
            await ctx.reply(embed=discord.Embed(description=f":x: {strerror}", color=red), delete_after=5,
                            mention_author=False)
        else:
            await ctx.reply(embed=discord.Embed(description=f":x: Internal error", color=red), delete_after=5,
                            mention_author=False)

            await sleep(1)

            channel = self.bot.get_channel(credentials["log_channel"])
            error = "".join(traceback.format_exception(type(error), error, error.__traceback__))
            await channel.send(f"```python\n{error}```")


def syncdata():
    global botdata

    host = listener(port=2006)

    while True:
        try:
            conn = host.accept()
            data = conn.recv()

            if data == "close":
                host.close()
                break

            botdata = processdeltas(data, botdata)
        except:
            traceback.print_exc()


async def setup(bot: commands.Bot):
    global botdata
    global credentials

    await bot.add_cog(events(bot))

    threading.Thread(target=host).start()
    threading.Thread(target=syncdata).start()

    botdata = loadconfig()
    credentials = json.load(open("data/credentials.json"))
