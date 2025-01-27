import discord
import aiohttp
import json
import os
from internal import utils

    #
    #
    # Utility commands
    #
    #
    
# Main def for handling utility commands
async def handle_utility_commands(client, message, user_message):

    # !ping command
    if user_message == '!ping':
        latency = round(client.latency * 1000)  # Latency in milliseconds
        await message.channel.send(f'Pong! Latency is {latency}ms')

    # !weather command
    def load_config():
        try:
            with open('config.json', 'r') as file:
                return json.load(file)
        except Exception as e:
            print(f"Error loading config file: {e}")
            return {}

    # Asynchronous function to get weather data
    async def get_weather(location):
        config = utils.load_config()  # Load the config
        api_key = config.get('api_key')  # Get the API key

        if not api_key:
            print("API key is missing in the config.")
            return None

        base_url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url) as response:
                return await response.json()

    # Handling the '!weather' command
    if user_message.startswith('!weather'):
        location = user_message.split(' ', 1)[1] if len(user_message.split()) > 1 else 'London'
        weather_data = await get_weather(location)

        if weather_data and weather_data['cod'] == 200:
            # Extract data from the weather response

            city_name = weather_data['name']
            country = weather_data['sys']['country']  # Country code
            temp = weather_data['main']['temp']
            temp_min = weather_data['main']['temp_min']  # Minimum temperature
            temp_max = weather_data['main']['temp_max']  # Maximum temperature
            description = weather_data['weather'][0]['description']
            humidity = weather_data['main']['humidity']
            pressure = weather_data['main']['pressure']
            wind_speed = weather_data['wind']['speed']
            wind_deg = weather_data['wind']['deg']

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
            embed.add_field(name="Wind", value=f"{wind_speed} m/s, {wind_deg}°", inline=False)

            # Send the embed message
            await message.channel.send(embed=embed)
        else:
            await message.channel.send("Could not retrieve weather information. Make sure the location is valid.")
            
    from datetime import datetime, timezone

    if user_message.startswith('!city'):
        location = user_message.split(' ', 1)[1] if len(user_message.split()) > 1 else 'London'
        weather_data = await get_weather(location)

        if weather_data and weather_data['cod'] == 200:
            # Extract data from the weather response
            city_name = weather_data['name']
            country = weather_data['sys']['country']
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

            # Create the embed message
            embed = discord.Embed(title=f"Information for: {city_name}, {country}", color=discord.Color.blue())
            embed.add_field(name="City", value=city_name, inline=False)
            embed.add_field(name="Country", value=country, inline=False)
            embed.add_field(name="Latitude", value=coords['lat'], inline=False)
            embed.add_field(name="Longitude", value=coords['lon'], inline=False)
            embed.add_field(name="Sea Level", value=f"{sea_level} m", inline=False)
            embed.add_field(name="Ground Level", value=f"{ground_level} m", inline=False)
            embed.add_field(name="Timezone Offset", value=timezone_offset_formatted, inline=False)
            embed.add_field(name="Sunrise", value=sunrise_time, inline=False)
            embed.add_field(name="Sunset", value=sunset_time, inline=False)

            # Send the embed message
            await message.channel.send(embed=embed)
        else:
            await message.channel.send("Could not retrieve city information. Make sure the location is valid.")

    # !download command
    async def handle_download_command(user_message):
        config = utils.load_config()
        download_folders = config.get("download_folders", {})

        # Split the command into parts
        parts = user_message.split(' ', 2)  # Split into 3 parts: command, folder, filename
        if len(parts) < 3:
            return "Usage: `!download <folder> <filename>` (e.g., `!download pack Betterminecraft.zip`)"

        folder_key = parts[1].lower()  # Folder (e.g., pack)
        file_name = parts[2]  # File name (e.g., Betterminecraft.zip)

        # Validate the folder
        if folder_key not in download_folders:
            return f"Unknown folder: `{folder_key}`. Available folders: {', '.join(download_folders.keys())}"

        # Build the full file path
        folder_path = download_folders[folder_key]
        file_path = os.path.join(folder_path, file_name)

        # Check if the file exists
        if os.path.isfile(file_path):
            return file_path  # Return the file path for sending
        else:
            return f"File `{file_name}` not found in folder `{folder_key}`."

    # Command Handler
    if user_message.startswith('!download'):
        response = await handle_download_command(user_message)

        if os.path.isfile(response):  # If the response is a valid file path
            await message.channel.send(file=discord.File(response))  # Send the file
        else:
            await message.channel.send(response)  # Send the error message
