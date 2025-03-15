import discord
import aiohttp
import json
import os
import math
import re
from datetime import datetime, timezone, timedelta
from internal import utils
from dotenv import load_dotenv
import logging
from discord.ext import commands
from discord.ui import Button, View
import asyncio
import sympy
from sympy import solve, symbols, parse_expr

#
#
# Utility commands
#
#

# Load environment variables from .env file
load_dotenv()

# Store the bot start time
bot_start_time = datetime.now(timezone.utc)

# Store last result for 'ans' functionality
LAST_RESULT = {}
    
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
            await message.channel.send("❌ Usage: !reminder \"Text\" DD.MM.YYYY HH:MM [dm/channel]\nExample: !reminder \"Meeting\" 25.03.2024 14:30 dm")
            logging.info(f"User {message.author} tried to create a reminder without correct parameters")
            return

        reminder_text = parts[1]
        try:
            # Extract remaining parameters after the text
            params = parts[2].strip().split()
            if len(params) < 2:
                await message.channel.send("❌ Please provide a date (DD.MM.YYYY) and time (HH:MM)!")
                return

            date_str = params[0]
            time_str = params[1]
            # Default is channel if not specified otherwise
            reminder_type = params[2].lower() if len(params) > 2 and params[2].lower() in ['dm', 'channel'] else 'channel'

            # Parse date and time
            reminder_datetime = datetime.strptime(f"{date_str} {time_str}", "%d.%m.%Y %H:%M")
            
            # Check if the time is in the future
            if reminder_datetime <= datetime.now():
                await message.channel.send("❌ The reminder time must be in the future!")
                return

            # Calculate delay until reminder
            delay = (reminder_datetime - datetime.now()).total_seconds()

            # Create reminder task
            async def send_reminder():
                await asyncio.sleep(delay)
                try:
                    if reminder_type == 'dm':
                        await message.author.send(f"🔔 **Reminder:** {reminder_text}")
                        logging.info(f"Reminder for {message.author} sent as DM: {reminder_text}")
                    else:
                        await message.channel.send(f"🔔 Hey {message.author.mention}, here's your reminder: {reminder_text}")
                        logging.info(f"Reminder for {message.author} sent in channel: {reminder_text}")
                except Exception as e:
                    logging.error(f"Error sending reminder: {e}")
                    if reminder_type == 'dm':
                        await message.channel.send(f"⚠️ Could not send reminder as DM to {message.author.mention}. Make sure DMs are enabled.")

            # Start reminder task
            asyncio.create_task(send_reminder())

            # Send confirmation
            location_text = "DM" if reminder_type == 'dm' else "This channel"
            embed = discord.Embed(
                title="⏰ Reminder Created",
                description=f"**Text:** {reminder_text}",
                color=discord.Color.green()
            )
            embed.add_field(name="Date", value=date_str, inline=True)
            embed.add_field(name="Time", value=time_str, inline=True)
            embed.add_field(name="Type", value=location_text, inline=True)
            await message.channel.send(embed=embed)
            
            logging.info(f"Reminder created by {message.author} for {reminder_datetime}: {reminder_text} ({reminder_type})")

        except ValueError:
            await message.channel.send("❌ Invalid date/time format! Use DD.MM.YYYY HH:MM")
            logging.warning(f"Invalid date/time format in reminder from {message.author}")
        except Exception as e:
            await message.channel.send("❌ An error occurred while creating the reminder.")
            logging.error(f"Error creating reminder from {message.author}: {e}")
            
    # !calc command
    
    # Safe math functions for the calculator
    SAFE_FUNCTIONS = {
        # Basic math operations
        'sqrt': math.sqrt, 
        'ln': math.log, 
        'log': math.log10,
        'log2': math.log2,
        
        # Trigonometric functions (in radians)
        'sin': math.sin, 
        'cos': math.cos, 
        'tan': math.tan,
        'asin': math.asin, 
        'acos': math.acos, 
        'atan': math.atan,
        
        # Hyperbolic functions
        'sinh': math.sinh,
        'cosh': math.cosh,
        'tanh': math.tanh,
        
        # Other math functions
        'exp': math.exp, 
        'pow': math.pow,
        'factorial': math.factorial,
        'abs': abs,
        'floor': math.floor,
        'ceil': math.ceil,
        'round': round,
        
        # Constants
        'pi': math.pi, 
        'e': math.e,
        'tau': math.tau,
        'inf': math.inf,
        
        # Root functions
        'sqrt': math.sqrt,
        'cbrt': lambda x: x**(1/3),  # Cubic root
        'root4': lambda x: x**(1/4)   # Fourth root
    }

    # Add lambda functions to SAFE_FUNCTIONS
    SAFE_FUNCTIONS.update({
        'cbrt': lambda x: x**(1/3),  # Cubic root
        'root4': lambda x: x**(1/4),  # Fourth root
        'solve': lambda eq: solve_equation(eq),
        'pq': lambda p, q: solve_pq(p, q),
        'quad': lambda a, b, c: solve_quadratic(a, b, c),
    })

    # Helper functions for the calculator
    def solve_pq(p, q):
        """Solves a PQ equation: x² + px + q = 0"""
        x1 = -p/2 + math.sqrt((p/2)**2 - q)
        x2 = -p/2 - math.sqrt((p/2)**2 - q)
        return f"x₁ = {x1:.4g}\nx₂ = {x2:.4g}"

    def solve_quadratic(a, b, c):
        """Solves a quadratic equation: ax² + bx + c = 0"""
        discriminant = b**2 - 4*a*c
        if discriminant < 0:
            return "No real solutions"
        x1 = (-b + math.sqrt(discriminant))/(2*a)
        x2 = (-b - math.sqrt(discriminant))/(2*a)
        return f"x₁ = {x1:.4g}\nx₂ = {x2:.4g}"

    def solve_equation(equation_str):
        """Solves a general equation using sympy"""
        x = symbols('x')
        try:
            equation = parse_expr(equation_str)
            solutions = solve(equation, x)
            if not solutions:
                return "No solutions found!"
            return "\n".join([f"x{i+1 if len(solutions)>1 else ''} = {sol}" for i, sol in enumerate(solutions)])
        except Exception as e:
            return f"Error solving equation: {str(e)}"

    if user_message.startswith('!calc'):
        try:
            global LAST_RESULT
            expression = user_message[6:].strip()
            if not expression:
                # Help message with available functions
                help_msg = (
                    "📝 **Calculator Usage:**\n"
                    "`!calc <expression>`\n\n"
                    "**Available Functions:**\n"
                    "• Basic Operations:\n"
                    "  - Addition (+), Subtraction (-)\n"
                    "  - Multiplication (×, *), Division (÷, /)\n"
                    "  - Powers (^, ², ³, ⁴, ⁵, ⁶, ⁷, ⁸, ⁹)\n"
                    "  - Square Root (√), Cubic Root (∛), Fourth Root (∜)\n"
                    "\n• Mathematical Functions:\n"
                    "  - Logarithms: ln(x), log(x), log2(x)\n"
                    "  - Trigonometry: sin(x), cos(x), tan(x)\n"
                    "  - Inverse Trig: asin(x), acos(x), atan(x)\n"
                    "  - Hyperbolic: sinh(x), cosh(x), tanh(x)\n"
                    "\n• Other Functions:\n"
                    "  - exp(x), abs(x), factorial(x)\n"
                    "  - floor(x), ceil(x), round(x)\n"
                    "\n• Constants:\n"
                    "  - π (pi), e, τ (tau), ∞ (inf)\n"
                    "\n• Special Features:\n"
                    "  - Previous result: ans\n"
                    "  - Equation solving: solve(equation)\n"
                    "  - PQ formula: pq(p,q)\n"
                    "  - Quadratic: quad(a,b,c)\n"
                    "\n**Examples:**\n"
                    "• `!calc 2 + 2`\n"
                    "• `!calc sin(45) + cos(30)`\n"
                    "• `!calc √(16) + ∛(27)`\n"
                    "• `!calc 2³ + π`\n"
                    "• `!calc solve(x^2 + 2x + 1)`\n"
                "• `!calc ans + 5`"
            )
                await message.channel.send(help_msg)
                return

            # Replace 'ans' with the last result for this user
            if 'ans' in expression:
                if message.author.id not in LAST_RESULT:
                    await message.channel.send("❌ No previous calculation found. Cannot use 'ans'.")
                    return
                expression = expression.replace('ans', str(LAST_RESULT[message.author.id]))

            # Debug log for initial expression
            logging.debug(f"Initial expression: {expression}")

            # Special character replacements
            replacements = {
                # Exponents
                '²': '**2',
                '³': '**3',
                '⁴': '**4',
                '⁵': '**5',
                '⁶': '**6',
                '⁷': '**7',
                '⁸': '**8',
                '⁹': '**9',

                # Mathematical symbols
                '^': '**',
                '×': '*',
                '·': '*',
                '÷': '/',

                # Roots
                '√': 'sqrt',
                '∛': 'cbrt',  # Cubic root as lambda function
                '∜': 'root4',  # Fourth root as lambda function

                # Greek letters and symbols
                'π': 'pi',
                'τ': 'tau',
                '∞': 'inf',
                'ℯ': 'e',

                # Other symbols
                '±': ' + [-]', # Plus or minus
                '∓': ' - [+]',  # Minus or negative
                '∑': 'sum',
                '∏': 'prod',
                '∆': 'delta',
            }
            
            # Store original expression for display
            original_expression = expression

            # Apply all replacements for calculation
            for old, new in replacements.items():
                expression = expression.replace(old, new)

            # Debug log after replacements
            logging.debug(f"After replacements: {expression}")
                
            # Convert degrees to radians for trig functions
            if any(func in expression for func in ['sin(', 'cos(', 'tan(']):
                expression = re.sub(r'(sin|cos|tan)\((.+?)\)', r'\1((\2) * pi / 180)', expression)

            # Debug log after trig conversion
            logging.debug(f"After trig conversion: {expression}")

            # Updated input validation to allow more characters
            if re.search(r'[^0-9+\-*/()., \w]', expression):
                logging.warning(f"Invalid characters in expression: {expression}")
                await message.channel.send("❌ Invalid characters detected!")
                return

            # Calculate result
            result = eval(expression, {"__builtins__": None}, SAFE_FUNCTIONS)
            
            # Store result for 'ans' functionality
            LAST_RESULT[message.author.id] = result

            # Format the result
            if isinstance(result, float):
                formatted_result = f"{result:.10g}"  # Show up to 10 significant digits
            else:
                formatted_result = str(result)

            # Create embed using original expression
            embed = discord.Embed(
                title="🔢 Calculator",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Expression",
                value=f"**{original_expression}**",  # Combine code block and bold
                inline=False
            )
            embed.add_field(
                name="Result",
                value=f"**{formatted_result}**",
                inline=False
            )
            
            # Add tip for using 'ans'
            embed.set_footer(text="💡 Tip: Use 'ans' in your next calculation to use this result!")

            await message.channel.send(embed=embed)
            logging.info(f"Calculation performed for {message.author}: {expression} = {result}")

        except ZeroDivisionError:
            await message.channel.send("❌ Cannot divide by zero!")
        except (SyntaxError, ValueError, NameError):
            await message.channel.send("❌ Invalid expression. Type `!calc` for help.")
            logging.warning(f"Invalid expression from {message.author}: {expression}")
        except Exception as e:
            await message.channel.send(f"❌ Error: {str(e)}")
            logging.error(f"Calculation error for {message.author}: {str(e)}")