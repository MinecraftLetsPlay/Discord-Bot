import discord
import logging
import os
import aiohttp
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# ----------------------------------------------------------------
# Helper Functions
# ----------------------------------------------------------------

# Load environment variables from .env file
load_dotenv()
NASA_API_KEY = os.getenv('NASA_API_KEY')

async def component_test():
    status = "🟩"
    messages = ["Sciencecific commands module loaded."]

    # Test 1: OPENWEATHERMAP_API_KEY present?
    if not os.getenv("NASA_API_KEY"):
        status = "🟧"
        messages.append("Warning: NASA_API_KEY not present in .env file.")
        
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.nasa.gov/planetary/apod', timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 403:
                    messages.append("NASA API reachable.")
                else:
                    status = "🟧"
                    messages.append(f"NASA API error: Status {response.status}")

    except Exception as e:
        status = "🟧"
        messages.append(f"API not reachable: {e}")
        
    return {"status": status, "msg": " | ".join(messages)}

# ----------------------------------------------------------------
# Main Command Handler
# ----------------------------------------------------------------

async def handle_sciencecific_commands(client, message, user_message):
    
    # ----------------------------------------------------------------
    # Command: !apod
    # Category: Scientific Commands
    # Type: Full Command
    # ----------------------------------------------------------------
    
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

    # ----------------------------------------------------------------
    # Command: !marsphoto [rover] [date]
    # Category: Scientific Commands
    # Type: Full Command
    # ----------------------------------------------------------------
    
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

    # ----------------------------------------------------------------
    # Command: !asteroids
    # Category: Scientific Commands
    # Type: Full Command
    # ----------------------------------------------------------------
    
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

    # ----------------------------------------------------------------
    # Command: !sun
    # Category: Scientific Commands
    # Type: <Placeholder>
    # ----------------------------------------------------------------
    
    if user_message.startswith('!sun'):
        try:
            args = user_message.split()
            today = datetime.utcnow().strftime("%Y-%m-%d")

            endpoints = {
                "cme": "CME",
                "flare": "FLR",
                "storm": "GST",
                "shock": "IPS",
                "particle": "SEP"
            }

            base_url = "https://api.nasa.gov/DONKI/"
            selected = args[1].lower() if len(args) > 1 else "all"
            results = []

            async with aiohttp.ClientSession() as session:
                # fetch single or all endpoints
                endpoints_to_fetch = (
                    {selected: endpoints[selected]} if selected in endpoints else endpoints
                )
                for key, endpoint in endpoints_to_fetch.items():
                    url = f"{base_url}{endpoint}?startDate={today}&api_key={NASA_API_KEY}"
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            results.append((endpoint, data))
                        else:
                            logging.warning(f"NASA API {endpoint} returned {resp.status}")
                    await asyncio.sleep(0.25)

            embed = discord.Embed(
                title="🌞 Solar Activity Overview",
                description=f"Space weather events for **{today} UTC**",
                color=discord.Color.gold()
            )

            total_events = 0
            for endpoint, data in results:
                if not data:
                    continue

                total_events += len(data)

                for idx, event in enumerate(data[:2]):  # max. 2 Events pro Typ
                    start = event.get("startTime") or event.get("beginTime") or "Unknown"
                    note = event.get("note", "")
                    link = event.get("link", "")
                    field_title = f"{endpoint} #{idx + 1}"

                    # Extra Infos, wenn vorhanden
                    extras = []
                    if "speed" in event:
                        extras.append(f"🚀 **Speed:** {event['speed']} km/s")
                    if "latitude" in event and "longitude" in event:
                        extras.append(f"📍 **Direction:** {event['latitude']}, {event['longitude']}")
                    if "sourceLocation" in event:
                        extras.append(f"☀️ **Source Region:** {event['sourceLocation']}")
                    if "activeRegionNum" in event:
                        extras.append(f"🔢 **Active Region:** {event['activeRegionNum']}")

                    # Fallback für „CME Analyses“ (Detaildaten in separatem Array)
                    if "cmeAnalyses" in event and event["cmeAnalyses"]:
                        analysis = event["cmeAnalyses"][0]
                        if analysis.get("speed"):
                            extras.append(f"💨 **Analysis Speed:** {analysis['speed']} km/s")
                        if analysis.get("type"):
                            extras.append(f"🧭 **CME Type:** {analysis['type']}")
                        if analysis.get("note"):
                            extras.append(f"📄 {analysis['note'][:150]}...")

                    details = f"🕓 **Start:** {start}\n"
                    if note:
                        details += f"🧾 {note[:300]}...\n"
                    if extras:
                        details += "\n".join(extras) + "\n"
                    if link:
                        details += f"[More Info]({link})"

                    embed.add_field(name=field_title, value=details, inline=False)

            if total_events == 0:
                embed.description = (embed.description or "") + "\n✅ No solar events recorded today. The Sun is calm."
            else:
                embed.set_footer(
                    text=f"Data source: NASA DONKI • {datetime.utcnow().strftime('%H:%M:%S')} UTC"
                )

            await message.channel.send(embed=embed)

        except Exception as e:
            await message.channel.send("❌ Error while fetching solar activity data.")
            logging.exception("Sun command error: %s", e)

    
    # ----------------------------------------------------------------
    # Command: !exoplanet
    # Category: Scientific Commands
    # Type: <Placeholder>
    # ----------------------------------------------------------------
    
    if user_message.startswith('!exoplanet'):
        await message.channel.send("🪐 Exoplanet command coming soon!")
        return
