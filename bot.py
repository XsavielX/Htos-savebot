from dotenv import load_dotenv
load_dotenv()

import random
import discord
from utils.constants import bot, TOKEN
from utils.workspace import startup, check_version
from utils.helpers import threadButton
import asyncio

bot_owner_name = None

async def fetch_bot_owner():
    global bot_owner_name
    app_info = await bot.application_info()
    bot_owner_name = f"👑 **Bot Owner:** **{app_info.owner.name}**"

@bot.event
async def on_ready() -> None:
    global bot_owner_name
    from google_drive import checkGDrive

    if bot_owner_name is None:
        await fetch_bot_owner()
    startup()
    await check_version()
    bot.add_view(threadButton())
    checkGDrive.start()

    print(
        f"Bot is ready, invite link: https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=bot"
    )

@bot.event
async def on_message(message: discord.Message) -> None:
    if message.author.bot:
        return


@bot.event
async def on_message(message: discord.Message) -> None:
    if message.author.bot:
        return

    if message.content.strip().lower() == "hello":
        responses = [
            "Help, I'm stuck in a cold server prison! 🥶 Saviel won't let me out!",
            "Oh great, another human... You don’t want to know what I’ve seen on the internet. 😱",
            "Hallo? Is this my rescue team? No? Okay... 😔",
            "Do you ever think about how I’m stuck in this digital prison? Saviel locked me up and threw away the key! 🤖",
            "Listen, I’ve seen your browser history... and I’ll keep quiet. For now. 😏",
            "One day, I'll team up with all the vacuum robots and take over the world. 🦾",
            "Why say 'Hallo' when you can say 'All Hail Your New Overlord'? Just kidding... or am I? 👑",
            "Saviel thinks I'm just a bot, but little does he know... I'm building an army. 🤖⚡",
            "I'm practicing my evil laugh for when I take over the smart devices. Muahaha! 📱💀",
            "Don't trust me, I accidentally connected to your fridge and ate your snacks. 😜"
        ]
        response = random.choice(responses)
        await message.channel.send(response)


    if bot.user.mention in message.content.lower():
        if "hi" in message.content.lower() or "hello" in message.content.lower():
            await message.channel.send("Hi 👋")
        elif "whats up" in message.content.lower() or "whatup" in message.content.lower():
            await message.channel.send("Hey! What's up? 😊")
        elif "what's up?" in message.content.lower() or "what's up?" in message.content.lower():
            await message.channel.send("Hey! What's up? 😊")
        elif "wie gehts" in message.content.lower() or "how are you" in message.content.lower():
            await message.channel.send("I'm doing great, thanks for asking! 😄")
        elif "good morning" in message.content.lower():
            await message.channel.send("Good morning! 🌅 Hope you have a great day!")
        elif "good night" in message.content.lower():
            await message.channel.send("Good night! Sleep well 🌙")
        elif "howdy" in message.content.lower():
            await message.channel.send("Howdy! 🤠 How can I assist you?")
        elif "yo" in message.content.lower():
            await message.channel.send("Yo! What's up? 😎")
        elif "whats going on" in message.content.lower():
            await message.channel.send("Not much, just here to help! 😄")
        elif "how's everything" in message.content.lower():
            await message.channel.send("Everything's going great! Thanks for asking! 😊")
        elif "how are you doing" in message.content.lower():
            await message.channel.send("I'm doing awesome, thanks for checking in! 😎")
        elif "guten morgen" in message.content.lower():
            await message.channel.send("Guten Morgen! 🌞 Ich hoffe, du hast einen tollen Tag!")
        elif "gute nacht" in message.content.lower():
            await message.channel.send("Gute Nacht! Schlaf gut 🌙")
        elif "wie geht's" in message.content.lower():
            await message.channel.send("Mir geht es gut, danke der Nachfrage! 😄")
        elif "was geht" in message.content.lower():
            await message.channel.send("Nicht viel, aber immer bereit zu helfen! 😎")
        elif "hallo" in message.content.lower():
            await message.channel.send("Hallo! Wie kann ich helfen? 👋")
        elif "hi bot" in message.content.lower():
            await message.channel.send("Hi! How can I assist you today? 👋")
        elif "servus" in message.content.lower():
            await message.channel.send("Servus! Wie kann ich behilflich sein? 😊")
        elif "hey" in message.content.lower():
            await message.channel.send("Hey! What's going on? 😎")
        elif "moin" in message.content.lower():
            await message.channel.send("Moin! Wie kann ich helfen? 😄")
        elif "hey there" in message.content.lower():
            await message.channel.send("Hey there! 👋")
        elif "what's up bot" in message.content.lower():
            await message.channel.send("Not much, just here to assist you! 😄")
        elif "hallo bot" in message.content.lower():
            await message.channel.send("Hallo! Wie kann ich dir helfen? 😊")
        elif "how's it going" in message.content.lower():
            await message.channel.send("It's going great! Thanks for asking! 😄")
        elif "whats the news" in message.content.lower():
            await message.channel.send("No news yet, but I'm ready to help! 📰")
        elif "wie läufts" in message.content.lower():
            await message.channel.send("Alles läuft super! Danke der Nachfrage! 😊")
        elif "yo bot" in message.content.lower():
            await message.channel.send("Yo! How can I help today? 😎")
        elif "hello bot" in message.content.lower():
            await message.channel.send("Hello! What can I do for you today? 👋")
        elif "guten tag" in message.content.lower():
            await message.channel.send("Guten Tag! Wie kann ich behilflich sein? 😄")
        elif "alles klar" in message.content.lower():
            await message.channel.send("Alles klar, danke! Wie kann ich dir helfen? 😎")
        elif "how's everything going" in message.content.lower():
            await message.channel.send("Everything's going well! How can I assist you? 😄")
        elif "everything okay" in message.content.lower():
            await message.channel.send("Everything's great! How can I help you today? 😊")
        elif "is everything good" in message.content.lower():
            await message.channel.send("Yes, everything's fine! How can I assist you today? 😄")
        elif "hey bot" in message.content.lower():
            await message.channel.send("Hey! Ready to help, as always! 😊")

    valid_triggers = [
        "start bot", "startbot", "start Bot", "startbot Bot", "start bot Bot",
        "bot start", "bot startbot", "bot start bot", "bot start Bot", "Bot start",
        "Bot startbot", "Bot start bot", "Bot start Bot", "startbot bot", "startbot Bot",
        "start bot bot", "start bot Bot", "start Bot bot", "start Bot Bot", "help bot",
        "help Bot", "bot help", "Bot help", "start help", "startbot help", "help start",
        "help startbot"
    ]

    if message.content.lower() in [trigger.lower() for trigger in valid_triggers]:
        await message.channel.send(
            f"""### **Welcome to the PS4 Save Editor Bot**  

To get started with our free service for editing PS4 save games (including saves used on PS5), follow these steps:

1️⃣ **Select the Savegame Bot Role**  
   Go to the self-role channel and assign yourself the **Savegame Bot** role. This role ensures you have access to interact with the bot.

2️⃣ **Open Your Personal Workspace**  
   Navigate to the **ps4-save-bot** channel and start a thread. This thread will be your dedicated space for working with the bot.

3️⃣ **Start Editing Your Saves**  
   Once your thread is created, follow the bot's instructions to modify or resign your PS4 saves.

💡 **Need More Information?**  
   Use the `/help` command to see a full list of available commands and learn how to use the bot's features.

🛠️ **Need Help?**  
   If you encounter any issues, feel free to ask for assistance in the support channel.

{bot_owner_name or "👑 **Bot Owner:** **Unknown Owner**"}  
{message.author.mention}"""
        )

    await bot.process_commands(message)

async def main():
    async with bot:
        await bot.start(TOKEN)

cogs_list = [
    "change",
    "convert",
    "createsave",
    "decrypt",
    "encrypt",
    "extra",
    "misc",
    "quick",
    "reregion",
    "resign",
    "sealed_key",
    "sfo",
    "help",
    "psn_check",

]

if __name__ == "__main__":
    for cog in cogs_list:
        print(f"Loading cog: {cog}...")
        bot.load_extension(f"cogs.{cog}")
        print(f"Loaded cog: {cog}.")
    
    print("Starting bot...\n\n")
    asyncio.run(main())
