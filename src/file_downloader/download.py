import os
import discord
from dotenv import load_dotenv
from src.utils.logging import setup_logger

# Set up logger
logger = setup_logger(__name__)

# Load environment variables from .env file
load_dotenv()

# Retrieve the token and channel ID from environment variables
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# Set up the client with the necessary intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

client = discord.Client(intents=intents)

MESSAGES_TO_PROCESS = 10

# COMPLETED_EMOJI is used by this bot to signal that a file has been processed
COMPLETED_EMOJI = "✅"

# REPEAT_EMOJI is used by users to signal that a file should be reprocessed
REPEAT_EMOJI = "🔁"

# Here's the structure of a message.reactions:
# [<Reaction emoji='✅' me=False count=1>, <Reaction emoji='🔁' me=False count=1>]


async def remove_white_check_mark_if_repeat(message):
    """
    Removes the bot's white check mark from the message if the message has a repeat emoji
    """
    remove_check_mark = False
    for reaction in message.reactions:
        if reaction.emoji == REPEAT_EMOJI:
            remove_check_mark = True
    if remove_check_mark:
        reactions_to_remove = []
        for reaction in message.reactions:
            if reaction.emoji == COMPLETED_EMOJI:
                logger.info(f"Removing {reaction.emoji} from {message}")
                reactions_to_remove.append(reaction)
        for reaction in reactions_to_remove:
            message.reactions.remove(reaction)


async def has_white_check_mark(message):
    """
    Returns True if the message has a white check mark reaction from the bot
    """
    for reaction in message.reactions:
        if reaction.emoji == COMPLETED_EMOJI and reaction.me:
            return True
    return False


async def add_white_check_mark(message):
    await message.add_reaction(COMPLETED_EMOJI)
    logger.info(f"Adding {COMPLETED_EMOJI} to {message}")


async def perform_download(message):
    if not message.attachments:
        logger.warning("No attachments found")
        return
    for attachment in message.attachments:
        if attachment.filename.endswith((".mp3", ".wav", ".m4a")):
            await attachment.save(f"data/voice-memos/{attachment.filename}")
            logger.info(f"Downloaded {attachment.filename}")


@client.event
async def on_ready():
    logger.info(f"Logged in as {client.user}")
    channel = client.get_channel(CHANNEL_ID)

    if channel is None:
        logger.error("Channel not found!")
        await client.close()
        return

    # Iterate through the latest messages in the channel and remove the
    # :white_check_mark: from any which have a :repeat: emoji
    async for message in channel.history(limit=MESSAGES_TO_PROCESS):
        await remove_white_check_mark_if_repeat(message)

    # Iterate through the latest messages in the channel and download the audio
    # files of any which do not have a :white_check_mark:
    async for message in channel.history(limit=MESSAGES_TO_PROCESS):
        if await has_white_check_mark(message):
            logger.info(f"Skipping message due to {COMPLETED_EMOJI} {message}")
            continue
        logger.info(f"Message: {message}, attachments: {message.attachments}")

        await perform_download(message)
        await add_white_check_mark(message)

    await client.close()


if __name__ == "__main__":
    client.run(TOKEN)
