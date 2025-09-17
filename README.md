# 🤖 MCLP Discord Bot  

A **feature-rich** Discord bot built with [Discord.py](https://discordpy.readthedocs.io/en/stable/), providing  
🔒 Moderation tools, 🎮 Minigames, 🛠️ Utility commands, and more!  
Designed for **private server use** with sophisticated permission handling and logging.  

---

## ✨ Core Functionality  

### 📂 Source Files  
- `main.py` – 📝 Entry point
- `bot.py` – 🔧 Main bot initialization and event handling   
- `console_to_discord.py` – 💬 Console ↔ Discord messaging  
- `command_router.py` – 🚦 Command routing system  

### 🗂️ Command Modules  
- `moderation_commands.py` – 🔒 Kick, Ban, Timeout  
- `minigames.py` – 🎮 RPS, Hangman, Quiz, scrabble etc
- `utility_commands.py` – 🛠️ Weather, Time, reminder etc.  
- `public_commands.py` – 👥 Help, Info and some public commands
- `system_commands.py` – 🖥️ Admin controls and system commands
- `calculator.py` – ➗ Advanced calculator with eqaution solving
- `mcserver_commands.py` – ⛏️ Minecraft-Server controls (Nitrado API)  

### 🔌 Support Modules  
- `utils.py` – 🧩 Helper functions for loading data
- `logging_setup.py` – 📜 Advanced logging with rotation  

---

## 🚧 Features Under Development  
- 🎵 **Music Bot Features** – Voice channel audio with YTMusic  

---

## ⚙️ Tech Stack  

- 🐍 **Python 3.11.4**  
- 💬 **Discord.py 2.6.3**  
- 🔊 **PyNaCl 1.6.0** (voice support)  
- 🌐 **aiohttp 3.12.15** (HTTP/WebSocket)  
- ⏳ **asyncio 4.0.0** (async operations)  
- 🔑 **python-dotenv 1.1.1** (environment variables)  
- 📐 **sympy 1.14.0** (advanced math & calculator)  
- 📅 **DateTime 5.5** (time-based utilities)  
- 🌍 **pytz 2025.2** (timezone handling)  

**Development Tools:**  
- 📦 **JSON** (lightweight data storage: configs, quiz data, scrabble)  
- 📝 **Logging system with rotation** (auto log management, error tracing)  
- 🔄 **Virtual Environment (venv)** for isolated dependencies

---

## 🛠️ Setup  

See [`requirements.txt`](./requirements.txt) for full dependencies.  

---

## 🔒 License  

📜 **Private License** – All rights reserved.  
Permission is granted to view the source code for **personal reference and educational purposes only**.  
🚫 Any other use (copy, modify, distribute, commercial) requires prior written consent.  

[`license.txt`](./license.txt)

---

## 👥 Authors  

- 🧑‍💻 Minecraft Lets Play (@MinecraftLetsPlay) → Dennis Plischke  
- 👨‍💻 Jirasrel (@Jirasrel)  
