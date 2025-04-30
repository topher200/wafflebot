import pytest
from unittest.mock import Mock, AsyncMock, patch
import discord
from .download import (
    remove_white_check_mark_if_repeat,
    has_white_check_mark,
    add_white_check_mark,
    perform_download,
    COMPLETED_EMOJI,
    REPEAT_EMOJI,
)


# Fixture for a mock Discord message
@pytest.fixture
def mock_message():
    message = AsyncMock()
    message.reactions = []
    message.attachments = []
    return message


# Fixture for a mock reaction
@pytest.fixture
def mock_reaction():
    reaction = Mock()
    reaction.me = False
    return reaction


@pytest.mark.asyncio
async def test_has_white_check_mark_with_no_reactions(mock_message):
    assert await has_white_check_mark(mock_message) is False


@pytest.mark.asyncio
async def test_has_white_check_mark_with_bot_checkmark(mock_message, mock_reaction):
    mock_reaction.emoji = COMPLETED_EMOJI
    mock_reaction.me = True
    mock_message.reactions = [mock_reaction]
    assert await has_white_check_mark(mock_message) is True


@pytest.mark.asyncio
async def test_add_white_check_mark(mock_message):
    await add_white_check_mark(mock_message)
    mock_message.add_reaction.assert_called_once_with(COMPLETED_EMOJI)


@pytest.mark.asyncio
async def test_perform_download_no_attachments(mock_message):
    await perform_download(mock_message)
    assert not mock_message.attachments


@pytest.mark.asyncio
async def test_perform_download_with_audio_file(mock_message):
    # Create a mock attachment
    mock_attachment = AsyncMock()
    mock_attachment.filename = "test.mp3"
    mock_message.attachments = [mock_attachment]

    await perform_download(mock_message)
    mock_attachment.save.assert_called_once_with("data/voice-memos/test.mp3")


@pytest.mark.asyncio
async def test_remove_white_check_mark_if_repeat(mock_message, mock_reaction):
    # Setup reactions
    check_reaction = Mock()
    check_reaction.emoji = COMPLETED_EMOJI
    repeat_reaction = Mock()
    repeat_reaction.emoji = REPEAT_EMOJI
    mock_message.reactions = [check_reaction, repeat_reaction]

    await remove_white_check_mark_if_repeat(mock_message)
    assert check_reaction not in mock_message.reactions
