import discord
import asyncio
import os
import json
import aiohttp
import discord.bot
import data.crypto.helpers as crypthelp
import utils.orbis as orbis
import aiofiles.os
from discord.ext import pages
from dataclasses import dataclass
from typing import Literal
from discord.ui.item import Item
from psnawp_api.core.psnawp_exceptions import PSNAWPNotFound
from google_drive import GDapi, GDapiError
from network import FTPps
from utils.constants import (
    logger, blacklist_logger, Color, Embed_t, bot, psnawp, 
    NPSSO, UPLOAD_TIMEOUT, FILE_LIMIT_DISCORD, SCE_SYS_CONTENTS, OTHER_TIMEOUT, MAX_FILES, BLACKLIST_MESSAGE,
    BOT_DISCORD_UPLOAD_LIMIT, MAX_PATH_LEN, MAX_FILENAME_LEN, PSN_USERNAME_RE, MOUNT_LOCATION, RANDOMSTRING_LENGTH, CON_FAIL_MSG, EMBED_DESC_LIM, EMBED_FIELD_LIM, QR_FOOTER1, QR_FOOTER2,
    embgdt, embUtimeout, embnt, emb8, embvalidpsn
)
from utils.exceptions import PSNIDError, FileError
from utils.workspace import fetch_accountid_db, write_accountid_db, cleanup, cleanupSimple, write_threadid_db, WorkspaceError, get_savename_from_bin_ext, blacklist_check_db
from utils.extras import zipfiles

@dataclass
class DiscordContext:
    ctx: discord.ApplicationContext
    msg: discord.Message

class TimeoutHelper:
    def __init__(self, embTimeout: discord.Embed) -> None:
        self.done = False
        self.embTimeout = embTimeout

    async def await_done(self) -> None:
        try:
            while not self.done:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
    
    async def handle_timeout(self, ctx: discord.ApplicationContext | discord.Message) -> None:
        await asyncio.sleep(2)
        if not self.done:
            await ctx.edit(embed=self.embTimeout, view=None)
            await asyncio.sleep(4)
            self.done = True

class threadButton(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    async def on_error(self, e: Exception, _: Item, __: discord.Interaction) -> None:
        logger.error(f"Unexpected error while creating thread: {e}")
    
    @discord.ui.button(label="Create thread", style=discord.ButtonStyle.primary, custom_id="CreateThread")
    async def callback(self, _: discord.Button, interaction: discord.Interaction) -> None:
        await interaction.response.send_message("Creating thread...", ephemeral=True)

        ids_to_remove = []
        global bot_name
        bot_name = discord.appinfo.__name__
        global bot_owner_name
        app_info = await bot.application_info()
        bot_owner_name = f"**{app_info.owner.name}**"

        try:
            thread = await interaction.channel.create_thread(name=interaction.user.name, auto_archive_duration=10080)
            await thread.send(interaction.user.mention)
            
            threadwelcome = discord.Embed(
                title="Welcome to Saviel's bot",
                description=("**Easily manage your PS4 game saves with this bot!**\n\n"
                             "📂 **Seamless Save Editing**\n"
                             "Effortlessly adjust game saves for new accounts or regions.\n\n"
                             "🔧 **Guided Assistance**\n"
                             "Need support? Use `/help` for detailed instructions.\n\n"
                             "🎮 **Reminder:** Always use your PlayStation username as the PSN ID for smooth operation.\n\n"
                             "Get started now and enjoy your personalized gaming experience! 🚀"),
                colour=0x0083ff
            )
            threadwelcome.set_thumbnail(url="https://cdn.discordapp.com/attachments/1256434247120584737/1297344797086060574/standard.gif?ex=671595ff&is=6714447f&hm=98be2d6eb93d0c40b68e072b0f8da8b4bfe3d6c3c3991fde38f9960f5c45f44b&")
            threadwelcome.set_footer(text="Start Modding & Have fun!", icon_url="https://cdn.discordapp.com/emojis/1253123128943579147.gif?size=48")
            botagreement = discord.Embed(
                title="User Agreement for {bot_name}",
                description= (
                    f"By using {bot_name} (hereafter referred to as 'The bot'), you agree to the following terms:\n"
                    f"Non-Monetary Use: The bot may not be used for any activity that generates monetary gain, directly or indirectly, without explicit written permission from [Your Name/Entity]. This includes, but is not limited to, charging fees for access to The bot, utilizing The bot in paid services, or selling features or results derived from its use.\n\n"
                    f"Permission Requirement: Explicit permission must be obtained in writing from {bot_name} to use The bot for any form of monetary gain. Unauthorized monetization will be considered a violation of this agreement.\n\n"
                    "Consequences of Violation: Any breach of this agreement may result in:\n\n"
                    "Immediate revocation of access to The bot.\n"
                    "Potential legal action to address the violation.\n\n"
                    "Acceptance of Terms: By using The bot, you acknowledge and agree to these terms. If you do not agree, discontinue use of The bot immediately.\n\n"
                ),
                colour=0x0083ff
            )
            await thread.send(embed=threadwelcome)
            await thread.send(embed=botagreement)
            ids_to_remove = await write_threadid_db(interaction.user.id, thread.id)
        except (WorkspaceError, discord.Forbidden) as e:
            logger.error(f"Can not create thread: {e}")
        
        try:
            for thread_id in ids_to_remove:
                old_thread = bot.get_channel(thread_id)
                if old_thread is not None:
                    await old_thread.delete() 
        except discord.Forbidden as e:
            logger.error(f"Can not clear old thread: {e}")

async def clean_msgs(messages: list[discord.Message]) -> None:
    for msg in messages:
        try:
            await msg.delete()
        except discord.Forbidden:
            pass


async def errorHandling(
          ctx: discord.ApplicationContext | discord.Message, 
          error: str, 
          workspaceFolders: list[str], 
          uploaded_file_paths: list[str] | None, 
          mountPaths: list[str] | None, 
          C1ftp: FTPps | None
        ) -> None:
    embe = discord.Embed(
        title="Error",
        description=error,
        colour=Color.DEFAULT.value
    )
    embe.set_footer(text=Embed_t.DEFAULT_FOOTER.value)
    await ctx.edit(embed=embe)
    if (uploaded_file_paths is not None) and (mountPaths is not None) and (C1ftp is not None) and error != CON_FAIL_MSG:
        await cleanup(C1ftp, workspaceFolders, uploaded_file_paths, mountPaths)
    else:
        cleanupSimple(workspaceFolders)

"""Makes the bot expect multiple files through discord or google drive."""
def upl_check(message: discord.Message, ctx: discord.ApplicationContext) -> bool:
    if message.author == ctx.author and message.channel == ctx.channel:
        return (len(message.attachments) >= 1) or (message.content and GDapi.is_google_drive_link(message.content)) or (message.content and message.content == "EXIT")
    
"""Makes the bot expect a single file through discord or google drive."""
def upl1_check(message: discord.Message, ctx: discord.ApplicationContext) -> bool:
    if message.author == ctx.author and message.channel == ctx.channel:
        return (len(message.attachments) == 1) or (message.content and GDapi.is_google_drive_link(message.content)) or (message.content and message.content == "EXIT")

async def upload2(
          d_ctx: DiscordContext, 
          saveLocation: str, 
          max_files: int, 
          sys_files: bool, 
          ps_save_pair_upload: bool, 
          ignore_filename_check: bool,
          savesize: int | None = None
        ) -> list[str]:

    try:
        message: discord.Message = await bot.wait_for("message", check=lambda message: upl_check(message, d_ctx.ctx), timeout=UPLOAD_TIMEOUT)  # Wait for 300 seconds for a response with attachments
    except asyncio.TimeoutError:
        await d_ctx.msg.edit(embed=embUtimeout)
        raise TimeoutError("TIMED OUT!")
    
    if len(message.attachments) > max_files:
        return []

    elif len(message.attachments) >= 1:
        attachments = message.attachments
        uploaded_file_paths = []
        valid_attachments = await orbis.checkSaves(d_ctx.msg, attachments, ps_save_pair_upload, sys_files, ignore_filename_check, savesize)

        for attachment in valid_attachments:
            file_path = os.path.join(saveLocation, attachment.filename)
            await attachment.save(file_path)
            logger.info(f"Saved {attachment.filename} to {file_path}")
            
            emb1 = discord.Embed(
                title="Upload alert: Successful", 
                description=f"File '{attachment.filename}' has been successfully uploaded and saved.", 
                colour=Color.DEFAULT.value
            )
            emb1.set_footer(text=Embed_t.DEFAULT_FOOTER.value)
            await d_ctx.msg.edit(embed=emb1)

            uploaded_file_paths.append(file_path)
            # run a quick check
            if ps_save_pair_upload and not attachment.filename.endswith(".bin"):
                await orbis.parse_pfs_header(file_path)
            elif ps_save_pair_upload and attachment.filename.endswith(".bin"):
                await orbis.parse_sealedkey(file_path)
        
        await message.delete() # delete afterwards for reliability

    elif message.content == "EXIT":
        raise TimeoutError("EXITED!")
    
    else:
        try:
            google_drive_link = message.content
            await message.delete()
            folder_id = await GDapi.grabfolderid(google_drive_link, d_ctx.msg)
            if not folder_id: raise GDapiError("Could not find the folder id!")
            uploaded_file_paths = await GDapi.downloadsaves_gd(d_ctx.msg, folder_id, saveLocation, max_files, SCE_SYS_CONTENTS if sys_files else None, ps_save_pair_upload, ignore_filename_check)
           
        except asyncio.TimeoutError:
            await d_ctx.msg.edit(embed=embgdt)
            raise TimeoutError("TIMED OUT!")
        
    return uploaded_file_paths

async def upload1(d_ctx: DiscordContext, saveLocation: str) -> str:        
    try:
        message: discord.Message = await bot.wait_for("message", check=lambda message: upl1_check(message, d_ctx.ctx), timeout=UPLOAD_TIMEOUT)  # Wait for 120 seconds for a response with an attachment
    except asyncio.TimeoutError:
        await d_ctx.msg.edit(embed=embUtimeout)
        raise TimeoutError("TIMED OUT!")

    if len(message.attachments) == 1:
        attachment = message.attachments[0]

        if len(attachment.filename) > MAX_FILENAME_LEN:
            await message.delete()
            raise FileError(f"Filename: {attachment.filename} ({len(attachment.filename)}) is exceeding {MAX_FILENAME_LEN}!")

        elif attachment.size > FILE_LIMIT_DISCORD:
            await message.delete()
            raise FileError(f"DISCORD UPLOAD ERROR: File size of '{attachment.filename}' exceeds the limit of {int(FILE_LIMIT_DISCORD / 1024 / 1024)} MB.")
        
        else:
            save_path = saveLocation
            file_path = os.path.join(save_path, attachment.filename)
            await attachment.save(file_path)
            logger.info(f"Saved {attachment.filename} to {file_path}")
            emb16 = discord.Embed(
                title="Upload alert: Successful", 
                description=f"File '{attachment.filename}' has been successfully uploaded and saved.", 
                colour=Color.DEFAULT.value
            )
            emb16.set_footer(text=Embed_t.DEFAULT_FOOTER.value)
            await message.delete()
            await d_ctx.msg.edit(embed=emb16)

    elif message.content == "EXIT":
        raise TimeoutError("EXITED!")

    else:
        try:
            google_drive_link = message.content
            await message.delete()
            folder_id = await GDapi.grabfolderid(google_drive_link, d_ctx.msg)
            if not folder_id: raise GDapiError("Could not find the folder id!")
            files = await GDapi.downloadsaves_gd(d_ctx.msg, folder_id, saveLocation, max_files=1, sys_files=None, ps_save_pair_upload=False, ignore_filename_check=False)
            if len(files) == 0:
                raise FileError("No files downloaded!")
            file_path = files[0]

        except asyncio.TimeoutError:
            await d_ctx.msg.edit(embed=embgdt)
            raise TimeoutError("TIMED OUT!")

    return file_path

async def upload2_special(d_ctx: DiscordContext, saveLocation: str, max_files: int, splitvalue: str, savesize: int | None = None) -> list[str]:
    try:
        message: discord.Message = await bot.wait_for("message", check=lambda message: upl_check(message, d_ctx.ctx), timeout=UPLOAD_TIMEOUT)  # Wait for 300 seconds for a response with one attachments
    except asyncio.TimeoutError:
        await d_ctx.msg.edit(embed=embUtimeout)
        raise TimeoutError("TIMED OUT!")
    
    if len(message.attachments) > max_files:
        return []

    elif len(message.attachments) >= 1:
        attachments = message.attachments
        uploaded_file_paths = []
        valid_attachments = await orbis.checkSaves(d_ctx.msg, attachments, False, False, True, savesize)

        for attachment in valid_attachments:
            rel_file_path = attachment.filename.split(splitvalue)
            rel_file_path = "/".join(rel_file_path)
            rel_file_path = os.path.normpath(rel_file_path)
            path_len = len(MOUNT_LOCATION + f"/{'X' * RANDOMSTRING_LENGTH}/" + rel_file_path + "/")
    
            file_name = os.path.basename(rel_file_path)
            if len(file_name) > MAX_FILENAME_LEN:
                raise FileError(f"File name ({file_name}) ({len(file_name)}) is exceeding {MAX_FILENAME_LEN}!")
            
            elif path_len > MAX_PATH_LEN:
                raise FileError(f"Path: {rel_file_path} ({path_len}) is exceeding {MAX_PATH_LEN}!")
            
            dir_path = os.path.join(saveLocation, os.path.dirname(rel_file_path))
            await aiofiles.os.makedirs(dir_path, exist_ok=True)
            full_path = os.path.join(dir_path, file_name)

            await attachment.save(full_path)
            logger.info(f"Saved {attachment.filename} to {full_path}")
            
            emb1 = discord.Embed(
                title="Upload alert: Successful", 
                description=f"File '{rel_file_path}' has been successfully uploaded and saved.", 
                colour=Color.DEFAULT.value
            )
            emb1.set_footer(text=Embed_t.DEFAULT_FOOTER.value)  
            await d_ctx.msg.edit(embed=emb1)

            uploaded_file_paths.append(full_path)
        
        await message.delete()

    elif message.content == "EXIT":
        raise TimeoutError("EXITED!")
    
    else:
        try:
            google_drive_link = message.content
            await message.delete()
            folder_id = await GDapi.grabfolderid(google_drive_link, d_ctx.msg)
            if not folder_id: raise GDapiError("Could not find the folder id!")
            uploaded_file_paths = await GDapi.downloadfiles_recursive(d_ctx.msg, saveLocation, folder_id, max_files, savesize)
           
        except asyncio.TimeoutError:
            await d_ctx.msg.edit(embed=embgdt)
            raise TimeoutError("TIMED OUT!")
        
    return uploaded_file_paths

async def psusername(ctx: discord.ApplicationContext, username: str) -> str:
    """Used to obtain an account ID, either through converting from username, obtaining from db, or manually. Utilizes the PSN API or a website doing it for us."""
    await ctx.defer()

    if username == "":
        user_id = await fetch_accountid_db(ctx.author.id)
        if user_id is not None:
            # check blacklist while we are at it
            if await blacklist_check_db(None, user_id):
                blacklist_logger.info(f"{ctx.author.name} ({ctx.author.id}) used a blacklisted account ID: {user_id}")
                raise PSNIDError(BLACKLIST_MESSAGE)
            return user_id
        else:
            raise PSNIDError("Could not find previously stored account ID.")

    def check(message: discord.Message, ctx: discord.ApplicationContext) -> str:
        if message.author == ctx.author and message.channel == ctx.channel:
            return message.content and orbis.checkid(message.content)

    limit = 0

    if len(username) < 3 or len(username) > 16:
        await asyncio.sleep(1)
        raise PSNIDError("Invalid PS username!")
    elif not bool(PSN_USERNAME_RE.fullmatch(username)):
        await asyncio.sleep(1)
        raise PSNIDError("Invalid PS username!")

    if NPSSO is not None:
        try:
            userSearch = psnawp.user(online_id=username)
            user_id = userSearch.account_id
            user_id = orbis.handle_accid(user_id)
            delmsg = False
        
        except PSNAWPNotFound:
            await ctx.respond(embed=emb8)
            delmsg = True

            try:
                response = await bot.wait_for("message", check=lambda message: check(message, ctx), timeout=OTHER_TIMEOUT)
                user_id = response.content
                await response.delete()
            except asyncio.TimeoutError:
                await ctx.edit(embed=embnt)
                raise TimeoutError("TIMED OUT!")
    else:
        while True:

            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://psn.flipscreen.games/search.php?username={username}") as response:
                    response.text = await response.text()

            if response.status == 200 and limit != 20:
                data = json.loads(response.text)
                obtainedUsername = data["online_id"]

                if obtainedUsername.lower() == username.lower():
                    user_id = data["user_id"]
                    user_id = orbis.handle_accid(user_id)
                    delmsg = False
                    break
                else:
                    limit += 1
            else:
                await ctx.respond(embed=emb8)
                delmsg = True

                try:
                    response = await bot.wait_for("message", check=lambda message: check(message, ctx), timeout=OTHER_TIMEOUT)
                    user_id = response.content
                    await response.delete()
                    break
                except asyncio.TimeoutError:
                    await ctx.edit(embed=embnt)
                    raise TimeoutError("TIMED OUT!")
            
    if delmsg:
        await asyncio.sleep(0.5)
        await ctx.edit(embed=embvalidpsn)
    else:
        await ctx.respond(embed=embvalidpsn)

    await asyncio.sleep(0.5)

    # check blacklist while we are at it
    if await blacklist_check_db(None, user_id):
        blacklist_logger.info(f"{ctx.author.name} ({ctx.author.id}) used a blacklisted account ID: {user_id}")
        raise PSNIDError(BLACKLIST_MESSAGE)

    await write_accountid_db(ctx.author.id, user_id.lower())
    return user_id.lower()

async def replaceDecrypted(
          d_ctx: DiscordContext, 
          fInstance: FTPps, 
          files: list[str], 
          titleid: str, 
          mountLocation: str, 
          upload_individually: bool, 
          upload_decrypted: str, 
          savePairName: str,
          savesize: int
        ) -> list[str]:

    """Used in the encrypt command to replace files one by one, or how many you want at once."""
    from utils.namespaces import Crypto
    completed = []
    if upload_individually or len(files) == 1:
        total_count = 0
        for file in files:
            fullPath = mountLocation + "/" + file
            cwdHere = fullPath.split("/")
            lastN = cwdHere.pop(len(cwdHere) - 1)
            cwdHere = "/".join(cwdHere)

            emb18 = discord.Embed(
                title=f"Resigning Process (Decrypted): Upload\n{savePairName}",
                description=f"Please attach a decrypted savefile that you want to upload, MUST be equivalent to {file} (can be any name).",
                colour=Color.DEFAULT.value
            )
            emb18.set_footer(text=Embed_t.DEFAULT_FOOTER.value)

            await d_ctx.msg.edit(embed=emb18)

            attachmentPath = await upload1(d_ctx, upload_decrypted)
            newPath = os.path.join(upload_decrypted, lastN)
            await aiofiles.os.rename(attachmentPath, newPath)
            await crypthelp.extra_import(Crypto, titleid, newPath)

            await fInstance.replacer(cwdHere, lastN)
            completed.append(file)
            total_count += await aiofiles.os.path.getsize(newPath)
        if total_count > savesize:
            raise orbis.OrbisError(f"The files you are uploading for this save exceeds the savesize {savesize}!")
    
    else:
        async def send_chunk(msg_container: list[discord.Message], chunk: str) -> None:
            embenc_out = discord.Embed(
                title=f"Resigning Process (Decrypted): Upload\n{savePairName}",
                description=chunk,
                colour=Color.DEFAULT.value
            )
            embenc_out.set_footer(text=Embed_t.DEFAULT_FOOTER.value)
            msg = await d_ctx.ctx.send(embed=embenc_out)
            msg_container.append(msg)
            await asyncio.sleep(1)

        SPLITVALUE = "SLASH"

        emb18 = discord.Embed(
            title=f"Resigning Process (Decrypted): Upload\n{savePairName}",
            description=f"Please attach at least one of these files and make sure its the same name, including path in the name if that is the case. Instead of '/' use '{SPLITVALUE}', here are the contents:",
            colour=Color.DEFAULT.value
        )
        emb18.set_footer(text=Embed_t.DEFAULT_FOOTER.value)
        await d_ctx.msg.edit(embed=emb18)
        await asyncio.sleep(2)

        msg_container: list[discord.Message] = []
        current_chunk = ""
        for line in files:
            if len(current_chunk) + len(line) + 1 > EMBED_DESC_LIM:
                await send_chunk(msg_container, current_chunk)
                current_chunk = ""
            
            if current_chunk:
                current_chunk += "\n"
            current_chunk += line
        if current_chunk:
            await send_chunk(msg_container, current_chunk)

        uploaded_file_paths = await upload2(d_ctx, upload_decrypted, max_files=MAX_FILES, sys_files=False, ps_save_pair_upload=False, ignore_filename_check=True, savesize=savesize)

        for msg in msg_container:
            await msg.delete(delay=0.5)

        if len(uploaded_file_paths) >= 1:
            for file in await aiofiles.os.listdir(upload_decrypted):
                file1 = file.split(SPLITVALUE)
                if file1[0] == "": file1 = file1[1:]
                file1 = "/".join(file1)

                if file1 not in files:
                    await aiofiles.os.remove(os.path.join(upload_decrypted, file))
                    
                else:
                    for saveFile in files:
                        if file1 == saveFile:
                            lastN = os.path.basename(saveFile)
                            cwdHere = saveFile.split("/")
                            cwdHere = cwdHere[:-1]
                            cwdHere = "/".join(cwdHere)
                            cwdHere = mountLocation + "/" + cwdHere

                            filePath = os.path.join(upload_decrypted, file)
                            newRename = os.path.join(upload_decrypted, lastN)
                            await aiofiles.os.rename(filePath, newRename)
                            await crypthelp.extra_import(Crypto, titleid, newRename)

                            await fInstance.replacer(cwdHere, lastN) 
                            completed.append(lastN)  
                    
        else:
            raise FileError("No files passed check!")

    if len(completed) == 0:
        raise FileError("Could not replace any files")

    return completed

async def send_final(d_ctx: DiscordContext, file_name: str, zipupPath: str) -> None:
    """Zips path and uploads file through discord or google drive depending on the size."""
    zipfiles(zipupPath, file_name)
    final_file = os.path.join(zipupPath, file_name)
    final_size = await aiofiles.os.path.getsize(final_file)
    file_size_mb = final_size / (1024 * 1024)

    if file_size_mb < BOT_DISCORD_UPLOAD_LIMIT:
        await d_ctx.ctx.send(file=discord.File(final_file), reference=d_ctx.msg)
    else:
        file_url = await GDapi.uploadzip(final_file, file_name)
        embg = discord.Embed(
            title="Google Drive: Upload complete",
            description=file_url,
            colour=Color.DEFAULT.value
        )
        embg.set_footer(text=Embed_t.DEFAULT_FOOTER.value)
        await d_ctx.ctx.send(embed=embg, reference=d_ctx.msg)

def qr_check(message: discord.Message, ctx: discord.ApplicationContext, max_index: int, exit_val: str) -> str | bool:
    if message.author == ctx.author and message.channel == ctx.channel:
        if message.content == exit_val:
            return message.content
        else:
            try:
                index = int(message.content)
                return 1 <= index <= max_index
            except ValueError:
                return False
    return False

import discord
from discord.ui import View, Button
from dataclasses import dataclass
from typing import Literal
import os

@dataclass
class DiscordContext:
    ctx: discord.ApplicationContext
    msg: discord.Message

class WorkspaceError(Exception):
    pass

class PaginatorView(View):
    def __init__(self, items: list[str], title: str, per_page: int = 15):  # Updated to 15 items per page
        super().__init__(timeout=120)
        self.items = items
        self.title = title
        self.per_page = per_page
        self.current_page = 0
        self.selected_item = None
        self.message = None
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()

        prev_button = Button(label="Previous", style=discord.ButtonStyle.primary, row=0)
        prev_button.disabled = self.current_page == 0
        prev_button.callback = self.previous_page
        self.add_item(prev_button)

        next_button = Button(label="Next", style=discord.ButtonStyle.primary, row=0)
        next_button.disabled = (self.current_page + 1) * self.per_page >= len(self.items)
        next_button.callback = self.next_page
        self.add_item(next_button)

        start_index = self.current_page * self.per_page
        end_index = min(start_index + self.per_page, len(self.items))
        row = 1
        for i, item in enumerate(self.items[start_index:end_index], start=1):
            button = Button(label=f"{start_index + i}", style=discord.ButtonStyle.secondary, row=row)
            button.callback = self.make_select_callback(item)
            self.add_item(button)

            if i % 5 == 0:
                row += 1

        exit_button = Button(label="Exit", style=discord.ButtonStyle.danger, row=row)
        exit_button.callback = self.exit
        self.add_item(exit_button)

    def make_select_callback(self, item):
        async def callback(interaction: discord.Interaction):
            self.selected_item = item
            self.stop()
            await interaction.response.defer()
        return callback

    async def previous_page(self, interaction: discord.Interaction):
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    async def next_page(self, interaction: discord.Interaction):
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    async def exit(self, interaction: discord.Interaction):
        self.selected_item = "EXIT"
        self.stop()
        if self.message:
            try:
                await self.message.delete()
            except discord.errors.NotFound:
                pass
        await interaction.response.defer()

    def get_embed(self):
        start_index = self.current_page * self.per_page
        end_index = min(start_index + self.per_page, len(self.items))
        description = "\n".join(f"{start_index + i}. {item}" for i, item in enumerate(self.items[start_index:end_index], start=1))
        embed = discord.Embed(title=self.title, description=description, colour=discord.Colour.blurple())
        embed.set_footer(text=f"Page {self.current_page + 1} of {(len(self.items) + self.per_page - 1) // self.per_page}")
        return embed

async def qr_interface_main(d_ctx: DiscordContext, stored_saves: dict) -> tuple[str, dict] | tuple[Literal["EXIT"], Literal["EXIT"]]:
    raise NotImplementedError("This function is deprecated. Please use 'run_qr_paginator' instead.")

async def run_qr_paginator(d_ctx: DiscordContext, stored_saves: dict[str, dict[str, dict[str, str]]]) -> str:
    messages_to_delete = []

    while True:
        
        games = list(stored_saves.keys())
        if not games:
            raise WorkspaceError("NO STORED SAVES!")

        view = PaginatorView(games, title="Select a Game")
        embed = view.get_embed()
        view.message = await d_ctx.ctx.send(embed=embed, view=view)
        messages_to_delete.append(view.message)

        await view.wait()

        if view.selected_item == "EXIT":
            for message in messages_to_delete:
                try:
                    await message.delete()
                except discord.errors.NotFound:
                    pass
            return "EXIT"

        selected_game_name = view.selected_item
        selected_game_data = stored_saves[selected_game_name]
        for message in messages_to_delete:
            try:
                await message.delete()
            except discord.errors.NotFound:
                pass

        
        versions = []
        previous_cusa = None
        for cusa, titleId_dict in selected_game_data.items():
            for savedesc, path in titleId_dict.items():
                if cusa != previous_cusa:
                    versions.append((f"(🔸 {cusa})                            🔹️{savedesc}", path))  # CUSA wird nun zuerst angezeigt, danach die Version
                    previous_cusa = cusa
                else:
                    versions.append((f"       🔹️ {savedesc}", path))  # Nur die Version, wenn CUSA gleich bleibt

        if not versions:
            raise WorkspaceError(f"No versions available for the game '{selected_game_name}'.")

        version_names = [v[0] for v in versions]
        view = PaginatorView(version_names, title=f"Select a Version for {selected_game_name}")
        embed = view.get_embed()
        view.message = await d_ctx.ctx.send(embed=embed, view=view)

        await view.wait()

        if view.selected_item == "EXIT":
            try:
                await view.message.delete()
            except discord.errors.NotFound:
                pass
            return "EXIT"

        selected_version_name = view.selected_item
        selected_version_path = next(v[1] for v in versions if v[0] == selected_version_name)

        # Pfad auflösen und zurückgeben
        savename = await get_savename_from_bin_ext(selected_version_path)
        if not savename:
            raise WorkspaceError("Failed to extract save name!")

        full_path = os.path.join(selected_version_path, savename)
        try:
            await view.message.delete()
        except discord.errors.NotFound:
            pass
        return full_path
