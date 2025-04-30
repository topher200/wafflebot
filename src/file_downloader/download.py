import datetime
import os
from pathlib import Path

import discord
from dotenv import load_dotenv

from src.utils.logging import setup_logger

logger = setup_logger(__name__)

VOICE_MEMOS_DIR = Path("data/voice-memos")
VOICE_MEMOS_DIR.mkdir(parents=True, exist_ok=True)

# Load environment variables from .env file
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID_STR = os.getenv("CHANNEL_ID")

if TOKEN is None:
    raise ValueError("DISCORD_TOKEN environment variable is not set")
if CHANNEL_ID_STR is None:
    raise ValueError("CHANNEL_ID environment variable is not set")

try:
    CHANNEL_ID = int(CHANNEL_ID_STR)
except ValueError as e:
    raise ValueError(f"CHANNEL_ID must be an integer, got: {CHANNEL_ID_STR}") from e

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


class EnhancedMessage:
    """
    A wrapper class for discord.Message that provides a more readable string
    representation.
    """

    def __init__(self, message):
        self._message = message

    def __getattr__(self, attr):
        return getattr(self._message, attr)

    def __str__(self):
        attachments_str = ", ".join(a.filename for a in self._message.attachments)
        return (
            f"Message(id={self._message.id}, "
            f"author={self._message.author.name}, "
            f"attachments=[{attachments_str}])"
        )

    def __repr__(self):
        return self.__str__()


async def has_white_check_mark(message):
    """
    Returns True if the message has a white check mark reaction from the bot
    """
    for reaction in message.reactions:
        if reaction.emoji == COMPLETED_EMOJI and reaction.me:
            return True
    return False


async def has_repeat_emoji(message):
    """
    Returns True if the message has a repeat emoji
    """
    for reaction in message.reactions:
        if reaction.emoji == REPEAT_EMOJI:
            return True
    return False


async def add_white_check_mark(message):
    await message.add_reaction(COMPLETED_EMOJI)
    logger.info(f"Adding {COMPLETED_EMOJI} to {message}")


async def perform_download(message):
    message = EnhancedMessage(message)
    if not message.attachments:
        logger.warning("No attachments found")
        return
    for attachment in message.attachments:
        if attachment.filename.endswith((".mp3", ".wav", ".m4a")):
            # prefix with a sortable timestamp with milliseconds precision
            current_time = datetime.datetime.now(tz=datetime.UTC).strftime(
                "%Y-%m-%d_%H-%M-%S_%f"
            )
            save_path = VOICE_MEMOS_DIR / f"{current_time}-{attachment.filename}"
            await attachment.save(str(save_path))
            logger.info(f"Downloaded {attachment.filename}")


async def process_messages(channel):
    """
    Process MESSAGES_TO_PROCESS messages in the channel.

    Download audio files if they either:
    1. Don't have a checkmark, or
    2. Have a repeat emoji (regardless of checkmark)
    """
    history = await channel.history(limit=MESSAGES_TO_PROCESS)
    async for message in history:
        message = EnhancedMessage(message)
        should_process = False

        if not await has_white_check_mark(message):
            should_process = True
            logger.info(f"Processing new message {message}")
        elif await has_repeat_emoji(message):
            should_process = True
            logger.info(f"Reprocessing message with repeat emoji {message}")

        if should_process:
            await perform_download(message)
            await add_white_check_mark(message)
        else:
            logger.info(f"Skipping message {message}")


@client.event
async def on_ready():
    logger.info(f"Logged in as {client.user}")
    channel = client.get_channel(CHANNEL_ID)

    if channel is None:
        logger.error("Channel not found!")
        await client.close()
        return

    await process_messages(channel)
    await client.close()


if __name__ == "__main__":
    client.run(TOKEN)
