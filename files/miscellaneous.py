import json
import time

import discord
from discord.ext import commands
from discord.ext.commands import has_permissions

from main import version

cogs = ["utility", "fun", "space", "miscellaneous", "moderation", "configuration"]
credentials = {}


class miscellaneous(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(description="Test if the bot is working")
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def test(self, ctx):
        await ctx.send('Bot is up and working properly')

    @commands.command(description="See the bot's statistics")
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def stats(self, ctx):
        ping = round(self.bot.latency * 1000)
        servers = len(self.bot.guilds)

        embed = discord.Embed(title="Bot statistics", description="Processing...", color=discord.Colour.dark_blue())

        start = time.perf_counter()
        msg = await ctx.send(embed=embed)
        end = time.perf_counter()
        time.sleep(1)

        total = ((end - start) * 1000) - ping

        embed = discord.Embed(title="Bot statistics", color=discord.Colour.dark_blue())
        embed.add_field(name="Connection latency", value=f"{ping}ms")
        embed.add_field(name="API latency", value=f"{round(total)}ms")
        embed.add_field(name="Servers", value=str(servers))

        await msg.edit(embed=embed)

    @commands.command(description="Get my invite link")
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def invite(self, ctx):
        await ctx.send(embed=discord.Embed(title="Invite link",
                                           url="https://example.com",
                                           color=discord.Colour.dark_blue()))

    @commands.command(description="Get help on using the bot")
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def help(self, ctx):
        cats = ""
        comms = ""
        for cog in cogs:
            cats = cats + f"**`{cog}`**\n"

        args = ctx.message.content.split(" ")
        msg = discord.Embed(title="Help",
                            description=f"Here is a list of all command categories. For more information on a category,"
                                        f" use `{credentials['prefix']}help <category>`.",
                            color=discord.Colour.dark_blue())

        msg = msg.add_field(name="------------", value=cats)

        try:
            cat = args[1]
            commands = self.bot.get_cog(cat).get_commands() if cat in cogs else None

            for command in commands:
                comms += f"`{credentials['prefix']}{command.name}` - {command.description}\n"

            msg = discord.Embed(title=cat.capitalize() + " commands", description=comms,
                                color=discord.Colour.dark_blue())
        except:
            pass

        await ctx.send(embed=msg)

    @commands.command(description="View the changelog for the latest update")
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def changelog(self, ctx):
        msg = discord.Embed(title=f"Changelog for v{version}", color=discord.Colour.dark_blue())
        msg.add_field(name="New commands/features",
                      value=f"**-** You can now set a separate bot messages channel. See `{credentials['prefix']}config` for more information.\n"
                            "**-** The performance and reliability of anti-raid has been improved.\n"
                            "**-** Revamped welcome message.",
                      inline=False)
        msg.add_field(name="What's changed",
                      value="**-** Removed a few unused settings.\n"
                            "**-** To better deal with rate limiting, anti-raid will no longer log kicks/bans unless "
                            "it was triggered by a blacklisted nickname or inappropriate nickname.")
        msg.add_field(name="What's fixed",
                      value="**-**")
        msg.add_field(name=f"Changelog for v12",
                      value="**-** Completely reworked config/data sync and storage system.\n"
                            f"**-** `{credentials['prefix']}showconfig` is now merged with "
                            f"`{credentials['prefix']}config` (`{credentials['prefix']}config show`).\n"
                            "**-** Mitigates error message when adding me to a server.",
                      inline=False)

        await ctx.send(embed=msg)

    @commands.command(description="View the currently running studies")
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def studies(self, ctx):

        msg = discord.Embed(title=f"Current studies", description="No studies are being run.",
                            color=discord.Colour.dark_blue())
        await ctx.send(embed=msg)

    @commands.command(description="Troubleshoot issues with Omni")
    @has_permissions(manage_guild=True)
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def troubleshoot(self, ctx):
        issues = ""

        if not ctx.guild.system_channel:
            issues += "**-** A system messages channel isn't set. Affects anti-raid" \
                      " (you will not receive anti-raid alerts).\n"

        for perm in ctx.guild.me.guild_permissions:
            name = perm[0]
            value = perm[1]

            if not value:
                if name == "kick_members":
                    issues += "**-** I cannot kick members. Affects antiraid (active mode).\n"
                elif name == "view_channels":
                    issues += "**-** I cannot view channels. May affect AFK, greetings, and profanity filter.\n"
                elif name == "manage_messages":
                    issues += "**-** I cannot manage messages: Affects profanity filter.\n"
                elif name == "mention_everyone":
                    issues += f"**-** I cannot ping @everyone. Affects `{credentials['prefix']}announcements`\n"
                elif name == "read_message_history":
                    issues += "**-** I cannot read message history. This affects any command that takes parameters," \
                              " error messages, and anti-spam messages/warnings.\n"
                elif name == "manage_guild":
                    issues += "**-** I cannot manage the server. Affects anti-raid with revoke invites on and raising" \
                              " server verification level on.\n"
                elif name == "ban_members":
                    issues += "**-** I cannot ban members. Affects anti-raid when set to" \
                              " ban new members during a raid.\n"

        if issues == "":
            issues = "No issues found."

        embed = discord.Embed(title="Potential issues", description=issues, color=discord.Colour.dark_blue())
        await ctx.send(embed=embed)


def setup(bot: commands.Bot):
    global credentials

    credentials = json.load(open("data/credentials.json"))
    bot.add_cog(miscellaneous(bot))
