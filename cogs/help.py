import discord
from discord.ext import commands

class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def fetch_bot_owner(self):
        app_info = await self.bot.application_info()
        return app_info.owner.name

    @commands.slash_command(name="help", description="Learn how to use the PS4 Save Editor Bot.")
    async def helpbot(self, ctx: discord.ApplicationContext):
        bot_owner_name = await self.fetch_bot_owner()
        embed = discord.Embed(
            title="PS4 Save Editor Bot - Tutorial",
            description=(
                "Welcome to the PS4 Save Editor Bot! This bot is designed to assist you in modifying and managing your PS4 save games, "
                "whether you're looking to resign, decrypt, or customize your saves.\n\n"
                "### **How to Use**\n"
                "Use the following commands to interact with your PS4 save files. For best results, ensure your saves are compatible.\n\n"
                "**Core Commands:**\n"
                "🔧 **/resign** - Resign your PS4 save file to a new PlayStation account.\n"
                "🌍 **/reregion** - Change the region of a save to match your game version.\n"
                "🔓 **/decrypt** - Decrypt your save file for editing.\n"
                "🔒 **/encrypt** - Re-encrypt your save file after making changes.\n"
                "🖼️ **/change picture** - Customize the icon/picture associated with your save.\n"
                "📝 **/change title** - Modify the title of your save file for better organization.\n\n"
                "**Quick and Advanced Tools:**\n"
                "⚡ **/quick cheats** - Add pre-made cheat codes to your save for specific games.\n"
                "🎮 **/quick codes** - Apply quick save modifications with preloaded codes.\n"
                "📁 **/quick resign** - Quickly resign pre-stored save files.\n"
                "🔑 **/sealed_key decrypt** - Decrypt sealed keys in `.bin` files.\n"
                "🧩 **/convert** - Convert PS4 save files to PC or other supported platforms.\n"
                "📜 **/sfo read** - Extract information from a `param.sfo` file.\n"
                "🖋️ **/sfo write** - Edit and rewrite parameters in a `param.sfo` file.\n\n"
                "**Important Notes:**\n"
                "- Ensure that your saves are properly backed up before making modifications.\n"
                "- Resigning and re-encryption are required for saves to function on new accounts or consoles.\n\n"
                "**Learn More**\n"
                "Watch our detailed video tutorial for step-by-step instructions: **[YouTube Tutorial](https://www.youtube.com/watch?v=cGeVhia0KjA)**\n\n"
                f"**👑 Bot Owner:** **{bot_owner_name}**"
            ),
            colour=discord.Colour.gold()
        )
        embed.set_footer(text="Start Modding & Have fun!")
        await ctx.respond(embed=embed)

def setup(bot: commands.Bot):
    bot.add_cog(HelpCog(bot))
