import discord
import logging
import os
import io
import csv
import aiohttp
import asyncio
import urllib.parse
from datetime import datetime, timezone
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
    # Get the astronomy picture of the day from NASA
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
    # Get a random Mars rover photo from NASA
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
    # Get near-Earth asteroids from NASA
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
    # Type: Full Command
    # Get recent solar activity from NASA
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
                # Fetch single or all endpoints
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
                            message.channel.send(f"❌ Error fetching {endpoint} data from NASA API.")
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

                    # Extra details based on event type
                    extras = []
                    if "speed" in event:
                        extras.append(f"🚀 **Speed:** {event['speed']} km/s")
                    if "latitude" in event and "longitude" in event:
                        extras.append(f"📍 **Direction:** {event['latitude']}, {event['longitude']}")
                    if "sourceLocation" in event:
                        extras.append(f"☀️ **Source Region:** {event['sourceLocation']}")
                    if "activeRegionNum" in event:
                        extras.append(f"🔢 **Active Region:** {event['activeRegionNum']}")

                    # Fallback for „CME Analyses“
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
                    text=f"Data source: NASA DONKI • {datetime.now(timezone.utc).strftime('%H:%M:%S')} UTC"
                )

            await message.channel.send(embed=embed)
            logging.info("Displayed solar activity data")

        except Exception as e:
            await message.channel.send("❌ Error while fetching solar activity data.")
            logging.exception("Sun command error: %s", e)
        return
    
    # ----------------------------------------------------------------
    # Command: !exoplanet <name|nearest|latest|count>
    # Category: Scientific Commands
    # Type: Full Command
    # Get data about exoplanets from NASA Exoplanet Archive
    # ----------------------------------------------------------------

    if user_message.startswith('!exoplanet'):
        parts = user_message.split(maxsplit=1)

        # Function: Determine habitability based on extended criteria
        async def is_habitable(planet):
            try:
                def safe_float(value):
                    try:
                        return float(value) if value not in (None, '', ' ') else 0.0
                    except ValueError:
                        return 0.0

                radius = safe_float(planet.get('pl_rade'))
                mass = safe_float(planet.get('pl_bmasse'))
                temp = safe_float(planet.get('pl_eqt'))

                if radius == 0 or temp == 0:
                    logging.debug(f"Skipping incomplete habitability check for {planet.get('pl_name', 'Unknown')}")
                    return False

                return (
                    0.8 <= radius <= 1.8 and
                    (mass == 0 or mass <= 10) and
                    180 <= temp <= 310
                )

            except Exception as e:
                logging.warning(f"Habitable check failed for planet: {planet.get('pl_name', 'Unknown')} ({e})")
                return False


        try:
            if len(parts) == 2 and parts[1].lower() == "count":
                sql = "SELECT count(distinct pl_name) as total FROM ps"
                url = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query=" + urllib.parse.quote(sql) + "&format=csv"

                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        if response.status != 200:
                            raise Exception(f"API returned {response.status}")
                        text = await response.text()
                        reader = csv.DictReader(io.StringIO(text))
                        data = list(reader)
                        total = int(data[0].get("total", 0))
                        await message.channel.send(f"🪐 There are currently **{total:,}** confirmed exoplanets in NASA's Exoplanet Archive.")
                        logging.info("Displayed exoplanet count")
                return

            # Show nearest known exoplanets
            if len(parts) == 2 and parts[1].lower() == "nearest":
                query = (
                    "SELECT DISTINCT pl_name, hostname, disc_year, sy_dist, pl_rade, pl_bmasse, pl_eqt, discoverymethod "
                    "FROM ps WHERE sy_dist IS NOT NULL ORDER BY sy_dist ASC"
                )
                url = (
                    "https://exoplanetarchive.ipac.caltech.edu/TAP/sync?"
                    f"query={query.replace(' ', '+')}&format=csv&MAXREC=20"
                )

                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        if response.status != 200:
                            raise Exception(f"API returned {response.status}")

                        text = await response.text()
                        reader = csv.DictReader(io.StringIO(text))
                        results = list(reader)

                        # Filter to unique planet names
                        seen = set()
                        unique_planets = []
                        for planet in results:
                            name = planet.get("pl_name")
                            if name and name not in seen:
                                unique_planets.append(planet)
                                seen.add(name)
                            if len(unique_planets) >= 5:
                                break

                        if not unique_planets:
                            await message.channel.send("❌ No nearby exoplanets found.")
                            return

                        embed = discord.Embed(
                            title="🪐 Nearest Known Exoplanets",
                            color=discord.Color.orange()
                        )

                        for p in unique_planets:
                            dist_display = "N/A"
                            temp_str = "N/A"
                            habitable = False
                            
                            try:
                                # Read and convert values
                                radius = float(p.get("pl_rade") or 0)
                                mass = float(p.get("pl_bmasse") or 0)
                                temp_k = float(p.get("pl_eqt") or 0)

                                # Kelvin → Celsius
                                temp_c = temp_k - 273.15 if temp_k else None
                                dist_pc = float(p.get("sy_dist") or 0)
                                dist_ly = dist_pc * 3.26156 if dist_pc else None
                                
                                if temp_k:
                                    temp_str = f"{temp_k:.2f} K ({temp_c:.1f} °C)" if temp_c is not None else "N/A"
                                if temp_k:
                                    dist_display = f"{dist_pc:.2f} pc (≈ {dist_ly:.2f} ly)" if dist_pc is not None else "N/A"

                                # Habitability Check (in °C)
                                habitable = (
                                    0.8 <= radius <= 1.8 and
                                    (mass == 0 or mass <= 10) and
                                    (temp_c is not None and -93 <= temp_c <= 37)
                                )
                            except Exception as e:
                                habitable = False
                                temp_str = "N/A"
                                logging.warning(f"Habitable check failed for planet: {p.get('pl_name', 'Unknown')} ({e})")

                            embed.add_field(
                                name=p.get("pl_name", "Unknown"),
                                value=(
                                    f"Host Star: {p.get('hostname', 'N/A')}\n"
                                    f"Discovery: {p.get('disc_year', 'N/A')} ({p.get('discoverymethod', 'N/A')})\n"
                                    f"Distance: {dist_display}\n"
                                    f"Radius: {p.get('pl_rade', 'N/A')} R⊕\n"
                                    f"Mass: {p.get('pl_bmasse', 'N/A')} M⊕\n"
                                    f"Temperature: {temp_str}\n"
                                    f"Habitable: {'✅ Possibly' if habitable else '❌ Unlikely'}"
                                ),
                                inline=False
                            )

                        await message.channel.send(embed=embed)
                        logging.info("Displayed nearest unique exoplanets")
                    return

            # Latest discovered exoplanets
            if len(parts) == 2 and parts[1].lower() == "latest":
                query = (
                    "SELECT pl_name, hostname, disc_year, sy_dist, pl_rade, pl_bmasse, pl_eqt, discoverymethod "
                    "FROM ps WHERE disc_year IS NOT NULL ORDER BY disc_year DESC"
                )
                url = (
                    "https://exoplanetarchive.ipac.caltech.edu/TAP/sync?"
                    f"query={query.replace(' ', '+')}&format=csv&MAXREC=20"
                )

                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        if response.status != 200:
                            raise Exception(f"API returned {response.status}")

                        text = await response.text()
                        reader = csv.DictReader(io.StringIO(text))
                        results = list(reader)

                        # No results check
                        if not results:
                            await message.channel.send("❌ No exoplanet data found.")
                            return

                        # Only 5 newest unique planet names
                        seen = set()
                        unique_planets = []
                        for planet in results:
                            name = planet.get("pl_name")
                            if name and name not in seen:
                                unique_planets.append(planet)
                                seen.add(name)
                            if len(unique_planets) >= 5:
                                break

                        embed = discord.Embed(
                            title="🪐 Latest Discovered Exoplanets",
                            color=discord.Color.purple()
                        )

                        for p in unique_planets:
                            dist_display = "N/A"
                            temp_str = "N/A"
                            habitable = False

                            try:
                                # Parse data
                                radius = float(p.get("pl_rade") or 0)
                                mass = float(p.get("pl_bmasse") or 0)
                                temp_k = float(p.get("pl_eqt") or 0)

                                # Kelvin → Celsius
                                temp_c = temp_k - 273.15 if temp_k else None
                                dist_pc = float(p.get("sy_dist") or 0)
                                dist_ly = dist_pc * 3.26156 if dist_pc else None

                                if temp_k:
                                    temp_str = f"{temp_k:.2f} K ({temp_c:.1f} °C)" if temp_c is not None else "N/A"
                                if dist_pc:
                                    dist_display = f"{dist_pc:.2f} pc (≈ {dist_ly:.2f} ly)" if dist_ly is not None else "N/A"

                                # Habitability Check (°C)
                                habitable = (
                                    0.8 <= radius <= 1.8 and
                                    (mass == 0 or mass <= 10) and
                                    (temp_c is not None and -93 <= temp_c <= 37)
                                )
                            except Exception as e:
                                habitable = False
                                temp_str = "N/A"
                                logging.warning(f"Habitable check failed for planet: {p.get('pl_name', 'Unknown')} ({e})")

                            embed.add_field(
                                name=p.get("pl_name", "Unknown"),
                                value=(
                                    f"Host Star: {p.get('hostname', 'N/A')}\n"
                                    f"Discovery: {p.get('disc_year', 'N/A')} ({p.get('discoverymethod', 'N/A')})\n"
                                    f"Distance: {dist_display}\n"
                                    f"Radius: {p.get('pl_rade', 'N/A')} R⊕\n"
                                    f"Mass: {p.get('pl_bmasse', 'N/A')} M⊕\n"
                                    f"Temperature: {temp_str}\n"
                                    f"Habitable: {'✅ Possibly' if habitable else '❌ Unlikely'}"
                                ),
                                inline=False
                            )

                        await message.channel.send(embed=embed)
                        logging.info("Displayed latest discovered unique exoplanets")
                return

            # Specific exoplanet search
            if len(parts) >= 2:
                planet_name = " ".join(parts[1:])  # Falls der Name Leerzeichen enthält
                # Entferne Trennzeichen und bereite flexible Suche vor
                search_key = planet_name.replace("-", "").replace(" ", "")

                # SQL: Ignoriere Leerzeichen und Bindestriche im Vergleich
                query = (
                    "SELECT DISTINCT pl_name, hostname, disc_year, sy_dist, pl_rade, pl_bmasse, pl_eqt, discoverymethod "
                    "FROM ps WHERE REPLACE(REPLACE(pl_name, '-', ''), ' ', '') "
                    f"LIKE '%{search_key}%'"
                )

                url = (
                    "https://exoplanetarchive.ipac.caltech.edu/TAP/sync?"
                    f"query={urllib.parse.quote(query)}&format=csv&MAXREC=3"
                )

                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        if response.status != 200:
                            raise Exception(f"API returned {response.status}")
                        text = await response.text()
                        reader = csv.DictReader(io.StringIO(text))
                        results = list(reader)

                        if not results:
                            await message.channel.send(f"❌ No exoplanet found matching '{planet_name}'.")
                            return

                        # Nimm den ersten Treffer
                        p = results[0]

                        # Temperatur & Distanz konvertieren
                        dist_display = "N/A"
                        temp_str = "N/A"
                        habitable = False

                        try:
                            radius = float(p.get("pl_rade") or 0)
                            mass = float(p.get("pl_bmasse") or 0)
                            temp_k = float(p.get("pl_eqt") or 0)

                            temp_c = temp_k - 273.15 if temp_k else None
                            dist_pc = float(p.get("sy_dist") or 0)
                            dist_ly = dist_pc * 3.26156 if dist_pc else None

                            if dist_pc:
                                dist_display = f"{dist_pc:.2f} pc (≈ {dist_ly:.2f} ly)"
                            if temp_k:
                                temp_str = f"{temp_k:.2f} K ({temp_c:.1f} °C)" if temp_c is not None else "N/A"

                            habitable = (
                                0.8 <= radius <= 1.8 and
                                (mass == 0 or mass <= 10) and
                                (temp_c is not None and -93 <= temp_c <= 37)
                            )
                        except Exception as e:
                            habitable = False
                            logging.warning(f"Habitable check failed for planet: {p.get('pl_name', 'Unknown')} ({e})")

                        # Embed formatieren
                        embed = discord.Embed(
                            title=f"🪐 {p.get('pl_name', 'Unknown')}",
                            color=discord.Color.blurple()
                        )
                        embed.add_field(name="Host Star", value=p.get("hostname", "N/A"))
                        embed.add_field(name="Discovery Year", value=p.get("disc_year", "N/A"))
                        embed.add_field(name="Method", value=p.get("discoverymethod", "N/A"))
                        embed.add_field(name="Distance", value=dist_display)
                        embed.add_field(name="Radius", value=f"{p.get('pl_rade', 'N/A')} R⊕")
                        embed.add_field(name="Mass", value=f"{p.get('pl_bmasse', 'N/A')} M⊕")
                        embed.add_field(name="Temperature", value=temp_str)
                        embed.add_field(name="Habitable", value="✅ Possibly" if habitable else "❌ Unlikely")

                        await message.channel.send(embed=embed)
                        logging.info(f"Displayed exoplanet data for '{planet_name}'")
                return
        except Exception as e:
            await message.channel.send("❌ Error while fetching exoplanet data.")
            logging.exception("Exoplanet command error: %s", e)
