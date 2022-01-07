# Events
## Method Descriptions
**Documentation here is a work in progress**


### class events(commands.Cog)
Class where all Discord event listeners are stored.

#### on_message(self, ctx: discord.Message)
Discord listener that is called whenever a message that Omni can see
is received. This listener is responsible for message related functions
such as the profanity filter, AFK status, and modmail. 

**This listener is not responsible for calling `bot.process_commands()`.**

#### on_member_join(self, member: discord.Member)
Discord listener that is called whenever a member joins a server that
Omni is in. It processes member join events for the anti-raid feature.

#### on_guild_join(self, guild)
Discord listener that is called whenever Omni joins a new server.
It is responsible for creating configuration values for the new server
and sending the welcome message.

#### on_command_error(self, ctx, error)
Discord listener that is called whenever a command raises an error. 
It is responsible for most of the error handling.