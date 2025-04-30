from unittest.mock import AsyncMock, Mock

import pytest

from .download import (
    COMPLETED_EMOJI,
    REPEAT_EMOJI,
    add_white_check_mark,
    has_repeat_emoji,
    has_white_check_mark,
    perform_download,
    process_messages,
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
async def test_has_repeat_emoji(mock_message, mock_reaction):
    # Test without repeat emoji
    assert await has_repeat_emoji(mock_message) is False

    # Test with repeat emoji
    mock_reaction.emoji = REPEAT_EMOJI
    mock_message.reactions = [mock_reaction]
    assert await has_repeat_emoji(mock_message) is True


class AsyncIterList:
    def __init__(self, items):
        self.items = items

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self.items:
            raise StopAsyncIteration
        return self.items.pop(0)


@pytest.mark.asyncio
async def test_process_messages_with_checkmark():
    # Create a mock message with checkmark
    mock_message = AsyncMock()
    check_reaction = Mock()
    check_reaction.emoji = COMPLETED_EMOJI
    check_reaction.me = True
    mock_message.reactions = [check_reaction]

    # Create a mock attachment
    mock_attachment = AsyncMock()
    mock_attachment.filename = "test.mp3"
    mock_message.attachments = [mock_attachment]

    # Create mock channel that returns our message
    mock_channel = AsyncMock()
    mock_channel.history.return_value = AsyncIterList([mock_message])

    # Call process_messages
    await process_messages(mock_channel)

    # Verify that save was NOT called since message had checkmark
    mock_attachment.save.assert_not_called()


@pytest.mark.asyncio
async def test_process_messages_with_checkmark_and_repeat():
    # Create a mock message with both checkmark and repeat emoji
    mock_message = AsyncMock()
    check_reaction = Mock()
    check_reaction.emoji = COMPLETED_EMOJI
    check_reaction.me = True
    repeat_reaction = Mock()
    repeat_reaction.emoji = REPEAT_EMOJI
    mock_message.reactions = [check_reaction, repeat_reaction]

    # Create a mock attachment
    mock_attachment = AsyncMock()
    mock_attachment.filename = "test.mp3"
    mock_message.attachments = [mock_attachment]

    # Create mock channel that returns our message
    mock_channel = AsyncMock()
    mock_channel.history.return_value = AsyncIterList([mock_message])

    # Call process_messages
    await process_messages(mock_channel)

    # Verify that save WAS called since message had repeat emoji
    mock_attachment.save.assert_called_once_with("data/voice-memos/test.mp3")
