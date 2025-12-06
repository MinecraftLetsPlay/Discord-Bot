# 🤖 MCLP Discord Bot  

A **feature-rich** Discord bot built with [Discord.py](https://discordpy.readthedocs.io/en/stable/), providing  
🔒 Moderation tools, 🎮 Minigames, 🛠️ Utility commands, and more!  
Designed for **private server use** with sophisticated permission handling and logging.  

---

## ✨ Core Functionality  

### 📂 Source Files  

- `main.py` – 📝 Entry point
- `bot.py` – 🔧 Main bot initialization and event handling 
- `command_router.py` – 🚦 Command routing system  

### 🗂️ Command Modules  

- `moderation_commands.py` – 🔒 Discord moderation - Kick, Ban, Timeout etc.
- `minigames.py` – 🎮 Text-based minigames - RPS, Hangman, Quiz, Scrabble etc.
- `utility_commands.py` – 🛠️ Utility tools - Weather, Time, Reminder etc.  
- `public_commands.py` – 👥 Public commands - Help, Info, Serverinfo etc.
- `system_commands.py` – 🖥️ Admin controls, logging configuration and system commands.
- `calculator.py` – ➗ Advanced text-based calculator with eqaution solving.
- `mcserver_commands.py` – ⛏️ Minecraft-Server controls. (Nitrado API)
- `Sciencecific_commands.py` - 🔬 Sciencecific commands - Exoplanets, Sun activity etc.

### 🔌 Support Modules  

- `utils.py` – 🧩 Helper functions for loading / writing data and authorization.
- `logging_setup.py` – 📜 Advanced logging with rotation.

---

## 🚧 Features Under Development  

- 🎵 **Music Bot Features** – Voice channel audio with Spotify as search engine and YTMusic as provider.

---

## ⚙️ Tech Stack  
### Some of the core packages:
- 🐍 **Python 3.13.5** → Python-version the Bot runs on
- 💬 **Discord.py 2.6.4** → API Wrapper
- 🔊 **PyNaCl 1.6.1** → voice support  
- 🌐 **aiohttp 3.13.2** → HTTP/WebSocket
- ⏳ **asyncio 4.0.0** → async operations
- 🔑 **python-dotenv 1.2.1** → environment variables
- 📐 **sympy 1.14.0** → advanced math & calculator
- 📅 **DateTime 6.0** → time-based utilities
- 🌍 **pytz 2025.2** → timezone handling

### **Development Tools:**  

- 📦 **JSON** → lightweight data storage: configs, quiz data, scrabble
- 📝 **Logging system with rotation** → auto log management, error tracing
- 🔄 **Virtual Environment (venv)** → for isolated dependencies

### **Runtime environment**

- The Bot itself runs on a Raspberry Pi 5 B with a Quad-Core 64-Bit 2.4 Ghz CPU and 8 GB LPDDR4X RAM.

- The bot runs inside a Python venv with Python 3.13.5.

---

## 🌐 APIs & Data Sources

- **Discord API (Gateway & REST)** → Login, Chat, Slash Commands, Events

- **Discord Voice API** → Voice support (via PyNaCl)

- **Cat Fact API** → <https://catfact.ninja/fact> <br>
→ random cat facts

- **Free Dictionary API** → <https://api.dictionaryapi.dev/api/v2/entries/en/> & <https://api.dictionaryapi.dev/api/v2/entries/de/> <br>
  → Dictionary for locales English & German

- **OpenWeatherMap API** → <http://api.openweathermap.org/data/2.5/weather> <br>
→ Real-time weather data (also used for city data)

- **NASA API** → <https://api.nasa.gov/planetary>
→ Mars Rover photos, asteroides, astronomy picture of the day, space weather and exoplanets.

- **Nitrado API** → <https://api.nitrado.net/services/> → game server management

## 🛠️ Setup  

**Important!** <br>
See [`requirements.txt`](./requirements.txt) for full dependencies.  

---

## 🔒 License  

📜 **Private License** – All rights reserved.  
Permission is granted to view the source code for **personal reference and educational purposes only**.  
🚫 Any other use (copy, modify, distribute, commercial) requires prior written consent.  

> [`license.txt`](./license.txt)

---

## 📝 Changelog

### Version 1.0

- utils.py now handles all authorization logic and uses atomic read/write functions to support simultaneous file access.

- All data operations now rely on the atomic read/write functionality provided by utils.py.

- Authorization has been expanded from global-only to both global and server-based, enabling server-specific configurations.

- Logging can now be configured to either exclude entire servers or include/exclude specific channels.

- Each server automatically receives its own config.json file to store server-specific settings.

- File access and authorization logic have been optimized and unified.

---

## 👥 Authors  

- 🧑‍💻 Minecraft Lets Play (@MinecraftLetsPlay) → Dennis Plischke  
- 👨‍💻 Jirasrel (@Jirasrel)  
