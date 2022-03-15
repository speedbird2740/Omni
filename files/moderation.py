import threading
import time
from asyncio import sleep

import discord
from better_profanity import profanity
from discord.ext import commands
from discord.ext.commands import has_permissions, bot_has_permissions

from files.backend.config_framework import loadconfig, saveconfig, listener, gethash, processdeltas

botdata = {}


class moderation(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(description="Detect and protect against server raids.")
    @has_permissions(kick_members=True)
    @bot_has_permissions(kick_members=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def antiraid(self, ctx, setting=None, value=None):
        hash = gethash(ctx.guild.id)
        raidconfig = botdata[hash]["config"]["antiraid"]
        syntax = f"guild.{hash}.config.antiraid"

        if setting == "end":
            if raidconfig["underraid"]:
                saveconfig({
                    f"{syntax}.count.reset": None,
                    f"{syntax}.underraid": False,
                    f"{syntax}.log.reset": None
                })

                await ctx.send("Anti-raid ended!")
            else:
                await ctx.send("Anti-raid hasn't been triggered!")

        elif setting == "enable":
            saveconfig({
                f"{syntax}.enabled": True
            })
            await ctx.send("Anti-raid enabled!")

        elif setting == "disable":
            saveconfig({
                f"{syntax}.enabled": False
            })
            await ctx.send("Anti-raid disabled!")

        elif setting == "mode":
            if value == "passive":
                saveconfig({
                    f"{syntax}.mode": "passive"
                })
                await ctx.send("Anti-raid set to passive!")
            elif value == "active":
                saveconfig({
                    f"{syntax}.mode": "active"
                })
                await ctx.send("Anti-raid set to active!")

        elif setting == "rate":
            value = value.split("/")

            try:
                memberlimit = int(value[0])
                seconds = int(value[1])
                saveconfig({
                    f"{syntax}.rate": [memberlimit, seconds]
                })

                if not memberlimit > 1:
                    raise commands.errors.BadArgument("Member limit must be greater than 1")
                if not seconds > 1:
                    raise commands.errors.BadArgument("Seconds must be greater than 1.")
            except TypeError:
                raise commands.errors.BadArgument("Rate limits must be integers.")

            await ctx.send(f"Anti-raid rate limit set to {memberlimit} new member(s) every {seconds} second(s)!")

        elif setting == "action":
            if value == "kick":
                saveconfig({
                    f"{syntax}.action": "kick"
                })
                await ctx.send("Action on anti-raid trigger set to kick!")
            elif value == "ban":
                saveconfig({
                    f"{syntax}.action": "ban"
                })
                await ctx.send("Action on anti-raid trigger set to ban!")

        elif setting == "revokeinvites":
            if value == "enable":
                saveconfig({
                    f"{syntax}.revokeinvites": True
                })
                await ctx.send("Enabled revoking invites on anti-raid trigger!")
            elif value == "disable":
                saveconfig({
                    f"{syntax}.revokeinvites": False
                })
                await ctx.send("Disabled revoking invites on anti-raid trigger!")

        elif setting == "raiseverification":
            if value == "enable":
                saveconfig({
                    f"{syntax}.raiseverification": True
                })
                await ctx.send("Enabled raising server verification on anti-raid trigger!")
            elif value == "disable":
                saveconfig({
                    f"{syntax}.raiseverification": False
                })
                await ctx.send("Disabled raising server verification on anti-raid trigger!")

        elif setting == "banprofanenicks":
            if value == "enable":
                saveconfig({
                    f"{syntax}.banprofanenicks": True
                })
                await ctx.send("Enabled kicking new members with profane nicknames!")
            elif value == "disable":
                saveconfig({
                    f"{syntax}.banprofanenicks": False
                })
                await ctx.send("Disabled kicking new members with profane nicknames!")

        elif setting == "add":
            if value.lower() not in raidconfig["blacklist"]:
                if len(value) >= 32:
                    raise commands.errors.BadArgument("Nickname must be less than 32 characters")
                elif len(raidconfig["blacklist"]) >= 30:
                    raise commands.errors.BadArgument("There can be no more than 30 blacklisted nicknames")

                saveconfig({
                    f"{syntax}.blacklist.append": value.lower()
                })
                await ctx.send(f"Added {value} to the nickname blacklist!")
            else:
                await ctx.send(f"{value} is already in the blacklist!")

        elif setting == "remove":
            if value.lower() in raidconfig["blacklist"]:
                saveconfig({
                    f"{syntax}.blacklist.remove": value.lower()
                })
                await ctx.send(f"Removed {value} from the nickname blacklist!")
            else:
                await ctx.send(f"{value} is not in the blacklist!")

        elif setting == "trigger":
            syntax = f"guild.{hash}.config.antiraid"

            saveconfig({
                f"{syntax}.enabled": True,
                f"{syntax}.count.reset": None,
                f"{syntax}.mode": "active",
                f"{syntax}.underraid": True
            })
            await ctx.send("Anti-raid manually triggered!")

            if raidconfig["raiseverification"]:
                if not ctx.guild.verification_level == discord.VerificationLevel.high \
                        or not ctx.guild.verification_level == discord.VerificationLevel.very_high:
                    try:
                        await ctx.guild.edit(verification_level=discord.VerificationLevel.high)
                    except:
                        pass
                    finally:
                        await sleep(0.4)

            if raidconfig["revokeinvites"]:
                for invite in await ctx.guild.invites():
                    try:
                        await invite.delete(reason="Automatic action carried out (anti-raid triggered)")
                    except:
                        pass
                    finally:
                        await sleep(0.5)

        elif setting == "show":
            if raidconfig["enabled"]:
                raidenabled = "Yes"
            else:
                raidenabled = "No"

            if raidconfig["underraid"]:
                underraid = "Yes"
            else:
                underraid = "No"

            if raidconfig["banprofanenicks"]:
                banprofanenicks = "Yes"
            else:
                banprofanenicks = "No"

            if len(raidconfig["blacklist"]) > 0:
                blacklist = ", ".join(raidconfig["blacklist"])
            else:
                blacklist = "No banned nicknames."

            if raidconfig["revokeinvites"]:
                revokeinvites = "Yes"
            else:
                revokeinvites = "No"

            if raidconfig["raiseverification"]:
                raiseverification = "Yes"
            else:
                raiseverification = "No"

            embed = discord.Embed(title="Anti-raid configuration", color=discord.Colour.dark_blue())
            embed.add_field(name="Anti-raid enabled", value=raidenabled)
            embed.add_field(name="Server under raid", value=underraid)
            embed.add_field(name="Anti-raid mode", value=raidconfig["mode"])
            embed.add_field(name="Anti-raid rate limit",
                            value=f'{raidconfig["rate"][0]} new members every {raidconfig["rate"][1]} seconds')
            embed.add_field(name="Action on anti-raid trigger", value=raidconfig["action"])
            embed.add_field(name="Revoke server invites on anti-raid trigger", value=revokeinvites)
            embed.add_field(name="Raise server verification on anti-raid trigger", value=raiseverification)
            embed.add_field(name="Disallow profane nicknames", value=banprofanenicks)
            embed.add_field(name="Blacklisted nicknames", value=blacklist)

            await ctx.send(embed=embed)

        else:
            embed = discord.Embed(title="Anti-raid", description="Configure the anti-raid module.",
                                  color=discord.Colour.dark_blue())
            embed.add_field(name="Enable or disable anti-raid", value="```./antiraid enable/disable```", inline=False)

            embed.add_field(name="Anti-raid modes", value="".join(
                ("There are two modes: passive, and active. In passive mode, Omni will",
                 " alert everyone with the kick members permission. Active mode will kick any new members"
                 " after anti-raid is triggered on top of alerting",
                 "\n\nTo change the mode, use the following command```./antiraid mode passive/active```")),
                            inline=False)

            embed.add_field(name="Rate limit",
                            value="Change the rate limit at which anti-raid will trigger at. The format is"
                                  " `<new members>/<seconds>` ```./antiraid rate 2/4```",
                            inline=False)

            embed.add_field(name="Action on anti-raid trigger",
                            value="```./antiraid action kick/ban```Kicking due to profane nickname will kick regardless"
                                  " of this setting.",
                            inline=False)

            embed.add_field(name="Revoke all server invites on anti-raid trigger",
                            value="```./antiraid revokeinvites enable/disable```",
                            inline=False)

            embed.add_field(name="Raise the server verification on anti-raid trigger",
                            value="This will set the verification level to High if it is lower than that ```./antiraid"
                                  " raiseverification enable/disable```",
                            inline=False)
            embed.add_field(name="Disallow new members with profane nicknames",
                            value="```./antiraid banprofanenicks enable/disable```", inline=False)

            embed.add_field(name="Disallow new members with a specific phrase in their nickname",
            value="```./antiraid add/remove <nickname>```Case insensitive", inline=False)

            embed.add_field(name="Manually trigger anti-raid", value="```./antiraid trigger```")
            embed.add_field(name="End anti-raid after triggering", value="```./antiraid end```")
            embed.add_field(name="Show the current anti-raid configuration", value="```./antiraid show```")

            await ctx.send(embed=embed)

    @commands.command(description="Audit your server for weak or dangerous role permissions and more.")
    @has_permissions(manage_guild=True)
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def audit(self, ctx):

        warnings = ""
        critical = ""

        for role in ctx.guild.roles:
            if role.is_default():
                for permission in role.permissions:
                    name = permission[0]
                    value = permission[1]

                    if name == "mention_everyone" and value:
                        warnings += f"**-** {role.mention} can ping @everyone, @here, and all roles.\n"

                    elif name == "manage_channels" and value:
                        critical += f"**-** {role.mention} can manage channels.\n"

                    elif name == "manage_roles" and value:
                        critical += f"**-** {role.mention} can manage roles.\n"

                    elif name == "view_audit_log" and value:
                        warnings += f"**-** {role.mention} can view audit log.\n"

                    elif name == "manage_guild" and value:
                        critical += f"**-** {role.mention} can manage server.\n"

                    elif name == "kick_members" and value:
                        critical += f"**-** {role.mention} can kick members.\n"

                    elif name == "ban_members" and value:
                        critical += f"**-** {role.mention} can ban members.\n"

                    elif name == "manage_messages" and value:
                        warnings += f"**-** {role.mention} can manage messages.\n"

                    elif name == "administrator" and value:
                        critical += f":x: **CRITICAL: {role.mention} has administrator.**\n"

                    elif name == "view_guild_insights" and value:
                        warnings += f"**-** {role.mention} can view server insights.\n"

                    elif name == "manage_nicknames" and value:
                        critical += f"**-** {role.mention} can manage nicknames.\n"

                    elif name == "manage_emojis" and value:
                        critical += f"**-** {role.mention} can manage emojis.\n"

                    elif name == "priority_speaker" and value:
                        warnings += f"**-** {role.mention} can be priority speaker in voice channels.\n"

            elif role.managed:
                for permission in role.permissions:
                    name = permission[0]
                    value = permission[1]

                    if name == "administrator" and value:
                        critical += f"**-** {role.mention} has administrator. **NO bot, integration, or organization requires the administrator permission.**\n"

            else:
                permissions = []

                for permission in role.permissions:
                    name = permission[0]
                    value = permission[1]

                    if value:
                        permissions.append(name)

                if "kick_members" in permissions and not "administrator" in permissions:
                    warnings += f"**-** {role.mention} has moderator permissions.\n"

                elif "ban_members" in permissions and not "administrator" in permissions:
                    warnings += f"**-** {role.mention} has moderator permissions.\n"

                elif "administrator" in permissions or any("manage" in permission for permission in permissions):
                    warnings += f"**-** {role.mention} has manager/administrator permissions.\n"

                if profanity.contains_profanity(role.name):
                    warnings += f"**-** {role.mention}: potentially offensive role name.\n"

        if profanity.contains_profanity(ctx.guild.name):
            warnings += f"**-** Potentially offensive server name.\n"

        for channel in ctx.guild.channels:
            if profanity.contains_profanity(channel.name):
                warnings += f"**-** {channel.mention}: potentially offensive channel name.\n"

        if not ctx.guild.mfa_level == 1:
            warnings += "**-** 2 factor authentication for moderator powers is not required.\n"

        if ctx.guild.verification_level == discord.VerificationLevel.none:
            warnings += "**-** Server verification is disabled.\n"

        if ctx.guild.verification_level == discord.ContentFilter.disabled:
            warnings += "**-** Media content isn't being scanned for explicit content.\n"

        if warnings == "":
            warnings = "No warnings found."
        if critical == "":
            critical = "No critical issues found."

        try:
            embed = discord.Embed(title="Server audit", color=discord.Colour.dark_blue())
            embed.add_field(name="Warnings", value=warnings, inline=False)
            embed.add_field(name="Critical", value=critical, inline=False)

            await ctx.send(embed=embed)
        except:
            embed1 = discord.Embed(title="Warnings", description=warnings, color=discord.Colour.dark_blue())
            embed2 = discord.Embed(title="Critical", description=critical, color=discord.Colour.dark_blue())

            await ctx.send(embed=embed1)
            time.sleep(0.5)
            await ctx.send(embed=embed2)

    @commands.command(description="Modmail for your moderation needs")
    @has_permissions(kick_members=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def modmail(self, ctx, *args):
        if len(args) > 0:
            action = args[0]

            if action == "set" and len(args) == 1:
                hash = gethash(ctx.guild.id)
                saveconfig({
                    f"guild.{hash}.config.modmailchannel": ctx.message.channel.id
                })

                await ctx.send(f"I've set {ctx.message.channel.mention} as the modmail channel!")

            elif action == "send" and len(args) > 2:
                member = self.bot.get_user(int(args[1].replace("<", "").
                                               replace("!", "").replace(">", "").replace("@", "")))

                if any(member.id == user.id for user in ctx.guild.members):
                    msg = profanity.censor(ctx.message.content.replace(f"./modmail send {args[1]} ", ""), censor_char="\*")

                    embed = discord.Embed(title=f"New message from {ctx.guild.name}", description=msg,
                                          color=discord.Colour.dark_blue())
                    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
                    embed.set_footer(text=str(ctx.author.id))

                    try:
                        await member.send(embed=embed)
                        await ctx.send(f"Successfully sent the message to {member.name}")
                    except:
                        await ctx.send(f"Failed to send the message to {member.name}")
                else:
                    await ctx.send("Cannot find user.")

        else:
            embed = discord.Embed(title="Modmail", color=discord.Colour.dark_blue())
            embed.add_field(name="Set up a modmail channel",
                            value="```./modmail set``` in the channel you want to set as modmail.", inline=False)
            embed.add_field(name="Send/reply to modmail",
                            value="```./modmail send <user id> <message>```All sent and"
                                  " received messages will be filtered from profanity.",
                            inline=False)

            await ctx.send(embed=embed)


def syncdata():
    global botdata

    host = listener(port=2004)

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

    bot.add_cog(moderation(bot))
    botdata = loadconfig()
    threading.Thread(target=syncdata).start()
