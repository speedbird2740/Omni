import json
import random
import threading
import time
import traceback
from asyncio import sleep

import discord
from discord.ext import commands

from files.backend.config_framework import loadconfig
from files.backend.webrequests import spacex_data, getdata

facts = []
nasalinks = []
apod = {}
spacex = {}
botdata = {}
credentials = {}


class space(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(description="Loading bar that represents a full orbit around Earth")
    @commands.cooldown(4, 5400, commands.BucketType.guild)
    async def orbit(self, ctx):

        await ctx.send("This is a loading bar that represents a full orbit around earth")
        chars = "[                                                      ]"
        evennums = [i for i in range(0, 100, 2)]
        char = 1
        msg = await ctx.send(chars)

        for i in range(22):
            chars = list(msg.content)
            chars[char] = "="
            chars[-2] = ""
            if char in evennums:
                chars[-3] = ""
            await msg.edit(content="".join(chars))
            char += 1

            await sleep(245.454545454545)

    @commands.command(description="Get random facts and images on space")
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def space(self, ctx):
        temp = random.randint(random.randint(0, 99 - 1), 100)

        if temp > 30:
            media = random.choice(nasalinks).replace(" ", "%20")
            embed = discord.Embed(color=discord.Colour.dark_blue()).set_image(url=media)
        else:
            media = random.choice(facts)
            embed = discord.Embed(description=media, color=discord.Colour.dark_blue())

        await ctx.send(embed=embed)

    @commands.command(description="Nasa's Astronomy Image of the Day")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def apod(self, ctx):
        try:
            msg = discord.Embed(title=apod["title"], description=apod["explanation"], color=discord.Colour.dark_blue())
            msg = msg.set_image(url=apod["hdurl"])
            msg = msg.set_footer(text=apod["date"])
        except KeyError:
            msg = discord.Embed(title="Failed to fetch one or more data parameters", color=discord.Colour.gold())

            if "title" in apod:
                msg.add_field(name="Found a title", value=apod["title"], inline=False)
            if "url" in apod:
                msg.add_field(name="Found an unmatching url", value=apod["url"], inline=False)

        await ctx.send(embed=msg)

    @commands.command(description="Get data about SpaceX rockets")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def spacex(self, ctx):
        args = ctx.message.content.split(" ")

        last_updated = spacex["last_updated"]

        if len(args) > 1:
            endpoint = args[1].lower()

            if endpoint == "company":
                ceo = spacex["company"]["ceo"]
                address = spacex["company"]["headquarters"]["address"] + ". " + spacex["company"]["headquarters"][
                    "city"] + ", " + spacex["company"]["headquarters"]["state"]
                website = spacex["company"]["links"]["website"]
                rockets = spacex["company"]["vehicles"]
                launch_sites = spacex["company"]["launch_sites"]
                employees = spacex["company"]["employees"]

                embed = discord.Embed(title="SpaceX", color=discord.Colour.dark_blue())
                embed = embed.add_field(name="Founder", value="Elon Musk, 2002")
                embed = embed.add_field(name="CEO", value=ceo)
                embed = embed.add_field(name="Address", value=address)
                embed = embed.add_field(name="Employees", value=employees)
                embed = embed.add_field(name="Vehicles", value=rockets)
                embed = embed.add_field(name="Launch sites", value=launch_sites)
                embed = embed.add_field(name="Website", value=website)

            elif endpoint == "boosters":
                embed = discord.Embed(title="Last 10 SpaceX boosters", color=discord.Colour.dark_blue())
                count = 0

                for i in range(10):
                    count += 1
                    booster = spacex["cores"][-count]

                    status = booster["status"]
                    reuse_count = booster["reuse_count"]
                    landings = booster["rtls_landings"] + booster["asds_landings"]
                    last_update = booster["last_update"]

                    embed = embed.add_field(name=f"#{count}",
                                            value=f"**Status:** {status}\n**Reuses:** {reuse_count}\n"
                                                  f"**Landings:** {landings}\n**Last update:** {last_update}")

            elif endpoint == "dragon":
                dragon = spacex["dragons"][1]

                launch_payload_kg = dragon["launch_payload_mass"]["kg"]
                launch_payload_lb = dragon["launch_payload_mass"]["lb"]

                launch_vol_cm = dragon["launch_payload_vol"]["cubic_meters"]
                launch_vol_cf = dragon["launch_payload_vol"]["cubic_feet"]

                return_payload_kg = dragon["return_payload_mass"]["kg"]
                return_payload_lb = dragon["return_payload_mass"]["lb"]

                return_vol_cm = dragon["return_payload_vol"]["cubic_meters"]
                return_vol_cf = dragon["return_payload_vol"]["cubic_feet"]

                solar_arrays = dragon["trunk"]["cargo"]["solar_array"]

                height_w_trunk_m = dragon["height_w_trunk"]["meters"]
                height_w_trunk_f = dragon["height_w_trunk"]["feet"]

                diameter_m = dragon["diameter"]["meters"]
                diameter_f = dragon["diameter"]["feet"]

                first_flight = dragon["first_flight"]
                description = dragon["description"]
                image = dragon["flickr_images"][0]

                thruster1 = dragon["thrusters"][0]
                thruster1_type = thruster1["type"]
                thruster1_amount = thruster1["amount"]

                thruster2 = dragon["thrusters"][0]
                thruster2_type = thruster2["type"]
                thruster2_amount = thruster2["amount"]

                embed = discord.Embed(title="SpaceX Crew Dragon", color=discord.Colour.dark_blue())

                embed = embed.add_field(name="Launch payload mass",
                                        value=f"{launch_payload_kg} kg ({launch_payload_lb} lbs)")
                embed = embed.add_field(name="Launch payload volume",
                                        value=f"{launch_vol_cm} m² ({launch_vol_cf} f²)")
                embed = embed.add_field(name="Return payload mass",
                                        value=f"{return_payload_kg} kg ({return_payload_lb} lbs)")
                embed = embed.add_field(name="Return payload volume",
                                        value=f"{return_vol_cm} m² ({return_vol_cf} f²)")
                embed = embed.add_field(name="Height with trunk",
                                        value=f"{height_w_trunk_m} m ({height_w_trunk_f} f)")
                embed = embed.add_field(name="Diameter", value=f"{diameter_m} m ({diameter_f} f)")
                embed = embed.add_field(name="Thrusters",
                                        value=f"{thruster1_amount} {thruster1_type} thrusters, {thruster2_amount} {thruster2_type} thrusters")
                embed = embed.add_field(name="Solar arrays", value=solar_arrays)
                embed = embed.add_field(name="First flight", value=first_flight)
                embed = embed.add_field(name="Description", value=description)
                embed = embed.set_image(url=image)

            elif endpoint == "history":
                embed = discord.Embed(title="SpaceX history", color=discord.Colour.dark_blue())

                for launch in spacex["history"]:
                    details = launch["details"]
                    date = launch["event_date_utc"]
                    article = launch["links"]["article"]

                    embed = embed.add_field(name=launch["title"], value=f"{details}\n{article}\n{date}",
                                            inline=False)

            elif endpoint == "next":
                embed = discord.Embed(title=spacex["next"]["name"], color=discord.Colour.dark_blue())

                cast = spacex["next"]["links"]["webcast"]
                launch_date = spacex["next"]["date_utc"]
                description = spacex["next"]["details"]
                flight_number = spacex["next"]["flight_number"]
                try:
                    recovery_attempt_fairing = spacex["next"]["fairings"]["recovery_attempt"]
                except:
                    recovery_attempt_fairing = "unknown"
                core_reused = spacex["next"]["cores"][0]["reused"]
                landing_type = spacex["next"]["cores"][0]["landing_type"]
                landing_success = spacex["next"]["cores"][0]["landing_success"]

                if cast is None:
                    cast = "unknown"
                if launch_date is None:
                    launch_date = "unknown"
                if flight_number is None:
                    flight_number = "unknown"
                if recovery_attempt_fairing is None:
                    recovery_attempt_fairing = "unknown"
                if core_reused is None:
                    core_reused = "unknown"
                if landing_type is None:
                    landing_type = "unknown"
                if landing_success is None:
                    landing_success = "unknown"

                embed = embed.add_field(name="Launch date (UTC)", value=launch_date)
                embed = embed.add_field(name="Flight number", value=flight_number)
                embed = embed.add_field(name="Fairing recovery attempt", value=recovery_attempt_fairing)
                embed = embed.add_field(name="Booster reused", value=core_reused)
                embed = embed.add_field(name="Landing type", value=landing_type)
                embed = embed.add_field(name="Booster landing successful", value=landing_success)
                embed = embed.add_field(name="Cast", value=cast)

            elif endpoint == "starlink":
                try:
                    n = int(args[-1])
                except:
                    n = -1

                if len(spacex["starlink"]) >= n > 0:
                    sat = spacex["starlink"][n - 1]
                    embed = discord.Embed(title=f"Starlink satellite #{n}", color=discord.Colour.dark_blue())

                    embed = embed.add_field(name="Version", value=sat["version"])
                    embed = embed.add_field(name="Launch date", value=sat["spaceTrack"]["LAUNCH_DATE"])
                    embed = embed.add_field(name="Decay date", value=sat["spaceTrack"]["DECAY_DATE"])
                else:
                    lensats = len(spacex["starlink"])
                    embed = discord.Embed(title="Starlink",
                                          description=f"{lensats - 1} satellites\n\nFor more info on a satellite, use "
                                                      f"`{credentials['prefix']}spacex starlink <n>`. For example: `{credentials['prefix']}spacex starlink 500`",
                                          color=discord.Colour.dark_blue())
            else:
                raise commands.errors.BadArgument(f'Invalid endpoint "{endpoint}"')

        else:
            embed = discord.Embed(title="SpaceX", description="The following endpoints are available.",
                                  color=discord.Colour.dark_blue())
            embed.add_field(name="Company", value="Get general information about SpaceX.")
            embed.add_field(name="Boosters", value="Get information about SpaceX's boosters.")
            embed.add_field(name="Dragon", value="Get information about crew dragon.")
            embed.add_field(name="History", value="View SpaceX's past achievements.")
            embed.add_field(name="Next", value="Get information about SpaceX's next mission.")
            embed.add_field(name="Starlink", value="Get information about starlink.")
            embed.add_field(name="Usage", value=f"Use `{credentials['prefix']}spacex <endpoint>` to access endpoints.", inline=False)

        embed.set_footer(text=f"Information last updated {last_updated} UTC")
        await ctx.send(embed=embed)


def syncdata(bot):
    global botdata
    global facts
    global nasalinks
    global apod
    global spacex

    credentials = json.load(open("data/credentials.json"))
    slapgifs, fightgifs, facts, nasalinks = getdata()
    count = 60

    while True:
        if count >= 60:
            _apod = apod
            _spacex = spacex
            count = 0
            try:
                apod, spacex = spacex_data()
            except Exception as error:
                error = "".join(traceback.format_exception(type(error), error, error.__traceback__))
                bot.loop.create_task(bot.get_channel(credentials["log_channel"]).send(f"```python\n{error}```"))
                spacex = _spacex
                apod = _apod

        count += 1
        time.sleep(5)


def setup(bot: commands.Bot):
    global botdata
    global credentials

    bot.add_cog(space(bot))
    botdata = loadconfig()
    credentials = json.load(open("data/credentials.json"))
    threading.Thread(target=syncdata, args=(bot,)).start()
