import os
import discord
import logging.config
import re
import errno
from zipfile import (
    #ZIP_BZIP2, 
    #ZIP_DEFLATED, 
    #ZIP_LZMA, 
    ZIP_STORED
)
from discord.ext import commands
from enum import Enum
from psnawp_api import PSNAWP

VERSION = "v2.1.0"

# LOGGER
def setup_logger(path: str, logger_type: str) -> logging.Logger:
    dirname = os.path.dirname(path)

    if not os.path.exists(dirname):
        os.makedirs(dirname)
    if not os.path.exists(path):
        with open(path, "w"):
            ...

    logger = logging.getLogger(logger_type)

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "detailed": {
                "format": "[%(levelname)s|%(module)s|L%(lineno)d] %(asctime)s: %(message)s",
                "datefmt": "%Y-%m-%d - %H:%M:%S%z"
            }
        },
        "handlers": {
            logger_type: {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": path,
                "maxBytes": 25 * 1024 * 1024,
                "backupCount": 3
            }
        },
        "loggers": {
            logger_type: {
                "level": "INFO",
                "handlers": [
                    logger_type
                ]
            }
        }
    }
    logging.config.dictConfig(config=logging_config)

    return logger
logger = setup_logger(os.path.join("logs", "HTOS.log"), "HTOS_LOGS")
blacklist_logger = setup_logger(os.path.join("logs", "BLACKLIST.log"), "BLACKLIST_LOGS")

# CONFIG
IP = str(os.getenv("IP"))
PORT_FTP = int(os.getenv("FTP_PORT"))
PORT_CECIE = int(os.getenv("CECIE_PORT"))
MOUNT_LOCATION = str(os.getenv("MOUNT_PATH"))
PS_UPLOADDIR = str(os.getenv("UPLOAD_PATH"))
STORED_SAVES_FOLDER = str(os.getenv("STORED_SAVES_FOLDER_PATH"))
UPLOAD_ENCRYPTED = os.path.join("UserSaves", "uploadencrypted")
UPLOAD_DECRYPTED = os.path.join("UserSaves", "uploaddecrypted")
DOWNLOAD_ENCRYPTED = os.path.join("UserSaves", "downloadencrypted")
PNG_PATH = os.path.join("UserSaves", "png")
PARAM_PATH = os.path.join("UserSaves", "param")
DOWNLOAD_DECRYPTED = os.path.join("UserSaves", "downloaddecrypted")
KEYSTONE_PATH = os.path.join("UserSaves", "keystone")
RANDOMSTRING_LENGTH = 10
DATABASENAME_THREADS = "valid_threads.db"
DATABASENAME_ACCIDS = "account_ids.db"
DATABASENAME_BLACKLIST = "blacklist.db"
TOKEN = str(os.getenv("TOKEN"))
NPSSO = str(os.getenv("NPSSO"))
# how to obtain NPSSO:
# go to playstation.com and login
# go to this link https://ca.account.sony.com/api/v1/ssocookie
# find {"npsso":"<64 character npsso code>"}

# if you leave it None the psn.flipscreen.games website will be used to obtain account ID

BLACKLIST_MESSAGE = "YOU HAVE BEEN DENIED!"

psnawp = None
if NPSSO is not None:
    psnawp = PSNAWP(NPSSO)
    print("psnawp initialized")
else:
    print("It is recommended that you register a NPSSO token.")

# BOT INITIALIZATION 
activity = discord.Activity(type=discord.ActivityType.watching, name="a Tutorial before messaging Saviel privately 😉")
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=">", activity=activity, intents=intents)

# TITLE IDS FOR CRYPT HANDLING
GTAV_TITLEID = ["CUSA00411", "CUSA00419", "CUSA00880"] 
RDR2_TITLEID = ["CUSA03041", "CUSA08519", "CUSA08568", "CUSA15698"]
XENO2_TITLEID = ["CUSA05350", "CUSA05088", "CUSA04904", "CUSA05085", "CUSA05774"]
BL3_TITLEID = ["CUSA07823", "CUSA08025"]
WONDERLANDS_TITLEID = ["CUSA23766", "CUSA23767"]
NDOG_TITLEID = ["CUSA00557", "CUSA00559", "CUSA00552", "CUSA00556", "CUSA00554", # tlou remastered
                "CUSA00341", "CUSA00917", "CUSA00918", "CUSA04529", "CUSA00912", # uncharted 4
                "CUSA07875", "CUSA09564", "CUSA07737", "CUSA08347", "CUSA08352"] # uncharted the lost legacy
NDOG_COL_TITLEID = ["CUSA02344", "CUSA02343", "CUSA02826", "CUSA02320", "CUSA01399"] # the nathan drake collection
NDOG_TLOU2_TITLEID = ["CUSA07820", "CUSA10249", "CUSA13986", "CUSA14006"] # tlou part 2
MGSV_TPP_TITLEID = ["CUSA01140", "CUSA01154", "CUSA01099"]
MGSV_GZ_TITLEID = ["CUSA00218", "CUSA00211", "CUSA00225"]
REV2_TITLEID = ["CUSA00924", "CUSA01133", "CUSA01141", "CUSA00804"]
DL1_TITLEID = ["CUSA00050", "CUSA02010", "CUSA03991", "CUSA03946", "CUSA00078"]
DL2_TITLEID = ["CUSA12555", "CUSA12584", "CUSA28617", "CUSA28743"]
RGG_TITLEID = ["CUSA32173", "CUSA32174", "CUSA32171"]
DI1_TITLEID = ["CUSA03291", "CUSA03290", "CUSA03684", "CUSA03685"]
DI2_TITLEID = ["CUSA27043", "CUSA01104", "CUSA35681"]
NMS_TITLEID = ["CUSA03952", "CUSA04841", "CUSA05777", "CUSA05965"]
TERRARIA_TITLEID = ["CUSA00737", "CUSA00740"]
SMT5_TITLEID = ["CUSA42697", "CUSA42698"]
RCUBE_TITLEID = ["CUSA16074", "CUSA27390"]

# BOT CONFIG
FILE_LIMIT_DISCORD = 500 * 1024 * 1024  # 500 MB, discord file limit
SYS_FILE_MAX = 1 * 1024 * 1024 # sce_sys files are not that big so 1 MB, keep this low
MAX_FILES = 100
UPLOAD_TIMEOUT = 600 # seconds, for uploading files or google drive folder link
OTHER_TIMEOUT = 300 # seconds, for button click, responding to quickresign command, and responding with account id
BOT_DISCORD_UPLOAD_LIMIT = 25 # 25 mb minimum when no nitro boosts in server
ZIPFILE_COMPRESSION_MODE = ZIP_STORED # check the imports for all modes
ZIPFILE_COMPRESSION_LEVEL = None # change this only if you know the range for the chosen mode
CREATESAVE_ENC_CHECK_LIMIT = 20 # if the amount of gamesaves uploaded in createsave command is less or equal to this number we will perform a check on each of the files to see if we can add encryption to it

PS_ID_DESC = "Your Playstation Network username. Do not include if you want to use the previous one."

BASE_ERROR_MSG = "**Oops**❗ Something went wrong on the server-side. Please give it another shot, and if it keeps happening, feel free to reach out to the host for help!"

QR_FOOTER1 = "Respond with the number of your desired game, or type 'EXIT' to quit."
QR_FOOTER2 = "Respond with the number of your desired save, or type 'BACK' to go to the game menu."

# ORBIS CONSTANTS THAT DOES NOT NEED TO BE IN orbis.py

SCE_SYS_CONTENTS = ["param.sfo", "icon0.png", "keystone", "sce_icon0png1", "sce_paramsfo1"]
MANDATORY_SCE_SYS_CONTENTS = ["param.sfo", "icon0.png", "keystone"]

ICON0_MAXSIZE = 0x1C800
ICON0_FORMAT = (228, 128)
ICON0_NAME = "icon0.png"

KEYSTONE_SIZE = SEALED_KEY_ENC_SIZE = 0x60
KEYSTONE_NAME = "keystone"

PARAM_NAME = "param.sfo"

SAVEBLOCKS_MAX = 2**15 # SAVESIZE WILL BE SAVEBLOCKS * 2¹⁵
SAVESIZE_MAX = SAVEBLOCKS_MAX << 15

MAX_PATH_LEN = 1024
MAX_FILENAME_LEN = 255

# regex
PSN_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_-]+$")

# ERRNO
CON_FAIL = [errno.ECONNREFUSED, errno.ETIMEDOUT, errno.EHOSTUNREACH, errno.ENETUNREACH]
CON_FAIL_MSG = "PS4 not connected!"

# EMBEDS
EMBED_DESC_LIM = 4096
EMBED_FIELD_LIM = 25

class Color(Enum):
    DEFAULT = 0x854bf7
    GREEN = 0x22EA0D
    RED = 0xF42B00

class Embed_t(Enum):
    DEFAULT_FOOTER = f"Hosted by Saviel. ({VERSION})"

embUtimeout = discord.Embed(
    title="⏳ Upload Alert: Error",
    description="⚠️ Time's up! You didn't attach any files.\n📂 Please try again and make sure to upload the required files in time.",
    colour=Color.DEFAULT.value
)
embUtimeout.set_footer(text="⏰ Upload responsibly • PS4 Save Bot")

embgdt = discord.Embed(
    title="❌ Google Drive Upload: Error",
    description="⏳ You didn't respond with the link in time!\n🔗 Please try again and ensure to provide the correct link promptly.",
    colour=Color.DEFAULT.value
)
embgdt.set_footer(text="📂 Stay organized • PS4 Save Bot")

emb6 = discord.Embed(
    title="⚠️ Upload Alert: Error",
    description="🚫 You either didn't upload **2 valid save files** in one response or the files are invalid!\n📂 Please check your files and try again.",
    colour=Color.DEFAULT.value
)
emb6.set_footer(text="🔄 Double-check your uploads • PS4 Save Bot")

embhttp = discord.Embed(
    title="🌐 HTTP Error",
    description="🚫 Are you sure you uploaded **binary content**?\n📂 Please verify the file type and try again.",
    colour=Color.DEFAULT.value
)
embhttp.set_footer(text="⚙️ Upload valid binary files • PS4 Save Bot")

embEncrypted1 = discord.Embed(
    title="🔒 Resigning Process: Encrypted",
    description="📂 Please attach **at least two encrypted savefiles** (.bin and non-bin).\n💡 Type **'EXIT'** to cancel the command.",
    colour=Color.DEFAULT.value
)
embEncrypted1.set_footer(text="📄 Ensure to attach both files • PS4 Save Bot")

embDecrypt1 = discord.Embed(
    title="🔓 Decrypt Process",
    description="📂 Please attach **at least two encrypted savefiles** (.bin and non-bin).\n💡 Type **'EXIT'** to cancel the command.",
    colour=Color.DEFAULT.value
)
embDecrypt1.set_footer(text="📄 Ensure to attach both files • PS4 Save Bot")

emb14 = discord.Embed(
    title="🔁 Resigning Process: Decrypted",
    description="📂 Please attach **at least two encrypted savefiles** (.bin and non-bin).\n❌ Type **'EXIT'** to cancel the command.",
    colour=Color.DEFAULT.value
)
emb14.set_footer(text="📂 Attach the required files • PS4 Save Bot")

emb20 = discord.Embed(
    title="🌍 Re-region Process: Foreign Region Upload",
    description="📂 Please attach **at least two encrypted savefiles** from the **foreign region** (.bin and non-bin).\n❌ Type **'EXIT'** to cancel the command.",
    colour=Color.DEFAULT.value
)
emb20.set_footer(text="📄 Attach the required files • PS4 Save Bot")

emb4 = discord.Embed(
    title="🔒 Resigning Process: Encrypted",
    description="✨ Your save is being resigned. Please wait...",
    colour=Color.DEFAULT.value
)
emb4.set_footer(
    text="🔄 Sit tight, your save will be ready shortly!",
    icon_url="https://cdn.discordapp.com/emojis/1253123128943579147.gif?size=48"
)

emb21 = discord.Embed(
    title="🌍 Re-region Process: Upload Your Region's Encrypted Files",
    description="⚙️ Please attach **two encrypted savefiles** (.bin and non-bin).\n💡 Type **'EXIT'** to cancel the command.",
    colour=Color.DEFAULT.value
)
emb21.set_footer(
    text="📂 Let’s get those files ready for your region!",
    icon_url="https://cdn.discordapp.com/emojis/1253123128943579147.gif?size=48"
)

emb22 = discord.Embed(
    title="🔑 Keystone Process: Obtaining Keystone",
    description="⏳ Your keystone is being obtained. Please wait...",
    colour=Color.DEFAULT.value
)
emb22.set_footer(
    text="🔒 Securing your keystone file...",
    icon_url="https://cdn.discordapp.com/emojis/1253123128943579147.gif?size=48"
)

embpng = discord.Embed(
    title="🖼️ PNG Process: File Upload",
    description="📂 Please attach **two encrypted savefiles** (.bin and non-bin).\n💡 Type **'EXIT'** to cancel the command.",
    colour=Color.DEFAULT.value
)
embpng.set_footer(
    text="📤 Ready to process your PNG files...",
    icon_url="https://cdn.discordapp.com/emojis/1253123128943579147.gif?size=48"
)

embpng1 = discord.Embed(
    title="🖼️ PNG Process: Initializing",
    description="📂 Mounting save...",
    colour=Color.DEFAULT.value
)
embpng1.set_footer(text="🔄 Initializing process • PS4 Save Bot")

embpng2 = discord.Embed(
    title="🖼️ PNG Process: Downloading",
    description="📂 Save mounted successfully.",
    colour=Color.DEFAULT.value
)
embpng2.set_footer(text="📤 Preparing your PNG file • PS4 Save Bot")

emb8 = discord.Embed(
    title="⚠️ PSN Username Error",
    description=f"🚫 Your input was not a valid PSN username.\n⏳ You have {OTHER_TIMEOUT} seconds to reply with your account ID.",
    colour=Color.DEFAULT.value
)
emb8.set_footer(text="⚙️ Please provide a valid username • PS4 Save Bot")

embnt = discord.Embed(
    title="❌ Time Limit Reached",
    description="⏳ You did not send your account ID in time.",
    colour=Color.DEFAULT.value
)
embnt.set_footer(text="⏰ Be prompt next time • PS4 Save Bot")

embvalidpsn = discord.Embed(
    title="✅ PSN Username Verified",
    description="🎉 Your input was a valid PSN username.",
    colour=Color.DEFAULT.value
)
embvalidpsn.set_footer(text="✔️ Verification complete • PS4 Save Bot")

embinit = discord.Embed(
    title="🎮 PS4 Save Bot",
    description="Click the ```Create Thread```button to get started! You can return to your personal thread anytime.\n\nIf the interaction fails, the bot might be offline.",
    colour=0x39FF14
)
embinit.set_footer(
    text="📢 Ready to help • PS4 Save Bot",
    icon_url="https://cdn.discordapp.com/attachments/1306713257909948436/1309976832036048916/lightning.gif?size=48"
)
embinit.set_thumbnail(
    url="https://cdn.discordapp.com/attachments/1256434247120584737/1297344797086060574/standard.gif"
)

embTitleChange = discord.Embed(
    title="📝 Change Title: Upload",
    description="📂 Please attach **two encrypted savefiles** (.bin and non-bin).\n💡 Type **'EXIT'** to cancel the command.",
    colour=Color.DEFAULT.value
)
embTitleChange.set_footer(text="📤 Let’s update your save title • PS4 Save Bot")

embTitleErr = discord.Embed(
    title="❌ Change Title: Error",
    description="🚫 Please select a main title or subtitle.",
    colour=Color.DEFAULT.value
)
embTitleErr.set_footer(text="⚠️ Title selection required • PS4 Save Bot")

embTimedOut = discord.Embed(
    title="⏳ Timed Out!",
    description="📤 Sending file...",
    colour=Color.DEFAULT.value
)
embTimedOut.set_footer(text="⚡ Action timeout • PS4 Save Bot")

embDone_G = discord.Embed(
    title="✅ Success",
    description="🎉 Please report any errors or issues.",
    colour=Color.DEFAULT.value
)
embDone_G.set_footer(text="✔️ Completed successfully • PS4 Save Bot")

emb_conv_choice = discord.Embed(
    title="🔄 Converter: Choice",
    description="❓ Could not recognize the platform of the save.\n🔧 Please choose what platform to convert the save to.",
    colour=Color.DEFAULT.value
)
emb_conv_choice.set_footer(text="⚙️ Conversion process • PS4 Save Bot")

emb_upl_savegame = discord.Embed(
    title="📂 Upload Save Files",
    description="📂 Please attach **1 fully decrypted savefile**.\n💡 Type **'EXIT'** to cancel the command.",
    colour=Color.DEFAULT.value
)
emb_upl_savegame.set_footer(text="📤 Ready to process your files • PS4 Save Bot")

loadSFO_emb = discord.Embed(
    title="🔄 Initializing",
    description="📂 Loading param.sfo...",
    colour=Color.DEFAULT.value
)
loadSFO_emb.set_footer(text="⚡ Processing • PS4 Save Bot")

finished_emb = discord.Embed(
    title="✅ Finished",
    description="🎉 Task completed successfully.",
    colour=Color.DEFAULT.value
)
finished_emb.set_footer(text="✔️ All done • PS4 Save Bot")

loadkeyset_emb = discord.Embed(
    title="🔄 Initializing",
    description="🔑 Obtaining keyset...",
    colour=Color.DEFAULT.value
)
loadkeyset_emb.set_footer(text="🔒 Secure processing • PS4 Save Bot")

working_emb = discord.Embed(
    title="🔄 Working...",
    description="⏳ Please wait while the process completes.",
    colour=Color.DEFAULT.value
)
working_emb.set_footer(text="⚡ Processing • PS4 Save Bot")

retry_emb = discord.Embed(
    title="🔄 Please Try Again",
    description="🚫 Something went wrong. Try again.",
    colour=Color.DEFAULT.value
)
retry_emb.set_footer(text="🔄 Retry • PS4 Save Bot")

blacklist_emb = discord.Embed(
    title=BLACKLIST_MESSAGE,
    colour=Color.RED.value
)
blacklist_emb.set_footer(text="⛔ Access restricted • PS4 Save Bot")

embChannelError = discord.Embed(
    title="🚫 Channel Error",
    description="📂 Invalid channel for this action.\n➡️ Please use the **bot channel** for commands.",
    colour=Color.DEFAULT.value
)
embChannelError.set_footer(text="📢 Stay organized • PS4 Save Bot")
