import discord
import aiohttp
import json
import os
from datetime import datetime, timezone, timedelta
from internal import utils
from dotenv import load_dotenv
import logging
from discord.ext import commands
from discord.ui import Button, View
import asyncio

#
#
# Utility commands
#
#

# Load environment variables from .env file
load_dotenv()

# Store the bot start time
bot_start_time = datetime.now(timezone.utc)

# Dictionary to map country codes to full country names
# Dictionary to map country codes to full country names
country_names = {
    "AF": "Afghanistan", "AL": "Albania", "DZ": "Algeria", "AD": "Andorra", "AO": "Angola", "AG": "Antigua and Barbuda", "AR": "Argentina", "AM": "Armenia", "AU": "Australia", "AT": "Austria", 
    
    "AZ": "Azerbaijan", "BS": "Bahamas", "BH": "Bahrain", "BD": "Bangladesh", "BB": "Barbados", "BY": "Belarus", "BE": "Belgium", "BZ": "Belize", "BJ": "Benin", "BT": "Bhutan", "BO": "Bolivia",
    
    "BA": "Bosnia and Herzegovina", "BW": "Botswana", "BR": "Brazil", "BN": "Brunei", "BG": "Bulgaria", "BF": "Burkina Faso", "BI": "Burundi", "CV": "Cabo Verde", "KH": "Cambodia", 
    
    "CM": "Cameroon", "CA": "Canada", "CF": "Central African Republic", "TD": "Chad", "CL": "Chile", "CN": "China", "CO": "Colombia", "KM": "Comoros", "CG": "Congo",
    
    "CD": "Congo (Democratic Republic)", "CR": "Costa Rica", "CI": "Côte d'Ivoire", "HR": "Croatia", "CU": "Cuba", "CY": "Cyprus", "CZ": "Czech Republic", "DK": "Denmark", "DJ": "Djibouti",
    
    "DM": "Dominica", "DO": "Dominican Republic", "EC": "Ecuador", "EG": "Egypt", "SV": "El Salvador", "GQ": "Equatorial Guinea", "ER": "Eritrea", "EE": "Estonia", "SZ": "Eswatini", 
    
    "ET": "Ethiopia", "FJ": "Fiji", "FI": "Finland", "FR": "France", "GA": "Gabon", "GM": "Gambia", "GE": "Georgia", "DE": "Germany", "GH": "Ghana", "GR": "Greece", "GD": "Grenada",
    
    "GT": "Guatemala", "GN": "Guinea", "GW": "Guinea-Bissau", "GY": "Guyana", "HT": "Haiti", "HN": "Honduras", "HU": "Hungary", "IS": "Iceland", "IN": "India", "ID": "Indonesia", "IR": "Iran", 
    
    "IQ": "Iraq", "IE": "Ireland", "IL": "Israel", "IT": "Italy", "JM": "Jamaica", "JP": "Japan", "JO": "Jordan", "KZ": "Kazakhstan", "KE": "Kenya", "KI": "Kiribati", "KP": "North Korea", 
    
    "KR": "South Korea", "KW": "Kuwait", "KG": "Kyrgyzstan", "LA": "Laos", "LV": "Latvia", "LB": "Lebanon", "LS": "Lesotho", "LR": "Liberia", "LY": "Libya", "LI": "Liechtenstein", 
    
    "LT": "Lithuania", "LU": "Luxembourg", "MG": "Madagascar", "MW": "Malawi", "MY": "Malaysia", "MV": "Maldives", "ML": "Mali", "MT": "Malta", "MH": "Marshall Islands", 
    
    "MR": "Mauritania", "MU": "Mauritius", "MX": "Mexico", "FM": "Micronesia", "MD": "Moldova", "MC": "Monaco", "MN": "Mongolia", "ME": "Montenegro", "MA": "Morocco", "MZ": "Mozambique",
    
    "MM": "Myanmar", "NA": "Namibia", "NR": "Nauru", "NP": "Nepal", "NL": "Netherlands", "NZ": "New Zealand", "NI": "Nicaragua", "NE": "Niger", "NG": "Nigeria", "MK": "North Macedonia", 
    
    "NO": "Norway", "OM": "Oman", "PK": "Pakistan", "PW": "Palau", "PA": "Panama", "PG": "Papua New Guinea", "PY": "Paraguay", "PE": "Peru", "PH": "Philippines", "PL": "Poland",
    
    "PT": "Portugal", "QA": "Qatar", "RO": "Romania", "RU": "Russia", "RW": "Rwanda", "KN": "Saint Kitts and Nevis", "LC": "Saint Lucia", "VC": "Saint Vincent and the Grenadines", 
    
    "WS": "Samoa", "SM": "San Marino", "ST": "São Tomé and Príncipe", "SA": "Saudi Arabia", "SN": "Senegal", "RS": "Serbia", "SC": "Seychelles", "SL": "Sierra Leone", "SG": "Singapore", 
    
    "SK": "Slovakia", "SI": "Slovenia", "SB": "Solomon Islands", "SO": "Somalia", "ZA": "South Africa", "SS": "South Sudan", "ES": "Spain", "LK": "Sri Lanka", "SD": "Sudan", "SR": "Suriname",
    
    "SE": "Sweden", "CH": "Switzerland", "SY": "Syria", "TJ": "Tajikistan", "TZ": "Tanzania", "TH": "Thailand", "TL": "Timor-Leste", "TG": "Togo", "TO": "Tonga", "TT": "Trinidad and Tobago",
    
    "TN": "Tunisia", "TR": "Turkey", "TM": "Turkmenistan", "TV": "Tuvalu", "UG": "Uganda", "UA": "Ukraine", "AE": "United Arab Emirates", "GB": "United Kingdom", "US": "United States", 
    
    "UY": "Uruguay", "UZ": "Uzbekistan", "VU": "Vanuatu", "VE": "Venezuela", "VN": "Vietnam", "YE": "Yemen", "ZM": "Zambia", "ZW": "Zimbabwe"
}

# Main def for handling utility commands
async def handle_utility_commands(client, message, user_message):

    # !ping command
    if user_message == '!ping':
        latency = round(client.latency * 1000)  # Latency in milliseconds
        await message.channel.send(f'Pong! Latency is {latency}ms')
        logging.info(f"Pong! Latency is {latency}ms")

    # !uptime command
    if user_message == '!uptime':
        current_time = datetime.now(timezone.utc)
        uptime_duration = current_time - bot_start_time
        days, seconds = uptime_duration.days, uptime_duration.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        uptime_message = f"Uptime: {days}d {hours}h {minutes}m {seconds}s"
        await message.channel.send(uptime_message)
        logging.info(f"Uptime: {days}d {hours}h {minutes}m {seconds}s")

    # !weather command
    def load_config():
        try:
            with open('config.json', 'r') as file:
                return json.load(file)
        except Exception as e:
            logging.error(f"❌ Error loading config file: {e}")
            return {}

    # Asynchronous function to get weather data
    async def get_weather(location):
        api_key = os.getenv('OPENWEATHERMAP_API_KEY')  # Get the API key from .env

        if not api_key:
            logging.error("❌ API key is missing.")
            return None

        base_url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url) as response:
                return await response.json()

    # Function to convert wind direction in degrees to compass direction
    def wind_direction(degrees):
        directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
        index = round(degrees / 22.5) % 16
        return directions[index]

    # Handling the '!weather' command
    if user_message.startswith('!weather'):
        location = user_message.split(' ', 1)[1] if len(user_message.split()) > 1 else 'London'
        weather_data = await get_weather(location)

        if weather_data and weather_data['cod'] == 200:
            # Extract data from the weather response
            city_name = weather_data['name']
            country = weather_data['sys']['country']
            temp = weather_data['main']['temp']
            temp_min = weather_data['main']['temp_min']
            temp_max = weather_data['main']['temp_max']
            description = weather_data['weather'][0]['description']
            humidity = weather_data['main']['humidity']
            pressure = weather_data['main']['pressure']
            wind_speed = weather_data['wind']['speed']
            wind_deg = weather_data['wind']['deg']
            wind_dir = wind_direction(wind_deg)  # Convert wind degrees to compass direction

            # Determine embed color based on weather description
            if 'clear' in description or 'sun' in description:
                embed_color = discord.Color.gold()  # Sunny or clear
            elif 'rain' in description:
                embed_color = discord.Color.blue()  # Rainy
            elif 'storm' in description or 'thunder' in description:
                embed_color = discord.Color.dark_gray()  # Thunderstorm
            elif 'cloud' in description:
                embed_color = discord.Color.light_gray()  # Cloudy weather
            elif 'snow' in description:
                embed_color = discord.Color.from_rgb(255, 255, 255)  # Snow
            elif 'fog' in description or 'mist' in description:
                embed_color = discord.Color.light_gray()  # Foggy or misty
            elif 'drizzle' in description:
                embed_color = discord.Color.sky_blue()  # Drizzle
            elif 'extreme' in description or 'hurricane' in description or 'tornado' in description:
                embed_color = discord.Color.purple()  # Extreme weather
            else:
                embed_color = discord.Color.default()  # Default color

            # Create an embed message
            embed = discord.Embed(title=f"Weather in {city_name}, {country}", color=embed_color)
            embed.add_field(name="Temperature", value=f"{temp}°C", inline=False)
            embed.add_field(name="Min / Max Temperature", value=f"{temp_min}°C / {temp_max}°C", inline=False)
            embed.add_field(name="Description", value=description.capitalize(), inline=False)
            embed.add_field(name="Humidity", value=f"{humidity}%", inline=False)
            embed.add_field(name="Pressure", value=f"{pressure} hPa", inline=False)
            embed.add_field(name="Wind", value=f"{wind_speed} m/s, {wind_deg}° ({wind_dir})", inline=False)

            # Send the embed message
            await message.channel.send(embed=embed)
            logging.info(f"Displayed weather information for {city_name}, {country}.")
        else:
            await message.channel.send("⚠️ Could not retrieve weather information. Make sure the location is valid.")
            logging.warning("⚠️ Could not retrieve weather information. Invalid location.")

    # !city command
    if user_message.startswith('!city'):
        location = user_message.split(' ', 1)[1] if len(user_message.split()) > 1 else 'London'
        weather_data = await get_weather(location)

        if weather_data and weather_data['cod'] == 200:
            # Extract data from the weather response
            city_name = weather_data['name']
            country_code = weather_data['sys']['country']  # Country code
            country = country_names.get(country_code, country_code)  # Get full country name or use code if not found
            coords = weather_data['coord']
            sea_level = weather_data['main'].get('sea_level', 'N/A')  # Use 'N/A' if sea_level is not provided
            ground_level = weather_data['main'].get('grnd_level', 'N/A')  # Use 'N/A' if grnd_level is not provided
            timezone_offset = weather_data['timezone']
            timezone_offset_hours = timezone_offset / 3600  # Divide by 3600 to convert seconds to hours
            timezone_offset_formatted = f"{timezone_offset_hours:+.1f} hours"  # Add "+" for positive offsets

            # Convert sunrise and sunset timestamps to readable times
            sunrise_unix = weather_data['sys']['sunrise']
            sunset_unix = weather_data['sys']['sunset']
            sunrise_time = datetime.fromtimestamp(sunrise_unix, tz=timezone.utc).strftime('%H:%M:%S UTC')
            sunset_time = datetime.fromtimestamp(sunset_unix, tz=timezone.utc).strftime('%H:%M:%S UTC')

            # Calculate the local time of the city
            local_time = datetime.now(timezone.utc) + timedelta(seconds=timezone_offset)
            local_time_formatted = local_time.strftime('%Y-%m-%d %H:%M:%S')

            # Create the embed message
            embed = discord.Embed(title=f"Information for: {city_name}, {country_code}", color=discord.Color.blue())
            embed.add_field(name="City", value=city_name, inline=False)
            embed.add_field(name="Country", value=country, inline=False)
            embed.add_field(name="Latitude", value=coords['lat'], inline=False)
            embed.add_field(name="Longitude", value=coords['lon'], inline=False)
            embed.add_field(name="Sea Level", value=f"{sea_level} m", inline=False)
            embed.add_field(name="Ground Level", value=f"{ground_level} m", inline=False)
            embed.add_field(name="Timezone Offset", value=timezone_offset_formatted, inline=False)
            embed.add_field(name="Local Date/Time (City)", value=local_time_formatted, inline=False)
            embed.add_field(name="Sunrise", value=sunrise_time, inline=False)
            embed.add_field(name="Sunset", value=sunset_time, inline=False)

            # Send the embed message
            await message.channel.send(embed=embed)
            logging.info(f"Displayed city information for {city_name}, {country}.")
        else:
            await message.channel.send("⚠️ Could not retrieve city information. Make sure the location is valid.")
            logging.warning("⚠️ Could not retrieve city information. Invalid location.")

    # !download command
    async def handle_download_command(user_message):
        config = utils.load_config()
        download_folders = config.get("download_folders", {})

        # Split the command into parts
        parts = user_message.split(' ', 2)  # Split into 3 parts: command, folder, filename
        if len(parts) < 3:
            return "ℹ️ Usage: `!download <folder> <filename>` (e.g., `!download pack Betterminecraft.zip`)"

        folder_key = parts[1].lower()  # Folder (e.g., pack)
        file_name = parts[2]  # File name (e.g., Betterminecraft.zip)

        # Validate the folder
        if folder_key not in download_folders:
            return f"ℹ️ Unknown folder: `{folder_key}`. Available folders: {', '.join(download_folders.keys())}"

        # Build the full file path
        folder_path = download_folders[folder_key]
        file_path = os.path.join(folder_path, file_name)

        # Check if the file exists
        if os.path.isfile(file_path):
            return file_path  # Return the file path for sending
        else:
            return f"⚠️ File `{file_name}` not found in folder `{folder_key}`."

    # Command Handler
    if user_message.startswith('!download'):
        response = await handle_download_command(user_message)

        if os.path.isfile(response):  # If the response is a valid file path
            await message.channel.send(file=discord.File(response))  # Send the file
            logging.info(f"File `{response}` sent to {message.author}.")
        else:
            await message.channel.send(response)  # Send the error message
            logging.warning(f"File not found: {response}")
            
    # !time command
    if user_message.startswith('!time'):
        location = user_message.split(' ', 1)[1] if len(user_message.split()) > 1 else 'London'
        weather_data = await get_weather(location)

        if weather_data and weather_data['cod'] == 200:
            # Extract data from the weather response
            city_name = weather_data['name']
            country_code = weather_data['sys']['country']  # Country code
            country = country_names.get(country_code, country_code)  # Get full country name or use code if not found
            timezone_offset = weather_data['timezone']
            timezone_offset_hours = timezone_offset / 3600  # Divide by 3600 to convert seconds to hours
            timezone_offset_formatted = f"{timezone_offset_hours:+.1f} hours"  # Add "+" for positive offsets

            # Calculate the local time
            local_time = datetime.now(timezone.utc) + timedelta(seconds=timezone_offset)
            local_time_formatted = local_time.strftime('%Y-%m-%d %H:%M:%S')

            # Create the embed message
            embed = discord.Embed(title=f"Time in {city_name}, {country}", color=discord.Color.green())
            embed.add_field(name="Local Date/Time", value=local_time_formatted, inline=False)
            embed.add_field(name="Timezone Offset", value=timezone_offset_formatted, inline=False)
            embed.add_field(name="UTC Date/Time", value=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'), inline=False)
            embed.add_field(name="Your Date/Time", value=datetime.now().strftime('%Y-%m-%d %H:%M:%S'), inline=False)

            # Send the embed message
            await message.channel.send(embed=embed)
            logging.info(f"Displayed time information for {city_name}, {country}.")
        else:
            await message.channel.send("⚠️ Could not retrieve time information. Make sure the location is valid.")
            logging.warning("⚠️ Could not retrieve time information. Invalid location.")
            
    # !poll command
    if user_message.startswith('!poll'):
        # Split the command into parts while preserving original case
        # Use message.content instead of user_message to preserve case
        parts = message.content.split('"')

        if len(parts) < 3:
            await message.channel.send("❌ Usage: !poll \"Question\" \"Option1\" \"Option2\" ...")
            logging.info(f"User {message.author} tried to create a poll without correct parameters")
            return

        # Preserve original case for question and options
        question = parts[1]  # Keep original case for question
        options = [part for part in parts[2:] if part.strip()]  # Keep original case for options

        if len(options) < 2:
            await message.channel.send("❌ You must provide at least two options.")
            logging.info(f"User {message.author} tried to create a poll with less than 2 options")
            return
        if len(options) > 10:
            await message.channel.send("❌ You can provide a maximum of ten options.")
            logging.info(f"User {message.author} tried to create a poll with more than 10 options")
            return

        class PollView(View):
            def __init__(self, options):
                super().__init__(timeout=None)
                self.votes = {option: 0 for option in options}  # Use original case for options
                self.total_votes = 0
                self.user_votes = {}  # Track user votes
                for i, option in enumerate(options):
                    button = Button(label=option, custom_id=f"poll_option_{i}")  # Use original case for button labels
                    button.callback = self.vote_callback
                    self.add_item(button)

            async def vote_callback(self, interaction: discord.Interaction):
                user_id = interaction.user.id
                custom_id = interaction.data['custom_id']
                option = next((opt for opt in self.votes if f"poll_option_{list(self.votes.keys()).index(opt)}" == custom_id), None)
                
                if option:
                    # If user clicks the same option again, remove the vote
                    if user_id in self.user_votes and self.user_votes[user_id] == option:
                        self.votes[option] -= 1
                        self.total_votes -= 1
                        del self.user_votes[user_id]
                        await interaction.response.send_message(f"Your vote for **{option}** has been removed!", ephemeral=True)
                        logging.info(f"User {interaction.user} removed their vote for {option}")
                    else:
                        # Remove previous vote if exists
                        if user_id in self.user_votes:
                            previous_option = self.user_votes[user_id]
                            self.votes[previous_option] -= 1
                            self.total_votes -= 1
                            logging.info(f"User {interaction.user} changed their vote from {previous_option} to {option}")

                        # Add new vote
                        self.votes[option] += 1
                        self.total_votes += 1
                        self.user_votes[user_id] = option
                        await interaction.response.send_message(f"You voted for **{option}**!", ephemeral=True)
                        logging.info(f"User {interaction.user} voted for {option}")

                    await self.update_poll_message(interaction.message)

            async def update_poll_message(self, message):
                if self.total_votes == 0:
                    results = "No votes yet"
                else:
                    results = "\n".join([f"{option}: {votes} vote{'s' if votes != 1 else ''} ({votes / self.total_votes * 100:.1f}%)" 
                                       for option, votes in self.votes.items()])
                embed = message.embeds[0]
                embed.set_field_at(0, name="Results", value=results, inline=False)
                embed.set_footer(text=f"Total: {self.total_votes} vote{'s' if self.total_votes != 1 else ''}")
                await message.edit(embed=embed, view=self)

        # Create embed with original case for question
        embed = discord.Embed(title="📊 Poll", description=f"**{question}**", color=discord.Color.blue())
        embed.add_field(name="Results", value="No votes yet", inline=False)
        embed.set_footer(text="No votes yet")
        view = PollView(options)
        poll_message = await message.channel.send(embed=embed, view=view)
        logging.info(f"Poll created by {message.author}: '{question}' with options: {', '.join(options)}")#
        
    # !reminder command
    if user_message.startswith('!reminder'):
        # Split the command into parts while preserving original case
        parts = message.content.split('"')

        if len(parts) < 2:
            await message.channel.send("❌ Nutzung: !reminder \"Text\" DD.MM.YYYY HH:MM [dm/channel]\nBeispiel: !reminder \"Meeting\" 25.03.2024 14:30 dm")
            logging.info(f"Nutzer {message.author} hat versucht einen Reminder ohne korrekte Parameter zu erstellen")
            return

        reminder_text = parts[1]
        try:
            # Restliche Parameter nach dem Text extrahieren
            params = parts[2].strip().split()
            if len(params) < 2:
                await message.channel.send("❌ Bitte gib ein Datum (DD.MM.YYYY) und eine Uhrzeit (HH:MM) an!")
                return

            date_str = params[0]
            time_str = params[1]
            # Standard ist channel, wenn nicht anders angegeben
            reminder_type = params[2].lower() if len(params) > 2 and params[2].lower() in ['dm', 'channel'] else 'channel'

            # Datum und Zeit parsen
            reminder_datetime = datetime.strptime(f"{date_str} {time_str}", "%d.%m.%Y %H:%M")
            
            # Prüfen ob der Zeitpunkt in der Zukunft liegt
            if reminder_datetime <= datetime.now():
                await message.channel.send("❌ Der Zeitpunkt muss in der Zukunft liegen!")
                return

            # Verzögerung bis zum Reminder berechnen
            delay = (reminder_datetime - datetime.now()).total_seconds()

            # Reminder-Task erstellen
            async def send_reminder():
                await asyncio.sleep(delay)
                try:
                    if reminder_type == 'dm':
                        await message.author.send(f"🔔 **Erinnerung:** {reminder_text}")
                        logging.info(f"Reminder für {message.author} wurde als DM gesendet: {reminder_text}")
                    else:
                        await message.channel.send(f"🔔 Hey {message.author.mention}, hier ist deine Erinnerung: {reminder_text}")
                        logging.info(f"Reminder für {message.author} wurde im Channel gesendet: {reminder_text}")
                except Exception as e:
                    logging.error(f"Fehler beim Senden des Reminders: {e}")
                    if reminder_type == 'dm':
                        await message.channel.send(f"⚠️ Konnte den Reminder nicht als DM senden an {message.author.mention}. Stelle sicher, dass DMs aktiviert sind.")

            # Reminder-Task starten
            asyncio.create_task(send_reminder())

            # Bestätigung senden
            location_text = "DM" if reminder_type == 'dm' else "diesem Channel"
            embed = discord.Embed(
                title="⏰ Reminder erstellt",
                description=f"**Text:** {reminder_text}",
                color=discord.Color.green()
            )
            embed.add_field(name="Datum", value=date_str, inline=True)
            embed.add_field(name="Uhrzeit", value=time_str, inline=True)
            embed.add_field(name="Typ", value=location_text, inline=True)
            await message.channel.send(embed=embed)
            
            logging.info(f"Reminder erstellt von {message.author} für {reminder_datetime}: {reminder_text} ({reminder_type})")

        except ValueError:
            await message.channel.send("❌ Ungültiges Datum/Uhrzeit Format! Nutze DD.MM.YYYY HH:MM")
            logging.warning(f"Ungültiges Datum/Uhrzeit Format bei Reminder von {message.author}")
        except Exception as e:
            await message.channel.send("❌ Ein Fehler ist aufgetreten beim Erstellen der Erinnerung.")
            logging.error(f"Fehler beim Erstellen des Reminders von {message.author}: {e}")
