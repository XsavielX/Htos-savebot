import os
import discord
import logging.config
import re
import errno
from zipfile import (
    # ZIP_BZIP2,
    # ZIP_DEFLATED,
    # ZIP_LZMA,
    ZIP_STORED
)
from discord.ext import commands
from enum import Enum
from psnawp_api import PSNAWP

VERSION = "v2.0.3"

# LOGGER
def setup_logger() -> logging.Logger:
    LOGGER_FOLDER = "logs"
    LOGGER_PATH = os.path.join(LOGGER_FOLDER, "HTOS.log")
    if not os.path.exists(LOGGER_FOLDER):
        os.makedirs(LOGGER_FOLDER)
    if not os.path.exists(LOGGER_PATH):
        with open(LOGGER_PATH, "w"):
            ...

    logger = logging.getLogger("HTOS_LOGS")

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
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": LOGGER_PATH,
                "maxBytes": 25 * 1024 * 1024,
                "backupCount": 3
            }
        },
        "loggers": {
            "HTOS_LOGS": {
                "level": "INFO",
                "handlers": [
                    "file"
                ]
            }
        }
    }
    logging.config.dictConfig(config=logging_config)

    return logger


logger = setup_logger()

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
TOKEN = str(os.getenv("TOKEN"))
NPSSO = str(os.getenv("NPSSO"))
# how to obtain NPSSO:
# go to playstation.com and login
# go to this link https://ca.account.sony.com/api/v1/ssocookie
# find {"npsso":"<64 character npsso code>"}

# if you leave it None the psn.flipscreen.games website will be used to obtain account ID

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
NDOG_TITLEID = ["CUSA00557", "CUSA00559", "CUSA00552", "CUSA00556", "CUSA00554",  # tlou remastered
                "CUSA00341", "CUSA00917", "CUSA00918", "CUSA04529", "CUSA00912",  # uncharted 4
                "CUSA07875", "CUSA09564", "CUSA07737", "CUSA08347", "CUSA08352"]  # uncharted the lost legacy
NDOG_COL_TITLEID = ["CUSA02344", "CUSA02343", "CUSA02826", "CUSA02320", "CUSA01399"]  # the nathan drake collection
NDOG_TLOU2_TITLEID = ["CUSA07820", "CUSA10249", "CUSA13986", "CUSA14006"]  # tlou part 2
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

# BOT CONFIG
FILE_LIMIT_DISCORD = 500 * 1024 * 1024  # 500 MB, discord file limit
SYS_FILE_MAX = 1 * 1024 * 1024  # sce_sys files are not that big so 1 MB, keep this low
MAX_FILES = 100
UPLOAD_TIMEOUT = 600  # seconds, for uploading files or google drive folder link
OTHER_TIMEOUT = 300  # seconds, for button click, responding to quickresign command, and responding with account id
BOT_DISCORD_UPLOAD_LIMIT = 25  # 25 mb minimum when no nitro boosts in server
ZIPFILE_COMPRESSION_MODE = ZIP_STORED  # check the imports for all modes
ZIPFILE_COMPRESSION_LEVEL = None  # change this only if you know the range for the chosen mode
CREATESAVE_ENC_CHECK_LIMIT = 20  # if the amount of gamesaves uploaded in createsave command is less or equal to this number we will perform a check on each of the files to see if we can add encryption to it

PS_ID_DESC = "Your Playstation Network username. Do not include if you want to use the previous one."

BASE_ERROR_MSG = "An unexpected server-side error has occurred! Try again, and if it occurs multiple times, please contact the host."

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

SAVEBLOCKS_MAX = 2 ** 15  # SAVESIZE WILL BE SAVEBLOCKS * 2¹⁵
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
    title="Upload alert: Error",
    description="Time's up! You didn't attach any files.",
    colour=Color.DEFAULT.value
)
embUtimeout.set_footer(text=Embed_t.DEFAULT_FOOTER.value)

embgdt = discord.Embed(
    title="Google drive upload: Error",
    description="You did not respond with the link in time!",
    colour=Color.DEFAULT.value
)
embgdt.set_footer(text=Embed_t.DEFAULT_FOOTER.value)

emb6 = discord.Embed(
    title="Upload alert: Error",
    description="You did not upload 2 savefiles in one response to the bot, or you uploaded invalid files!",
    colour=Color.DEFAULT.value
)
emb6.set_footer(text=Embed_t.DEFAULT_FOOTER.value)

embhttp = discord.Embed(
    title="HttpError",
    description="Are you sure that you uploaded binary content?",
    colour=Color.DEFAULT.value
)
embhttp.set_footer(text=Embed_t.DEFAULT_FOOTER.value)

embEncrypted1 = discord.Embed(
    title="Resigning process: Encrypted",
    description="Please attach atleast two encrypted savefiles that you want to upload (.bin and non bin).",
    colour=Color.DEFAULT.value
)
embEncrypted1.set_footer(text=Embed_t.DEFAULT_FOOTER.value)

embDecrypt1 = discord.Embed(
    title="Decrypt Process",
    description="Please attach atleast two encrypted savefiles that you want to upload (.bin and non bin).",
    colour=Color.DEFAULT.value
)
embDecrypt1.set_footer(text=Embed_t.DEFAULT_FOOTER.value)

emb14 = discord.Embed(
    title="Resigning process: Decrypted",
    description="Please attach atleast two encrypted savefiles that you want to upload (.bin and non bin).",
    colour=Color.DEFAULT.value
)
emb14.set_footer(text=Embed_t.DEFAULT_FOOTER.value)

emb20 = discord.Embed(
    title="Re-region process: Upload encrypted files from the FOREIGN region",
    description="Please attach atleast two encrypted savefiles that you want to upload (.bin and non bin).",
    colour=Color.DEFAULT.value
)
emb20.set_footer(text=Embed_t.DEFAULT_FOOTER.value)

emb4 = discord.Embed(
    title="Resigning process: Encrypted",
    description="Your save is being resigned, please wait...",
    colour=Color.DEFAULT.value
)
emb4.set_footer(text=Embed_t.DEFAULT_FOOTER.value)

emb21 = discord.Embed(
    title="Re-region process: Upload encrypted files from YOUR region",
    description="Please attach two encrypted savefiles that you want to upload (.bin and non bin).",
    colour=Color.DEFAULT.value
)
emb21.set_footer(text=Embed_t.DEFAULT_FOOTER.value)

emb22 = discord.Embed(
    title="Obtain process: Keystone",
    description="Obtaining keystone, please wait...",
    colour=Color.DEFAULT.value
)
emb22.set_footer(text=Embed_t.DEFAULT_FOOTER.value)

embpng = discord.Embed(
    title="PNG Process",
    description="Please attach atleast two encrypted savefiles that you want to upload (.bin and non bin).",
    colour=Color.DEFAULT.value
)
embpng.set_footer(text=Embed_t.DEFAULT_FOOTER.value)

embpng1 = discord.Embed(
    title="PNG process: Initializing",
    description="Mounting save.",
    colour=Color.DEFAULT.value
)
embpng1.set_footer(text=Embed_t.DEFAULT_FOOTER.value)

embpng2 = discord.Embed(
    title="PNG process: Downloading",
    description="Save mounted",
    colour=Color.DEFAULT.value
)
embpng2.set_footer(text=Embed_t.DEFAULT_FOOTER.value)

embnv1 = discord.Embed(
    title="Error: PS username not valid",
    description="This PS username is not in a valid format.",
    colour=Color.DEFAULT.value
)
embnv1.set_footer(text=Embed_t.DEFAULT_FOOTER.value)

emb8 = discord.Embed(
    title="Error: PSN username",
    description=f"Your input was not a valid PSN username, you have {OTHER_TIMEOUT} seconds to reply with your account ID instead.",
    colour=Color.DEFAULT.value
)
emb8.set_footer(text=Embed_t.DEFAULT_FOOTER.value)

embnt = discord.Embed(
    title="Error: Time limit reached",
    description="You did not send your account ID in time.",
    colour=Color.DEFAULT.value
)
embnt.set_footer(text=Embed_t.DEFAULT_FOOTER.value)

embvalidpsn = discord.Embed(
    title="Obtained: PSN username",
    description="Your input was a valid PSN username.",
    colour=Color.DEFAULT.value
)
embvalidpsn.set_footer(text=Embed_t.DEFAULT_FOOTER.value)

embinit = discord.Embed(
    title="Ps4 Save Bot <:emoji_1:1297350848858558464> ",
    description="<:emoji_3:1297365418524147802> Click the ```Create Thread```button to get started! You can return to your personal thread anytime. <:emoji_4:1297366547123408939>\n\n<:emoji_5:1297369037889601607> If the interaction fails, the bot is most likely offline. <:emoji_6:1297369891736780931>",
    colour=0x39FF14  # Neon-Green
)

embinit.set_footer(
    text=Embed_t.DEFAULT_FOOTER.value,
    icon_url="https://cdn.discordapp.com/attachments/1256434247120584737/1297375655654195250/lightning.gif?ex=6715b2bc&is=6714613c&hm=94dea1274dda3e7996b5c369d03585e0ee4b5c4edc985abff86e20b84c67e898&"
)

embinit.set_thumbnail(url="https://cdn.discordapp.com/attachments/1256434247120584737/1297344797086060574/standard.gif?ex=671595ff&is=6714447f&hm=98be2d6eb93d0c40b68e072b0f8da8b4bfe3d6c3c3991fde38f9960f5c45f44b&=&width=120&height=120")

embTitleChange = discord.Embed(
    title="Change title: Upload",
    description="Please attach atleast two encrypted savefiles that you want to upload (.bin and non bin).",
    colour=Color.DEFAULT.value
)
embTitleChange.set_footer(text=Embed_t.DEFAULT_FOOTER.value)

embTitleErr = discord.Embed(
    title="Change title: Error",
    description="Please select a maintitle or subtitle.",
    colour=Color.DEFAULT.value
)
embTitleErr.set_footer(text=Embed_t.DEFAULT_FOOTER.value)

embTimedOut = discord.Embed(
    title="Timed out!",
    description="Sending file.",
    colour=Color.DEFAULT.value
)
embTimedOut.set_footer(text=Embed_t.DEFAULT_FOOTER.value)

embDone_G = discord.Embed(
    title="Success",
    description=f"Please report any errors.",
    colour=Color.DEFAULT.value
)
embDone_G.set_footer(text=Embed_t.DEFAULT_FOOTER.value)

emb_conv_choice = discord.Embed(
    title="Converter: Choice",
    description=f"Could not recognize the platform of the save, please choose what platform to convert the save to.",
    colour=Color.DEFAULT.value
)
emb_conv_choice.set_footer(text=Embed_t.DEFAULT_FOOTER.value)

emb_upl_savegame = discord.Embed(
    title="Upload files",
    description=f"Please attach atleast 1 savefile, it must be fully decrypted.",
    colour=Color.DEFAULT.value
)
emb_upl_savegame.set_footer(text=Embed_t.DEFAULT_FOOTER.value)

loadSFO_emb = discord.Embed(
    title="Initializing",
    description="Loading param.sfo...",
    color=Color.DEFAULT.value
)
loadSFO_emb.set_footer(text=Embed_t.DEFAULT_FOOTER.value)

finished_emb = discord.Embed(title="Finished", color=Color.DEFAULT.value)
finished_emb.set_footer(text=Embed_t.DEFAULT_FOOTER.value)

loadkeyset_emb = discord.Embed(
    title="Initializing",
    description="Obtaining keyset...",
    color=Color.DEFAULT.value
)
loadkeyset_emb.set_footer(text=Embed_t.DEFAULT_FOOTER.value)

working_emb = discord.Embed(
    title="Working...",
    color=Color.DEFAULT.value
)
working_emb.set_footer(text=Embed_t.DEFAULT_FOOTER.value)
