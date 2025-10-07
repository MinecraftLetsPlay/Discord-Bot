import discord
import logging
import os
import aiohttp
from datetime import datetime
from dotenv import load_dotenv
from internal import utils

# Load environment variables from .env file
load_dotenv()
NASA_API_KEY = os.getenv('NASA_API_KEY')

async def handle_sciencecific_commands(client, message, user_message):
    # !apod
    if user_message.startswith('!apod'):
        url = f'https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}'
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    embed = discord.Embed(
                        title=data.get('title', 'Astronomy Picture of the Day'),
                        description=data.get('explanation', 'No explanation available.'),
                        color=discord.Color.blue()
                    )
                    embed.set_image(url=data.get('url'))
                    embed.set_footer(text=f"Date: {data.get('date', '')} | Copyright: {data.get('copyright', 'NASA')}")
                    await message.channel.send(embed=embed)
                    logging.info("Displayed APOD")
                else:
                    await message.channel.send("❌ Could not fetch APOD from NASA API.")
                    logging.error(f"APOD API error: {response.status}")
        return

    # !marsphoto command
    if user_message.startswith('!marsphoto'):
        parts = user_message.split()
        # Default values
        rover = "curiosity"
        date = datetime.now().strftime('%Y-%m-%d')

        # Check if arguments are provided
        if len(parts) == 2:
            # Check if the argument is a rover name or a date
            if parts[1].lower() in ["curiosity", "spirit"]:
                rover = parts[1].lower()
            else:
                date = parts[1]
        elif len(parts) >= 3:
            rover = parts[1].lower()
            date = parts[2]
        else:
            await message.channel.send("❌ Usage: `!marsphoto [rover] [YYYY-MM-DD]` (rover: curiosity, spirit)")
            return
            
        # Build URL and fetch data

        url = f'https://api.nasa.gov/mars-photos/api/v1/rovers/{rover}/photos?earth_date={date}&api_key={NASA_API_KEY}'
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    photos = data.get('photos', [])
                    if photos:
                        import random
                        photo = random.choice(photos)
                        embed = discord.Embed(
                            title=f"Mars Rover Photo ({photo['rover']['name']})",
                            description=f"Camera: {photo['camera']['full_name']}\nDate: {photo['earth_date']}",
                            color=discord.Color.red()
                        )
                        embed.set_image(url=photo['img_src'])
                        await message.channel.send(embed=embed)
                        logging.info(f"Displayed Mars photo from {rover} on {date}")
                    else:
                        await message.channel.send(f"❌ No photos found for {rover.title()} on {date}.")
                else:
                    await message.channel.send("❌ Could not fetch Mars photo from NASA API.")
                    logging.error(f"Mars photo API error: {response.status}")
        return


    if user_message.startswith('!asteroids'):
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={today}&end_date={today}&api_key={NASA_API_KEY}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        neos = []
                        # The API returns a dictionary with dates as keys
                        for date_key in data.get("near_earth_objects", {}):
                            neos.extend(data["near_earth_objects"][date_key])
                        if not neos:
                            await message.channel.send("☄️ No near-Earth asteroids found for today!")
                            return
                        # Sort by distance
                        neos.sort(key=lambda n: float(n["close_approach_data"][0]["miss_distance"]["kilometers"]))
                        # Next 5 ones
                        embed = discord.Embed(
                            title="☄️ Next 5 Near-Earth Asteroids",
                            description=f"Found for {today}",
                            color=discord.Color.orange()
                        )
                        for neo in neos[:5]:
                            name = neo["name"]
                            size = neo["estimated_diameter"]["meters"]
                            diameter = f"{size['estimated_diameter_min']:.1f}–{size['estimated_diameter_max']:.1f} m"
                            miss_distance = float(neo["close_approach_data"][0]["miss_distance"]["kilometers"])
                            velocity = float(neo["close_approach_data"][0]["relative_velocity"]["kilometers_per_hour"])
                            hazardous = "⚠️" if neo["is_potentially_hazardous_asteroid"] else ""
                            abs_mag = neo.get("absolute_magnitude_h", "N/A")
                            approach_date = neo["close_approach_data"][0]["close_approach_date"]
                            orbiting_body = neo["close_approach_data"][0]["orbiting_body"]
                            jpl_url = neo.get("nasa_jpl_url", "")
                            embed.add_field(
                                name=f"{name} {hazardous}",
                                value=(
                                    f"Size: {diameter}\n"
                                    f"Absolute Magnitude: {abs_mag}\n"
                                    f"Distance: {miss_distance:,.0f} km\n"
                                    f"Velocity: {velocity:,.0f} km/h\n"
                                    f"Approach Date: {approach_date}\n"
                                    f"Orbiting Body: {orbiting_body}\n"
                                ),
                                inline=False
                            )
                        await message.channel.send(embed=embed)
                        logging.info("Displayed asteroid data")
                    else:
                        await message.channel.send("❌ Error fetching asteroid data from NASA API.")
        except Exception as e:
            await message.channel.send("❌ Error processing asteroid data.")
            logging.error(f"Asteroids command error: {e}")
        return

    if user_message.startswith('!sun'):
        await message.channel.send("🌞 Sun command coming soon!")
        return

    if user_message.startswith('!exoplanet'):
        await message.channel.send("🪐 Exoplanet command coming soon!")
        return
